# Patch Series and Provenance

The source archive is external. Apply kernel patches only to a separate writable copy of the matching Samsung kernel source. Preserve the original archive and clean build outputs. Review the diff and source revision before applying.

## Kernel patches

Apply `0001` through `0007` in numeric order for the recorded experimental build. They export pstore/RAM-console symbols, correct a MediaTek platform comparison, and fix PowerVR device-node arguments and power-state handling. Patches 0001–0003 passed a historical `patch --dry-run -p1` against the matching source. Patches 0004–0007 compiled and linked in isolated output directories. These results do not prove runtime stability.

The `candidates/` series is not part of the recorded Image:

- `0008`: RAM-console legacy-aware ARM64 layout; isolated object build and offline layout checks only.
- `0009` and `0010`: SEC_DEBUG architecture candidates; reviewed, not built with SEC_DEBUG enabled.

## Device-tree adaptations

`device-tree/` holds separate DTS changes for staging an A02-specific ARM64 tree from Samsung source. These are not kernel patch-series entries 0001–0010 and must be reviewed against the exact source revision. The public route uses Samsung's GPLv2 stock MT6739 DTS and changes only `/pmu:compatible` to `arm,armv8-pmuv3`; `scripts/device-tree/prepare_stock_port.py` performs this change on an isolated copy while preserving all other source bytes and headers. The public tree contains `0001-sm-a022f-stock-base-armv8-pmu.patch` and `0002-arm64-mt6739-soc-codec-label.patch`. The generic ARM64 `soc_codec` label patch is an alternate-base integration fix, not needed by the stock-base route. No DTB/DTBO binary is included.

## Attribution and review

See [`../NOTICE.md`](../NOTICE.md), [`../docs/licensing-and-security.md`](../docs/licensing-and-security.md), and the [patch license review](../docs/license-review-2026-10-20.md). The local firmware-derived `device-tree/0001-a02-arm64-pmu-compat.patch` is intentionally absent from the public Git index and archive; `.gitignore` and the repository audit enforce that boundary. Its local copy remains unchanged. The exact 12-patch public subset has scoped GPLv2/GPLv2-or-later clearance. Patch acceptance must be checked against the exact source files by a maintainer with authorized source access. A patch parser or successful compile is not an ABI or runtime proof.
