"""Offline telemetry/privacy/primary-error controls; no archive, nodes or services."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import cache_evidence as cache_module
import native_runner as native
import run as host
from entrotter_engine.evm import ExecutionError


def stats():
    return dict(requests=4, upstream=2, hits=2, entries=2, bytes=24, uncached=0, errors=0, refused_handlers=0)


def row():
    return dict(pid=42, pgid=42, port=23456, returncode=0, stdin_closed=True,
                stdout_closed=True, group_absent=True, port_closed=True, stats=stats(), closed=True)


class CacheEvidenceTests(unittest.TestCase):
    def test_stats_and_rows_strictly_finite(self):
        self.assertEqual(cache_module.finite_stats(stats()), stats())
        self.assertEqual(cache_module.finite_row(row()), row())
        for value in [None, {**stats(), 'requests': True}, {**stats(), 'upstream': 4097},
                      {**stats(), 'entries': 1025}, {**stats(), 'bytes': 8388609},
                      {**stats(), 'PRIVATE': 'https://provider.invalid?secret=PRIVATE'}]:
            with self.assertRaises(ValueError):
                cache_module.finite_stats(value)
        for value in [{**row(), 'pid': True}, {**row(), 'pgid': 43},
                      {**row(), 'port': 65536}, {**row(), 'stdin_closed': False},
                      {**row(), 'returncode': None}, {**row(), 'PRIVATE': 'secret'}]:
            with self.assertRaises(ValueError):
                cache_module.finite_row(value)

    def test_exact_single_child_startup_binding_excludes_token_and_url(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = cache_module.CacheEvidence(Path(directory), native.category)
            process = SimpleNamespace(pid=42)
            evidence.launched(process)
            cache = SimpleNamespace(url='http://127.0.0.1:23456/'+'ab'*16, process=process)
            evidence.started(cache)
            with self.assertRaises(ValueError):
                evidence.launched(SimpleNamespace(pid=43))
            serialized = (Path(directory)/'owned-cache.json').read_text()
            self.assertNotIn('http', serialized)
            self.assertNotIn('ab'*16, serialized)
            self.assertEqual(json.loads(serialized)[0]['port'],23456)
            for url in ['https://127.0.0.1:23456/'+'ab'*16,
                        'http://user:PRIVATE@127.0.0.1:23456/'+'ab'*16,
                        'http://127.0.0.1:23456/'+'ab'*16+'?secret=PRIVATE']:
                cache.url = url
                with self.assertRaises(ValueError):
                    evidence.started(cache)

    def test_closure_records_actual_independent_fields_without_inventing_unknown_port(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            evidence=cache_module.CacheEvidence(output,native.category)
            process=SimpleNamespace(pid=42,poll=lambda:0,stdin=io.BytesIO(),stdout=io.BytesIO())
            process.stdin.close();process.stdout.close()
            cache=SimpleNamespace(process=process,stats=stats(),url='http://127.0.0.1:23456/'+'ab'*16)
            evidence.launched(process)
            with patch.object(cache_module,'group_absent',return_value=True),patch.object(cache_module,'port_closed',return_value=True) as port:
                evidence.closed(cache)
                port.assert_not_called()
                self.assertIsNone(evidence.rows[0]['port_closed'])
                self.assertFalse(evidence.rows[0]['closed'])
                evidence.started(cache)
                evidence.closed(cache)
            self.assertEqual(evidence.rows[0],row())
            cache.stats={'PRIVATE':'secret'}
            with patch.object(cache_module,'group_absent',side_effect=OSError('PRIVATE URL')):
                evidence.closed(cache)
            self.assertNotIn('PRIVATE',json.dumps(evidence.secondary))

    def test_host_observation_healthy_resources_no_nonzero_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);(output/'owned-cache.json').write_text(json.dumps([row()]))
            with patch.object(host.os,'kill',side_effect=ProcessLookupError) as signal_call, \
                 patch.object(host,'group_absent',return_value=True), \
                 patch.object(host,'port_closed',return_value=True):
                rows,errors=host.observe_cache(output,time.monotonic()+1)
            self.assertEqual(errors,[])
            self.assertTrue(rows[0]['host_pid_absent'])
            self.assertTrue(rows[0]['host_port_closed'])
            signal_call.assert_called_once_with(42,0)

    def test_host_exhausted_shared_budget_never_signals_stale_pid_or_connects(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);(output/'owned-cache.json').write_text(json.dumps([row()]))
            with patch.object(host.os,'kill',return_value=None) as signal_call, \
                 patch.object(host,'group_absent',return_value=False), \
                 patch.object(host,'port_closed') as connect:
                rows,errors=host.observe_cache(output,time.monotonic()-1)
            self.assertFalse(rows[0]['host_pid_absent'])
            self.assertIsNone(rows[0]['host_port_closed'])
            self.assertIn('owned_cache_process_remains',errors)
            self.assertIn('owned_cache_observation_budget_exhausted',errors)
            signal_call.assert_called_once_with(42,0)
            connect.assert_not_called()

    def test_host_malformed_and_snapshot_fault_are_secondary_finite(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);path=output/'owned-cache.json'
            path.write_text(json.dumps([{**row(),'PRIVATE':'https://provider.invalid?key=PRIVATE'}]))
            self.assertEqual(host.observe_cache(output,time.monotonic()+1),([],['owned_cache_ledger_error']))
            path.write_text(json.dumps([row()]))
            with patch.object(host.os,'kill',side_effect=ProcessLookupError), \
                 patch.object(host,'group_absent',return_value=True), \
                 patch.object(host,'port_closed',return_value=True), \
                 patch.object(host,'atomic',side_effect=OSError('PRIVATE filename')):
                rows,errors=host.observe_cache(output,time.monotonic()+1)
            self.assertEqual(errors,['owned_cache_evidence_error'])
            self.assertNotIn('PRIVATE',json.dumps([rows,errors]))

    def test_entrypoint_cache_snapshot_fault_preserves_candidate_primary_and_baseline(self):
        prefix=json.loads((native.HERE/'signed-prefix.json').read_text())
        source={'inputs':[dict(index=x['index'],hash=x['hash'],sender=x['recovered_signer'],raw=x['raw_signed_transaction']) for x in prefix]}
        baseline={'outcomes':[],'matches_original_receipts':False}
        primary=ExecutionError('Canonical trace execution budget exceeded')
        class Cache:
            process=None
            def __init__(self,*args):pass
            def __enter__(self):return self
            def __exit__(self,*args):return None
        def replay(*args):
            if args[2]:raise primary
            return baseline
        def execute(raw):
            deadline=time.monotonic()+150
            captured=native.trace.capture_source(None,SimpleNamespace(call=lambda *a:None),deadline)
            with native.trace.ParentCache(None,None,deadline):
                native.trace.replay_branch(captured,None,[],deadline)
                native.trace.replay_branch(captured,None,[12],deadline)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            with patch.object(native,'OUTPUT',output),patch.object(native.trace,'ParentCache',Cache), \
                 patch.object(native.trace,'capture_source',lambda *a:source), \
                 patch.object(native.trace,'replay_branch',replay),patch.object(native,'execute_request',execute), \
                 patch.object(cache_module.CacheEvidence,'closed',side_effect=OSError('PRIVATE URL')), \
                 contextlib.redirect_stdout(io.StringIO()):
                native.main()
            value=json.loads((output/'result.json').read_text())
            self.assertEqual(value['primary_code'],'trace_budget_exceeded')
            self.assertEqual(value['primary_stage'],'candidate_replay')
            self.assertEqual(json.loads((output/'baseline-branch.json').read_text())['result'],baseline)
            self.assertGreater(len(value['cache_observation_errors']),0)
            self.assertNotIn('PRIVATE',json.dumps(value))
            self.assertFalse((output/'candidate-branch.json').exists())

    def test_cache_launch_snapshot_failure_always_stops_and_closes_known_owned_child(self):
        prefix=json.loads((native.HERE/'signed-prefix.json').read_text())
        source={'inputs':[dict(index=x['index'],hash=x['hash'],sender=x['recovered_signer'],raw=x['raw_signed_transaction']) for x in prefix],
                'parent':{'number':'0x1','hash':'0x'+'ab'*32}}
        process=SimpleNamespace(pid=42,stdin=io.BytesIO(),stdout=io.BytesIO(),wait=lambda **kwargs:0,poll=lambda:0)
        def execute(raw):
            deadline=time.monotonic()+150
            captured=native.trace.capture_source(None,SimpleNamespace(call=lambda *a:None),deadline)
            with native.trace.ParentCache('http://127.0.0.1:1',captured['parent'],deadline):
                self.fail('Failed launch snapshot must not begin replay')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            with patch.object(native,'OUTPUT',output),patch.object(native.trace,'capture_source',lambda *a:source), \
                 patch.object(native.evm.subprocess,'Popen',return_value=process), \
                 patch.object(cache_module.CacheEvidence,'snapshot',side_effect=OSError('PRIVATE URL')), \
                 patch.object(native.os,'killpg') as kill,patch.object(native,'execute_request',execute), \
                 contextlib.redirect_stdout(io.StringIO()):
                native.main()
            kill.assert_called_once_with(42,native.signal.SIGKILL)
            self.assertTrue(process.stdin.closed)
            self.assertTrue(process.stdout.closed)
            result=json.loads((output/'result.json').read_text())
            self.assertEqual(result['primary_error'],'os_error')
            self.assertEqual(result['primary_stage'],'parent_cache_startup')
            self.assertNotIn('PRIVATE',json.dumps(result))
            self.assertTrue((output/'captured-source.json').exists())
            self.assertFalse((output/'baseline-branch.json').exists())

if __name__=='__main__':unittest.main()
