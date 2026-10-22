# Android Boot Header v2 and Minimal AArch64 Layout Experiments

## Technical scope

This case covers the offline construction and validation of successive Android boot header v2 layouts for a Minimal AArch64 Boot Proof. The image is not an Android ARM64 ROM and is not approved for flashing.

## Executive summary

The stock SM-A022F boot header describes a 32-bit kernel at 0x40008000. The AArch64 Image declares text_offset 0x80000, so that stock kernel address is not congruent with the required placement alignment. The raw AArch64 Image also exceeded the recorded 24 MiB boot partition. The experiments used gzip compression, an adjusted kernel address, a source-built base FDT, and a minimal initramfs. The newest retained candidate is 11,816,960 bytes and its locally computed SHA-256 matches the saved audit. Header, component, ELF, CPIO, gzip, FDT, and size checks passed offline. No LK or device boot test occurred.

## Device, kernel, and toolchain context

The target is Samsung Galaxy A02 SM-A022F, reference firmware A022FXXS3BWH1. The current candidate contains a compressed AArch64 Linux 4.14.186 Image, a compressed initramfs with a static ELF64 PID 1, and a one-entry Android DT table containing the source-built base FDT. The kernel used the saved ARM64 configuration and PowerVR patches through 0007. The actual image and executable initramfs are local-only.

## Original problem and symptoms

Three separate constraints had to be checked independently:

1. **Kernel address protocol:** the stock address 0x40008000 is 0x8000 modulo 2 MiB, while the Image header's text offset is 0x80000. The experiment used 0x40080000 as a congruent candidate address; LK relocation behavior is not established.
2. **Partition capacity:** the raw Image is 28,323,856 bytes, larger than the 25,165,824-byte boot partition. Gzip reduced the kernel section enough for an offline package to fit.
3. **DT and initramfs content:** a package must contain the correct board base and test PID 1 while preserving page alignment. A parsed header does not show that LK consumes these fields as expected.

## Layout history and artifact identity

The retained reports identify distinct artifacts; their checks must not be transferred between versions.

| Layout | Size | SHA-256 | Recorded distinction |
| --- | ---: | --- | --- |
| Earlier merged-r00 layout | 11,878,400 bytes | 460e9845bc6c36eba45806cca8e2030529ffcbd97810dff8c5f4313b5366bb25 | Used a merged tree; overlay handling was unresolved. |
| Earlier source-base, console-only layout | 11,814,912 bytes | c777304b479484561e9c4a2292c2cd3b27403d0d1a8473e90e8419a5c4d15fe4 | Different compressed kernel and smaller 845-byte initramfs. |
| Current USB-ACM layout | 11,816,960 bytes | 1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450 | Uses source-built base FDT and 2,248-byte USB observation initramfs; local only. |

The current candidate's last-write time was recorded as 2026-10-20, but filesystem metadata cannot prove a trusted build creation time. The exact full-image packing command was not retained in the public repository, so full bit-for-bit reconstruction from public inputs is not claimed.

## Investigation and confirmed root causes

The stock boot address cannot be assumed to meet the AArch64 Image protocol; the address was changed in the prototype, but runtime relocation is still unknown. Raw image capacity was a real size limit, addressed by compression rather than by disabling kernel features. An earlier FDT layout used a merged tree; the current candidate instead packages a source-built base FDT and leaves runtime DTBO selection unresolved. The resulting layout is internally parseable but is not a validated boot chain.

No single retained report attributes every layout revision to one bug. The component sizes differ across versions because kernel compression, FDT choice, and initramfs contents differ.

## Validation and verified results

The current local boot.img is 11,816,960 bytes with SHA-256 1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450; the independent file hash in this review matched the saved audit. Offline checks report:

- Android! magic, header version 2, page size 2,048, and a 1,660-byte header.
- Kernel gzip section 11,742,494 bytes at 0x40080000; decompression returns the expected 28,323,856-byte AArch64 Image.
- Ramdisk section 2,248 bytes at 0x45000000; it contains a 5,696-byte ELF64/AArch64 static /init with no PT_INTERP or PT_DYNAMIC.
- DT table at 0x44000000 with a single FDT entry; the embedded base FDT parsed successfully.
- The package fits the 24 MiB partition by 13,348,864 bytes, and the declared arithmetic kernel end is below the DT and ramdisk addresses.
- The candidate has no AVB footer or Samsung signer trailer.

These results establish byte structure and arithmetic only. They do not prove LK parsing, decompression scratch placement, EL transition, signature policy, Trusty reservations, overlay application, or device boot.

## Remaining limitations

The exact candidate is unsigned and must never be treated as flashable. LK/AVB acceptance, K64 runtime handoff, memory ownership, and recovery are unverified. USB observation itself has a source-level defect in the retained candidate described in [the USB ConfigFS case](05-usb-configfs-probe.md). The public repository deliberately excludes the candidate binary and firmware-derived inputs.

## Lessons learned

- Record a size and hash for every candidate; equal filenames do not imply equal artifacts.
- Validate kernel protocol addresses, partition capacity, header layout, compression, and memory arithmetic as distinct gates.
- Static non-overlap arithmetic is not a complete boot-time memory map.
- A valid header v2 container is not the same as a signed or bootloader-accepted Samsung image.

## Evidence references

The public detailed record is [Minimal AArch64 Boot Image](../minimal-aarch64-boot-image.md), with [offline layout audit](../boot-layout-audit.md), [candidate audit summary](../evidence/minimal-boot-candidate-audit.json), [kernel QA](../kernel-qa.md), and [flash readiness](../flash-readiness.md). The source-only probe is in [probes/minimal-aarch64-usb-acm](../../probes/minimal-aarch64-usb-acm/).

The local candidate and audit are not distributed. The candidate file hash recomputed during this review matched the public audit value; no image was rebuilt or modified.

## Current status

**RESOLVED — OFFLINE VALIDATION ONLY** for the current file's recorded header, components, hash, and capacity arithmetic. **UNVERIFIED** for signature acceptance, LK/K64 execution, runtime memory layout, and any device boot.
