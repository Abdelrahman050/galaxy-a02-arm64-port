# Reconstructing the SM-A022F Device Tree from Maintainable Sources

## Technical scope

This case covers the source-based reconstruction and static comparison of the Galaxy A02 SM-A022F Device Tree for A022FXXS3BWH1 revisions r00, r01, and r06. It does not establish bootloader selection or device operation.

## Executive summary

A generic MT6739 ARM64 base was not a safe substitute for the Samsung K39/A02 board tree: it omitted Samsung modem/security reservations, Trusty-related nodes, boot arguments, and other board properties. The Samsung ARM64 A02 overlays also depended on K39 source files not present in the ARM64 directory. The retained source workflow staged the Samsung MT6739 base, shared includes, K39 board files, and A02 overlays into an isolated target, changing only the PMU compatible string for the AArch64 build. Source-built DTBOs and merged FDTs were compared with official-derived inputs. The comparison passed statically; no target was booted.

## Device, source, and toolchain context

The work used Samsung's open-source kernel package for MT6739, K39 shared DTS/DTSI dependencies, the A02 board overlays, and official-derived FDT/DTBO comparison inputs held locally. The public tree includes bounded preparation/build tools, patches, manifests, and sanitized comparison reports, not firmware images or a complete source archive. The reproducible standalone build used system DTC 1.7.2 and overlay support.

## Original problem and symptoms

The first ARM64 A02 board source referenced K39 labels and include files absent from the ARM64 source directory. A standalone overlay compilation reported unresolved references such as chosen, odm, i2c1, and pio when it lacked the base tree. A generic MT6739 source tree was considered, but after resolving a missing soc_codec label it still had 719 nodes versus 738 in the official A02 merged tree and lacked Samsung-specific modem/security reserved-memory, TEE/Trusty, and bootargs details.

## Investigation and root cause

The missing information was not one PMU property. The device tree is a layered SoC, platform, and board description. The Samsung A02 overlay must be interpreted with its K39 dependencies and Samsung MT6739 base; compiling it alone or attaching it to a generic base changes the hardware and memory-reservation description. In addition, the initial firmware-derived PMU patch raised redistribution uncertainty. The public reproduction path was therefore switched to source inputs with traceable Samsung open-source provenance.

## Failed attempts

- The standalone A02 overlay did not resolve labels without its required base tree and include set.
- The generic MT6739 ARM64 base became syntactically buildable after resolving a label, but remained semantically incomplete for A02; a successful DTC invocation did not make it a device-tree match.
- Samsung's in-tree DTC 1.4.4 failed the recorded standalone overlay build; system DTC 1.7.2 produced overlays matching the official-derived DTBO inputs. This does not prove that the kernel's in-tree Makefile target is ready.

## Applied engineering work

An isolated helper staged 21 selected Samsung DTS/DTSI inputs into a new target from the ARM32 Samsung base, shared platform includes, K39 board/GPIO files, and existing Samsung A02 overlays. The base adaptation changes only /pmu:compatible from arm,cortex-a7-pmu to arm,armv8-pmuv3. Boot arguments, TEE/Trusty nodes, SEC and CCCI reservations, and the other board content were retained. A source-based patch and manifest record the adaptation; the firmware-derived patch remains excluded from the public subset.

## Validation and verified results

- Source-built r00, r01, and r06 DTBO files were byte-identical to the corresponding official-derived overlays.
- The source-built merged FDTs matched their corresponding official-derived trees in nodes, properties, and reservation data except for the intended /pmu:compatible change.
- r00 had 738 nodes; r01 and r06 had 737. No missing or extra node/property differences were recorded in the source-based comparisons.
- A separate recheck rebuilt the staged base source byte-for-byte and compared saved candidate trees structurally. It did not freshly compile all DTBs in the Windows session; the original Linux DTC logs remain local.

These are offline source and structure results. They do not prove the kernel build includes these DTBs, that LK selects the expected overlay, or that the secure monitor and drivers accept the tree.

## Remaining limitations

The A02 ARM64 target is not registered as a verified normal kernel DTB/DTBO build target. The external-DTC workflow is reproducible within its recorded inputs, but the in-tree DTC/Makefile integration remains open. Official firmware-derived comparison inputs and full source logs are not redistributed. Runtime DTBO selection and device boot are unverified.

## Lessons learned

- Reuse the exact board-specific base and include chain before editing isolated overlays.
- Compare semantic FDT content, reservations, and bootargs; a successful compile or similar SoC name is not enough.
- Keep PMU adaptation minimal and independently reviewable.
- Separate source provenance and redistribution from binary comparison. A technically useful firmware-derived patch can be replaced by a reproducible source-based transformation without publishing firmware data.

## Evidence references

See [source-build QA](../device-tree-source-build-qa.md), [Device Tree and LK analysis](../device-tree-bootloader.md), [source evidence matrix](../evidence-matrix.md), [source-based PMU patch](../../patches/device-tree/0001-sm-a022f-stock-base-armv8-pmu.patch), and [DTS source-build evidence](../evidence/dt-source-build-audit.json) with its [source manifest](../evidence/dt-sources-manifest.json).

Retained local-only diagnostics include dt-reproduce-new/audit.json, revision-specific DTC/rebuild logs, source manifests, and the earlier source-gap audit. They include references to local input staging and are not copied here. The public machine-readable audit is the reviewable summary.

## Current status

**RESOLVED — OFFLINE VALIDATION ONLY** for source-based reproduction and semantic comparison of the saved r00/r01/r06 trees with the intended PMU change. **OPEN / UNVERIFIED** for in-tree target integration, LK selection, and runtime hardware behavior.
