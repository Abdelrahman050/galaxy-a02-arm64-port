# Device Tree and Bootloader Assessment

This report separates offline source/image findings from behavior that still requires a device test. The exact Samsung source and firmware inputs are external and are not included.

## Device Tree

The best current ARM64 candidate uses Samsung's stock MT6739 base, the K39 dependencies, and the existing A02 board overlays. A source-based build was compared semantically with the official merged FDTs for r00, r01, and r06:

- node and property sets matched;
- memory reservations matched;
- only `/pmu:compatible` differed, intentionally changed from the ARM32 Cortex-A7 PMU string to the ARMv8 PMU compatible string;
- all three overlay DTBO files matched the official bytes.

This comparison is documented in [`device-tree-source-build-qa.md`](device-tree-source-build-qa.md), with the machine-readable audit and source hash manifest under [`evidence/`](evidence/). The helper scripts live in [`scripts/device-tree/`](../scripts/device-tree/). The result is not an in-tree `make dtbs` target and was not tested on the phone.

A generic ARM64 MT6739 base is not an acceptable substitute: the recorded comparison found missing secure/TEE-related content, boot arguments, and board-specific nodes. Preserve the matched Samsung base's reserved memory, Trusty/TEE integration, `/chosen` data, and board-specific overlays in any future integration.

## LK and architecture handoff

Static analysis found a compiled K64 SMC/gzip path in the inspected LK. The evidence includes an SMC call site using `0x82000115` and a 50 MiB gzip argument in one path. The final allocation meaning, branch condition, runtime address, exception-level state, and Trusty/TEE acceptance remain unknown. Static presence does not prove the device selects the branch or that it accepts an experimental kernel.

The LK binary, strings, disassembly excerpts, and cross-reference dumps are intentionally not redistributed. See the bounded [`LK handoff report`](lk-handoff.md) for the conclusion and its evidence limits.

## Boot image and memory arithmetic

The inspected stock boot image uses Android boot header v2 and an ARM32 zImage. Its recorded header has `kernel_addr=0x40008000`, `ramdisk_addr=0x45000000`, and a 2048-byte page size. The AArch64 kernel Image header reports `text_offset=0x80000`, `image_size=33,325,056` bytes, and flags `0xA`. Reusing the stock kernel address directly does not satisfy the AArch64 Image alignment arithmetic; `0x40080000` is a nearby arithmetically congruent example, not a proven LK destination.

The raw ARM64 Image is larger than the recorded 24 MiB boot partition. Gzip-based offline layouts fit by byte count and one unsigned header-v2 prototype was about 11.8 MB. This does not establish that LK decompresses to a safe region, that the FDT/ramdisk placement is valid with all reserved memory, or that AVB/signature checks accept the image. Generated layout binaries and raw boot/VBMeta parser outputs are excluded; see [`boot-layout-audit.md`](boot-layout-audit.md) and [`flash-readiness.md`](flash-readiness.md).

## Evidence status

| Claim | Status | Limit |
| --- | --- | --- |
| Board-specific FDT matches official r00/r01/r06 semantics | **PASS (offline)** | One intentional PMU property change; not runtime-tested. |
| DTBO overlays match official bytes | **PASS (offline)** | Does not prove LK selects the expected overlay. |
| LK contains a K64 path | **PASS (static)** | No proof of branch execution, TEE acceptance, or AArch64 kernel entry. |
| Candidate address and compressed layout fit arithmetic checks | **PASS (offline arithmetic)** | No proof of actual load, decompression, memory safety, signing, or acceptance. |
| Experimental image accepted by LK/AVB | **UNVERIFIED** | No candidate-specific device result. |
| Kernel reaches `/init` on the phone | **UNVERIFIED** | No observed boot or reliable hardware log capture. |

The overall flash decision remains **NO-GO**. The user-reported unlocked/Orange/Download Mode observations documented separately do not change the candidate-image acceptance status.
