"""Actual BuildKit diagnostics; requires the locally built, tagged worker image."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from entrotter_engine.isolated import client, verify_daemon

ROOT = Path(__file__).resolve().parents[1]


class BuildOutputTests(unittest.TestCase):
    def test_real_multistep_build_has_one_bounded_diagnostic_stream(self):
        image = os.environ["ENTROTTER_WORKER_IMAGE"]
        owner = uuid.uuid4().hex
        with client() as prefix, tempfile.TemporaryDirectory() as directory:
            verify_daemon(prefix)
            base = json.loads(subprocess.check_output(
                [*prefix, "image", "inspect", image], timeout=10
            ))[0]
            tag = "entrotter-worker:" + base["Config"]["Labels"]["org.entrotter.source"][:16]
            tagged = json.loads(subprocess.check_output(
                [*prefix, "image", "inspect", tag], timeout=10
            ))[0]
            self.assertEqual(tagged["Id"], image)
            work = Path(directory)
            instruction = "RUN " + json.dumps([
                "python3", "-c",
                "import os,time\nfor _ in range(2048):\n os.write(1,b'o'*1023+b'\\n'); os.write(2,b'e'*1023+b'\\n'); time.sleep(0.001)"
            ]) + "\n"
            # One step can hit BuildKit's own log clipping first. Multiple steps
            # exercise the helper's aggregate production limit without changing
            # daemon settings or downloading another base image.
            (work / "Dockerfile").write_text("FROM " + tag + "\n" + instruction * 4)
            iid = work / "image-id"
            code = """import sys
sys.path.insert(0,'scripts')
import build_worker as b
with b.build_deadline(60),b.client() as prefix:
    b.run_build_command([*prefix,'build','--network=none','--no-cache',
        '--progress=plain','--label','org.entrotter.build-log-probe='+sys.argv[3],
        '--iidfile',sys.argv[2],sys.argv[1]])
"""
            try:
                result = subprocess.run(
                    [sys.executable, "-c", code, str(work), str(iid), owner],
                    cwd=ROOT, capture_output=True, timeout=70,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-2048:])
                self.assertEqual(result.stdout, b"")
                self.assertLessEqual(len(result.stderr), 1024 * 1024 + 256)
                notice = b"Entrotter: 1 MiB diagnostic limit; further build output discarded."
                self.assertEqual(result.stderr.count(notice), 1)
                proof = {
                    "status": "passed", "steps": 4,
                    "producer_requested_bytes": 16 * 1024 * 1024,
                    "stdout_bytes": len(result.stdout),
                    "stderr_bytes": len(result.stderr), "notice_count": 1,
                    "scope": "Actual local BuildKit; RUN network disabled; owned probe image removed in finally",
                }
            finally:
                if iid.exists():
                    probe = iid.read_text().strip()
                    details = json.loads(subprocess.check_output(
                        [*prefix, "image", "inspect", probe], timeout=10
                    ))[0]
                    self.assertEqual(details["Config"]["Labels"].get("org.entrotter.build-log-probe"), owner)
                    subprocess.run([*prefix, "image", "rm", probe], check=True,
                                   stdout=subprocess.DEVNULL, timeout=10)
            output = ROOT / ".quality/build-output-docker.json"
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps(proof, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
