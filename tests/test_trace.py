"""Separate transaction-replay tests; synthetic chains never claim archive proof."""

from copy import deepcopy
import json
import os
import secrets
import shutil
import subprocess
import time
import unittest
from unittest.mock import patch

from entrotter_engine.artifact import verify
from entrotter_engine.evm import AnvilSession, ExecutionError
from entrotter_engine.rpc import OwnedTraceRPC, RPC, RPCError
from entrotter_engine.trace import (
    capture_source, data, quantity, receipt_projection, rlp, run_trace_native,
    signed_transaction, validate_plan,
    run_trace, verify_trace, replay_branch,
)


def plan():
    return {'trace_version': '0.1.0', 'source': {'chain_id': 1,
            'block_number': 19000000, 'block_hash': '0x' + 'ab' * 32},
            'through_index': 2, 'skip_indices': [0]}


def transaction(kind=2):
    return {'type': hex(kind), 'chainId': '0x1', 'nonce': '0x0',
            'gas': '0xc350', 'to': '0x' + '12' * 20, 'value': '0x0',
            'input': '0x', 'gasPrice': '0x2', 'maxPriorityFeePerGas': '0x1',
            'maxFeePerGas': '0x2', 'accessList': [],
            'v': '0x25' if kind == 0 else '0x0', 'r': '0x1', 's': '0x1'}


def receipt():
    return {'type': '0x2', 'status': '0x1', 'gasUsed': '0x5208',
            'cumulativeGasUsed': '0x5208', 'effectiveGasPrice': '0x1',
            'transactionIndex': '0x0', 'transactionHash': '0x' + 'aa' * 32,
            'from': '0x' + '12' * 20, 'to': '0x' + '34' * 20,
            'contractAddress': None, 'logsBloom': '0x' + '00' * 256, 'logs': []}


