"""Versioned additive wire contract; runtime digest and semantic checks are separate."""

from copy import deepcopy
import unittest
from typing import Any
from contract_validation import validator as contract_validator
from jsonschema.exceptions import ValidationError


class RecordingSchemaTests(unittest.TestCase):
    def test_shape_rejects_executable_action_extensions(self):
        validator = contract_validator("agent-recording")
        recording: dict[str, Any] = {
            "agent_version": "0.1.0",
            "provider": {"provider": "schema-test"},
            "exchanges": [
                {
                    "request": {
                        "agent_version": "0.1.0",
                        "request_id": "a" * 64,
                        "observation": {
                            "step": 0,
                            "local_block_number": 0,
                            "native_balance_wei": "0",
                            "tokens": [],
                            "completed_actions": [],
                            "actor": "0x" + "0" * 40,
                            "local_chain_id": 31337,
                            "local_block_hash": "0x" + "b" * 64,
                            "timestamp": 1,
                        },
                        "proposed_action": {"to": "0x" + "1" * 40},
                        "preflight": {"status": "success", "return_data": "0x"},
                        "limits": {
                            "remaining_requested_gas": 21000,
                            "max_response_bytes": 4096,
                        },
                        "choices": {"execute": "execute", "hold": "hold"},
                    },
                    "response": {
                        "request_id": "a" * 64,
                        "choice": "hold",
                        "reason": "schema example",
                    },
                }
            ],
        }
        validator.validate(recording)
        result_validator = contract_validator("result")
        report = {
            "schema_version": "0.1.0",
            "artifact_id": "a" * 64,
            "mode": "evm-local",
            "scenario": {},
            "baseline": {"metrics": {}, "trace": []},
            "candidate": {"metrics": {}, "trace": []},
            "comparison": {},
            "assumptions": [],
            "agent": recording,
        }
        result_validator.validate(report)
        for change in [{"choice": "shell"}, {"command": "anything"}, {"reason": ""}]:
            bad = deepcopy(recording)
            bad["exchanges"][0]["response"].update(change)
            self.assertFalse(validator.is_valid(bad))
            with self.assertRaises(ValidationError):
                result_validator.validate({**report, "agent": bad})
        invalid_exchanges: list[list[Any]] = [[], recording["exchanges"] * 33]
        for exchanges in invalid_exchanges:
            bad = {**recording, "exchanges": exchanges}
            self.assertFalse(validator.is_valid(bad))
            with self.assertRaises(ValidationError):
                result_validator.validate({**report, "agent": bad})

    def test_existing_report_envelope_still_accepts_no_agent(self):
        contract_validator("result").validate(
            {
                "schema_version": "0.1.0",
                "artifact_id": "a" * 64,
                "mode": "fixture",
                "scenario": {},
                "baseline": {"metrics": {}, "trace": []},
                "candidate": {"metrics": {}, "trace": []},
                "comparison": {},
                "assumptions": [],
            }
        )


if __name__ == "__main__":
    unittest.main()
