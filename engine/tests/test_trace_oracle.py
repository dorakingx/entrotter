"""Actual signed synthetic oracle dependency and read-only provider failures."""

from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler

from entrotter_engine.evm import AnvilSession, ExecutionError
from entrotter_engine.trace import run_trace_native, verify_trace

ROOT = Path(__file__).resolve().parents[1]
READS = {'eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber',
         'eth_getBlockByHash', 'eth_getBalance', 'eth_getCode', 'eth_getStorageAt',
         'eth_getTransactionCount', 'eth_getTransactionReceipt', 'eth_getProof',
         'eth_call', 'eth_gasPrice', 'net_version', 'web3_clientVersion'}


def assert_port_closed(port):
    with socket.socket() as sock:
        sock.settimeout(.2)
        if sock.connect_ex(('127.0.0.1', port)) == 0:
            raise AssertionError('Owned diagnostic port remains open')


def close_node(node):
    node.__exit__(None, None, None)
    if node.process is None:
        return  # Launch failed before any guardian/port was owned.
    if node.process.poll() != 0:
        raise AssertionError('Owned guardian did not exit successfully')
    assert_port_closed(urlsplit(node.rpc.url).port)


class ReadOnlyFaultProxy:
    """Same local source in all arms; no writes or invented state responses."""

    def __init__(self, target, fault, parent_number):
        self.target = target
        self.fault = fault
        self.parent_number = parent_number
        self.requests = Counter()
        self.denied = Counter()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                self.connection.settimeout(3)
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 4*1024*1024:
                    self.send_error(413); return
                req = json.loads(self.rfile.read(size))
                batch = isinstance(req, list)
                replies = [owner.reply(r) for r in (req if batch else [req])]
                body = json.dumps(replies if batch else replies[0]).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def reply(self, request):
        method = request.get('method')
        self.requests[method] += 1
        result = {'jsonrpc': '2.0', 'id': request.get('id')}
        # Anvil-only account/node fast paths are unsupported in every arm,
        # including the verified control, as on an ordinary Ethereum provider.
        if method not in READS:
            self.denied[method] += 1
            return {**result, 'error': {'code': -32601, 'message': 'Read-only proxy'}}
        if (self.fault == 'parent_missing' and method == 'eth_getBlockByNumber'
                and request['params'][0] == hex(self.parent_number)):
            self.denied[method] += 1
            return {**result, 'result': None}
        if method == self.fault:
            self.denied[method] += 1
            return {**result, 'error': {'code': -32000, 'message': 'Synthetic missing state'}}
        opener = build_opener(ProxyHandler({}))
        req = Request(self.target, json.dumps(request).encode(), {'Content-Type': 'application/json'})
        with opener.open(req, timeout=3) as response:
            raw = response.read(4*1024*1024+1)
        if len(raw) > 4*1024*1024:
            raise RuntimeError('Diagnostic response exceeded bound')
        return json.loads(raw)

    def close(self):
        port = self.server.server_port
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise AssertionError('Diagnostic proxy thread remains live')
        assert_port_closed(port)


