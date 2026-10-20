# SM-A022F ARM64 RAM-console compatibility candidate

This is a bounded offline step. The phone and official firmware were not touched. Samsung's original kernel source and all earlier ARM64 outputs were preserved.

## Changes in a separate source copy

Source copy: a separate local WSL clone named `kernel-source-arm64-ram-compat` (created from the prior experimental clone without its build outputs). Read-only directory comparison against that prior clone found only these three changed source files, plus known dangling `bat_setting` symlink warnings:

- [`0008-ram-console-legacy-aware-arm64-layout.patch`](../patches/candidates/0008-ram-console-legacy-aware-arm64-layout.patch) changes `mtk_ram_console.c` only when `CONFIG_ARM64=y` and `CONFIG_SEC_DEBUG` is off. The stock ARM32 console offset of 0x480 from `off_linux` is retained. The native ARM64 reboot-reason struct remains 0x368 bytes with its three `unsigned long` address fields at 64-bit width. A 16-byte magic/inverse/version/size tag is placed at offset 0x380, outside the native struct and before the console section. A copy of the previous record is classified by validated header bounds and tag; six tail fields with shifted offsets are read from the stock ARM32 layout when the tag is absent. The initial buffer is copied before the region is cleared, as in Samsung's implementation.
- [`0009-sec-debug-guard-arm32-register-save.patch`](../patches/candidates/0009-sec-debug-guard-arm32-register-save.patch) makes four `CONFIG_MACH_MT6739` branches in `sec_debug.c` choose the ARM32 assembly only when `CONFIG_ARM64` is absent.
- [`0010-sec-debug-select-aarch64-register-layout.patch`](../patches/candidates/0010-sec-debug-select-aarch64-register-layout.patch) applies the same architecture guard to the register-layout type in `sec_debug.h`.

The patches do **not** enable `CONFIG_SEC_DEBUG`, change the kernel `.config`, or prove its fixed physical buffers safe. The `#ifndef CONFIG_MACH_MT6739` task-dump branch is left unchanged because it is not the ARM32 register-save assembly path.

## Evidence

| Check | Result | Evidence and limit |
|---|---|---|
| Stock and native RAM layout measurement | PASS | Stock ARM32 `last_reboot_reason` is 0x468; current native ARM64 is 0x368; both previous header types are 0x40. [`last-reboot-reason-abi.csv`](evidence/last-reboot-reason-abi.csv) captures offsets extracted from vmlinux DWARF. |
| Legacy tail layout in the compiled ARM64 object | PASS | Target `BUILD_BUG_ON` checks size 0x468 and offsets 828, 848, 872. The saved object DWARF independently reports 0x468 and the expected offsets; its sanitized excerpt is in [`arm64-legacy-tail-object-dwarf.txt`](evidence/arm64-legacy-tail-object-dwarf.txt). |
| Legacy/new format model and bounds | PASS (offline model) | [`check_ram_compat_layout.py`](evidence/check_ram_compat_layout.py) passed synthetic stock, native, corrupt-marker, short-buffer, and 64-bit pointer round-trip checks. It compares all 139 shared field offsets from the two original DWARF records. This model is not a boot test. |
| Isolated target object compilation | PASS | `make -j4 drivers/misc/mediatek/ram_console/mtk_ram_console.o` exited 0 in 31.66s, producing ELF64/AArch64 object SHA256 `424fdae7c978f76af2cb83f741b910cc8c668d64f3ad2c54e2e3e912c0275d78`; prior object SHA256 `6d40f39221eb304466e8a096a434ef4a0fde4f113dfb7fd18fc9c628d01f1877`. Config SHA256 remained `cf28ea2d10ed44db355ef454ab9cc395b0ae2c82d870e396cba1bc8a197ef354`. The log has 13 host/Kconfig warnings, no target-file warnings or errors. |
| Full Image link or device boot | UNVERIFIED | No full Image was built for this candidate. No flash or runtime test was performed. |
| SEC_DEBUG on ARM64 | UNVERIFIED | Guard patches are reviewed source changes only; `CONFIG_SEC_DEBUG` stayed off, so `sec_debug.c` was not built. Memory reservations at 0x4B800000/0x4B810000, record ABI, and bootloader ownership remain unresolved. |

The object build command and raw log are retained in the separate local work area; a [sanitized log](evidence/ram-compat-object-build.log) is packaged here. The object and config checksums are recorded above. Earlier clean Image and GPU 0007 Image manifests were rechecked successfully after this work.

## Merge gate

Patch 0008 is a **candidate**, not a default boot image change. The 0x380 tag lies in bytes that stock ARM32 uses for `panic_str`; detection uses a four-word signature, but no stock crash RAM sample was available to exercise a real record. LK, TEE, Samsung AEE, and any other reader of this reserved region have not been proven to tolerate native 64-bit address fields or the tag. The reserved-memory address and size also need confirmation in the boot DT and LK handoff. Until those checks and a separately approved device test, mark persistent RAM compatibility **UNVERIFIED at runtime** and leave SEC_DEBUG disabled.
