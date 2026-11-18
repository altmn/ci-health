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

    def test_packaged_skill_links_resolve_in_archive_and_staging(self):
        output = release.build(self.root)
        extracted = self.root / "unpacked"
        with zipfile.ZipFile(output) as archive:
            archive.extractall(extracted)
        for package in (extracted, self.root / "dist/local-plugin"):
            for path in (package / release.SKILL).rglob("*.md"):
                with self.subTest(package=package.name, path=path.relative_to(package)):
                    release.local_links(package, path)

    def test_source_reference_missing_from_package_is_rejected(self):
        reference = self.root / release.SKILL / "references/additional.md"
        reference.write_text("# Additional guidance\n")
        entrypoint = self.root / release.SKILL / "SKILL.md"
        entrypoint.write_text(entrypoint.read_text() + "\n[Additional guidance](references/additional.md#details)\n")
        with self.assertRaisesRegex(release.ReleaseError, "unpackaged skill link"):
            release.build(self.root)

    def test_packaged_skill_links_decode_paths_and_preserve_fragment_handling(self):
        entrypoint = self.root / release.SKILL / "SKILL.md"
        for target in ("references/%6deasurement.md#evidence-to-retain", "#local-section"):
            with self.subTest(target=target):
                entrypoint.write_text(f"[Guidance]({target})\n")
                release.local_links(self.root, entrypoint, set(release.RUNTIME))
        for target in ("%2e%2e/%2e%2e/%2e%2e/outside.md#details", "references/missing.md#details"):
            with self.subTest(target=target):
                entrypoint.write_text(f"[Guidance]({target})\n")
                with self.assertRaisesRegex(release.ReleaseError, "broken or escaping local link"):
                    release.local_links(self.root, entrypoint, set(release.RUNTIME))

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
