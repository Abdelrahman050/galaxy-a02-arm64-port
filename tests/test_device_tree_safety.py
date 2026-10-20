import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "device-tree"


class DeviceTreeOutputSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, path, *args, env=None):
        merged = os.environ.copy()
        merged["PYTHONDONTWRITEBYTECODE"] = "1"
        if env:
            merged.update(env)
        return subprocess.run([sys.executable, "-B", str(path), *map(str, args)],
                              env=merged, capture_output=True, text=True, check=False)

    def test_prepare_refuses_output_nested_in_source(self):
        source = self.root / "kernel"
        source.mkdir()
        (source / "Makefile").write_text("", encoding="utf-8")
        target = source / "generated-stage"
        result = self.run_script(SCRIPT / "prepare_stock_port.py",
                                 "--kernel-source", source, "--target", target)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())

    def test_fdt_candidates_refuse_overlapping_output(self):
        source = self.root / "firmware"
        source.mkdir()
        output = source / "candidate-output"
        result = self.run_script(SCRIPT / "build_candidates.py",
                                 env={"A02_FDT_INPUT": str(source),
                                      "A02_FDT_OUTPUT": str(output)})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_source_build_refuses_stage_overlapping_inputs_before_writing(self):
        stage = self.root / "kernel"
        stage.mkdir()
        (stage / "sources-manifest.json").write_text("{}\n", encoding="utf-8")
        firmware = self.root / "firmware"
        firmware.mkdir()
        result = self.run_script(SCRIPT / "build_stock_port.py",
                                 "--kernel-source", stage,
                                 "--firmware-analysis", firmware,
                                 "--stage", stage)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((stage / "build").exists())


if __name__ == "__main__":
    unittest.main()
