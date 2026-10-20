# External Inputs and Provenance

No Samsung source archive or official firmware package is included in this repository.

## Samsung open-source source package

The Phase 2 build used the following external archive members from Samsung's open-source package. Hashes identify the examined copies; verify the downloaded files before use.

| Archive member | SHA-256 |
| --- | --- |
| `Kernel.tar.gz` | `0e16a5dce007a91f6215a194c534cb9cf84fcf8fff021609cc47f344cfcc1f27` |
| `Platform.tar.gz` | `5e79eff9d5da3c946936c12b9ac1d26f699802a3cb6f0837ad8a087fb003eb0b` |

The Samsung archive also named `README_Kernel.txt` and `README_Platform.txt`. `README_Kernel.txt` and the kernel archive's top-level `COPYING` were reviewed for the scoped patch license audit; see [`license-review-2026-10-20.md`](license-review-2026-10-20.md). The Platform archive and its README were not reviewed because none of the staged patches target it. No `Platform.tar.gz` source or binary is staged here.

## Official firmware bundle

Reference build: `A022FXXS3BWH1`, CSC `OJM3BWH1`; local bundle directory was named `EGY-A022FXXS3BWH1-20231011122728` under the owner's Downloads folder. The personal absolute path is intentionally omitted. The hashes below came from read-only hashing of the external bundle and were not Samsung signature verification.

| External file | Bytes | SHA-256 |
| --- | ---: | --- |
| `AP_A022FXXS3BWH1_CL24267853_QB69446539_REV00_user_low_ship_MULTI_CERT_meta_RKEY_OS11.tar.md5` | 3,070,320,846 | `548a978332dde949def40398ebb6ce620d6503503b7aaad14896a4fc1a9321c2` |
| `BL_A022FXXS3BWH1_CL24267853_QB69446539_REV00_user_low_ship_MULTI_CERT.tar.md5` | 1,730,748 | `233dd220f9c6d2e1740e8b884565aa47246d6a9b35a394c8a0a5fabf9d885ee4` |
| `CP_A022FXXS3BWH1_CP24789634_CL24267853_QB69446539_REV00_user_low_ship_MULTI_CERT.tar.md5` | 31,908,040 | `1eb6c98560e157f2e2dc2eaeebabc3579a363666aeaf43bebb88d449708ce6ef` |
| `CSC_OMC_OJM_A022FOJM3BWH1_CL24267853_QB69446539_REV00_user_low_ship_MULTI_CERT.tar.md5` | 23,593,158 | `11120f7524fe4384a9216c241b78c77df982cd32650e4306503f20b232b0b2f7` |
| `HOME_CSC_OMC_OJM_A022FOJM3BWH1_CL24267853_QB69446539_REV00_user_low_ship_MULTI_CERT.tar.md5` | 23,572,683 | `ad91a0a335607c6051db120da1b0fd6eb71e153c6390b1e343e6d5823c062ca6` |

The AP archive contains boot, recovery, DTBO, super, userdata, modem/TEE firmware, and VBMeta-related members. BL contains preloader and LK-related members. The CSC contains the PIT. These files are excluded because they are copyrighted firmware and are not required to review the staged text and patch set. Do not use these hash records as proof of firmware authenticity.

## Examined derived inputs

The detailed Phase 2 reproducibility record also identifies SHA-256 values for an extracted official `boot.img`, an `lk-verified.img` copy, and `A02_EUR_OPEN.pit`. These are listed in [`reproducibility.md`](reproducibility.md) as references only; the files are not included.
