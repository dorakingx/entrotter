#!/usr/bin/env python3
"""Optional real-browser smoke test for the zero-build Pages site."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SITE = WORKSPACE / "entrotter.github.io"
EVIDENCE = ROOT / "evidence"
EVIDENCE.mkdir(exist_ok=True)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(SITE)))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
url = f"http://127.0.0.1:{server.server_port}/"
results = []
try:
    with sync_playwright() as p:
        executable = (
            os.environ.get("CHROMIUM_PATH")
            or shutil.which("chromium")
            or shutil.which("google-chrome")
        )
        browser = p.chromium.launch(
            executable_path=executable,
            headless=True,
            args=["--no-sandbox"],
        )
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=1
        )
        errors = []
        requests = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: requests.append(r.url))
        page.goto(url)
        page.wait_for_function(
            "document.querySelector('#report-status').textContent.includes('Integrity verified locally')"
        )
        if not page.locator("#baseline-value").inner_text() == "5,800":
            raise AssertionError()
        if not page.locator("#candidate-value").inner_text() == "8,557.05":
            raise AssertionError()
        results.append(
            "Desktop: report loaded and SHA-256 verified; model values match engine output"
        )
        page.screenshot(path=str(EVIDENCE / "site-desktop.png"), full_page=True)
        page.select_option("#scenario", "recovery-trap")
        page.wait_for_function(
            "document.querySelector('#report-status').textContent.includes('recovery trap')"
        )
        if not page.locator("#delta-value").inner_text().startswith("-"):
            raise AssertionError()
        results.append(
            "Recovery fixture visibly underperforms holding (negative control)"
        )
        corrupt = json.loads((SITE / "reports/liquidity-shock.json").read_text())
        corrupt["candidate"]["metrics"]["final_equity"] = "99999999"
        page.set_input_files(
            "#import",
            {
                "name": "tampered.json",
                "mimeType": "application/json",
                "buffer": json.dumps(corrupt).encode(),
            },
        )
        page.wait_for_function(
            "document.querySelector('#report-status').textContent.includes('mismatch')"
        )
        if not page.locator("#candidate-value").inner_text() == "—":
            raise AssertionError()
        results.append("Tampered local artifact rejected; stale metrics cleared")
        # A correctly hashed title with markup must be rendered as text, never as an element.
        import hashlib

        hostile = json.loads((SITE / "reports/liquidity-shock.json").read_text())
        hostile.pop("artifact_id")
        hostile["scenario"]["title"] = "<img src=x onerror=alert(1)> 🛸"
        hostile["artifact_id"] = hashlib.sha256(
            json.dumps(
                hostile, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode()
        ).hexdigest()
        before = len(requests)
        page.set_input_files(
            "#import",
            {
                "name": "safe-text.json",
                "mimeType": "application/json",
                "buffer": json.dumps(hostile).encode(),
            },
        )
        page.wait_for_function(
            "document.querySelector('#report-status').textContent.includes('Integrity verified locally')"
        )
        if not page.locator("#report-status img").count() == 0:
            raise AssertionError()
        if not len(requests) == before:
            raise AssertionError()
        results.append(
            "Unicode hash compatible; imported HTML-like title stays inert text; no upload/network request"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        page.reload()
        page.wait_for_function(
            "document.querySelector('#report-status').textContent.includes('Integrity verified locally')"
        )
        if not page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        ):
            raise AssertionError()
        page.screenshot(path=str(EVIDENCE / "site-mobile.png"), full_page=True)
        results.append("390px mobile layout has no horizontal overflow")
        if not not errors:
            raise AssertionError(errors)
        if not all((r.startswith(url) or r.startswith("data:") for r in requests)):
            raise AssertionError(requests)
        results.append("No JavaScript exceptions or unexpected third-party requests")
        browser.close()
finally:
    server.shutdown()
    server.server_close()
    thread.join()
(EVIDENCE / "browser-verification.json").write_text(
    json.dumps(
        {"checks": results, "status": "passed", "server_scope": "local_only"}, indent=2
    )
    + "\n"
)
print("\n".join(results))
