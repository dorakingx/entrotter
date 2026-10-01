#!/usr/bin/env python3
"""Interleave three paired runs of the same frozen task; compare complete common outcomes."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import platform
import subprocess
import time

from entrotter_engine.agent import AgentController, RiskPolicy
from entrotter_engine.artifact import verify
from entrotter_engine.runner import run_agent
from direct_anvil_case import CASE_SHA256, load_case, run_direct

ROOT = Path(__file__).resolve().parents[1]


def project(report):
    if not verify(report):
        raise ValueError("Engine artifact integrity check failed")
    result = {"source": report["source"], "branches": []}
    for label, policy in [("baseline", "execute"), ("candidate", "preflight")]:
        branch = report[label]
        token_initial = {
            t["address"]: t["initial_balance_raw"] for t in branch["tokens"]
        }
        token_final = {t["address"]: t["final_balance_raw"] for t in branch["tokens"]}
        result["branches"].append(
            {
                "policy": policy,
                "initial": {
                    "native_wei": branch["metrics"]["initial_balance_wei"],
                    "tokens_raw": token_initial,
                },
                "steps": [
                    {
                        "status": step["status"],
                        "receipt": step.get("receipt"),
                        "balances": {
                            "native_wei": step["actor_balance_wei"],
                            "tokens_raw": step["token_balances_raw"],
                        },
                    }
                    for step in branch["trace"]
                ],
                "final": {
                    "native_wei": branch["metrics"]["final_balance_wei"],
                    "tokens_raw": token_final,
                },
                "gas_used": branch["metrics"]["gas_used"],
                "gas_cost_wei": branch["metrics"]["gas_cost_wei"],
            }
        )
    return result


def main():
    target = ROOT / "evidence/direct-anvil-comparison.json"
    if target.exists():
        raise ValueError("Do not overwrite previous benchmark evidence")
    scenario = load_case()
    engine_commit = subprocess.check_output(
        ["git", "-C", str(ROOT.parent / "engine"), "rev-parse", "HEAD"], text=True
    ).strip()
    if engine_commit != "bb8b3e8d32c7cbd49629d337758f30bfdf805045":
        raise ValueError(
            "Use the same frozen engine commit as the historical agent benchmark"
        )
    if subprocess.check_output(
        ["git", "-C", str(ROOT.parent / "engine"), "status", "--porcelain"], text=True
    ).strip():
        raise ValueError("Engine checkout must be clean")
    anvil_version = subprocess.check_output(["anvil", "--version"], text=True).strip()
    if "1.8.3" not in anvil_version:
        raise ValueError("This benchmark requires Foundry v1.8.3")
    reference = project(
        json.loads(
            (ROOT / "evidence/causal-v1/causal-uniswap-19000000-risk.json").read_text()
        )
    )
    result = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "source": scenario["source"],
        "scenario_sha256": CASE_SHA256,
        "engine_commit": engine_commit,
        "anvil_version": anvil_version,
        "python": platform.python_version(),
        "platform": platform.system(),
        "benchmark_code_sha256": {
            name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest()
            for name in ["direct_anvil_case.py", "benchmark_direct.py"]
        },
        "measurement": "Each timing includes two isolated forks, source verification, setup, execution, per-step observations and cleanup; excludes disk serialization",
        "run_order": [
            ["direct", "entrotter"],
            ["entrotter", "direct"],
            ["direct", "entrotter"],
        ],
        "runs": [],
        "limitations": [
            "Three repetitions on one known development case, no statistical speed claim",
            "Shared frozen transaction inputs and Anvil; direct path has no Entrotter runtime imports",
            "Entrotter also produces a typed decision recording and content-addressed report outside the common projection",
            "Setup/code authoring time is not measured; no claim of contributor productivity or independent user validation",
            "Network/archive caches and OS scheduling remain uncontrolled",
            "Child CPU and cumulative peak RSS are observations, not whole-process hard quotas",
        ],
    }
    target.write_text(json.dumps(result, indent=2) + "\n")
    for repetition, order in enumerate(result["run_order"], start=1):
        for method in order:
            print(f"repetition {repetition}: {method}", flush=True)
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            started = time.perf_counter()
            try:
                if method == "direct":
                    outcome = run_direct()
                else:
                    report = run_agent(
                        scenario,
                        AgentController(RiskPolicy(), [2], max_requested_gas=500000),
                    )
                    outcome = project(report)
                duration = time.perf_counter() - started
                if outcome != reference:
                    raise ValueError(
                        "Common outcomes differ from the pinned report; no performance conclusion allowed"
                    )
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                result["runs"].append(
                    {
                        "repetition": repetition,
                        "method": method,
                        "status": "passed",
                        "wall_seconds": duration,
                        "all_common_outcomes_equal": True,
                        "outcome_sha256": hashlib.sha256(
                            json.dumps(
                                outcome, sort_keys=True, separators=(",", ":")
                            ).encode()
                        ).hexdigest(),
                        "child_cpu_seconds": after.ru_utime
                        + after.ru_stime
                        - before.ru_utime
                        - before.ru_stime,
                        "child_peak_rss_so_far": after.ru_maxrss,
                        "child_peak_rss_unit": "bytes"
                        if platform.system() == "Darwin"
                        else "KiB",
                    }
                )
            except BaseException as exc:
                result["status"] = "failed"
                result["runs"].append(
                    {
                        "repetition": repetition,
                        "method": method,
                        "status": "failed",
                        "error_type": type(exc).__name__,
                    }
                )
                target.write_text(json.dumps(result, indent=2) + "\n")
                raise
            target.write_text(json.dumps(result, indent=2) + "\n")
    result["status"] = "passed"
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    result["common_outcome"] = reference
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "runs": len(result["runs"]),
                "evidence": str(target.relative_to(ROOT)),
            }
        )
    )


if __name__ == "__main__":
    main()
