# Phase 6 — Minimal AArch64 Boot Proof: Offline Implementation and Postflight

**Investigation date:** 2026-10-24
**Device:** Samsung Galaxy A02 SM-A022F, MT6739, reference firmware `A022FXXS3BWH1`
**Scope:** Local-only construction and read-only validation. No phone access, kernel rebuild, flash, or Android ARM64 build.

## Executive summary and research question

The official device software uses an ARM32 kernel and 32-bit Android, although its Cortex-A53 CPU supports AArch64. Phase 6 asks a narrower question than the project's final goal: can the matching boot chain enter an AArch64 kernel and execute a minimal AArch64 PID 1? A positive device result would require an attributable marker captured from the phone. Phase 6 produced an **unsigned, local-only Android boot-header-v2 layout** and verified its bytes offline. It has **not** been submitted to the device. It is neither a usable Android ROM nor an authorized flash image.

The final local candidate is **11,814,912 bytes**, SHA-256 `a523d16f1810b07c39144bc4aaf112d2acb7667236378faae8904afe3f879952`. Its evidence must not be transferred to the earlier 11,816,960-byte USB-ACM candidate documented in the [historical boot-image record](../minimal-aarch64-boot-image.md). Phase 4 established scoped source/tool identity; [Phase 5](phase5-controlled-aarch64-rebuild.md) supplied the frozen Build 1 `Image`. The Phase 5 build pair remains non-identical; no WLAN-date correction or additional kernel build occurred here.

## Frozen kernel and tool provenance

The input was Phase 5 Build 1 from the experimental Samsung-source copy, built for `ARCH=arm64`, `MTK_PLATFORM=mt6739` with Android Clang/LLD r383902 **11.0.1**. The retained `frozen-kernel.json` rehashed each existing artifact against the Phase 5 record. Clang SHA-256 was `c3d0831fad23a7a73d41b66aad9cb7dc5f8fc09943dc90d473b06bd2521fa907`.

| Frozen file | Bytes | SHA-256 | Evidence scope |
| --- | ---: | --- | --- |
| `arch/arm64/boot/Image` | 28,323,856 | `f68ec016d5fcb6d1630a509381f72b7009df28d12256c90a508977da18af5d8f` | AArch64 `ARM\x64` Image header; `text_offset=0x80000`, declared `image_size=33,325,056` |
| `vmlinux` | 280,599,856 | `01e3a3c398f7b19fa8e61f95dbbc63864dfa0ab2631b05b33b6675e27cc55383` | ELF64 AArch64, build scope only |
| `System.map` | 5,125,657 | `c88c2084277b1d7351a415ebd68cecf0e192dd382bb2aae70032c23b6ef2b567` | Matched retained Phase 5 record |
| `.config` | 157,806 | `cf28ea2d10ed44db355ef454ab9cc395b0ae2c82d870e396cba1bc8a197ef354` | Matched retained Phase 5 record |

The frozen configuration has `CONFIG_BLK_DEV_INITRD=y`, `CONFIG_RD_GZIP=y`, `CONFIG_BINFMT_ELF=y`, and `CONFIG_CMDLINE_FROM_BOOTLOADER=y`; `CONFIG_INITRAMFS_SOURCE=""`. The first three support the proposed external gzip `newc` archive and ELF `/init` **if** the bootloader passes the archive's address and size to Linux. They do not establish that LK will do so. The built-in kernel command line is a fallback, not a proven effective runtime command line when the bootloader supplies `/chosen/bootargs`. See [reproducibility](../reproducibility.md) for external inputs and [kernel QA](../kernel-qa.md) for earlier build limits.

## Minimal PID 1 and deterministic initramfs

The isolated `init_console.c` is a freestanding, statically linked AArch64 probe. It uses direct Linux syscalls for `getpid`, `uname`, `openat`, `write`, `close`, and `nanosleep`. After verifying PID 1 and obtaining `uname`, it repeatedly writes the marker below to `/dev/console` and `/dev/kmsg`:

```text
A02-PHASE6-PROBE kernel=f68ec016d5fcb6d1 pid=1 uname.machine=aarch64
```

The hash prefix expresses intended provenance; the program cannot authenticate the running kernel by itself. It contains no USB gadget identity or partition-writing path. Because the owner has no authorized USB VID/PID, the later corrected but untested [USB-ACM source](../../probes/minimal-aarch64-usb-acm/) was **not** used to create this Phase 6 binary. The older USB binary's ConfigFS defect is historical, not a defect silently repaired in this image; see [CS-05](../case-studies/05-usb-configfs-probe.md).

