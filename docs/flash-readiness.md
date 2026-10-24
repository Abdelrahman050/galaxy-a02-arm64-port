# Flash Readiness — Minimal ARM64 Boot Proof

**Decision: BLOCKED / NO-GO.** This report distinguishes recorded static/build evidence from later user-reported device-state observations. The later [Phase 6 offline report](evidence/phase6-minimal-aarch64-offline.md) does not change this decision. This document is not authorization to flash.

## What is known

- The historical local-only USB-ACM layout is 11,816,960 bytes, SHA-256 `1f4f147bdc9641f0836a35bf3de925cf17d4311399c418d74073aa5ce7d78450`; see its [historical record](minimal-aarch64-boot-image.md). The newer Phase 6 unsigned **console-only** layout is 11,814,912 bytes, SHA-256 `a523d16f1810b07c39144bc4aaf112d2acb7667236378faae8904afe3f879952`. It passed offline format checks but has no proven external marker path or LK-to-FDT initrd delivery. Neither executable image is included here.
- LK disassembly contains a compiled K64 SMC/gzip branch. Selection of this path, exact runtime addresses, secure-monitor acceptance, and transfer into the ARM64 kernel remain unverified.
- The retained candidate's AArch64 PID 1 uses VID/PID `1d6b:0104`, identified by USB-ID records as Linux Foundation's Multifunction Composite Gadget, and is not a project-assigned identity. It also writes unprefixed hexadecimal-looking values to ConfigFS attributes parsed by upstream Linux v4.14 with base autodetection: the `1d6b` VID text is expected to be rejected, while leading-zero `0104`/`0200`/`0100` are octal. A later Phase 6 read-only check confirmed base-autodetect parsing in the local Samsung 4.14.186 source; actual gadget execution on the phone was never tested. Revised PR-review source emits `0x`-prefixed numeric attributes, requires an explicitly authorized VID/PID and unique serial, and the Windows listener waits for that exact PnP identity; this source is not in the retained image and has not been rebuilt. Do not use that historical USB candidate for an observation test. The newer Phase 6 marker is `A02-PHASE6-PROBE kernel=f68ec016d5fcb6d1 pid=1 uname.machine=aarch64`, but console/kmsg writes have no verified external capture route. The phone UDC, Windows COM enumeration, and marker path have not been tested. No trustworthy SM-A022F UART pinout is available. Silence or no matching COM device would be inconclusive.
- RAM-console compatibility is unresolved; the compatibility candidate has only object-build and offline layout evidence. `SEC_DEBUG` is disabled in the saved kernel configuration.
- The matching official firmware is external. An isolated one-member candidate TAR and stock-boot rollback TAR were checked by listing and member hashes but were not submitted to Odin. Odin's acceptance/mapping and recovery after a failed candidate have not been tested. Full-firmware recovery may affect user data.

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

1. No current independent user-data backup is documented; full-firmware recovery can erase data.
2. Odin one-member boot-only candidate and stock rollback package mapping is unverified, and no tested recovery route exists for this exact model/build.
3. No phone UDC/COM enumeration or `/init` marker observation has been performed. This is a planned positive-only proof channel, not a precondition to prove LK accepts the candidate.
4. The historical USB candidate has a third-party USB identity and source-level ConfigFS numeric-format error. The latest Phase 6 candidate avoids USB descriptors but still lacks a proven externally observable console/pstore route. Any future probe change needs a new artifact identity and complete offline review; no VID/PID may be used without authorization.
5. The unsigned candidate's AVB/Samsung-signature acceptance, K64 runtime branch, and actual decompression/output memory behavior are unknown; those are intended hardware-test questions, not established passes.
6. RAM-console ABI and `SEC_DEBUG` remain separate kernel QA issues. They are not used by the probe's observation path, but remain open for kernel stability and later Android work.

The shortest next path is a verified data backup, trusted confirmation of a tested recovery path for the single `boot` partition (or explicit acceptance of full-firmware/data-loss risk), and owner review/approval of the exact write, reboot, observation, and recovery plan. A historical Odin detection report does not replace a fresh check. The [Odin recovery note](odin-recovery-readiness.md) records these limits. Repository scripts do not issue device commands.
