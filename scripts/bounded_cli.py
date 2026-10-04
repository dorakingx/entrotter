#!/usr/bin/env python3
"""Run the installed trusted CLI in one bounded Linux user-service job.

This is an operator tool, not a sandbox or an arbitrary-command interface.
Install with check_host_envelope.py beside the pinned guest source repositories.
"""

import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import sys

from check_host_envelope import current_limits

UNIT = "entrotter-cli-bounded.service"
PROPERTIES = {
    "CPUQuota": "100%",
    "MemoryMax": "256M",
    "MemorySwapMax": "0",
    "TasksMax": "64",
    "LimitNOFILE": "256",
    "LimitCORE": "0",
    "NoNewPrivileges": "yes",
    "KillMode": "control-group",
    "RuntimeMaxSec": "180s",
    "TimeoutStopSec": "2s",
    "Restart": "no",
    "UMask": "0077",
}


def process_start(pid: int) -> str:
    """Linux start ticks distinguish a reused PID from the original caller."""
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


def cancel(signum: int, frame: object) -> None:
    raise RuntimeError(f"CLI job cancelled by signal {signum}")


def stop(child: subprocess.Popen[bytes]) -> None:
    if child.poll() is not None:
        return
    try:
        os.killpg(child.pid, signal.SIGTERM)
        child.wait(timeout=1)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=1)
    except ProcessLookupError:
        child.wait(timeout=1)


def worker(pid: int, start: str, cwd: str, arguments: list[str]) -> int:
    # Check actual kernel limits before importing or executing the CLI.
    current_limits()
    app = Path.home() / ".local/share/entrotter"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        str(app / name / "src") for name in ["engine", "sdk", "cli"]
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # The syscall wrapper exists on Linux only; Darwin's typing stubs omit it.
    owner: int = getattr(os, "pidfd_open")(pid)
    child = None
    try:
        if process_start(pid) != start:
            raise ValueError("Original CLI caller is gone; refusing a reused PID")
        with selectors.DefaultSelector() as watcher:
            watcher.register(owner, selectors.EVENT_READ)
            if watcher.select(timeout=0):
                raise ValueError("Original CLI caller already exited")
            signal.signal(signal.SIGTERM, cancel)
            signal.signal(signal.SIGINT, cancel)
            child = subprocess.Popen(
                ["/usr/bin/python3", "-P", "-m", "entrotter_cli", *arguments],
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            while child.poll() is None:
                if watcher.select(timeout=0.1):
                    raise RuntimeError("Original CLI caller exited; cancelling job")
            code = child.returncode
            return code if code >= 0 else 128 - code
    finally:
        if child is not None:
            stop(child)
        os.close(owner)


def dispatch(arguments: list[str]) -> int:
    if sys.platform != "linux" or not hasattr(os, "pidfd_open"):
        raise ValueError("Bounded CLI requires Linux cgroup v2 and pidfd support")
    if not arguments:
        raise ValueError("Pass CLI arguments, for example: run fixture.json --local")
    pid = os.getpid()
    command = [
        "/usr/bin/systemd-run",
        "--user",
        "--unit=" + UNIT,
        "--wait",
        "--pipe",
        "--collect",
        "--quiet",
        "--service-type=exec",
        "--expand-environment=no",
        "--property=EnvironmentFile="
        + shlex.quote(str(Path.home() / ".config/entrotter/engine.env")),
        *["--property=" + key + "=" + value for key, value in PROPERTIES.items()],
        "/usr/bin/python3",
        str(Path(__file__).resolve()),
        "--worker",
        str(pid),
        process_start(pid),
        str(Path.cwd()),
        "--",
        *arguments,
    ]
    # Fixed unit name gives atomic per-user admission, even across caller folders.
    # No secrets are placed in command arguments; the private environment file is
    # read by the user manager. CLI paths/arguments never pass through a shell.
    return subprocess.run(command, stdin=subprocess.DEVNULL, check=False).returncode


def main() -> int:
    try:
        arguments = sys.argv[1:]
        if arguments and arguments[0] == "--worker":
            if len(arguments) < 6 or arguments[4] != "--":
                raise ValueError("Malformed internal CLI job invocation")
            return worker(int(arguments[1]), arguments[2], arguments[3], arguments[5:])
        return dispatch(arguments)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Bounded CLI rejected: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
