# Test and Evidence Boundaries

## Recorded project tests

- The AArch64 kernel was built, then rebuilt in an independent clean output. Both builds completed; config and `System.map` matched, but `Image` and `vmlinux` differed by SHA-256. This is a successful rebuild, not bit-identical reproducibility or a boot test.
- Kernel patches 0001–0003 passed a historical dry-run apply check against the exact Samsung source copy. Patches 0004–0007 compiled and linked in isolated build outputs. Patch 0008 passed an AArch64 object-only build and offline layout checks. Patches 0009–0010 were reviewed only.
- PowerVR changes were compiled and linked; no GPU or display test was run.
- Device-tree comparisons covered all nodes, properties, and memory reservations for the selected official merged trees; only the intended PMU compatible property differed. DTBO r00/r01/r06 outputs matched byte-for-byte. No device boot was performed.
- Static LK analysis established that a K64 branch is present. It did not establish runtime branch selection or secure-world acceptance.
- The offline boot layout was unsigned. Size and header checks are arithmetic/static checks only.

## Tests included with this staging tree

`tests/test_repo_audit.py` exercises positive and negative cases for safe text, firmware-image exclusion, secret/local-path patterns, checksum mismatch/coverage, and exclusion of the local-only firmware-derived PMU patch. `tests/test_device_tree_safety.py` verifies that three device-tree helpers reject output paths that overlap read-only source/firmware inputs before writing. `tests/test_prepare_stock_port.py` uses synthetic DTS inputs to verify correct PMU-only editing, source immutability, output isolation, and rejection of binary, malformed, wrong-SoC, ambiguous-PMU, and incomplete inputs. `tests/test_build_helper_safety.py` verifies the kernel helper refuses source/output overlap and a non-empty output directory before running `make`. `scripts/repo_audit.py` checks the final staged tree and SHA-256 manifest. These repository hygiene checks do not validate Linux runtime behavior, device-tree semantics without exact FDT inputs, signature trust, or hardware boot.

The `kernel_qa.py`, `fdt_diff.py`, `flash_readiness_gate.py`, and device-tree scripts are included for future use against separately supplied inputs. Their CLI/help and syntax can be checked locally; this repository does not include copyrighted firmware, kernel source, or generated binaries needed to rerun the full Phase 2 tests.

No GitHub Actions result exists yet. The included workflow is a read-only proposal until it actually runs on GitHub.
