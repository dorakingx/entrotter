"""Offline additive trace contracts; shape checks never establish execution truth."""

from copy import deepcopy
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from contract_validation import validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def example_plan():
    return json.loads((ROOT / "traces/ethereum-mainnet-prefix.plan.json").read_text())


def example_result():
    return json.loads(
        (ROOT / "tests/data/trace-mainnet-prefix.result.json").read_text()
    )


class TraceContractTests(unittest.TestCase):
    def test_original_plan_and_receipt_result_validate_offline(self):
        with patch.object(socket, "socket", side_effect=AssertionError("No network")):
            validator("trace-plan").validate(example_plan())
            validator("trace-result").validate(example_result())

    def test_separate_family_preserves_v01_contract_boundaries(self):
        self.assertFalse(validator("scenario").is_valid(example_plan()))
        self.assertFalse(validator("result").is_valid(example_result()))
        old = {
            "schema_version": "0.1.0",
            "artifact_id": "a" * 64,
            "mode": "fixture",
            "scenario": {},
            "baseline": {"metrics": {}, "trace": []},
            "candidate": {"metrics": {}, "trace": []},
            "comparison": {},
            "assumptions": [],
        }
        validator("result").validate(old)
        self.assertFalse(validator("trace-result").is_valid(old))

    def test_plan_rejects_unknown_versions_sources_and_executable_fields(self):
        for modify in [
            lambda p: p.update(trace_version="2"),
            lambda p: p.update(command="unsafe"),
            lambda p: p["source"].update(chain_id=31337),
            lambda p: p["source"].update(chain_id=True),
            lambda p: p["source"].update(block_hash="latest"),
            lambda p: p["source"].update(rpc_url="unsafe"),
            lambda p: p.update(through_index=32),
            lambda p: p.update(through_index=True),
            lambda p: p.update(skip_indices=[0, 0]),
            lambda p: p.update(skip_indices=[32]),
        ]:
            p = example_plan()
            modify(p)
            with self.subTest(plan=p), self.assertRaises(ValidationError):
                validator("trace-plan").validate(p)

    def test_sorted_and_prefix_dependent_skip_rules_remain_engine_semantics(self):
        p = example_plan()
        p.update(through_index=0, skip_indices=[1, 0])
        # Unique/in-range indices are shape-valid; sortedness and <=through_index are runtime rules.
        validator("trace-plan").validate(p)

    def test_terminal_outcomes_require_their_status_specific_fields(self):
        check = validator("trace-result")
        for status in ["skipped", "rejected", "not_mined", "nonce_conflict"]:
            r = example_result()
            outcome = {
                "index": 0,
                "hash": r["source"]["inputs"][0]["hash"],
                "status": status,
            }
            if status == "nonce_conflict":
                outcome.update(expected_nonce=0, original_nonce=1)
            r["candidate"] = {
                "anvil_version": "schema-only example",
                "outcomes": [outcome],
                "matches_original_receipts": False,
            }
            check.validate(r)
            outcome["receipt"] = deepcopy(r["baseline"]["outcomes"][0]["receipt"])
            self.assertFalse(check.is_valid(r))
        for modify in [
            lambda o: o.update(status="queued"),
            lambda o: o.pop("receipt"),
            lambda o: o.pop("differing_fields"),
            lambda o: o.update(command="unsafe"),
        ]:
            r = example_result()
            modify(r["baseline"]["outcomes"][0])
            self.assertFalse(check.is_valid(r))

    def test_verified_flags_cannot_contradict_branch_outcome_shape(self):
        for modify in [
            lambda r: r.update(baseline_verified=False),
            lambda r: r["baseline"].update(matches_original_receipts=1),
            lambda r: r["baseline"]["outcomes"][0].update(differing_fields=["gasUsed"]),
            lambda r: r["candidate"].update(matches_original_receipts=True),
        ]:
            r = example_result()
            modify(r)
            self.assertFalse(validator("trace-result").is_valid(r))

    def test_projected_receipts_reject_malformed_quantities_addresses_and_logs(self):
        for modify in [
            lambda r: r.update(status="0x2"),
            lambda r: r.update(gasUsed="0x00"),
            lambda r: r.update(type="0x3"),
            lambda r: r.update(transactionHash="0x00"),
            lambda r: r.update(logsBloom="0x"),
            lambda r: r["logs"][0].update(topics=["0x00"]),
            lambda r: r["logs"][0].update(removed=True),
        ]:
            report = example_result()
            modify(report["baseline"]["outcomes"][0]["receipt"])
            self.assertFalse(validator("trace-result").is_valid(report))

    def test_schema_does_not_recompute_receipt_equivalence_or_hashes(self):
        r = example_result()
        r["baseline"]["outcomes"][0]["receipt"]["gasUsed"] = "0x1"
        # Both values and flags still have valid shape: equality and content hashes need the engine.
        validator("trace-result").validate(r)

    def test_source_header_prefix_and_assumption_bounds(self):
        for modify in [
            lambda r: r["source"]["header"].update(timestamp=1710338135),
            lambda r: r["source"]["header"].update(gas_limit=30000001),
            lambda r: r["source"].update(inputs=[]),
            lambda r: r["source"].update(inputs=r["source"]["inputs"] * 33),
            lambda r: r.update(runtime_seconds=-1),
            lambda r: r.update(assumptions=[]),
            lambda r: r.update(schema_version="0.1.0"),
        ]:
            r = example_result()
            modify(r)
            self.assertFalse(validator("trace-result").is_valid(r))


if __name__ == "__main__":
    unittest.main()
