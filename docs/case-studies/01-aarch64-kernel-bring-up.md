# AArch64 Kernel Bring-Up on an ARM32 Samsung Source Tree

## Technical scope

This case covers the first successful AArch64 kernel build from the Samsung Galaxy A02 SM-A022F kernel source context, and the architecture-specific build failures encountered while adapting an ARM32-oriented tree. It does not cover device boot or Android userspace.

## Executive summary

The source package and stock Android 11 configuration targeted 32-bit ARM. Building with ARCH=arm64 exposed several different classes of defects: a literal quoted MediaTek platform directory in generated build paths, file-local pstore/RAM-console symbols needed by other objects, and Samsung debug code selected by the MT6739 SoC symbol even when compiled for AArch64. The build eventually produced an AArch64 Image and ELF64 vmlinux, and an independent clean-output build also exited successfully. The working configuration kept watchdog/SPM support linked and left SEC_DEBUG disabled. These results prove buildability within that configuration only; they do not prove runtime safety or byte-for-byte reproducibility.

## Device, kernel, and toolchain context

- Device target: Samsung Galaxy A02 SM-A022F, reference firmware A022FXXS3BWH1.
- Kernel: Samsung 4.14.186 source package; stock build instructions target ARCH=arm.
- Experimental build: ARCH=arm64, MTK_PLATFORM=mt6739, Android Clang r383902 with Android GCC/binutils 4.9, isolated output directories.
- The saved ARM64 configuration enables CONFIG_ARM64 and CONFIG_COMPAT. It selects MT6739 platform drivers and the common MediaTek watchdog interfaces.

## Original problem and symptoms

The first AArch64 configuration was not a routine compiler-target switch. Architecture assumptions were distributed across make variables, exported symbols, Kconfig selections, and Samsung debug code.

Retained diagnostics include:

- Make reported “No rule to make target” for paths containing the literal directory component "mt6739". The log shows this for MMC and WLAN platform objects.
- A source build with SEC_DEBUG selected reached ARM32-specific pt_regs fields such as ARM_pc/ARM_lr and ARM instructions such as mrc p15, which the AArch64 assembler rejected.
- Earlier link attempts reported unresolved persistent_ram_vmap and ram_console_buffer symbols; a separate log shows the static/non-static declaration conflict for persistent_ram_vmap.
- An earlier mksysmap run was recorded as a Bus error. A read-only streaming check of the retained partial-output archive later found two .tmp_vmlinux* members with all bytes zero: 279,886,016 bytes (SHA-256 `0d42da0dd5abaa13a57d6c1567e14863fe3bd4d4d37ed6e0599558122ae0807c`) and 280,934,616 bytes (SHA-256 `1e88f8d7fa3567f1fc8d5c56f14fae2a7e945f929249738b6a97811e160cba3f`). The .tmp_kallsyms1.S and .tmp_kallsyms1.o members are zero-length (empty-file SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). This confirms malformed generated intermediates in that archived snapshot. It does not establish which process reported Bus error, why the files were zero-filled, or that the source tree was damaged. See the [archived temporary-file measurements](../evidence/mksysmap-zero-temporaries-2026-10-22.json).

## Investigation and root cause

The evidence separates several causes rather than assigning every failure to “ARM64 incompatibility.”

1. **Confirmed build-variable defect:** the MTK_PLATFORM comparison allowed quotation marks to become part of a directory name. Patch 0003 corrects the Makefile comparison without removing the affected drivers.
2. **Confirmed symbol-visibility defect:** persistent_ram_vmap and ram_console_buffer were file-local in the selected configuration although other linked code referenced them. Patches 0001 and 0002 adjust linkage for the SEC_DEBUG-disabled build. Their runtime mapping and persistent-memory behavior were not changed or validated.
3. **Confirmed architecture-selection defect:** SEC_DEBUG branches use CONFIG_MACH_MT6739 as a proxy for architecture. The same SoC symbol is set by the AArch64 build, so ARM32 register layouts and assembly were selected. The successful kernel configuration therefore leaves SEC_DEBUG disabled; later guard patches are candidates, not proof of an enabled SEC_DEBUG build.
4. **Watchdog/SPM configuration:** the retained final configuration selects MTK watchdog common and v2 interfaces, and the successful link contains the relevant watchdog and SPM symbols. This is evidence that the chosen build configuration links these paths, not that the watchdog or SPM works on the device.
5. **mksysmap diagnosis remains uncertain:** the archived partial-output snapshot confirms invalid zero-filled temporary ELF intermediates, but the original complete failure log, emitting process, and historical disk state are unavailable. Disk exhaustion, interrupted output, I/O failure, tool failure, and other causes remain unproven. No source corruption is established.

