# Source-maintainable SM-A022F AArch64 DTB candidate

**Status:** PASS for a reproducible **static Device Tree source build** matching official Samsung A022FXXS3BWH1 for hardware revisions r00, r01 and r06, with one deliberate ARM64 PMU change. **UNVERIFIED** for bootloader acceptance and runtime operation. No firmware, original Samsung source, build outputs or device partitions were modified.

## Implementation

`prepare_stock_port.py` copies 21 DT source files into a new isolated target. The base is Samsung's `arch/arm/boot/dts/mt6739.dts`, renamed to `arch/arm64/boot/dts/mediatek/mt6739-sm-a022f-stock.dts`. Its sole content edit is `/pmu:compatible`: `arm,cortex-a7-pmu` → `arm,armv8-pmuv3`. It copies the stock base's active supporting includes (`cust_mt6739_msdc.dtsi`, `trusty.dtsi`, `mt6357.dtsi`, `modem-MT6739ap-pdata.dtsi`), K39 board/gpio files, and the existing Samsung ARM64 A02 board overlays. The original `kernel-source/out/include/generated/autoconf.h` supplies the stock conditional DT choices; in particular it enables `CONFIG_SEC_DEBUG`, `CONFIG_SEC_DEBUG_AUTO_COMMENT`, `CONFIG_TEEGRIS_TEE_SUPPORT`, and `CONFIG_MTK_PMIC_CHIP_MT6357`.

`build_stock_port.py` preprocesses and compiles the copied base and each overlay using system DTC 1.7.2 with `-@`, merges with `fdtoverlay`, records logs and compares raw FDT node paths, property bytes and memreserve entries against the extracted official DTBs. The build script hashes every staged source and official input before and after to detect unintended changes. The one-line review patch is `0001-sm-a022f-stock-base-armv8-pmu.patch`; patch application was verified on a temporary stock source copy and produced exactly the staged base file.

## Evidence

| Comparison | Nodes | Missing / extra | FDT memreserve | Property differences |
| --- | ---: | ---: | --- | --- |
| Stock-derived ARM64 base vs official boot DTB | 426 / 426 | 0 / 0 | Equal | `/pmu:compatible` only |
| r00 merged vs official | 738 / 738 | 0 / 0 | Equal | `/pmu:compatible` only |
| r01 merged vs official | 737 / 737 | 0 / 0 | Equal | `/pmu:compatible` only |
| r06 merged vs official | 737 / 737 | 0 / 0 | Equal | `/pmu:compatible` only |

All three source DTBOs are **byte-identical** to official `dtbo-0/1/2.dtb`. The official base and merged comparisons include `/chosen:bootargs`, Samsung SEC and CCCI reserved-memory, `/teegris`, `/trusty`, and all overlay hardware nodes. The packaged [`audit.json`](evidence/dt-source-build-audit.json) contains the complete machine-readable comparisons and [`sources-manifest.json`](evidence/dt-sources-manifest.json) records hashes of all staged source files. The [PMU replacement recheck](evidence/dt-pmu-source-replacement-equivalence.json) records the 2026-10-20 helper run and saved DTB equivalence. Compiler and merge logs remain in the local isolated work directory. The local `reproduction-check/` run independently produced byte-identical base, overlays and merged DTBs to the first staged build; derived firmware DTB binaries are not redistributed in this package.

Built merged DTB SHA-256:

| Revision | SHA-256 |
| --- | --- |
| r00 | `14e8e1911588f8253400d3adaa6e4a62abd001d2cfe509ab6ad24cb25ec8138e` |
| r01 | `b6898e3d24f7fcb7b9d27a0f3148dfce0e2cedbe51d4f781d54fadadcb0fb79c` |
| r06 | `b6898e3d24f7fcb7b9d27a0f3148dfce0e2cedbe51d4f781d54fadadcb0fb79c` |

## Reproduce in a fresh directory

Run inside WSL/Linux with `cpp`, `dtc`, `fdtoverlay` and Python 3 installed. Supply the read-only Samsung source root and official firmware-analysis root:

```sh
python3 prepare_stock_port.py --kernel-source /path/to/kernel-source --target /path/to/new-stage
python3 build_stock_port.py --kernel-source /path/to/kernel-source --firmware-analysis /path/to/firmware-analysis --stage /path/to/new-stage
```

The source root must contain the stock ARM32 `out/include/generated/autoconf.h`; a different config can alter reserved memory or TEE nodes and fail exact comparison. `prepare_stock_port.py` refuses to overwrite an existing stage.

## Interpretation and remaining gates

The copied Samsung base is faithful to the official DTB at the property level, so the earlier generic ARM64 `mt6739.dts` drift is avoided. This says nothing about whether the built AArch64 kernel's drivers accept all those bindings or whether LK loads the kernel at the required ARM64 address and exception level. The boot image layout, gzip path, LK entry address, signed boot chain and runtime reservations require separate evidence or a later consented device test. This DTB has **not** been packaged into a boot image or flashed. No Android ARM64 userspace behavior is implied by this result.

The candidate is built by the independent reproducible script, not yet registered as a target in `arch/arm64/boot/dts/mediatek/Makefile`. Samsung's in-tree DTC 1.4.4 failed the standalone A02 overlay, while system DTC 1.7.2 produced official-identical overlays. Kernel Makefile integration therefore needs either a newer DTC or an explicit external DT build rule; simply adding the target would not establish a repeatable full DTBO build.

## Public PMU reproduction and current recheck

The public reproduction path uses Samsung's source archive rather than the historical firmware-decompiled DTS patch. During the 2026-10-20 recheck, only the helper's 21 required DTS/DTSI inputs were extracted into a disposable test directory. `prepare_stock_port.py` completed successfully; its `mt6739-sm-a022f-stock.dts` output matched the earlier isolated source-stage file byte-for-byte (SHA-256 `be2a5934175f25214408b95330383c9915c3834a1caf8386ecf04619dd61dde4`). The archive hash was unchanged. Synthetic positive/negative tests also verify input identity, PMU uniqueness, malformed/binary rejection, missing overlays, source immutability, and separate-output behavior.

The already-built source-based r00/r01/r06 merged DTBs were compared again with the previous firmware-derived candidate DTBs using `fdt_diff.py`, allowing `/pmu:compatible`; all three returned **PASS**, with zero missing/extra nodes or properties, no other changed properties, and equal reservation maps. This establishes equivalence between those saved outputs only. `dtc` was not available in the current Windows session, so this recheck did not freshly compile DTBs. Static tree equality still does not prove that LK loads the tree, that drivers accept it, or that a phone boots.
