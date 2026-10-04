#!/usr/bin/env python3
"""Actual admission, argument, owner-death and full 180-second CLI budget proof.

Run only in the installed dedicated Linux test VM. HTTP faults below deliberately
stall a local test server; they are not model, archive or successful engine runs.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time

APP = Path.home() / ".local/share/entrotter"
LAUNCHER = APP / "bounded_cli.py"
UNIT = "entrotter-cli-bounded.service"


def show():
    process = subprocess.run(
        [
            "systemctl",
            "--user",
            "show",
            UNIT,
            "-p",
            "MainPID",
            "-p",
            "ActiveState",
            "-p",
            "RuntimeMaxUSec",
            "-p",
            "Result",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return dict(line.split("=", 1) for line in process.stdout.splitlines())


def wait_idle():
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if show().get("MainPID", "0") == "0":
            return
        time.sleep(0.05)
    raise RuntimeError("CLI unit remains active after cancellation")


class FaultServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, drip):
        super().__init__(("127.0.0.1", 0), FaultHandler)
        self.seen = threading.Event()
        self.release = threading.Event()
        self.drip = drip


class FaultHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.server.seen.set()
        if not self.server.drip:
            self.server.release.wait(20)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(1024 * 1024))
        self.end_headers()
        try:
            while not self.server.release.wait(0.2):
                self.wfile.write(b" ")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def limits(pid):
    path = next(
        line[3:]
        for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
        if line.startswith("0::/")
    )
    root = Path("/sys/fs/cgroup") / path.lstrip("/")
    return {
        name: (root / name).read_text().strip()
        for name in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")
    }


def fault_case(kind, work):
    server = FaultServer(kind == "runtime")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    output = work / (kind + ".json")
    output.write_text("existing owner data")
    command = [
        "/usr/bin/python3",
        str(LAUNCHER),
        "run",
        str(APP / "fixture.json"),
        "--api",
        f"http://127.0.0.1:{server.server_port}",
        "-o",
        str(output),
    ]
    started = time.monotonic()
    owner = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if not server.seen.wait(10):
            raise RuntimeError("Bounded CLI never reached the fault server")
        state = show()
        actual = limits(int(state["MainPID"]))
        if actual != {
            "cpu.max": "100000 100000",
            "memory.max": "268435456",
            "memory.swap.max": "0",
            "pids.max": "64",
        }:
            raise RuntimeError("Actual CLI cgroup differs from its limits")
        if state["RuntimeMaxUSec"] != "3min":
            raise RuntimeError("Actual CLI lifetime is not 180 seconds")
        duplicate = None
        if kind == "sigterm":
            duplicate = subprocess.run(
                ["/usr/bin/python3", str(LAUNCHER), "doctor"],
                capture_output=True,
                timeout=10,
            )
            if duplicate.returncode == 0 or show()["MainPID"] != state["MainPID"]:
                raise RuntimeError("Second CLI disturbed or bypassed the incumbent")
        if kind != "runtime":
            owner.send_signal(signal.SIGTERM if kind == "sigterm" else signal.SIGKILL)
        stdout, stderr = owner.communicate(timeout=195 if kind == "runtime" else 5)
        elapsed = time.monotonic() - started
        wait_idle()
        if output.read_text() != "existing owner data" or owner.returncode == 0:
            raise RuntimeError("Fault replaced the destination or returned success")
        if kind == "runtime" and not 179 <= elapsed <= 186:
            raise RuntimeError(f"Wrong full-budget expiry: {elapsed}")
        recovery = subprocess.run(
            ["/usr/bin/python3", str(LAUNCHER), "doctor"],
            capture_output=True,
            timeout=10,
        )
        if recovery.returncode:
            raise RuntimeError(
                "CLI admission did not recover: " + recovery.stderr.decode()
            )
        return {
            "kind": kind,
            "elapsed_seconds": elapsed,
            "kernel_limits": actual,
            "runtime_max": state["RuntimeMaxUSec"],
            "owner_returncode": owner.returncode,
            "duplicate_rejected_incumbent_preserved": duplicate is not None,
            "recovery_passed": True,
            "destination_preserved": True,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
        server.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        wait_idle()


def main():
    wait_idle()
    with tempfile.TemporaryDirectory(prefix="entrotter-cli-proof-") as directory:
        work = Path(directory) / "cwd %h $HOME ' space"
        work.mkdir()
        # A report folder must not select a Python package for the trusted CLI.
        spoof = work / "entrotter_cli"
        spoof.mkdir()
        (spoof / "__init__.py").write_text(
            "raise RuntimeError('Untrusted cwd package was imported')\n"
        )
        scenario = work / "scenario $HOME%h.json"
        scenario.write_bytes((APP / "fixture.json").read_bytes())
        output = work / "report $HOME%h.json"
        literal = subprocess.run(
            [
                "/usr/bin/python3",
                str(LAUNCHER),
                "run",
                scenario.name,
                "--local",
                "-o",
                output.name,
            ],
            cwd=work,
            capture_output=True,
            timeout=195,
        )
        if literal.returncode:
            raise RuntimeError("Literal arguments failed: " + literal.stderr.decode())
        expected = json.loads((APP / "bounded-fixture.json").read_text())
        if json.loads(output.read_text()) != expected:
            raise RuntimeError("Literal-path report differs from the complete fixture")
        results = [fault_case(kind, work) for kind in ("sigterm", "sigkill", "runtime")]
    wait_idle()
    workers = subprocess.check_output(
        ["docker", "ps", "-aq", "--filter", "label=org.entrotter.worker=true"],
        text=True,
    ).strip()
    if workers:
        raise RuntimeError("An owned worker remains")
    print(
        json.dumps(
            {
                "status": "passed",
                "literal_paths_preserved": True,
                "cwd_package_spoof_not_imported": True,
                "faults": results,
                "owned_workers_after_run": 0,
                "probe_scope": "Faults use a deliberately stalled local HTTP server; "
                "normal fixture and real local Anvil equality are separate evidence.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
