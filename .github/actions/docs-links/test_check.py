"""Behavior checks using actual Lychee and an owned local HTTP server, no mocks."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import threading
import unittest

from check import scan

BINARY = Path(sys.argv.pop(1)).resolve()


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class LinkChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / "target.md").write_text("# Existing heading\n")

    def check(self, filename, content, passed, **kwargs):
        (self.root / filename).write_text(content)
        code, report = scan(BINARY, self.root, [filename], **kwargs)
        self.assertGreater(report["total"], 0)
        self.assertEqual(code == 0, passed, report)
        return report

    def test_markdown_local_file_and_fragment(self):
        self.check("README.md", "[valid](target.md#existing-heading)", True)
        self.check("README.md", "[missing](missing.md)", False)
        self.check("README.md", "[missing](target.md#missing)", False)

    def test_hidden_template_is_checked(self):
        (self.root / ".github").mkdir()
        self.check(".github/PULL_REQUEST_TEMPLATE.md", "[missing](../missing.md)", False)

    def test_html_root_relative_query_and_fragment(self):
        (self.root / "index.html").write_text('<h1 id="main">Main</h1>')
        self.check("404.html", '<a href="/index.html?v=1#main">Home</a>', True)
        self.check("404.html", '<a href="/index.html#missing">Home</a>', False)
        self.check("404.html", '<img src="/missing.png">', False)

    def test_css_resource(self):
        self.check("style.css", 'body { background: url("missing.png"); }', False)

    def test_repository_inventory_and_empty_scan_rejection(self):
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        (self.root / "README.md").write_text("No links here.\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Checker test", "-c",
                        "user.email=checker@example.invalid", "commit", "--quiet",
                        "-m", "Local regression fixture"], cwd=self.root, check=True)
        output = self.root / "report.json"
        command = [sys.executable, str(Path(__file__).with_name("check.py")),
                   "--binary", str(BINARY), "--repo", str(self.root),
                   "--output", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(output.read_text())["passed"])
        (self.root / "README.md").write_text("[target](target.md#existing-heading)")
        (self.root / "untracked.md").write_text("[missing](missing.md)")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = json.loads(output.read_text())
        self.assertEqual(list(evidence["files"]), ["README.md"])
        self.assertNotIn(str(self.root), output.read_text())
        subprocess.run(["git", "add", "untracked.md"], cwd=self.root, check=True)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_http_success_fragment_and_404(self):
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(self.root)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            (self.root / "index.html").write_text('<h1 id="main">Main</h1>')
            base = f"http://127.0.0.1:{server.server_port}"
            for suffix, passed in [("/index.html#main", True),
                                   ("/index.html#missing", False),
                                   ("/missing.html", False)]:
                self.check("README.md", f"[HTTP]({base}{suffix})", passed,
                           allow_test_loopback=True)
            report = self.check("README.md", f"[example]({base}/)", True)
            self.assertEqual(report["excludes"], 1)
            self.assertEqual(report["successful"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main(verbosity=2)
