"""Offline hostile ABI/identity/deadline/failure controls; no archive, nodes or HTTP."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import time
import unittest
from unittest.mock import patch
from consumer_observer import (ConsumerObserver, address, uint, code_identity, SELECTORS,
                               ORACLE, WETH, PROXY, ZERO, UNIT, CODE_MAX_BYTES, PHASES)
from entrotter_engine.rpc import RPCError


def abi_int(x):return '0x' + x.to_bytes(32, 'big').hex()
def abi_addr(x):return '0x' + '00'*12 + x[2:]


class HostileError(Exception):
    def __str__(self):raise AssertionError('formatter invoked')
    def __repr__(self):raise AssertionError('formatter invoked')


class RPC:
    timeout = 10
    def __init__(self, error=None):self.calls=[];self.error=error
    def call(self, method, params):
        self.calls.append((method,deepcopy(params),self.timeout))
        if self.error is not None:raise self.error
        if method=='eth_getCode':return '0x60006000'
        key=next(k for k,v in SELECTORS.items() if params[0]['data'].startswith(v))
        return {'source':abi_addr(PROXY),'price':abi_int(257082415000),
                'base_currency':abi_addr(ZERO),'base_unit':abi_int(UNIT)}[key]


class ConsumerTest(unittest.TestCase):
    def prepared(self,p):
        c=ConsumerObserver(p,'c9'*32)
        producer=[]
        for branch,phase in sorted(PHASES):
            c.observe(RPC(),branch,phase,time.monotonic()+10)
            answer=256292441874 if (branch,phase)==('baseline','after') else 257082415000
            c.rows[-1]['raw']['price']=abi_int(answer);c.rows[-1]['decoded']['price']=answer
            producer.append({'branch':branch,'phase':phase,'errors':[],
                'decoded':{'aggregator':'0xe62b71cf983019bff55bc83b48601ce8419650cc',
                'latestRoundData':{'round_id':10478 if (branch,phase)==('baseline','after') else 10477,
                                  'answer':answer,'started_at':1,'updated_at':1,'answered_in_round':1}}})
        return c,producer

    def test_strict_fixed_abi_and_code_bounds(self):
        for bad in (None,1,'0x','0X'+'00'*32,'0x'+'00'*31,'0x'+'00'*33,'0x'+'gg'*32,'0x'+'00'*32+' ',abi_int(1)+'00'):
            with self.subTest(value=type(bad).__name__),self.assertRaises(ValueError):uint(bad)
        with self.assertRaises(ValueError):address('0x01'+'00'*31)
        self.assertEqual(uint(abi_int(2**256-1)),2**256-1)
        self.assertEqual(address(abi_addr(PROXY)),PROXY)
        self.assertEqual(code_identity('0x')['nonempty'],False)
        self.assertEqual(code_identity('0xAB')['sha256'],code_identity('0xab')['sha256'])
        for bad in ('0x0','0xGG','0x'+'00'*(CODE_MAX_BYTES+1)):
            with self.assertRaises(ValueError):code_identity(bad)

    def test_exact_queries_timeout_and_hash_only_raw_code(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32);rpc=RPC();c.observe(rpc,'baseline','before',time.monotonic()+1)
            self.assertEqual(len(rpc.calls),6);self.assertEqual(rpc.timeout,10)
            self.assertTrue(all(0<x[2]<=1 for x in rpc.calls))
            self.assertEqual(rpc.calls[:2],[('eth_getCode',[ORACLE,'latest'],rpc.calls[0][2]),('eth_getCode',[PROXY,'latest'],rpc.calls[1][2])])
            for method,params,_ in rpc.calls[2:]:
                self.assertEqual(method,'eth_call');self.assertEqual(params[0]['to'],ORACLE);self.assertEqual(params[1],'latest')
                if params[0]['data'][:10] in (SELECTORS['source'],SELECTORS['price']):
                    self.assertEqual(params[0]['data'][10:],'0'*24+WETH[2:])
            saved=(Path(t)/'consumer-observations.json').read_text()
            self.assertNotIn('60006000',saved);self.assertLess(len(saved),65536)
            self.assertEqual(json.loads(saved)['request_id'],'ab'*32)

    def test_deadline_refuses_reads_and_restores_timeout(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32);rpc=RPC();c.observe(rpc,'baseline','before',time.monotonic()-1)
            self.assertEqual(rpc.calls,[]);self.assertEqual(rpc.timeout,10)
            self.assertEqual(c.rows[0]['errors'],[{'query':'oracle_code','category':'timeout'}])

    def test_midphase_deadline_stops_remaining_queries(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32);rpc=RPC()
            with patch('consumer_observer.time.monotonic',side_effect=[1,3]):c.observe(rpc,'baseline','before',2)
            self.assertEqual(len(rpc.calls),1);self.assertEqual(rpc.timeout,10)
            self.assertEqual(c.rows[0]['errors'][-1]['category'],'timeout')

    def test_hostile_and_forged_rpc_errors_are_finite(self):
        class Forged(RPCError):
            @property
            def code(self):raise HostileError()
        for error in (HostileError('secret://credentials/body'),Forged('secret://credentials/body')):
            with self.subTest(type=type(error).__name__),tempfile.TemporaryDirectory() as t:
                c=ConsumerObserver(Path(t),'ab'*32);rpc=RPC(error);c.observe(rpc,'baseline','before',time.monotonic()+10)
                output=(Path(t)/'consumer-observations.json').read_text()
                self.assertNotIn('secret',output);self.assertEqual(len(c.rows[0]['errors']),6)
                self.assertEqual(rpc.timeout,10)

    def test_exact_complete_observations_have_narrow_view_only_flag(self):
        with tempfile.TemporaryDirectory() as t:
            c,p=self.prepared(Path(t));result=c.classify(p,True)
            self.assertTrue(result['owned_read_only_price_observation_complete'])
            self.assertEqual(result['unproven_reasons'],[])
            self.assertIn('No signed consumer transaction',result['scope'])
            self.assertNotIn('profit',json.dumps({k:v for k,v in result.items() if k!='scope'}))
            self.assertFalse(c.classify(p,False)['owned_read_only_price_observation_complete'])

    def test_mismatches_and_missing_or_empty_evidence_never_claim_complete(self):
        cases=[('wrong_source',lambda c,p:c.rows[0]['decoded'].update(source=ORACLE)),
               ('wrong_unit',lambda c,p:c.rows[0]['decoded'].update(base_unit=10**18)),
               ('wrong_base',lambda c,p:c.rows[0]['decoded'].update(base_currency=WETH)),
               ('price_mismatch',lambda c,p:c.rows[0]['decoded'].update(price=1)),
               ('empty_code',lambda c,p:c.rows[0]['code'].update(oracle_code=code_identity('0x'))),
               ('code_changed',lambda c,p:c.rows[0]['code'].update(proxy_code=code_identity('0x60'))),
               ('phase_missing',lambda c,p:c.rows.pop()),
               ('phase_duplicate',lambda c,p:c.rows.__setitem__(0,deepcopy(c.rows[1]))),
               ('producer_phase_missing',lambda c,p:p.pop()),
               ('producer_negative',lambda c,p:p[0]['decoded']['latestRoundData'].update(answer=-1)),
               ('producer_source',lambda c,p:p[0]['decoded'].update(aggregator=ORACLE)),
               ('producer_shape',lambda c,p:p[0]['decoded']['latestRoundData'].pop('round_id')),
               ('error',lambda c,p:c.rows[0]['errors'].append({'query':'price','category':'rpc_error'})),
               ('snapshot_error',lambda c,p:c.secondary.append({'category':'other','code':'consumer_snapshot_failed'}))]
        for name,change in cases:
            with self.subTest(case=name),tempfile.TemporaryDirectory() as t:
                c,p=self.prepared(Path(t));change(c,p)
                self.assertFalse(c.classify(p,True)['owned_read_only_price_observation_complete'])

    def test_actual_entrypoint_candidate_failure_preserves_new_rows_and_original_primary(self):
        # Reuse the real offline entrypoint fault control, adding assertions on the
        # new observer's finalization rather than substituting a successful report.
        from test_evidence import EvidenceTest
        seen=[]
        original=ConsumerObserver.classify
        def classify(observer,producer,verified):
            result=original(observer,producer,verified)
            seen.append((deepcopy(observer.rows),verified,result))
            return result
        with patch.object(ConsumerObserver,'classify',classify):
            EvidenceTest().test_entrypoint_failure_finalizes_complete_observations_without_replay_services()
        self.assertEqual(len(seen),1)
        rows,verified,result=seen[0]
        self.assertEqual(len(rows),4)
        self.assertEqual(set((x['branch'],x['phase']) for x in rows),PHASES)
        self.assertEqual(rows[-1]['errors'][0]['category'],'skipped_primary_failure')
        self.assertFalse(verified)
        self.assertFalse(result['owned_read_only_price_observation_complete'])
        self.assertIn('replay_not_verified',result['unproven_reasons'])

    def test_primary_failure_skip_and_snapshot_error_retained(self):
        with tempfile.TemporaryDirectory() as t:
            c=ConsumerObserver(Path(t),'ab'*32)
            with patch('consumer_observer.atomic',side_effect=HostileError()):c.skipped('candidate','after')
            self.assertEqual(c.rows[0]['errors'][0]['category'],'skipped_primary_failure')
            self.assertEqual(c.secondary,[{'category':'other','code':'consumer_snapshot_failed'}])
            c.save();self.assertEqual(json.loads((Path(t)/'consumer-observations.json').read_text())['rows'],c.rows)
            with self.assertRaises(ValueError):c.skipped('candidate','after')
            self.assertFalse(c.classify([],False)['owned_read_only_price_observation_complete'])

if __name__=='__main__':unittest.main()