class TraceValidationTests(unittest.TestCase):
    def test_exact_plan_boundaries(self):
        self.assertEqual(validate_plan(plan()), plan())
        p = plan(); p['through_index'] = 31; p['skip_indices'] = list(range(32))
        self.assertEqual(validate_plan(p), p)
        for field, values in [('through_index', [-1, 32, True, '0']),
                              ('skip_indices', [[0, 0], [1, 0], [3], [True], '0']),
                              ('trace_version', ['1', 1])]:
            for value in values:
                p = plan(); p[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_plan(p)

    def test_no_urls_code_or_source_guessing(self):
        for field in ['url', 'command', 'provider', 'agent', 'schema_version']:
            p = plan(); p[field] = 'unsafe'
            with self.assertRaises(ValueError): validate_plan(p)
        for field, value in [('chain_id', True), ('chain_id', 31337),
                             ('block_number', True), ('block_number', 0),
                             ('block_hash', 'latest'), ('rpc_url', 'http://example.com')]:
            p = plan(); p['source'][field] = value
            with self.assertRaises(ValueError): validate_plan(p)

    def test_invalid_plan_refused_before_network_or_node(self):
        p = plan(); p['through_index'] = 32
        with patch('entrotter_engine.trace.RPC') as rpc, patch('entrotter_engine.trace.AnvilSession') as node:
            with self.assertRaises(ValueError): run_trace_native(p)
            rpc.assert_not_called(); node.assert_not_called()

    def test_missing_archive_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ExecutionError, 'no fallback'):
            run_trace_native(plan())

    def test_caller_mutation_cannot_change_admitted_plan(self):
        p=plan(); original=deepcopy(p)
        def capture(snapshot, upstream, deadline):
            p['skip_indices']=[-1]
            return {'sentinel':True}
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL':'https://example.com'}), \
             patch('entrotter_engine.trace.capture_source', side_effect=capture), \
             patch('entrotter_engine.trace.replay_branch', return_value={'matches_original_receipts':True}) as replay:
            r=run_trace_native(p)
        self.assertEqual(r['plan'], original)
        self.assertEqual(replay.call_args_list[1].args[2], original['skip_indices'])
        self.assertIsNot(r['plan'], p)

    def test_default_trace_has_no_native_fallback(self):
        with patch('entrotter_engine.isolated.client', side_effect=RuntimeError('no daemon')), \
             patch('entrotter_engine.trace.run_trace_native') as native:
            with self.assertRaisesRegex(RuntimeError,'no daemon'): run_trace(plan())
            native.assert_not_called()

    def test_quantity_and_bytes(self):
        self.assertEqual(quantity('0x0', 'test'), 0)
        self.assertEqual(quantity('0x' + 'f'*64, 'test'), 2**256-1)
        for bad in ['0x00', '-1', 1, True, '0x' + 'f'*65, '0x']:
            with self.assertRaises(ValueError): quantity(bad, 'test')
        self.assertEqual(data('0xaAbB', 'test', size=2), b'\xaa\xbb')
        for bad in ['0x1', '0xgg', 'aa', None]:
            with self.assertRaises(ValueError): data(bad, 'test')
        with self.assertRaises(ValueError): data('0x0000', 'test', limit=1)

    def test_rlp_boundary_vectors(self):
        self.assertEqual(rlp(0), b'\x80')
        self.assertEqual(rlp(127), b'\x7f')
        self.assertEqual(rlp(128), b'\x81\x80')
        self.assertEqual(rlp([b'cat', b'dog']), bytes.fromhex('c88363617483646f67'))
        self.assertEqual(rlp(b'a'*55), b'\xb7'+b'a'*55)
        self.assertEqual(rlp(b'a'*56), b'\xb8\x38'+b'a'*56)
        self.assertEqual(rlp([b'a'*56]), b'\xf8\x3a\xb8\x38'+b'a'*56)
        for bad in [-1, 2**256, True, 'string', {}]:
            with self.assertRaises(ValueError): rlp(bad)

    def test_legacy_and_typed_encoding_vectors(self):
        dest = '12'*20
        self.assertEqual(signed_transaction(transaction(0)), '0x'+'df800282c35094'+dest+'8080250101')
        self.assertEqual(signed_transaction(transaction(1)), '0x01'+'e101800282c35094'+dest+'8080c0800101')
        self.assertEqual(signed_transaction(transaction(2)), '0x02'+'e20180010282c35094'+dest+'8080c0800101')
        tx = transaction(); tx['to'] = None
        self.assertIn('82c350808080', signed_transaction(tx))

    def test_unsupported_signatures_and_budgets(self):
        for field, values in [('type', ['0x3', '0x4']), ('chainId', ['0x2']),
                              ('v', ['0x2']), ('s', ['0x0', '0x'+'f'*64]),
                              ('r', ['0x0', '0x'+'f'*64]), ('yParity', ['0x1']),
                              ('maxPriorityFeePerGas', ['0x3']), ('gas', ['0x1']),
                              ('input', ['0x00' + '00'*65536])]:
            for value in values:
                tx = transaction(); tx[field] = value
                with self.subTest(field=field), self.assertRaises(ValueError): signed_transaction(tx)
        tx = transaction(0); tx['v'] = '0x27'
        with self.assertRaises(ValueError): signed_transaction(tx)

    def test_access_list_order_and_bounds(self):
        tx = transaction(1)
        tx['accessList'] = [{'address':'0x'+'ab'*20, 'storageKeys':['0x'+'11'*32, '0x'+'22'*32]}]
        raw = signed_transaction(tx)
        changed = deepcopy(tx); changed['accessList'][0]['storageKeys'].reverse()
        self.assertNotEqual(raw, signed_transaction(changed))
        tx['accessList'][0]['storageKeys'] *= 129
        with self.assertRaises(ValueError): signed_transaction(tx)
        tx['accessList'] = [{'address':'0x'+'ab'*20,'storageKeys':[], 'command':'unsafe'}]
        with self.assertRaises(ValueError): signed_transaction(tx)

    def test_normal_and_upstream_transports_still_refuse_raw(self):
        for rpc in [RPC('https://example.com'), RPC('http://127.0.0.1:1', local=True)]:
            with self.assertRaises(RPCError): rpc.call('eth_sendRawTransaction', ['0x00'])
        for url in ['https://127.0.0.1:1', 'http://localhost:1', 'http://example.com']:
            with self.assertRaises(RPCError): OwnedTraceRPC(url)
        for method in ['anvil_setBalance', 'anvil_setCode', 'anvil_impersonateAccount', 'eth_sendTransaction']:
            with self.assertRaises(RPCError): OwnedTraceRPC('http://127.0.0.1:1').call(method)

    def test_receipt_compares_ordered_bytes_but_not_block_hash(self):
        r = receipt(); p = receipt_projection(r)
        r.update(blockHash='0x'+'ff'*32, blockNumber='0x1')
        self.assertEqual(p, receipt_projection(r))
        r['status']='0x0'; self.assertNotEqual(p, receipt_projection(r))
        r['logs']=[{'address':r['to'],'topics':['0x'+'11'*32], 'data':'0x00', 'removed':False}]
        a=receipt_projection(r); r['logs'][0]['data']='0x01'
        self.assertNotEqual(a, receipt_projection(r))
        r['logs'][0]['removed']=True
        with self.assertRaises(ValueError): receipt_projection(r)

    def test_missing_state_and_bad_source_never_substitute_fixture(self):
        class WrongSource:
            def call(self, method, params=None): return '0x2'
        with self.assertRaisesRegex(ExecutionError, 'upstream chain'):
            capture_source(plan(), WrongSource(), time.monotonic()+30)
        r=receipt(); del r['gasUsed']
        with self.assertRaises(ValueError): receipt_projection(r)


