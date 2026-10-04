"""Frozen evaluation provenance and input integrity; no archive access or holdout execution."""

import hashlib
import json
from pathlib import Path
import unittest
from entrotter_engine.models import validate
from contract_validation import validator

ROOT = Path(__file__).resolve().parents[1] / "benchmarks/causal-v1"


class FrozenCaseTests(unittest.TestCase):
    def test_frozen_inputs_and_split_are_unchanged(self):
        data = (ROOT / "manifest.json").read_bytes()
        self.assertEqual(
            hashlib.sha256(data).hexdigest(),
            "f147489fcde8de04be6a9de459fe011018488bd75e66a84de55f6a8a35ed030e",
        )
        manifest = json.loads(data)
        self.assertEqual(len(manifest["cases"]), 5)
        self.assertEqual(
            [
                x["source"]["block_number"]
                for x in manifest["cases"]
                if x["split"] == "holdout"
            ],
            [20000000, 21000000],
        )
        self.assertEqual(
            [
                x["source"]["block_number"]
                for x in manifest["cases"]
                if x["split"] == "development"
            ],
            [19000000],
        )
        schema = validator("scenario")
        for case in manifest["cases"]:
            path = ROOT / case["path"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), case["sha256"]
            )
            raw = json.loads(path.read_text())
            schema.validate(raw)
            scenario = validate(raw)
            self.assertEqual(
                scenario["source"]["block_hash"], case["source"]["block_hash"]
            )
            self.assertEqual(case["decision_steps"], [2])
            self.assertEqual(len(scenario["steps"]), 3)
            for slot in scenario["steps"]:
                self.assertEqual(slot["baseline"], slot["candidate"])
            encoded = scenario["steps"][2]["candidate"]["data"][10:]
            words = [encoded[i : i + 64] for i in range(0, len(encoded), 64)]
            self.assertEqual(int(words[4], 16), case["source"]["timestamp"] + 3600)
            self.assertEqual(str(int(words[6], 16)), case["minimum_out_raw"])


if __name__ == "__main__":
    unittest.main()
