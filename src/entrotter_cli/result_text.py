"""Exact presentation of a sealed v0.1 result; no execution or valuation inference."""

from __future__ import annotations

import json
import re

MAX_UINT256 = 2**256 - 1


def _object(value: object, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Text inspection needs an object for {name}")
    return value


def _quoted(value: object) -> str:
    # JSON escapes terminal control characters and bidirectional Unicode metadata.
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True)


def _integer(value: object, *, signed: bool = False) -> int:
    pattern = r"(?:-?[1-9][0-9]{0,77}|0)" if signed else r"(?:[1-9][0-9]{0,77}|0)"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("Text inspection needs canonical integer strings")
    result = int(value)
    if abs(result) > MAX_UINT256:
        raise ValueError("Text inspection integer exceeds uint256 magnitude")
    return result


def _amount(value: int | None, decimals: int, *, signed: bool = False) -> str:
    if value is None:
        return "Unavailable"
    whole, fraction = divmod(abs(value), 10**decimals)
    tail = str(fraction).zfill(decimals).rstrip("0") if decimals else ""
    sign = "-" if value < 0 else "+" if signed and value > 0 else ""
    return sign + str(whole) + ("." + tail if tail else "")


def _table(rows: list[tuple[str, int | None, int | None]], decimals: int) -> list[str]:
    rendered = [("Value", "Baseline", "Candidate", "Candidate - baseline")]
    for label, baseline, candidate in rows:
        difference = (
            candidate - baseline
            if baseline is not None and candidate is not None
            else None
        )
        rendered.append(
            (
                label,
                _amount(baseline, decimals, signed=label == "Change"),
                _amount(candidate, decimals, signed=label == "Change"),
                _amount(difference, decimals, signed=True),
            )
        )
    widths = [max(len(row[index]) for row in rendered) for index in range(4)]
    return [
        "  ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ).rstrip()
        for row in rendered
    ]


def _metadata(value: object) -> tuple[str, str, int]:
    row = _object(value, "token metadata")
    address, symbol, decimals = (
        row.get("address"),
        row.get("symbol"),
        row.get("decimals"),
    )
    if not isinstance(address, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        raise ValueError("Invalid token address for text inspection")
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9_-]{1,12}", symbol):
        raise ValueError("Invalid token symbol for text inspection")
    if type(decimals) is not int or not 0 <= decimals <= 36:
        raise ValueError("Invalid token decimals for text inspection")
    return address.lower(), symbol, decimals


def _token_lines(report: dict, scenario: dict) -> list[str]:
    supplied = scenario.get("tracked_tokens", [])
    if not isinstance(supplied, list) or len(supplied) > 8:
        raise ValueError("Text inspection supports at most eight tracked tokens")
    metadata = [_metadata(value) for value in supplied]
    pinned = {token[0]: token for token in metadata}
    if len(pinned) != len(metadata):
        raise ValueError("Duplicate tracked token identity")
    states: dict[str, dict[str, tuple[int, int, int]]] = {}
    absent_branches = []
    for branch in ("baseline", "candidate"):
        values = _object(report.get(branch), branch).get("tokens")
        states[branch] = {}
        if values is None:
            absent_branches.append(branch)
            continue
        if not isinstance(values, list) or len(values) > 8:
            raise ValueError("Invalid token records for text inspection")
        for value in values:
            row = _object(value, "token record")
            identity = _metadata(row)
            address = identity[0]
            if address in states[branch]:
                raise ValueError("Duplicate branch token identity")
            if pinned.get(address) != identity:
                raise ValueError("Branch token identity or units differ from scenario")
            initial = _integer(row.get("initial_balance_raw"))
            final = _integer(row.get("final_balance_raw"))
            change = _integer(row.get("balance_delta_raw"), signed=True)
            if change != final - initial:
                raise ValueError("Token change differs from final minus initial")
            states[branch][address] = initial, final, change
    if not metadata:
        return [
            "",
            "ERC-20 state: Unavailable (missing branch records)"
            if absent_branches
            else "No ERC-20 tokens tracked",
        ]
    lines = []
    for address, symbol, decimals in metadata:
        lines.extend(["", f"{symbol} ({address}; {decimals} decimals)"])
        baseline, candidate = (
            states["baseline"].get(address),
            states["candidate"].get(address),
        )
        for branch in ("baseline", "candidate"):
            if address not in states[branch]:
                lines.append(f"Unavailable: missing {branch} record")
        rows = [
            (
                label,
                baseline[index] if baseline else None,
                candidate[index] if candidate else None,
            )
            for index, label in enumerate(("Initial", "Final", "Change"))
        ]
        lines.extend(_table(rows, decimals))
    return lines


