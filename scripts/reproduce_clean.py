#!/usr/bin/env python3
"""Measure a public clean checkout; native/recorded defaults stay frozen, bounded is explicit."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument(
    "--historical",
    action="store_true",
    help="Require archive RPC and real Anvil; no fallback",
)
mode.add_argument(
    "--agent",
    action="store_true",
    help="Replay recorded model decisions on local Anvil, no model call",
)
mode.add_argument(
    "--bounded",
    action="store_true",
    help="Build and use the bounded default from separately pinned public sources",
)
mode.add_argument(
    "--bounded-agent",
    action="store_true",
    help="Build the bounded worker and replay the public local agent record, no model call",
)
parser.add_argument(
    "--foundry-archive",
    type=Path,
    help="For bounded modes: predownloaded Foundry archive, still checksum-verified",
)
parser.add_argument(
    "--output", type=Path, help="Write verification evidence to this file"
)
args = parser.parse_args()
bounded = args.bounded or args.bounded_agent
recorded = args.agent or args.bounded_agent
if args.foundry_archive and not bounded:
    parser.error("--foundry-archive requires --bounded or --bounded-agent")
pins = json.loads(
    (
        ROOT / ("bounded-worker-pins.json" if bounded else "dependency-pins.json")
    ).read_text()
)
started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix="entrotter-reproduce-") as folder:
    work = Path(folder)
    for name, sha in pins.items():
        target = work / name
        subprocess.run(["git", "init", "--quiet", str(target)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(target),
                "fetch",
                "--quiet",
                "--depth=1",
                f"https://github.com/entrotter/{name}.git",
                sha,
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(target), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
            check=True,
        )
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(work / "venv")], check=True
    )
    python = str(
        work / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        str(work / name / "src") for name in ["engine", "sdk-python", "cli"]
    )
    image_manifest = None
    if bounded:
        build = [
            python,
            "scripts/build_worker.py",
            "--output",
            str(work / "image.json"),
        ]
        if args.foundry_archive:
            build += ["--archive", str(args.foundry_archive.resolve())]
        subprocess.run(
            build,
            cwd=work / "engine",
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
        image_manifest = json.loads((work / "image.json").read_text())
        env["ENTROTTER_WORKER_IMAGE"] = image_manifest["image_id"]
    scenario = (
        "evm/ethereum-uniswap-slippage.json"
        if args.historical
        else "fixtures/liquidity-shock.json"
    )
    sample = (
        "ethereum-uniswap-slippage.json" if args.historical else "liquidity-shock.json"
    )
    commands = [
        [
            python,
            "-m",
            "entrotter_cli",
            "run",
            "scenarios/" + scenario,
            "--local",
            "-o",
            "report.json",
        ],
        [python, "-m", "entrotter_cli", "verify", "report.json"],
        [python, "-m", "entrotter_cli", "inspect", "report.json"],
    ]
    if recorded:
        (work / "recorded.json").write_bytes(
            (ROOT / "evidence/agent-local-codex.json").read_bytes()
        )
        commands[0] = [
            python,
            "-c",
            """import json
from entrotter_engine.agent import AgentController, ReplayPolicy
from entrotter_engine.runner import run_agent
from entrotter_engine.artifact import verify, write_report
r = json.load(open("recorded.json"))
if not verify(r): raise ValueError("Invalid recording hash")
steps = [x["request"]["observation"]["step"] for x in r["agent"]["exchanges"]]
write_report(run_agent(r["scenario"], AgentController(ReplayPolicy(r["agent"]), steps)), "report.json")
""",
        ]
        if args.bounded_agent:
            commands[0] = [
                python,
                "-c",
                """import json
from entrotter_engine.runner import run_agent
from entrotter_engine.artifact import verify, write_report
r = json.load(open("recorded.json"))
if not verify(r): raise ValueError("Invalid recording hash")
exchanges = r["agent"]["exchanges"]
steps = [x["request"]["observation"]["step"] for x in exchanges]
budget = exchanges[0]["request"]["limits"]["remaining_requested_gas"]
actual = run_agent(r["scenario"], decision_steps=steps, recording=r["agent"], max_requested_gas=budget)
if actual != r: raise ValueError("Complete recorded artifact differs")
write_report(actual, "report.json")
""",
            ]
    for command in commands:
        subprocess.run(
            command, cwd=work, env=env, check=True, capture_output=True, text=True
        )
    report = json.loads((work / "report.json").read_text())
    expected = (
        json.loads((work / "recorded.json").read_text())
        if recorded
        else json.loads((work / "entrotter.github.io/reports" / sample).read_text())
    )
    if not report == expected:
        raise AssertionError()
elapsed = time.perf_counter() - started
result = {
    "status": "passed",
    "wall_seconds_including_clone_and_venv": elapsed,
    "mode": "bounded-recorded-agent-local-evm"
    if args.bounded_agent
    else "bounded-offline"
    if args.bounded
    else (
        "recorded-agent-local-evm"
        if args.agent
        else ("archived-state" if args.historical else "offline")
    ),
    "under_five_minutes": elapsed < 300,
    "dependency_pins": pins,
    "environment": "fresh venv without pip; no system site packages or third-party runtime dependencies",
    "artifact_id": report["artifact_id"],
    "matches_recorded_sample" if recorded else "matches_public_sample": True,
    "scope": "five code/data/site repos; coordination checkout already present",
}
if bounded:
    result["bounded_worker"] = image_manifest
    result["prerequisites"] = (
        "Running configured local Docker/cgroup-v2 daemon; image/base/build caches may be warm. Docker installation/VM startup excluded; source clone, venv, image build and execution included."
    )
    result["predownloaded_foundry_archive"] = bool(args.foundry_archive)
filename = (
    "clean-bounded-agent-reproduction.json"
    if args.bounded_agent
    else "clean-bounded-reproduction.json"
    if args.bounded
    else (
        "clean-agent-reproduction.json"
        if args.agent
        else (
            "clean-historical-reproduction.json"
            if args.historical
            else "clean-reproduction.json"
        )
    )
)
if recorded:
    result["new_agent_model_calls"] = 0
destination = args.output or ROOT / "evidence" / filename
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(0 if elapsed < 300 else 1)
