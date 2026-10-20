# LK and AArch64 Handoff Findings

Static inspection of the matching Samsung LK image found a compiled K64 handoff path with an SMC call site and a gzip handling branch. The analyzed references included SMC function ID `0x82000115` and a 50 MiB gzip argument in one path.

This is evidence that code for a K64 route exists in the inspected LK binary. It does **not** prove:

- that the SM-A022F runtime state selects the K64 branch;
- that the tested bootloader and TrustZone firmware permit an AArch64 kernel;
- that the candidate `Image.gz` is loaded or decompressed at the calculated address;
- that LK passes the expected register state, FDT pointer, reserved-memory map, or DTBO;
- that AVB or Samsung signature checks accept the candidate image; or
- that control reaches the kernel or `/init` on the device.

The LK binary, disassembly excerpts, strings, and cross-reference dumps are excluded from this repository. Their firmware-derived content is not necessary to publish the summarized finding. Exact reference-image hashes are in [`reproducibility.md`](reproducibility.md).

The next reliable proof requires a controlled, owner-authorized hardware experiment with a reviewed exact image, a dependable early-log channel, and a recovery plan. Until then the handoff remains **UNVERIFIED at runtime** and flash readiness remains **NO-GO**.
