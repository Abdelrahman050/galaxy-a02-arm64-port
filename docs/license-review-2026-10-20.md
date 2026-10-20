# License and Device Tree Patch Review

**Review date:** 2026-10-20
**Scope:** Samsung SM-A022F kernel source notices and the exact patch set proposed for the public archive. This is a source-provenance review, not legal advice.

## Samsung source evidence

The local Samsung Open Source package's `Kernel.tar.gz` was inspected read-only; no complete source tree was extracted. Its SHA-256 is `0e16a5dce007a91f6215a194c534cb9cf84fcf8fff021609cc47f344cfcc1f27`, matching the provenance value in [`external-inputs.md`](external-inputs.md). `README_Kernel.txt` specifies `ARCH=arm` and `arch/arm/boot/Image.gz`; it adds no separate redistribution restriction. The archive's `COPYING` is GNU GPL version 2. Per-file headers were checked for all patch targets that exist in the archive.

## Device Tree patch finding

The local-only file `patches/device-tree/0001-a02-arm64-pmu-compat.patch` targets `a02-arm64-r00-candidate.dts`, a decompiled official-firmware tree that is not in the Samsung kernel source archive. Its hunk includes firmware-derived DTS context (`interrupt-parent = <0x02>` and numeric `interrupts` cells), as well as changing `/pmu:compatible` from `arm,cortex-a7-pmu` to `arm,armv8-pmuv3`. The change is small, but its origin and redistribution rights are not established by the kernel package. No independent firmware-DTS redistribution grant was available in the examined material. That uncertainty is not a conclusion that infringement occurred; it is a reason not to redistribute this particular artifact without a grant.

The PMU adaptation can be reproduced from Samsung's GPLv2 kernel source instead. The source contains the stock MT6739 base, K39 dependencies, and the SM-A022F r00/r01/r06 overlays. [`prepare_stock_port.py`](../scripts/device-tree/prepare_stock_port.py) takes an authorized, read-only source tree, validates the MT6739 root and exact stock PMU property, then writes a separate target containing the source files with precisely `/pmu:compatible` changed. It preserves all other DTS bytes and source notices. The public source-backed patch `device-tree/0001-sm-a022f-stock-base-armv8-pmu.patch` expresses that same PMU change against the GPLv2 stock base. The disputed firmware-context patch is not needed for this workflow.

The source-based helper was exercised against the Samsung archive by selectively extracting only 21 required DTS/DTSI members into a disposable test directory. Its emitted stock base matched the prior isolated source-stage file byte-for-byte (SHA-256 `be2a5934175f25214408b95330383c9915c3834a1caf8386ecf04619dd61dde4`). Existing compiled source-based r00/r01/r06 FDT candidates were then compared with the previous firmware-derived candidate FDTs: each had zero node/property differences and equal reservation maps. The `dtc` executable was unavailable in this Windows session, so no fresh compiled-DTB rebuild was performed here. Earlier recorded audits compare the source-built merged trees with official r00/r01/r06 merged trees, allowing only `/pmu:compatible`; this remains static evidence and does not establish boot or runtime compatibility.

The excluded local patch SHA-256 is `ad5ea2c72b1bd9ab3a3f7dddd236ba954f6d8003e6d4d081f8e762c4ec03749b`. It is excluded from Git staging, `SHA256SUMS`, and the public archive, while its local project and engineering copies remain intact.

## Public patch-by-patch notice review

The public release contains 12 patches. The following kernel source targets and headers were checked against the Samsung package:

| Public patch | Source target / notice found | Assessment for the public subset |
| --- | --- | --- |
| `0001-pstore-export-persistent-ram-vmap.patch` | `fs/pstore/ram_core.c`; Google notice, GPL version 2 | GPL-2.0; retain copyright and license notices. |
| `0002-export-ram-console-buffer.patch` | MediaTek RAM-console driver; GPL version 2 | GPL-2.0; retain attribution. |
| `0003-compare-mtk-platform-unquoted.patch` | MediaTek ECCCI Makefile; GPL version 2 | GPL-2.0; retain attribution. |
| `0004-powervr-use-device-node-in-dvfs.patch` | MediaTek `mtk_mfgsys.c`; GPL version 2 | GPL-2.0; retain attribution. |
| `0005-powervr-handle-unknown-power-state.patch` | Same `mtk_mfgsys.c` target; GPL version 2 | GPL-2.0; retain attribution. |
| `0006-powervr-optional-power-index-node-lock.patch` | Same `mtk_mfgsys.c` target; GPL version 2 | GPL-2.0; retain attribution. |
| `0007-powervr-guard-ged-power-state.patch` | Same `mtk_mfgsys.c` target; GPL version 2 | GPL-2.0; retain attribution. |
| `candidates/0008-ram-console-legacy-aware-arm64-layout.patch` | MediaTek RAM-console driver; GPL version 2 | GPL-2.0; candidate status does not change the notice. |
| `candidates/0009-sec-debug-guard-arm32-register-save.patch` | Samsung `sec_debug.c`; GPL version 2 | GPL-2.0; retain Samsung attribution and warranty notice. |
| `candidates/0010-sec-debug-select-aarch64-register-layout.patch` | Samsung `sec_debug.h`; GPL version 2 or any later version | GPL-2.0 option is explicit; retain attribution. |
| `device-tree/0001-sm-a022f-stock-base-armv8-pmu.patch` | Samsung-source-derived stock MT6739 DTS base; GPLv2 source header | GPL-2.0 source adaptation; provenance and original source notices are documented. |
| `device-tree/0002-arm64-mt6739-soc-codec-label.patch` | MediaTek ARM64 MT6739 DTS; GPL version 2 | GPL-2.0; separate generic-base integration fix, not needed by the stock-base route. |

The target headers identify GPL version 2 for the MediaTek and Samsung `sec_debug.c` files; `sec_debug.h` permits version 2 or any later version. No additional per-file exception or redistribution restriction was found for these 12 targets. The root [`LICENSE`](../LICENSE) supplies GPL-2.0-only terms for original repository material where applicable; it does not supersede upstream copyright or relicense excluded firmware content. See [`NOTICE.md`](../NOTICE.md) for attribution boundaries.

## Decision

**LICENSE CLEARANCE: PASS for the exact 12-patch public subset and the listed repository files, subject to preserving notices and complying with GPL-2.0 distribution obligations.**

**LICENSE CLEARANCE: BLOCKED for the original 13-patch collection as a whole.** The firmware-derived PMU patch remains local-only pending explicit rights to redistribute it. This is a bounded review of identified files, not a blanket legal guarantee for uninspected inputs or future changes.

The Samsung Platform source archive was not examined because none of the public patch targets the Platform source. No Samsung firmware, source archive, proprietary vendor library, bootloader binary, or compiled DTB/DTBO is included. Toolchains and build tools are external dependencies under their own terms.

References: [GNU GPL version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html); [Samsung Open Source Release Center](https://opensource.samsung.com/).
