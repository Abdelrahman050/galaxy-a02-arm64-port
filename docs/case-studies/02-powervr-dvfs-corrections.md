# PowerVR DVFS Pointer and Power-State Corrections

## Technical scope

This study covers the MT6739 PowerVR integration code in the Samsung kernel and the isolated AArch64 compile/link checks for the prepared patch series. It does not claim that the GPU, display, or Android graphics stack works.

## Executive summary

The inherited DVFS path passed a 32-bit device index to PowerVR APIs whose parameter type is a device-node pointer. Four compiled call sites produced Clang integer-to-pointer conversion warnings. The target API dereferences the node, making the mismatch a plausible invalid-pointer fault when the path runs. Patches 0004–0007 replaced the bad inputs and guarded power-state error paths. Separate output directories built and linked successfully, and the four conversion diagnostics disappeared. Runtime DVFS remains untested.

## Device, kernel, and toolchain context

The target is SM-A022F on MT6739 using Samsung kernel 4.14.186. The recorded ARM64 builds used Android Clang r383902 and the associated Android GCC 4.9 cross-tools. The GPU source is under Samsung's MT6739 RGX integration; the public repository contains only the reviewed patches and evidence summaries, not proprietary binaries or a full kernel source copy.

## Original problem and error evidence

The relevant call sites in mtk_mfgsys.c passed an IMG_UINT32 index into helpers declared to accept PPVRSRV_DEVICE_NODE or PVRSRV_DEVICE_NODE pointers. Clang reported four -Wint-conversion diagnostics at the active DVFS paths. The same type error existed in the original Samsung file and the unpatched experiment copy, whose recorded hashes matched.

A later call site ignored an error returned by PVRSRVGetDevicePowerState. The patch review also found a conditional power-index path using the device identifier for PowerLock/PowerUnlock. That conditional path was not enabled by the recorded build configuration.

## Investigation and root cause

The source interface distinguishes an index from a node pointer. Passing the index as a pointer is not a harmless warning: the state-query implementation dereferences the supplied node. The required object was already available through the existing MTKGetRGXDevNode helper. Separately, callers consumed an output state without establishing that the query had succeeded, and clock pre/post operations needed balanced exits on failure.

## Failed attempts

The original unpatched AArch64 builds linked despite the pointer-conversion warnings. That successful link was not evidence of a correct runtime call. No retained hardware trace demonstrates a GPU crash; the fault is a source-level risk inferred from the callee dereference and incorrect argument type.

## Applied fixes

- Patch 0004 uses the existing device-node helper and checks the returned node before the active DVFS calls. It also corrects the corresponding conditional call site and removes the now-unused index helper.
- Patch 0005 checks power-state query results and balances a successful pre-clock call with post-clock cleanup before returning without a frequency change.
- Patch 0006 corrects the node passed to lock/unlock in MTK_CAL_POWER_INDEX. That conditional code needs a dedicated build with the option enabled.
- Patch 0007 handles a separate active GED frequency-commit state-query failure and reports a failed commit while balancing clock callbacks.

## Validation and verified results

The 0004–0006 isolated incremental build exited 0 and linked an AArch64 Image. The four integer-to-pointer diagnostics fell to zero; 47 other warnings remained in the object. A follow-up build including 0007 also exited 0; it reported no undefined-symbol or target section-mismatch diagnostic in that build. The object warning count changed from 47 to 46, not to zero. The saved Image, vmlinux, and System.map hashes are documented in [kernel QA](../kernel-qa.md).

The 0006 optional path was not compiled by the current configuration. No power transition, lock behavior, GPU frequency change, display operation, or thermal behavior was tested on the phone.

## Remaining limitations

This work verifies type correction and compilation/linkage under the selected configuration. It does not establish correct lock lifetime under all runtime paths, successful clock sequencing in hardware, compatible GPU firmware, graphics HAL operation, or Android ARM64 userspace support.

## Lessons learned

- A 32-bit integer accepted through an implicit pointer conversion can survive compilation and linking while remaining unsafe at runtime.
- Fix the API contract with the actual object, rather than suppressing warnings or disabling DVFS.
- Error-return paths in clock/power code must preserve callback pairing and lock state.
- Report warning deltas precisely; no conversion warning does not mean warning-free.

## Evidence references

The public patch sequence is [0004](../../patches/0004-powervr-use-device-node-in-dvfs.patch), [0005](../../patches/0005-powervr-handle-unknown-power-state.patch), [0006](../../patches/0006-powervr-optional-power-index-node-lock.patch), and [0007](../../patches/0007-powervr-guard-ged-power-state.patch). See [kernel QA](../kernel-qa.md) for hashes, warning counts, exact build scope, and open runtime gates.

The retained local build records are gpu-fix-incremental-build.log and gpu-commit-guard-build.log. Their SHA-256 values at this review were c576e01b30f8e194b6fd0d50e2f8509055038fa8c8b9cb07571e201d96afd161 and 463a3e1be908ae89a93623d8c361503a299cdd8790d8701d03dfcb5d9f9c40f2. Full logs were not published because they include local paths and raw build output.

## Current status

**RESOLVED — BUILD/COMPILE ONLY** for the diagnosed pointer conversions and patched active power-state paths under the recorded configurations. **UNVERIFIED** for the conditional 0006 path and all GPU/device runtime behavior.