@unittest.skipUnless(shutil.which('anvil'), 'Real Anvil required')
class TraceOracleProviderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT/'tests/data/canonical-local-oracle-inputs.json').read_text())
        fixture = cls.fixture
        cls.source = AnvilSession(trace=True)
        cls.addClassCleanup(close_node, cls.source)
        original_popen = subprocess.Popen
        def source_start(command, *args, **kwargs):
            # Only the source genesis allocation; never replay state/signature repair.
            return original_popen([*command, '--fund-accounts',
                *[a+':'+fixture['actor_balance_eth'] for a in fixture['actors']]], *args, **kwargs)
        with patch('entrotter_engine.evm.subprocess.Popen', side_effect=source_start):
            cls.source.__enter__()
        rpc = cls.source.rpc
        # Real signed CREATE transactions establish the synthetic parent state.
        for raw, address, runtime in zip(fixture['deployment_transactions'],
                [fixture['oracle'], fixture['consumer']],
                [fixture['oracle_runtime'], fixture['consumer_runtime']]):
            tx_hash = rpc.call('eth_sendRawTransaction', [raw]); rpc.call('evm_mine')
            receipt = rpc.call('eth_getTransactionReceipt', [tx_hash])
            if receipt['status'] != '0x1' or receipt['contractAddress'] != address:
                raise AssertionError('Original signed synthetic CREATE did not execute')
            if rpc.call('eth_getCode', [address, 'latest']) != runtime:
                raise AssertionError('Deployed synthetic bytecode differs')
        cls.parent_value = int(rpc.call('eth_call', [{'to': fixture['oracle'], 'data': '0x'}, 'latest']), 16)
        for raw in fixture['raw_transactions']: rpc.call('eth_sendRawTransaction', [raw])
        for method, value in [('evm_setNextBlockTimestamp', fixture['target_timestamp']),
                ('evm_setBlockGasLimit', hex(fixture['gas_limit'])),
                ('anvil_setNextBlockBaseFeePerGas', hex(fixture['base_fee'])),
                ('anvil_setCoinbase', fixture['coinbase']),
                ('anvil_setNextBlockPrevRandao', fixture['prevrandao'])]:
            rpc.call(method, [value])
        rpc.call('evm_mine')
        block = rpc.call('eth_getBlockByNumber', ['latest', False])
        if len(block['transactions']) != 2:
            raise AssertionError('Original synthetic oracle block did not execute')
        cls.plan = {'trace_version': '0.1.0', 'source': {'chain_id': 1,
            'block_number': int(block['number'], 16), 'block_hash': block['hash']},
            'through_index': 1, 'skip_indices': [0]}
        cls.cleanup_records = []
        cls.report, cls.nodes = cls.run_owned(rpc.url)
        cls.fault_observations = {}
        cls.fault_reports = {}

    @classmethod
    def run_owned(cls, url):
        nodes = []
        def create(*args, **kwargs):
            node = AnvilSession(*args, **kwargs); nodes.append(node); return node
        try:
            with patch.dict(os.environ, {'ENTROTTER_RPC_URL': url}), \
                    patch('entrotter_engine.trace.AnvilSession', side_effect=create):
                return run_trace_native(cls.plan), nodes
        finally:
            for node in nodes:
                if node.process is None:
                    continue  # Preserve the actual launch exception.
                if node.process.poll() != 0:
                    original = sys.exception()
                    if original is None:
                        raise AssertionError('Replay guardian failed cleanup')
                    original.add_note('Replay guardian exited nonzero during cleanup')
                if node.rpc is not None:
                    assert_port_closed(urlsplit(node.rpc.url).port)
                cls.cleanup_records.append({'guardian_returncode': node.process.poll(),
                    'port_closed': True if node.rpc is not None else None})

    def fault(self, name):
        proxy = ReadOnlyFaultProxy(self.source.rpc.url, name, self.plan['source']['block_number']-1)
        try:
            report, _ = self.run_owned(proxy.url)
            self.fault_reports[name] = report
            return report
        finally:
            self.fault_observations[name] = {'requests': dict(proxy.requests), 'denied': dict(proxy.denied)}
            proxy.close()
            self.fault_observations[name]['proxy_thread_and_port_closed'] = True

    def test_original_signed_oracle_update_and_adverse_omission(self):
        report = self.report
        self.assertTrue(verify_trace(report)); self.assertTrue(report['baseline_verified'])
        self.assertEqual(self.parent_value, 10)
        baseline = report['baseline']['outcomes']
        self.assertEqual([o['status'] for o in baseline], ['executed', 'executed'])
        self.assertEqual([o['receipt']['status'] for o in baseline], ['0x1', '0x1'])
        self.assertEqual([int(o['receipt']['gasUsed'], 16) for o in baseline], [26167, 26438])
        self.assertEqual([int(o['receipt']['cumulativeGasUsed'], 16) for o in baseline], [26167, 52605])
        self.assertEqual([o['differing_fields'] for o in baseline], [[], []])
        word = '0x'+(20).to_bytes(32, 'big').hex()
        self.assertEqual(baseline[1]['receipt']['logs'][0]['data'], word)
        candidate = report['candidate']['outcomes']
        self.assertEqual([o['status'] for o in candidate], ['skipped', 'executed'])
        self.assertEqual(candidate[1]['hash'], report['source']['inputs'][1]['hash'])
        self.assertEqual(candidate[1]['receipt']['status'], '0x0')
        self.assertEqual(int(candidate[1]['receipt']['gasUsed'], 16), 25808)
        self.assertEqual(candidate[1]['receipt']['logs'], [])
        self.assertEqual(set(candidate[1]['differing_fields']),
            {'status', 'gasUsed', 'cumulativeGasUsed', 'transactionIndex', 'logsBloom', 'logs'})
        self.assertFalse(report['candidate']['matches_original_receipts'])
        # Both forks leave the actual source unchanged, with the real update20.
        value = self.source.rpc.call('eth_call', [{'to': self.fixture['oracle'], 'data': '0x'}, 'latest'])
        self.assertEqual(int(value, 16), 20)
        self.assertEqual([self.source.rpc.call('eth_getTransactionCount', [a, 'latest'])
            for a in self.fixture['actors']], ['0x3', '0x1'])
        self.assertNotIn(self.source.rpc.url, json.dumps(report))

    def test_read_only_provider_control_matches_original(self):
        report = self.fault('none')
        self.assertTrue(verify_trace(report)); self.assertTrue(report['baseline_verified'])
        self.assertEqual(report['baseline']['outcomes'], self.report['baseline']['outcomes'])
        self.assertEqual(report['candidate']['outcomes'], self.report['candidate']['outcomes'])
        self.assertGreater(self.fault_observations['none']['requests'].get('eth_getStorageAt', 0), 0)

    def test_missing_parent_code_and_balance_refuse_without_fixture(self):
        for fault, message, method in [('parent_missing', 'parent block is unavailable', 'eth_getBlockByNumber'),
                ('eth_getCode', 'No fixture substitution', 'eth_getCode'),
                ('eth_getBalance', 'No fixture substitution', 'eth_getBalance')]:
            with self.subTest(fault=fault), self.assertRaisesRegex(ExecutionError, message):
                self.fault(fault)
            self.assertGreater(self.fault_observations[fault]['denied'].get(method, 0), 0)
            self.assertNotIn(fault, self.fault_reports)

    def test_missing_mining_storage_is_unverified_not_mined(self):
        report = self.fault('eth_getStorageAt')
        self.assertTrue(verify_trace(report))
        self.assertFalse(report['baseline_verified'])
        self.assertFalse(report['baseline']['matches_original_receipts'])
        self.assertFalse(report['candidate']['matches_original_receipts'])
        self.assertEqual([o['status'] for o in report['baseline']['outcomes']], ['not_mined', 'not_mined'])
        self.assertEqual([o['status'] for o in report['candidate']['outcomes']], ['skipped', 'not_mined'])
        self.assertTrue(all('receipt' not in o for branch in ['baseline', 'candidate'] for o in report[branch]['outcomes']))
        self.assertEqual(report['source'], self.report['source'])
        self.assertGreater(self.fault_observations['eth_getStorageAt']['denied'].get('eth_getStorageAt', 0), 0)


if __name__ == '__main__':
    unittest.main()