The first isolated compile stopped under `-Werror` because of a nested aggregate initializer. Replacing that initializer with `{0}` produced a successful compile/link. A subsequent repeat yielded the same `/init` digest but a different CPIO digest: three changed bytes were traced to the source-file timestamp field. The build helper then set `/init` mtime to epoch zero before archiving. **Two later fresh probe builds** produced identical ELF, CPIO, and gzip hashes. This demonstrates deterministic probe packaging within those tested conditions; it does not repair Phase 5 kernel reproducibility.

| Probe artifact | Bytes | SHA-256 | Check |
| --- | ---: | --- | --- |
| `/init` | 1,968 | `a4a634d46c654033cf2c08175048db01f9b2791808b8eb0594a0b917dbeaedb6` | Little-endian AArch64 ELF64 `ET_EXEC`, `PT_LOAD`, no `PT_INTERP`/`PT_DYNAMIC`; executable mode `0755` in archive |
| `initramfs.cpio` | 3,072 | `561b1d8db3df817f2330d743f96f9bc1279b206986d4a9876b0525106b909164` | `newc`; `dev/`, character nodes `dev/console` (5:1), `dev/kmsg` (1:11), `/init`, trailer |
| `initramfs.cpio.gz` | 977 | `4e80b576e67e86e3b6f6272a145bde71beb53e3143f424a10d0afa8f52779bb3` | gzip round trip and two-build byte identity |

The source, build helper, logs, binaries, repeat-build files and their SHA manifest remain in the local Phase 6 evidence directory. They are **not** part of this publication proposal. The retained source SHA-256 is `a0573095e67d6ce803b9f9f09057c43218f8bd43cff7bd30e2cdbf37b8adc084`; the retained `build_console.sh` SHA-256 is `7afde5d1dc9ad66aa8efe1c209b2d50b46ac516325e0c505999f2eafabfbea85`. Their build used the retained Clang/LLD and kernel `usr/gen_init_cpio` without rebuilding the kernel. No runtime execution was tested.

## Boot-header-v2 construction and artifact chronology

The isolated packer accepted the exact matching stock boot input only after a SHA-256 preflight, then copied selected header/DT-table metadata, used the frozen Image, source-built base FDT, and final console-only initramfs. The stock image, firmware, packaged candidate, and executable initramfs are not redistributed. The initial packer preflight caught a **mistyped expected ramdisk digest before any candidate was written**; measuring the unchanged input and correcting the constant allowed packaging. A later timestamp correction produced a **new final artifact**, leaving the intermediate artifact intact.

| Artifact | Bytes | SHA-256 | Relationship |
| --- | ---: | --- | --- |
| Earlier USB-ACM candidate | 11,816,960 | `1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450` | Historical kernel/probe; unprefixed ConfigFS VID; not Phase 6 |
| First Phase 6 intermediate | 11,814,912 | `9f285950263bd26133570696d0222a0a947c8e6009354c4fef68c85b2341cdc5` | Timestamp-variable ramdisk; superseded |
| **Final Phase 6 local layout** | **11,814,912** | **`a523d16f1810b07c39144bc4aaf112d2acb7667236378faae8904afe3f879952`** | Frozen Phase 5 Build 1, deterministic console-only ramdisk; current offline candidate |

The final byte-derived header fields are `ANDROID!`, version **2**, header **1,660 bytes**, page **2,048 bytes**, `kernel_addr=0x40080000`, `ramdisk_addr=0x45000000`, and `dtb_addr=tags_addr=0x44000000`. `second_size` and `recovery_dtbo_size` are zero. The header cmdline is `bootopt=64S3,32S1,32S1 console=ttyMT0,115200n8 loglevel=8 ignore_loglevel`; LK's effective FDT bootargs remain unverified. Neither this cmdline nor the packaged base FDT bootargs explicitly requests `skip_initramfs` or overrides `/init`.

| Packaged component | Header-derived offset | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Gzip AArch64 kernel | 2,048 | 11,742,490 | `9c8d4e87f8fdd9392d579453d89ea4df5f74fc3b9cb9471a5c110720790a0efb` |
| Gzip `newc` ramdisk | 11,745,280 | 977 | `4e80b576e67e86e3b6f6272a145bde71beb53e3143f424a10d0afa8f52779bb3` |
| One-entry Android DT table | 11,747,328 | 65,740 | `b577da1f246ba2e9cbcf0540ad68e648daeb3e5cc78e049c768d4a217b57caeb` |

