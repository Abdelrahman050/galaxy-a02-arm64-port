# Licensing and Content Audit

## Redistribution boundary

The repository staging package excludes the complete Samsung source archive, official AP/BL/CP/CSC firmware, firmware images and partition tables, proprietary vendor blobs, bootloader/TEE binaries, generated kernel images, DTB/DTBO binaries, initramfs binaries, local backups, and credentials. Only source patches, configuration, scripts, and reviewed written reports are staged.

The full Samsung open-source archive used for the study is identified in [`reproducibility.md`](reproducibility.md) by archive member names and hashes, without a user-specific path. Archive metadata and hashes are provenance references, not redistributed contents.

## License review

The exact local Samsung kernel source package was reviewed on 2026-10-20 without extracting the full archive. The reviewed `Kernel.tar.gz` SHA-256 is `0e16a5dce007a91f6215a194c534cb9cf84fcf8fff021609cc47f344cfcc1f27`. `README_Kernel.txt` contains build instructions (`ARCH=arm`, `arch/arm/boot/Image.gz`) and no additional redistribution terms. The archive's top-level `COPYING` is GNU GPL version 2; source headers for the kernel-backed patch targets are summarized in [`license-review-2026-10-20.md`](license-review-2026-10-20.md).

The exact public subset contains 12 patches with reviewed GPLv2 or GPLv2-or-later provenance. The local `patches/device-tree/0001-a02-arm64-pmu-compat.patch` targets decompiled firmware DTS context. No source header or independent redistribution grant was available, so the original 13-patch collection is not cleared. That file remains unchanged in the local worktree and is excluded from the public index, checksum manifest, and release archive. The source-based PMU patch and `prepare_stock_port.py` preserve its engineering function without redistributing its firmware-derived context. See the patch-by-patch findings in [`license-review-2026-10-20.md`](license-review-2026-10-20.md).

**Decision:** License clearance is **PASS for the exact 12-patch public subset** and **BLOCKED for the original 13-patch collection** until independent redistribution rights for the firmware-derived patch are established. No Samsung firmware, proprietary vendor library, source archive, or LK binary is staged. Root `LICENSE` applies to original repository material where no file-specific notice applies; it does not relicense upstream code or firmware. Build dependencies are external and must be obtained under their own licenses. This is a scoped provenance review, not legal advice or a blanket license grant.

## Repository hygiene checks

The included `scripts/repo_audit.py`, tests, and top-level `SHA256SUMS` provide repeatable checks for file inventory, manifest integrity, forbidden binary/archive suffixes, size limits, and a limited set of secret and local-path patterns. These checks are not comprehensive and cannot establish that every secret or legal issue has been found. Review file-level notices and source provenance before reuse.

## GitHub license classifier metadata

On 2026-10-21 the GitHub repository API reported `license.spdx_id=NOASSERTION` (`name=Other`). This is GitHub's content classifier result, not a license grant or a legal finding. The root `LICENSE` retains the existing GPL version 2 text and kernel notice; source patches retain their own reviewed GPLv2 or GPLv2-or-later provenance, while the original PMU patch remains excluded. The new freestanding probe and its helpers are original project material under the repository license. No SPDX identifier was added to the root file because doing so without a complete per-file SPDX review could incorrectly suggest one license applies to every upstream-derived file. No third-party rights were changed. The classifier result remains an explicit metadata limitation.