class TraceMineDeadlineTests(unittest.TestCase):
    def replay(self, *, remaining=30, failure=False):
        original = receipt()
        captured = {
            'parent': {'chain_id': 1, 'block_number': 18999999,
                       'block_hash': '0x' + 'ab' * 32},
            'header': {'timestamp': 1705173443, 'gas_limit': 30000000,
                       'base_fee': 1, 'coinbase': '0x' + 'cd' * 20,
                       'prevrandao': '0x' + 'ef' * 32},
            'inputs': [{'index': 0, 'hash': original['transactionHash'],
                        'sender': original['from'], 'nonce': 0, 'raw': '0x00',
                        'original_receipt': receipt_projection(original)}],
        }
        class SlowMiningRPC:
            timeout = 10
            mine_timeout = None
            block_reads = 0
            def call(self, method, params=None):
                if method == 'eth_getBlockByNumber':
                    self.block_reads += 1
                    if self.block_reads == 1:
                        return {'hash': captured['parent']['block_hash']}
                    header = captured['header']
                    return {'number': hex(19000000), 'timestamp': hex(header['timestamp']),
                            'gasLimit': hex(header['gas_limit']), 'baseFeePerGas': '0x1',
                            'miner': header['coinbase'], 'mixHash': header['prevrandao']}
                if method == 'eth_getTransactionCount': return '0x0'
                if method == 'eth_sendRawTransaction': return original['transactionHash']
                if method == 'eth_getTransactionReceipt': return original
                if method == 'evm_mine':
                    self.mine_timeout = self.timeout
                    # A valid archive-backed mine exceeds the ordinary read cap.
                    if failure or (remaining > 10 and self.timeout <= 10):
                        raise RPCError('simulated mining socket timeout')
                    return None
                if method in OwnedTraceRPC.LOCAL_METHODS: return None
                raise AssertionError(method)
        rpc = SlowMiningRPC()
        with patch('entrotter_engine.trace.AnvilSession') as node, \
             patch('entrotter_engine.trace.time.monotonic', return_value=1000):
            node.return_value.__enter__.return_value.rpc = rpc
            node.return_value.__enter__.return_value.version = 'test node'
            if failure:
                with self.assertRaisesRegex(RPCError, 'mining socket timeout'):
                    replay_branch(captured, 'https://example.com', [], 1000 + remaining)
                result = None
            else:
                result = replay_branch(captured, 'https://example.com', [], 1000 + remaining)
            node.return_value.__exit__.assert_called_once()
            self.assertEqual(node.call_args.kwargs['lifetime'], remaining)
        self.assertEqual(rpc.timeout, 10)
        return rpc.mine_timeout, result

    def test_slow_mine_uses_remaining_primitive_budget_then_restores_reads(self):
        timeout, result = self.replay()
        self.assertEqual(timeout, 30)
        self.assertTrue(result['matches_original_receipts'])

    def test_mine_never_gets_a_fresh_budget_when_deadline_is_near(self):
        timeout, result = self.replay(remaining=2.5)
        self.assertEqual(timeout, 2.5)
        self.assertTrue(result['matches_original_receipts'])

    def test_failed_mine_restores_timeout_and_exits_owned_context(self):
        timeout, result = self.replay(failure=True)
        self.assertEqual(timeout, 30)
        self.assertIsNone(result)


