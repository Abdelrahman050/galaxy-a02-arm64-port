# Phase 5 — Controlled AArch64 Rebuild and WLAN Date Non-Determinism

**Investigation date:** 2026-10-23 UTC

**Target:** Samsung Galaxy A02 SM-A022F, MT6739 family

**Scope:** Two sequential `ARCH=arm64 MTK_PLATFORM=mt6739` kernel `Image` builds in fresh output directories. No boot-image packaging or device test.

## Technical background

The official SM-A022F software uses an ARM32 kernel and Android userspace. This project has an experimental AArch64 kernel configuration, but compile and link success cannot establish LK/K64 handoff, device boot, or Android ARM64 operation. An earlier pair of successful builds had different `Image` and `vmlinux` hashes without a complete record of paired source and tool inputs. The [historical kernel case study](../case-studies/01-aarch64-kernel-bring-up.md) keeps that earlier evidence separate. Phase 5 created a new controlled pair to test the current source and toolchain, not to rewrite the earlier history.

## Build environment and methodology

- The experimental Samsung-source copy, saved QA `.config`, Android Clang **11.0.1 r383902**, LLD **11.0.1**, and the 11 checked AArch64 GNU helpers matched their retained [Phase 4](phase4-live-integrity.md) fingerprints. The Clang SHA-256 was `c3d0831fad23a7a73d41b66aad9cb7dc5f8fc09943dc90d473b06bd2521fa907`; the LLD SHA-256 was `c8b3b0e4d4be9c9098034388d54bca4116fee62ae0751f7ee1ce24401495dc57`.
- Before the builds and after each build, the same 77,162 experimental regular files matched the retained Phase 4 manifest in membership, size, and hash. The 36 recorded symlink target strings also remained unchanged. This is a scoped source-integrity result, not proof of upstream authenticity or runtime correctness.
- Each run copied the same saved QA configuration into a **new, independent, empty output directory**, ran `olddefconfig`, then built `Image` with `make -j4`. Both selected `ARCH=arm64`, `MTK_PLATFORM=mt6739`, the same explicit Clang/LLD paths and AArch64 GNU prefix, and `ANDROID_MAJOR_VERSION=r`.
- `LC_ALL=C`, `TZ=UTC`, `KBUILD_BUILD_USER=phase5`, `KBUILD_BUILD_HOST=a02-controlled`, `KBUILD_BUILD_TIMESTAMP=2026-10-23T00:00:00Z`, `KBUILD_BUILD_VERSION=1`, and `SOURCE_DATE_EPOCH=1792713600` were fixed for both runs. Output directories were separate and outside the source tree; older outputs were neither reused nor cleaned.
- The local Phase 5 runner and full logs retain exact commands and selected environment. The repository's [generic build helper](../../scripts/build_kernel.py) is **not** the Phase 5 runner and has not been shown to recreate these exact outputs. Raw logs, manifests, binaries, and machine-specific paths remain local.

## Problems encountered

Both builds exited successfully, yet the `Image` and `vmlinux` bytes changed. Matching `.config` and `System.map` did not imply identical code. The observed differences include linked executable sections, so the discrepancy cannot be dismissed as ELF debug metadata alone. This is a reproducibility failure for this pair; differing bytes by themselves do not prove corruption or a functional fault.

Both logs contain 238 `warning:` occurrences. Neither records an `error:` diagnostic, undefined-symbol failure, or section-mismatch diagnostic; the build exits were zero. These warnings were not individually resolved by this documentation investigation. The host-compiler `modpost.c` const-qualifier warning is not a kernel `modpost` failure.

## Investigation and root-cause analysis

