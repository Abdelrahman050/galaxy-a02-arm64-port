# Curated Evidence Files

This directory contains text-only, sanitized output needed to inspect specific Phase 2 claims: DWARF field layouts, a CSV field-offset comparison, the isolated RAM-console object-build log, the source-tree difference summary, and the Device Tree source-build audit/manifest. It does not contain kernel/firmware/vendor binaries or raw LK disassembly.

The files are snapshots of local checks. Local machine paths in the RAM-console object log and DWARF output are replaced with `$PROJECT_ROOT`. [`dt-pmu-source-replacement-equivalence.json`](dt-pmu-source-replacement-equivalence.json) records the 2026-10-20 source-helper recheck and structural comparison of saved r00/r01/r06 DTBs; it explicitly records that those DTBs were not freshly compiled in that recheck. The other reports are historical snapshots. Their presence does not claim that every check was rerun from this publication tree. See [`../testing.md`](../testing.md) for scope and limits.
