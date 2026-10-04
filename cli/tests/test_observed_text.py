"""Recorded text golden and synthetic controls; no fresh historical execution."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from entrotter_cli.main import main
from entrotter_sdk import Client, ObservedTraceResult
from test_position_text import seal
from test_require_complete import unmatched_baseline

DATA = Path(__file__).parent / "data"
SAMPLE = DATA / "observed-price32.json"


def prices(baseline, candidate):
    report = json.loads(SAMPLE.read_bytes())
    for row, price in zip(report["observations"], [baseline] * 3 + [candidate]):
        raw = row["raw"]
        raw["price"] = "0x" + price.to_bytes(32, "big").hex()
        words = bytearray.fromhex(raw["latest_round_data"][2:])
        words[32:64] = price.to_bytes(32, "big")
        raw["latest_round_data"] = "0x" + words.hex()
    report["classification"].update(
        baseline_price=baseline, candidate_price=candidate,
        price_difference=candidate-baseline,
    )
    ObservedTraceResult.parse(seal(report))
    return report


class ObservedTextTests(unittest.TestCase):
    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(list(args))
            except SystemExit as stopped:
                code = stopped.code
        return code, out.getvalue(), err.getvalue()

    def inspect(self, report):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.json"
            path.write_text(json.dumps(report))
            return self.invoke("observed-inspect", str(path), "--format", "text")

    def test_actual_whole_text_and_offline_guards(self):
        self.assertEqual(hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
                         "7010848300c353310fb78dab7f377daea4226633e49af3c1a384bcb3a579ba9d")
        with patch.dict(sys.modules, {"entrotter_engine": None}), patch.object(
            Client, "_request", side_effect=AssertionError("No HTTP")
        ), patch("socket.socket", side_effect=AssertionError("No network")), patch(
            "entrotter_cli.main.ExportBudget", side_effect=AssertionError("No export")
        ):
            code, out, err = self.invoke("observed-inspect", str(SAMPLE), "--format", "text")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, (DATA / "observed-price32.txt").read_text())

    def test_default_and_explicit_json_are_preserved(self):
        default = self.invoke("observed-inspect", str(SAMPLE))
        explicit = self.invoke("observed-inspect", str(SAMPLE), "--format", "json")
        self.assertEqual(default, explicit)
        self.assertEqual((default[0], default[2]), (0, ""))
        self.assertEqual(hashlib.sha256(default[1].encode()).hexdigest(),
                         "b4a6a14d3fb4acaae8eaf2fba783641e9094d85a2dbba5b293c3d912e381c532")

    def test_signed_zero_and_smallest_unit_differences(self):
        for baseline, candidate, delta in [
            (100000001, 100000002, "+0.00000001"),
            (100000002, 100000001, "-0.00000001"),
            (100000001, 100000001, "0"),
            (200000000, 100000000, "-1"),
        ]:
            with self.subTest(baseline=baseline, candidate=candidate):
                code, out, err = self.inspect(prices(baseline, candidate))
                self.assertEqual((code, err), (0, ""))
                self.assertIn("Candidate - baseline (USD): " + delta + "\n", out)
                self.assertIn("Price comparison: Complete recorded views", out)

    def test_six_original_synthetic_controls_remain_distinct(self):
        for control in json.loads((DATA / "observed-controls.json").read_bytes()):
            with self.subTest(name=control["name"]):
                report = json.loads(SAMPLE.read_bytes())
                report.update({k:v for k,v in control.items() if k != "name"})
                ObservedTraceResult.parse(report)
                code, out, err = self.inspect(report)
                self.assertEqual((code, err), (0, ""))
                if control["name"] == "large_integer":
                    self.assertIn("Baseline after (USD): 16069380442589902755419620923411626025222029937827928.35301366\n", out)
                    self.assertIn("Candidate after (USD): 16069380442589902755419620923411626025222029937827928.35301376\n", out)
                    self.assertIn("Candidate - baseline (USD): +0.0000001\n", out)
                else:
                    self.assertIn("Price comparison: UNPROVEN", out)
                    self.assertIn("Baseline after (USD): Unavailable\n", out)
                    self.assertIn("Candidate after (USD): Unavailable\n", out)
                    self.assertIn("Candidate - baseline (USD): Unavailable\n", out)
                    for reason in control["classification"]["unproven_reasons"]:
                        self.assertIn(reason, out)
                if control["name"] == "rpc_missing_head":
                    self.assertIn("head block Unavailable", out)
                    self.assertIn("View errors: head: timeout", out)

    def test_unsupported_currency_and_unit_are_not_presented_as_usd(self):
        for query, word in [("base_unit", 1000000), ("base_currency", 1)]:
            report = json.loads(SAMPLE.read_bytes())
            for row in report["observations"]:
                row["raw"][query] = "0x" + word.to_bytes(32, "big").hex()
            report["classification"].update(
                complete_price_views=False,
                unproven_reasons=["unsupported_currency_or_unit"],
                baseline_price=None, candidate_price=None, price_difference=None,
            )
            ObservedTraceResult.parse(seal(report))
            code, out, err = self.inspect(report)
            self.assertEqual((code, err), (0, ""))
            self.assertNotIn("2570.82415", out)
            self.assertIn("baseline before: Unavailable", out)
            self.assertIn("unsupported_currency_or_unit", out)

    def test_price_completeness_does_not_hide_unmatched_receipts(self):
        report = unmatched_baseline(json.loads(SAMPLE.read_bytes()))
        code, out, err = self.inspect(report)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Original receipts: UNPROVEN", out)
        self.assertIn("Price comparison: Complete recorded views", out)
        self.assertIn("Candidate - baseline (USD): +7.89973126", out)

    def test_invalid_input_prints_no_partial_text(self):
        invalid = json.loads(SAMPLE.read_bytes())
        invalid["classification"]["price_difference"] += 1
        for payload in [json.dumps(invalid), (DATA / "report.json").read_text(),
                        '{"artifact_id":1,"artifact_id":2}']:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "bad.json"
                path.write_text(payload)
                code, out, err = self.invoke("observed-inspect", str(path), "--format", "text")
            self.assertEqual((code, out), (1, ""))
            self.assertTrue(err.startswith("Error:"))
            self.assertNotIn("Traceback", err)

    def test_format_is_opt_in_only_for_inspection(self):
        for args in [
            ["observed-verify", str(SAMPLE), "--format", "text"],
            ["observed-inspect", str(SAMPLE), "--format", "html"],
            ["observed-inspect", str(SAMPLE), "--native"],
            ["observed-inspect", str(SAMPLE), "--require-complete"],
        ]:
            code, out, _ = self.invoke(*args)
            self.assertEqual((code, out), (2, ""))
