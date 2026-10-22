# Reproducing the offline kernel and probe work

## Inputs and provenance

The Samsung archives are external inputs and are not bundled here. The copies used for this investigation had these SHA-256 digests:

| Input | SHA-256 |
| --- | --- |
| `Kernel.tar.gz` | `0e16a5dce007a91f6215a194c534cb9cf84fcf8fff021609cc47f344cfcc1f27` |
| `Platform.tar.gz` | `5e79eff9d5da3c946936c12b9ac1d26f699802a3cb6f0837ad8a087fb003eb0b` |
| Official `boot.img` extracted from `A022FXXS3BWH1` | `a8f18ed7a671f3c7c4aebdf5a1f6c80843616b1aaad4e9251a38163d839753c3` |
| Official `lk-verified.img` copy | `7783eef0ecf9fede74ee5a803360c2987f71db65724521e2f553a776c558076d` |
| Official `A02_EUR_OPEN.pit` copy | `086261a351c39bc7b8233d66deea22822dcb151cbb83260443e2d4ab2488cf08` |

The original Samsung source tree was kept read-only. Three baseline patches in `../patches/` passed `patch --dry-run -p1` against it. Their original-file SHA-256 values were `4d2107ca75e9df7e69b64e0f4ffcbad5e021e94966983d2bd9e03ea0e29a52fe` for `fs/pstore/ram_core.c`, `38bcea83578295456ceb0676db1e530559a004d0d06780e42b7a9f568408212f` for `mtk_ram_console.c`, and `0a6606427ef69e937e9c3c846a00214a48589f151ac4b6718a99f915e8665b15` for `eccci/fsm/Makefile`.

Apply patches `0001`–`0003` for the independent clean-build baseline. Patches `0004`–`0006` were then applied to the experimental copy and built in a third output; patch `0007` was built in a fourth output. Preserve each output directory before adding the next patch. The [patch index](../patches/README.md), [kernel QA](kernel-qa.md), and [source-tree comparison](evidence/source-tree-diff.txt) distinguish these states. The final GPU-patched output is still a compile-only artifact; the RAM-console and Samsung debug gaps are **not** fixed by this series.

## Kernel build inputs

- Ubuntu WSL2 x86-64, Android Clang `r383902`, AArch64 Android GCC/binutils `4.9`.
- A **separate, writable clone** of the Samsung source with the ordered patches applied; never patch the original source or firmware.
- Exact baseline configuration: [`config/a02-arm64.config`](../config/a02-arm64.config).
- `ARCH=arm64`, `ANDROID_MAJOR_VERSION=r`, `MTK_PLATFORM=mt6739`, `CLANG_TRIPLE=aarch64-linux-gnu-`, Android GCC `CROSS_COMPILE`, and Clang/LLD `CC`/`LD`.

The independent QA build copied the saved `.config` into a fresh output directory, ran `make O=<new-out> ARCH=arm64 MTK_PLATFORM=mt6739 ... olddefconfig`, then `make O=<new-out> ARCH=arm64 MTK_PLATFORM=mt6739 ... -j4 Image`. Its `olddefconfig` output was byte-identical to the saved `.config`. The full command, tool paths, log, hashes, and completion status are recorded in the kernel QA report. The kernel `Image` target does not build or validate a device-specific DTB.

When comparing two successful builds, do not assume bitwise-identical `Image` or `vmlinux` unless build timestamps and all generated metadata are controlled. Inspect architecture, link/map consistency, configuration, warnings, and the exact build log. Preserve both output directories.

## Device tree and minimal AArch64 boot probe

The [FDT staging scripts](../scripts/device-tree/README.md) compare read-only firmware DTBs and write candidate DTBs only to a separate directory. The [source integration plan](source-device-tree-plan.md) records the Samsung-base method and historical generic-base gap.

The newer USB-ACM PID 1 source and host reader are included under [`probes/minimal-aarch64-usb-acm/`](../probes/minimal-aarch64-usb-acm/). `build.sh` uses the existing Clang `r383902` and the authorized kernel source copy's `usr/gen_init_cpio`; set `KERNEL_WORK_ROOT` to that separate copy, provide an authorized `USB_VID`, assigned `USB_PID`, unique `USB_SERIAL`, and an empty `PROBE_OUT`, then run the helper from the probe directory. It fixes timestamps for the ELF/CPIO/gzip outputs and refuses to overwrite non-empty output. The revised source writes explicit `0x` prefixes for USB VID/PID and BCD ConfigFS values, following the Linux v4.14 base-autodetection parser. These PR-review source files are newer than the retained local image and are not represented by its component hashes. See [component and source-revision hashes](evidence/minimal-initramfs-checksums.txt).

The local header-v2 USB candidate was parsed and validated offline; its full binary is deliberately not distributed. The exact USB-variant image packer source/invocation was not retained in the public package, so a developer can reproduce the kernel, source FDT, and initramfs inputs from authorized sources but cannot claim byte-for-byte recreation of this final image from this repository alone. Header values and byte layout are published in the [minimal image record](minimal-aarch64-boot-image.md). No hardware validation or flash is part of the procedure.

The [earlier boot-layout audit](boot-layout-audit.md) records previous unsigned layout prototypes; their sizes and hashes are separate from the newest USB candidate.
