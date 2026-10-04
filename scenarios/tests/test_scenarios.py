import json
from pathlib import Path
import unittest
from entrotter_engine.models import validate
from contract_validation import validator

ROOT = Path(__file__).resolve().parents[1]


class ScenarioTests(unittest.TestCase):
    def test_manifest_paths(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        names = []
        for key in [
            "fixtures",
            "evm_local",
            "historical_templates",
            "historical_scenarios",
        ]:
            for name in manifest[key]:
                path = ROOT / name
                self.assertTrue(path.is_file())
                self.assertTrue(path.resolve().is_relative_to(ROOT))
                names.append(name)
        self.assertEqual(len(names), len(set(names)))
        discovered = {
            p.relative_to(ROOT).as_posix()
            for directory in ("fixtures", "evm")
            for p in (ROOT / directory).glob("*.json")
        }
        self.assertEqual(set(names), discovered)

    def test_all_runtime_validate(self):
        for p in list((ROOT / "fixtures").glob("*.json")) + list(
            (ROOT / "evm").glob("*.json")
        ):
            with self.subTest(path=p.name):
                validate(json.loads(p.read_text()))

    def test_no_real_claims_in_synthetic(self):
        for p in (ROOT / "fixtures").glob("*.json"):
            data = json.loads(p.read_text())
            self.assertEqual(data["provenance"]["kind"], "synthetic")

    def test_json_schema(self):
        scenario_validator = validator("scenario")
        for p in list((ROOT / "fixtures").glob("*.json")) + list(
            (ROOT / "evm").glob("*.json")
        ):
            with self.subTest(path=p.name):
                scenario_validator.validate(json.loads(p.read_text()))


if __name__ == "__main__":
    unittest.main()
