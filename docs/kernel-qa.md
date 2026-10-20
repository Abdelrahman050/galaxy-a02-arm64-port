# SM-A022F AArch64 kernel QA (phase 2)

Date: 2026-10-18. Firmware reference: A022FXXS3BWH1. All checks below are offline; no device boot or flashing was performed. The original Samsung source and official firmware remain unmodified.

## Evidence and status

| Criterion | Status | Evidence / limit |
|---|---|---|
| Existing ARM64 build artifacts are internally well formed | PASS | `Image` is a 4K-page AArch64 boot image with magic `0x644d5241`; `vmlinux` is ELF64/AArch64; `System.map` regenerated from `vmlinux` with the Android cross-`nm` matches byte-for-byte (SHA256 `99be309e7e59b89d3cf5eb296d279b34d453fa6403c562ab6350bbbece86f5b2`). |
| 32-bit userspace compatibility and MT6739 core configuration | PASS (configuration/linkage) | `CONFIG_ARM64=y`, `CONFIG_COMPAT=y`, `CONFIG_COMPAT_BINFMT_ELF=y`, `CONFIG_MACH_MT6739=y`, `CONFIG_PINCTRL_MT6739=y`; SPM (`mt_spm_init`), MTK watchdog (`mtk_wdt_probe`, `mtk_wdt_init`), RAM console init and pstore symbols are linked. Runtime functionality remains unverified. |
| Samsung SEC_DEBUG feature parity with stock ARM32 | FAIL | Stock ARM32 enables `SEC_DEBUG`, LAST_KMSG, AUTO_COMMENT, INIT_EXIT_PANIC and SOFTDOG; ARM64 config explicitly disables `SEC_DEBUG` and therefore its dependent features. Directly enabling it would select ARM32 register layout and `mrc p15` / `r0` assembly under `CONFIG_MACH_MT6739` even for ARM64; architecture guards and reserved-memory/ABI review are required. |
| Persistent RAM console ABI parity | FAIL | DWARF shows `ram_console_buffer` header is 0x40 bytes on both architectures, but active `last_reboot_reason` is 0x468 bytes in stock ARM32 and 0x368 bytes in current ARM64. `off_console` uses `ALIGN(sizeof(last_reboot_reason),64)`, shifting the Linux console section by 0x100 bytes. Existing reboot logs cannot be assumed compatible. |
| PowerVR GPU DVFS pointer correctness | PASS (compile/link); runtime UNVERIFIED | Four compiled calls in the inherited `mtk_mfgsys.c` pass a 32-bit device index to APIs requiring `PVRSRV_DEVICE_NODE *`. Independent experimental patches 0004–0006 corrected the calls and rebuilt the object and Image. The four `-Wint-conversion` diagnostics fell to zero; device DVFS operation still needs a test. |
| Independent clean ARM64 rebuild | PASS (compile), byte-for-byte FAIL | Separate output `out-arm64-a02-qa`, full log `clean-rebuild.log`, `-j4`; copied prior `.config`, `olddefconfig` produced an empty diff. Image, vmlinux and System.map were produced with exit 0. `.config` and System.map match the first build; Image/vmlinux hashes differ. Prior output is untouched. |
| Boot on SM-A022F | UNVERIFIED | No phone test. Correct DTB, LK handoff, boot memory placement and ramdisk are separate gates. |

## Existing artifact measurements

