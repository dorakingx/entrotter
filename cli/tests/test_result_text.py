"""Exact recorded presentation; mutations are synthetic controls, not new EVM runs."""
from contextlib import redirect_stdout, redirect_stderr
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from entrotter_cli.main import main
from entrotter_sdk import Client

SAMPLE = Path(__file__).parent / 'data/aave-borrow-result.json'


def seal(row):
    body = {k: v for k, v in row.items() if k != 'artifact_id'}
    row['artifact_id'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return row


class ResultTextTests(unittest.TestCase):
    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(args)
            except SystemExit as stopped:
                code = stopped.code
        return code, out.getvalue(), err.getvalue()

    def inspect(self, row):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'control.json'
            path.write_text(json.dumps(seal(row)))
            return self.invoke(['inspect', str(path), '--format', 'text'])

    def test_recorded_aave_exact_output_and_offline_boundary(self):
        with patch.dict(sys.modules, {'entrotter_engine': None}), patch.object(Client, '_request', side_effect=AssertionError('No API')), patch('socket.socket', side_effect=AssertionError('No network')), patch('entrotter_cli.main.ExportBudget', side_effect=AssertionError('No export')):
            code, out, err = self.invoke(['inspect', str(SAMPLE), '--format', 'text'])
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(out, SAMPLE.with_suffix('.txt').read_text())
        for value in ['10.000000094454558462', '723131', '560326', '-162805', '+0.002422422432849788', 'preflight-risk-v1', 'Step 3: hold', '0xea51d7853eefb32b6ee06b1c12e6dcca88be0ffe']:
            self.assertIn(value, out)
        self.assertIn('Balance differences do not measure profit', out)

    def test_default_json_unchanged_and_explicit_json(self):
        original = self.invoke(['inspect', str(SAMPLE)])
        self.assertEqual((original[0], original[2]), (0, ''))
        self.assertEqual(hashlib.sha256(original[1].encode()).hexdigest(), '9e45e81fd5d5a111cfeffe51ad95010cc442679e1bdfcec40fdff759b66b6d99')
        self.assertEqual(self.invoke(['inspect', str(SAMPLE), '--format', 'json']), original)

    def test_missing_token_record_and_zero_are_distinct(self):
        row = json.loads(SAMPLE.read_bytes())
        row['candidate']['tokens'] = row['candidate']['tokens'][1:]
        code, out, err = self.inspect(row)
        self.assertEqual((code, err), (0, ''))
        first = out.split('WETH (', 1)[1].split('AWETH (', 1)[0]
        self.assertIn('Unavailable', first)
        self.assertIn('missing candidate record', first)
        self.assertIn('0', first)

    def test_exact_uint256_negative_units_and_address_identity(self):
        row = json.loads(SAMPLE.read_bytes())
        maximum = 2**256 - 1
        for name, final in [('baseline', maximum), ('candidate', maximum - 1)]:
            token = row[name]['tokens'][0]
            token.update(initial_balance_raw=str(maximum), final_balance_raw=str(final), balance_delta_raw=str(final-maximum))
        row['scenario']['tracked_tokens'][0]['decimals'] = 0
        for name in ['baseline', 'candidate']:
            row[name]['tokens'][0]['decimals'] = 0
            row[name]['tokens'][0]['address'] = row[name]['tokens'][0]['address'].upper().replace('0X', '0x')
        code, out, err = self.inspect(row)
        self.assertEqual((code, err), (0, ''))
        self.assertIn(str(maximum), out)
        self.assertIn(str(maximum - 1), out)
        self.assertIn('-1', out)
        self.assertNotIn('e+', out)
        for name in ['baseline', 'candidate']:
            row[name]['tokens'][0]['decimals'] = 36
        row['scenario']['tracked_tokens'][0]['decimals'] = 36
        code, out, err = self.inspect(row)
        self.assertEqual((code, err), (0, ''))
        self.assertIn('-0.' + '0'*35 + '1', out)

    def test_resealed_false_units_identities_and_arithmetic_fail_finitely(self):
        changes = [
            ('token decimals', lambda r: r['candidate']['tokens'][0].update(decimals=6)),
            ('token identity', lambda r: r['candidate']['tokens'][0].update(address='0x'+'2'*40)),
            ('duplicate token', lambda r: r['candidate']['tokens'].append(copy.deepcopy(r['candidate']['tokens'][0]))),
            ('delta', lambda r: r['candidate']['tokens'][0].update(balance_delta_raw='0')),
            ('integer bool', lambda r: r['candidate']['tokens'][0].update(final_balance_raw=True)),
            ('integer float', lambda r: r['candidate']['tokens'][0].update(final_balance_raw=1.0)),
            ('integer overflow', lambda r: r['candidate']['tokens'][0].update(final_balance_raw=str(2**256))),
            ('integer sign', lambda r: r['candidate']['tokens'][0].update(final_balance_raw='-1')),
            ('integer padding', lambda r: r['candidate']['tokens'][0].update(final_balance_raw='01')),
            ('unsafe symbol', lambda r: r['scenario']['tracked_tokens'][0].update(symbol='WETH\x1b[2J')),
            ('decimals bool', lambda r: r['scenario']['tracked_tokens'][0].update(decimals=True)),
            ('native delta', lambda r: r['comparison'].update(final_balance_delta_wei='1')),
        ]
        for label, change in changes:
            with self.subTest(label=label):
                row = json.loads(SAMPLE.read_bytes()); change(row)
                code, out, err = self.inspect(row)
                self.assertEqual((code, out), (1, ''))
                self.assertTrue(err.startswith('Error: '))
                self.assertNotIn('Traceback', err)

    def test_fixture_legacy_native_and_escaped_free_text(self):
        fixtures = SAMPLE.parent
        for name in ['report.json', 'agent-risk-local.json']:
            code, out, err = self.invoke(['inspect', str(fixtures/name), '--format', 'text'])
            self.assertEqual((code, err), (0, ''))
            self.assertIn('Content hash: verified', out)
            if name == 'report.json': self.assertIn('Synthetic fixture', out)
            else: self.assertIn('No ERC-20 tokens tracked', out)
        row = json.loads(SAMPLE.read_bytes())
        row['scenario']['id'] = 'case\n\x1b[2J'
        row['assumptions'].append('Assumption\n\x1b[31m')
        code, out, err = self.inspect(row)
        self.assertEqual((code, err), (0, ''))
        self.assertNotIn('\x1b', out)
        self.assertIn('\\n\\u001b', out)

    def test_format_arguments_and_bad_integrity(self):
        self.assertEqual(self.invoke(['inspect', str(SAMPLE), '--format', 'yaml'])[0], 2)
        self.assertEqual(self.invoke(['verify', str(SAMPLE), '--format', 'text'])[0], 2)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'bad.json'; row=json.loads(SAMPLE.read_bytes()); row['artifact_id']='0'*64; path.write_text(json.dumps(row))
            code,out,err=self.invoke(['inspect',str(path),'--format','text'])
            self.assertEqual((code,out),(1,'')); self.assertNotIn('Traceback',err)
