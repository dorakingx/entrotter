"""Offline evidence-loss/error-privacy regressions. No services, RPC or native replay."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import contextlib
import io
import time
import unittest
from unittest.mock import patch
from entrotter_engine.artifact import canonical
from entrotter_engine.evm import ExecutionError
from entrotter_engine.rpc import RPCError, FAILURE_CODES
from evidence import Evidence, error_code
from native_runner import category


class HostileError(Exception):
    def __str__(self):
        raise AssertionError('private formatter invoked')

    def __repr__(self):
        raise AssertionError('private formatter invoked')


class EvidenceTest(unittest.TestCase):
    def recorder(self, output):
        return Evidence(output, 'ab' * 32, [], category)

    def test_baseline_survives_candidate_failure_with_exact_source_request_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            recorder = self.recorder(p)
            captured = {'inputs': [], 'parent': {'chain_id': 1, 'block_number': 1}, 'header': {}}
            returned = recorder.capture(lambda *args: captured, None, type('RPC', (), {'call': lambda *args: None})(), 1)
            self.assertIs(returned, captured)
            baseline = {'outcomes': [{'index': 0, 'status': 'executed', 'receipt': {'gasUsed': '0x1'}}], 'matches_original_receipts': True}
            self.assertIs(recorder.replay(lambda *args: baseline, captured, None, [], 1), baseline)
            original_error = ExecutionError('Canonical trace execution budget exceeded')
            def fail(*args):
                raise original_error
            with self.assertRaises(ExecutionError) as caught:
                recorder.replay(fail, captured, None, [12], 1)
            self.assertIs(caught.exception, original_error)
            source = json.loads((p / 'captured-source.json').read_text())
            frozen_baseline = json.loads((p / 'baseline-branch.json').read_text())
            self.assertEqual(source['source'], captured)
            self.assertEqual(frozen_baseline['result'], baseline)
            self.assertEqual(frozen_baseline['source_sha256'], sha256(canonical(captured)).hexdigest())
            self.assertEqual(frozen_baseline['request_id'], 'ab' * 32)
            self.assertFalse((p / 'candidate-branch.json').exists())
            self.assertEqual(recorder.failures[-1]['stage'], 'candidate_replay')
            self.assertEqual(recorder.failures[-1]['code'], 'trace_budget_exceeded')

    def test_entrypoint_failure_finalizes_complete_observations_without_replay_services(self):
        import native_runner as module
        source = {'inputs': [{'index': x['index'], 'hash': x['hash'], 'sender': x['recovered_signer'],
                              'raw': x['raw_signed_transaction']} for x in json.loads((module.HERE / 'signed-prefix.json').read_text())]}
        baseline = {'outcomes': [], 'matches_original_receipts': False}
        class RPC:
            timeout = 10
            def call(self, method, *args):
                if method == 'eth_getBlockByNumber':
                    return {'number': '0x1', 'hash': '0x' + 'ab' * 32, 'timestamp': '0x1'}
                if args[0][0]['data'] == module.GETTERS['aggregator']:
                    return '0x' + '00' * 12 + module.AGGREGATOR[2:]
                return '0x' + '00' * 160
        class Session:
            def __init__(self):
                self.rpc, self.process = RPC(), None
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                pass
        def replay(captured, url, skipped, deadline):
            with module.trace.AnvilSession():
                if skipped:
                    raise ExecutionError('Canonical trace execution budget exceeded')
                return baseline
        def execute(raw):
            deadline = time.monotonic() + 150
            captured = module.trace.capture_source(None, RPC(), deadline)
            module.trace.replay_branch(captured, None, [], deadline)
            module.trace.replay_branch(captured, None, [12], deadline)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(module, 'OUTPUT', output), patch.object(module.trace, 'AnvilSession', Session), \
                 patch.object(module.trace, 'capture_source', lambda *args: source), \
                 patch.object(module.trace, 'replay_branch', replay), patch.object(module, 'execute_request', execute), \
                 contextlib.redirect_stdout(io.StringIO()):
                module.main()
            result = json.loads((output / 'result.json').read_text())
            observations = json.loads((output / 'observations.json').read_text())
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['primary_code'], 'trace_budget_exceeded')
            self.assertEqual(result['primary_stage'], 'candidate_replay')
            self.assertEqual(observations, result['observations'])
            self.assertEqual(len(observations), 4)
            self.assertEqual(observations[-1]['errors'][0]['category'], 'skipped_primary_failure')
            self.assertEqual(json.loads((output / 'baseline-branch.json').read_text())['result'], baseline)
            self.assertFalse((output / 'report.json').exists())

    def test_snapshot_io_fault_keeps_original_return_then_primary_error_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = self.recorder(Path(directory))
            baseline = {'outcomes': [], 'matches_original_receipts': False}
            with patch('evidence.atomic', side_effect=OSError('private /Users/example?secret=1')):
                self.assertIs(recorder.replay(lambda *args: baseline, {}, None, [], 1), baseline)
            error = ExecutionError('private https://provider.example/credential')
            def fail(*args):
                raise error
            with self.assertRaises(ExecutionError) as caught:
                recorder.replay(fail, {}, None, [12], 1)
            self.assertIs(caught.exception, error)
            self.assertEqual(recorder.secondary[0]['code'], 'snapshot_failed')
            serialized = json.dumps([recorder.secondary, recorder.failures])
            self.assertNotIn('private', serialized)
            self.assertNotIn('credential', serialized)

    def test_exact_static_error_only_without_stringifying_arbitrary_exception(self):
        self.assertEqual(error_code(ExecutionError('Canonical trace execution budget exceeded')), 'trace_budget_exceeded')
        self.assertEqual(error_code(ExecutionError('Canonical trace execution budget exceeded?secret=1')), 'execution_error_other')
        self.assertEqual(error_code(HostileError('private')), 'other_error')
        self.assertEqual(error_code(ExecutionError(['private'])), 'other_error')

    def test_failed_rpc_method_is_finite_and_exception_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = self.recorder(Path(directory))
            error = HostileError('private URL')
            class RPC:
                def call(self, *args, **kwargs):
                    raise error
            rpc = RPC()
            _, observed = recorder.rpc_wrapper(rpc, 'candidate_replay')
            with self.assertRaises(HostileError) as caught:
                observed('evm_mine')
            self.assertIs(caught.exception, error)
            self.assertEqual(recorder.failures[-1]['method'], 'evm_mine')
            with self.assertRaises(HostileError):
                observed('private-method-URL')
            self.assertEqual(recorder.failures[-1]['method'], 'other')
            recorder.observing = True
            count = len(recorder.failures)
            with self.assertRaises(HostileError):
                observed('eth_call')
            self.assertEqual(len(recorder.failures), count)
            self.assertNotIn('private', json.dumps(recorder.failures))

class SafeRPCMetadataTests(unittest.TestCase):
    def test_recorded_codes_ignore_hostile_properties_and_match_real_observed_method(self):
        class Forged(RPCError):
            @property
            def diagnostics(self):
                raise AssertionError('private diagnostics property invoked')
            @property
            def code(self):
                raise AssertionError('private code property invoked')
            def __str__(self):
                raise AssertionError('private exception formatted')
            def __repr__(self):
                raise AssertionError('private exception represented')
        with tempfile.TemporaryDirectory() as directory:
            recorder = Evidence(Path(directory), 'ab' * 32, [], category)
            for code in FAILURE_CODES:
                error = Forged('PRIVATE_ERROR https://provider.invalid?key=PRIVATE', code=code, method='evm_mine')
                class RPC:
                    def call(self, *args, **kwargs):
                        raise error
                _, observed = recorder.rpc_wrapper(RPC(), 'candidate_replay')
                recorder.failures.clear()
                with self.assertRaises(RPCError) as caught:
                    observed('evm_mine')
                self.assertIs(caught.exception, error)
                row = recorder.failures[0]
                self.assertEqual(row['rpc_diagnostics'], {'code': code, 'method': 'evm_mine'})
                self.assertTrue(row['rpc_method_matches_observed'])
                self.assertNotIn('PRIVATE', json.dumps(row))
            recorder.failures.clear()
            recorder.failure(Forged('PRIVATE', code={'private': 'PRIVATE_CODE'}, method=['PRIVATE_METHOD']), 'candidate_replay', 'evm_mine')
            self.assertEqual(recorder.failures[0]['rpc_diagnostics'], {'code': 'unknown', 'method': None})
            self.assertFalse(recorder.failures[0]['rpc_method_matches_observed'])
            self.assertNotIn('PRIVATE', json.dumps(recorder.failures))

    def test_outer_native_suffix_accepts_only_finite_exact_generated_values(self):
        stem = 'Canonical trace RPC failed; original inputs/state may be unavailable. No fixture substitution.'
        for code in FAILURE_CODES:
            self.assertEqual(error_code(ExecutionError(stem + f' [rpc_code={code}; rpc_method=evm_mine]')), 'trace_rpc_failed')
        self.assertEqual(error_code(ExecutionError(stem + ' [rpc_code=PRIVATE_CODE; rpc_method=evm_mine]')), 'execution_error_other')
        self.assertEqual(error_code(ExecutionError(stem + ' [rpc_code=timeout; rpc_method=PRIVATE_METHOD]')), 'execution_error_other')

    def test_snapshot_failure_keeps_new_metadata_and_exact_primary_error_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = Evidence(Path(directory), 'ab' * 32, [], category)
            baseline = {'outcomes': [], 'matches_original_receipts': False}
            with patch('evidence.atomic', side_effect=OSError('PRIVATE_WRITE_ERROR')):
                self.assertIs(recorder.replay(lambda *args: baseline, {}, None, [], 1), baseline)
            error = RPCError('PRIVATE_TIMEOUT_BODY', code='timeout', method='evm_mine')
            def fail(*args):
                raise error
            with self.assertRaises(RPCError) as caught:
                recorder.replay(fail, {}, None, [12], 1)
            self.assertIs(caught.exception, error)
            self.assertEqual(recorder.failures[-1]['rpc_diagnostics']['code'], 'timeout')
            self.assertEqual(recorder.secondary[0]['code'], 'snapshot_failed')
            self.assertNotIn('PRIVATE', json.dumps([recorder.failures, recorder.secondary]))

if __name__ == '__main__':
    unittest.main(verbosity=2)
