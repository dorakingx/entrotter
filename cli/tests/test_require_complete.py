"""Shell exit contracts; mutated records are synthetic, never fresh EVM evidence."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from entrotter_cli.main import main
from entrotter_sdk import Client, ObservedTraceResult, PositionResult
from test_position_text import FIELDS, seal, synthetic

DATA = Path(__file__).parent / "data"
POSITION = DATA / "aave-account-position13.json"
OBSERVED = DATA / "observed-price32.json"


def unproven_position(row, reasons):
    row["classification"].update(
        complete_account_views=False,
        unproven_reasons=sorted(reasons),
        baseline=None,
        candidate=None,
        differences={k: None for k in FIELDS},
        base_unit=None,
        baseline_health_status="unproven",
        candidate_health_status="unproven",
    )
    PositionResult.parse(seal(row))
    return row


def unmatched_baseline(row):
    """Change one reported receipt, retaining a consistent trace and price views."""
    trace = row["trace_report"]
    outcome = trace["baseline"]["outcomes"][-1]
    receipt = outcome["receipt"]
    receipt["effectiveGasPrice"] = hex(int(receipt["effectiveGasPrice"], 16) + 1)
    source = trace["source"]["inputs"][-1]["original_receipt"]
    outcome["differing_fields"] = sorted(k for k in receipt if receipt[k] != source[k])
    trace["baseline"]["matches_original_receipts"] = False
    trace["baseline_verified"] = False
    seal(trace)
    row["trace_artifact_id"] = trace["artifact_id"]
    row["classification"]["baseline_receipts_verified"] = False
    ObservedTraceResult.parse(seal(row))
    return row


class RequireCompleteTests(unittest.TestCase):
    def invoke(self, command, path, *flags):
        return subprocess.run(
            [sys.executable, "-m", "entrotter_cli", command, str(path), *flags],
            env=os.environ.copy(),
            capture_output=True,
            timeout=15,
        )

    def compare(self, command, row, code, reasons=()):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "record.json"
            path.write_text(json.dumps(row))
            default = self.invoke(command, path)
            required = self.invoke(command, path, "--require-complete")
        self.assertEqual((default.returncode, default.stderr), (0, b""))
        self.assertEqual(required.returncode, code, required.stderr)
        self.assertEqual(default.stdout, required.stdout)
        self.assertTrue(json.loads(required.stdout)["integrity_verified"])
        expected = (
            (
                "Incomplete recorded comparison: " + ", ".join(sorted(reasons)) + "\n"
            ).encode()
            if code
            else b""
        )
        self.assertEqual(required.stderr, expected)
        return json.loads(required.stdout)

    def test_original_default_bytes_and_success_exit_are_preserved(self):
        for command, path, digest in [
            (
                "position-verify",
                POSITION,
                "85121fd50da2ba2290a5c4bbb820efd02dcb3b6848f6718d90959878ecde552f",
            ),
            (
                "observed-verify",
                OBSERVED,
                "7be2cf3ff1da0820eea9d8e2f544df7f6bb54d398da23ac57939bcbbc1d46291",
            ),
        ]:
            with self.subTest(command=command):
                default = self.invoke(command, path)
                required = self.invoke(command, path, "--require-complete")
                self.assertEqual((required.returncode, required.stderr), (0, b""))
                self.assertEqual((default.returncode, default.stderr), (0, b""))
                self.assertEqual(default.stdout, required.stdout)
                self.assertEqual(hashlib.sha256(default.stdout).hexdigest(), digest)

    def test_all_existing_price_controls_change_only_exit_policy(self):
        for control in json.loads((DATA / "observed-controls.json").read_bytes()):
            with self.subTest(control=control["name"]):
                row = json.loads(OBSERVED.read_bytes())
                row.update({k: v for k, v in control.items() if k != "name"})
                summary = self.compare(
                    "observed-verify",
                    row,
                    0 if control["name"] == "large_integer" else 3,
                    row["classification"]["unproven_reasons"],
                )
                self.assertEqual(summary["classification"], row["classification"])

    def test_missing_account_and_nested_price_are_unproven(self):
        row = json.loads(POSITION.read_bytes())
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
        row = unproven_position(row, ["incomplete_account_views"])
        summary = self.compare("position-verify", row, 3, ["incomplete_account_views"])
        self.assertTrue(summary["prices"]["classification"]["complete_price_views"])
        self.assertIsNone(summary["classification"]["differences"]["health_factor_wad"])

        row = json.loads(POSITION.read_bytes())
        price = row["price_report"]
        price["observations"][1]["code"]["source_code"] = {
            "bytes": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
        }
        price["classification"].update(
            complete_price_views=False,
            unproven_reasons=["code_identity_changed", "code_unavailable"],
            baseline_price=None,
            candidate_price=None,
            price_difference=None,
        )
        ObservedTraceResult.parse(seal(price))
        row = unproven_position(row, ["price_views_unproven"])
        self.compare("position-verify", row, 3, ["price_views_unproven"])

    def test_baseline_receipts_gate_even_when_price_views_are_complete(self):
        price = unmatched_baseline(json.loads(OBSERVED.read_bytes()))
        self.assertTrue(price["classification"]["complete_price_views"])
        self.compare("observed-verify", price, 3, ["baseline_receipts_unverified"])
        row = json.loads(POSITION.read_bytes())
        unmatched_baseline(row["price_report"])
        row = unproven_position(row, ["baseline_receipts_unverified"])
        self.compare("position-verify", row, 3, ["baseline_receipts_unverified"])

    def test_complete_account_adverse_zero_and_no_debt_are_success(self):
        baseline = json.loads(POSITION.read_bytes())["classification"]["baseline"]
        no_debt = {**baseline, "total_debt_base": 0, "health_factor_wad": 2**256 - 1}
        cases = [
            (baseline, baseline),
            (
                baseline,
                {
                    **baseline,
                    "available_borrows_base": 0,
                    "health_factor_wad": 10**18 - 1,
                },
            ),
            (no_debt, no_debt),
            (no_debt, baseline),
            (baseline, no_debt),
        ]
        for a, b in cases:
            with self.subTest(b=b):
                self.compare("position-verify", synthetic(a, b), 0)

    def test_complete_price_zero_and_negative_differences_are_success(self):
        for difference in [0, -1]:
            row = json.loads(OBSERVED.read_bytes())
            value = row["classification"]["baseline_price"] + difference
            view = row["observations"][3]["raw"]
            view["price"] = "0x" + value.to_bytes(32, "big").hex()
            feed = bytes.fromhex(view["latest_round_data"][2:])
            view["latest_round_data"] = (
                "0x" + (feed[:32] + value.to_bytes(32, "big") + feed[64:]).hex()
            )
            row["classification"].update(
                candidate_price=value, price_difference=difference
            )
            ObservedTraceResult.parse(seal(row))
            self.compare("observed-verify", row, 0)

    def test_invalid_or_resealed_contradictory_reports_never_print_json(self):
        for command, source in [
            ("position-verify", POSITION),
            ("observed-verify", OBSERVED),
        ]:
            row = json.loads(source.read_bytes())
            row["classification"]["unproven_reasons"] = ["invented\nreason"]
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "invalid.json"
                for invalid in [row, seal(copy.deepcopy(row)), {"wrong_family": True}]:
                    path.write_text(json.dumps(invalid))
                    for flags in [(), ("--require-complete",)]:
                        result = self.invoke(command, path, *flags)
                        self.assertEqual((result.returncode, result.stdout), (1, b""))
                        self.assertNotIn(b"Traceback", result.stderr)
                path.write_text('{"profile":1,"profile":2}')
                result = self.invoke(command, path, "--require-complete")
                self.assertEqual((result.returncode, result.stdout), (1, b""))

    def test_inspection_and_execution_reject_the_option(self):
        for command in [
            "position-inspect",
            "observed-inspect",
            "verify",
            "trace-position",
            "trace-observe",
            "run",
            "replay",
        ]:
            result = self.invoke(command, POSITION, "--require-complete")
            self.assertEqual((result.returncode, result.stdout), (2, b""))
        result = self.invoke(
            "position-verify", POSITION, "--require-complete", "--format", "text"
        )
        self.assertEqual((result.returncode, result.stdout), (2, b""))

    def test_verification_stays_offline_without_engine_or_export_ledger(self):
        with (
            patch.dict(sys.modules, {"entrotter_engine": None}),
            patch.object(Client, "_request", side_effect=AssertionError("No HTTP")),
            patch("socket.socket", side_effect=AssertionError("No network")),
            patch(
                "entrotter_cli.main.ExportBudget",
                side_effect=AssertionError("No ledger"),
            ),
        ):
            for command, source in [
                ("position-verify", POSITION),
                ("observed-verify", OBSERVED),
            ]:
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    status = main([command, str(source), "--require-complete"])
                self.assertEqual((status, err.getvalue()), (0, ""))
                self.assertTrue(json.loads(out.getvalue())["integrity_verified"])


if __name__ == "__main__":
    unittest.main()
