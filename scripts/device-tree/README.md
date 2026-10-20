# Device-tree audit helpers

These helpers reproduce limited Phase 2 source/FDT comparisons from separately supplied, authorized inputs. They do not apply changes to the Samsung source tree or official firmware.

## Source-build comparison

Requirements in Linux/WSL: Python 3, `cpp`, `dtc`, `fdtoverlay`, and the exact Samsung kernel source and extracted matching firmware DTB/DTBO files. The kernel source and firmware paths are read-only inputs. Use a new writable staging directory outside both input trees:

```sh
python3 scripts/device-tree/prepare_stock_port.py \
  --kernel-source /readonly/samsung-kernel-copy \
  --target /scratch/a02-dt-stage

python3 scripts/device-tree/build_stock_port.py \
  --kernel-source /readonly/samsung-kernel-copy \
  --firmware-analysis /readonly/extracted-official-dt \
  --stage /scratch/a02-dt-stage
```

`prepare_stock_port.py` refuses an existing target or a target overlapping the source tree. `build_stock_port.py` requires the prepared manifest, refuses a non-empty build output, and refuses staging paths that overlap kernel or firmware inputs. Compiler output and comparison JSON stay below the chosen staging directory.

`prepare_stock_port.py` is the public, source-based PMU route. It requires the stock `mediatek,mt6739` root, exactly one top-level `pmu` node, and the expected `arm,cortex-a7-pmu` property. It rejects binary DTBs, malformed or unexpected DTS input, missing A02 overlays, symlinked inputs, and outputs inside/overlapping the source tree. It creates a new target and records each source/output SHA-256 plus the single intended change. Its small validator checks input identity and the specific PMU node; it is not a general DTS parser or DTC replacement. Use `dtc`/the normal source build and the semantic FDT comparison before integrating the result.

The firmware-derived PMU patch retained in the local engineering copy is deliberately excluded from the public Git index and archive. It is not needed to reproduce the PMU change from Samsung's licensed source tree. Do not copy it into a public release unless redistribution rights are separately established.

The alternative `build_candidates.py` operates on already merged official FDT inputs and changes only the PMU compatible string. Set `A02_FDT_INPUT` to a read-only input directory and `A02_FDT_OUTPUT` to a new, separate output directory. It refuses overlapping inputs/outputs and a non-empty output directory.

These scripts have not been run by public CI. Reproducing the historical Phase 2 comparison requires the exact external inputs and tool versions. Output DTBs are research artifacts and are not verified boot images or flash-ready files.
