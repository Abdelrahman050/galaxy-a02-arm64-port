import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import repo_audit


class RepositoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_safe_text_is_allowed(self):
        self.put("docs/report.md", "offline research only\n")
        self.assertEqual(repo_audit.content_violations(self.root), [])

    def test_firmware_image_suffix_is_rejected(self):
        self.put("firmware/boot.img", "placeholder")
        self.assertTrue(any("forbidden file type" in e for e in
                            repo_audit.content_violations(self.root)))

    def test_common_secret_and_local_path_patterns_are_rejected(self):
        self.put("notes.txt", "token ghp_" + "A" * 30
                 + "\nC:\\Users\\someone\\Downloads\\x"
                 + "\n/local/" + "user/work/project/file.txt\n")
        violations = repo_audit.content_violations(self.root)
        self.assertTrue(any("secret pattern" in e for e in violations))
        self.assertTrue(sum("local user path" in e for e in violations) >= 2)

    def test_checksum_mismatch_is_detected(self):
        payload = self.put("docs/data.md", "before\n")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        self.put("SHA256SUMS", f"{digest}  docs/data.md\n")
        payload.write_text("after\n", encoding="utf-8")
        self.assertIn("SHA-256 mismatch: docs/data.md",
                      repo_audit.checksum_violations(self.root))

    def test_manifest_requires_every_file(self):
        self.put("docs/data.md", "sample\n")
        self.put("SHA256SUMS", "")
        self.assertIn("file missing from SHA256SUMS: docs/data.md",
                      repo_audit.checksum_violations(self.root))

    def test_local_pre_publish_review_is_excluded(self):
        review = self.put("PRE-PUBLISH-REVIEW.md", "local review only\n")
        self.put("SHA256SUMS", "")
        self.assertNotIn(review, repo_audit.repo_files(self.root))
        self.assertEqual(repo_audit.content_violations(self.root), [])
        self.assertEqual(repo_audit.checksum_violations(self.root), [])

    def test_local_firmware_derived_patch_is_excluded(self):
        patch = self.put(
            "patches/device-tree/0001-a02-arm64-pmu-compat.patch",
            "local-only review fixture\n")
        self.put("SHA256SUMS", "")
        self.assertNotIn(patch, repo_audit.repo_files(self.root))
        self.assertEqual(repo_audit.content_violations(self.root), [])
        self.assertEqual(repo_audit.checksum_violations(self.root), [])

    def test_tracked_local_firmware_derived_patch_is_rejected(self):
        patch = self.put(
            "patches/device-tree/0001-a02-arm64-pmu-compat.patch",
            "local-only review fixture\n")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", str(patch)], check=True)

        self.assertIn(patch, repo_audit.repo_files(self.root))
        violations = repo_audit.content_violations(self.root)
        self.assertTrue(any("local-only path is tracked" in e for e in violations))

    def test_tracked_local_review_is_rejected_even_when_safe_text(self):
        review = self.put("PRE-PUBLISH-REVIEW.md", "local review only\n")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", str(review)], check=True)

        self.assertIn(review, repo_audit.repo_files(self.root))
        violations = repo_audit.content_violations(self.root)
        self.assertTrue(any("local-only path is tracked" in e for e in violations))

    def test_ignored_firmware_binary_is_rejected_if_force_tracked(self):
        self.put(".gitignore", "*.img\n")
        image = self.put("firmware/boot.img", "placeholder")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "-f", str(image)], check=True)

        self.assertIn(image, repo_audit.repo_files(self.root))
        violations = repo_audit.content_violations(self.root)
        self.assertTrue(any("forbidden file type" in e for e in violations))


if __name__ == "__main__":
    unittest.main()
