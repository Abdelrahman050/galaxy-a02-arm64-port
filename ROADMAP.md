# Roadmap to Android ARM64

The project goal is a complete Android ARM64 system on SM-A022F that runs applications built for `arm64-v8a`. A kernel build or minimal `/init` proof is an intermediate gate only.

## Release hygiene checkpoint

- Use the Samsung-source-based stock MT6739 PMU adaptation for public reproduction. The firmware-derived historical patch remains preserved locally and excluded from public staging until its redistribution rights are established.
- Keep source archive and firmware inputs external. Re-run license, checksum, secret, and archive/index parity audits for each release snapshot.
- This checkpoint does not change the technical gates or imply device boot readiness; **FLASH READINESS remains NO-GO**.

## Gate 1 — Freeze and qualify kernel artifacts

- Reproduce the saved ARM64 build from an authorized Samsung source archive in a writable copy and a fresh output directory.
- Keep original and patched outputs separate; record tool versions, full command, config digest, map/image digests, and warnings.
- Resolve RAM-console record compatibility and the `SEC_DEBUG` architecture path without disabling required drivers merely to build.
- Review the PowerVR kernel changes for lifetime, locking, and error-path behavior. Compile/link evidence is not GPU runtime evidence.

**Exit evidence:** a traceable kernel build with ABI review, no unresolved memory-layout issue in the proposed test path, and explicit boot/runtime unknowns.

## Gate 2 — Establish device-specific boot feasibility

- Integrate the matched Samsung MT6739/K39/A02 DT source through the kernel's supported build path and preserve reserved memory, TEE/Trusty nodes, and boot arguments.
- Confirm boot-header fields, compression, image/FDT/initramfs placement, load and decompression addresses against the exact LK build and its runtime behavior.
- Establish signature/AVB acceptance for the exact candidate image; unlocked/Orange state alone is not acceptance evidence.
- Establish a reliable early-log channel and a recovery procedure for the exact model and bootloader. Assess user-data loss explicitly.
- Run a minimal AArch64 `/init` proof only after the separate human-reviewed readiness gate and explicit owner authorization.

The historical USB-ACM layout is retained in [the earlier image record](docs/minimal-aarch64-boot-image.md). [Phase 6](docs/evidence/phase6-minimal-aarch64-offline.md) produced a distinct, unsigned console/kmsg-only candidate and identified the unverified LK-to-FDT initrd handoff. No dependable external marker or tested rollback exists. This is preparation for the gate, not exit evidence.

**Exit evidence:** observed execution into AArch64 `/init` with attributable early logs, plus a tested recovery path. Static LK disassembly or a fitting image size is insufficient.

## Gate 3 — Build the Android ARM64 platform

- After Gate 2 and a credible graphics path, create Android 11 device configuration: device tree, `BoardConfig`, product makefiles, VINTF manifests/matrices, init rc, fstab, SELinux policy, and kernel modules.
- Define the vendor boundary. Determine which 32-bit vendor services can remain isolated behind supported Binder/HIDL interfaces and which components require 64-bit counterparts.
- Resolve the 64-bit graphics stack. Source or validate compatible PowerVR ARM64 user libraries and mapper/gralloc/HWC interfaces; a 32-bit binary cannot be loaded into a 64-bit process.
- Build a minimal ARM64 userspace, then add services in small, diagnosable groups.

**Exit evidence:** a booting Android ARM64 userspace with core services, display/input/storage/network smoke checks, and documented vendor compatibility.

## Gate 4 — Validate the final goal

- Confirm `ro.product.cpu.abilist` exposes the intended ARM64 ABI and verify the running linker/process architecture.
- Install and run an app built exclusively for `arm64-v8a`.
- Exercise suspend/resume, charging, audio, camera, radio, storage, thermal behavior, and recovery. Record logs and regressions per firmware/build.
- Publish only reproducible source, scripts, patches, and legally distributable documentation. Keep firmware and vendor blobs external.

**Exit evidence:** repeatable Android ARM64 boots and successful `arm64-v8a` application execution, with hardware and recovery test results.

## Resource planning

The recorded kernel build ran in WSL2 x86-64 with 16 logical CPUs and about 8 GiB RAM. A full Android build is a separate, substantially larger workload. Before that gate, budget a Linux host with approximately 64 GiB RAM and several hundred GiB of free SSD space; validate the current AOSP requirements at planning time. Do not download/build full AOSP until boot feasibility and graphics integration have credible paths.
