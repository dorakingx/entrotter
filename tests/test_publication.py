"""Check static-publication boundaries and the retired legacy bootstrap option."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("static_publish", ROOT / "scripts/publish.py")
assert SPEC is not None and SPEC.loader is not None
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


class PublicationTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        site = root / "website"
        site.mkdir()
        files = sorted(publisher.PUBLIC_ROOT_FILES) + ["reports/example.json"]
        for name in files:
            path = site / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"public bytes\n")
        (site / "public-files.json").write_text(json.dumps(files))
        (site / ".env").write_text("PRIVATE_SENTINEL\n")
        return site

    def test_staging_preserves_bytes_and_excludes_unlisted_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = self.fixture(root)
            output = root / "output"
            with patch.object(publisher, "SITE", site):
                names = publisher.stage(output)
            actual = sorted(
                p.relative_to(output).as_posix()
                for p in output.rglob("*") if p.is_file()
            )
            self.assertEqual(actual, sorted(names))
            for name in names:
                self.assertEqual((output / name).read_bytes(), (site / name).read_bytes())
            self.assertFalse((output / ".env").exists())
            self.assertFalse((output / "public-files.json").exists())

    def test_escape_and_hidden_paths_fail_before_output_creation(self):
        for name in ["../.env", "/etc/passwd", "reports/.env", "assets//icon.png"]:
            with self.subTest(path=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                site = self.fixture(root)
                manifest = site / "public-files.json"
                manifest.write_text(json.dumps(json.loads(manifest.read_text()) + [name]))
                with patch.object(publisher, "SITE", site), self.assertRaises(ValueError):
                    publisher.stage(root / "output")
                self.assertFalse((root / "output").exists())

    def test_symlink_parent_cannot_publish_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = self.fixture(root)
            private = root / "private"
            private.mkdir()
            (private / "secret.json").write_text("PRIVATE_SENTINEL")
            (site / "assets").symlink_to(private, target_is_directory=True)
            manifest = site / "public-files.json"
            manifest.write_text(json.dumps(json.loads(manifest.read_text()) + ["assets/secret.json"]))
            with patch.object(publisher, "SITE", site), self.assertRaises(ValueError):
                publisher.stage(root / "output")
            self.assertFalse((root / "output").exists())

    def test_legacy_apply_option_is_rejected_without_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PATH"] = directory
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/publish.py"), "--apply"],
                cwd=directory, env=environment, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("bootstrap is retired", result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
