# SM-A022F AArch64 device-tree source integration (bounded audit)

**Current result:** The next step proposed below has now been performed in an isolated build. Samsung's stock MT6739 base plus the existing A02 overlays and K39 includes reproduce all official r00/r01/r06 trees at the parsed FDT level, with only the intentional ARMv8 PMU compatible change. See the [completed source-build QA](device-tree-source-build-qa.md). The sections below retain the earlier generic-ARM64-base failure as engineering history; they do not describe the current best DT candidate.

## What was proved

* The ARM64 A02 board overlays are already present in Samsung's source. A copied `a02_eur_open_w00_r00.dts`, with its K39 dependencies copied from the ARM32 tree into the relative include paths, compiled with system DTC 1.7.2 (`-@`) to an **80,597-byte DTBO byte-for-byte identical to official `dtbo-0.dtb`**: SHA-256 `a4ef2a81cf0252909cced18e03979a5b332a7cc82b296710bfef89b25302af20`.
* The prior K39 compile failure was produced by the kernel's older DTC 1.4.4 when compiling this overlay independently. Its 44 distinct unresolved label messages are misleading as a measure of genuinely absent source labels. Modern DTC records 42 external fixups; 41 resolve against the source-built ARM64 MT6739 base. The single absent symbol is `soc_codec`.
* The ARM64 MT6739 base already contains the corresponding `mt_soc_codec_name` node, but omits its `soc_codec:` label. The isolated one-line [patch](../patches/device-tree/0002-arm64-mt6739-soc-codec-label.patch) restores that label. After applying it only to a staged copy, the ARM64 base and official-equivalent A02 r00 overlay compile and merge successfully (`source-integration/mt6739-a02-r00-merged.dtb`). This is a **source-build milestone, not an official-equivalent or boot-ready DTB**.

## Exact source/include graph

Relative to Samsung's kernel source root:

| Source | Direct dependency or role |
| --- | --- |
| `arch/arm64/boot/dts/mediatek/mt6739.dts` | Generic ARM64 MT6739 base; includes `mediatek/cust_mt6739_msdc.dtsi`, `mediatek/trusty.dtsi`, PMIC `mediatek/mt6357.dtsi` or `mt6356.dtsi`, conditional charger files. Does **not** include Samsung modem pdata unlike stock ARM32 base. |
| `arch/arm64/boot/dts/mediatek/a02/a02_eur_open_w00_r00.dts` | Board r00 overlay; includes `../../k39tv1_bsp_titan_hamster.dts`, `../../k39tv1_bsp_titan_hamster/gpio00.dtsi`, and `mt6739.a02_eur_open.00.dtsi`. |
| `arch/arm64/boot/dts/mediatek/a02/a02_eur_open_w00_r01.dts`, `a02_eur_open_w00_r06.dts` | Board r01/r06 overlays; use the same K39 main file, `gpio01.dtsi`, and `mt6739.a02_eur_open.01.dtsi`. |
| `arch/arm/boot/dts/k39tv1_bsp_titan_hamster.dts` | K39 board nodes and `&soc_codec` update; direct headers `generated/autoconf.h`, `dt-bindings/mmc/mt6739-msdc.h`, `dt-bindings/pinctrl/mt6739-pinfunc.h`. |
| `arch/arm/boot/dts/k39tv1_bsp_titan_hamster/gpio00.dtsi`, `gpio01.dtsi` | Hardware revision pin, GPIO, I2C and regulator updates; include IRQ/GIC bindings. Both define `i2c_lcd_bias_mtk` and refer to MT6739 base and PMIC labels. |
| `arch/arm64/boot/dts/mediatek/a02/mt6739.a02_eur_open.{00,01}.dtsi` | Each includes eight existing A02 files: `mt6739-a02_common`, `mt6739_a02_camera_00`, `mt6739_a02_eif_common`, `mt6739_a02_audio_common`, `mt6739_a02_sensor_r00`, `mt6739_a02_input_common`, `mt6739_a02_pm_common`, `display_lcd_a02_common`. |

