#!/usr/bin/env python3
"""Run the pinned Uniswap acceptance case twice; require actual fork receipts."""

import json
from pathlib import Path
import platform
import resource
import time

from entrotter_engine.artifact import verify
from entrotter_engine.runner import run

ROOT = Path(__file__).resolve().parents[1]
scenario_path = ROOT.parent / "scenarios/evm/ethereum-uniswap-slippage.json"
scenario = json.loads(scenario_path.read_text())
evidence = ROOT / "evidence"
evidence.mkdir(exist_ok=True)
reports, durations = [], []
for attempt in range(2):
    start = time.perf_counter()
    report = run(scenario)
    durations.append(time.perf_counter() - start)
    if not verify(report):
        raise AssertionError()
    if not report["source"]["block_hash"] == scenario["source"]["block_hash"]:
        raise AssertionError()
    baseline, candidate = report["baseline"], report["candidate"]
    if not [step["status"] for step in baseline["trace"]] == ["success"] * 3:
        raise AssertionError()
    if not [step["status"] for step in candidate["trace"]] == [
        "success",
        "success",
        "reverted",
    ]:
        raise AssertionError()
    if not baseline["start_block"] == candidate["start_block"] == 19000000:
        raise AssertionError()
    if not baseline["start_timestamp"] == candidate["start_timestamp"]:
        raise AssertionError()
    for b, c in zip(baseline["tokens"], candidate["tokens"]):
        if not b["initial_balance_raw"] == c["initial_balance_raw"] == "0":
            raise AssertionError()
    if not baseline["tokens"][0]["final_balance_raw"] == "0":
        raise AssertionError()
    if not candidate["tokens"][0]["final_balance_raw"] == str(10**18):
        raise AssertionError()
    if not int(baseline["tokens"][1]["final_balance_raw"]) > 0:
        raise AssertionError()
    if not candidate["tokens"][1]["final_balance_raw"] == "0":
        raise AssertionError()
    for branch in [baseline, candidate]:
        cost = sum(
            int(s["receipt"]["gasUsed"], 16)
            * int(s["receipt"]["effectiveGasPrice"], 16)
            for s in branch["trace"]
        )
        if not cost == int(branch["metrics"]["gas_cost_wei"]):
            raise AssertionError()
        if not int(branch["metrics"]["balance_delta_wei"]) == -(10**18) - cost:
            raise AssertionError()
    reports.append(report)
if not reports[0] == reports[1]:
    raise AssertionError("Repeated fixed-source execution diverged")
(evidence / "historical-uniswap.json").write_text(
    json.dumps(reports[0], indent=2) + "\n"
)
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
result = {
    "status": "passed",
    "mode": "archived-state supplied-action execution",
    "scenario": str(scenario_path.relative_to(ROOT.parent)),
    "source": reports[0]["source"],
    "artifact_id": reports[0]["artifact_id"],
    "runs": 2,
    "identical_artifacts": True,
    "wall_seconds_per_run": durations,
    "anvil_version": reports[0]["baseline"]["tool_version"],
    "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
    "child_maxrss": usage.ru_maxrss,
    "child_maxrss_unit": "bytes" if platform.system() == "Darwin" else "KiB",
    "resource_scope": "children of this checker, peak RSS not aggregate; no CPU or RSS hard cap",
    "limitations": [
        "One sourced scenario; not three scenarios or untouched holdouts",
        "Manually specified actions; no integrated agent or historical trace replay",
        "No portfolio valuation; symbols are labels; unlisted assets are omitted",
    ],
}
(evidence / "historical-verification.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps(result, indent=2))
