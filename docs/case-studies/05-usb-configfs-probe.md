# Minimal init USB ConfigFS Encoding and Device Identity

## Technical scope

This case covers the freestanding AArch64 /init used by the local Minimal Boot Proof, its USB ConfigFS descriptor writes, and the revised source/host listener committed for review. It does not claim CDC-ACM enumeration or marker receipt on the phone.

## Executive summary

The retained candidate's /init writes an unprefixed USB vendor string 1d6b and leading-zero descriptor strings such as 0104, 0200, and 0100. Upstream Linux v4.14 parses these u16 ConfigFS fields with base autodetection: the vendor value is not valid hexadecimal without a 0x prefix, and leading zero selects octal. The exact Samsung 4.14.186 parser was not retained for this review, so the device-specific outcome remains an inference. A later source change emits explicit 0x-prefixed values, requires a caller-provided authorized VID/PID and unique serial, and waits for an exact PnP identity before opening a COM port. The corrected source was compiled separately but was not inserted into the retained image.

## Device, kernel, toolchain context

The candidate targets SM-A022F and its experimental ARM64 Linux 4.14.186 kernel. The probe is a freestanding static AArch64 PID 1 with no Android init or libc. The candidate audit records a static ELF64 /init, gzip/newc CPIO structure, and USB gadget configuration code. The later source-only correction was built with a separate Clang 21.1.6 toolchain using synthetic compile-time identity values; that build did not create a new initramfs or boot image.

## Original problem and evidence

The original source wrote 1d6b as the VID and 0104 as the PID, with 0200 and 0100 for BCD values. It used a sample Linux Foundation vendor/product identity, not an identity assigned to this project. The host capture script at that stage required a COM port name before the gadget could enumerate, so it could not itself wait for this test device to appear.

Upstream Linux v4.14's configfs.c uses kstrtou16 with base 0 for these descriptor fields. Under that parser, 1d6b fails numeric parsing, while 0104, 0200, and 0100 are octal values. This predicts failure at the vendor write if Samsung's 4.14.186 source retains the upstream parser. The exact Samsung file is not present in the retained reviewed inputs, so the prediction is not a verified Samsung runtime result.

## Investigation and root cause

Two independent issues were identified:

1. **Encoding:** the init wrote hexadecimal-looking text without an explicit base prefix to a base-autodetect parser.
2. **Identity and observation:** Linux Foundation's VID is not a project-assigned identifier, and preselecting a COM port cannot securely identify a device that appears only after boot.

The candidate's offline ELF/CPIO/gzip checks verified file format, not successful ConfigFS writes. That gap became visible only when the source behavior was compared with the kernel parser contract and the host listener's discovery flow.

## Applied source correction

Commit f6adee4 changes the probe builder to require a four-digit VID, PID, and unique serial from the caller, reject reserved zero/all-ones values, and generate explicit 0x-prefixed descriptor values. The host reader waits for an exact VID/PID/serial PnP match, rechecks the device instance before and after opening its associated COM port, rejects ambiguous matches, and writes an evidence record without overwriting. This policy does not choose or authorize an actual USB ID; the test owner must supply an ID they are entitled to use.

## Validation and verified results

The revised init source passed a separate Clang compile/link with synthetic identity macros. Repository CI checked the build script syntax and the synthetic policy tests passed on the reviewed branch. These checks do not execute the build helper with the actual kernel gen_init_cpio toolchain. The retained candidate remains at 11,816,960 bytes with its original hash and contains the earlier init source; it was not rebuilt from commit f6adee4.

No live USB UDC binding, Windows PnP enumeration, COM capture, or marker receipt has been tested. A black screen is expected for the tiny probe and is not a success/failure signal by itself.

## Remaining limitations

- Samsung's exact configfs parser behavior is unverified against the vendor source.
- The revised source is not in the retained candidate binary.
- No authorized test VID/PID has been provided in the evidence set.
- UDC availability, electrical/OTG role, PnP identity format, and CDC-ACM behavior are untested on hardware.
- A successful host marker would prove only that this AArch64 PID 1 reported uname.machine=aarch64, not Android boot or application support.

## Lessons learned

- Parse semantics matter: a string that looks like hexadecimal is not necessarily parsed as hexadecimal.
- Separate candidate artifacts from later source fixes; never attribute a fix to a binary that was not rebuilt from it.
- A generic COM port can connect to the wrong device. Discover and verify the exact device identity before opening a serial handle.
- A sample vendor ID is not project identity. Use only an ID explicitly authorized for the test.

## Evidence references

The source fix is [commit f6adee4](https://github.com/Abdelrahman050/galaxy-a02-arm64-port/commit/f6adee4b5e9d2b0ba80213ba4a84dac186186e6a), with revised [init source](../../probes/minimal-aarch64-usb-acm/init.c), [build helper](../../probes/minimal-aarch64-usb-acm/build.sh), and [host reader](../../probes/minimal-aarch64-usb-acm/capture_usb_acm.ps1). See [Minimal AArch64 Boot Image](../minimal-aarch64-boot-image.md) and [flash readiness](../flash-readiness.md).

The parser behavior is linked to the primary upstream [Linux v4.14 configfs.c](https://github.com/torvalds/linux/blob/v4.14/drivers/usb/gadget/configfs.c#L147-L170). That is not a substitute for inspecting the Samsung vendor copy. The original local init source hash is eed092d598d0dfaaabd3fe62a9c365058bd5cb9f9e15a78cff1d5fd904761368; the retained candidate hash is documented separately in the boot-image report. The binary and full local initramfs artifacts are not distributed.

## Current status

**PARTIALLY RESOLVED.** The revised source corrected the encoding and identity-discovery design and passed a separate compile/link check. The retained candidate still contains the earlier source. Samsung parser behavior, UDC/COM operation, and marker delivery remain **UNVERIFIED**.
