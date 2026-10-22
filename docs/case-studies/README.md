# Engineering Case Studies

This index records engineering incidents supported by retained source, build, comparison, test, or CI evidence. It separates build and offline results from device runtime. Six cases were selected based on evidence quality, technical importance, and reusable lessons.

## Selected studies

| ID | Case | Current disposition | Evidence strength |
| --- | --- | --- | --- |
| CS-01 | [AArch64 kernel bring-up on an ARM32 Samsung source tree](01-aarch64-kernel-bring-up.md) | Build path verified; architecture debt remains | High for compile/link; medium for some historical root-cause details |
| CS-02 | [PowerVR DVFS pointer and power-state corrections](02-powervr-dvfs-corrections.md) | Compile/link fixes verified; GPU runtime unverified | High for source and build evidence |
| CS-03 | [Reconstructing the SM-A022F Device Tree from maintainable sources](03-sm-a022f-device-tree-reconstruction.md) | Static source reproduction verified | High for source-built FDT/DTBO comparisons |
| CS-04 | [Android boot header v2 and Minimal AArch64 layout experiments](04-boot-header-v2-layout.md) | Current candidate validated offline only | High for local artifact/hash and parser evidence |
| CS-05 | [Minimal init USB ConfigFS encoding and identity](05-usb-configfs-probe.md) | Source fix verified to compile; hardware path unverified | High for source/compile; medium for Samsung parser inference |
| CS-06 | [Making the repository audit Git-aware](06-git-aware-repository-audit.md) | Verified by synthetic tests and read-only CI | High within the tested audit scope |

## Incident inventory

The inventory includes important open questions as well as the selected studies. Evidence quality describes the retained evidence for the stated scope, not confidence in runtime behavior.

