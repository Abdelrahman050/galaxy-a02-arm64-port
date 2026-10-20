# Development sequence and acceptance gates

1. **Reproducible kernel.** Preserve the first output, perform a separate clean AArch64 build, verify ELF architecture, hashes, config, `System.map`, and modpost. Repair architecture-sensitive code without disabling required hardware components. In particular, audit the PowerVR DVFS device-node pointer callsites and Samsung debug/reserved-memory behavior. Preserve the stock RAM-console persistent-memory ABI; the current ARM64 fallback moves `off_console` by 256 bytes.
2. **Device-specific FDT.** The isolated Samsung-source build has passed a full static comparison for all three board revisions: only the PMU compatible string differs from official FDTs. Keep its stock reservations, Trusty/TEE nodes, bootargs, modem/CCCI and peripherals. Integrate it as a maintained build target after choosing a compatible DTC path; confirm driver binding and bootloader use separately.
3. **Bootloader handoff.** The exact Samsung LK binary has a compiled K64 SMC handoff and gzip path, but the path's runtime reachability and final physical target remain unproven. Establish that it decompresses the proposed AArch64 `Image` at its required offset and enters it with the required CPU mode, MMU/cache state, and `x0` DTB pointer. The raw `Image` exceeds the 24 MiB boot partition; an unsigned compressed v2 layout with the source-built base FDT fits by size only. Verify decompressed memory space, Samsung signer/AVB policy, the v2 DT-table wrapper, and LK's real DTBO selection/application to that base.
4. **Small boot proof.** With the owner's explicit approval for a device test, use the isolated static AArch64 `/init` to obtain an unmistakable AArch64 console marker and `uname.machine=aarch64`. Collect logs and preserve recovery options. The current offline archive does not pass the on-device gate.
5. **Android 11 ARM64 bring-up.** Only after boot feasibility and a graphics architecture are established, build a product/device tree with `TARGET_ARCH=arm64`, a matching multilib strategy, init/fstab/SELinux/VINTF/partition setup, and a compatible vendor interface. Start with init and logging, then Binder/HIDL services, display/SurfaceFlinger, input, storage, radio, and network.
6. **Graphics.** Supply or develop an ARM64-compatible mapper/gralloc and EGL/GLES stack for the PowerVR kernel driver, or validate a software path that actually presents frames on this hardware. The existing 32-bit passthrough mapper cannot be loaded into an ARM64 process. Fix kernel PowerVR pointer-width defects before treating graphics as functional.
7. **End-to-end proof.** Confirm 64-bit Android userspace and install/run an `arm64-v8a` test APK, then exercise essential hardware and stability. Record boot logs, ABI properties, `linker64`, loaded library architecture, graphics output, and app behavior. AArch64 kernel boot alone does not pass this gate.

## Resource gate

The current WSL2 instance has about 8 GiB RAM and the Windows system disk has roughly 32 GiB free. Keep using it for kernel/DT/firmware analysis. A full Android source checkout and build needs a larger Linux host or server; [current AOSP requirements](https://source.android.com/docs/setup/start/requirements) call for at least 64 GiB RAM and 400 GiB free storage. The selected Android 11 branch and disk estimate are tracked in the [Android report](android-userspace-audit.md).

## Required inputs before full Android build

- Matching Android 11 AOSP or LineageOS manifest/branch and a suitable Linux build host.
- SM-A022F device/product/BoardConfig, partition, fstab, init, SELinux, VINTF, and extract-files definitions, to be created or sourced and verified against this firmware.
- A legal, compatible ARM64 graphics implementation or a validated on-device rendering alternative; assess PowerVR kernel driver ABI compatibility as part of this.
- Device boot logs or a verifiable LK handoff path once the owner authorizes a device test.

No original firmware images or proprietary blobs are included in this package.
