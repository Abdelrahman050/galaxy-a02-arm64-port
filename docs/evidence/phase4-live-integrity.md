# Phase 4 — Live Source and Toolchain Integrity Verification

**Assessment date:** 2026-10-23
**Target:** Samsung Galaxy A02 SM-A022F, MT6739 family
**Scope:** Read-only inspection of the Samsung kernel source archive, baseline and experimental source trees, build outputs, and the installed WSL toolchain.

## Summary

An approved live WSL collection completed successfully. The results strengthen the project’s source and toolchain evidence and support a **CONDITIONAL GO for a new, isolated ARM64 `Image` build** after a fresh preflight. No build or patch application was performed as part of this audit. **FLASH READINESS remains BLOCKED / NO-GO.**

This report distinguishes four different claims: matching file hashes establish integrity only within the scanned scope; structurally valid artifacts establish offline format checks; compile/link success establishes a build result; neither proves bootloader acceptance, AArch64 runtime handoff, Android ARM64, or `arm64-v8a` execution.

## Source findings

- The baseline tree had **77,161 regular files** totaling 1,039,860,582 bytes. Their hashes matched the corresponding regular-file entries streamed from Samsung’s open-source kernel archive. The archive was not extracted during this check. This does not authenticate Samsung’s origin or prove complete tree identity outside the regular-file comparison.
- Baseline and experimental trees had 77,161 common regular-file paths; 77,157 hashes matched, four files differed, and no baseline file was missing. The differences are the MTK platform comparison in `drivers/misc/mediatek/eccci/fsm/Makefile`, PowerVR changes in `mtk_mfgsys.c`, the RAM-console export, and the pstore export. These are source deltas, not evidence of corruption.
- The experimental tree also contains `mtk_ram_console.c.orig`, which is byte-identical to the baseline source file. It is a retained backup copy and is not a named input to the recorded kernel build.
- All **36 symbolic links in each tree** were inspected. The link paths and target strings match across trees; 34 resolve. Two legacy TB8168 battery include links under `arch/arm/boot/dts/bat_setting/` are broken in both trees. A read-only search found no references to those includes in the ARM64 MediaTek DTS directory. No links were changed.

The source archive comparison is scoped to regular files and the inspected link targets. It is not a semantic review of every source file, a functional-equivalence claim, or proof that every historical build used these exact inputs. See the published [source-tree difference summary](source-tree-diff.txt) for the four known file deltas.

## Toolchain and patch state

The configured Android Clang **11.0.1 (r383902)** and LLD **11.0.1** were present and their payload hashes matched retained values. The measured SHA-256 values were `c3d0831fad23a7a73d41b66aad9cb7dc5f8fc09943dc90d473b06bd2521fa907` for Clang and `c8b3b0e4d4be9c9098034388d54bca4116fee62ae0751f7ee1ce24401495dc57` for LLD. The AArch64 GNU binutils helpers (`as`, `ar`, `ranlib`, `ld`, `nm`, `objcopy`, `objdump`, `readelf`, `size`, `strip`, and `elfedit`) were present as GNU binutils 2.27.0.20170315 and fingerprinted. In particular, the measured `objcopy` and `strip` hashes were `50c3126734475459b3ee045345906ce875a352eda372be2fb26799785695d322` and `520f159a98271d1e4a8440bf0e7a7b3a4bceae962ca8ee4252b15600cfb017a6`.

The recorded `Image` build command selects Clang and LLD explicitly, so missing AArch64 GCC/G++ wrappers are not a blocker for that command. Historical process-execution traces were not retained; current tool identity does not prove every historical helper binary was identical or which helpers were invoked in each run.

The local collection contains 25 patch-file entries and 13 unique patch contents. Hunk comparison against actual source—not just `git apply --check`—found uniquely matching postimages for five patch contents: pstore export, RAM-console export, the MTK platform comparison, optional PowerVR power-index locking, and the GED power-state guard. Two overlapping PowerVR patch candidates contain mixed postimage matches and context drift, so their individual application is only partially verified. The legacy RAM-console-layout, two SEC_DEBUG, and codec-label patches match preimages in the experimental source. Two Device Tree patches target candidate files absent from these kernel source roots. This text-matching check neither applied patches nor proves that one patch uniquely introduced each line.

## Build outputs and readiness

The four inspected experimental ARM64 output directories contain a 28,323,856-byte ARM64 `Image`, little-endian AArch64 ELF64 `vmlinux`, a structurally valid `System.map`, and the saved ARM64 configuration. The observed artifacts passed their format checks and matched retained local snapshots. The output inventories remain marked **INCOMPLETE** because the scanner did not follow each output directory’s `source` link; absent `Image.gz` is not a failure for an `Image` target. These results do not establish that the image boots or that the artifacts are bit-for-bit reproducible.

**Build Readiness: CONDITIONAL GO** for a controlled `Image` build only. Before starting, recheck free space and the source, configuration, and tool hashes; use fresh, separate output directories and the saved QA configuration; preserve full logs; and compare the resulting `Image`, `vmlinux`, map, configuration, and ELF sections. Do not clean or reuse historical outputs. This status is not build authorization.

**FLASH READINESS: BLOCKED / NO-GO.** LK/AVB acceptance, LK-to-K64 runtime handoff, early `/init` execution, USB-ACM observation, and Odin recovery after a failed boot remain unverified. No image was flashed and no phone was accessed during this audit.

## Evidence references

- [Reproducibility notes](../reproducibility.md)
- [Kernel QA](../kernel-qa.md)
- [Flash readiness](../flash-readiness.md)
- [Source-tree difference summary](source-tree-diff.txt)

The detailed local manifests and raw collection JSON are not included in the public repository because they expose unnecessary machine-specific inventory and are not needed to substantiate this scoped summary.
