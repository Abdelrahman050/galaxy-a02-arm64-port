# Notices and Attribution

This repository is an independent research project and is not affiliated with Samsung or MediaTek.

- Samsung source files and device-specific materials remain the property of their respective copyright holders. The authorized source archive is not redistributed here. The exact 12 public patches reviewed in [`docs/license-review-2026-10-20.md`](docs/license-review-2026-10-20.md) carry GPLv2 or GPLv2-or-later source notices. The original 13-patch collection includes a firmware-derived device-tree patch with unresolved redistribution rights; that file is retained in the local development copy and excluded from the public Git index and archive. The source-backed PMU adaptation preserves the intended engineering change without including firmware-derived DTS context.
- MediaTek copyright notices in upstream source remain intact. No proprietary MediaTek vendor libraries or firmware are included.
- Linux kernel code in the reviewed patch targets is licensed under GPL version 2, with one SEC_DEBUG header allowing version 2 or any later version. Do not remove upstream copyright or SPDX headers when applying patches.
- Documentation, configuration, scripts, and the freestanding `/init` probe/host reader in this staging repository are original project material offered under the repository license unless a file states otherwise. This does not relicense third-party code or firmware.
- Exact firmware and source-archive hashes are recorded only as provenance identifiers. Hashes do not grant a right to redistribute the corresponding files.

Third-party tools such as Clang, GCC/binutils, DTC, `fdtput`, `fdtoverlay`, and Python are external dependencies and are not bundled.