The compressed kernel inflates to the exact frozen raw Image. The DT table embeds a 65,676-byte base FDT with SHA-256 `b5314ec277200b532aba7d1302a86abd84ba878a78f3c7216c093a2f21cb825b`. The complete image is below the recorded 25,165,824-byte single-boot-partition capacity by **13,350,912 bytes**. This is a capacity check, not an Odin mapping or bootloader acceptance check. The candidate has **no Samsung signer trailer or AVB footer** and is not an Odin package.

## Device Tree, addresses, and LK limits

The source-built SM-A022F base tree preserves the Samsung MT6739/K39 board description. The earlier [source-build audit](../device-tree-source-build-qa.md) found its r00/r01/r06 merged trees semantically equal to matching official-derived references except for the intentional ARMv8 PMU `compatible` change; the overlays matched byte-for-byte. Phase 6 rechecked the saved FDT and overlay hashes. The package contains the **base** FDT in the DT table, not a premerged board-revision tree; actual DTBO selection/application at boot remains unverified.

The base FDT describes RAM `0x40000000..0x60000000`, fixed reservations from `0x48400000` and `0x4b000000`, plus dynamic/unmapped `consys-reserve-memory` and Trusty/TEE nodes. Static comparison found no **fixed-reservation** overlap with the declared AArch64 Image range `0x40080000..0x42048000`, the DT-table scenario at `0x44000000`, or the compressed ramdisk scenario at `0x45000000`. A hypothetical 50 MiB inflate output beginning at `0x40080000` also avoids those fixed ranges. This does not establish actual LK decompression/scratch addresses, dynamic allocation, secure-world ownership or the final FDT pointer.

The Image header's `text_offset=0x80000` supports the intended `0x40000000 + 0x80000 = 0x40080000` entry arithmetic. Static analysis of the matching LK found compiled K64-labelled SMC/gzip logic. It **does not** establish that normal boot selects K64, accepts this unsigned layout, uses the declared addresses, or hands the FDT to the kernel at the required execution level. See [LK handoff](../lk-handoff.md) and [CS-04](../case-studies/04-boot-header-v2-layout.md).

## Independent offline validation and targeted postflight

The original Phase 6 validator rereads the candidate and checks its digest, header magic/version, padding, gzip-to-Image identity, ramdisk equality, DT-table/FDT hashes, addresses and AOSP image-ID. It also parses a separately retained CPIO and ELF. **It is not wholly independent of the packer:** section offsets, expected hashes and capacity come from the packer's `audit.json`, and its CPIO parse is of the separate ramdisk whose bytes it first compares with the packaged section.

The subsequent **read-only postflight** used a separate parser that derived section sizes and aligned offsets from the actual candidate header, checked that they exactly consume the file, decompressed the **embedded** kernel and ramdisk, parsed the embedded `newc` entries and executable `/init` mode, and measured the embedded FDT. It did not use `audit.json` for those boundaries. It confirmed the final candidate size and digest, frozen Image digest, ramdisk digest and 65,676-byte FDT digest above. This provides a second implementation of the container-boundary check; it remains an offline format test, not a boot test. The postflight's one-off parser/output is retained in the Work execution record rather than published as a reusable tool.

The exact frozen `.config` has `CONFIG_BLK_DEV_INITRD=y`, `CONFIG_RD_GZIP=y`, and `CONFIG_BINFMT_ELF=y`. Source inspection found the external-initramfs path, default `/init` attempt, and FDT parser's dependence on `/chosen/linux,initrd-start` and `/chosen/linux,initrd-end`. **The packaged base FDT contains neither initrd property.** LK must supply suitable properties in the actual FDT handed to Linux. Their names occur in the inspected LK, but static presence does not prove that this path executes for the candidate. `CONFIG_CMDLINE_FROM_BOOTLOADER=y` also means the packaged header's cmdline alone cannot establish Linux's effective bootargs. These are concrete handoff dependencies, not evidence that `/init` has failed on the phone.

## Troubleshooting outcomes and remaining gates