## Failed attempts and applied engineering work

The retained logs show successive source/configuration attempts with compile and link failures. The evidence supports the specific repairs above; it does not preserve a reliable one-to-one explanation for every failed attempt. The successful baseline used a separate experimental source copy, the corrected platform comparison, the symbol-linkage patches, the supported watchdog selections, and SEC_DEBUG disabled. The original Samsung source was left unchanged.

## Validation and verified results

- The successful Image is identified as a Linux ARM64 boot executable; vmlinux is ELF64/AArch64; System.map was regenerated from vmlinux and matches the recorded map digest.
- CONFIG_COMPAT and core MT6739 options appear in the saved configuration; selected SPM, watchdog, RAM-console, and pstore symbols are present in the link evidence.
- A clean-output make Image run exited 0. The saved .config and System.map hashes matched the earlier output, while Image and vmlinux hashes differed. A binary comparison reported 11,443 differing Image bytes. The possible build-banner contribution was not fully isolated, so bit-for-bit reproducibility is not claimed.
- The raw Image was larger than the recorded 24 MiB boot partition; compression and bootloader behavior were investigated separately.

## Follow-up Reproduction Investigation — 2026-10-22

This read-only follow-up tested whether the saved first-build versus clean-build hash difference could be attributed only to the kernel build banner or debug metadata. No kernel rebuild was run. The preserved artifacts were checked against their SHA-256 manifests, their ELF64/AArch64 section tables were compared, and same-address/same-size `.text` function ranges were compared byte-for-byte with the repository tool [`compare_elf_text_ranges.py`](../../scripts/compare_elf_text_ranges.py). The saved [JSON comparison output](../evidence/kernel-build-diff-2026-10-22.json) records the input ELF sizes and hashes, section measurements, and each changed range's address, size, and differing-byte count without local paths or binary contents.

| Section | Address | Earlier / clean size | Changed bytes | Changed fraction |
| --- | ---: | ---: | ---: | ---: |
| `.text` | `0xffffff8008080800` | 15,355,120 / 15,355,120 | 656 | 0.004272% |
| `.rodata` | `0xffffff8009000000` | 7,755,858 / 7,755,858 | 9,871 | 0.127272% |
| `.init.text` | `0xffffff8009800000` | 446,528 / 446,528 | 367 | 0.082190% |
| `.init.data` | `0xffffff80098c4000` | 74,752 / 74,752 | 120 | 0.160531% |
| `.data` | `0xffffff8009a00000` | 1,557,224 / 1,557,224 | 421 | 0.027035% |

The equal-sized `Image` files differ at 11,443 bytes in 1,874 runs. For a reproducible count, the comparison script accepts ELF64 little-endian AArch64 files, selects defined nonzero-size STT_FUNC symbols assigned to `.text`, and deduplicates their ranges by exact (st_value, st_size). It compares only ranges present with the same address and size in both files. Under that explicit rule, 203 of 58,754 common unique ranges contain changed bytes. The companion output also reports a separate symbol-identity count using (name, st_value, st_size); it is not interchangeable with the range count. The previous 198 of 58,279 statement is withdrawn because its extraction and filtering rule was not retained and it is not reproducible from the saved method. The observed differences establish changed machine-code bytes, not a functional regression, corruption, or which build is correct. The script's synthetic tests cover aliases, range deduplication, and rejection of non-AArch64 ELF input.

