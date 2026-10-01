"""Negative gates for source, dependency and diagnostic coverage."""

from copy import deepcopy
import json
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
check_dependencies = importlib.import_module("check_dependencies")
check_security = importlib.import_module("check_security")
check_types = importlib.import_module("check_types")
production_files = importlib.import_module("quality_scope").production_files


class QualityPolicyTests(unittest.TestCase):
    def test_type_gate_rejects_new_missing_or_crashed_diagnostics(self):
        policy = json.loads((ROOT / "quality-inputs.json").read_text())[
            "frozen_type_findings"
        ]
        report = (
            "\n".join(x["diagnostic"] for x in policy)
            + "\nFound 3 errors in 1 file (checked 7 source files)\n"
        )
        self.assertEqual(check_types.evaluate(report, 1, policy), 3)
        for output, code in [
            (report + "new.py:1: error: new problem\n", 1),
            (report.replace(policy[0]["diagnostic"], ""), 1),
            (report, 2),
            ("", 0),
        ]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                check_types.evaluate(output, code, policy)
        self.assertEqual(
            check_types.evaluate(
                "Success: no issues found in 10 source files\n", 0, []
            ),
            0,
        )

    def test_dependency_gate_rejects_missing_unpinned_or_unhashed_tools(self):
        source = "tool==1.0\n"
        lock = "tool==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"
        self.assertEqual(check_dependencies.evaluate(source, lock), {"tool": "1.0"})
        cases = [
            ("", lock),
            (source, ""),
            (source, "tool==2.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"),
            (source, "tool==1.0\n"),
            (source, lock + "--extra-index-url https://example.invalid\n"),
            ("tool>=1.0\n", lock),
        ]
        for declared, locked in cases:
            with (
                self.subTest(declared=declared, locked=locked),
                self.assertRaises(ValueError),
            ):
                check_dependencies.evaluate(declared, locked)

    def test_security_gate_retains_findings_and_rejects_drift_or_skips(self):
        finding = {
            "filename": "scripts/example.py",
            "test_id": "B404",
            "line_number": 1,
            "code": "1 import subprocess\n",
        }
        report = {
            "errors": [],
            "metrics": {"_totals": {"loc": 1, "skipped_tests": 0}},
            "results": [finding],
        }
        policy = {
            "findings": [
                {
                    **check_security.fingerprint(finding),
                    "reason": "A trusted subprocess import; execution is reviewed at each actual call site.",
                }
            ]
        }
        self.assertEqual(check_security.evaluate(report, policy), 1)
        for changed in [
            dict(report, results=[]),
            dict(report, errors=["scanner failed"]),
            dict(report, metrics={"_totals": {"loc": 1, "skipped_tests": 1}}),
        ]:
            with self.assertRaises(ValueError):
                check_security.evaluate(changed, policy)
        changed = deepcopy(report)
        changed["results"][0]["code"] = "1 changed source\n"
        with self.assertRaises(ValueError):
            check_security.evaluate(changed, policy)

    def test_scope_includes_new_scripts_and_hidden_production_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in [
                "scripts/new.py",
                ".github/actions/new/check.py",
                ".github/actions/new/test_check.py",
                "evidence/archived.py",
            ]:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("")
            self.assertEqual(
                production_files(root),
                [".github/actions/new/check.py", "scripts/new.py"],
            )

    def test_frozen_provider_keeps_its_historical_hash(self):
        import hashlib

        policy = json.loads((ROOT / "quality-inputs.json").read_text())
        manifest = json.loads(
            (ROOT.parent / "scenarios/benchmarks/causal-v1/manifest.json").read_text()
        )
        actual = hashlib.sha256(
            (ROOT / "scripts/codex_policy.py").read_bytes()
        ).hexdigest()
        self.assertEqual(actual, policy["frozen_sources"]["scripts/codex_policy.py"])
        self.assertEqual(actual, manifest["policy"]["codex_adapter_sha256"])


if __name__ == "__main__":
    unittest.main()
