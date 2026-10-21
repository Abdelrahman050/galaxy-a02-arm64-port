# Experimental Minimal AArch64 USB-ACM Probe

This local-buildable probe is intended to observe whether a kernel reaches a freestanding AArch64 PID 1 on the Samsung Galaxy A02 SM-A022F. It is not Android, a recovery image, or a flashable package. No binary image or initramfs is distributed here.

## Contents

- `init.c`: static PID 1 using direct AArch64 Linux system calls. It prints a console marker, attempts a CDC-ACM configfs gadget, binds an available UDC, then writes the `uname.machine` marker to `/dev/ttyGS0`.
- `build.sh`: builds `/init` and a deterministic gzip-compressed `newc` initramfs using an existing Android Clang and the kernel's `gen_init_cpio` host utility. Outputs are written only to this directory's ignored `build/` folder.
- `capture_usb_acm.ps1`: bounded read-only serial listener. It opens the selected COM port and asserts DTR but sends no serial payload.

The source and scripts are original project material under the repository license; see [`NOTICE.md`](../../NOTICE.md). Syscall numbers are checked against Linux's asm-generic UAPI definitions. Build/runtime evidence and limitations are in [`docs/minimal-aarch64-boot-image.md`](../../docs/minimal-aarch64-boot-image.md).

## Build

On the existing WSL2 development environment, set `KERNEL_WORK_ROOT` to a separate authorized Samsung-source working copy containing the recorded Clang bundle and the built `usr/gen_init_cpio`, then run:

```sh
cd probes/minimal-aarch64-usb-acm
KERNEL_WORK_ROOT=/path/to/authorized/kernel-work-copy bash build.sh
```

`CLANG` and `GEN_INIT_CPIO` may be set explicitly to those existing tools. The script does not install or download tools. Confirm the generated `build/SHA256SUMS`, inspect `build/elf-readelf.txt`, and validate the CPIO archive before using any packaging code. The full kernel source remains an external input.

## Host observation

Only after a separately reviewed and authorized device test, select the COM port associated with the gadget and run:

```powershell
.\capture_usb_acm.ps1 -Port COM7 -TimeoutSeconds 120
```

Replace `COM7` with the verified port. The script asserts DTR, sends no data, and reports `INCONCLUSIVE` on timeout. Driver/open errors and lack of a COM port are also inconclusive. The required positive marker is `A02 ARM64 boot probe: PID 1 entered; uname.machine=aarch64`.

## Limitations

The USB controller, UDC availability, Windows enumeration, and marker path are untested on this hardware. The current candidate uses sample VID/PID `1d6b:0104`; it is not a project-assigned identity and must be reviewed before any hardware use. This probe does not access partitions, mount Android data, reboot, or flash. Do not treat it or its output as authorization to flash.
