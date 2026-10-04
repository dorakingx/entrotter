"""Exact text presentation of validated fixed-profile recorded price views."""

from __future__ import annotations

from textwrap import fill
from typing import TYPE_CHECKING

from .position_text import _scaled

if TYPE_CHECKING:
    from entrotter_sdk import ObservedTraceResult


def format_observed(observed: ObservedTraceResult) -> str:
    """Recorded view completeness and original receipt matching remain separate."""
    classification, trace = observed.classification, observed.trace
    plan = trace.report["plan"]
    source = plan["source"]
    lines = [
        "Aave V3 Ethereum WETH price (recorded comparison)",
        f"Price artifact: {observed.artifact_id}",
        f"Trace artifact: {trace.artifact_id}",
        "Internal integrity: verified (not provider or execution authentication)",
        f"Source: chain {source['chain_id']}, block {source['block_number']}",
        f"Block hash: {source['block_hash']}",
        f"Prefix: {len(trace.transactions)} original transactions; "
        f"candidate omits indices {plan['skip_indices']}",
        "Original receipts: " + ("verified" if trace.baseline_verified else "UNPROVEN"),
        "Price comparison: "
        + (
            "Complete recorded views"
            if classification.complete_price_views
            else "UNPROVEN"
        ),
    ]
    if classification.unproven_reasons:
        lines.append("Price reasons: " + ", ".join(classification.unproven_reasons))
    lines.extend(
        [
            "",
            "Baseline after (USD): " + _scaled(classification.baseline_price, 10**8),
            "Candidate after (USD): " + _scaled(classification.candidate_price, 10**8),
            "Candidate - baseline (USD): "
            + _scaled(classification.price_difference, 10**8, signed=True),
            "",
            "Recorded view prices (USD; a quoted value alone does not prove completeness):",
        ]
    )
    for row in observed.observations:
        unit = (
            10**8
            if row.base_unit == 10**8 and row.base_currency == "0x" + "00" * 20
            else None
        )
        head = str(row.head.number) if row.head is not None else "Unavailable"
        lines.append(
            f"{row.branch} {row.phase}: {_scaled(row.price, unit)}; head block {head}"
        )
        if row.errors:
            lines.append(
                "  View errors: "
                + ", ".join(f"{e.query}: {e.code or e.category}" for e in row.errors)
            )
    lines.extend(
        [
            "",
            "USD uses the fixed profile's 100000000 base unit; values are not rounded.",
            "Unproven comparison values remain unavailable, even if some views have prices.",
            "Use --format json for full signed feed rounds, head/code identities and errors.",
            "",
            fill(
                "Scope: " + observed.report["scope"],
                width=88,
                break_long_words=False,
                break_on_hyphens=False,
            ),
        ]
    )
    return "\n".join(lines)