- Prior `Image` SHA256: `921396f81cbda87b541ec7160678ec405301597209b55a0802a53030d7027759`; size 28,323,856 bytes.
- Prior `vmlinux` SHA256: `0a8d95fb88d5facae1d115528575f9c192308f30a0a0287775d15ca083cc355e`; ELF64/AArch64 executable.
- Prior `System.map` SHA256: `99be309e7e59b89d3cf5eb296d279b34d453fa6403c562ab6350bbbece86f5b2`; 119,763 lines.
- Prior `.config` SHA256: `cf28ea2d10ed44db355ef454ab9cc395b0ae2c82d870e396cba1bc8a197ef354`.
- ARM64 header has `text_offset=0x80000`, `image_size=0x01fc8000` (33,325,056 bytes), flags `0xA`. The declared memory footprint exceeds file size due runtime sections such as BSS; placement in LK's RAM layout is unverified.
- Independent clean `Image` SHA256: `2050aa93b92e9298927ceae8a5d0659189cd81f9cba1480f72a7277460518146`; `vmlinux`: `283ffd9f4f7dd1623ffe1239ede82cdfc16cbfceaad3746932fbf274515b61e4`. The Image is the same 28,323,856 bytes as the first but differs at 11,443 byte positions; the first difference is at offset 50,037. Identical `.config` and System.map show a repeatable compile and symbol set, not identical machine code. Different Linux build banners are one likely contributor, but no complete binary-difference attribution was done.
- Clean build started 2026-10-18 12:18:23 UTC and ended 12:35:06 UTC, elapsed 16m32.83s; `make -j4 Image` exit 0, peak RSS about 1.55 GiB. Exact command and environment are in `clean_rebuild.sh` and `clean-rebuild.log`. `clean-rebuild-SHA256SUMS` verifies all four artifacts.
- PowerVR 0004–0006 experimental `Image` SHA256: `c817c0b9a4690bcecd5f851e9c239347e4278a3ccdf15ea5c684ce857838924b`; `vmlinux`: `fdd93f592fd6e79c0d3e83992255bd736cc6f9415b8cb573ec8fb00345666883`. The incremental isolated build took 1m50s and exited 0. `.config` and System.map remain identical to the clean build. The affected `mtk_mfgsys.o` hash changed from `f376228e05b7caa4240dd58d56425cedb21b91c414f50f4d3ba3ef94e7ab6a1b` to `36ab0eef13cbbdd98e9d91051e47c1dd32926e1ae6db9b0e820c9261c55bccc0`; 47 other warnings remain in this object, with zero `-Wint-conversion` diagnostics. `gpu-fix-SHA256SUMS` verifies the new artifacts.
- PowerVR 0007 follow-up experimental `Image` SHA256: `631581ff73a88a4b9a53b69a43660678c0e714ab5009d37212e9add583543131`; `vmlinux`: `9ebfafb8d3c66a238b61443fe28ed831cd2b36ed9735c6c034e1b1ceaf3f4966`; `System.map`: `a845aec5a9c4c6dc218e30cdafb025302370e444254e3cb285da14044ac429c6`. The fourth isolated output `out-arm64-a02-gpufix2` rebuilt and linked in 2m31.95s with exit 0 and the same `.config`. `mtk_mfgsys.o` SHA256 is `f3caeed7bd647f5d355254e58dd447994650acce585f055a1f9038fc62b34a4f`; its warning count fell from 47 to 46 because the redundant unused variable was removed. No `-Wint-conversion`, undefined-symbol or section-mismatch diagnostics appear in `gpu-commit-guard-build.log`. `gpu-commit-guard-SHA256SUMS` verifies all four files; the 0004–0006 output hashes also still verify. This remains a compile-only result.
- Official PIT boot partition is 24 MiB (25,165,824 bytes), so the raw 28,323,856-byte Image cannot fit. A read-only derived `gzip -n -1` proof is `Image.gz`, 11,760,269 bytes, SHA256 `dedd7cbb9b2f0bcb21cd7e60f92968071921c2d7c59cd2fddde28bcf8a257ab4`, and `gzip -t` passes. Compression and AArch64 handoff in this device's LK are unverified.

## Patch and runtime review

