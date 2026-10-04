"""Real synthetic same-block funding; no historical or Docker proof is implied."""

from copy import deepcopy
import os
import secrets
import shutil
import socket
import subprocess
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from entrotter_engine.evm import AnvilSession
from entrotter_engine.rpc import RPC
from entrotter_engine.trace import run_trace_native, verify_trace


def cast(*args):
    result = subprocess.run(['cast', *args], capture_output=True, text=True, timeout=15)
    if result.returncode:
        # Never emit signing argv, private fixture material or helper stderr.
        raise RuntimeError('Disposable synthetic signing helper failed')
    return result.stdout.strip()


def assert_closed(test, session):
    test.assertEqual(session.process.poll(), 0)
    with socket.socket() as sock:
        sock.settimeout(.2)
        test.assertNotEqual(sock.connect_ex(('127.0.0.1', urlsplit(session.rpc.url).port)), 0)


class TraceAdmissionProfileTests(unittest.TestCase):
    def test_only_trace_profile_defers_pool_admission(self):
        for trace in [False, True]:
            with self.subTest(trace=trace), \
                 patch('entrotter_engine.evm.shutil.which', return_value='/trusted/anvil'), \
                 patch('entrotter_engine.evm.subprocess.Popen', side_effect=RuntimeError('capture only')) as launch:
                with self.assertRaisesRegex(RuntimeError, 'capture only'):
                    AnvilSession(trace=trace).__enter__()
            command = launch.call_args.args[0]
            self.assertEqual('--disable-pool-balance-checks' in command, trace)
            self.assertIn('--memory-limit', command)
            self.assertEqual(command[command.index('--memory-limit') + 1], '67108864')
            self.assertEqual(command[command.index('--host') + 1], '127.0.0.1')
            self.assertIn('--no-mining', command)
            self.assertNotIn('--disable-block-gas-limit', command)
            self.assertNotIn('--auto-impersonate', command)


