"""Plain text presentation of an already validated fixed-profile SDK result."""

from __future__ import annotations

from textwrap import fill
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entrotter_sdk import PositionResult


def _scaled(value: int | None, unit: int | None, signed: bool = False) -> str:
    """Fixed SDK units are powers of ten; integer arithmetic preserves every digit."""
    if value is None or unit is None:
        return "Unavailable"
    whole, remainder = divmod(abs(value), unit)
    fraction = str(remainder).zfill(len(str(unit)) - 1).rstrip("0")
    magnitude = str(whole) + ("." + fraction if fraction else "")
    sign = "-" if value < 0 else "+" if signed and value > 0 else ""
    return sign + magnitude


def format_position(position: PositionResult) -> str:
    """Internal consistency is separate from completeness and external authenticity."""
    classification = position.classification
    prices, trace = position.prices, position.trace
    plan = position.plan["trace"]
    source = plan["source"]
    lines = [
        "Aave V3 Ethereum account impact (recorded comparison)",
        f"Account: {position.account}",
        f"Position artifact: {position.artifact_id}",
        f"Price artifact: {prices.artifact_id}",
        f"Trace artifact: {trace.artifact_id}",
        "Internal integrity: verified (not provider or execution authentication)",
        f"Source: chain {source['chain_id']}, block {source['block_number']}",
        f"Block hash: {source['block_hash']}",
        f"Prefix: {len(trace.transactions)} original transactions; "
        f"candidate omits indices {plan['skip_indices']}",
        "Original receipts: " + ("verified" if trace.baseline_verified else "UNPROVEN"),
        "Account comparison: "
        + (
            "Complete recorded views"
            if classification.complete_account_views
            else "UNPROVEN"
        ),
    ]
    if classification.unproven_reasons:
        lines.append("Account reasons: " + ", ".join(classification.unproven_reasons))
    lines.append(
        "Price views: "
        + (
            "Complete recorded views"
            if prices.classification.complete_price_views
            else "UNPROVEN"
        )
    )
    if prices.classification.unproven_reasons:
        lines.append(
            "Price reasons: " + ", ".join(prices.classification.unproven_reasons)
        )
    rows = [("After-prefix values", "Baseline", "Candidate", "Candidate - baseline")]
    for field, label, unit in (
        ("total_collateral_base", "Collateral (USD)", classification.base_unit),
        ("total_debt_base", "Debt (USD)", classification.base_unit),
        (
            "available_borrows_base",
            "Available borrowing (USD)",
            classification.base_unit,
        ),
        ("liquidation_threshold_bps", "Liquidation threshold (%)", 100),
        ("ltv_bps", "LTV (%)", 100),
        ("health_factor_wad", "Health factor", classification.health_factor_unit),
    ):
        values = []
        for branch in (classification.baseline, classification.candidate):
            if (
                field == "health_factor_wad"
                and branch is not None
                and branch.total_debt_base == 0
            ):
                values.append("No debt")
            else:
                values.append(
                    _scaled(
                        getattr(branch, field) if branch is not None else None, unit
                    )
                )
        difference = getattr(classification.differences, field)
        delta = _scaled(difference, unit, signed=True)
        if field.endswith("_bps") and difference is not None:
            delta += " pp"
        if (
            field == "health_factor_wad"
            and difference is None
            and (
                classification.baseline_health_status == "no_debt"
                or classification.candidate_health_status == "no_debt"
            )
        ):
            delta = "Not defined (no debt)"
        rows.append((label, values[0], values[1], delta))
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    lines.append("")
    lines.extend(
        "  ".join(value.ljust(widths[i]) for i, value in enumerate(row)).rstrip()
        for row in rows
    )
    statuses = {
        "no_debt": "No debt",
        "below_one": "Below 1",
        "at_or_above_one": "At or above 1",
        "unproven": "Unproven",
    }
    lines.extend(
        [
            "",
            "Baseline health: " + statuses[classification.baseline_health_status],
            "Candidate health: " + statuses[classification.candidate_health_status],
            "USD denotes the fixed profile's base currency; pp denotes percentage points.",
            "No-debt health has no finite normalized delta. The input report retains raw ABI words.",
            "Use --format json for the full classifications and recorded observation details.",
            "",
            fill(
                "Scope: " + position.report["scope"],
                width=88,
                break_long_words=False,
                break_on_hyphens=False,
            ),
        ]
    )
    return "\n".join(lines)
