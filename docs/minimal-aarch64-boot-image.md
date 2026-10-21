# Minimal AArch64 Boot Image — Offline Engineering Record

- **Device:** Samsung Galaxy A02 (`SM-A022F`)
- **Reference firmware:** `A022FXXS3BWH1` (Android 11)
- **Current artifact:** USB-ACM observation layout, retained locally only
- **Device result:** **UNVERIFIED**
- **Flash readiness:** **BLOCKED / NO-GO**

This record documents an offline boot-layout experiment intended to answer one narrow question: can the matching LK/TEE chain enter an AArch64 kernel and run a tiny AArch64 PID 1? It is not an Android ARM64 ROM, does not contain Android services or vendor libraries, and does not demonstrate `arm64-v8a` app support. The executable boot image and initramfs remain outside this public repository.

## Candidate identity and chronology

The current USB-ACM layout is **11,816,960 bytes** with SHA-256 `1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450`. The digest and size were recalculated from the local image during this update and match the saved offline audit in [`evidence/minimal-boot-candidate-audit.json`](evidence/minimal-boot-candidate-audit.json). The image is explicitly unsigned and must not be flashed.

The local filesystem reports a last-write time of **2026-10-20 22:21:11 +03:00** for this file. That is ordinary filesystem metadata, not a signed or immutable build record; the actual creation time cannot be proven more strongly from retained evidence. The preflight report was saved later that evening.

Earlier layouts are distinct artifacts and their measurements must not be transferred to the current image:

| Layout | Size | SHA-256 | Difference / status |
| --- | ---: | --- | --- |
| Merged-r00 FDT, earlier clean-kernel layout | 11,878,400 | `460e9845bc6c36eba45806cca8e2030529ffcbd97810dff8c5f4313b5366bb25` | Earlier prototype with a merged tree; overlay handling at boot was unresolved. |
| Source-built base FDT, earlier console-only layout | 11,814,912 | `c777304b479484561e9c4a2292c2cd3b27403d0d1a8473e90e8419a5c4d15fe4` | Used a different kernel gzip and a smaller 845-byte initramfs. |
| **Current USB-ACM layout** | **11,816,960** | **`1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450`** | Uses the source-built base FDT and a 2,248-byte USB observation initramfs; local only. |

The first two rows come from the earlier [boot-layout audit](boot-layout-audit.md). Their small size difference is not evidence of equivalence: the kernel compression and initramfs inputs differ. The current candidate is the newest image found in the retained work area.

## Production sequence and reproducibility boundary

1. **Kernel:** the tested AArch64 `Image` came from the isolated Samsung-source build with the reviewed PowerVR changes through patch `0007`. The full kernel source, toolchain bundle, build outputs, and firmware are external inputs and are not copied here. Build instructions and input provenance are in [reproducibility](reproducibility.md); kernel QA is in [kernel-qa](kernel-qa.md).
2. **Device tree:** the candidate contains the Samsung-source-based SM-A022F base tree produced through the public device-tree staging workflow and the licensed PMU adaptation. Its parsed structure was compared with official-derived trees; the intentional PMU compatible change is documented in [device-tree and LK research](device-tree-bootloader.md). The DTBO remains a separate boot-chain input and was not packaged in this image.
3. **Probe initramfs:** [`probes/minimal-aarch64-usb-acm/`](../probes/minimal-aarch64-usb-acm/) contains the original freestanding `/init`, its build helper, and a Windows serial reader. The helper uses the existing Android Clang and kernel `gen_init_cpio`; it does not download tools or touch a device.
4. **Image layout:** the local experiment placed the compressed kernel, compressed initramfs, and one-entry Android DT table in a page-aligned Android boot header v2 container. It did not copy the stock image's signer trailer or AVB footer. The complete current USB-layout packer invocation/source was not retained in the public package, so this exact image is **not yet bit-for-bit reproducible from the repository alone**. The allowed source-build parts can be reproduced from authorized kernel inputs; the image itself and firmware-derived input bytes are deliberately excluded.

Do not use the old layout generator as proof that it recreates this USB candidate. A future public packer would need its own source review, synthetic tests, and comparison against exact user-supplied inputs before being described as reproducible.

## Kernel component

The kernel payload was independently decompressed from the current candidate and checked against the retained kernel QA evidence:

| Measurement | Value |
| --- | --- |
| Kernel release embedded in image | `4.14.186` |
| Architecture / Image magic | AArch64 / `0x644d5241` (`ARM\x64`) |
| Uncompressed `Image` size / SHA-256 | 28,323,856 bytes / `631581ff73a88a4b9a53b69a43660678c0e714ab5009d37212e9add583543131` |
| Compressed kernel section size / SHA-256 | 11,742,494 bytes / `be341f7261cb0b5fe6cb1e8d9c3e4b15dbaf1997395d5a6f93d59126184f1ee0` |
| AArch64 Image header | `text_offset=0x80000`, `image_size=33,325,056` (`0x01fc8000`), flags `0xA` |
| Saved ARM64 config SHA-256 | `cf28ea2d10ed44db355ef454ab9cc395b0ae2c82d870e396cba1bc8a197ef354` |
| Toolchain evidence | Android Clang `r383902`, Clang `11.0.1`; see the reproducibility record for the associated cross-toolchain details. |

