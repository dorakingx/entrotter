"""Real unittest output distinguishes a skipped-looking name from a skipped test."""

from io import StringIO
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verification_log import unittest_has_skips


class VerificationLogTests(unittest.TestCase):
    def test_actual_success_with_skipped_in_method_name_is_accepted(self):
        class Passing(unittest.TestCase):
            def test_no_empty_partial_skipped_security_success(self):
                pass

        stream = StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Passing)
        )
        self.assertTrue(result.wasSuccessful())
        self.assertIn("skipped", stream.getvalue())
        self.assertFalse(unittest_has_skips(stream.getvalue()))

    def test_actual_skip_is_rejected_in_verbose_and_summary_output(self):
        class Skipping(unittest.TestCase):
            @unittest.skip("Anvil unavailable")
            def test_real_evm(self):
                pass

        for verbosity in [1, 2]:
            stream = StringIO()
            result = unittest.TextTestRunner(stream=stream, verbosity=verbosity).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(Skipping)
            )
            self.assertEqual(len(result.skipped), 1)
            self.assertTrue(unittest_has_skips(stream.getvalue()))
