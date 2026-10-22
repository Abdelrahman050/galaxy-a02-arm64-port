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
- An earlier mksysmap run was recorded as a Bus error, with temporary vmlinux outputs beginning with zero bytes. The retained narrative says storage exhaustion was a likely cause, but the original complete failure log is not available to prove that diagnosis.

## Investigation and root cause

The evidence separates several causes rather than assigning every failure to “ARM64 incompatibility.”

1. **Confirmed build-variable defect:** the MTK_PLATFORM comparison allowed quotation marks to become part of a directory name. Patch 0003 corrects the Makefile comparison without removing the affected drivers.
2. **Confirmed symbol-visibility defect:** persistent_ram_vmap and ram_console_buffer were file-local in the selected configuration although other linked code referenced them. Patches 0001 and 0002 adjust linkage for the SEC_DEBUG-disabled build. Their runtime mapping and persistent-memory behavior were not changed or validated.
3. **Confirmed architecture-selection defect:** SEC_DEBUG branches use CONFIG_MACH_MT6739 as a proxy for architecture. The same SoC symbol is set by the AArch64 build, so ARM32 register layouts and assembly were selected. The successful kernel configuration therefore leaves SEC_DEBUG disabled; later guard patches are candidates, not proof of an enabled SEC_DEBUG build.
4. **Watchdog/SPM configuration:** the retained final configuration selects MTK watchdog common and v2 interfaces, and the successful link contains the relevant watchdog and SPM symbols. This is evidence that the chosen build configuration links these paths, not that the watchdog or SPM works on the device.
5. **mksysmap diagnosis remains uncertain:** later artifact verification and the clean rebuild succeeded, but the available record does not establish whether the earlier Bus error came from a full disk, an incomplete linker output, or another cause.

## Failed attempts and applied engineering work

The retained logs show successive source/configuration attempts with compile and link failures. The evidence supports the specific repairs above; it does not preserve a reliable one-to-one explanation for every failed attempt. The successful baseline used a separate experimental source copy, the corrected platform comparison, the symbol-linkage patches, the supported watchdog selections, and SEC_DEBUG disabled. The original Samsung source was left unchanged.

## Validation and verified results

- The successful Image is identified as a Linux ARM64 boot executable; vmlinux is ELF64/AArch64; System.map was regenerated from vmlinux and matches the recorded map digest.
- CONFIG_COMPAT and core MT6739 options appear in the saved configuration; selected SPM, watchdog, RAM-console, and pstore symbols are present in the link evidence.
- A clean-output make Image run exited 0. The saved .config and System.map hashes matched the earlier output, while Image and vmlinux hashes differed. A binary comparison reported 11,443 differing Image bytes. The possible build-banner contribution was not fully isolated, so bit-for-bit reproducibility is not claimed.
- The raw Image was larger than the recorded 24 MiB boot partition; compression and bootloader behavior were investigated separately.

## Remaining limitations

SEC_DEBUG is still disabled. The RAM-console ABI differs between the stock ARM32 and experimental ARM64 builds. The clean-build machine code was not bit-identical. The build did not test modules, SPM/watchdog runtime, the device tree handoff, LK, Android, or phone boot.

## Lessons learned

- A successful cross-architecture link can require both correct Kconfig selections and source fixes; neither should be replaced with broad driver disablement.
- SoC identity is not an architecture test. Architecture-specific Samsung code needs explicit ARM32/AArch64 guards.
- Symbol visibility fixes prove linkage, not persistence or safe memory ownership.
- Repeating a build with the same configuration is useful, but matching config and symbol maps do not establish identical machine code.

## Evidence references

Published references: [kernel QA](../kernel-qa.md), [saved ARM64 configuration](../../config/a02-arm64.config), and patches [0001](../../patches/0001-pstore-export-persistent-ram-vmap.patch), [0002](../../patches/0002-export-ram-console-buffer.patch), and [0003](../../patches/0003-compare-mtk-platform-unquoted.patch). The detailed status of SEC_DEBUG and RAM-console compatibility is in [STATUS](../../STATUS.md).

Retained local-only evidence includes arm64-resume-relink-20261018.log, arm64-build-20261018-a02-pinctrl-fixed.log, clean-rebuild.log, and the corresponding build notes. Those logs were not copied into the public repository because they include local build paths and are large raw diagnostics. The clean-rebuild log SHA-256 recorded during this review is 28923c77c5652b35deb1a2f18ab8791e75b31892f5698893010fb0b00d94aafe.

## Current status

**PARTIALLY RESOLVED — BUILD/COMPILE ONLY.** An AArch64 kernel and a separate clean rebuild completed; SEC_DEBUG, RAM-console runtime compatibility, bit-identical reproducibility, and all device runtime behavior remain open or unverified.
