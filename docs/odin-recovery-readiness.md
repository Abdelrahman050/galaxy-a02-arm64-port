# Odin Recovery Readiness — SM-A022F

**Recovery status: UNVERIFIED.** This note records offline preparation and its limits; it is not an instruction or authorization to flash.

## Recorded inputs and offline preparation

- The reference build is `A022FXXS3BWH1`. The official AP/BL/CP/CSC package and its extracted `boot.img.lz4` remain external and are not included here.
- A local read-only extraction of the stock boot member and two one-member TAR containers was recorded in the private preflight report. The candidate TAR contained `boot.img`; the rollback TAR contained `boot.img.lz4`. Container listing and member hashes matched their local inputs.
- The TAR layouts were **not** submitted to Odin. Odin's acceptance and partition mapping for either one-member archive are therefore unknown. The matching official firmware was previously used by the owner, but that does not validate these new TAR files.
- The recorded PIT describes one `boot` partition and no A/B slot. No rollback partition write or boot was performed.

The firmware binaries, extracted boot image, candidate image, TAR files, PIT, and full recovery package are intentionally excluded from this repository. Their hashes in local reports identify evidence only and do not authorize redistribution.

## Recovery risks and open gates

1. A failed boot may still leave Download Mode available, but that outcome is not guaranteed or tested with this candidate.
2. There is no retained confirmation of a current, independent user-data backup. A full firmware restore can overwrite `userdata`; `HOME_CSC` is not a data-preservation guarantee.
3. The stock-boot-only rollback TAR has not been accepted or mapped by Odin on this exact model/build. Do not assume that a file loading into the AP slot means Odin will write only `boot`.
4. Owner-reported Odin detection in Download Mode is historical; the raw capture and timestamp are not retained. It must be confirmed again immediately before any separately authorized test.
5. The experimental image has no Samsung signer trailer or AVB footer. `flash.locked=0`, unlocked device state, and orange verified-boot state do not prove acceptance by Samsung LK/TEE.

## Conditional recovery planning

Before any future hardware test, prepare a fresh, independently verified data backup; confirm exact model, bootloader, and available official firmware on the host; and obtain trusted evidence that the intended single-partition rollback path is accepted for this Odin/device combination. If that cannot be established, the contingency is a reviewed full-firmware recovery with the data-loss risk explicitly accepted. Do not load PIT, enable repartition, or include BL/CP/CSC in a boot-only experiment.

The user must review and explicitly authorize the exact image write, reboot, observation, and recovery sequence after these gates are resolved. No such authorization is contained in this document. See [flash readiness](flash-readiness.md) and the [minimal image record](minimal-aarch64-boot-image.md).
