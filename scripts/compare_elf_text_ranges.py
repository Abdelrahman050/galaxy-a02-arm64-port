#!/usr/bin/env python3
"""Read-only ELF64/AArch64 section and .text function-range comparison.

The report is deterministic: input paths are not serialized, records are sorted,
and timestamps are omitted. Function identities are unique
(name, st_value, st_size) tuples for defined STT_FUNC symbols in .text.
Address ranges are separately deduplicated as (st_value, st_size), so aliases
cannot silently change the range denominator. No ELF is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")
SYMBOL = struct.Struct("<IBBHQQ")
SHT_SYMTAB = 2
STT_FUNC = 2
SHN_UNDEF = 0
MACHINE_AARCH64 = 183
SECTIONS = (".text", ".rodata", ".init.text", ".init.data", ".data", ".notes")


class InputError(ValueError):
    pass


def checked_slice(data: mmap.mmap, offset: int, size: int, label: str) -> memoryview:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise InputError(f"{label} exceeds file bounds")
    return memoryview(data)[offset : offset + size]


def c_string(table: bytes, offset: int, label: str) -> str:
    if offset < 0 or offset >= len(table):
        raise InputError(f"{label} string offset is out of bounds")
    end = table.find(b"\0", offset)
    if end < 0:
        raise InputError(f"{label} string is not NUL-terminated")
    return table[offset:end].decode("utf-8", "replace")


@dataclass(frozen=True)
class Section:
    name: str
    index: int
    address: int
    offset: int
    size: int
    link: int
    entry_size: int


class ELF:
    def __init__(self, path: Path):
        self.path = path
        self.handle = path.open("rb")
        try:
            self.data = mmap.mmap(self.handle.fileno(), 0, access=mmap.ACCESS_READ)
        except Exception:
            self.handle.close()
            raise
        self.sections: list[Section] = []
        self.by_name: dict[str, Section] = {}
        self.text_functions: set[tuple[str, int, int]] = set()
        try:
            self._parse()
        except Exception:
            self.data.close()
            self.handle.close()
            raise

    def close(self) -> None:
        self.data.close()
        self.handle.close()

    def _parse(self) -> None:
        if len(self.data) < ELF_HEADER.size:
            raise InputError(f"{self.path.name}: truncated ELF header")
        fields = ELF_HEADER.unpack_from(self.data, 0)
        ident, e_type, machine, version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = fields
        if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
            raise InputError(f"{self.path.name}: expected ELF64 little-endian version 1")
        if machine != MACHINE_AARCH64:
            raise InputError(f"{self.path.name}: expected ELF machine AArch64 (183), found {machine}")
        if shentsize != SECTION_HEADER.size or shnum == 0 or shstrndx >= shnum:
            raise InputError(f"{self.path.name}: unsupported or incomplete section table")
        checked_slice(self.data, shoff, shentsize * shnum, "section table")
        raw_sections = [SECTION_HEADER.unpack_from(self.data, shoff + i * shentsize) for i in range(shnum)]
        shstr = raw_sections[shstrndx]
        shstr_data = checked_slice(self.data, shstr[4], shstr[5], "section-name table").tobytes()
        for index, raw in enumerate(raw_sections):
            name_off, stype, sflags, addr, offset, size, link, info, align, entsize = raw
            name = c_string(shstr_data, name_off, "section-name")
            if stype != 8:  # SHT_NOBITS has no bytes in the file.
                checked_slice(self.data, offset, size, f"section {name}")
            section = Section(name, index, addr, offset, size, link, entsize)
            self.sections.append(section)
            if name and name not in self.by_name:
                self.by_name[name] = section
        text = self.by_name.get(".text")
        if text is None:
            raise InputError(f"{self.path.name}: .text section is missing")
        symtabs = [s for s in self.sections if raw_sections[s.index][1] == SHT_SYMTAB]
        if not symtabs:
            raise InputError(f"{self.path.name}: .symtab is missing; function comparison is unavailable")
        for symtab in symtabs:
            if symtab.entry_size < SYMBOL.size or symtab.entry_size == 0 or symtab.size % symtab.entry_size:
                raise InputError(f"{self.path.name}: malformed symbol table")
            if symtab.link >= len(self.sections):
                raise InputError(f"{self.path.name}: symbol string table index is invalid")
            strings_sec = self.sections[symtab.link]
            strings = checked_slice(self.data, strings_sec.offset, strings_sec.size, "symbol string table").tobytes()
            for pos in range(symtab.offset, symtab.offset + symtab.size, symtab.entry_size):
                st_name, st_info, st_other, st_shndx, st_value, st_size = SYMBOL.unpack_from(self.data, pos)
                if (st_info & 0x0F) != STT_FUNC or st_shndx != text.index or st_size == 0:
                    continue
                start = st_value - text.address
                if start < 0 or start + st_size > text.size:
                    continue
                name = c_string(strings, st_name, "symbol")
                if name:
                    self.text_functions.add((name, st_value, st_size))

    def bytes_at(self, section: Section, address: int, size: int) -> memoryview:
        relative = address - section.address
        if relative < 0 or relative + size > section.size:
            raise InputError(f"address range lies outside {section.name}")
        return checked_slice(self.data, section.offset + relative, size, section.name)

    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def changed_bytes(left: memoryview, right: memoryview) -> int:
    return sum(a != b for a, b in zip(left, right)) + abs(len(left) - len(right))


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def compare(left: ELF, right: ELF) -> dict:
    section_results = []
    for name in SECTIONS:
        a, b = left.by_name.get(name), right.by_name.get(name)
        if a is None and b is None:
            continue
        item = {"section": name, "earlier_present": a is not None, "later_present": b is not None}
        if a is not None:
            item["earlier"] = {"address": f"0x{a.address:x}", "size": a.size}
        if b is not None:
            item["later"] = {"address": f"0x{b.address:x}", "size": b.size}
        if a is not None and b is not None and a.address == b.address:
            common = min(a.size, b.size)
            count = changed_bytes(left.bytes_at(a, a.address, common), right.bytes_at(b, b.address, common))
            count += abs(a.size - b.size)
            item["changed_bytes_including_size_delta"] = count
            item["changed_fraction_of_larger_section"] = round(count / max(a.size, b.size), 9) if max(a.size, b.size) else 0.0
        else:
            item["byte_comparison"] = "not performed: section addresses differ or section is absent"
        section_results.append(item)

    common_symbols = left.text_functions & right.text_functions
    # Count function identity once per exact (name, address, size) tuple.
    changed_symbols = []
    for name, address, size in sorted(common_symbols):
        if changed_bytes(left.bytes_at(left.by_name[".text"], address, size), right.bytes_at(right.by_name[".text"], address, size)):
            changed_symbols.append((name, address, size))

    left_ranges = {(address, size) for _, address, size in left.text_functions}
    right_ranges = {(address, size) for _, address, size in right.text_functions}
    common_ranges = left_ranges & right_ranges
    changed_ranges = []
    for address, size in sorted(common_ranges):
        a = left.bytes_at(left.by_name[".text"], address, size)
        b = right.bytes_at(right.by_name[".text"], address, size)
        count = changed_bytes(a, b)
        if count:
            changed_ranges.append({
                "address": f"0x{address:x}",
                "size": size,
                "different_bytes": count,
            })

    result = {
        "format": "read-only ELF64 little-endian AArch64 comparison",
        "identity_rule": "unique defined STT_FUNC symbols in .text keyed by (name, st_value, st_size); same-address ranges are separately deduplicated by (st_value, st_size)",
        "inputs": {
            "earlier": {"size": len(left.data), "sha256": left.sha256()},
            "later": {"size": len(right.data), "sha256": right.sha256()},
        },
        "sections": section_results,
        "text_function_identity_comparison": {
            "earlier_unique_identities": len(left.text_functions),
            "later_unique_identities": len(right.text_functions),
            "matched_identities": len(common_symbols),
            "changed_matched_identities": len(changed_symbols),
        },
        "text_unique_address_range_comparison": {
            "earlier_unique_ranges": len(left_ranges),
            "later_unique_ranges": len(right_ranges),
            "matched_ranges": len(common_ranges),
            "changed_matched_ranges": len(changed_ranges),
            "changed_ranges": changed_ranges,
        },
        "interpretation_limit": "Different linked bytes are not by themselves evidence of a functional defect, corruption, or cause. This tool does not validate source, patch, toolchain, generated-input identity, or runtime behavior.",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("earlier", type=Path, help="earlier vmlinux ELF64/AArch64")
    parser.add_argument("later", type=Path, help="later vmlinux ELF64/AArch64")
    parser.add_argument("--output", type=Path, help="write deterministic JSON to this path; default is stdout")
    args = parser.parse_args()
    left = right = None
    try:
        left, right = ELF(args.earlier), ELF(args.later)
        report = compare(left, right)
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        if left is not None:
            left.close()
        if right is not None:
            right.close()


if __name__ == "__main__":
    raise SystemExit(main())