@unittest.skipUnless(shutil.which('anvil') and shutil.which('cast'), 'Real Anvil/cast required; no synthetic pass')
class CanonicalLocalIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = AnvilSession(trace=True)
        cls.session.__enter__()
        cls.addClassCleanup(cls.session.__exit__, None, None, None)
        rpc = cls.session.rpc
        cls.rpc = rpc
        def cast(*args):
            # Only a random disposable local fixture key; never retained in artifacts.
            result = subprocess.run(['cast', *args], capture_output=True, text=True, timeout=15)
            if result.returncode: raise RuntimeError('Synthetic fixture cast command failed')
            return result.stdout.strip()
        key='0x'+secrets.token_hex(32)
        actor=cast('wallet', 'address', '--private-key', key).lower()
        setup=RPC(rpc.url, local=True)
        setup.call('anvil_setBalance', [actor, hex(10**20)])
        revert='0x'+'ab'*20; log='0x'+'cd'*20; recipient='0x'+'ef'*20
        setup.call('anvil_setCode', [revert, '0x60006000fd'])
        setup.call('anvil_setCode', [log, '0x600160005260206000a000'])
        rpc.call('evm_setNextBlockTimestamp', [1700000012]); rpc.call('evm_mine')
        cls.raws=[]
        for index, target in enumerate([recipient, revert, log]):
            options=['mktx', target, '--rpc-url', rpc.url, '--chain-id', '1', '--nonce', str(index),
                     '--gas-limit', '50000', '--gas-price', '2000000000', '--value', '1' if index==0 else '0', '--private-key', key]
            if index<2: options += ['--legacy']
            if index==1: options += ['--access-list','[]']
            if index==2: options += ['--priority-gas-price','1000000000']
            raw=cast(*options); cls.raws.append(raw)
            rpc.call('eth_sendRawTransaction', [raw])
        rpc.call('evm_setNextBlockTimestamp', [1700000024]); rpc.call('evm_mine')
        cls.block=rpc.call('eth_getBlockByNumber', ['latest', True])
        cls.plan={'trace_version':'0.1.0','source':{'chain_id':1,'block_number':int(cls.block['number'],16),'block_hash':cls.block['hash']},'through_index':2,'skip_indices':[0]}
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL':rpc.url}):
            cls.report=run_trace_native(cls.plan)

    def test_real_signature_reconstruction_all_types(self):
        self.assertEqual([int(tx['type'],16) for tx in self.block['transactions']], [0,1,2])
        for tx, raw in zip(self.block['transactions'], self.raws):
            self.assertEqual(signed_transaction(tx), raw)

    def test_paired_replay_original_success_revert_and_logs(self):
        self.assertTrue(self.report['baseline_verified'])
        outcomes=self.report['baseline']['outcomes']
        self.assertEqual([r['receipt']['status'] for r in outcomes], ['0x1','0x0','0x1'])
        self.assertEqual(len(outcomes[-1]['receipt']['logs']), 1)
        self.assertTrue(all(not r['differing_fields'] for r in outcomes))
        self.assertEqual([r['status'] for r in self.report['candidate']['outcomes']], ['skipped','nonce_conflict','nonce_conflict'])
        self.assertFalse(self.report['candidate']['matches_original_receipts'])
        self.assertFalse(verify(self.report)) # Separate format, never a v0.1 action result.
        self.assertTrue(verify_trace(self.report))
        self.assertNotIn(self.rpc.url, json.dumps(self.report))

    def test_archive_failure_and_pin_divergence(self):
        p=deepcopy(self.plan); p['source']['block_hash']='0x'+'ff'*32
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL':self.rpc.url}), self.assertRaisesRegex(ExecutionError,'Pinned trace block'):
            run_trace_native(p)
        p=deepcopy(self.plan); p['through_index']=3
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL':self.rpc.url}), self.assertRaisesRegex(ExecutionError,'prefix is unavailable'):
            run_trace_native(p)

    def test_rejection_and_owned_node_cleanup(self):
        captured=capture_source(self.plan, RPC(self.rpc.url), time.monotonic()+30)
        captured['header']['base_fee']=5000000000
        from entrotter_engine.trace import replay_branch
        nodes=[]
        def create(*args,**kwargs):
            node=AnvilSession(*args,**kwargs); nodes.append(node); return node
        with patch('entrotter_engine.trace.AnvilSession', side_effect=create):
            # High original-header fee rejects all originals without repairing signatures.
            r=replay_branch(captured, self.rpc.url, [], time.monotonic()+30)
            self.assertFalse(r['matches_original_receipts'])
            self.assertEqual([x['status'] for x in r['outcomes']], ['rejected','nonce_conflict','nonce_conflict'])
        self.assertEqual(len(nodes),1)
        self.assertIsNotNone(nodes[0].process.poll())
        with self.assertRaises(RPCError): nodes[0].rpc.call('eth_chainId')

    def test_error_inside_trace_context_closes_node(self):
        node=AnvilSession(trace=True)
        with self.assertRaisesRegex(RuntimeError,'cancelled'):
            with node: raise RuntimeError('cancelled')
        self.assertIsNotNone(node.process.poll())
        with self.assertRaises(RPCError): node.rpc.call('eth_chainId')