def _native_lines(report: dict) -> list[str]:
    fields = (
        "initial_balance_wei",
        "final_balance_wei",
        "balance_delta_wei",
        "gas_cost_wei",
    )
    values: dict[str, list[int | None]] = {}
    metrics = {}
    for branch in ("baseline", "candidate"):
        row = _object(
            _object(report.get(branch), branch).get("metrics"), branch + " metrics"
        )
        metrics[branch] = row
        values[branch] = [
            _integer(row[key], signed=key == "balance_delta_wei")
            if key in row
            else None
            for key in fields
        ]
        initial, final, change = values[branch][:3]
        if (
            initial is not None
            and final is not None
            and change is not None
            and change != final - initial
        ):
            raise ValueError("Native change differs from final minus initial")
    comparison = _object(report.get("comparison"), "comparison")
    if "final_balance_delta_wei" in comparison:
        difference = _integer(comparison["final_balance_delta_wei"], signed=True)
        baseline, candidate = values["baseline"][1], values["candidate"][1]
        if (
            baseline is not None
            and candidate is not None
            and difference != candidate - baseline
        ):
            raise ValueError("Native comparison differs from candidate minus baseline")
    lines = ["", "Native balance (10^18 wei per native unit)"]
    lines.extend(
        _table(
            [
                (label, values["baseline"][index], values["candidate"][index])
                for index, label in enumerate(
                    ("Initial", "Final", "Change", "Gas cost")
                )
            ],
            18,
        )
    )
    rows = []
    for field, label in (
        ("gas_used", "Gas used"),
        ("reverted_transactions", "Reverted transactions"),
        ("rejected_transactions", "Rejected transactions"),
    ):
        counts: list[int | None] = []
        for branch in ("baseline", "candidate"):
            value = metrics[branch].get(field)
            if value is None:
                counts.append(None)
            elif field == "gas_used":
                counts.append(_integer(value))
            elif type(value) is int and 0 <= value <= MAX_UINT256:
                counts.append(value)
            else:
                raise ValueError("Invalid transaction count for text inspection")
        rows.append((label, counts[0], counts[1]))
    lines.extend(["", *_table(rows, 0)])
    return lines


def format_result(report: dict, agent: dict | None = None) -> str:
    """Validate displayed identities/units/accounting; hashes do not authenticate EVM."""
    scenario = _object(report.get("scenario"), "scenario")
    if not isinstance(scenario.get("id"), str):
        raise ValueError("Text inspection needs a scenario ID string")
    mode = report.get("mode")
    lines = [
        "Synthetic fixture result"
        if mode == "fixture"
        else f"Recorded EVM result ({mode})",
        "Scenario: " + _quoted(scenario["id"]),
        "Artifact: " + report["artifact_id"],
        "Content hash: verified; execution and provider authenticity unproven",
    ]
    if mode == "fixture":
        for name in ("baseline", "candidate"):
            metrics = _object(
                _object(report.get(name), name).get("metrics"), name + " metrics"
            )
            lines.extend(
                ["", name.capitalize() + " model metrics: " + _quoted(metrics)]
            )
        lines.append("Comparison: " + _quoted(report.get("comparison")))
    else:
        source = scenario.get("source")
        if source is not None:
            lines.append("Source pin (reported): " + _quoted(source))
        lines.extend(_native_lines(report))
        lines.extend(_token_lines(report, scenario))
        lines.extend(
            [
                "",
                "Balance differences do not measure profit; token roles and valuations are not inferred.",
            ]
        )
    if agent is not None:
        lines.extend(
            [
                "",
                "Recorded agent: " + _quoted(agent["provider"]),
                f"Initial requested gas budget: {agent['initial_requested_gas_budget']}",
            ]
        )
        for decision in agent["decisions"]:
            lines.append(
                f"Step {decision['step']}: {decision['choice']} | "
                + _quoted(decision["reason"])
            )
        lines.append(agent["scope"])
    assumptions = report.get("assumptions")
    if not isinstance(assumptions, list) or not all(
        isinstance(value, str) for value in assumptions
    ):
        raise ValueError("Text inspection needs recorded assumption strings")
    lines.extend(
        ["", "Recorded assumptions:", *("- " + _quoted(value) for value in assumptions)]
    )
    return "\n".join(lines)
