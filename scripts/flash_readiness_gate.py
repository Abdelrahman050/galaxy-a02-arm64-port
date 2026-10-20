#!/usr/bin/env python3
"""Fail-closed, read-only image/readiness audit. Never operates on a device."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_INPUT = 1024 * 1024
MAX_EVIDENCE_ARTIFACT = 64 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
EVIDENCE_TYPES = {
    "signature_policy_known": {"documented_policy"},
    "candidate_signature_acceptance_verified": {"signature_verification", "runtime_test"},
    "avb_chain_consistent": {"cryptographic_verification"},
    "bootloader_handoff_verified": {"runtime_test"},
    "early_observation_channel_verified": {"runtime_test"},
    "recovery_firmware_hashes_verified": {"hash_verification"},
    "download_mode_recovery_verified": {"runtime_test"},
    "user_data_backup_verified": {"hash_verification"},
    "data_loss_risk_reviewed": {"review_record"},
    "official_firmware_untouched": {"hash_comparison"},
}
IMAGE_BOUND_GATES = {
    "candidate_signature_acceptance_verified",
    "avb_chain_consistent",
    "bootloader_handoff_verified",
    "early_observation_channel_verified",
}
OBSERVATION_PROOF = {"raw_log", "tool_output", "verified_runtime"}


def add(checks, reasons, name, status, detail=None, reason=None):
    item = {"name": name, "status": status}
    if detail is not None:
        item["detail"] = detail
    checks.append(item)
    if status in {"FAIL", "UNVERIFIED"} and reason:
        reasons.append(reason)


def load_json(path, label):
    if not path.is_file():
        raise ValueError(f"{label} file is missing")
    if path.stat().st_size > MAX_INPUT:
        raise ValueError(f"{label} exceeds 1 MiB")
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def hash_file(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def verify_artifact(record, evidence_dir):
    artifact = record.get("evidence_artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
        return "UNVERIFIED", {"artifact_present": False}
    declared = artifact.get("sha256")
    if not isinstance(declared, str) or SHA256_RE.fullmatch(declared) is None:
        return "FAIL", {"artifact_path": artifact.get("path"), "declared_sha256_valid": False}
    relative = Path(artifact["path"])
    if relative.is_absolute():
        return "FAIL", {"artifact_path": artifact["path"], "path_is_relative": False}
    try:
        base = evidence_dir.resolve()
        path = (base / relative).resolve(strict=True)
        if not path.is_relative_to(base) or not path.is_file():
            return "FAIL", {"artifact_path": artifact["path"], "path_within_evidence_directory": False}
        if path.stat().st_size > MAX_EVIDENCE_ARTIFACT:
            return "FAIL", {"artifact_path": artifact["path"], "size_limit_bytes": MAX_EVIDENCE_ARTIFACT}
        actual, size = hash_file(path)
    except (OSError, RuntimeError, ValueError):
        return "UNVERIFIED", {"artifact_path": artifact["path"], "artifact_readable": False}
    matched = actual.lower() == declared.lower()
    return ("ARTIFACT_HASH_MATCH" if matched else "FAIL"), {"artifact_path": artifact["path"], "actual_sha256": actual, "declared_sha256": declared, "artifact_size_bytes": size}


def evidence_record(value, key, digest, evidence_dir, checks, reasons):
    record = value.get(key)
    if not isinstance(record, dict):
        add(checks, reasons, key, "UNVERIFIED", reason=f"{key} lacks a structured evidence record; raw Boolean metadata is not proof")
        return
    evidence_type = record.get("evidence_type")
    reference = record.get("reference")
    valid = (
        record.get("value") is True
        and isinstance(evidence_type, str)
        and evidence_type in EVIDENCE_TYPES[key]
        and isinstance(reference, str)
        and bool(reference.strip())
    )
    detail = {"evidence_type": evidence_type, "reference_present": bool(isinstance(reference, str) and reference.strip())}
    artifact_status, artifact_detail = verify_artifact(record, evidence_dir)
    detail["evidence_artifact"] = artifact_detail
    if key in IMAGE_BOUND_GATES:
        subject = record.get("subject_sha256")
        bound = isinstance(digest, str) and SHA256_RE.fullmatch(str(subject or "")) is not None and subject.lower() == digest
        detail["subject_matches_actual_image"] = bound
        valid = valid and bound
    status = artifact_status if valid and artifact_status == "ARTIFACT_HASH_MATCH" else ("FAIL" if artifact_status == "FAIL" else "UNVERIFIED")
    add(checks, reasons, key, status, detail, f"{key} is missing, unverified, incorrectly typed, unreferenced, or not bound to the measured image")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="candidate evidence JSON")
    parser.add_argument("--image", type=Path, help="exact candidate image file; read-only SHA-256 verification")
    parser.add_argument("--policy", type=Path, help="optional device-specific state policy JSON")
    args = parser.parse_args()
    checks, reasons = [], []
    digest = None
    try:
        evidence = load_json(args.evidence, "evidence")
        device, candidate = evidence.get("device", {}), evidence.get("candidate", {})
        if not isinstance(device, dict) or not isinstance(candidate, dict):
            raise ValueError("device and candidate must be JSON objects")

        model = evidence.get("target_model")
        model_match = isinstance(model, str) and bool(model.strip()) and device.get("model") == model and candidate.get("target_model") == model
        add(checks, reasons, "target_model_matches_device_and_candidate", "PASS" if model_match else "FAIL", {"target_model": model, "device_model": device.get("model"), "candidate_model": candidate.get("target_model")}, "target model is missing or differs across records")
        boot = device.get("bootloader_build")
        boot_match = isinstance(boot, str) and bool(boot.strip()) and candidate.get("tested_bootloader_build") == boot
        add(checks, reasons, "bootloader_build_matches_test_record", "PASS" if boot_match else "UNVERIFIED", {"observed": boot, "tested": candidate.get("tested_bootloader_build")}, "tested bootloader build is missing or does not match")

        declared = candidate.get("image_sha256")
        declared_valid = isinstance(declared, str) and SHA256_RE.fullmatch(declared) is not None
        actual_size = None
        if args.image is not None:
            if not args.image.is_file():
                add(checks, reasons, "image_file_sha256", "FAIL", {"path_exists": False}, "specified image file is missing")
            else:
                digest, actual_size = hash_file(args.image)
                hash_match = declared_valid and digest.lower() == declared.lower()
                add(checks, reasons, "image_file_sha256", "PASS" if hash_match else "FAIL", {"actual_sha256": digest, "declared_sha256": declared, "actual_size_bytes": actual_size}, "actual image SHA-256 does not match the declared SHA-256")
        else:
            add(checks, reasons, "image_file_sha256", "UNVERIFIED", {"declared_sha256_valid": declared_valid}, "exact image file was not supplied, so its declared hash cannot be verified")
        if not declared_valid:
            add(checks, reasons, "declared_image_sha256_format", "FAIL", {"declared_sha256": declared}, "declared image SHA-256 is missing or malformed")

        image_size, partition_size = candidate.get("image_size_bytes"), candidate.get("partition_size_bytes")
        declared_sizes_ok = isinstance(image_size, int) and not isinstance(image_size, bool) and image_size > 0 and isinstance(partition_size, int) and not isinstance(partition_size, bool) and partition_size > 0
        sizes_consistent = declared_sizes_ok and (actual_size is None or actual_size == image_size)
        fits = sizes_consistent and image_size <= partition_size
        add(checks, reasons, "image_fits_partition", "PASS" if fits else "FAIL", {"declared_image_size_bytes": image_size, "actual_image_size_bytes": actual_size, "partition_size_bytes": partition_size}, "image/partition sizes are invalid, inconsistent with the file, or image exceeds partition")

        target_partition = candidate.get("target_partition")
        partition_proof = candidate.get("partition_identity")
        partition_ok = (
            isinstance(target_partition, str) and bool(target_partition.strip())
            and isinstance(partition_proof, dict)
            and partition_proof.get("value") == target_partition
            and isinstance(partition_proof.get("evidence_type"), str)
            and partition_proof.get("evidence_type") in {"partition_table_analysis", "runtime_test"}
            and isinstance(partition_proof.get("reference"), str) and bool(partition_proof["reference"].strip())
        )
        partition_artifact_status, partition_artifact_detail = verify_artifact(partition_proof, args.evidence.parent) if isinstance(partition_proof, dict) else ("UNVERIFIED", {"artifact_present": False})
        partition_status = "ARTIFACT_HASH_MATCH" if partition_ok and partition_artifact_status == "ARTIFACT_HASH_MATCH" else ("FAIL" if partition_artifact_status == "FAIL" else "UNVERIFIED")
        add(checks, reasons, "target_partition_identity", partition_status, {"target_partition": target_partition, "proof_type": partition_proof.get("evidence_type") if isinstance(partition_proof, dict) else None, "evidence_artifact": partition_artifact_detail}, "target partition identity lacks a matching, hash-verified evidence artifact")

        for key in EVIDENCE_TYPES:
            evidence_record(candidate, key, digest, args.evidence.parent, checks, reasons)

        if args.policy is not None:
            policy = load_json(args.policy, "device policy")
            policy_model = policy.get("target_model")
            policy_match = policy_model == model
            add(checks, reasons, "device_policy_model_match", "PASS" if policy_match else "FAIL", {"policy_model": policy_model, "candidate_model": model}, "device policy model does not match this candidate")
            required = policy.get("required_observations", [])
            if not isinstance(required, list):
                raise ValueError("device policy required_observations must be an array")
            observations = device.get("observations", {})
            if not isinstance(observations, dict):
                raise ValueError("device observations must be an object")
            for item in required:
                if not isinstance(item, dict) or not isinstance(item.get("field"), str):
                    raise ValueError("each device policy observation requires a field")
                field = item["field"]
                observed = observations.get(field)
                match = isinstance(observed, dict) and observed.get("value") == item.get("expected")
                proof_ok = match and isinstance(observed.get("evidence_level"), str) and observed.get("evidence_level") in OBSERVATION_PROOF and isinstance(observed.get("reference"), str) and bool(observed["reference"].strip())
                artifact_status, artifact_detail = verify_artifact(observed, args.evidence.parent) if isinstance(observed, dict) else ("UNVERIFIED", {"artifact_present": False})
                status = "ARTIFACT_HASH_MATCH" if proof_ok and artifact_status == "ARTIFACT_HASH_MATCH" else ("FAIL" if isinstance(observed, dict) and match and artifact_status == "FAIL" else ("FAIL" if isinstance(observed, dict) and not match else "UNVERIFIED"))
                add(checks, reasons, f"policy_observation:{field}", status, {"expected": item.get("expected"), "observed": observed.get("value") if isinstance(observed, dict) else None, "evidence_level": observed.get("evidence_level") if isinstance(observed, dict) else None, "evidence_artifact": artifact_detail}, f"device policy observation {field} is missing, mismatched, or lacks verified artifact bytes")

    except (OSError, ValueError, json.JSONDecodeError, UnicodeError) as exc:
        add(checks, reasons, "input_validation", "FAIL", {"error": str(exc)}, str(exc))

    ready = not reasons
    result = {"schema": "flash-readiness.v2", "decision": "READY_FOR_REVIEW" if ready else "NO_GO", "checks": checks, "reasons": reasons, "action_authorized": False, "action_performed": False, "scope": "Read-only metadata and supplied-image audit. ARTIFACT_HASH_MATCH confirms only that referenced bytes match their declared hash; a human must inspect their semantics and separately authorize any future device modification."}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