The saved configuration has `CONFIG_ARM64=y`, `CONFIG_COMPAT=y`, `CONFIG_MACH_MT6739=y`, `CONFIG_USB_GADGET=y`, `CONFIG_USB_CONFIGFS=y`, `CONFIG_USB_CONFIGFS_ACM=y`, and `CONFIG_USB_MTK_OTG=y`. `SEC_DEBUG` is disabled. The RAM-console ABI compatibility patch is not linked into this image; the previously documented ARM32/ARM64 record-layout issue remains open. Neither issue has been proven to prevent this minimal test, and neither is used as an observation channel.

The raw `Image` is larger than the recorded 24 MiB boot partition. The boot-header kernel component is gzip-compressed; its successful decompression and matching raw `Image` digest are offline checks, not proof that LK will decompress it to a safe runtime address.

## Android boot header v2 and components

The candidate was parsed from its actual bytes. The field layout follows AOSP's [boot image header definitions](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/master/include/bootimg/bootimg.h). The current values are:

| Header field | Value |
| --- | --- |
| Magic / header version / header size | `ANDROID!` / `2` / 1,660 bytes |
| Page size | 2,048 bytes |
| `kernel_size` / `kernel_addr` | 11,742,494 / `0x40080000` |
| `ramdisk_size` / `ramdisk_addr` | 2,248 / `0x45000000` |
| `second_size` / `second_addr` | 0 / `0x0` |
| `tags_addr` | `0x44000000` |
| `recovery_dtbo_size` / offset | 0 / 0 |
| `dtb_size` / `dtb_addr` | 65,740 / `0x44000000` |
| `name` / raw `os_version` | `SRPTK19C003` / `0x16000179` |
| Kernel command line | `bootopt=64S3,32S1,32S1 console=ttyMT0,115200n8 loglevel=8 ignore_loglevel` |
| Extra command line | empty |
| 32-byte header image-ID field | `8821b04e800d1cbb9ea4461340eecd94e708ad47000000000000000000000000` |

The image-ID field is header metadata, not a Samsung signature or AVB authorization. The kernel section begins at byte 2,048; the ramdisk at 11,745,280; and the DT table at 11,749,376. Each section is padded to the 2,048-byte page boundary. The container ends at 11,816,960 bytes.

The DT section is an Android DT table with one entry: table magic `0xd7b7ab1e`, table size 65,740, 32-byte header and entry, FDT offset 64, and FDT payload size 65,676. The embedded FDT has magic `0xd00dfeed` and SHA-256 `b5314ec277200b532aba7d1302a86abd84ba878a78f3c7216c093a2f21cb825b`. It is the source-built **base** tree, not a pre-merged r00/r01/r06 tree. Runtime DTBO selection/application is unverified.

The initramfs is gzip-compressed `newc` CPIO. Its decompressed archive is 6,656 bytes and contains only `dev/`, `dev/console`, `sys/`, `/init`, and the CPIO trailer. `/init` is a 5,696-byte ELF64 little-endian AArch64 `ET_EXEC`, entry `0x210750`, with no `PT_INTERP` or `PT_DYNAMIC` segment. Its hash and the CPIO/gzip component hashes are in [`evidence/minimal-initramfs-checksums.txt`](evidence/minimal-initramfs-checksums.txt).

## `/init` and USB-ACM observation

The static PID 1 writes an early marker to `/dev/console`, calls AArch64 `uname`, mounts only `sysfs` and `configfs`, creates a CDC-ACM configfs gadget, binds the first available UDC, reads the `ttyGS0` major/minor from sysfs, and emits:

```text
A02 ARM64 boot probe: PID 1 entered; uname.machine=aarch64
```

The syscall numbers used by the freestanding implementation follow Linux's [AArch64/asm-generic syscall definitions](https://github.com/torvalds/linux/blob/master/include/uapi/asm-generic/unistd.h). The gadget setup follows the Linux [configfs gadget interface](https://docs.kernel.org/usb/gadget_configfs.html) and [ACM gadget testing documentation](https://docs.kernel.org/usb/gadget-testing.html). The host-side PowerShell script opens a user-selected COM port, asserts DTR, reads for a bounded interval, sends no serial payload, and returns `INCONCLUSIVE` on timeout. A port-open or driver error also cannot be interpreted as kernel failure.

The code has passed offline ELF/CPIO/gzip and syntax checks, but the phone's UDC, host enumeration, Windows COM creation, and marker transmission have **not** been tested. The candidate uses the configfs sample-style VID/PID `1d6b:0104`; this is not a project-assigned USB identity. Before any hardware use, replace it with an appropriate identity under a separately reviewed source revision and verify Windows driver behavior. The retained candidate's source behavior was not silently changed during this publication update.

