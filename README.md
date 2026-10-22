# Samsung Galaxy A02 (SM-A022F) ARM64 Port

**Status: Research and development · Work in progress · Not a usable ROM**

This repository documents an engineering effort to develop a complete Android ARM64 system for the Samsung Galaxy A02 (SM-A022F), with the eventual goal of running applications built exclusively for `arm64-v8a`. Kernel compilation is one prerequisite; it is not evidence that the phone can boot the kernel or run a 64-bit Android userspace.

## Device and source scope

| Item | Value |
| --- | --- |
| Device | Samsung Galaxy A02, SM-A022F |
| SoC | MediaTek MT6739 family |
| Reference firmware | `A022FXXS3BWH1`, Android 11 |
| Kernel source | Samsung open-source package for the device; source archive is not redistributed here |
| Official Android release | Android 11 with a 32-bit ARM userspace |
| Official kernel | 32-bit ARM (`ARCH=arm`, output under `arch/arm/boot/`) |
| CPU capability | Cortex-A53 / Armv8-A supports AArch64 as well as AArch32 |
| Current stock userspace | 32-bit ARM (`armeabi-v7a`, `armeabi`) |
| Project target | Complete Android ARM64 userspace capable of running `arm64-v8a` applications |

## Architecture clarification

The Galaxy A02's official Android 11 software is ARM32: Samsung's kernel build instructions select `ARCH=arm` and identify `arch/arm/boot/Image.gz` as the kernel output, and the inspected stock userspace libraries are 32-bit ELF ([userspace audit](docs/android-userspace-audit.md); package and build provenance in [`docs/reproducibility.md`](docs/reproducibility.md)). The phone's Cortex-A53 cores implement Armv8-A and support AArch64, but that CPU capability does not make the shipped kernel or Android system 64-bit. See Arm's [Cortex-A53 specifications](https://www.arm.com/products/silicon-ip-cpu/cortex-a/cortex-a53).

This project is developing both an AArch64 kernel and a complete Android ARM64 userspace with the required device and vendor integration. It is not an ABI flag or system-property change. The experimental AArch64 kernel has compiled successfully, including an independent clean-output rebuild; however, booting it on the phone, running Android ARM64, and executing an `arm64-v8a` application on the device have **not** been demonstrated.

## Verified progress

- An AArch64 Linux kernel `Image` was built, then built again in an independent clean output directory. The saved configuration and `System.map` matched; the `Image` and `vmlinux` hashes differed, so bit-for-bit reproducibility has **not** been established.
- A Samsung MT6739/K39/A02 device-tree source build was compared semantically with official merged firmware trees for revisions r00, r01, and r06. Node, property, and reserved-memory data matched except for the intentional ARMv8 PMU `compatible` change. The three DTBO overlays matched byte-for-byte. This was an isolated source build, not an in-tree `make dtbs` or device boot test.
- Static LK analysis found a compiled K64 handoff path, including an SMC call site. It does not show that this device takes the path, that the secure monitor accepts the handoff, or that the candidate kernel reaches EL1.
- PowerVR kernel patches compiled and linked in isolated kernel outputs. GPU operation, display, and graphics userspace compatibility remain untested.
- A local-only USB-ACM Minimal AArch64 Boot Proof layout was structurally checked at 11,816,960 bytes. Its detailed header, component hashes, `/init`, memory arithmetic, and evidence limits are in [`docs/minimal-aarch64-boot-image.md`](docs/minimal-aarch64-boot-image.md); the binary and initramfs are not distributed. LK/AVB acceptance, UDC/COM behavior, and a real boot remain unverified.

## Current blockers

- RAM-console record layout differs between the legacy ARM32 reader and the ARM64 build. A compatibility patch passed an isolated object build and offline layout checks, but was not linked into a full kernel image or tested on-device.
- `SEC_DEBUG` is disabled in the current ARM64 configuration. Architecture-specific candidate patches were reviewed but not built with `SEC_DEBUG` enabled.
- The official Android system and vendor stack inspected so far are 32-bit. The stock graphics mapper, gralloc, EGL/GLES, HWC, and Vulkan libraries checked are ELF32; no compatible ARM64 graphics stack has been verified.
- Candidate-image signature and AVB acceptance, LK load/decompression addresses, secure-world behavior, early log capture, and recovery after a failed boot have not been demonstrated.
- The retained USB-ACM candidate uses a Linux Foundation sample VID/PID and must not be treated as a ready observation image. Source review also found its unprefixed ConfigFS descriptor values conflict with the upstream Linux 4.14 base-autodetect parser, so gadget setup is expected to fail at `idVendor` unless Samsung's 4.14.186 source differs. The PR-review source now emits `0x`-prefixed values, requires an explicitly authorized identity, and the host reader waits for its exact PnP match; this revised source has not been built into a candidate. UDC, Windows COM enumeration, and marker reception remain untested. Odin's one-member rollback mapping and a current independent data backup are also unverified.
- Android ARM64 has not been built or booted on this device. No `arm64-v8a` application has been run on it.

The present flash-readiness decision is **NO-GO**. Later user-reported observations indicated `flash.locked=0`, `vbmeta.device_state=unlocked`, `verifiedbootstate=orange`, bootloader build `A022FXXS3BWH1`, and Odin recognition in Download Mode. A raw capture and timestamp were not retained with the evidence. These observations describe the reported state at that time; they do not establish that LK accepts the experimental image or that recovery is safe.

## Repository map

- [`STATUS.md`](STATUS.md): PASS / FAIL / UNVERIFIED evidence matrix.
- [`ROADMAP.md`](ROADMAP.md): staged development path toward Android ARM64 and `arm64-v8a` execution.
- [`docs/`](docs/): kernel QA, device tree, LK, boot layout, userspace, graphics, RAM-console, reproducibility, and readiness reports.
- [`probes/minimal-aarch64-usb-acm/`](probes/minimal-aarch64-usb-acm/): source-only experimental AArch64 `/init` and identity-matched USB-ACM reader; the revised source has not been incorporated into the local candidate.
- [`patches/`](patches/): ordered kernel changes, unmerged candidates, and separate device-tree adaptations.
- [`config/`](config/): the saved ARM64 kernel configuration.
- [`scripts/`](scripts/): build and bounded, read-only audit tools.

## Reproduction overview

The Samsung source archives, matching official firmware, proprietary vendor libraries, and generated binaries are external inputs and are not included. Obtain authorized copies independently, verify their identity and hashes against [`docs/external-inputs.md`](docs/external-inputs.md) and [`docs/reproducibility.md`](docs/reproducibility.md), and work only from a writable source copy. Keep firmware inputs read-only and place all build output in a separate output directory.

The recorded kernel toolchain was Android Clang `r383902` with Android GCC/binutils `4.9`, using `ARCH=arm64`, `MTK_PLATFORM=mt6739`, and the included configuration. See the reproducibility report before attempting a build. The included build helper never cleans output directories; use a new output directory for each clean-build comparison.

```sh
export KERNEL_SRC=/path/to/writable/samsung-kernel-copy
export KERNEL_OUT=/path/to/separate/output-directory
export TOOLCHAIN_ROOT=/path/to/recorded/android-toolchain
python3 scripts/build_kernel.py
```

The helper refuses a non-empty `KERNEL_OUT` and writes configuration, build outputs, and a log only beneath that separate directory. It does not package or flash an image. A successful build is a compile/link result, not a boot or runtime result.

The separate [Minimal AArch64 Boot Image record](docs/minimal-aarch64-boot-image.md) documents the newest local-only header-v2 layout and how to reproduce the allowed kernel/initramfs inputs. The current USB candidate itself is not in the repository, and exact full-image recreation from the public tree alone is not yet established. Its readiness and rollback gates remain in [flash readiness](docs/flash-readiness.md) and [Odin recovery readiness](docs/odin-recovery-readiness.md).

## Safety and redistribution

This is research material, not a flashable ROM. Do not use any generated or experimental image for flashing. No device operation is part of this repository's build or audit scripts. Firmware, proprietary blobs, private keys, full backups, LK binaries, and generated boot images are intentionally excluded. The public source subset contains 12 reviewed patches; the firmware-derived PMU patch is retained in the local development copy but excluded from the public Git index and archive. License clearance is **PASS for this exact public subset** and **BLOCKED for the original 13-patch collection** until redistribution rights for that firmware-derived patch are established. See [`docs/license-review-2026-10-20.md`](docs/license-review-2026-10-20.md) for the source-based PMU replacement and evidence. See [`SECURITY.md`](SECURITY.md), [`NOTICE.md`](NOTICE.md), and the per-file upstream notices before reuse.

The included GitHub Actions workflow has one successful read-only run on the initial `main` commit; see [`docs/ci.md`](docs/ci.md) for the exact commit and scope. That run did not build the kernel or test the phone. No CI status badge is included.
