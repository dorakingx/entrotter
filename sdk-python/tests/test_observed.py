"""Recorded native wrapper and engine-sealed synthetic controls; no chain calls."""
from dataclasses import FrozenInstanceError
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from entrotter_sdk import (
    Client, ClientError, ObservedTraceResult, PriceClassification,
    load_observed_trace, verify_observed_trace, verify_trace, verify,
)

DATA = Path(__file__).parent / 'data'

def sample():
    return json.loads((DATA / 'observed-price32.json').read_bytes())

def seal(row):
    body = {key: value for key, value in row.items() if key != 'artifact_id'}
    row['artifact_id'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return row

def control(name):
    row = sample()
    item = next(item for item in json.loads((DATA / 'observed-controls.json').read_bytes()) if item['name'] == name)
    row.update({key: value for key, value in item.items() if key != 'name'})
    return row

class ObservedReaderTests(unittest.TestCase):
    def reject(self, row):
        seal(row)
        self.assertFalse(verify_observed_trace(row))
        with self.assertRaises(ClientError): ObservedTraceResult.parse(row)

    def test_read_supported_price_report_without_engine_or_http(self):
        self.assertEqual(hashlib.sha256((DATA / 'observed-price32.json').read_bytes()).hexdigest(), '7010848300c353310fb78dab7f377daea4226633e49af3c1a384bcb3a579ba9d')
        with patch.object(Client, '_request', side_effect=AssertionError('No HTTP operation')), patch('socket.socket', side_effect=AssertionError('No network')):
            result = load_observed_trace(DATA / 'observed-price32.json')
        self.assertEqual(result.report, sample())
        self.assertTrue(result.trace.baseline_verified)
        self.assertEqual(result.trace.artifact_id, result.report['trace_artifact_id'])
        self.assertEqual(result.classification, PriceClassification(True, True, (), 256292441874, 257082415000, 789973126))
        self.assertEqual([row.price for row in result.observations], [257082415000, 256292441874, 257082415000, 257082415000])
        self.assertEqual([(row.branch, row.phase) for row in result.observations], [('baseline','before'),('baseline','after'),('candidate','before'),('candidate','after')])
        for row, raw in zip(result.observations, result.report['observations']):
            self.assertEqual(row.latest_round_data.answer, row.price)
            self.assertEqual(row.base_unit, 100000000)
            self.assertEqual(row.base_currency, '0x'+'00'*20)
            self.assertEqual(row.source, '0x'+raw['raw']['source'][26:])
            self.assertEqual(row.aggregator, '0x'+raw['raw']['aggregator'][26:])
            self.assertEqual(row.oracle_code.sha256, raw['code']['oracle_code']['sha256'])
            self.assertEqual(row.source_code.bytes, raw['code']['source_code']['bytes'])
            self.assertEqual(row.head.hash, raw['head']['hash'])
            self.assertEqual(row.errors, ())
        rows = result.trace.transactions
        self.assertEqual(len(rows), 32)
        for tx in rows:
            self.assertEqual(tx.baseline.receipt, tx.original_receipt)
            if tx.index == 12:
                self.assertEqual(tx.candidate.status, 'skipped')
                self.assertIsNone(tx.candidate.receipt)
            elif tx.index < 12:
                self.assertEqual(tx.candidate.receipt, tx.original_receipt)
            else:
                self.assertEqual(tx.candidate.receipt.transaction_index, tx.original_receipt.transaction_index-1)
                self.assertEqual(tx.candidate.receipt.cumulative_gas_used, tx.original_receipt.cumulative_gas_used-336752)
                self.assertEqual(tx.candidate.differing_fields, ('cumulativeGasUsed','transactionIndex'))

    def test_large_integer_cross_engine_golden_is_exact(self):
        row = control('large_integer'); self.assertTrue(verify_observed_trace(row))
        parsed = ObservedTraceResult(row)
        self.assertEqual(parsed.classification.candidate_price, 2**200)
        self.assertEqual(parsed.classification.price_difference, 10)
        self.assertEqual(parsed.observations[3].latest_round_data.answer, 2**200)
        self.assertEqual(parsed.report, row)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'large.json';p.write_text(json.dumps(row));self.assertEqual(load_observed_trace(p).report, row)

    def test_incomplete_and_adverse_records_remain_readable_without_false_delta(self):
        for name in ('missing_source','zero_code','future_feed','rpc_missing_head','negative_feed'):
            with self.subTest(name=name):
                row=control(name);result=ObservedTraceResult.parse(row)
                self.assertFalse(result.classification.complete_price_views)
                self.assertIsNone(result.classification.price_difference)
                self.assertTrue(result.classification.unproven_reasons)
                self.assertEqual(result.report, row)
        rpc=ObservedTraceResult(control('rpc_missing_head')).observations[0]
        self.assertIsNone(rpc.head)
        self.assertEqual(rpc.errors[0].query, 'head')
        self.assertEqual(rpc.errors[0].code, 'timeout')
        self.assertEqual(rpc.errors[0].method, 'eth_getBlockByNumber')
        missing=ObservedTraceResult(control('missing_source')).observations[1]
        self.assertIsNone(missing.source)
        self.assertEqual(missing.price, 256292441874)
        self.assertEqual(missing.errors[0].query, 'source')
        self.assertEqual(missing.errors[0].category, 'invalid_response')
        negative=ObservedTraceResult(control('negative_feed'))
        self.assertLess(negative.observations[1].latest_round_data.answer, 0)

    def test_snapshot_and_every_nested_typed_record_are_immutable(self):
        original=sample();result=ObservedTraceResult.parse(original);copy_report=result.report
        original['observations'][0]['raw']['price']='0x'+'00'*32
        copy_report['classification']['price_difference']=0
        copy_report['trace_report']['baseline_verified']=False
        self.assertEqual(result.report, sample())
        row=result.observations[0]
        for value, name, changed in ((result,'_encoded',b'{}'), (row,'price',0), (row.head,'timestamp',0), (row.oracle_code,'bytes',0), (row.latest_round_data,'answer',0), (result.classification,'price_difference',0)):
            with self.assertRaises(FrozenInstanceError): setattr(value,name,changed)
        error=ObservedTraceResult(control('rpc_missing_head')).observations[0].errors[0]
        with self.assertRaises(FrozenInstanceError):error.code='unknown'
        trace=result.trace;trace_copy=trace.report;trace_copy['source']['inputs'].clear()
        self.assertEqual(len(result.trace.transactions),32)

    def test_hash_resealed_contradictions_are_rejected(self):
        mutations = [
            ('profile',lambda r:r.update(profile='custom-code')),
            ('version',lambda r:r.update(observation_version='0.2.0')),
            ('scope',lambda r:r.update(scope='Profit proven')),
            ('nested id',lambda r:r.update(trace_artifact_id='0'*64)),
            ('nested inconsistent receipt',lambda r:r['trace_report']['baseline']['outcomes'][0]['receipt'].update(gasUsed='0x1')),
            ('phase order',lambda r:r['observations'].reverse()),
            ('extra row',lambda r:r['observations'].append(copy.deepcopy(r['observations'][0]))),
            ('unknown selector',lambda r:r['observations'][0]['raw'].update(custom='0x00')),
            ('missing coverage',lambda r:r['observations'][0]['raw'].pop('price')),
            ('failed available query',lambda r:r['observations'][0]['errors'].append({'query':'price','category':'unavailable'})),
            ('address padding',lambda r:r['observations'][0]['raw'].update(source='0x01'+'00'*31)),
            ('round width',lambda r:r['observations'][0]['raw'].update(latest_round_data='0x'+'00'*159)),
            ('round id overflow',lambda r:r['observations'][0]['raw'].update(latest_round_data='0x'+'ff'*32+r['observations'][0]['raw']['latest_round_data'][66:])),
            ('parent hash',lambda r:r['observations'][0]['head'].update(hash='0x'+'00'*32)),
            ('post timestamp',lambda r:r['observations'][1]['head'].update(timestamp=0)),
            ('bool timestamp',lambda r:r['observations'][0]['head'].update(timestamp=True)),
            ('code bound',lambda r:r['observations'][0]['code']['oracle_code'].update(bytes=65537)),
            ('code hash',lambda r:r['observations'][0]['code']['oracle_code'].update(sha256='bad')),
            ('false delta',lambda r:r['classification'].update(price_difference=1)),
            ('false completeness',lambda r:r['classification'].update(complete_price_views=False)),
            ('extra classifier',lambda r:r['classification'].update(profit=1)),
            ('oversized observations',lambda r:r['observations'][0]['errors'].append({'query':'x'*65536,'category':'unavailable'})),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                row=sample();mutate(row)
                if name=='nested inconsistent receipt':
                    seal(row['trace_report']);row['trace_artifact_id']=row['trace_report']['artifact_id']
                self.reject(row)

    def test_rpc_diagnostics_are_finite_and_query_bound(self):
        for variant in ('method','message','duplicate','code','category'):
            with self.subTest(variant=variant):
                row=control('rpc_missing_head');error=row['observations'][0]['errors'][0]
                if variant=='method':error['diagnostics']['method']='eth_sendRawTransaction'
                elif variant=='message':error['diagnostics']['message']='private URL'
                elif variant=='code':error['diagnostics']['code']='provider secret'
                elif variant=='category':error['category']='custom'
                else:row['observations'][0]['errors'].append(copy.deepcopy(error))
                self.reject(row)

    def test_hash_and_family_separation(self):
        row=sample();row['artifact_id']='0'*64
        self.assertFalse(verify_observed_trace(row))
        self.assertFalse(verify_trace(sample()))
        self.assertFalse(verify(sample()))
        self.assertFalse(verify_observed_trace(sample()['trace_report']))
        for value in (None,[],{'unexpected':True}):self.assertFalse(verify_observed_trace(value))

    def test_regular_file_duplicate_key_malformed_and_size_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'report.json'
            raw=(DATA/'observed-price32.json').read_text()
            for text in ('{"profile":"a","profile":"b"}',raw.replace('"observations": [','"observations": null, "observations": [',1),'NaN','{"x":'+ '1'*513+'}', '['*1200+']'*1200, ' '*(8*1024*1024+1)):
                p.write_text(text)
                with self.assertRaises(ClientError):load_observed_trace(p)
            for name in (Path(directory),Path(directory)/'missing'):
                with self.assertRaises(ClientError):load_observed_trace(name)
            if hasattr(os,'mkfifo'):
                fifo=Path(directory)/'fifo';os.mkfifo(fifo)
                with self.assertRaises(ClientError):load_observed_trace(fifo)

    def test_in_memory_cycle_nan_and_wrong_scalar_are_safe_errors(self):
        cycle={};cycle['cycle']=cycle
        for row in (cycle, {'nan':float('nan')},'string'):
            self.assertFalse(verify_observed_trace(row))
            with self.assertRaises(ClientError):ObservedTraceResult.parse(row)
