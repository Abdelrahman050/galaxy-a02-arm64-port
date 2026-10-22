import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path


REPO_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_elf_text_ranges.py"
SCRIPT = REPO_SCRIPT if REPO_SCRIPT.is_file() else Path(__file__).with_name("compare_elf_text_ranges.py")
SPEC = importlib.util.spec_from_file_location("compare_elf_text_ranges", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_elf(path: Path, text: bytes, machine: int = 183) -> None:
    names = b"\0func_a\0func_b\0alias_a\0"
    shnames = b"\0.text\0.strtab\0.symtab\0.shstrtab\0"
    text_offset = 64
    str_offset = text_offset + len(text)
    sym_offset = (str_offset + len(names) + 7) & ~7
    symbols = [
        (0, 0, 0, 0, 0, 0),
        (1, 0x12, 0, 1, 0x1000, 4),
        (8, 0x12, 0, 1, 0x1004, 4),
        (15, 0x12, 0, 1, 0x1000, 4),
    ]
    sym_data = b"".join(struct.pack("<IBBHQQ", *entry) for entry in symbols)
    shstr_offset = sym_offset + len(sym_data)
    shoff = (shstr_offset + len(shnames) + 7) & ~7
    data = bytearray(shoff + 5 * 64)
    ident = b"\x7fELF" + bytes((2, 1, 1, 0, 0)) + bytes(7)
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 2, machine, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 5, 4)
    data[:64] = header
    data[text_offset : text_offset + len(text)] = text
    data[str_offset : str_offset + len(names)] = names
    data[sym_offset : sym_offset + len(sym_data)] = sym_data
    data[shstr_offset : shstr_offset + len(shnames)] = shnames
    headers = [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 1, 6, 0x1000, text_offset, len(text), 0, 0, 4, 0),
        (7, 3, 0, 0, str_offset, len(names), 0, 0, 1, 0),
        (15, 2, 0, 0, sym_offset, len(sym_data), 2, 1, 8, 24),
        (23, 3, 0, 0, shstr_offset, len(shnames), 0, 0, 1, 0),
    ]
    for index, entry in enumerate(headers):
        start = shoff + index * 64
        data[start : start + 64] = struct.pack("<IIQQQQIIQQ", *entry)
    path.write_bytes(data)


class CompareELFTests(unittest.TestCase):
    def test_counts_named_symbols_and_deduplicated_ranges_separately(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as temp:
            first = Path(temp) / "first.elf"
            second = Path(temp) / "second.elf"
            make_elf(first, b"AAAABBBBCCCCDDDD")
            make_elf(second, b"AABABBBBCCCCDDDD")
            left, right = MODULE.ELF(first), MODULE.ELF(second)
            try:
                result = MODULE.compare(left, right)
            finally:
                left.close()
                right.close()
            self.assertEqual(result["text_function_identity_comparison"]["matched_identities"], 3)
            self.assertEqual(result["text_function_identity_comparison"]["changed_matched_identities"], 2)
            ranges = result["text_unique_address_range_comparison"]
            self.assertEqual(ranges["matched_ranges"], 2)
            self.assertEqual(ranges["changed_matched_ranges"], 1)

    def test_rejects_non_aarch64_elf(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as temp:
            path = Path(temp) / "wrong-machine.elf"
            make_elf(path, b"AAAABBBBCCCCDDDD", machine=62)
            with self.assertRaises(MODULE.InputError):
                MODULE.ELF(path)


if __name__ == "__main__":
    unittest.main()