The source path `drivers/misc/mediatek/connectivity/wlan_drv_gen2/Makefile` defines `DRIVER_BUILD_DATE` by calling `date +%Y%m%d%H%M%S` and passes it as a compiler macro. `drivers/misc/mediatek/connectivity/wlan_drv_gen2/os/linux/gl_sys.c` uses that value in `sysCreateWifiVer`. The retained generated WLAN `.o.cmd` recorded `20261023011838` in Build 1 and `20261023012924` in Build 2. The linked ELF files respectively contain `2_0_1-20261023011838` and `2_0_1-20261023012924`.

At the same `sysCreateWifiVer` address, a disassembly spot-check found different AArch64 `adrp`/`add` operands referring to the changed `.rodata` string placement. Thus a changing clock-derived build input is **confirmed to enter the linked output** and to affect at least this machine-code reference. Fixed `KBUILD_BUILD_TIMESTAMP` and `KBUILD_BUILD_USER/HOST` affect the standard kernel build identity; they do not replace this driver Makefile's independent wall-clock call. `SOURCE_DATE_EPOCH` was set, but that Makefile expression does not read it. `TZ=UTC` controls timezone, not the advancing clock.

The two ELFs have the same section addresses and sizes. The read-only comparison measured:

| ELF section | Size in each build | Differing bytes |
| --- | ---: | ---: |
| `.text` | 15,355,120 | 967 |
| `.rodata` | 7,755,858 | 10,347 |
| `.init.text` | 446,528 | 371 |
| `.init.data` | 74,752 | 112 |
| `.data` | 1,557,224 | 492 |

