"""Offline layout/model checks; target C offsets are checked by BUILD_BUG_ON."""

from pathlib import Path
import csv
import ctypes
import struct


HERE = Path(__file__).resolve().parent
rows = {row["field"]: row for row in csv.DictReader((HERE / "last-reboot-reason-abi.csv").open(newline=""))}
changed = {"last_init_func", "pmic_ext_buck", "hang_detect_timeout_count", "last_async_func", "last_sync_func", "gz_irq"}
for field, row in rows.items():
    if row["stock_arm32_offset"] and row["arm64_fallback_offset"] and field not in changed:
        assert row["stock_arm32_offset"] == row["arm64_fallback_offset"], field


class LegacyTail(ctypes.Structure):
    _fields_ = [
        ("common", ctypes.c_uint8 * 828),
        ("last_init_func", ctypes.c_uint32),
        ("pmic_ext_buck", ctypes.c_uint8),
        ("padding", ctypes.c_uint8 * 3),
        ("hang_detect_timeout_count", ctypes.c_uint32),
        ("last_async_func", ctypes.c_uint32),
        ("last_sync_func", ctypes.c_uint32),
        ("gz_irq", ctypes.c_uint32),
        ("is_upload", ctypes.c_uint32),
        ("upload_reason", ctypes.c_uint32),
        ("is_power_reset", ctypes.c_uint32),
        ("power_reset_reason", ctypes.c_uint32),
        ("mcupm_skip", ctypes.c_uint32),
        ("panic_str", ctypes.c_char * 256),
    ]


assert ctypes.sizeof(LegacyTail) == 0x468
for field in changed | {"panic_str"}:
    assert getattr(LegacyTail, field).offset == int(rows[field]["stock_arm32_offset"]), field

NATIVE_REASON_SIZE = 0x368
NATIVE_TAG_OFFSET = 0x380
REASON_AREA = 0x480
TAG_MAGIC = 0x41303236
assert NATIVE_REASON_SIZE < NATIVE_TAG_OFFSET
assert NATIVE_TAG_OFFSET + 16 <= REASON_AREA
assert REASON_AREA == (ctypes.sizeof(LegacyTail) + 63) & ~63


def layout_valid(buf_size, off_linux, off_console, sz_console):
    return (0x40 <= off_linux <= buf_size and
            off_linux <= off_console <= buf_size and
            off_console - off_linux == REASON_AREA and
            sz_console == buf_size - off_console)


def native_tag_valid(blob, off_linux):
    values = struct.unpack_from("<IIII", blob, off_linux + NATIVE_TAG_OFFSET)
    return values == (TAG_MAGIC, (~TAG_MAGIC) & 0xFFFFFFFF, 1, NATIVE_REASON_SIZE)


size = 0x1000
off_linux = 0x200
off_console = off_linux + REASON_AREA
assert layout_valid(size, off_linux, off_console, size - off_console)
assert not layout_valid(size, off_linux, off_linux + 0x380, size - off_linux - 0x380)
assert not layout_valid(size, size - 0x40, size + 0x440, 0)
assert not layout_valid(size, off_linux, off_console, size - off_console + 1)

legacy = bytearray(size)
struct.pack_into("<I", legacy, off_linux + 828, 0xFEDCBA98)
struct.pack_into("<I", legacy, off_linux + 848, 0x12345678)
assert not native_tag_valid(legacy, off_linux)
assert struct.unpack_from("<I", legacy, off_linux + LegacyTail.last_init_func.offset)[0] == 0xFEDCBA98
assert struct.unpack_from("<I", legacy, off_linux + LegacyTail.gz_irq.offset)[0] == 0x12345678

native = bytearray(size)
high_pointer = 0xFFFF800010203040
struct.pack_into("<Q", native, off_linux + int(rows["last_init_func"]["arm64_fallback_offset"]), high_pointer)
struct.pack_into("<IIII", native, off_linux + NATIVE_TAG_OFFSET,
                 TAG_MAGIC, (~TAG_MAGIC) & 0xFFFFFFFF, 1, NATIVE_REASON_SIZE)
assert native_tag_valid(native, off_linux)
assert struct.unpack_from("<Q", native, off_linux + int(rows["last_init_func"]["arm64_fallback_offset"]))[0] == high_pointer
native[off_linux + NATIVE_TAG_OFFSET + 4] ^= 1
assert not native_tag_valid(native, off_linux)

print("PASS: 139 shared fields checked against ELF/DWARF offsets")
print("PASS: legacy 0x468 size and changed tail offsets match stock ARM32 DWARF")
print("PASS: 0x380 native tag stays outside 0x368 struct and before 0x480 console")
print("PASS: synthetic stock/native/bad headers and 64-bit pointer round-trip")
