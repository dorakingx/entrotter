"""Controller regressions; actual cgroup/pidfd enforcement runs in Linux."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("bounded_cli", SCRIPTS / "bounded_cli.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class BoundedCliTests(unittest.TestCase):
    def test_unsupported_host_fails_before_job_creation(self):
        with (
            mock.patch.object(launcher.sys, "platform", "darwin"),
            mock.patch.object(launcher.subprocess, "run") as run,
            self.assertRaisesRegex(ValueError, "requires Linux"),
        ):
            launcher.dispatch(["doctor"])
        run.assert_not_called()

    def test_missing_kernel_limits_fail_before_cli_execution(self):
        with (
            mock.patch.object(
                launcher, "current_limits", side_effect=ValueError("cap")
            ),
            mock.patch.object(launcher.subprocess, "Popen") as popen,
            self.assertRaisesRegex(ValueError, "cap"),
        ):
            launcher.worker(123, "456", "/tmp", ["doctor"])
        popen.assert_not_called()

    def test_start_identity_handles_parentheses_and_spaces_in_comm(self):
        with mock.patch.object(
            launcher.Path,
            "read_text",
            return_value="123 (name with ) space) " + " ".join(map(str, range(3, 30))),
        ):
            self.assertEqual(launcher.process_start(123), "22")

    def test_term_ignoring_owned_process_is_killed(self):
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                "print('ready',flush=True); time.sleep(60)",
            ],
            start_new_session=True,
            stdout=subprocess.PIPE,
        )
        try:
            self.assertEqual(child.stdout.readline(), b"ready\n")
            started = time.monotonic()
            launcher.stop(child)
            self.assertLess(time.monotonic() - started, 2.5)
            self.assertEqual(child.returncode, -9)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
            child.stdout.close()


if __name__ == "__main__":
    unittest.main()