Debug metadata also differs substantially: `.debug_line` grows by 96,927 bytes, `.debug_info` by 99 bytes, and `.debug_str` by 3 bytes. The complete clean `vmlinux` is 97,032 bytes larger. The embedded Linux version strings show build number `#3` versus `#1` and timestamps `14:27:54` versus `15:34:51` EEST on 2026-10-18. The visible Clang/LLD identity strings agree, but the actual compiler and linker executables were not hashed.

The saved `.config` and `System.map` match. The clean build used a new output directory, but both builds reference the same mutable source-tree path. No paired source commit/diff, applied-patch manifest, compiler/linker binary hashes, generated-header manifest, or complete environment snapshot was retained. Stale incremental objects, source/patch changes, toolchain binaries, and generated build inputs therefore remain possible causes. None is established. The current preserved build artifacts are valid and match their manifests; no truncation or corruption is confirmed in this pair. Separately, a partial-output archive has now been verified to contain the zero-filled intermediates described above; this finding does not attribute their cause or establish source corruption.

The later Minimal AArch64 boot candidate is a separate artifact: its 11,742,494-byte gzip kernel decompresses to SHA-256 `631581ff73a88a4b9a53b69a43660678c0e714ab5009d37212e9add583543131`, matching the saved later GPU-guard `Image`, not either image in the comparison pair. The boot candidate itself remains local and untested on the device.

**Follow-up status:** verified build differences; bit-for-bit reproducibility failed for this pair; cause remains **INCONCLUSIVE**. No synthetic failure was run because it would not distinguish the missing historical inputs. Raw binaries and build logs remain local; the public record contains only hashes and derived measurements.

## Remaining limitations

SEC_DEBUG is still disabled. The RAM-console ABI differs between the stock ARM32 and experimental ARM64 builds. The clean-build machine code was not bit-identical. The build did not test modules, SPM/watchdog runtime, the device tree handoff, LK, Android, or phone boot.

## Lessons learned

- A successful cross-architecture link can require both correct Kconfig selections and source fixes; neither should be replaced with broad driver disablement.
- SoC identity is not an architecture test. Architecture-specific Samsung code needs explicit ARM32/AArch64 guards.
- Symbol visibility fixes prove linkage, not persistence or safe memory ownership.
- Repeating a build with the same configuration is useful, but matching config and symbol maps do not establish identical machine code.

## Evidence references

Published references: [kernel QA](../kernel-qa.md), [saved ARM64 configuration](../../config/a02-arm64.config), and patches [0001](../../patches/0001-pstore-export-persistent-ram-vmap.patch), [0002](../../patches/0002-export-ram-console-buffer.patch), and [0003](../../patches/0003-compare-mtk-platform-unquoted.patch). The [comparison tool](../../scripts/compare_elf_text_ranges.py), its [synthetic tests](../../tests/test_compare_elf_text_ranges.py), and the [comparison output](../evidence/kernel-build-diff-2026-10-22.json) define and preserve the function-range count. The [archived temporary-file measurements](../evidence/mksysmap-zero-temporaries-2026-10-22.json) record the prior invalid outputs. The detailed status of SEC_DEBUG and RAM-console compatibility is in [STATUS](../../STATUS.md).

Retained local-only evidence includes arm64-resume-relink-20261018.log, arm64-build-20261018-a02-pinctrl-fixed.log, clean-rebuild.log, and the corresponding build notes. Those logs were not copied into the public repository because they include local build paths and are large raw diagnostics. The clean-rebuild log SHA-256 recorded during this review is 28923c77c5652b35deb1a2f18ab8791e75b31892f5698893010fb0b00d94aafe.

## Current status

**PARTIALLY RESOLVED — BUILD/COMPILE ONLY.** An AArch64 kernel and a separate clean rebuild completed; SEC_DEBUG, RAM-console runtime compatibility, bit-identical reproducibility, and all device runtime behavior remain open or unverified.

