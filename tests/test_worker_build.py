"""Build input bounds; daemon access is replaced only in these unit tests."""

from contextlib import nullcontext
import ctypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "build_worker", ROOT / "scripts/build_worker.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class WorkerBuildTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX process supervision")
    def test_native_block_cannot_delay_the_supervised_deadline(self):
        def native_block(*args):
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            # PyDLL holds the GIL during this native call. A Python thread/timer
            # in the same process is insufficient; the separate guardian kills it.
            ctypes.PyDLL(None).sleep(5)

        started = time.monotonic()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(builder, "prepare_image", side_effect=native_block):
                with self.assertRaisesRegex(ValueError, "deadline"):
                    with builder.build_deadline(0.2):
                        builder.prepare_supervised([], Path(directory), None, 0.2)
        self.assertLess(time.monotonic() - started, 1.2)

    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX process supervision")
    def test_owner_sigkill_closes_lifetime_pipe_and_stops_build_session(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "pid"
            code = """import os,sys,time,signal
from pathlib import Path
sys.path.insert(0, 'scripts')
import build_worker as b
def stalled(*args):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    Path(sys.argv[1]).write_text(str(os.getpid()))
    time.sleep(10)
b.prepare_image=stalled
b.prepare_supervised([], Path(sys.argv[2]), None, 10)
"""
            owner = subprocess.Popen([sys.executable, "-c", code, str(marker), directory], cwd=ROOT)
            try:
                deadline = time.monotonic() + 3
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(marker.exists(), "The supervised job never started")
                pid = int(marker.read_text())
                owner.kill()
                owner.wait(timeout=2)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    observed = subprocess.run(["ps", "-eo", "pgid=,stat="], capture_output=True, text=True, timeout=2)
                    active = [line for line in observed.stdout.splitlines() if line.split()[0] == str(pid) and not line.split()[1].startswith("Z")]
                    if not active:
                        break
                    time.sleep(0.02)
                self.assertFalse(active, active)
            finally:
                if owner.poll() is None:
                    owner.kill()
                owner.wait(timeout=2)

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires POSIX timers")
    def test_real_stalled_http_body_is_interrupted(self):
        release = threading.Event()

        class Stalled(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "100")
                self.end_headers()
                release.wait(5)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Stalled)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(ValueError, "deadline"):
                with builder.build_deadline(0.15):
                    with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=5) as response:
                        response.read(100)
            self.assertLess(time.monotonic() - started, 0.8)
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires POSIX timers")
    def test_timeout_kills_owned_command_and_term_ignoring_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "child-pid"
            code = "import os,signal,time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); pid=os.fork(); Path(%r).write_text(str(os.getpid())) if pid==0 else None; time.sleep(10)" % str(marker)
            started = time.monotonic()
            with self.assertRaisesRegex(ValueError, "deadline"):
                with builder.build_deadline(0.5):
                    builder.run_build_command([sys.executable, "-c", code])
            self.assertLess(time.monotonic() - started, 3)
            self.assertTrue(marker.exists(), "The descendant never started")
            pid = int(marker.read_text())
            state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=2)
            self.assertTrue(not state.stdout.strip() or state.stdout.strip().startswith("Z"), state.stdout)

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires POSIX timers")
    def test_sigterm_cancels_and_restores_process_handlers(self):
        handlers = {signum: signal.getsignal(signum) for signum in [signal.SIGTERM, signal.SIGINT, signal.SIGALRM]}
        with self.assertRaisesRegex(KeyboardInterrupt, "cancelled"):
            with builder.build_deadline(3):
                builder.run_build_command([sys.executable, "-c", f"import os,signal,time; os.kill({os.getpid()}, signal.SIGTERM); time.sleep(10)"])
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertEqual(handlers, {signum: signal.getsignal(signum) for signum in handlers})

    def test_manifest_failure_preserves_prior_bytes_without_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "manifest.json"
            target.write_text("previous manifest")
            with patch.object(builder.os, "replace", side_effect=OSError("failed")):
                with self.assertRaisesRegex(OSError, "failed"):
                    builder.write_manifest(target, {"image_id": "new"})
            self.assertEqual(target.read_text(), "previous manifest")
            self.assertEqual(list(Path(directory).iterdir()), [target])
            builder.write_manifest(target, {"image_id": "new"})
            self.assertIn('"image_id": "new"', target.read_text())

    def test_invalid_budgets_are_rejected_before_allocating_resources(self):
        for seconds in ["0", "-1", "601", "nan", "inf"]:
            with self.subTest(seconds=seconds), patch("sys.argv", ["build_worker", "--timeout-seconds", seconds]):
                with self.assertRaises(SystemExit) as caught:
                    builder.main()
                self.assertEqual(caught.exception.code, 2)

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires POSIX timers")
    def test_blocked_download_obeys_whole_build_budget_and_preserves_manifest(self):
        def blocked_download(*args, **kwargs):
            time.sleep(2)
            raise ValueError("download finally returned")

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            output.write_text("previous manifest")
            started = time.monotonic()
            with (
                patch.object(builder, "BUILD_SECONDS", 0.15, create=True),
                patch.object(builder, "client", return_value=nullcontext([])),
                patch.object(builder, "verify_daemon", return_value={"Architecture": "aarch64"}),
                patch.object(builder, "urlopen", side_effect=blocked_download),
                patch("sys.argv", ["build_worker", "--output", str(output)]),
                self.assertRaisesRegex(ValueError, "deadline"),
            ):
                builder.main()
            self.assertLess(time.monotonic() - started, 0.8)
            self.assertEqual(output.read_text(), "previous manifest")

    def test_exact_limit_is_accepted_and_hash_is_preserved(self):
        payload = b"verified release bytes"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "archive"
            with patch.object(builder, "MAX_ARCHIVE_BYTES", len(payload)):
                builder.copy_verified_archive(
                    io.BytesIO(payload), target, hashlib.sha256(payload).hexdigest()
                )
            self.assertEqual(target.read_bytes(), payload)

    def test_endless_stream_cannot_fill_disk_or_request_unbounded_reads(self):
        class Endless:
            def read(self, size):
                self_case.assertGreater(size, 0)
                self_case.assertLessEqual(size, builder.READ_BYTES)
                return b"x" * size

        self_case = self
        limit = 2 * builder.READ_BYTES
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "archive"
            with (
                patch.object(builder, "MAX_ARCHIVE_BYTES", limit),
                self.assertRaisesRegex(ValueError, "archive exceeds"),
            ):
                builder.copy_verified_archive(Endless(), target, "unused")
            self.assertEqual(target.stat().st_size, limit)

    def test_corrupt_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                builder.copy_verified_archive(
                    io.BytesIO(b"changed"),
                    Path(directory) / "archive",
                    hashlib.sha256(b"original").hexdigest(),
                )

    def test_deadline_checks_after_slow_read_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "archive"
            with (
                patch.object(
                    builder.time,
                    "monotonic",
                    side_effect=[0, 1, builder.ARCHIVE_SECONDS],
                ),
                self.assertRaisesRegex(ValueError, "deadline exceeded"),
            ):
                builder.copy_verified_archive(io.BytesIO(b"late"), target, "unused")
            self.assertEqual(target.stat().st_size, 0)

    def test_local_regular_file_is_streamed_without_read_bytes(self):
        payload = b"local release bytes"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "archive"
            source.write_bytes(payload)
            with patch.object(
                Path, "read_bytes", side_effect=AssertionError("whole-file read")
            ):
                builder.stage_local_archive(
                    source, target, hashlib.sha256(payload).hexdigest()
                )
            self.assertEqual(target.read_bytes(), payload)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_fifo_without_writer_rejects_without_hanging(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "fifo"
            os.mkfifo(fifo)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; sys.path.insert(0, 'scripts'); from build_worker import stage_local_archive; stage_local_archive(Path(sys.argv[1]), Path(sys.argv[2]), 'unused')",
                    str(fifo),
                    str(Path(directory) / "target"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be a regular file", result.stderr)

    def test_oversized_archive_rejected_before_digest_or_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "archive"
            source.write_bytes(b"12345")
            output = Path(directory) / "manifest.json"
            output.write_text("previous manifest")
            with (
                patch.object(builder, "MAX_ARCHIVE_BYTES", 4, create=True),
                patch.object(builder, "client", return_value=nullcontext([])),
                patch.object(
                    builder, "verify_daemon", return_value={"Architecture": "aarch64"}
                ),
                patch(
                    "sys.argv",
                    ["build_worker", "--archive", str(source), "--output", str(output)],
                ),
                self.assertRaisesRegex(ValueError, "archive exceeds"),
            ):
                builder.main()
            self.assertEqual(output.read_text(), "previous manifest")


if __name__ == "__main__":
    unittest.main()
