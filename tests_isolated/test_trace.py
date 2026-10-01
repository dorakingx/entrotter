"""Actual no-network worker replay of public disposable synthetic signed inputs."""
import json
import os
from pathlib import Path
import unittest

import test_worker as harness
from entrotter_engine.trace import verify_trace

ROOT = Path(__file__).resolve().parents[1]


class BoundedCanonicalReplay(unittest.TestCase):
    probe = harness.IsolatedWorkerTests.probe

    @classmethod
    def setUpClass(cls):
        cls.image = os.environ['ENTROTTER_WORKER_IMAGE']

    def test_actual_worker_reconstructs_original_receipts_and_nonce_conflicts(self):
        fixture=json.loads((ROOT/'tests/data/canonical-local-inputs.json').read_text())
        code='''import json,os
from entrotter_engine.evm import AnvilSession
from entrotter_engine.rpc import RPC
from entrotter_engine.worker_protocol import encode_trace_request,execute_request
fixture=FIXTURE
with AnvilSession(trace=True) as source:
    rpc=source.rpc
    setup=RPC(rpc.url,local=True)
    setup.call('anvil_setBalance',[fixture['actor'],hex(int(fixture['actor_balance_wei']))])
    for address,bytecode in fixture['local_contracts'].items(): setup.call('anvil_setCode',[address,bytecode])
    rpc.call('evm_setNextBlockTimestamp',[fixture['parent_timestamp']]);rpc.call('evm_mine')
    for raw in fixture['raw_transactions']:rpc.call('eth_sendRawTransaction',[raw])
    rpc.call('evm_setNextBlockTimestamp',[fixture['target_timestamp']]);rpc.call('evm_mine')
    block=rpc.call('eth_getBlockByNumber',['latest',False])
    plan={'trace_version':'0.1.0','source':{'chain_id':1,'block_number':int(block['number'],16),'block_hash':block['hash']},'through_index':2,'skip_indices':[0]}
    os.environ['ENTROTTER_RPC_URL']=rpc.url
    result=execute_request(encode_trace_request(plan))
print(json.dumps(result))
'''.replace('FIXTURE',repr(fixture))
        result,_=self.probe(code)
        self.assertEqual(result.returncode,0,result.stderr)
        envelope=json.loads(result.stdout);report=envelope['report']
        self.assertTrue(verify_trace(report))
        self.assertTrue(report['baseline_verified'])
        self.assertEqual([r['receipt']['status'] for r in report['baseline']['outcomes']],['0x1','0x0','0x1'])
        self.assertEqual([r['status'] for r in report['candidate']['outcomes']],['skipped','nonce_conflict','nonce_conflict'])
        self.assertTrue(all(not r['differing_fields'] for r in report['baseline']['outcomes']))

    def test_actual_image_protocol_retains_same_block_funding_and_unmined_omission(self):
        fixture=json.loads((ROOT/'tests/data/canonical-local-funding-inputs.json').read_text())
        code='''import json,os,subprocess
from unittest.mock import patch
from entrotter_engine.evm import AnvilSession
from entrotter_engine.worker_protocol import encode_trace_request,execute_request
fixture=FIXTURE
original_popen=subprocess.Popen
def fixture_start(command,*args,**kwargs):
    return original_popen([*command,'--fund-accounts',fixture['actor']+':'+fixture['actor_balance_eth']],*args,**kwargs)
source=AnvilSession(trace=True)
# Only the original synthetic source receives a startup allocation. Replay
# nodes fork its pinned parent without state overrides or signing material.
with patch('entrotter_engine.evm.subprocess.Popen',side_effect=fixture_start):
    source.__enter__()
try:
    rpc=source.rpc
    rpc.call('evm_setNextBlockTimestamp',[fixture['target_timestamp']])
    rpc.call('evm_setBlockGasLimit',['0xc350'])
    rpc.call('anvil_setNextBlockBaseFeePerGas',['0x3b9aca00'])
    rpc.call('anvil_setCoinbase',['0x'+'42'*20])
    rpc.call('anvil_setNextBlockPrevRandao',['0x'+'11'*32])
    for raw in fixture['raw_transactions']:rpc.call('eth_sendRawTransaction',[raw])
    rpc.call('evm_mine')
    block=rpc.call('eth_getBlockByNumber',['latest',False])
    if len(block['transactions'])!=2:raise RuntimeError('Original funding block did not execute')
    plan={'trace_version':'0.1.0','source':{'chain_id':1,'block_number':int(block['number'],16),'block_hash':block['hash']},'through_index':1,'skip_indices':[0]}
    os.environ['ENTROTTER_RPC_URL']=rpc.url
    result=execute_request(encode_trace_request(plan))
finally:
    source.__exit__(None,None,None)
print(json.dumps(result))
'''.replace('FIXTURE',repr(fixture))
        # This executes the worker protocol in the bounded image. It does not
        # replace the separate host default-client/lifecycle integration gates.
        result,_=self.probe(code)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)['report']
        self.assertTrue(verify_trace(report))
        self.assertTrue(report['baseline_verified'])
        baseline=report['baseline']['outcomes']
        self.assertEqual([o['receipt']['status'] for o in baseline],['0x1','0x1'])
        self.assertEqual([int(o['receipt']['gasUsed'],16) for o in baseline],[21000,21000])
        self.assertEqual([int(o['receipt']['cumulativeGasUsed'],16) for o in baseline],[21000,42000])
        self.assertEqual([o['receipt']['transactionIndex'] for o in baseline],['0x0','0x1'])
        self.assertTrue(all(not o['differing_fields'] for o in baseline))
        candidate=report['candidate']['outcomes']
        self.assertEqual([o['status'] for o in candidate],['skipped','not_mined'])
        self.assertNotIn('receipt',candidate[1])
        self.assertFalse(report['candidate']['matches_original_receipts'])
