# Security Policy

## Project scope

This repository contains research notes, source patches, configuration, and local audit/build helpers. It is not a ROM, recovery package, boot image, or flashing tool. No script in this repository should communicate with or write to a connected device.

## Reporting

For a security issue in a script or patch, use GitHub's private vulnerability reporting for this repository if it is enabled. Otherwise, contact the maintainer privately through the [GitHub profile](https://github.com/Abdelrahman050). Do not include firmware images, proprietary blobs, personal data, secrets, or device identifiers in a public issue.

## Safe use

- Review scripts before running them and use a disposable working copy of the authorized source tree.
- Keep stock source archives and firmware read-only; write build products only to a separate output directory.
- Do not treat a successful build, unlocked state, Orange verified-boot state, partition-size calculation, or Download Mode recognition as permission or evidence to flash a candidate.
- Keep private signing keys, tokens, backups, and firmware images out of version control.
- Any future hardware test requires a separate, explicit authorization after image, recovery, data-loss, and logging risks are reviewed.

The project maintains **FLASH READINESS: NO-GO** until the missing evidence is independently established.
