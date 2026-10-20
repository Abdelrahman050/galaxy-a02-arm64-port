#!/usr/bin/env python3
"""Read-only structural comparison of two flattened device trees (DTBs)."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

FDT_MAGIC = 0xD00DFEED
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9
MAX_DTB = 64 * 1024 * 1024


def align4(value):
    return (value + 3) & ~3


def cstring(data, start, limit):
    if start < 0 or start >= limit:
        raise ValueError("string offset out of bounds")
    end = data.find(b"\0", start, limit)
    if end < 0:
        raise ValueError("unterminated string")
    return data[start:end].decode("utf-8", "strict"), end + 1


def parse_dtb(path):
    data = path.read_bytes()
    if len(data) < 40 or len(data) > MAX_DTB:
        raise ValueError(f"{path.name}: invalid or oversized DTB")
    header = struct.unpack_from(">10I", data, 0)
    magic, total, off_struct, off_strings, off_reserve, version, last_comp, _, size_strings, size_struct = header
    if magic != FDT_MAGIC or total > len(data) or total < 40 or version < 16 or last_comp > version:
        raise ValueError(f"{path.name}: invalid FDT header")
    for off, size, label in ((off_struct, size_struct, "structure"), (off_strings, size_strings, "strings")):
        if off < 40 or size > total or off + size > total:
            raise ValueError(f"{path.name}: {label} block out of bounds")
    if off_reserve < 40 or off_reserve >= total:
        raise ValueError(f"{path.name}: reservation map offset out of bounds")

    reservations, pos = [], off_reserve
    reserve_end = off_struct
    while pos + 16 <= reserve_end:
        address, size = struct.unpack_from(">QQ", data, pos)
        pos += 16
        if address == 0 and size == 0:
            break
        reservations.append((address, size))
    else:
        raise ValueError(f"{path.name}: unterminated reservation map")

    strings = data[off_strings:off_strings + size_strings]
    struct_end = off_struct + size_struct
    pos = off_struct
    stack, nodes, properties = [], set(), {}
    saw_end = False
    while pos + 4 <= struct_end:
        token = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        if token == FDT_BEGIN_NODE:
            name, pos = cstring(data, pos, struct_end)
            pos = align4(pos)
            if pos > struct_end:
                raise ValueError(f"{path.name}: node name exceeds structure block")
            parent = stack[-1] if stack else ""
            full = "/" if not parent and not name else (parent.rstrip("/") + "/" + name if parent else "/" + name)
            stack.append(full)
            nodes.add(full)
        elif token == FDT_END_NODE:
            if not stack:
                raise ValueError(f"{path.name}: unmatched FDT_END_NODE")
            stack.pop()
        elif token == FDT_PROP:
            if not stack or pos + 8 > struct_end:
                raise ValueError(f"{path.name}: malformed property header")
            length, nameoff = struct.unpack_from(">II", data, pos)
            pos += 8
            if nameoff >= len(strings) or pos + length > struct_end:
                raise ValueError(f"{path.name}: property bounds invalid")
            propname, _ = cstring(strings, nameoff, len(strings))
            key = (stack[-1], propname)
            if key in properties:
                raise ValueError(f"{path.name}: duplicate property {key}")
            properties[key] = data[pos:pos + length]
            pos = align4(pos + length)
        elif token == FDT_NOP:
            continue
        elif token == FDT_END:
            if stack:
                raise ValueError(f"{path.name}: unclosed nodes")
            saw_end = True
            break
        else:
            raise ValueError(f"{path.name}: unknown structure token 0x{token:x}")
    if not saw_end or "/" not in nodes:
        raise ValueError(f"{path.name}: missing FDT_END or root node")
    return {"nodes": nodes, "properties": properties, "reservations": reservations, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def value_summary(raw):
    if len(raw) <= 128 and raw.endswith(b"\0"):
        try:
            value = raw[:-1].decode("utf-8")
            if all(ch.isprintable() for ch in value):
                return {"string": value}
        except UnicodeDecodeError:
            pass
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--allow-property", action="append", default=[], metavar="/node:property")
    args = parser.parse_args()
    try:
        left, right = parse_dtb(args.reference), parse_dtb(args.candidate)
        missing_nodes = sorted(left["nodes"] - right["nodes"])
        extra_nodes = sorted(right["nodes"] - left["nodes"])
        left_keys, right_keys = set(left["properties"]), set(right["properties"])
        missing_props = sorted(left_keys - right_keys)
        extra_props = sorted(right_keys - left_keys)
        changed = []
        for key in sorted(left_keys & right_keys):
            if left["properties"][key] != right["properties"][key]:
                changed.append({"node": key[0], "property": key[1], "reference": value_summary(left["properties"][key]), "candidate": value_summary(right["properties"][key]), "allowed": f"{key[0]}:{key[1]}" in args.allow_property})
        reserve_equal = left["reservations"] == right["reservations"]
        disallowed = [item for item in changed if not item["allowed"]]
        passed = not missing_nodes and not extra_nodes and not missing_props and not extra_props and not disallowed and reserve_equal
        result = {"schema": "fdt-diff.v1", "status": "PASS" if passed else "FAIL", "reference": {"sha256": left["sha256"], "bytes": left["bytes"]}, "candidate": {"sha256": right["sha256"], "bytes": right["bytes"]}, "missing_nodes": missing_nodes, "extra_nodes": extra_nodes, "missing_properties": [f"{n}:{p}" for n, p in missing_props], "extra_properties": [f"{n}:{p}" for n, p in extra_props], "changed_properties": changed, "reservation_map_equal": reserve_equal, "reference_reservations": left["reservations"], "candidate_reservations": right["reservations"], "scope": "Structural comparison only; does not apply overlays, validate driver semantics, or prove boot/runtime compatibility."}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if passed else 1
    except (OSError, ValueError, UnicodeError, struct.error) as exc:
        print(json.dumps({"schema": "fdt-diff.v1", "status": "FAIL", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
