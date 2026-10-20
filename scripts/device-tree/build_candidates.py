#!/usr/bin/env python3
"""Stage minimal A02 ARM64 DTBs from read-only official merged DTBs.

This script never writes to the Samsung source or firmware-analysis inputs.
It changes only the PMU compatible string, preserving every other FDT node
and property byte-for-byte at the semantic level. A boot test is still needed.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import difflib
import re
from pathlib import Path


SOURCE = Path(os.environ["A02_FDT_INPUT"]) if "A02_FDT_INPUT" in os.environ else None
STAGE = Path(os.environ["A02_FDT_OUTPUT"]) if "A02_FDT_OUTPUT" in os.environ else None
REVISIONS = {
    "r00": "a02-eur-open-00-merged.dtb",
    "r01": "a02-eur-open-01-merged.dtb",
    "r06": "a02-eur-open-01b-merged.dtb",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_fdt(path: Path) -> tuple[dict[str, dict[str, bytes]], dict[str, int]]:
    blob = path.read_bytes()
    fields = struct.unpack_from(">10I", blob)
    magic, total, struct_off, strings_off, memreserve_off, version, _, _, strings_len, struct_len = fields
    if magic != 0xD00DFEED or version < 16 or total > len(blob):
        raise ValueError(f"Invalid FDT header: {path}")
    strings = blob[strings_off : strings_off + strings_len]
    memreserve = []
    reserve_pos = memreserve_off
    while reserve_pos + 16 <= struct_off:
        address, size = struct.unpack_from(">QQ", blob, reserve_pos)
        reserve_pos += 16
        if (address, size) == (0, 0):
            break
        memreserve.append([address, size])
    nodes: dict[str, dict[str, bytes]] = {}
    stack: list[str] = []
    pos = struct_off
    while pos < struct_off + struct_len:
        tag = struct.unpack_from(">I", blob, pos)[0]
        pos += 4
        if tag == 1:  # FDT_BEGIN_NODE
            end = blob.index(b"\0", pos)
            stack.append(blob[pos:end].decode("utf-8"))
            pos = (end + 4) & ~3
            nodes["/" + "/".join(stack[1:])] = {}
        elif tag == 2:  # FDT_END_NODE
            stack.pop()
        elif tag == 3:  # FDT_PROP
            length, name_off = struct.unpack_from(">II", blob, pos)
            pos += 8
            end = strings.index(b"\0", name_off)
            name = strings[name_off:end].decode("utf-8")
            value = blob[pos : pos + length]
            pos = (pos + length + 3) & ~3
            nodes["/" + "/".join(stack[1:])][name] = value
        elif tag == 4:  # FDT_NOP
            continue
        elif tag == 9:  # FDT_END
            break
        else:
            raise ValueError(f"Invalid FDT token {tag}: {path}")
    return nodes, {"version": version, "node_count": len(nodes),
                   "property_count": sum(map(len, nodes.values())),
                   "memreserve": memreserve}


def text_prop(nodes: dict[str, dict[str, bytes]], node: str, prop: str) -> str:
    return nodes[node][prop].rstrip(b"\0").decode("utf-8", errors="replace")


def compare_properties(original: dict[str, dict[str, bytes]],
                       candidate: dict[str, dict[str, bytes]]) -> list[str]:
    changes = []
    for node in sorted(set(original) | set(candidate)):
        left, right = original.get(node, {}), candidate.get(node, {})
        for prop in sorted(set(left) | set(right)):
            if left.get(prop) != right.get(prop):
                changes.append(f"{node}:{prop}")
    return changes


def main() -> None:
    if SOURCE is None or not SOURCE.is_dir():
        raise ValueError(f"Missing read-only FDT input directory: {SOURCE}")
    if STAGE is None:
        raise ValueError("Set A02_FDT_OUTPUT to a separate writable staging directory")
    source = SOURCE.resolve()
    stage = STAGE.resolve()
    if source == stage or source in stage.parents or stage in source.parents:
        raise ValueError("FDT output must not overlap the read-only input tree")
    if stage.exists() and any(stage.iterdir()):
        raise ValueError("FDT output must be new or empty; refusing to overwrite existing files")
    STAGE.mkdir(parents=True, exist_ok=True)
    audit = {"description": "Official A02 merged DTB plus ARMv8 PMU compatible only",
             "boot_tested": False, "revisions": {}}
    manifest = []
    for revision, filename in REVISIONS.items():
        original_path = SOURCE / filename
        original_sha = sha256(original_path)
        candidate_path = STAGE / f"a02-arm64-{revision}-candidate.dtb"
        candidate_path.write_bytes(original_path.read_bytes())
        before, before_stats = read_fdt(original_path)
        if text_prop(before, "/pmu", "compatible") != "arm,cortex-a7-pmu":
            raise ValueError(f"Unexpected original PMU for {revision}")
        subprocess.run(["fdtput", "-t", "s", str(candidate_path),
                        "/pmu", "compatible", "arm,armv8-pmuv3"], check=True)
        after, after_stats = read_fdt(candidate_path)
        changes = compare_properties(before, after)
        if changes != ["/pmu:compatible"]:
            raise ValueError(f"Unexpected changes in {revision}: {changes}")
        if before_stats["memreserve"] != after_stats["memreserve"]:
            raise ValueError(f"FDT memreserve changed in {revision}")
        if sha256(original_path) != original_sha:
            raise ValueError(f"Original changed unexpectedly: {original_path}")
        dts_path = STAGE / f"a02-arm64-{revision}-candidate.dts"
        original_dts_path = STAGE / f"official-{revision}-roundtrip.dts"
        original_decompile = subprocess.run(["dtc", "-I", "dtb", "-O", "dts",
                                             "-o", str(original_dts_path),
                                             str(original_path)],
                                            capture_output=True, text=True)
        original_log = original_decompile.stdout + original_decompile.stderr
        (STAGE / f"official-{revision}-dtc.log").write_text(original_log)
        if original_decompile.returncode != 0:
            raise RuntimeError(f"DTC decompile failed for official {revision}")
        decompile = subprocess.run(["dtc", "-I", "dtb", "-O", "dts",
                                    "-o", str(dts_path), str(candidate_path)],
                                   capture_output=True, text=True)
        candidate_log = decompile.stdout + decompile.stderr
        (STAGE / f"a02-arm64-{revision}-dtc.log").write_text(candidate_log)
        if decompile.returncode != 0:
            raise RuntimeError(f"DTC decompile failed for {revision}")
        normalize_log = lambda value: re.sub(r"^.*?\.dts:", "DTS:", value,
                                             flags=re.MULTILINE)
        if normalize_log(original_log) != normalize_log(candidate_log):
            raise ValueError(f"New or changed DTC warnings in {revision}")
        patch = difflib.unified_diff(
            original_dts_path.read_text().splitlines(keepends=True),
            dts_path.read_text().splitlines(keepends=True),
            fromfile=f"a/official-merged-a02-{revision}.dts",
            tofile=f"b/a02-arm64-{revision}-candidate.dts")
        (STAGE / f"0001-a02-arm64-{revision}-pmu-compat.patch").write_text("".join(patch))
        rebuilt_path = STAGE / f"a02-arm64-{revision}-rebuilt.dtb"
        rebuild = subprocess.run(["dtc", "-I", "dts", "-O", "dtb",
                                  "-o", str(rebuilt_path), str(dts_path)],
                                 capture_output=True, text=True)
        (STAGE / f"a02-arm64-{revision}-rebuild.log").write_text(
            rebuild.stdout + rebuild.stderr)
        if rebuild.returncode != 0:
            raise RuntimeError(f"DTS rebuild failed for {revision}")
        rebuilt, rebuilt_stats = read_fdt(rebuilt_path)
        if compare_properties(after, rebuilt) or after_stats["memreserve"] != rebuilt_stats["memreserve"]:
            raise ValueError(f"DTS roundtrip changed the FDT meaning for {revision}")
        reserved = [path for path in before if path.startswith("/reserved-memory/")
                    and path.count("/") == 2]
        audit["revisions"][revision] = {
            "original": filename,
            "original_sha256": original_sha,
            "candidate_sha256": sha256(candidate_path),
            "rebuilt_sha256": sha256(rebuilt_path),
            "original_pmu": text_prop(before, "/pmu", "compatible"),
            "candidate_pmu": text_prop(after, "/pmu", "compatible"),
            "changed_properties": changes,
            "bootargs_preserved": before["/chosen"]["bootargs"] == after["/chosen"]["bootargs"],
            "trusty_preserved": all(before.get(path) == after.get(path) for path in before
                                    if path == "/trusty" or path.startswith("/trusty/")),
            "teegris_preserved": before.get("/teegris") == after.get("/teegris"),
            "reserved_memory_nodes_preserved": all(before.get(path) == after.get(path)
                                                   for path in before if path == "/reserved-memory"
                                                   or path.startswith("/reserved-memory/")),
            "reserved_memory_children": sorted(reserved),
            "original_fdt_stats": before_stats,
            "candidate_fdt_stats": after_stats,
            "rebuilt_semantically_identical": True,
            "dtc_warning_lines_inherited": len(original_log.splitlines()),
            "dtc_log": f"a02-arm64-{revision}-dtc.log",
        }
        manifest.append(f"{sha256(candidate_path)}  {candidate_path.name}")
    (STAGE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (STAGE / "SHA256SUMS").write_text("\n".join(manifest) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
