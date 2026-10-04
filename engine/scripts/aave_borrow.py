"""Compare supplied Aave actions, or inspect their saved result without RPC calls.

Execution uses the default bounded worker and the operator's archive endpoint.
This is local impersonated action execution, not original signed transaction replay.
"""

import argparse
import json
import os
from pathlib import Path
import stat

from entrotter_engine.agent import MAX_RECORDING_BYTES, ReplayPolicy
from entrotter_engine.artifact import MAX_REPORT_BYTES, verify, write_report
from entrotter_engine.runner import load, run_agent

SCENARIO = Path(__file__).resolve().parents[1] / "tests/data/aave-borrow-actions.json"
BORROW_TOPIC = "0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON field")
        result[key] = value
    return result


def read_json(path, limit):
    # Nonblocking open precedes descriptor inspection; a FIFO cannot wait for a writer.
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW), "rb"
    ) as source:
        require(
            stat.S_ISREG(os.fstat(source.fileno()).st_mode),
            "Input must be a regular file",
        )
        raw = source.read(limit + 1)
    require(len(raw) <= limit, "Input exceeds its byte limit")
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(isinstance(value, dict), "Input must be a JSON object")
    return value


def check(report, scenario):
    """Check this example's receipts, units and causal decision, not provider truth."""
    require(verify(report), "Result content hash is invalid")
    require(report["scenario"] == scenario, "Result is for a different scenario")
    require(
        report["mode"] == "evm-fork" and report["local_chain_id"] == 31337,
        "Wrong execution profile",
    )
    require(
        all(
            report["source"][key] == value for key, value in scenario["source"].items()
        ),
        "Wrong archive source pin",
    )
    actor = scenario["actor"]
    pool = scenario["steps"][2]["baseline"]["to"]
    weth, aweth, vweth = [t["address"] for t in scenario["tracked_tokens"]]
    statuses = {
        "baseline": ["success", "success", "success", "reverted", "success"],
        "candidate": ["success", "success", "success", "noop", "success"],
    }
    for name, expected in statuses.items():
        branch = report[name]
        trace = branch["trace"]
        require(
            branch["start_block"] == scenario["source"]["block_number"]
            and branch["start_timestamp"] == report["source"]["timestamp"],
            "Wrong branch start",
        )
        require(
            [x["status"] for x in trace] == expected,
            "Unexpected outcome sequence: " + name,
        )
        tokens = branch["tokens"]
        require(
            [{k: t[k] for k in ["address", "symbol", "decimals"]} for t in tokens]
            == scenario["tracked_tokens"],
            "Wrong tracked assets",
        )
        require(
            all(t["initial_balance_raw"] == "0" for t in tokens),
            "Initial token balance differs",
        )
        require(
            branch["metrics"]["initial_balance_wei"] == scenario["actor_balance_wei"],
            "Native balance override differs",
        )
        gas = cost = 0
        previous_native = int(scenario["actor_balance_wei"])
        previous = {t["address"]: "0" for t in tokens}
        for i, outcome in enumerate(trace):
            held = name == "candidate" and i == 3
            action = None if held else scenario["steps"][i][name]
            require(
                outcome["step"] == i and outcome["action"] == action,
                "Executed action differs",
            )
            balances = outcome["token_balances_raw"]
            require(set(balances) == set(previous), "Missing tracked balance")
            require(
                outcome["token_deltas_raw"]
                == {a: str(int(v) - int(previous[a])) for a, v in balances.items()},
                "Per-step token delta differs",
            )
            previous = balances
            if held:
                require(
                    "receipt" not in outcome
                    and "transaction_hash" not in outcome
                    and outcome["gas_used"] == "0",
                    "Hold submitted a transaction",
                )
                require(
                    int(outcome["actor_balance_wei"]) == previous_native,
                    "Hold changed the native balance",
                )
                continue
            if action is None:
                raise ValueError("Executed slot is missing its action")
            receipt = outcome["receipt"]
            require(
                receipt["from"] == actor
                and receipt["to"] == action["to"]
                and receipt["transactionHash"] == outcome["transaction_hash"],
                "Receipt transaction differs",
            )
            require(
                int(receipt["status"], 16) == (0 if i == 3 else 1),
                "Receipt status differs",
            )
            require(
                int(receipt["blockNumber"], 16) == branch["start_block"] + i + 1,
                "Wrong receipt slot",
            )
            used = int(receipt["gasUsed"], 16)
            paid = used * int(receipt["effectiveGasPrice"], 16)
            require(0 < used <= action["gas"], "Receipt exceeds requested gas")
            require(
                str(used) == outcome["gas_used"]
                and str(paid) == outcome["gas_cost_wei"],
                "Gas receipt/metric differs",
            )
            gas += used
            cost += paid
            transferred = (
                int(action.get("value_wei", "0"))
                if outcome["status"] == "success"
                else 0
            )
            previous_native -= paid + transferred
            require(
                int(outcome["actor_balance_wei"]) == previous_native,
                "Per-step native accounting differs",
            )
        metrics = branch["metrics"]
        require(
            metrics["gas_used"] == str(gas) and metrics["gas_cost_wei"] == str(cost),
            "Aggregated gas differs",
        )
        require(
            metrics["reverted_transactions"] == (1 if name == "baseline" else 0)
            and metrics["rejected_transactions"] == 0,
            "Revert and submission rejection were confused",
        )
        require(
            metrics["final_balance_wei"] == trace[-1]["actor_balance_wei"]
            and int(metrics["balance_delta_wei"])
            == int(metrics["final_balance_wei"]) - int(metrics["initial_balance_wei"]),
            "Native balance metrics differ",
        )
        require(
            int(metrics["balance_delta_wei"]) == -(10**19) - cost,
            "Native funds do not account for wrapping and gas",
        )
        require(
            trace[0]["token_balances_raw"][weth] == str(10**19),
            "Wrapping did not create 10 WETH",
        )
        require(
            trace[2]["token_balances_raw"]
            == {weth: "0", aweth: str(10**19), vweth: "0"},
            "Supply did not create 10 aWETH",
        )
        require(
            trace[3]["token_balances_raw"][weth] == "0"
            and trace[3]["token_balances_raw"][vweth] == "0",
            "Refused proposal created funds or debt",
        )
        require(
            previous[weth] == previous[vweth] == str(10**18)
            and int(previous[aweth]) >= 10**19,
            "Final underlying/debt/supply units differ",
        )
        require(
            all(
                t["final_balance_raw"] == previous[t["address"]]
                and t["balance_delta_raw"] == previous[t["address"]]
                for t in tokens
            ),
            "Final token summary differs",
        )
        events = [
            log
            for log in trace[4]["receipt"]["logs"]
            if log["address"] == pool and log["topics"][0] == BORROW_TOPIC
        ]
        require(len(events) == 1, "Missing unique Pool Borrow event")
        event = events[0]
        require(
            event["topics"]
            == [
                BORROW_TOPIC,
                "0x" + weth[2:].rjust(64, "0"),
                "0x" + actor[2:].rjust(64, "0"),
                "0x" + "0" * 64,
            ],
            "Borrow reserve/beneficiary/referral differs",
        )
        words = [
            event["data"][2:][i : i + 64] for i in range(0, len(event["data"]) - 2, 64)
        ]
        require(
            len(words) == 4
            and words[0] == actor[2:].rjust(64, "0")
            and int(words[1], 16) == 10**18
            and int(words[2], 16) == 2,
            "Borrow caller/amount/variable mode differs",
        )
    require(
        report["baseline"]["trace"][:3] == report["candidate"]["trace"][:3],
        "Shared setup execution differs",
    )
    require(
        report["baseline"]["tokens"] == report["candidate"]["tokens"],
        "Final tracked token results differ",
    )
    recording = report["agent"]
    ReplayPolicy(recording)
    require(
        recording["provider"]
        == {
            "provider": "builtin",
            "model": "preflight-risk-v1",
            "deterministic": True,
            "seed": None,
            "cost_usd": "0",
        },
        "Unexpected decision provider",
    )
    require(len(recording["exchanges"]) == 1, "Unexpected number of decisions")
    exchange = recording["exchanges"][0]
    request, response = exchange["request"], exchange["response"]
    observation = request["observation"]
    candidate = report["candidate"]
    require(
        response["choice"] == "hold"
        and candidate["trace"][3]["agent_decision"] == response,
        "Decision binding differs",
    )
    require(
        request["preflight"] == {"status": "rejected", "return_data": None}
        and request["proposed_action"] == scenario["steps"][3]["candidate"],
        "Preflight/proposal differs",
    )
    require(
        observation["step"] == 3
        and observation["local_chain_id"] == 31337
        and observation["actor"] == actor
        and observation["local_block_number"] == candidate["start_block"] + 3
        and observation["timestamp"] == candidate["start_timestamp"] + 36,
        "Observation is for another decision slot",
    )
    require(
        observation["local_block_hash"]
        == candidate["trace"][2]["receipt"]["blockHash"],
        "Observation head differs from the completed supply block",
    )
    require(
        observation["completed_actions"]
        == [
            {k: x[k] for k in ["step", "status", "gas_used"]}
            for x in candidate["trace"][:3]
        ],
        "Completed actions include wrong or future steps",
    )
    require(
        observation["tokens"]
        == [
            {
                **t,
                "balance_raw": candidate["trace"][2]["token_balances_raw"][
                    t["address"]
                ],
            }
            for t in scenario["tracked_tokens"]
        ]
        and observation["native_balance_wei"]
        == candidate["trace"][2]["actor_balance_wei"],
        "Observation balances differ",
    )
    difference = int(candidate["metrics"]["final_balance_wei"]) - int(
        report["baseline"]["metrics"]["final_balance_wei"]
    )
    require(
        report["comparison"]["final_balance_delta_wei"] == str(difference),
        "Native comparison differs",
    )
    return {
        "artifact_id": report["artifact_id"],
        "statuses": statuses,
        "borrowed_weth_raw_each": str(10**18),
        "variable_debt_raw_each": str(10**18),
        "gas_used": {name: report[name]["metrics"]["gas_used"] for name in statuses},
        "native_balance_difference_wei": str(difference),
        "valuation": "exact local units; not profit or a forecast",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", type=Path, help="Inspect a saved result without execution or RPC"
    )
    parser.add_argument("--output", type=Path, default=Path("aave-borrow-report.json"))
    parser.add_argument(
        "--recording", type=Path, help="Replay exactly the saved agent recording"
    )
    args = parser.parse_args()
    scenario = load(SCENARIO)
    if args.check:
        require(args.recording is None, "--check does not accept --recording")
        report = read_json(args.check, MAX_REPORT_BYTES)
    else:
        recording = (
            read_json(args.recording, MAX_RECORDING_BYTES) if args.recording else None
        )
        report = run_agent(scenario, decision_steps=[3], recording=recording)
        write_report(
            report, args.output
        )  # Preserve complete returned data before checks.
    print(json.dumps(check(report, scenario), indent=2))


if __name__ == "__main__":
    main()
