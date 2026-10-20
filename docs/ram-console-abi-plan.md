# Persistent RAM console ABI repair plan

This is an offline implementation plan for the SM-A022F ARM64 experiment. It does not modify the Samsung source, firmware, or the phone. The clean and GPU patched kernels have **not** been booted.

## Proven mismatch

DWARF in the stock ARM32 `out/vmlinux` and independent ARM64 `out-arm64-a02-qa/vmlinux` shows:

| Type | Stock ARM32 | Current ARM64 | ARM64 Samsung header if `SEC_DEBUG` enabled |
|---|---:|---:|---:|
| `ram_console_buffer` header | 0x40 | 0x40 | 0x40 |
| `last_reboot_reason` | 0x468 (1128) | 0x368 (872) | 0x478 (1144) |
| `ALIGN(sizeof(last_reboot_reason), 64)` | 0x480 | 0x380 | 0x480 |

The current ARM64 configuration disables `CONFIG_SEC_DEBUG`, so `mtk_ram_console.c` uses a shorter fallback struct. `ram_console_init()` at lines 600–605 sets `off_console = off_linux + ALIGN(sizeof(struct last_reboot_reason), 64)` and then clears the new region. This moves the console section 0x100 bytes earlier than stock. The previous log reader at lines 523–533 accepts old console data only when the old header's `off_console` matches the current `sizeof()` calculation, so stock-format logs can be rejected even when their header is otherwise valid.

The field-offset CSV, [field-offset CSV](evidence/last-reboot-reason-abi.csv), was extracted from the two ELF/DWARF files using [comparison script](evidence/compare_ram_console_dwarf.py); the raw debug dumps are also saved. The 139 fields shared by stock and ARM64 fallback have identical offsets until the three `unsigned long` address fields near the end. Stock ARM32 places `last_init_func` at 828, `last_async_func` at 840, `last_sync_func` at 844, and `gz_irq` at 848. ARM64 places them at 832, 848, 856, and 864. The stock struct then includes six Samsung fields absent from the fallback, including a 256-byte `panic_str`. Turning `SEC_DEBUG` on would restore those fields but retain 64-bit `unsigned long` widths, so the layout is still different.

## Implementation sequence

1. **Define explicit persistent formats.** Add a separate `legacy_arm32_last_reboot_reason` with fixed-width fields and explicit padding to reproduce the stock 0x468-byte format. Keep the ARM64 writer's native 64-bit address fields in a distinct versioned format rather than silently truncating kernel pointers to 32 bits. Use compile-time `BUILD_BUG_ON` or `static_assert` for total size and `offsetof` at the boundary fields listed above. Keep the 0x40-byte `ram_console_buffer` header stable.
2. **Read old records according to their stored offsets and format.** Validate signature, stored section bounds, alignment, and lengths before touching data. Decode stock ARM32 records with the legacy layout. Do not require `old.off_console == old.off_linux + ALIGN(sizeof(current_arm64_struct), 64)`. Preserve any good previous record in memory before initializing the current region.
3. **Choose a new ARM64 format only after checking the bootloader and vendor AEE consumers.** If they parse this region, a compatible version tag or a separate reserved area is required. A naive larger struct may overwrite neighboring reserved memory or confuse LK/TEE. The official DTB/DTBO reserved-memory map and the stock header should be checked together.
4. **Add offline tests for both layouts.** Build synthetic stock-format headers and records, validate bounds and decoding, exercise malformed offsets, and compare resulting offsets to the stock DWARF table. Build and inspect the ARM64 object/DWARF to verify its chosen layout. A cold-boot RAM-preservation test remains impossible without a separately approved device test.

## Status and limit

The ABI mismatch is **FAIL**. The repair is **UNVERIFIED** and is not part of the current images. Address fields are recorded through `aee_rr_rec_last_{init,async,sync}_func(unsigned long)` in `mtk_ram_console.c` around lines 2404–2428; forcing these storage fields to `uint32_t` would lose high bits of AArch64 pointers. The previous memory contents and LK/TEE ownership cannot be confirmed from a compile-only test.