| Problem | Investigation and observed result | Current scope |
| --- | --- | --- |
| Initial probe compile stopped under `-Werror` | The aggregate initializer was corrected to `{0}`; static ELF64 AArch64 compile/link then passed. | **RESOLVED — COMPILE/LINK ONLY**; no runtime |
| Repeated CPIO output changed with identical ELF | Three archive bytes tracked to the `/init` source mtime field; setting mtime to epoch zero yielded two byte-identical repeat outputs. | **RESOLVED — OFFLINE VALIDATION ONLY** |
| Initial packer rejected an expected-input digest | The digest constant was corrected from a fresh measurement of the unchanged ramdisk before packaging. | **RESOLVED — OFFLINE PREFLIGHT ONLY** |
| Validator and packer shared `audit.json` assumptions | A separate read-only parser derived boundaries from actual header bytes and checked embedded content; original validator's independence claim was narrowed. | **PARTIALLY RESOLVED**; reusable validator correction is not implemented |
| Base FDT omits initrd address properties | Kernel source requires them for the external archive; LK contains matching property names, but its actual candidate handoff is unknown. | **UNRESOLVED / UNVERIFIED RUNTIME** |
| No authorized USB identity or verified alternate observation channel | Phase 6 omitted USB identity and wrote a console/kmsg marker. Neither an SM-A022F UART path nor persistent-log readback is proven. Silence would be inconclusive. | **BLOCKED** for attributable device test |
| Recovery and authentication | Candidate is unsigned; LK/AVB acceptance, tested one-member Odin rollback, independent current data backup and post-failure Download Mode access are unproven. | **BLOCKED / NO-GO** for flashing |

The `/dev/kmsg` write does not imply that the message survives a failed boot. The frozen config includes pstore options, but no proven ramoops FDT/backend and readback path exists. The separate RAM-console ABI and `SEC_DEBUG` problems remain open; their presence should not be recast as Phase 6 failures or solved runtime functions.

## Lessons and reproducibility boundary

1. Pin an exact kernel artifact when later packaging work must not inherit an unexplained rebuild difference. A frozen digest establishes identity, not device compatibility.
2. Make tiny archive inputs deterministic at the file-metadata level, then compare two fresh outputs; a stable ELF alone is insufficient.
3. Parse a boot image from its own header bytes. Rechecking offsets copied from the packer's audit can preserve a common mistake.
4. A boot header can contain a ramdisk while the final Linux FDT still lacks the properties needed to deliver it. Verify the handoff contract separately.
5. A marker program is only evidence of execution if a reliable, attributable channel captures it. Console writes with no known capture path do not supply that evidence.
6. Keep historical candidates and their hashes distinct. A source correction or later artifact never retroactively validates an earlier binary.

The retained local record includes `PHASE6_MINIMAL_AARCH64_BOOT_PROOF_REPORT.md` (SHA-256 `f69c7114c8e144c233cd3b4a738a2db9e6a123d24574ec305ac31cdae5a51340`), `frozen-kernel.json`, `offline-validation-final.json`, the final `audit.json`, `device-tree-inspection.json`, `memory-layout-final.json`, exact source/build scripts, and `PHASE6_SHA256SUMS.txt`. The original report contains local paths and discusses non-redistributable inputs; this sanitized account publishes conclusions and digests, **not** raw logs, firmware-derived bytes, kernel binaries, or the boot candidate. Authorized Samsung source and matching firmware remain external. The public repository alone cannot recreate the exact candidate byte-for-byte.

## Readiness and next research gates

| Decision | Status | Evidence boundary |
| --- | --- | --- |
| **OFFLINE BOOT IMAGE READINESS** | **CONDITIONAL GO** | Header-derived layout, component identities, ELF/newc/gzip/FDT checks and recorded capacity arithmetic pass; runtime handoff and acceptance remain conditional. |
| **DEVICE TEST READINESS** | **NO-GO** | No proven attributable observation channel; initrd FDT handoff and exact boot-chain behavior remain unverified; current independent data backup and tested recovery are absent. |
| **FLASH READINESS** | **BLOCKED / NO-GO** | Candidate is unsigned and local-only; no approval or tested recovery path exists. |

The shortest useful next investigation is to establish a justified observation route and a reviewed data-backup/rollback plan, then resolve the exact LK-to-kernel initrd/FDT handoff question as far as offline evidence permits. Whether LK/TEE accepts the candidate and whether `/init` executes require a separately approved hardware experiment. Android ARM64 userspace and `arm64-v8a` application execution remain future goals.

## Technical references

- [AOSP boot image header definitions](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h)
- [Linux AArch64 boot protocol](https://docs.kernel.org/arch/arm64/booting.html)
- [Device Tree source-build QA](../device-tree-source-build-qa.md)
- [Flash readiness](../flash-readiness.md) and [Odin recovery readiness](../odin-recovery-readiness.md)
