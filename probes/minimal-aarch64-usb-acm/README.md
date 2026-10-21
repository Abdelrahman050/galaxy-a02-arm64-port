# Experimental Minimal AArch64 USB-ACM Probe

This local-buildable probe is intended to observe whether a kernel reaches a freestanding AArch64 PID 1 on the Samsung Galaxy A02 SM-A022F. It is not Android, a recovery image, or a flashable package. No binary image or initramfs is distributed here.

## Contents

- `init.c`: static PID 1 using direct AArch64 Linux system calls. It prints a console marker, attempts a CDC-ACM configfs gadget, binds an available UDC, then writes the `uname.machine` marker to `/dev/ttyGS0`.
- `build.sh`: builds `/init` and a deterministic gzip-compressed `newc` initramfs using an existing Android Clang and the kernel's `gen_init_cpio` host utility. Outputs are written only to this directory's ignored `build/` folder.
- `capture_usb_acm.ps1`: bounded listener that waits for the probe to enumerate, resolves only the COM port whose present PnP instance matches the explicitly supplied VID, PID, and unique USB serial, and writes a local JSON evidence record. It opens no other COM port and sends no serial payload.

The source and scripts are original project material under the repository license; see [`NOTICE.md`](../../NOTICE.md). Syscall numbers are checked against Linux's asm-generic UAPI definitions. Build/runtime evidence and limitations are in [`docs/minimal-aarch64-boot-image.md`](../../docs/minimal-aarch64-boot-image.md).

## Build

On the existing WSL2 development environment, set `KERNEL_WORK_ROOT` to a separate authorized Samsung-source working copy containing the recorded Clang bundle and the built `usr/gen_init_cpio`. Supply a VID you own or are explicitly authorized to use, a PID assigned under that VID, and a unique serial for this image. The script checks only formatting; it cannot verify ownership or allocation. It rejects reserved all-zero/all-one values and refuses to overwrite a non-empty output directory. Use a fresh `PROBE_OUT` for each build:

```sh
cd probes/minimal-aarch64-usb-acm
KERNEL_WORK_ROOT=/path/to/authorized/kernel-work-copy \
USB_VID=YOUR_ASSIGNED_VID USB_PID=YOUR_ASSIGNED_PID USB_SERIAL=YOUR_UNIQUE_SERIAL \
PROBE_OUT=/path/to/new/empty/probe-output bash build.sh
```

The `YOUR_ASSIGNED_*` strings are placeholders and must be replaced with an identity you are entitled to use. `CLANG` and `GEN_INIT_CPIO` may be set explicitly to existing tools. The script does not install or download tools. Confirm the output `SHA256SUMS`, inspect `elf-readelf.txt`, and validate the CPIO archive before using any packaging code. The full kernel source remains an external input.

## Host observation

Only after a separately reviewed and authorized device test, start the listener before the test. It waits for enumeration and accepts only a present USB Ports-class PnP instance matching the exact VID, PID, and serial built into that probe. It rechecks the identity immediately before and after opening the associated COM port; if the identity changes, it closes the port without reading. It records the PnP identity, port, result, and bounded received text to a new JSON file, and refuses to overwrite an existing evidence file.

```powershell
.\capture_usb_acm.ps1 -Vid YOUR_ASSIGNED_VID -Pid YOUR_ASSIGNED_PID -DeviceSerial YOUR_UNIQUE_SERIAL -TimeoutSeconds 120
```

Replace the placeholders with the values used to build the probe; do not copy them literally. The VID, PID, and serial must exactly match the separately built probe. The script asserts DTR, sends no payload, and reports `INCONCLUSIVE` on timeout. Multiple matching devices are treated as ambiguous and no port is opened. Driver/open errors and lack of a matching COM device are inconclusive. The required positive marker is `A02 ARM64 boot probe: PID 1 entered; uname.machine=aarch64`.

The ConfigFS descriptor values are written with an explicit `0x` prefix because Linux v4.14 parses these values with base autodetection. The retained older candidate used unprefixed hexadecimal-looking text; upstream v4.14 would reject its `1d6b` vendor ID and interpret leading-zero descriptor values as octal. The corrected source is not part of that retained image. Samsung's exact 4.14.186 ConfigFS implementation and all runtime gadget behavior still need confirmation.

## Limitations

The USB controller, UDC availability, Windows enumeration, and marker path are untested on this hardware. The retained local candidate was built with `1d6b:0104`, which the USB ID database identifies as Linux Foundation's Multifunction Composite Gadget; it is not a project identity and must not be reused as one. In addition, its source used unprefixed numeric values that conflict with the upstream v4.14 base-autodetection parser. The checked-in source now uses `0x` prefixes, has no default identity, and requires explicit build-time values. That source revision is not in the retained candidate: rebuild and revalidate a new image before any test. A legitimate test should use a VID/PID you own or have explicit authorization to use, plus a unique serial. See [USB-IF Vendor ID guidance](https://www.usb.org/getting-vendor-id), [Linux v4.14 ConfigFS source](https://github.com/torvalds/linux/blob/v4.14/drivers/usb/gadget/configfs.c#L147-L170), and the [USB ID record](https://usb-ids.gowdy.us/read/UD/1d6b). This probe does not access partitions, mount Android data, reboot, or flash. Do not treat it or its output as authorization to flash.
