#!/usr/bin/env python3
"""Explicit Linux integration checks for the installed, local host service.

Run only in a dedicated test VM. Creates bounded transient systemd user units;
never run this program as an HTTP handler or accept its arguments from reports.
"""

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid

SERVICE = "entrotter-engine.service"
PROPERTIES = {
    "CPUQuota": "100%",
    "MemoryMax": "256M",
    "MemorySwapMax": "0",
    "TasksMax": "64",
    "LimitNOFILE": "256",
    "LimitCORE": "0",
    "NoNewPrivileges": "yes",
    "KillMode": "control-group",
    "RuntimeMaxSec": "15s",
    "TimeoutStopSec": "1s",
    "Restart": "no",
}


def command(*args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def show(unit):
    text = command(
        "systemctl",
        "--user",
        "show",
        unit,
        "-p",
        "ActiveState",
        "-p",
        "Result",
        "-p",
        "MainPID",
        "-p",
        "ControlGroup",
        "-p",
        "RuntimeMaxUSec",
        "-p",
        "MemoryMax",
        "-p",
        "MemorySwapMax",
        "-p",
        "TasksMax",
    )
    return dict(line.split("=", 1) for line in text.splitlines())


def cgroup():
    path = next(
        x[3:]
        for x in Path("/proc/self/cgroup").read_text().splitlines()
        if x.startswith("0::/")
    )
    return Path("/sys/fs/cgroup") / path.lstrip("/")


def probe(kind):
    # Every probe first verifies the actual cgroup, not just launch arguments.
    from check_host_envelope import current_limits

    admitted = current_limits()
    print(json.dumps({"stage": "admission", "limits": admitted}), flush=True)
    group = cgroup()
    if kind == "memory":
        allocations = [bytearray(16 * 1024 * 1024) for _ in range(24)]
        raise RuntimeError(f"Memory cap did not stop {len(allocations)} allocations")
    if kind == "runtime":
        time.sleep(10)
        raise RuntimeError("Runtime limit failed")
    children = []
    try:
        if kind == "pids":
            for _ in range(80):
                try:
                    children.append(
                        subprocess.Popen(
                            [sys.executable, "-c", "import time; time.sleep(10)"],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    )
                except OSError as error:
                    if error.errno != errno.EAGAIN:
                        raise
                    print(
                        json.dumps(
                            {
                                "kind": kind,
                                "children": len(children),
                                "errno": error.errno,
                                "events": (group / "pids.events").read_text(),
                            }
                        ),
                        flush=True,
                    )
                    return
            raise RuntimeError("Task cap did not reject 80 children")
        before = dict(x.split() for x in (group / "cpu.stat").read_text().splitlines())
        code = "import time; stop=time.monotonic()+3\nwhile time.monotonic()<stop: pass"
        children = [subprocess.Popen([sys.executable, "-c", code]) for _ in range(2)]
        for child in children:
            child.wait(timeout=8)
        after = dict(x.split() for x in (group / "cpu.stat").read_text().splitlines())
        throttled = int(after["nr_throttled"]) - int(before["nr_throttled"])
        if throttled <= 0:
            raise RuntimeError("No observed CPU throttling")
        print(json.dumps({"kind": kind, "throttled_periods": throttled}), flush=True)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=["cpu", "memory", "pids", "runtime"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.probe:
        probe(args.probe)
        return
    if sys.platform != "linux" or args.output is None:
        raise SystemExit("Run in the dedicated Linux VM with --output")
    app = Path.home() / ".local/share/entrotter"
    state = show(SERVICE)
    if (
        state["ActiveState"] != "active"
        or state["MemoryMax"] != "268435456"
        or state["TasksMax"] != "64"
        or state["RuntimeMaxUSec"] != "1h"
    ):
        raise RuntimeError("The installed API service is not running with its limits")
    group = Path("/sys/fs/cgroup") / state["ControlGroup"].lstrip("/")
    limits = {
        name: (group / name).read_text().strip()
        for name in ["cpu.max", "memory.max", "memory.swap.max", "pids.max"]
    }
    from check_host_envelope import validate_limits

    validate_limits(limits)
    environment = dict(
        os.environ,
        PYTHONPATH=":".join(
            str(app / repo / "src") for repo in ["engine", "sdk", "cli"]
        ),
        ENTROTTER_EXPORT_STATE_DIR=str(app / "test-export-ledger"),
    )
    reports = []
    for name in ["fixture", "local"]:
        output = app / f"test-{name}.json"
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "entrotter_cli",
                "run",
                str(app / f"{name}.json"),
                "-o",
                str(output),
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=210,
        )
        if process.returncode:
            raise RuntimeError(process.stderr)
        report = json.loads(output.read_text())
        artifact = report.pop("artifact_id")
        calculated = hashlib.sha256(
            json.dumps(
                report, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()
        if artifact != calculated:
            raise RuntimeError("API report integrity mismatch")
        with urllib.request.urlopen(
            "http://127.0.0.1:8787/v1/runs/" + artifact, timeout=10
        ) as response:
            stored = json.load(response)
        report["artifact_id"] = artifact
        if stored != report:
            raise RuntimeError("Stored API and CLI reports differ")
        reports.append(
            {
                "case": name,
                "artifact_id": artifact,
                "mode": report["mode"],
                "api_cli_exact_equality": True,
            }
        )
    results = []
    for kind in ["cpu", "pids", "memory", "runtime"]:
        unit = "entrotter-host-proof-" + uuid.uuid4().hex + ".service"
        properties = dict(PROPERTIES)
        if kind == "runtime":
            properties["RuntimeMaxSec"] = "2s"
        commandline = ["systemd-run", "--user", "--unit=" + unit, "--wait", "--pipe"]
        commandline += [
            "--property=" + key + "=" + value for key, value in properties.items()
        ]
        started = time.monotonic()
        try:
            process = subprocess.run(
                [
                    *commandline,
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--probe",
                    kind,
                ],
                capture_output=True,
                text=True,
                timeout=25,
            )
            result = show(unit)
            expected = {
                "cpu": "success",
                "pids": "success",
                "memory": "oom-kill",
                "runtime": "timeout",
            }[kind]
            if result["Result"] != expected or result["MainPID"] != "0":
                raise RuntimeError(
                    f"Unexpected {kind} result: {result}, {process.stderr}"
                )
            if kind in ["cpu", "pids"] and process.returncode:
                raise RuntimeError(process.stderr)
            results.append(
                {
                    "probe": kind,
                    "result": {
                        key: result[key] for key in ["ActiveState", "Result", "MainPID"]
                    },
                    "configured_properties": properties,
                    "exit_code": process.returncode,
                    "elapsed_seconds": time.monotonic() - started,
                    "output": process.stdout.strip(),
                }
            )
        finally:
            subprocess.run(
                ["systemctl", "--user", "stop", unit], capture_output=True, timeout=15
            )
            subprocess.run(
                ["systemctl", "--user", "reset-failed", unit],
                capture_output=True,
                timeout=15,
            )
    negative_unit = "entrotter-host-proof-" + uuid.uuid4().hex + ".service"
    marker = app / "unexpected-unguarded-start"
    if marker.exists():
        raise RuntimeError("Refuse to overwrite prior guard marker")
    negative = dict(PROPERTIES, MemoryMax="infinity")
    negative["ExecStartPre"] = (
        str(Path(sys.executable)) + " " + str(app / "check_host_envelope.py")
    )
    try:
        process = subprocess.run(
            [
                "systemd-run",
                "--user",
                "--unit=" + negative_unit,
                "--wait",
                "--pipe",
                *["--property=" + key + "=" + value for key, value in negative.items()],
                sys.executable,
                "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).touch()",
                str(marker),
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )
        rejected = show(negative_unit)
        if (
            process.returncode == 0
            or marker.exists()
            or rejected["Result"] != "exit-code"
        ):
            raise RuntimeError("Unbounded unit reached its main executable")
        guard = {
            "result": rejected["Result"],
            "main_executable_started": marker.exists(),
            "exit_code": process.returncode,
            "diagnostics": process.stdout + process.stderr,
        }
    finally:
        subprocess.run(
            ["systemctl", "--user", "stop", negative_unit],
            capture_output=True,
            timeout=15,
        )
        subprocess.run(
            ["systemctl", "--user", "reset-failed", negative_unit],
            capture_output=True,
            timeout=15,
        )
    args.output.write_text(
        json.dumps(
            {
                "service": state,
                "kernel_limits": limits,
                "reports": reports,
                "probes": results,
                "unbounded_start_rejected": guard,
                "runtime_probe_seconds": 2,
                "production_runtime_expiry_not_waited": True,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {"reports": len(reports), "probes": len(results), "status": "passed"}
        )
    )


if __name__ == "__main__":
    main()