| ID | Incident or engineering question | Evidence / date basis | Current status | Evidence quality / lesson |
| --- | --- | --- | --- | --- |
| I-01 | ARM64 build conversion: toolchain, MTK platform selection, exported pstore/RAM-console symbols, and watchdog/SPM configuration | Kernel QA and retained build logs dated 2026-10-18; patches 0001–0003 | RESOLVED — BUILD/COMPILE ONLY | High for successful build and named corrections. A build configuration change is not runtime validation. See CS-01. |
| I-02 | Earlier mksysmap Bus error and zero-filled temporary link outputs | Build note; no complete original failure log retained | PARTIALLY RESOLVED; original cause INSUFFICIENT EVIDENCE | Low for root cause. A later clean build succeeded, but this does not establish why the old output was corrupted. |
| I-03 | Independent clean rebuild produced the same config and System.map but different Image and vmlinux hashes | Clean-rebuild log and SHA manifest dated 2026-10-18 | OPEN / PARTIALLY RESOLVED | High for the observed difference, low for attribution. Build success is repeatable; bit-for-bit reproducibility is not established. |
| I-04 | PowerVR DVFS passed device indices where APIs require device-node pointers; later state-query paths also needed guards | Patches 0004–0007, kernel QA, isolated build logs dated 2026-10-18/19 | RESOLVED — BUILD/COMPILE ONLY | High for source correction and link results; runtime remains open. See CS-02. |
| I-05 | A generic MT6739 ARM64 tree did not preserve Samsung K39/A02 hardware and reserved-memory details | Source-gap audits and DT build reports dated 2026-10-18 to 2026-10-20 | RESOLVED — OFFLINE VALIDATION ONLY | High for structural comparison; no LK selection or device boot was tested. See CS-03. |
| I-06 | Samsung in-tree DTC and Makefile integration did not provide a verified A02 ARM64 DT target | Retained DTC logs and public source-build QA | OPEN / UNVERIFIED | Medium. External DTC 1.7.2 source builds passed; that does not register or validate the in-tree target. |
| I-07 | Firmware-derived PMU patch provenance was unsuitable for the public subset; the adaptation was replaced with a source-based procedure | Public license review, source manifest, and replacement-equivalence report dated 2026-10-20 | RESOLVED — OFFLINE VALIDATION ONLY | High for the published source-based reproduction; no firmware-derived patch is included in the public branch. |
| I-08 | Stock header kernel address was not congruent with the AArch64 Image offset; raw Image exceeded the boot partition | Header/layout audits and current candidate audit | RESOLVED — OFFLINE VALIDATION ONLY | High for arithmetic and parsed layout; decompression placement and LK acceptance remain unknown. See CS-04. |
| I-09 | The candidate has no Samsung signer trailer or AVB footer; acceptance by the device boot chain is unknown | Stock/candidate layout and AVB audit JSON; no runtime test | OPEN / UNVERIFIED | High for offline structural absence, no evidence of LK/TEE decision. |
| I-10 | Retained /init used an unprefixed ConfigFS VID and leading-zero hexadecimal-like descriptor values | Old local init source, retained image audit, and upstream v4.14 parser review; corrected source commit f6adee4 | PARTIALLY RESOLVED | High for old source values and new source compile; exact Samsung 4.14.186 parser behavior and gadget operation remain unverified. See CS-05. |
| I-11 | USB VID/PID attribution and test-device identity were not project-authorized | Candidate audit; revised probe build policy in commit f6adee4 | RESOLVED — SOURCE POLICY ONLY | High for the source policy; no VID/PID has been authorized or tested on hardware. See CS-05. |
| I-12 | USB UDC binding, Windows PnP/COM appearance, and marker receipt | Source and offline ELF/CPIO evidence only | OPEN / UNVERIFIED | Medium. The revised reader is identity-matched, but no live UDC or host enumeration was tested. |
| I-13 | ARM32 and ARM64 persistent RAM-console record layouts differ | DWARF dumps and offset comparison; candidate patch object/model QA dated 2026-10-18 | PARTIALLY RESOLVED | High for layout mismatch and object/model checks; no full Image, real retained record, or runtime reader test. |
| I-14 | SEC_DEBUG selects ARM32 register structures and assembly under a SoC-only conditional | ARM64 compiler logs, config, and candidate guard patches | OPEN / UNVERIFIED | High for compile-time incompatibility; feature remains disabled and candidate guards were not built with SEC_DEBUG enabled. |
| I-15 | LK contains a K64-labelled branch, but selection, secure-world acceptance, addresses, and handoff are unknown | Static strings/xrefs/disassembly dated 2026-10-19/20 | OPEN / UNVERIFIED | Medium for branch presence, none for runtime handoff. |
| I-16 | Recovery via a one-partition Odin boot write, data preservation, and current independent user-data backup | Preflight/recovery analysis; no rollback test or current backup evidence | OPEN / BLOCKED | Medium for identified risk, insufficient for safe recovery. FLASH READINESS remains BLOCKED / NO-GO. |
| I-17 | Stock vendor and graphics components are 32-bit; no complete ARM64 Android system or compatible graphics stack exists in evidence | Android userspace and graphics audits | NOT ACHIEVED / OPEN | High for inspected stock artifacts; no Android ARM64 build or app execution exists. |
| I-18 | Repository audit initially excluded local-only paths without distinguishing tracked files | Baseline audit implementation/tests at b086465; fix and Git-index fixtures in 7c62f87; main CI run 8 | RESOLVED — VERIFIED IN DEFINED SCOPE | High for tested Git-index cases and CI. The audit is not a general security scanner. See CS-06. |

## Evidence policy and gaps

- A case status applies only to the validation scope named in that case. “Resolved” never means that the phone booted unless a hardware result is explicitly retained.
- Full kernel logs and local firmware-derived binaries remain in the local engineering evidence set. They are not copied here because they contain local build paths, large build output, or non-redistributable inputs. Their filenames, findings, and limits are identified where relevant; published reports and patches are linked where available.
- No complete historical chat transcript was found among the project artifacts reviewed. Investigation chronology is therefore limited to timestamped reports, retained logs, Git commits, source diffs, and filesystem metadata explicitly identified as such.
- No retroactive GitHub Issues were created. The open engineering gates remain tracked in [STATUS](../../STATUS.md), [ROADMAP](../../ROADMAP.md), and [flash readiness](../flash-readiness.md).
