import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_kernel.py"


class KernelBuildHelperSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)
        self.source = self.root / "kernel"
        self.source.mkdir()
        (self.source / "Makefile").write_text("", encoding="utf-8")
        self.toolchain = self.root / "toolchain"
        self.toolchain.mkdir()
        self.env = os.environ.copy()
        self.env.update({
            "PYTHONDONTWRITEBYTECODE": "1",
            "KERNEL_SRC": str(self.source),
            "TOOLCHAIN_ROOT": str(self.toolchain),
            "KERNEL_CONFIG": str(ROOT / "config" / "a02-arm64.config"),
        })

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, output):
        env = self.env.copy()
        env["KERNEL_OUT"] = str(output)
        return subprocess.run([sys.executable, "-B", str(SCRIPT)], env=env,
                              capture_output=True, text=True, check=False)

    def test_refuses_output_nested_in_source(self):
        output = self.source / "out"
        result = self.invoke(output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_refuses_nonempty_output_without_overwriting(self):
        output = self.root / "existing-output"
        output.mkdir()
        sentinel = output / "previous-result.txt"
        sentinel.write_text("preserve\n", encoding="utf-8")
        result = self.invoke(output)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve\n")
        self.assertFalse((output / ".config").exists())


if __name__ == "__main__":
    unittest.main()
