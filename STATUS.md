# Engineering Status

Status labels apply only to the claim and evidence scope listed. `PASS` never implies a successful phone boot unless runtime evidence says so.

| Requirement | Status | Evidence and limit |
| --- | --- | --- |
| License clearance for exact public subset (12 patches) | **PASS (scoped)** | All 12 public patches have traceable GPLv2 or GPLv2-or-later source provenance, with notices retained/documented. The original 13-patch collection remains **BLOCKED** because one firmware-derived patch is excluded pending a separate redistribution grant. See [`docs/license-review-2026-10-20.md`](docs/license-review-2026-10-20.md). |
| AArch64 kernel build | **PASS (build only)** | Initial build and separate clean rebuild completed. Configuration and `System.map` matched; `Image`/`vmlinux` digests differed. No boot evidence. |
| MT6739 kernel configuration and `CONFIG_COMPAT` | **PASS (configuration/link only)** | Enabled in the saved ARM64 config and present in build evidence; on-device behavior untested. |
| PowerVR pointer/state patches | **PASS (compile/link only)** | Patches 0004–0007 compiled and linked in isolated outputs; no display/GPU runtime test. |
| SM-A022F device-tree semantic comparison | **PASS (offline comparison)** | Samsung MT6739 base, K39 dependencies, and A02 overlays matched official merged r00/r01/r06 trees in nodes, properties, and reserved memory except the intentional `/pmu:compatible` ARMv8 change. DTBO files were byte-identical. Not an in-tree target or boot test. |
| Source-based PMU adaptation reproducibility | **PASS (isolated source-copy test)** | The bounded helper ran on 21 selectively extracted Samsung DTS/DTSI inputs and emitted a stock base byte-identical to the prior source staging. Existing r00/r01/r06 source DTBs matched prior candidate DTBs structurally. No fresh DTC rebuild in this Windows session. |
| LK K64 support | **PASS (static presence only)** | Disassembly showed a compiled K64 SMC/gzip branch. Branch selection, final addresses, TEE acceptance, and runtime handoff are **UNVERIFIED**. |
| Current Minimal AArch64 boot image layout | **PASS (offline validation only)** | Local USB-ACM candidate is 11,816,960 bytes, SHA-256 `1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450`; v2 header, section hashes, gzip/ELF/CPIO/FDT parse, and 24 MiB size arithmetic were rechecked. The binary is excluded. See [`docs/minimal-aarch64-boot-image.md`](docs/minimal-aarch64-boot-image.md). LK/AVB acceptance and runtime placement remain **UNVERIFIED**. |
| Minimal AArch64 `/init` observation design | **PASS (offline source/artifact checks only)** | Static ELF64/AArch64 PID 1 and USB-ACM marker reader are source-reviewed and included without build outputs. UDC binding, COM enumeration, and marker reception remain **UNVERIFIED**. |
| User-reported device state | **UNVERIFIED (provenance-limited)** | Later report: `flash.locked=0`, `vbmeta.device_state=unlocked`, `verifiedbootstate=orange`, bootloader `A022FXXS3BWH1`, and Odin recognition in Download Mode. Raw capture/timestamp not retained. Does not prove candidate acceptance or recovery. |
| RAM-console ABI | **FAIL / OPEN** | ARM32 record is 0x468 bytes; ARM64 fallback is 0x368 bytes. Candidate compatibility patch passed object-only and offline layout checks, but is not linked into the tested full `Image`. |
| `SEC_DEBUG` ARM64 path | **FAIL / OPEN** | Disabled in the saved build. Candidate architecture guards are review-only and were not built with `SEC_DEBUG` enabled. |
| Android ARM64 userspace | **FAIL (not present in stock image)** | Inspected stock system/vendor are 32-bit and do not provide a verified 64-bit Android userspace. No ARM64 Android image has been built or booted. |
| ARM64 graphics/vendor stack | **FAIL / UNVERIFIED** | Stock graphics components inspected are ELF32. No compatible ARM64 mapper, gralloc, EGL/GLES, HWC, or Vulkan implementation has been verified. |
| `arm64-v8a` app execution on phone | **UNVERIFIED / NOT ACHIEVED** | No such application has been run on the device. |
| Flash readiness | **BLOCKED / NO-GO** | Candidate-image acceptance and K64 runtime handoff are unknown; USB observation is not hardware-validated; no independent current data backup or tested Odin boot-only rollback mapping is documented. See [flash readiness](docs/flash-readiness.md) and [Odin recovery readiness](docs/odin-recovery-readiness.md). |

## Scope notes

- A successful kernel build does not establish device compatibility, bootloader acceptance, Android userspace support, or hardware stability.
- Historical reports predate later user-reported device observations. Both the chronology and provenance limitation are retained in [`docs/flash-readiness.md`](docs/flash-readiness.md).
- No phone partitions were written as part of the recorded work.