Copy the three K39 files into the matching `arch/arm64/boot/dts/` paths in an **experimental copy only**. The ARM64 A02 overlay sources then need no content edits for the tested official firmware revision. The r00 overlay is byte-identical to official; earlier r01/r06 source overlays were also byte-identical to official. The full old-DTC label-to-definition mapping is in [`label-graph-audit.json`](device-tree-source-build-qa.md).

## Why the merged source tree is still not acceptable

The staged one-line label patch makes `fdtoverlay` succeed, but [`source-gap-audit.json`](device-tree-source-build-qa.md) reports 719 nodes versus 738 official nodes, 224 official paths absent, 205 extra paths, and 1,414 raw property differences. The raw property count includes widespread phandle renumbering and is **not** a count of independent device defects. Concrete incompatible changes are:

* The ARM64 generic base has only `/reserved-memory/consys-reserve-memory`; official has that plus CCCI modem dump and four Samsung SEC areas: `sec-log` at 0x4B000000, `sec-lastklog` at 0x4B200000, `sec-logger` at 0x4B400000 and `sec-autocomment` at 0x4B800000. The source-only conditional `sec-extrainfo` at 0x4B810000 is **absent in official firmware**; do not assume it may be safely enabled. `SEC_DEBUG` maps these physical addresses, so leave it disabled until reservations and runtime ownership are resolved.
* `/chosen:bootargs` differs; source-built ARM64 base adds `kaslr-seed`, uses `maxcpus=8` and different console/debug flags, while official A02 has `maxcpus=4` and its vendor bootargs. The bootloader may modify bootargs at runtime; the official DTB is the reproducible baseline.
* Generic ARM64 source omits `/teegris`, changes `/trusty` properties and adds `/nebula`; trust environment is therefore not equivalent.
* The stock base has Samsung modem pdata, audio and other platform content absent from the ARM64 generic base. Some paths also differ, such as official `/1000b000.pinctrl` versus ARM64 `/pinctrl@1000b000`, which makes direct overlay phandle equality insufficient to establish hardware equivalence.

## File-by-file next integration step

1. In an isolated worktree, start from **Samsung's ARM32 `arch/arm/boot/dts/mt6739.dts` and its included stock files** as the A02 board base for an ARM64 DT target. This has a shorter path to official DTB equivalence than retrofitting the generic ARM64 base. Change only `/pmu:compatible` to `arm,armv8-pmuv3` initially, then compile with the same Samsung configuration choices that produced official A02 nodes. Do not import an unrelated MT6739 board's GPIO or Trusty data.
2. Reuse the existing ARM64 `a02_eur_open_w00_r00/r01/r06.dts` and `mt6739.a02_eur_open.{00,01}.dtsi` files. Copy `k39tv1_bsp_titan_hamster.dts` plus `gpio00.dtsi` and `gpio01.dtsi` into the expected ARM64 relative paths. Keep the one-line `soc_codec:` fix only if the generic ARM64 base remains in use.
3. For each hardware revision, compile base and overlay using a DTC that supports `-@` overlays. Merge in staging. Compare **node paths, property bytes and FDT memory-reserve entries** to the official merged DTB. Acceptance for the first candidate: exactly one intentional difference, `/pmu:compatible`, as already demonstrated by the official-DTB-derived candidates and `build_candidates.py`. Preserve official `/chosen`, `/trusty`, `/teegris` and reserved-memory properties. A source-built tree that merely merges is not accepted.
4. Register the board-specific DTB and DTBO Makefile targets only after source equivalence is reached. Keep each revision's overlay and its patch separate for review. Runtime boot and driver compatibility remain unverified without a consented device test.

The verified official-DTB-derived AArch64 candidate set remains under `a02-arm64-r00/r01/r06-candidate.dtb` as a reference. The newer Samsung-source-build candidate reaches the same semantic target. Its remaining work is integration with a maintained DTC/build rule and runtime proof of LK handoff, binding compatibility and driver behavior. The old in-tree DTC 1.4.4 cannot build the A02 overlay as a standalone target; DTC 1.7.2 works in the isolated script.
