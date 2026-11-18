"""Package boundary and privacy regression tests using temporary synthetic trees."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release", ROOT / "scripts/release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (*release.RUNTIME, ".agents/plugins/marketplace.json"):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        # Runtime README links to contributor source docs; mirror source docs for validation.
        for source in ROOT.glob("*.md"):
            shutil.copyfile(source, self.root / source.name)
        shutil.copytree(ROOT / "docs", self.root / "docs", dirs_exist_ok=True)

    def test_archive_is_deterministic_and_excludes_private_files(self):
        (self.root / "evidence").mkdir()
        (self.root / "evidence/private.json").write_text('{"synthetic": true}')
        output = release.build(self.root)
        first = output.read_bytes()
        release.build(self.root)
        self.assertEqual(first, output.read_bytes())
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.namelist(), sorted(release.RUNTIME))
            self.assertNotIn(".codex-plugin/plugin.json", archive.namelist())
        stage = self.root / "dist/local-plugin"
        legacy = json.loads((stage / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(legacy["skills"], "./skills/")
        self.assertEqual(legacy["version"], json.loads((self.root / "plugin.json").read_text())["version"])

    def test_symlink_runtime_rejected(self):
        target = self.root / "PRIVACY.md"
        target.unlink()
        target.symlink_to(ROOT / "PRIVACY.md")
        with self.assertRaises(release.ReleaseError):
            release.validate(self.root)

    def test_unexpected_stage_content_preserved(self):
        release.build(self.root)
        private = self.root / "dist/local-plugin/private.txt"
        private.write_text("synthetic local content")
        with self.assertRaises(release.ReleaseError):
            release.build(self.root)
        self.assertEqual(private.read_text(), "synthetic local content")

    def test_symlink_output_rejected(self):
        (self.root / "dist").symlink_to(ROOT)
        with self.assertRaises(release.ReleaseError):
            release.build(self.root)

    def test_private_patterns_and_escaping_links_rejected(self):
        # Compose synthetic patterns so the test file contains no actual private credential/path.
        with self.assertRaises(release.ReleaseError):
            release.privacy_check("/" + "Users" + "/example/private", "synthetic")
        with self.assertRaises(release.ReleaseError):
            release.privacy_check("ghp_" + "x" * 36, "synthetic")
        (self.root / "README.md").write_text("[escape](../outside.md)")
        with self.assertRaises(release.ReleaseError):
            release.validate(self.root)

    def test_clean_release_requires_git_provenance(self):
        with self.assertRaises(release.ReleaseError):
            release.build(self.root, require_clean=True)


if __name__ == "__main__":
    unittest.main()
