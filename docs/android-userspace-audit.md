# Android ARM64 Userspace Feasibility

## Current stock baseline

The inspected Android 11 firmware is 32-bit userspace: it advertises `armeabi-v7a,armeabi`, has no verified `linker64` or `/vendor/lib64` stack, and the system/vendor libraries inspected are ELF32. The kernel and a minimal AArch64 initramfs do not turn that userspace into Android ARM64.

The stock VINTF manifest describes binderized HIDL services and declares the graphics mapper as supporting both 32- and 64-bit architectures. However, the inspected mapper implementation is present only as ELF32. The declared `32+64` metadata therefore does not establish a usable 64-bit mapper.

## Mixed-bitness vendor services

Separate 32-bit vendor HAL processes may be reachable from a 64-bit framework through Binder/HIDL when the Android build, VINTF compatibility, service registration, SELinux policy, and serialized interfaces all support the arrangement. This is a plausible integration approach, not a verified property of this device's vendor image.

A 64-bit process cannot load an ELF32 shared library in-process. Thus existing 32-bit binderized services might be retained behind IPC, but 64-bit graphics clients still need a 64-bit compatible mapper and its dependencies. Transporting a file descriptor or native handle does not prove that the 64-bit process understands the PowerVR payload or metadata.

## Graphics blocker

The stock graphics components inspected—mapper/gralloc, EGL/GLES, hardware composer, and Vulkan-related libraries—are ELF32. No compatible ARM64 PowerVR user-space package has been verified. The kernel's PowerVR changes passed compile/link checks only; GPU runtime is unverified.

An earlier offline inspection identified a stock PowerVR handle envelope of 208 bytes with 49 integer slots. That does not disclose the complete private field map, versioning, metadata protocol, fences/cache behavior, or a safe ARM64 implementation. See [`gralloc-handle-audit.md`](gralloc-handle-audit.md). Do not invent a shim that only reports success without implementing the buffer protocol.

## Required Android integration

After boot feasibility and graphics have credible solutions, an Android 11 ARM64 device port will need at least:

- device/product makefiles and `BoardConfig` targeting ARM64 and the exact MT6739 board;
- a maintained kernel and module build, boot image and DTB/DTBO packaging rules;
- VINTF manifest/matrix alignment with Android 11 vendor interface level and VNDK;
- init rc files, fstab, SELinux policy, properties, permissions, and firmware loading rules;
- vendor service and linker-namespace integration, including a deliberate 32-bit/64-bit boundary;
- compatible 64-bit graphics mapper/gralloc and presentation path, or a demonstrated software-rendering path that reaches the physical display.

No complete Android device tree, product image, or userspace build is included. Full AOSP/LineageOS compilation is intentionally gated on boot proof and a credible display/graphics path.

## Status

| Requirement | Status |
| --- | --- |
| Stock userspace architecture identified | **PASS: 32-bit** |
| Mixed-bitness Binder/HIDL integration | **UNVERIFIED** |
| ARM64 graphics stack | **FAIL: no compatible package verified** |
| Android ARM64 build | **NOT STARTED** |
| Android ARM64 boot on device | **UNVERIFIED** |
| `arm64-v8a` app execution on device | **NOT ACHIEVED** |

The project does not claim Android ARM64 readiness. The final goal remains a functioning ARM64 system that installs and runs an app built exclusively for `arm64-v8a`.

## References

- [AOSP HIDL architecture](https://source.android.com/docs/core/architecture/hidl)
- [AOSP VINTF objects and architecture declarations](https://source.android.com/docs/core/architecture/vintf/objects)
- [AOSP Android build requirements](https://source.android.com/docs/setup/start/requirements)
