#!/usr/bin/env python3
"""Local real-EVM comparison; model generation is explicitly opt-in, replay is offline."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import resource
import time

from entrotter_engine.agent import (
    AgentController,
    ReplayPolicy,
    RiskPolicy,
    DecisionProvider,
)
from entrotter_engine.artifact import verify, write_report
from entrotter_engine.runner import run, run_agent

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate-model",
        action="store_true",
        help="Use authenticated Codex CLI; consumes account usage",
    )
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--replay",
        type=Path,
        help="Replay a saved full report without model generation",
    )
    args = parser.parse_args()
    if args.generate_model and args.replay:
        parser.error("Choose model generation or offline replay")
    if args.replay:
        report = json.loads(args.replay.read_text())
        if not verify(report):
            raise ValueError("Input report content hash is invalid")
        steps = [
            x["request"]["observation"]["step"] for x in report["agent"]["exchanges"]
        ]
        replayed = run_agent(
            report["scenario"], AgentController(ReplayPolicy(report["agent"]), steps)
        )
        if replayed != report:
            raise ValueError("Complete replay artifact differs")
        print(
            json.dumps({"replay_exact": True, "artifact_id": replayed["artifact_id"]})
        )
        return
    scenario = json.loads(
        (ROOT.parent / "scenarios/evm/local-branch-revert.json").read_text()
    )
    scenario["steps"] = [
        {"baseline": deepcopy(s["candidate"]), "candidate": s["candidate"]}
        for s in scenario["steps"]
    ]
    steps = [0, 1]
    providers: list[tuple[str, DecisionProvider]] = [("risk", RiskPolicy())]
    if args.generate_model:
        from codex_policy import CodexPolicy

        providers.append(("codex", CodexPolicy(model=args.model)))
    results = []
    started = time.perf_counter()
    baseline = run(scenario)
    results.append(
        {
            "policy": "non-agent",
            "runtime_seconds": time.perf_counter() - started,
            "metrics": baseline["candidate"]["metrics"],
            "artifact_id": baseline["artifact_id"],
        }
    )
    write_report(baseline, ROOT / "evidence/agent-local-prescribed.json")
    for name, provider in providers:
        started = time.perf_counter()
        report = run_agent(scenario, AgentController(provider, steps))
        elapsed = time.perf_counter() - started
        replay_start = time.perf_counter()
        replayed = run_agent(
            scenario, AgentController(ReplayPolicy(report["agent"]), steps)
        )
        if (
            replayed != report
            or not verify(report)
            or report["baseline"] != baseline["baseline"]
        ):
            raise ValueError("Agent comparison or exact replay failed")
        replay_elapsed = time.perf_counter() - replay_start
        write_report(report, ROOT / f"evidence/agent-local-{name}.json")
        results.append(
            {
                "policy": name,
                "runtime_seconds": elapsed,
                "replay_seconds": replay_elapsed,
                "replay_exact": True,
                "metrics": report["candidate"]["metrics"],
                "choices": [
                    x["response"]["choice"] for x in report["agent"]["exchanges"]
                ],
                "artifact_id": report["artifact_id"],
            }
        )
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "scope": "One artificial local-EVM transfer/revert case, not historical market evaluation",
        "model_generation": args.generate_model,
        "results": results,
        "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "child_maxrss": usage.ru_maxrss,
        "child_maxrss_unit": "bytes" if platform.system() == "Darwin" else "KiB",
        "resource_scope": "All checker children, peak RSS not aggregate; no hard CPU/RSS cap",
        "limitations": [
            "Same execute-if-preflight-succeeds objective for risk policy and model; not proof of LLM advantage",
            "No prices or valuation, so profit and drawdown are not defined",
            "Historical cases and untouched holdouts still pending",
            "CLI reports requested model alias and token usage, not immutable served model or monetary cost",
        ],
    }
    target = (
        "agent-model-verification.json"
        if args.generate_model
        else "agent-risk-verification.json"
    )
    (ROOT / "evidence" / target).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
