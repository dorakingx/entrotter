"""Limit-policy tests; real systemd enforcement is recorded separately."""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "host_envelope",
    Path(__file__).resolve().parents[1] / "scripts/check_host_envelope.py",
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class HostEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.values = {
            "cpu.max": "100000 100000",
            "memory.max": "268435456",
            "memory.swap.max": "0",
            "pids.max": "64",
        }

    def test_documented_limits_and_stricter_limits_pass(self):
        self.assertEqual(checker.validate_limits(self.values)["tasks"], 64)
        self.values.update(
            {"cpu.max": "50000 100000", "memory.max": "67108864", "pids.max": "16"}
        )
        self.assertEqual(checker.validate_limits(self.values)["memory_bytes"], 67108864)

    def test_missing_unlimited_malformed_or_excessive_limits_fail(self):
        for field, invalid in {
            "cpu.max": [
                "max 100000",
                "200000 100000",
                "0 100000",
                "100000 0",
                "1",
                "1 2 3",
            ],
            "memory.max": ["max", "268435457", "0", "-1"],
            "memory.swap.max": ["max", "1", "-1"],
            "pids.max": ["max", "65", "0", "-1"],
        }.items():
            for value in invalid:
                with (
                    self.subTest(field=field, value=value),
                    self.assertRaises(ValueError),
                ):
                    checker.validate_limits(dict(self.values, **{field: value}))
            missing = self.values.copy()
            del missing[field]
            with self.subTest(missing=field), self.assertRaises(KeyError):
                checker.validate_limits(missing)


if __name__ == "__main__":
    unittest.main()