@unittest.skipUnless(shutil.which('anvil') and shutil.which('cast'), 'Real Anvil/cast required')
class TraceFundingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Signers are random disposable fixture material held only in memory.
        keys = ['0x' + secrets.token_hex(32) for _ in range(2)]
        cls.actors = [cast('wallet', 'address', '--private-key', key).lower() for key in keys]
        cls.target = '0x' + '33' * 20
        original_popen = subprocess.Popen
        def fixture_start(command, *args, **kwargs):
            command = list(command)
            # Source fixture startup allocation, never a replay balance/nonce patch.
            command += ['--fund-accounts', cls.actors[0] + ':1']
            # Independent valid source can be built even before the production fix.
            if '--disable-pool-balance-checks' not in command:
                command += ['--disable-pool-balance-checks']
            return original_popen(command, *args, **kwargs)
        cls.source = AnvilSession(trace=True)
        with patch('entrotter_engine.evm.subprocess.Popen', side_effect=fixture_start):
            cls.source.__enter__()
        cls.addClassCleanup(cls.source.__exit__, None, None, None)
        rpc = cls.source.rpc
        cls.raws = []
        for key, to, value in zip(keys, [cls.actors[1], cls.target], [10**16, 10**15]):
            raw = cast('mktx', to, '--private-key', key, '--legacy', '--chain', '1',
                       '--nonce', '0', '--gas-limit', '21000', '--gas-price', '1000000000',
                       '--value', str(value), '--rpc-url', rpc.url)
            cls.raws.append(raw)
            rpc.call('eth_sendRawTransaction', [raw])
        keys.clear()
        rpc.call('evm_setNextBlockTimestamp', [1700000123])
        rpc.call('evm_setBlockGasLimit', ['0xc350'])
        rpc.call('anvil_setNextBlockBaseFeePerGas', ['0x3b9aca00'])
        rpc.call('anvil_setCoinbase', ['0x' + '42' * 20])
        rpc.call('anvil_setNextBlockPrevRandao', ['0x' + '11' * 32])
        rpc.call('evm_mine')
        block = rpc.call('eth_getBlockByNumber', ['latest', True])
        if len(block['transactions']) != 2:
            raise RuntimeError('Original synthetic funding block did not execute')
        cls.block = block
        cls.plan = {'trace_version': '0.1.0', 'source': {'chain_id': 1,
                    'block_number': int(block['number'], 16), 'block_hash': block['hash']},
                    'through_index': 1, 'skip_indices': [0]}
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL': rpc.url}):
            cls.report = run_trace_native(cls.plan)

    def test_original_signed_funding_and_omission_same_block(self):
        report = self.report
        self.assertTrue(verify_trace(report))
        self.assertTrue(report['baseline_verified'])
        baseline = report['baseline']['outcomes']
        self.assertEqual([o['status'] for o in baseline], ['executed', 'executed'])
        self.assertEqual([o['receipt']['status'] for o in baseline], ['0x1', '0x1'])
        self.assertEqual([int(o['receipt']['gasUsed'], 16) for o in baseline], [21000, 21000])
        self.assertEqual([int(o['receipt']['cumulativeGasUsed'], 16) for o in baseline], [21000, 42000])
        self.assertEqual([o['receipt']['transactionIndex'] for o in baseline], ['0x0', '0x1'])
        self.assertEqual([o['differing_fields'] for o in baseline], [[], []])
        self.assertEqual([o['status'] for o in report['candidate']['outcomes']], ['skipped', 'not_mined'])
        self.assertFalse(report['candidate']['matches_original_receipts'])
        self.assertNotIn('receipt', report['candidate']['outcomes'][1])
        self.assertNotIn(self.source.rpc.url, str(report))

    def test_replay_preserves_inputs_and_closes_owned_node(self):
        from entrotter_engine.trace import capture_source, replay_branch
        captured = capture_source(self.plan, RPC(self.source.rpc.url), time.monotonic() + 30)
        before = deepcopy(captured)
        for sender, expected in zip(self.actors, [1, 1]):
            self.assertEqual(int(self.source.rpc.call('eth_getTransactionCount', [sender, 'latest']), 16), expected)
        self.assertEqual(int(self.source.rpc.call('eth_getBalance', [self.actors[1], 'latest']), 16), 8979000000000000)
        self.assertEqual(int(self.source.rpc.call('eth_getBalance', [self.target, 'latest']), 16), 10**15)
        nodes = []
        def create(*args, **kwargs):
            node = AnvilSession(*args, **kwargs); nodes.append(node); return node
        with patch('entrotter_engine.trace.AnvilSession', side_effect=create):
            result = replay_branch(captured, self.source.rpc.url, [1], time.monotonic() + 30)
        self.assertEqual([o['status'] for o in result['outcomes']], ['executed', 'skipped'])
        self.assertEqual(captured, before)
        for node in nodes: assert_closed(self, node)

    def test_invalid_signed_inputs_never_become_receipts(self):
        # Each case gets a fresh owned production-profile node and one mined
        # block. Pool acceptance alone is deliberately not called execution.
        key = '0x' + secrets.token_hex(32)
        actor = cast('wallet', 'address', '--private-key', key).lower()
        original_popen = subprocess.Popen
        def fixture_start(command, *args, **kwargs):
            return original_popen([*command, '--fund-accounts', actor + ':1'], *args, **kwargs)
        for label, gas, fee, nonce in [('intrinsic_gas', 20000, 10**9, 0),
                                       ('block_gas', 50001, 10**9, 0),
                                       ('base_fee', 21000, 1, 0),
                                       ('nonce_gap', 21000, 10**9, 1)]:
            with self.subTest(label=label):
                node = AnvilSession(trace=True)
                with patch('entrotter_engine.evm.subprocess.Popen', side_effect=fixture_start):
                    node.__enter__()
                try:
                    rpc = node.rpc
                    rpc.call('evm_setBlockGasLimit', ['0xc350'])
                    rpc.call('anvil_setNextBlockBaseFeePerGas', ['0x3b9aca00'])
                    raw = cast('mktx', self.target, '--private-key', key, '--legacy', '--chain', '1',
                               '--nonce', str(nonce), '--gas-limit', str(gas), '--gas-price', str(fee),
                               '--value', '1', '--rpc-url', rpc.url)
                    tx_hash = rpc.call('eth_sendRawTransaction', [raw])
                    rpc.call('evm_mine')
                    self.assertIsNone(rpc.call('eth_getTransactionReceipt', [tx_hash]))
                    self.assertEqual(rpc.call('eth_getTransactionCount', [actor, 'latest']), '0x0')
                    self.assertEqual(int(rpc.call('eth_getBalance', [actor, 'latest']), 16), 10**18)
                    self.assertEqual(rpc.call('eth_getBalance', [self.target, 'latest']), '0x0')
                finally:
                    node.__exit__(None, None, None)
                assert_closed(self, node)


if __name__ == '__main__':
    unittest.main()