## Addresses, memory, and boot-chain limits

The image declares kernel load address `0x40080000`, DT table address `0x44000000`, and ramdisk address `0x45000000`. Adding the Image header's declared `image_size` to the declared kernel start gives the conservative arithmetic end `0x42048000`; this is below the DT and ramdisk addresses. If a 50 MiB LK gzip capacity began at `0x40080000`, its arithmetic end would be `0x43280000`, also below those addresses. That is only a scenario calculation: the LK branch's real decompression output/scratch addresses, relocation behavior, full memory map, and Trusty ownership have not been established. The FDT carries the source-derived reserved-memory and TEE/Trusty description documented in the device-tree audit, but it cannot establish that LK honors the assumed placement.

The recorded PIT capacity for the single `boot` partition is 25,165,824 bytes (24 MiB). The current image is smaller by 13,348,864 bytes. This is a capacity check only. It says nothing about Odin mapping, image authentication, LK parsing, K64 branch selection, AArch64 entry state, or successful kernel decompression.

The inspected stock boot image is Android header v2 with 2,048-byte pages and an ARM32 zImage. Its stock kernel address is `0x40008000`; stock header metadata also includes Samsung signing and AVB structures. The experimental image instead carries the AArch64 gzip kernel and base-DT table described above and has **no AVB footer or Samsung signer trailer**. The public record compares structure and hashes only; it does not redistribute or reproduce the protected firmware image. Static LK inspection found a compiled K64-labelled SMC/gzip path (`0x82000115` and a 50 MiB argument in one path), but runtime selection and acceptance remain **UNVERIFIED**. User-reported unlocked/Orange and Odin-detection observations do not prove acceptance of this particular unsigned image.

## Offline results versus device evidence

| Check | Result | What it establishes |
| --- | --- | --- |
| Candidate SHA-256 and byte count | **PASS (offline)** | The local candidate matches the recorded 11,816,960-byte digest. |
| Android v2 header, section sizes, page padding, DT table | **PASS (offline parse)** | The byte layout is internally consistent and within the recorded PIT capacity. |
| Kernel gzip, decompressed AArch64 Image header/hash | **PASS (offline)** | The payload decompresses to the expected AArch64 Image bytes. |
| Init ELF64/AArch64, no dynamic interpreter, CPIO/gzip contents | **PASS (offline)** | The root archive contains the intended minimal static PID 1 and expected nodes. |
| ConfigFS/ACM/MTK OTG config symbols | **PASS (configuration only)** | Support is selected in the saved kernel configuration; a live UDC is not established. |
| LK/AVB accepts this candidate; live K64 handoff | **UNVERIFIED** | Only compiled LK logic and stock metadata have static analysis. |
| Phone runs the AArch64 kernel and reaches `/init` | **UNVERIFIED** | No candidate image has been written or booted on the phone. |
| USB UDC enumeration, Windows COM port, marker receive | **UNVERIFIED** | Host and device behavior has not been exercised. |
| Android ARM64 or `arm64-v8a` app execution | **NOT ACHIEVED** | This probe is not Android userspace. |

## Observation, recovery, and authorization gate

A positive result requires the host to receive the exact marker with `uname.machine=aarch64`. That would prove this kernel reached the intended AArch64 PID 1, but not Android, graphics, radios, stability, or app support. A black screen is expected for this minimal process. No COM port, no marker, or a reader error is **inconclusive**, because execution may have stopped before `/init`, configfs, UDC binding, or host enumeration.

The current flash decision remains **BLOCKED / NO-GO**. There is no retained proof of a current independent user-data backup; the single `boot` partition has no A/B fallback; Odin's handling of the one-member candidate and stock-boot rollback packages has not been tested; full-firmware recovery can erase data; and neither LK/AVB acceptance nor a reliable physical observation path has been demonstrated. The prior Odin recognition and device-state values are user-reported, not preserved raw captures. Review [flash readiness](flash-readiness.md) and [Odin recovery readiness](odin-recovery-readiness.md) before any future proposal.

No phone command, reboot, partition write, or flash occurred while preparing this record. The candidate and Odin TARs are excluded from the public tree. Any hardware test requires a separate risk review and the owner's explicit approval of the exact write, reboot, observation, and recovery sequence.

## References

- [AOSP boot image header definitions](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/master/include/bootimg/bootimg.h)
- [Linux ARM64 boot protocol](https://docs.kernel.org/arch/arm64/booting.html)
- [Linux configfs USB gadget interface](https://docs.kernel.org/usb/gadget_configfs.html)
- [Linux ACM gadget testing](https://docs.kernel.org/usb/gadget-testing.html)
- [AOSP verified boot device state](https://source.android.com/docs/security/features/verifiedboot/device-state)
