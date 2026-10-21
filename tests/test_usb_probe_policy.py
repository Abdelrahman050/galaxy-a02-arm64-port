"""Static safeguards for the experimental USB boot probe sources."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "probes" / "minimal-aarch64-usb-acm"


class UsbProbePolicyTests(unittest.TestCase):
    def test_init_has_no_default_vendor_identity(self):
        source = (PROBE / "init.c").read_text(encoding="utf-8")
        self.assertIn('#include "probe_identity.h"', source)
        self.assertIn("#error \"build.sh must generate a reviewed USB VID\"", source)
        self.assertIn("A02_USB_VID", source)
        self.assertIn("A02_USB_PID", source)
        self.assertIn("A02_USB_SERIAL", source)
        self.assertNotIn('"1d6b"', source)
        self.assertNotIn('"0104"', source)
        self.assertIn("text[0] = '0';", source)
        self.assertIn("text[1] = 'x';", source)
        self.assertIn('"0x0200"', source)
        self.assertIn('"0x0100"', source)

    def test_build_requires_identity_and_refuses_overwrite(self):
        source = (PROBE / "build.sh").read_text(encoding="utf-8")
        for name in ("USB_VID", "USB_PID", "USB_SERIAL"):
            self.assertIn(f'"${{{name}:?', source)
        self.assertIn("USB_VID must be four hex digits", source)
        self.assertIn("USB_PID must be four hex digits", source)
        self.assertIn("USB_SERIAL must be 1-32", source)
        self.assertIn("Refusing to overwrite non-empty output directory", source)
        self.assertIn("probe_identity.h", source)
        self.assertIn('-I "$out"', source)

    def test_capture_waits_and_filters_before_open(self):
        source = (PROBE / "capture_usb_acm.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-PnpDevice -PresentOnly -Class Ports", source)
        self.assertIn("$_.InstanceId -match $instancePattern", source)
        self.assertIn("$serialPattern = [regex]::Escape($DeviceSerial)", source)
        self.assertIn("if ($target.State -eq 'READY')", source)
        self.assertGreaterEqual(source.count("Get-TargetComPort"), 3)
        self.assertIn("PnP identity changed after opening the port", source)
        self.assertIn("[System.IO.Ports.SerialPort]::new(\n                $portName", source)
        self.assertIn("[System.IO.FileMode]::CreateNew", source)
        self.assertIn("No COM port was opened", source)
        self.assertNotIn("$serial.Write(", source)
        self.assertNotIn("[System.IO.Ports.SerialPort]::GetPortNames", source)


if __name__ == "__main__":
    unittest.main()
