"""Presentation controls are synthetic mutations, not new EVM executions."""

from contextlib import redirect_stdout, redirect_stderr
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from entrotter_cli.main import main
from entrotter_sdk import Client, PositionResult

SAMPLE = Path(__file__).parent / "data/aave-account-position13.json"
FIELDS = (
    "total_collateral_base",
    "total_debt_base",
    "available_borrows_base",
    "liquidation_threshold_bps",
    "ltv_bps",
    "health_factor_wad",
)


def seal(row):
    body = {k: v for k, v in row.items() if k != "artifact_id"}
    row["artifact_id"] = hashlib.sha256(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    return row


def synthetic(baseline, candidate=None):
    row = json.loads(SAMPLE.read_bytes())
    candidate = baseline if candidate is None else candidate
    for view, values in zip(
        row["observations"], [baseline, baseline, baseline, candidate]
    ):
        view["raw"] = "0x" + "".join(
            values[k].to_bytes(32, "big").hex() for k in FIELDS
        )
    differences = {k: candidate[k] - baseline[k] for k in FIELDS}
    if baseline["total_debt_base"] == 0 or candidate["total_debt_base"] == 0:
        differences["health_factor_wad"] = None

    def status(v):
        return (
            "no_debt"
            if v["total_debt_base"] == 0
            else ("below_one" if v["health_factor_wad"] < 10**18 else "at_or_above_one")
        )

    row["classification"].update(
        baseline=copy.deepcopy(baseline),
        candidate=copy.deepcopy(candidate),
        differences=differences,
        baseline_health_status=status(baseline),
        candidate_health_status=status(candidate),
    )
    PositionResult.parse(seal(row))
    return row


class PositionTextTests(unittest.TestCase):
    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(args)
            except SystemExit as stopped:
                code = stopped.code
        return code, out.getvalue(), err.getvalue()

    def inspect(self, row):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.json"
            path.write_text(json.dumps(row))
            return self.invoke(["position-inspect", str(path), "--format", "text"])

    def test_original_exact_text_offline_and_no_side_effects(self):
        with (
            patch.dict(sys.modules, {"entrotter_engine": None}),
            patch.object(Client, "_request", side_effect=AssertionError("No HTTP")),
            patch("socket.socket", side_effect=AssertionError("No network")),
            patch(
                "entrotter_cli.main.ExportBudget",
                side_effect=AssertionError("No ledger"),
            ),
        ):
            code, out, err = self.invoke(
                ["position-inspect", str(SAMPLE), "--format", "text"]
            )
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out, (SAMPLE.parent / "aave-account-position13.txt").read_text()
        )

    def test_default_json_byte_compatibility_and_explicit_json(self):
        for command, expected in [
            (
                "position-inspect",
                "f56d2633a2f53dd95528d4ae8bb78814c400c2e366a3eee353efdc15ef8a073e",
            ),
            (
                "position-verify",
                "85121fd50da2ba2290a5c4bbb820efd02dcb3b6848f6718d90959878ecde552f",
            ),
        ]:
            code, out, err = self.invoke([command, str(SAMPLE)])
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(hashlib.sha256(out.encode()).hexdigest(), expected)
            if command == "position-inspect":
                self.assertEqual(
                    self.invoke([command, str(SAMPLE), "--format", "json"]),
                    (code, out, err),
                )

    def test_exact_negative_zero_and_basis_point_deltas(self):
        baseline = json.loads(SAMPLE.read_bytes())["classification"]["baseline"]
        candidate = {
            **baseline,
            "available_borrows_base": baseline["available_borrows_base"] - 1,
            "health_factor_wad": baseline["health_factor_wad"] - 1,
            "ltv_bps": baseline["ltv_bps"] + 1,
            "liquidation_threshold_bps": baseline["liquidation_threshold_bps"] - 1,
        }
        code, out, err = self.inspect(synthetic(baseline, candidate))
        self.assertEqual((code, err), (0, ""))
        for value in ["-0.00000001", "-0.000000000000000001", "+0.01 pp", "-0.01 pp"]:
            self.assertIn(value, out)
        collateral = next(
            line for line in out.splitlines() if line.startswith("Collateral")
        )
        self.assertEqual(collateral.split()[-1], "0")

    def test_uint256_precision_and_exact_health_boundary(self):
        values = json.loads(SAMPLE.read_bytes())["classification"]["baseline"]
        values.update(total_collateral_base=2**256 - 1, available_borrows_base=2**200)
        for health, expected, status in [
            (10**18 - 1, "0.999999999999999999", "Below 1"),
            (10**18, "1", "At or above 1"),
            (
                2**200,
                "1606938044258990275541962092341162602522202.993782792835301376",
                "At or above 1",
            ),
        ]:
            values["health_factor_wad"] = health
            code, out, err = self.inspect(synthetic(values))
            self.assertEqual((code, err), (0, ""))
            self.assertIn(
                "1157920892373161954235709850086879078532699846656405640394575840079131.29639935",
                out,
            )
            self.assertIn(
                "16069380442589902755419620923411626025222029937827928.35301376", out
            )
            self.assertIn(expected, out)
            self.assertIn("Baseline health: " + status, out)
            self.assertNotIn("e+", out)

    def test_no_debt_and_transition_keep_health_difference_undefined(self):
        debt = json.loads(SAMPLE.read_bytes())["classification"]["baseline"]
        no_debt = {**debt, "total_debt_base": 0, "health_factor_wad": 2**256 - 1}
        for baseline, candidate in [
            (no_debt, no_debt),
            (no_debt, debt),
            (debt, no_debt),
        ]:
            code, out, err = self.inspect(synthetic(baseline, candidate))
            self.assertEqual((code, err), (0, ""))
            health = next(
                line for line in out.splitlines() if line.startswith("Health factor ")
            )
            self.assertIn("No debt", health)
            self.assertIn("Not defined (no debt)", health)
            self.assertNotIn(str(2**256 - 1), out)
            self.assertIn("raw ABI words", out)

    def test_valid_unproven_report_keeps_reasons_and_unavailable(self):
        row = json.loads(SAMPLE.read_bytes())
        row["observations"][1].update(
            raw=None,
            errors=[
                {
                    "query": "account_data",
                    "category": "rpc_error",
                    "diagnostics": {"code": "timeout", "method": "eth_call"},
                }
            ],
        )
        row["classification"].update(
            complete_account_views=False,
            unproven_reasons=["incomplete_account_views"],
            baseline=None,
            candidate=None,
            differences={k: None for k in FIELDS},
            base_unit=None,
            baseline_health_status="unproven",
            candidate_health_status="unproven",
        )
        PositionResult.parse(seal(row))
        code, out, err = self.inspect(row)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Account comparison: UNPROVEN", out)
        self.assertIn("incomplete_account_views", out)
        for label in ["Collateral", "Debt", "Available borrowing", "Health factor"]:
            line = next(line for line in out.splitlines() if line.startswith(label))
            self.assertEqual(line.count("Unavailable"), 3)
        self.assertIn("Baseline health: Unproven", out)

    def test_invalid_and_resealed_report_print_no_success(self):
        row = json.loads(SAMPLE.read_bytes())
        row["classification"]["differences"]["available_borrows_base"] = 0
        for invalid in [row, seal(copy.deepcopy(row))]:
            code, out, err = self.inspect(invalid)
            self.assertEqual((code, out), (1, ""))
            self.assertNotIn("Traceback", err)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "duplicate.json"
            path.write_text('{"account":1,"account":2}')
            code, out, err = self.invoke(
                ["position-inspect", str(path), "--format", "text"]
            )
            self.assertEqual((code, out), (1, ""))

    def test_text_is_opt_in_only_for_inspection_commands(self):
        for args in [
            ["position-verify", str(SAMPLE), "--format", "text"],
            ["observed-inspect", str(SAMPLE), "--format", "html"],
            ["position-inspect", str(SAMPLE), "--format", "html"],
        ]:
            code, out, err = self.invoke(args)
            self.assertEqual((code, out), (2, ""))