1. `0001-pstore-export-persistent-ram-vmap.patch` changes only linkage of `persistent_ram_vmap` from file-local to global when `CONFIG_SEC_DEBUG` is off. Its mapping algorithm is unchanged; `System.map` confirms a single global symbol. It does not supply a reserved-memory DT description or prove pstore works. The inherited implementation returns `vaddr + offset` without first checking `vmap` for NULL, so allocation failure needs later hardening if the path is exercised.
2. `0002-export-ram-console-buffer.patch` changes only linkage of the RAM console pointer from file-local to global with `CONFIG_SEC_DEBUG` off. The initialization and buffer layout are unchanged; link succeeds without a duplicate symbol. Runtime persistence depends on the correct reserved region. Existing `ram_console_size()` dereferences the pointer without a NULL guard before some callers check it; this was present before the patch.
3. `0003-compare-mtk-platform-unquoted.patch` corrects a Makefile comparison for unquoted `MTK_PLATFORM=mt6739`; it does not disable drivers.
4. `0004-powervr-use-device-node-in-dvfs.patch` is a prepared experimental correction for the four active PowerVR DVFS callsites at original lines 422, 428, 442 and 453. It uses the existing `MTKGetRGXDevNode()` helper and a NULL check, preserving GPU/DVFS. It also converts the fifth callsite at original line 635 inside inactive `MTK_CAL_POWER_INDEX` and removes the now-unused index helper.
5. `0005-powervr-handle-unknown-power-state.patch` separately checks `PVRSRVGetDevicePowerState` return values before using `ePowerState`. In the active path it pairs a successful PreClock call with PostClock when power state is unavailable, then exits without applying a DVFS change. The optional path unlocks and exits.
6. `0006-powervr-optional-power-index-node-lock.patch` separately passes the device-node pointer to PowerLock/Unlock in the inactive `MTK_CAL_POWER_INDEX` routine; this conditional code cannot be validated by the current configuration and needs a dedicated build if enabled later.
7. `0007-powervr-guard-ged-power-state.patch` addresses a separate active `MTKCommitFreqIdx` path that also ignored failure from `PVRSRVGetDevicePowerState`. It returns `IMG_FALSE` through `pbCommited` on failure and balances a successful PreClock with PostClock. It compiled and linked in fourth output `out-arm64-a02-gpufix2`; it is not part of the 0004–0006 Image above. Runtime lock behavior remains unverified.

The original Samsung `mtk_mfgsys.c` and the unpatched experiment copy had the same SHA256 `a0472e1cbc4c92fed711eb7248738e3cba11ca4eed169585d15c839d74eb26e6`, so the GPU calls are inherited source defects. The affected object was built as `.../mtk_mfgsys.o` (248,296 bytes). `PVRSRVGetDevicePowerState` immediately dereferences `psDeviceNode->psPowerDev`; a small index passed as a pointer can fault when DVFS is invoked. Link success does not make this path safe.

Samsung debug source uses `#ifdef CONFIG_MACH_MT6739` in `drivers/samsung/debug/sec_debug.c` around ARM32 register-save assembly, and `include/linux/sec_debug.h` uses the same SoC symbol for an ARM32 register structure. Since the ARM64 config also sets `CONFIG_MACH_MT6739`, enabling SEC_DEBUG without architecture-specific guards is invalid. Its init also maps fixed physical addresses 0x4B800000 and 0x4B810000; any restoration requires the official reserved-memory layout and LK ownership semantics.

DWARF evidence is saved in [stock ARM32 DWARF](evidence/stock-arm32-last-reboot-reason.dwarf.txt), [ARM64 DWARF](evidence/arm64-last-reboot-reason.dwarf.txt), [stock RAM-console DWARF](evidence/stock-arm32-ram-console-buffer.dwarf.txt) and [ARM64 RAM-console DWARF](evidence/arm64-ram-console-buffer.dwarf.txt). Stock `last_reboot_reason` is 0x468 bytes (1128), ARM64's fallback definition in `mtk_ram_console.c` is 0x368 (872), and the ARM64 SEC_DEBUG header's unused version is 0x478 (1144). Both 0x468 and 0x478 round up to 0x480 at 64-byte alignment, while 0x368 rounds to 0x380. The header itself is 0x40 on both. `unsigned long` fields in the SEC_DEBUG definition also change width across architectures. This is a concrete shared-memory ABI gap, not a linkage error from patches 0001/0002.

