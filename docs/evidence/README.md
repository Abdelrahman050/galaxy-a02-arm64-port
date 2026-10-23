# Curated Evidence Files

This directory contains text-only, sanitized output needed to inspect specific Phase 2 claims: DWARF field layouts, a CSV field-offset comparison, the isolated RAM-console object-build log, the source-tree difference summary, and the Device Tree source-build audit/manifest. It does not contain kernel/firmware/vendor binaries or raw LK disassembly.

The [Phase 4 live source and toolchain integrity report](phase4-live-integrity.md) summarizes a later read-only WSL collection: source-file hash coverage, symlink state, installed tool identities, patch-content comparison, and the scoped build-readiness decision. It is a sanitized summary; raw machine-specific manifests and collection output remain local.

The [Phase 5 controlled AArch64 rebuild case study](phase5-controlled-aarch64-rebuild.md) documents two successful fresh-output builds, their non-identical linked code/data, and the confirmed WLAN wall-clock build-date input. It separates that scoped root cause from the unresolved full-image reproducibility question. Full logs and binaries remain local; this report contains hashes and derived measurements only.

The Phase 2 evidence files are snapshots of local checks. Local machine paths in the RAM-console object log and DWARF output are replaced with `$PROJECT_ROOT`. [`dt-pmu-source-replacement-equivalence.json`](dt-pmu-source-replacement-equivalence.json) records the 2026-10-20 source-helper recheck and structural comparison of saved r00/r01/r06 DTBs; it explicitly records that those DTBs were not freshly compiled in that recheck. Other Phase 2 reports are historical snapshots; their presence does not claim that every check was rerun from this publication tree. See [`../testing.md`](../testing.md) for scope and limits.
