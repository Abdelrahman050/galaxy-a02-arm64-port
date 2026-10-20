#!/usr/bin/env python3
"""Read-only ARM64 kernel artifact and ABI audit; emits JSON on stdout."""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

MAX_METADATA = 4 * 1024 * 1024
MAX_MAP = 128 * 1024 * 1024


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_limited(path, limit):
    if path.stat().st_size > limit:
        raise ValueError(f"{path.name} exceeds the {limit}-byte metadata limit")
    return path.read_bytes()


def check_abi(baseline_path, candidate_path):
    baseline = json.loads(read_limited(baseline_path, MAX_METADATA))
    candidate = json.loads(read_limited(candidate_path, MAX_METADATA))
    if not isinstance(baseline.get("types"), dict) or not isinstance(candidate.get("types"), dict):
        raise ValueError("ABI JSON must contain an object named 'types'")
    differences = []
    names = sorted(set(baseline["types"]) | set(candidate["types"]))
    for name in names:
        old, new = baseline["types"].get(name), candidate["types"].get(name)
        if old is None or new is None:
            differences.append({"type": name, "field": "presence", "baseline": old is not None, "candidate": new is not None})
            continue
        for key in ("size", "alignment", "fields"):
            if old.get(key) != new.get(key):
                differences.append({"type": name, "field": key, "baseline": old.get(key), "candidate": new.get(key)})
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--vmlinux", required=True, type=Path)
    parser.add_argument("--system-map", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--abi-baseline", required=True, type=Path)
    parser.add_argument("--abi-candidate", required=True, type=Path)
    parser.add_argument("--require-config", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    checks, errors = [], []
    try:
        for label, path in (("Image", args.image), ("vmlinux", args.vmlinux), ("System.map", args.system_map), (".config", args.config)):
            if not path.is_file():
                raise ValueError(f"Missing input: {label}")
        image_head = args.image.open("rb").read(64)
        image_ok = len(image_head) >= 64 and struct.unpack_from("<I", image_head, 56)[0] == 0x644D5241
        checks.append({"name": "arm64_image_magic", "status": "PASS" if image_ok else "FAIL", "bytes": args.image.stat().st_size})
        if not image_ok:
            errors.append("Image lacks the AArch64 Linux Image magic at offset 0x38")

        elf = args.vmlinux.open("rb").read(20)
        elf_ok = len(elf) >= 20 and elf[:4] == b"\x7fELF" and elf[4] == 2 and elf[5] == 1 and struct.unpack_from("<H", elf, 18)[0] == 183
        checks.append({"name": "vmlinux_elf64_aarch64", "status": "PASS" if elf_ok else "FAIL"})
        if not elf_ok:
            errors.append("vmlinux is not a little-endian ELF64 AArch64 file")

        config_bytes = read_limited(args.config, MAX_METADATA)
        config = {}
        for line in config_bytes.decode("utf-8", "replace").splitlines():
            match = re.fullmatch(r"CONFIG_([A-Z0-9_]+)=(.*)", line)
            if match:
                config["CONFIG_" + match.group(1)] = match.group(2)
            else:
                match = re.fullmatch(r"# CONFIG_([A-Z0-9_]+) is not set", line)
                if match:
                    config["CONFIG_" + match.group(1)] = "n"
        requirements = ["CONFIG_ARM64=y"] + args.require_config
        config_failures = [item for item in requirements if "=" not in item or config.get(item.split("=", 1)[0]) != item.split("=", 1)[1]]
        checks.append({"name": "required_config", "status": "PASS" if not config_failures else "FAIL", "required": requirements, "failed": config_failures})
        if config_failures:
            errors.append("Required configuration entries do not match")

        map_size = args.system_map.stat().st_size
        map_ok = map_size > 0 and map_size <= MAX_MAP
        checks.append({"name": "system_map_present_bounded", "status": "PASS" if map_ok else "FAIL", "bytes": map_size, "sha256": sha256(args.system_map) if map_ok else None, "consistency_with_vmlinux": "NOT_CHECKED"})
        if not map_ok:
            errors.append("System.map is empty or exceeds the bounded audit size")

        abi_diffs = check_abi(args.abi_baseline, args.abi_candidate)
        checks.append({"name": "abi_layout", "status": "PASS" if not abi_diffs else "FAIL", "differences": abi_diffs})
        if abi_diffs:
            errors.append("ABI layout differs from the supplied baseline")
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError, struct.error) as exc:
        errors.append(str(exc))
        checks.append({"name": "input_validation", "status": "FAIL"})
    result = {"schema": "kernel-qa.v1", "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors, "scope": "Static input audit only; no build, symbol-map regeneration, boot, or runtime test."}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
