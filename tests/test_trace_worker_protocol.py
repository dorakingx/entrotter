"""Trace host/JSON/CLI fault probes; mocks do not establish kernel isolation."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from entrotter_engine.artifact import canonical, seal
from entrotter_engine.evm import ExecutionError
from entrotter_engine.trace import load_trace, run_trace, verify_trace, write_trace
from entrotter_engine.worker_protocol import encode_trace_request, execute_request
from test_trace import plan


def report():
    # Explicit protocol mock, never asserted as an actual transaction execution.
    return seal({'trace_version':'0.1.0', 'execution_kind':'canonical_transaction_prefix_replay',
                 'plan':plan(), 'source':{}, 'baseline':{'matches_original_receipts':False},
                 'candidate':{'matches_original_receipts':False}, 'baseline_verified':False,
                 'runtime_seconds':0, 'assumptions':['Mock host-binding fixture; no execution.']})


class TraceWorkerProtocolTests(unittest.TestCase):
    def test_exact_envelope_and_full_input_hash(self):
        raw=encode_trace_request(plan())
        with patch('entrotter_engine.trace.run_trace_native', return_value={'sentinel':1}) as native:
            value=execute_request(raw)
        self.assertEqual(value, {'worker_version':'1', 'request_id':sha256(raw).hexdigest(), 'report':{'sentinel':1}})
        self.assertEqual(native.call_args.args[0], plan())

    def test_invalid_envelopes_cannot_launch_nodes(self):
        envelope=json.loads(encode_trace_request(plan()))
        values=[{**envelope,'command':'unsafe'}, {**envelope,'worker_version':'2'},
                {**envelope,'scenario':{}}, {**envelope,'trace':{}},
                {**envelope,'trace':{**plan(),'skip_indices':[32]}}]
        with patch('entrotter_engine.trace.run_trace_native') as native:
            for value in values:
                with self.subTest(value=value), self.assertRaises(ValueError): execute_request(canonical(value))
            with self.assertRaises(ValueError): execute_request(canonical(envelope)+b' '*262144)
            native.assert_not_called()

    def test_foreign_or_corrupt_artifact_refused(self):
        r=report(); self.assertTrue(verify_trace(r))
        self.assertFalse(verify_trace({**r,'artifact_id':'0'*64}))
        self.assertFalse(verify_trace(seal({**r,'schema_version':'0.1.0'})))
        self.assertFalse(verify_trace(seal({**r,'trace_version':'2'})))
        self.assertFalse(verify_trace(seal({**r,'baseline_verified':True})))
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'preserved.json'; output.write_text('incumbent')
            with self.assertRaises(ValueError): write_trace({**r,'artifact_id':'0'*64},output)
            self.assertEqual(output.read_text(), 'incumbent')

    def test_input_file_size_type_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'plan.json'; p.write_bytes(canonical(plan()))
            self.assertEqual(load_trace(p), plan())
            p.write_bytes(b' '*(262144+1))
            with self.assertRaises(ValueError): load_trace(p)
            fifo=Path(directory)/'fifo'; os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError,'regular file'): load_trace(fifo)

    def test_cli_bounded_default_and_explicit_native(self):
        from entrotter_engine.__main__ import main
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'plan.json'; p.write_bytes(canonical(plan()))
            for flags, expected in [([], 'bounded'), (['--native'],'native')]:
                with patch('entrotter_engine.trace.run_trace', return_value=report()) as bounded, \
                     patch('entrotter_engine.trace.run_trace_native', return_value=report()) as native, \
                     patch('entrotter_engine.trace.write_trace') as write:
                    self.assertEqual(main(['trace-run',str(p),'-o','unused',*flags]),0)
                    self.assertEqual(bounded.call_count, int(expected=='bounded'))
                    self.assertEqual(native.call_count, int(expected=='native'))
                    write.assert_called_once()


class TraceHostProtocolTests(unittest.TestCase):
    import test_isolated as harness
    setUp=harness.IsolatedProtocolTests.setUp
    assert_cleanup=harness.IsolatedProtocolTests.assert_cleanup

    def envelope(self):
        raw=encode_trace_request(plan())
        return {'worker_version':'1','request_id':sha256(raw).hexdigest(),'report':report()}

    def invoke(self, response):
        with patch.dict(os.environ, {'FAKE_RESPONSE':json.dumps(response)}):
            return run_trace(plan())

    def test_valid_response_binding_and_cleanup(self):
        envelope=self.envelope()
        self.assertEqual(self.invoke(envelope),envelope['report'])
        self.assert_cleanup()

    def test_wrong_extra_corrupt_and_resealed_foreign_plan(self):
        good=self.envelope(); changed=deepcopy(good['report'])
        changed['plan']['skip_indices']=[1]
        variants=[good['report'], [], {**good,'worker_version':'2'}, {**good,'request_id':'0'*64},
                  {**good,'extra':True}, {**good,'report':seal(changed)},
                  {**good,'report':{**good['report'],'artifact_id':'0'*64}}]
        for value in variants:
            with self.subTest(value=str(value)[:40]), self.assertRaises(ExecutionError): self.invoke(value)
            self.assert_cleanup()

    def test_timeout_and_output_limit_clean_owned_worker(self):
        with patch.dict(os.environ, {'FAKE_HANG':'1'}), patch('entrotter_engine.isolated.HOST_TIMEOUT',.15):
            with self.assertRaisesRegex(ExecutionError,'timed out'): self.invoke(self.envelope())
        self.assert_cleanup()
        with patch('entrotter_engine.isolated.MAX_OUTPUT',16):
            with self.assertRaisesRegex(ExecutionError,'8 MiB'): self.invoke(self.envelope())
        self.assert_cleanup()

