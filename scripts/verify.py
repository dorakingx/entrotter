#!/usr/bin/env python3
"""Run all local checks. Skipped EVM tests are recorded, never disguised as evidence."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
p = argparse.ArgumentParser()
p.add_argument("--require-anvil", action="store_true")
args = p.parse_args()
if args.require_anvil and not shutil.which("anvil"):
    raise SystemExit("Anvil is required for this verification gate but is missing.")
env = dict(os.environ)
env["PYTHONPATH"] = os.pathsep.join(
    str(WORKSPACE / r / "src") for r in ["engine", "sdk-python", "cli"]
)
EVIDENCE = ROOT / "evidence"
EVIDENCE.mkdir(exist_ok=True)
checks = []
for repo in [
    "engine",
    "sdk-python",
    "cli",
    "scenarios",
    "entrotter.github.io",
    "entrotter",
]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    result = subprocess.run(
        command, cwd=WORKSPACE / repo, env=env, text=True, capture_output=True
    )
    log = result.stdout + result.stderr
    (EVIDENCE / f"{repo}-tests.log").write_text(log)
    print(repo, "PASS" if result.returncode == 0 else "FAIL")
    print("\n".join(log.strip().splitlines()[-4:]))
    checks.append(
        {
            "repository": repo,
            "command": "python -m unittest discover -s tests -v",
            "exit_code": result.returncode,
            "log": f"{repo}-tests.log",
            "contains_skipped_tests": bool("skipped" in log),
        }
    )
if shutil.which("node"):
    result = subprocess.run(
        ["node", "--test", "tests/report.test.mjs"],
        cwd=WORKSPACE / "entrotter.github.io",
        text=True,
        capture_output=True,
    )
    log = result.stdout + result.stderr
    (EVIDENCE / "website-javascript-tests.log").write_text(log)
    print("website JavaScript", "PASS" if result.returncode == 0 else "FAIL")
    checks.append(
        {
            "repository": "entrotter.github.io",
            "command": "node --test tests/report.test.mjs",
            "exit_code": result.returncode,
            "log": "website-javascript-tests.log",
            "contains_skipped_tests": False,
        }
    )
else:
    checks.append(
        {
            "repository": "entrotter.github.io",
            "command": "node --test tests/report.test.mjs",
            "exit_code": None,
            "status": "not_run_node_unavailable",
        }
    )
report = {
    "executed_at": datetime.now(timezone.utc).isoformat(),
    "python": sys.version.split()[0],
    "anvil_installed": shutil.which("anvil") is not None,
    "anvil_version": subprocess.check_output(["anvil", "--version"], text=True).strip()
    if shutil.which("anvil")
    else None,
    "archive_rpc_configured": bool(os.getenv("ENTROTTER_RPC_URL")),
    "historical_execution": "not_performed_by_this_script",
    "checks": checks,
}
(EVIDENCE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
raise SystemExit(
    int(
        any(
            c["exit_code"] != 0
            or (args.require_anvil and c.get("contains_skipped_tests"))
            for c in checks
        )
    )
)
