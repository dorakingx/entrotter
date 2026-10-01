#!/usr/bin/env python3
"""Fail closed unless this Linux service has the documented cgroup limits."""

import json
from pathlib import Path
import resource
import sys


def validate_limits(values: dict[str, str]) -> dict[str, int]:
    quota, period = (int(part) for part in values["cpu.max"].split())
    memory = int(values["memory.max"])
    swap = int(values["memory.swap.max"])
    tasks = int(values["pids.max"])
    if not (0 < quota <= period and period > 0):
        raise ValueError("Host service needs at most one CPU quota")
    if not (0 < memory <= 256 * 1024 * 1024 and swap == 0):
        raise ValueError("Host service needs at most 256 MiB and no swap")
    if not 0 < tasks <= 64:
        raise ValueError("Host service needs at most 64 tasks")
    return {
        "cpu_quota_us": quota,
        "cpu_period_us": period,
        "memory_bytes": memory,
        "swap_bytes": swap,
        "tasks": tasks,
    }


def current_limits() -> dict[str, int]:
    if sys.platform != "linux":
        raise ValueError("The bounded host service requires Linux cgroup v2")
    entries = Path("/proc/self/cgroup").read_text().splitlines()
    paths = [line[3:] for line in entries if line.startswith("0::/")]
    if len(paths) != 1 or ".." in Path(paths[0]).parts:
        raise ValueError("Cannot identify the service cgroup v2 path")
    group = Path("/sys/fs/cgroup") / paths[0].lstrip("/")
    result = validate_limits(
        {
            name: (group / name).read_text().strip()
            for name in ["cpu.max", "memory.max", "memory.swap.max", "pids.max"]
        }
    )
    status = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
    )
    if status.get("NoNewPrivs", "").strip() != "1":
        raise ValueError("The host service requires NoNewPrivileges")
    for limit, maximum in [(resource.RLIMIT_NOFILE, 256), (resource.RLIMIT_CORE, 0)]:
        soft, hard = resource.getrlimit(limit)
        if not 0 <= soft <= hard <= maximum:
            raise ValueError("Host file descriptor/core limits are missing")
    return result


def main() -> None:
    try:
        print(json.dumps({"status": "passed", "limits": current_limits()}))
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Host resource envelope rejected: {error}") from None


if __name__ == "__main__":
    main()
