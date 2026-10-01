#!/usr/bin/env python3
"""Run a preregistered archived-state comparison, retaining failures and exact replay evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import subprocess
import time

from entrotter_engine.agent import AgentController, ReplayPolicy, RiskPolicy
from entrotter_engine.artifact import verify, write_report
from entrotter_engine.runner import run, run_agent
from codex_policy import CodexPolicy, PROMPT, PROMPT_VERSION
from entrotter_engine.agent import digest

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT.parent / "scenarios/benchmarks/causal-v1"
FROZEN_MANIFEST_SHA256 = (
    "f147489fcde8de04be6a9de459fe011018488bd75e66a84de55f6a8a35ed030e"
)


def frozen_cases(split):
    raw = (CASES / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_MANIFEST_SHA256:
        raise ValueError("Frozen manifest changed; use a newly named benchmark")
    manifest = json.loads(raw)
    policy = manifest["policy"]
    if (
        hashlib.sha256((ROOT / "scripts/codex_policy.py").read_bytes()).hexdigest()
        != policy["codex_adapter_sha256"]
    ):
        raise ValueError("Provider code differs from the pre-execution freeze")
    if (
        digest({"prompt": PROMPT}) != policy["prompt_sha256"]
        or PROMPT_VERSION != policy["prompt_version"]
    ):
        raise ValueError("Prompt differs from the pre-execution freeze")
    engine = subprocess.check_output(
        ["git", "-C", str(ROOT.parent / "engine"), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(ROOT.parent / "engine"), "status", "--porcelain"], text=True
    ).strip()
    if engine != policy["engine_commit"] or dirty:
        raise ValueError("Engine must be clean at the frozen source commit")
    selected = []
    for case in manifest["cases"]:
        path = (CASES / case["path"]).resolve()
        if not path.is_relative_to(CASES.resolve()):
            raise ValueError("Case path escapes the frozen bundle")
        if hashlib.sha256(path.read_bytes()).hexdigest() != case["sha256"]:
            raise ValueError("Frozen scenario changed")
        if (case["split"] == "holdout") == (split == "holdout"):
            selected.append((case, json.loads(path.read_text())))
    return manifest, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True, choices=["evaluation", "holdout"])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--generate-model",
        action="store_true",
        help="Explicitly consume authenticated model usage",
    )
    mode.add_argument(
        "--replay-only",
        action="store_true",
        help="Use saved recordings without model calls",
    )
    args = parser.parse_args()
    manifest, cases = frozen_cases(args.split)
    directory = ROOT / "evidence/causal-v1"
    directory.mkdir(exist_ok=True)
    summary_path = directory / (args.split + ".json")
    if summary_path.exists() and not args.replay_only:
        raise ValueError(
            "Existing split evidence will not be overwritten; inspect it before a separately named rerun"
        )
    if args.split == "holdout":
        evaluation = json.loads((directory / "evaluation.json").read_text())
        if (
            evaluation["manifest_sha256"] != FROZEN_MANIFEST_SHA256
            or evaluation["status"] != "passed"
        ):
            raise ValueError(
                "Complete the unchanged evaluation split before opening holdouts"
            )
    result = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "split": args.split,
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "manifest": manifest,
        "status": "running",
        "cases": [],
        "mode": "archived-state supplied-action evaluation",
        "limitations": [
            "One protocol, five hand-selected source states; no statistical confidence claim",
            "Implementation holdout is not unseen model training data",
            "No future price path or valuation; profit/drawdown undefined",
            "Anvil version pinned; no explicit hardfork override for fork runs, not canonical trace replay",
            "Run order is fixed; wall time includes provider/cache/network variability",
            "Resource measurements cover checker children, peak RSS is not aggregate or a hard limit",
        ],
    }
    for case, scenario in cases:
        row = {
            "id": case["id"],
            "split": case["split"],
            "source": case["source"],
            "policies": [],
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "status": "running",
        }
        result["cases"].append(row)
        if not args.replay_only:
            summary_path.write_text(json.dumps(result, indent=2) + "\n")
        for name in ["non-agent", "risk", "model"]:
            path = directory / f"{case['id']}-{name}.json"
            try:
                print(f"{args.split}: {case['id']} {name}", flush=True)
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                started = time.perf_counter()
                if args.replay_only:
                    recorded = json.loads(path.read_text())
                    if not verify(recorded) or recorded["scenario"] != scenario:
                        raise ValueError(
                            "Saved report is invalid or uses a changed scenario"
                        )
                    report = (
                        run(scenario)
                        if name == "non-agent"
                        else run_agent(
                            scenario,
                            AgentController(
                                ReplayPolicy(recorded["agent"]),
                                case["decision_steps"],
                                max_requested_gas=manifest["policy"][
                                    "max_requested_gas"
                                ],
                            ),
                        )
                    )
                    if report != recorded:
                        raise ValueError("Complete saved report replay diverged")
                else:
                    if name == "non-agent":
                        report = run(scenario)
                    else:
                        provider = (
                            RiskPolicy()
                            if name == "risk"
                            else CodexPolicy(model=manifest["policy"]["model"])
                        )
                        report = run_agent(
                            scenario,
                            AgentController(
                                provider,
                                case["decision_steps"],
                                max_requested_gas=manifest["policy"][
                                    "max_requested_gas"
                                ],
                            ),
                        )
                duration = time.perf_counter() - started
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                if (
                    not verify(report)
                    or report["source"]["block_hash"] != case["source"]["block_hash"]
                ):
                    raise ValueError("Report or source pin failed verification")
                if name == "non-agent":
                    baseline = report["baseline"]
                    if baseline != report["candidate"]:
                        raise ValueError(
                            "Identical prescribed proposals diverged between isolated branches"
                        )
                elif report["baseline"] != baseline:
                    raise ValueError(
                        "Policy did not retain an identical baseline branch"
                    )
                replay_start = time.perf_counter()
                if not args.replay_only and name != "non-agent":
                    repeated = run_agent(
                        scenario,
                        AgentController(
                            ReplayPolicy(report["agent"]),
                            case["decision_steps"],
                            max_requested_gas=manifest["policy"]["max_requested_gas"],
                        ),
                    )
                    if repeated != report:
                        raise ValueError("Complete newly recorded replay diverged")
                replay_seconds = (
                    time.perf_counter() - replay_start if name != "non-agent" else None
                )
                if not args.replay_only:
                    write_report(report, path)
                row["policies"].append(
                    {
                        "name": name,
                        "status": "passed",
                        "artifact_id": report["artifact_id"],
                        "wall_seconds": duration,
                        "replay_seconds": replay_seconds,
                        "exact_replay": name != "non-agent" or args.replay_only,
                        "child_cpu_seconds": after.ru_utime
                        + after.ru_stime
                        - before.ru_utime
                        - before.ru_stime,
                        "child_peak_rss_so_far": after.ru_maxrss,
                        "child_peak_rss_unit": "bytes"
                        if platform.system() == "Darwin"
                        else "KiB",
                        "metrics": report["candidate"]["metrics"],
                        "tokens": report["candidate"]["tokens"],
                        "actions": [x["status"] for x in report["candidate"]["trace"]],
                        "choices": [
                            x["response"]["choice"]
                            for x in report.get("agent", {}).get("exchanges", [])
                        ],
                    }
                )
            except BaseException as error:
                row["policies"].append(
                    {
                        "name": name,
                        "status": "failed",
                        "error_type": type(error).__name__,
                        "note": "No fallback policy or substitute state used; raw provider messages are not published",
                    }
                )
                row["status"] = "failed"
                result["status"] = "failed"
                target = (
                    directory / (args.split + "-replay.json")
                    if args.replay_only
                    else summary_path
                )
                target.write_text(json.dumps(result, indent=2) + "\n")
                raise
        row["status"] = "passed"
        if not args.replay_only:
            summary_path.write_text(json.dumps(result, indent=2) + "\n")
    result["status"] = "passed"
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    target = (
        directory / (args.split + "-replay.json") if args.replay_only else summary_path
    )
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "split": args.split,
                "cases": len(cases),
                "evidence": str(target.relative_to(ROOT)),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
