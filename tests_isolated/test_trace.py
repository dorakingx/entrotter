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

