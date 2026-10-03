"""Resealed false claims must not pass the example's offline scientific checks."""

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from entrotter_engine.agent import digest
from entrotter_engine.artifact import seal, verify

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "aave_example", ROOT / "scripts/aave_borrow.py"
)
EXAMPLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXAMPLE)


class AaveBorrowExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(
            (ROOT / "evidence/aave-borrow-actions/report.json").read_text()
        )
        cls.scenario = json.loads(EXAMPLE.SCENARIO.read_text())

    def test_recorded_real_result_is_checked_offline(self):
        result = EXAMPLE.check(self.report, self.scenario)
        self.assertEqual(result["borrowed_weth_raw_each"], "1000000000000000000")
        self.assertEqual(
            result["gas_used"], {"baseline": "723131", "candidate": "560326"}
        )

    def test_resealed_gas_tokens_and_submission_claims_fail(self):
        for field in [
            "gas",
            "funds",
            "debt",
            "hold_receipt",
            "rejected",
            "source",
            "native_step",
        ]:
            with self.subTest(field=field):
                r = deepcopy(self.report)
                if field == "gas":
                    r["baseline"]["metrics"]["gas_cost_wei"] = "0"
                elif field in {"funds", "debt"}:
                    address = self.scenario["tracked_tokens"][
                        0 if field == "funds" else 2
                    ]["address"]
                    r["candidate"]["trace"][-1]["token_balances_raw"][address] = (
                        "9000000000000000000"
                    )
                elif field == "hold_receipt":
                    r["candidate"]["trace"][3]["receipt"] = r["baseline"]["trace"][3][
                        "receipt"
                    ]
                elif field == "rejected":
                    r["baseline"]["trace"][3]["status"] = "rejected"
                elif field == "native_step":
                    r["baseline"]["trace"][3]["actor_balance_wei"] = "123"
                else:
                    r["source"]["block_hash"] = "0x" + "0" * 64
                r = seal(r)
                self.assertTrue(verify(r))
                with self.assertRaises(ValueError):
                    EXAMPLE.check(r, self.scenario)

    def test_resealed_borrow_event_amount_mode_and_beneficiary_fail(self):
        for field in ["amount", "mode", "beneficiary"]:
            with self.subTest(field=field):
                r = deepcopy(self.report)
                log = next(
                    x
                    for x in r["candidate"]["trace"][-1]["receipt"]["logs"]
                    if x["topics"][0] == EXAMPLE.BORROW_TOPIC
                )
                if field == "beneficiary":
                    log["topics"][2] = "0x" + "0" * 64
                else:
                    offset = 2 + (1 if field == "amount" else 2) * 64
                    log["data"] = (
                        log["data"][:offset] + "0" * 64 + log["data"][offset + 64 :]
                    )
                with self.assertRaises(ValueError):
                    EXAMPLE.check(seal(r), self.scenario)

    def test_rebound_future_observation_and_wrong_provider_fail(self):
        for field in ["future", "provider", "head"]:
            with self.subTest(field=field):
                r = deepcopy(self.report)
                if field == "provider":
                    r["agent"]["provider"]["cost_usd"] = "999"
                else:
                    exchange = r["agent"]["exchanges"][0]
                    request = exchange["request"]
                    if field == "head":
                        request["observation"]["local_block_hash"] = "0x" + "0" * 64
                    else:
                        request["observation"]["completed_actions"].append(
                            {"step": 4, "status": "success", "gas_used": "266917"}
                        )
                    request["request_id"] = digest(
                        {k: v for k, v in request.items() if k != "request_id"}
                    )
                    exchange["response"]["request_id"] = request["request_id"]
                    r["candidate"]["trace"][3]["agent_decision"] = deepcopy(
                        exchange["response"]
                    )
                with self.assertRaises(ValueError):
                    EXAMPLE.check(seal(r), self.scenario)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX input admission")
    def test_input_admission_rejects_fifo_symlink_size_and_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            with self.assertRaises(ValueError):
                EXAMPLE.read_json(fifo, 16)
            data = root / "data.json"
            data.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):
                EXAMPLE.read_json(data, 16)
            data.write_bytes(b" " * 17)
            with self.assertRaises(ValueError):
                EXAMPLE.read_json(data, 16)
            data.write_text('{"a":1}')
            self.assertEqual(EXAMPLE.read_json(data, 16), {"a": 1})
            link = root / "link"
            link.symlink_to(data)
            with self.assertRaises(OSError):
                EXAMPLE.read_json(link, 16)
