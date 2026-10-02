"""Offline stop controls: no archive/HTTP/services/processes; local read-only OS/port probes."""
import contextlib
from hashlib import sha256
import io
import json
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch
from consumer_observer import ConsumerObserver, ORACLE, PROXY, SELECTORS, PHASES
from entrotter_engine.rpc import OwnedTraceRPC, RPCError, safe_diagnostics
from test_consumer_observer import RPC as FakeRPC, abi_addr, abi_int
import evidence as evidence_module
import native_runner as module


class ControlStop(BaseException):pass


class StopControls(unittest.TestCase):
    def test_duplicate_invalid_and_fifth_phase_do_not_issue_reads(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32);rpc=FakeRPC()
            c.observe(rpc,'baseline','before',time.monotonic()+10)
            n=len(rpc.calls)
            with self.assertRaises(ValueError):c.observe(rpc,'baseline','before',time.monotonic()+10)
            self.assertEqual(len(rpc.calls),n)
            with self.assertRaises(ValueError):c.observe(rpc,'not_branch','after',time.monotonic()+10)
            self.assertEqual(len(rpc.calls),n)
            for branch,phase in sorted(PHASES-{('baseline','before')}):c.observe(rpc,branch,phase,time.monotonic()+10)
            self.assertEqual(len(rpc.calls),24)
            with self.assertRaises(ValueError):c.observe(rpc,'candidate','after',time.monotonic()+10)
            self.assertEqual(len(rpc.calls),24)

    def test_nonfinite_bool_and_invalid_deadlines_refuse_before_reads(self):
        for deadline in (float('nan'),float('inf'),float('-inf'),True,False,None,'1'):
            with self.subTest(type=type(deadline).__name__),tempfile.TemporaryDirectory() as t:
                c=ConsumerObserver(Path(t),'ab'*32);rpc=FakeRPC()
                with self.assertRaises(ValueError):c.observe(rpc,'baseline','before',deadline)
                self.assertEqual(rpc.calls,[]);self.assertEqual(rpc.timeout,10)

    def test_observer_and_snapshot_propagate_nonexception_stop(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32);rpc=FakeRPC(ControlStop())
            with self.assertRaises(ControlStop):c.observe(rpc,'baseline','before',time.monotonic()+10)
            self.assertEqual(len(rpc.calls),1);self.assertEqual(rpc.timeout,10)
            self.assertEqual(c.rows,[])
            with patch('consumer_observer.atomic',side_effect=ControlStop()),self.assertRaises(ControlStop):c.save()
            self.assertEqual(c.secondary,[])

    def test_plain_rpc_timeout_is_normalized_and_recorded_finitely(self):
        rpc=OwnedTraceRPC('http://127.0.0.1:1')
        with patch.object(rpc.opener,'open',side_effect=TimeoutError('private://body/url')):
            with self.assertRaises(RPCError) as caught:rpc.call('eth_getCode',[ORACLE,'latest'])
            self.assertEqual(safe_diagnostics(caught.exception),{'code':'timeout','method':'eth_getCode'})
            with tempfile.TemporaryDirectory() as t:
                c=ConsumerObserver(Path(t),'ab'*32);c.observe(rpc,'baseline','before',time.monotonic()+10)
                self.assertEqual(len(c.rows[0]['errors']),6)
                self.assertTrue(all(x['rpc_diagnostics']['code']=='timeout' for x in c.rows[0]['errors']))
                self.assertNotIn('private',(Path(t)/'consumer-observations.json').read_text())
                self.assertEqual(rpc.timeout,10)

    def entrypoint(self,stop_phase,signum):
        handlers={};requests=[];replays=[];bodies=[];closed=[];source=json.loads((module.HERE/'signed-prefix.json').read_text())
        captured={'inputs':[{'index':x['index'],'hash':x['hash'],'sender':x['recovered_signer'],'raw':x['raw_signed_transaction']} for x in source]}
        oracle_calls=0
        class Response:
            length=None
            def __init__(self,value):self.value=value
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):return json.dumps(self.value).encode()
        class Process:
            pid=2147483647
            code=None
            def poll(self):return self.code
        def opener(request,timeout):
            nonlocal oracle_calls
            data=json.loads(request.data);requests.append(data['method'])
            if data['method']=='eth_getBlockByNumber':value={'number':'0x1','hash':'0x'+'ab'*32,'timestamp':'0x1'}
            elif data['method']=='eth_getCode':
                if data['params'][0]==ORACLE:
                    oracle_calls+=1
                    if stop_phase in ('before','after') and oracle_calls==(1 if stop_phase=='before' else 2):handlers[signum](signum,None)
                value='0x6000'
            elif data['params'][0]['data']==module.GETTERS['aggregator']:value=abi_addr(module.AGGREGATOR)
            elif data['params'][0]['data']==module.GETTERS['latestRoundData']:value='0x'+''.join(x.to_bytes(32,'big').hex() for x in (10477,257082415000,1,1,10477))
            else:
                key=next(k for k,v in SELECTORS.items() if data['params'][0]['data'].startswith(v))
                value={'source':abi_addr(PROXY),'price':abi_int(257082415000),'base_currency':abi_addr('0x'+'00'*20),'base_unit':abi_int(10**8)}[key]
            return Response({'jsonrpc':'2.0','id':data['id'],'result':value})
        sessions=[]
        class Session:
            def __init__(self):
                self.rpc=OwnedTraceRPC('http://127.0.0.1:1');self.rpc.opener.open=opener
                self.process=Process();sessions.append(self)
            def __enter__(self):return self
            def __exit__(self,*args):closed.append(self);self.process.code=0
        def replay(capture,url,skipped,deadline):
            replays.append('candidate' if skipped else 'baseline')
            with module.trace.AnvilSession():bodies.append(replays[-1])
            return {'outcomes':[],'matches_original_receipts':False}
        original_atomic=evidence_module.atomic
        def recording(path,value,limit):
            if stop_phase=='baseline_snapshot' and path.name=='baseline-branch.json':handlers[signum](signum,None)
            return original_atomic(path,value,limit)
        def execute(raw):
            deadline=time.monotonic()+150
            result=module.trace.capture_source(None,FakeRPC(),deadline)
            module.trace.replay_branch(result,None,[],deadline)
            module.trace.replay_branch(result,None,[12],deadline)
            raise ValueError('Should not reach after stopped observer')
        with tempfile.TemporaryDirectory() as t:
            with patch.object(module,'OUTPUT',Path(t)),patch.object(module.trace,'AnvilSession',Session), \
                 patch.object(module.trace,'capture_source',lambda *args:captured),patch.object(module.trace,'replay_branch',replay), \
                 patch.object(module,'execute_request',execute),patch.object(module.signal,'signal',lambda number,handler:handlers.__setitem__(number,handler)), \
                 patch.object(module.signal,'setitimer'),patch.object(evidence_module,'atomic',recording),contextlib.redirect_stdout(io.StringIO()):module.main()
            result=json.loads((Path(t)/'result.json').read_text())
            observations=json.loads((Path(t)/'consumer-observations.json').read_text())
        self.assertEqual(replays,['baseline']);self.assertEqual(bodies,[] if stop_phase=='before' else ['baseline'])
        self.assertEqual(result['primary_error'],'timeout');self.assertEqual(result['primary_stage'],'baseline_snapshot' if stop_phase=='baseline_snapshot' else 'baseline_replay')
        self.assertFalse(result['consumer_price_observation']['owned_read_only_price_observation_complete'])
        self.assertEqual(len(sessions),1);self.assertEqual(closed,sessions);self.assertEqual(sessions[0].process.code,0)
        if stop_phase!='baseline_snapshot':self.assertEqual(requests[-1],'eth_getCode')
        self.assertEqual(len(observations['rows']),0 if stop_phase=='before' else 2 if stop_phase=='baseline_snapshot' else 1)
        self.assertEqual(result['request_id'],sha256((module.HERE/'worker-request.json').read_bytes()).hexdigest())
        self.assertNotIn('Should not reach',json.dumps(result))

    def test_actual_completed_baseline_snapshot_stop_does_not_continue_candidate(self):
        self.entrypoint('baseline_snapshot',signal.SIGTERM)

    def test_actual_cache_startup_snapshot_stop_rescues_fixed_owner_without_work(self):
        from cache_evidence import CacheEvidence
        handlers={};closed=[];bodies=[];caches=[]
        class Process:
            pid=2147483647
            code=None
            stdin=stdout=None
            def poll(self):return self.code
        class Cache:
            def __init__(self,*args):self.process=Process();self.stats=None;self.url='http://127.0.0.1:1/'+'ab'*16;caches.append(self)
            def __enter__(self):return self
            def __exit__(self,*args):closed.append(self);self.process.code=0
        original_started=CacheEvidence.started
        def started(recorder,cache):
            # Exact finite owned metadata shape; original started->snapshot calls
            # immutable helper's atomic path, instrumented to deliver cancellation.
            recorder.rows=[{'pid':cache.process.pid,'pgid':cache.process.pid,'port':None,'returncode':None,
                'stdin_closed':None,'stdout_closed':None,'group_absent':None,'port_closed':None,'stats':None,'closed':False}]
            return original_started(recorder,cache)
        def stop(*args):handlers[signal.SIGTERM](signal.SIGTERM,None)
        def execute(raw):
            with module.trace.ParentCache(None,None):bodies.append('must_not_run')
            raise ValueError('must_not_continue')
        with tempfile.TemporaryDirectory() as t:
            with patch.object(module,'OUTPUT',Path(t)),patch.object(module.trace,'ParentCache',Cache), \
                 patch.object(module,'execute_request',execute),patch.object(CacheEvidence,'started',started), \
                 patch('cache_evidence.atomic',side_effect=stop),patch.object(module.signal,'signal',lambda number,handler:handlers.__setitem__(number,handler)), \
                 patch.object(module.signal,'setitimer'),contextlib.redirect_stdout(io.StringIO()):module.main()
            result=json.loads((Path(t)/'result.json').read_text())
        self.assertEqual(bodies,[]);self.assertEqual(closed,caches);self.assertEqual(len(caches),1)
        self.assertEqual(result['primary_error'],'timeout');self.assertEqual(result['primary_stage'],'parent_cache_startup')
        self.assertFalse(result['consumer_price_observation']['owned_read_only_price_observation_complete'])
        self.assertEqual(caches[0].process.code,0)

    def test_actual_before_observer_signal_stops_real_rpc_and_rescues_owned_session(self):
        self.entrypoint('before',signal.SIGTERM)

    def test_actual_after_observer_hard_alarm_stops_replay_and_runs_owned_exit(self):
        self.entrypoint('after',signal.SIGALRM)

if __name__=='__main__':unittest.main()
