#!/usr/bin/env python3
"""Measure one clean monorepo clone and its actual bounded local execution."""

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
    help="Replay recorded model decisions through the bounded worker, no model call",
)
mode.add_argument(
    "--bounded",
    action="store_true",
    help="Build and use the current monorepo bounded default",
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
parser.add_argument(
    "--public",
    action="store_true",
    help="Clone the personal public monorepo over HTTPS at the exact current revision",
)
args = parser.parse_args()
git_env = dict(os.environ)
if args.public:
    # Scoped child configuration; do not modify account/global settings.
    git_env = {k: v for k, v in git_env.items() if not k.startswith("GIT_")}
    git_env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_TERMINAL_PROMPT="0",
        GIT_ASKPASS="/usr/bin/false",
    )
# Every execution mode uses the current bounded default. The legacy --bounded
# spellings remain aliases; no native fallback or old-Org download is introduced.
bounded = True
recorded = args.agent or args.bounded_agent
revision = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=10, env=git_env
).strip()
if subprocess.check_output(
    ["git", "-C", str(ROOT), "diff", "HEAD", "--"], timeout=10, env=git_env
):
    raise ValueError("Commit the reviewed source before measuring a clean clone")
pins = {
    name: subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{name}"],
        text=True,
        timeout=10,
        env=git_env,
    ).strip()
    for name in ["engine", "sdk-python", "cli", "scenarios", "website"]
}
started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix="entrotter-reproduce-") as folder:
    work = Path(folder)
    public_url = "https://github.com/dorakingx/entrotter.git"
    if args.public:
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            raise ValueError("Public reproduction requires an exact Git commit")
        # Ignore inherited Git configuration/credentials, including checkout's
        # headers. These are child-process settings, not account/global changes.
        git = [
            "git",
            "-c",
            "credential.helper=",
            "-c",
            "http.extraHeader=",
            "-c",
            "http.cookieFile=",
            "-c",
            "http.saveCookies=false",
            "-c",
            "core.hooksPath=/dev/null",
        ]
        for command in [
            [*git, "clone", "--quiet", "--no-checkout", public_url, str(work)],
            [
                *git,
                "-C",
                str(work),
                "fetch",
                "--quiet",
                "--no-tags",
                "origin",
                revision,
            ],
            [*git, "-C", str(work), "checkout", "--quiet", "--detach", revision],
        ]:
            subprocess.run(command, env=git_env, check=True, timeout=120)
        if (
            subprocess.check_output(
                ["git", "-C", str(work), "remote", "get-url", "origin"],
                text=True,
                timeout=10,
                env=git_env,
            ).strip()
            != public_url
        ):
            raise ValueError("Public clone origin changed")
    else:
        # Local regression mode copies its own objects, without sibling clones.
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                "--single-branch",
                str(ROOT),
                str(work),
            ],
            check=True,
            timeout=120,
        )
    if (
        subprocess.check_output(
            ["git", "-C", str(work), "rev-parse", "HEAD"],
            text=True,
            timeout=10,
            env=git_env,
        ).strip()
        != revision
    ):
        raise ValueError("Source revision changed during clone")
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
    origins = json.loads(
        subprocess.check_output(
            [
                python,
                "-c",
                "import json, entrotter_cli, entrotter_sdk, entrotter_engine; "
                "print(json.dumps({m.__name__: m.__file__ for m in "
                "[entrotter_cli, entrotter_sdk, entrotter_engine]}))",
            ],
            cwd=work,
            env=env,
            text=True,
            timeout=10,
        )
    )
    module_origins = {}
    for name, path in origins.items():
        if not Path(path).is_relative_to(work):
            raise ValueError("Runtime package did not load from the fresh clone")
        module_origins[name] = Path(path).relative_to(work).as_posix()
    if (
        "include-system-site-packages = false"
        not in (work / "venv/pyvenv.cfg").read_text()
    ):
        raise ValueError("Fresh venv unexpectedly includes system site packages")
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
            (work / "evidence/agent-local-codex.json").read_bytes()
        )
        commands[0] = [
            python,
            "-m",
            "entrotter_cli",
            "replay",
            "recorded.json",
            "-o",
            "report.json",
        ]
    for command in commands:
        subprocess.run(
            command, cwd=work, env=env, check=True, capture_output=True, text=True
        )
    report = json.loads((work / "report.json").read_text())
    expected = (
        json.loads((work / "recorded.json").read_text())
        if recorded
        else json.loads((work / "website/reports" / sample).read_text())
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
    "monorepo_commit": revision,
    "component_trees": pins,
    "environment": "fresh public HTTPS clone and venv without pip; no system site packages or third-party runtime dependencies"
    if args.public
    else "fresh local clone and venv without pip; no system site packages or third-party runtime dependencies",
    "artifact_id": report["artifact_id"],
    "matches_recorded_sample" if recorded else "matches_public_sample": True,
    "scope": "one public HTTPS monorepo clone at the exact tested revision"
    if args.public
    else "one local monorepo clone; current code, data, website and coordination",
    "remote_public_clone_verified": args.public,
    "runtime_module_origins": module_origins,
    "source_origin": public_url if args.public else "current local checkout",
    "public_mode_credentials": "Inherited Git config, helpers, headers and cookies disabled; no claim about operator netrc/proxy configuration"
    if args.public
    else "not applicable",
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
    if args.bounded_agent:
        result["agent_entrypoint"] = "standalone CLI replay"
destination = args.output or ROOT / "evidence/monorepo-verification" / filename
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(0 if elapsed < 300 else 1)