The comparison also found changes in `.exit.text`, `.notes`, and debug sections. Under the published [ELF comparison tool's](../../scripts/compare_elf_text_ranges.py) unique `(address, size)` rule for defined nonzero-size `.text` function ranges, **361 of 58,754** matched ranges changed; 363 symbol identities changed under the tool's separate `(name, address, size)` rule. The WLAN date proves one source of non-determinism. It does **not** attribute all 361 changed ranges, the whole `.rodata` difference, or every changed `Image` byte to that single input. The earlier historical pair had different counts and inputs; its measurements must not be combined with this pair.

## Confirmed findings and validation results

| Claim | Result | Evidence boundary |
| --- | --- | --- |
| Two independent AArch64 `Image` builds | **SOLVED & VERIFIED — build scope** | `olddefconfig` and `Image` exited 0 twice. Both `Image` files are 28,323,856 bytes and identify as ARM64 boot executable Images; both `vmlinux` files parse as AArch64 ELF64. No phone boot was attempted. |
| Source and selected tool inputs stayed fixed | **SOLVED & VERIFIED — measured scope** | Pre-build and two post-build scans found no changed, missing, extra, unreadable, or unstable regular files; selected tool hashes matched Phase 4. Generated output contents are separate from this source scan. |
| `.config` and `System.map` | **SOLVED & VERIFIED — byte identity** | `.config`: 157,806 bytes, SHA-256 `cf28ea2d10ed44db355ef454ab9cc395b0ae2c82d870e396cba1bc8a197ef354` in both; `System.map`: 5,125,657 bytes, SHA-256 `c88c2084277b1d7351a415ebd68cecf0e192dd382bb2aae70032c23b6ef2b567` in both. |
| WLAN build-date input | **ROOT CAUSE CONFIRMED — scoped** | The Makefile's wall-clock expression, two generated command records, two embedded ELF strings, and `sysCreateWifiVer` reference change establish a real contributor to the changed link. |
| Whole-image byte reproducibility | **UNRESOLVED** | The two `Image` files differ at 12,298 byte positions; `vmlinux` differs at 90,563. Other changing inputs or linker effects have not been ruled out. |

The two `Image` SHA-256 values are `f68ec016d5fcb6d1630a509381f72b7009df28d12256c90a508977da18af5d8f` and `c4f2be0d118d398231ad22ffa2bd00f661e6fa7ffb1015351e6f39f51f05dcb7`. The corresponding `vmlinux` values are `01e3a3c398f7b19fa8e61f95dbbc63864dfa0ab2631b05b33b6675e27cc55383` and `c628f8294ac03619e1666b218f894c1988f53bb1d6446bac2dac8204529b521d`. These are identifiers for locally retained artifacts, **not downloadable or flashable files**.

## Proposed and verified solutions

**SOLVED & VERIFIED:** Fresh output directories, pinned standard KBUILD identity variables, fixed selected toolchain, and source scans made the two successful builds comparable. They did **not** make the binary outputs identical.

**FIX PROPOSED — NOT TESTED:** The smallest prospective intervention is to supply one explicitly chosen 14-digit UTC value as a GNU Make command-line variable, for example `DRIVER_BUILD_DATE=20261023000000`, on both otherwise identical build commands. A normal command-line assignment should override the Makefile's ordinary `=` assignment and preserve the current wall-clock behavior for builds that do not specify the variable. This propagation through the actual kernel build must be checked in the generated WLAN `.o.cmd` and linked version string before treating it as a fix. No kernel source patch or third build was made in Phase 5.

If the command-line value does not reach the driver, first trace variable propagation. A minimal **separately reviewed** source change to a conditional assignment (`?=`) could allow an explicitly exported environment value while retaining the existing default when unset; that alternative is also untested. A follow-up pair would need fresh output directories, fixed date and environment, source/tool preflight, artifact hashes, and section/range comparisons. Even a matching pair would demonstrate reproducibility only under those tested conditions; it would not prove phone boot.

## Remaining issues

- **UNRESOLVED:** How much of the remaining linked instruction and data difference is downstream of the WLAN string versus other generated inputs. No fixed-date comparison pair exists.
- **UNVERIFIED on hardware:** LK/AVB acceptance, K64 handoff, device-tree selection, early `/init` execution, and USB observation. The Phase 5 Images were not packaged into a new boot candidate.
- **BLOCKED / NO-GO for flashing:** The minimal proof still requires a frozen kernel input, corrected probe/initramfs, boot-header/DTB/DTBO and memory review, observation method, and recovery plan. See [flash readiness](../flash-readiness.md) and the [minimal boot-image record](../minimal-aarch64-boot-image.md). Full Android ARM64 userspace and `arm64-v8a` application execution remain future work.

## Lessons for other kernel developers

1. Pinning `KBUILD_BUILD_TIMESTAMP` does not control timestamps introduced independently by vendor Makefiles. Search generated `.cmd` files and linked strings when identical configurations produce different images.
2. Treat config, symbol-map, ELF metadata, executable sections, and raw `Image` as separate comparisons. Equal map addresses do not imply equal instruction bytes.
3. Preserve two clean output trees and the exact environment. Attribute a cause only to the scope demonstrated by command records and binary inspection; use a controlled fixed-input rebuild to test whether it explains the complete difference.
4. Keep compile/link, offline binary validation, device boot, and Android userspace claims separate. A reproducible kernel would still require bootloader, device-tree, observation, and recovery evidence before a phone test.

## Evidence provenance

The local Phase 5 record retains the full build/config logs, `file` and ELF section outputs, source scans, environment, artifact comparison, and changed-range analysis. To identify that retained record without publishing personal paths or binaries: `result.json` SHA-256 `4f38e8dab72dbd1d7f5f8bcd69fb866b08573743635c05e678b5ac588b65a66b`; Build 1 log SHA-256 `7780bd340225617b8a9a7c0fdff208076261618b0f349f8df034c70231cd745a`; Build 2 log SHA-256 `93eec024a80827178ee685a7f8b5586fb743e7319c1dc223b40b24fa18b913d9`; ELF range comparison JSON SHA-256 `3586e63d7d739b3c407e611853e37f19e21838c86b7b976b9dae17f069960a9d`. These are local evidence identifiers, not repository attachments. The Samsung-source Makefile and `gl_sys.c` are not redistributed here; consult an authorized copy of the SM-A022F open-source kernel package and its license notices.
