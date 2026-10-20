# Offline Boot Layout Audit

The Phase 2 work assembled unsigned Android boot-header-v2 layout prototypes in an isolated local work area. The prototypes used an AArch64 kernel image, a minimal AArch64 initramfs, and a device-specific base FDT. The later candidate retained the stock image's base-DTB-plus-DTBO arrangement rather than pre-merging an overlay.

## Findings

- The raw AArch64 `Image` exceeded the recorded 24 MiB boot partition capacity.
- Gzip-compressed payload layouts fit by size; one recorded unsigned layout was about 11.8 MB.
- Header and section-size checks were static arithmetic based on inspected boot/PIT inputs.
- The candidate layout was not signed or accepted by LK/AVB, and its LK decompression destination and runtime memory map were not proven.
- DTBO selection by the exact LK path remains unverified.
- No output image or initramfs binary is included in this repository.

The original prototype builder and generated image audits are not included because they create firmware-derived boot artifacts. The reports retain the findings and limitations without packaging an experimental image. The unsigned layout is **not flashable** and must not be treated as a candidate ready for device use.

For the current readiness blockers, see [`flash-readiness.md`](flash-readiness.md). For address and device-tree evidence, see [`device-tree-bootloader.md`](device-tree-bootloader.md) and [`lk-handoff.md`](lk-handoff.md).
