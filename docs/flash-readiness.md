# Flash Readiness — Minimal ARM64 Boot Proof

**Decision: NO-GO.** This report distinguishes recorded static/build evidence from later user-reported device-state observations. It is not authorization to flash.

## What is known

- An unsigned offline boot-layout prototype fit the recorded boot-partition capacity by size. It was not accepted by LK or AVB in a device test.
- LK disassembly contains a compiled K64 SMC/gzip branch. Selection of this path, exact runtime addresses, secure-monitor acceptance, and transfer into the ARM64 kernel remain unverified.
- The proposed minimal `/init` is static AArch64 and can emit a console marker in its intended environment. No physical UART pinout/log session has demonstrated that the phone would expose this output.
- RAM-console compatibility is unresolved; the compatibility candidate has only object-build and offline layout evidence. `SEC_DEBUG` is disabled in the saved kernel configuration.
- The recovery manifest refers to the official firmware bundle, which is excluded from this repository. Recovery after a failed candidate has not been tested. Full-firmware recovery may affect user data.

## Later user-reported observations

After an earlier report that had no operational phone connection, the project owner later reported these checks for the phone at that time:

| Observation | Reported value |
| --- | --- |
| `flash.locked` | `0` |
| `vbmeta.device_state` | `unlocked` |
| `verifiedbootstate` | `orange` |
| Bootloader build | `A022FXXS3BWH1` |
| Odin | Recognized in Download Mode |

The raw console output or screenshot and capture timestamp were not retained in the project evidence. Treat these as user-reported observations, not independently verified artifacts. They show reported lock/download-mode state only. They do not establish candidate signature acceptance, AVB policy for the exact image, safe K64 handoff, early-log availability, or recovery after a failed boot.

## Blocking evidence

1. No candidate-specific signature/AVB acceptance proof from the target LK/TEE.
2. No observed runtime K64 handoff or verified load/decompression addresses.
3. No tested early-log path reaching `/init`.
4. No tested recovery procedure for this exact candidate and bootloader, with data-loss risk reviewed.
5. RAM-console and SEC_DEBUG architecture gaps remain open.

All future hardware testing remains a separate stage requiring a fresh risk review and the owner's explicit authorization. Repository scripts do not issue device commands.