The precise field-offset comparison is in [field-offset CSV](evidence/last-reboot-reason-abi.csv), generated from full DWARF field dumps with [comparison script](evidence/compare_ram_console_dwarf.py). [RAM-console ABI repair plan](ram-console-abi-plan.md) describes a versioned, bounds-checked repair. Padding the short struct is insufficient: three serialized `unsigned long` fields move on ARM64 and the fallback omits six Samsung fields.

## Warning triage

- **Critical in the unpatched build:** PowerVR pointer/index mismatch in compiled GPU DVFS code has a direct invalid-pointer fault path. Patches 0004–0006 remove the four type warnings in a linked Image; runtime correctness is unverified. Another active PowerVR state-read path is addressed separately by patch 0007.
- **Configuration debt:** `TZDEV` and `ION_FD2PHYS` Kconfig definitions have inconsistent bool/tristate types. Current config keeps `CONFIG_TZDEV=y` and `CONFIG_TEEGRIS_TEE_SUPPORT=y`, but secure-world ABI is not validated.
- **Mostly inherited source diagnostics:** unused variables/functions, C90 declaration placement, `const` on function return type, duplicate typedefs, GPU pointer printed with `%x`, and host-build OpenSSL deprecations. They occur in source files unchanged from Samsung; stock ARM32 build suppressed many warnings via `KCFLAGS=-w`, so identical warning counts across architectures cannot be claimed.
- **Potential secondary issues:** misleading indentation in USB gadget cleanup code; inspect if USB failures arise after boot. Missing `kperfmon` Android framework files are logged while `CONFIG_KPERFMON` is off; previous build still produced an image.
- **modpost:** `make Image` runs the `vmlinux.o` built-in section-mismatch stage in `scripts/link-vmlinux.sh` via `Makefile.modpost`. It produced no target section-mismatch or undefined-symbol diagnostics. It did not request `.ko` modules, so module modpost/runtime is unverified. The lone warning in host `scripts/mod/modpost.c:811` about discarded `const` is a host compiler warning, not a target module failure.

## Source and scope audit

Read-only `diff -qr` between the original Samsung tree and the current experimental tree, excluding output directories, found only the expected source differences: `drivers/misc/mediatek/eccci/fsm/Makefile`, `drivers/misc/mediatek/ram_console/mtk_ram_console.c`, `fs/pstore/ram_core.c`, and the experimentally patched PowerVR file. A preserved `mtk_ram_console.c.orig` exists only in the experimental tree. The original tree has dangling `bat_setting` symlinks, so the directory comparison reports their missing targets; no separate SPM/Watchdog source delta was found. See [source-tree comparison](evidence/source-tree-diff.txt).

No result here proves boot, graphics operation or arm64-v8a application support. The raw Image also exceeds the official 24 MiB boot partition; LK decompression and runtime memory placement are separate, unverified gates.

## Bounded RAM-console follow-up

An isolated candidate patch now preserves the stock `0x480` console offset and
adds a guarded parser for the ARM32 legacy reason tail while keeping ARM64
pointer fields 64-bit. Its `mtk_ram_console.o` compiled as AArch64 with the
same `.config` and passed the offline layout model; it has **not** been linked
into a full Image or tested against real persistent RAM. SEC_DEBUG remains
disabled; the accompanying ARM64 register-save guards are review-only under
the current config. See the [candidate QA](ram-compat-candidate-qa.md) and
[`patches/candidates/`](../patches/candidates/). The earlier FAIL status above
still describes every built Image preserved in this package.
