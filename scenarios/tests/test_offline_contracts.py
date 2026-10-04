"""No network or arbitrary file retrieval during bundled schema resolution."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import shutil
import socket
import tempfile
import unittest
from unittest.mock import patch

from jsonschema.exceptions import SchemaError, ValidationError
from referencing.exceptions import Unresolvable

from contract_validation import KINDS, SCHEMAS, main, validator


class OfflineContractTests(unittest.TestCase):
    def test_command_validates_local_scenario(self):
        scenario = SCHEMAS.parent / "fixtures/liquidity-shock.json"
        output = StringIO()
        with (
            patch(
                "sys.argv", ["contract_validation", "--kind", "scenario", str(scenario)]
            ),
            redirect_stdout(output),
        ):
            main()
        self.assertIn("Valid scenario wire shape:", output.getvalue())

    def test_command_rejects_invalid_result_without_success_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text("{}")
            output = StringIO()
            with (
                patch(
                    "sys.argv", ["contract_validation", "--kind", "result", str(path)]
                ),
                redirect_stdout(output),
            ):
                with self.assertRaises(ValidationError):
                    main()
            self.assertEqual(output.getvalue(), "")

    def test_all_schema_meta_validation_with_network_disabled(self):
        with patch.object(
            socket, "socket", side_effect=AssertionError("Network forbidden")
        ):
            for kind in KINDS:
                with self.subTest(kind=kind):
                    validator(kind)

    def test_unknown_kind_fails(self):
        with self.assertRaises(ValueError):
            validator("../../private")

    def test_missing_schema_fails_even_without_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "schemas"
            shutil.copytree(SCHEMAS, root)
            (root / "agent-recording.v0.1.schema.json").unlink()
            with self.assertRaises(FileNotFoundError):
                validator("result", root)

    def test_invalid_schema_fails_at_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "schemas"
            shutil.copytree(SCHEMAS, root)
            path = root / "result.v0.1.schema.json"
            original = json.loads(path.read_text())
            original["type"] = "not-a-json-type"
            path.write_text(json.dumps(original))
            with self.assertRaises(SchemaError):
                validator("result", root)

    def test_unregistered_references_fail_without_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "schemas"
            shutil.copytree(SCHEMAS, root)
            path = root / "result.v0.1.schema.json"
            original = json.loads(path.read_text())
            sentinel = Path(tmp) / "external.schema.json"
            sentinel.write_text('{"type": "object"}')
            refs = ["missing.json", "https://example.invalid/schema", sentinel.as_uri()]
            for ref in refs:
                with self.subTest(ref=ref):
                    schema = deepcopy(original)
                    schema["properties"]["agent"]["$ref"] = ref
                    path.write_text(json.dumps(schema))
                    check = validator("result", root)
                    with (
                        patch.object(
                            socket,
                            "socket",
                            side_effect=AssertionError("Network forbidden"),
                        ) as network,
                        patch(
                            "builtins.open",
                            side_effect=AssertionError("File retrieval forbidden"),
                        ) as file_io,
                        patch.object(
                            Path,
                            "open",
                            side_effect=AssertionError("File retrieval forbidden"),
                        ) as path_io,
                        self.assertRaises(Unresolvable),
                    ):
                        check.validate(
                            {
                                "schema_version": "0.1.0",
                                "artifact_id": "a" * 64,
                                "mode": "evm-local",
                                "scenario": {},
                                "baseline": {"metrics": {}, "trace": []},
                                "candidate": {"metrics": {}, "trace": []},
                                "comparison": {},
                                "assumptions": [],
                                "agent": {},
                            }
                        )
                    network.assert_not_called()
                    file_io.assert_not_called()
                    path_io.assert_not_called()
