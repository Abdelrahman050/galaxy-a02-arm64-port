import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "device-tree"
sys.path.insert(0, str(SCRIPT_DIR))
import prepare_stock_port


VALID_BASE = b'''/* SPDX-License-Identifier: GPL-2.0-only */
/dts-v1/;
/ {
    model = "mt6739";
    compatible = "mediatek,mt6739";
    chosen { bootargs = "console=tty0 maxcpus=4"; };
    reserved-memory { test-area@40000000 { reg = <0x40000000 0x1000>; }; };
    pmu {
        compatible = "arm,cortex-a7-pmu";
        interrupt-parent = <&gic>;
        interrupts = <1 7 8>;
    };
};
'''


class StockPortPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)
        self.source = self.root / "kernel"
        self.target = self.root / "isolated-output"
        arm = self.source / "arch/arm/boot/dts"
        for relative in prepare_stock_port.ARM_FILES:
            path = arm / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(VALID_BASE if relative == "mt6739.dts"
                             else b"/* SPDX-License-Identifier: GPL-2.0-only */\n")
        overlays = self.source / "arch/arm64/boot/dts/mediatek/a02"
        overlays.mkdir(parents=True, exist_ok=True)
        for revision in ("r00", "r01", "r06"):
            (overlays / f"a02_eur_open_w00_{revision}.dts").write_text(
                f"/dts-v1/; /* {revision} test overlay */\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, target=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "prepare_stock_port.py"),
             "--kernel-source", str(self.source), "--target", str(target or self.target)],
            capture_output=True, text=True, check=False)

    def test_valid_synthetic_tree_is_identified(self):
        result = prepare_stock_port.validate_stock_base(VALID_BASE)
        self.assertEqual(result["root_compatible"], ["mediatek,mt6739"])
        self.assertEqual(result["pmu_compatible"], "arm,cortex-a7-pmu")

    def test_rejects_binary_dtb_input(self):
        with self.assertRaisesRegex(ValueError, "UTF-8 DTS text"):
            prepare_stock_port.validate_stock_base(b"\xd0\x0d\xfe\xed" + b"\0" * 40)

    def test_rejects_wrong_soc_identity(self):
        source = VALID_BASE.replace(b"mediatek,mt6739", b"mediatek,mt6738")
        with self.assertRaisesRegex(ValueError, "does not identify"):
            prepare_stock_port.validate_stock_base(source)

    def test_rejects_malformed_tree(self):
        source = VALID_BASE.replace(b"    };\n};\n", b"    };\n", 1)
        with self.assertRaisesRegex(ValueError, "unclosed brace"):
            prepare_stock_port.validate_stock_base(source)

    def test_rejects_wrong_or_ambiguous_pmu(self):
        wrong = VALID_BASE.replace(b"arm,cortex-a7-pmu", b"arm,armv8-pmuv3")
        with self.assertRaisesRegex(ValueError, "PMU compatible must be exactly"):
            prepare_stock_port.validate_stock_base(wrong)
        duplicate = VALID_BASE.replace(
            b"    };\n};\n",
            b"    };\n    pmu { compatible = \"arm,cortex-a7-pmu\"; };\n};\n", 1)
        with self.assertRaisesRegex(ValueError, "exactly one top-level pmu"):
            prepare_stock_port.validate_stock_base(duplicate)

    def test_copy_changes_only_pmu_and_preserves_input(self):
        base = self.source / "arch/arm/boot/dts/mt6739.dts"
        original = base.read_bytes()
        overlay = self.source / "arch/arm64/boot/dts/mediatek/a02/a02_eur_open_w00_r00.dts"
        overlay_original = overlay.read_bytes()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        output_base = self.target / "src/arch/arm64/boot/dts/mediatek/mt6739-sm-a022f-stock.dts"
        expected = original.replace(b'compatible = "arm,cortex-a7-pmu";',
                                    b'compatible = "arm,armv8-pmuv3";', 1)
        self.assertEqual(output_base.read_bytes(), expected)
        self.assertEqual(base.read_bytes(), original)
        output_overlay = self.target / "src/arch/arm64/boot/dts/mediatek/a02/a02_eur_open_w00_r00.dts"
        self.assertEqual(output_overlay.read_bytes(), overlay_original)
        manifest = json.loads((self.target / "sources-manifest.json").read_text(encoding="utf-8"))
        changed = [entry["staged"] for entry in manifest["files"] if entry["changed"]]
        self.assertEqual(changed, ["src/arch/arm64/boot/dts/mediatek/mt6739-sm-a022f-stock.dts"])
        self.assertEqual(manifest["pmu_change"], {
            "node": "/pmu", "property": "compatible",
            "from": "arm,cortex-a7-pmu", "to": "arm,armv8-pmuv3"})

    def test_rejects_invalid_source_before_creating_output(self):
        base = self.source / "arch/arm/boot/dts/mt6739.dts"
        base.write_bytes(VALID_BASE.replace(b"mediatek,mt6739", b"mediatek,mt6738"))
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.target.exists())

    def test_rejects_missing_revision_overlay_before_creating_output(self):
        (self.source / "arch/arm64/boot/dts/mediatek/a02/a02_eur_open_w00_r06.dts").unlink()
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("overlays are missing", result.stderr)
        self.assertFalse(self.target.exists())

    def test_rejects_output_inside_source_or_existing_target(self):
        nested = self.run_cli(self.source / "out")
        self.assertEqual(nested.returncode, 2)
        self.assertFalse((self.source / "out").exists())
        self.target.mkdir()
        existing = self.run_cli()
        self.assertEqual(existing.returncode, 2)
        self.assertTrue(self.target.is_dir())


if __name__ == "__main__":
    unittest.main()
