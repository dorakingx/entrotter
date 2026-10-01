"""Actual frozen reports plus resealed inconsistent data, never new chain calls."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from entrotter_sdk import Client, ClientError, RunResult, TraceResult, load_trace, verify, verify_trace
from entrotter_sdk.trace import _rlp, _signed_metadata

DATA = Path(__file__).parent / 'data'

def report():
    return json.loads((DATA / 'canonical-mainnet-prefix-four.result.json').read_text())

def encode_rlp(value):
    # Test-only encoder for bounded envelope metadata mutations, not signatures.
    if isinstance(value, int):
        value=value.to_bytes((value.bit_length()+7)//8,'big')
    if isinstance(value,list):
        body=b''.join(encode_rlp(v) for v in value); offset=0xc0
    else:
        if len(value)==1 and value[0]<128:return value
        body=value; offset=0x80
    if len(body)<=55:return bytes([offset+len(body)])+body
    length=len(body).to_bytes((len(body).bit_length()+7)//8,'big')
    return bytes([offset+55+len(length)])+length+body

def seal(value):
    body = {k:v for k,v in value.items() if k != 'artifact_id'}
    value['artifact_id'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return value

def set_path(value, path, replacement):
    for key in path[:-1]: value = value[key]
    value[path[-1]] = replacement

def unmatched_baseline(value, first_status):
    # Synthetic reported outcomes derived from frozen inputs, not executed evidence.
    base = value['baseline']; outcomes = base['outcomes']
    outcomes[0] = {'index':0, 'hash':outcomes[0]['hash'], 'status':first_status}
    if first_status == 'rejected':
        outcomes[3] = {'index':3, 'hash':outcomes[3]['hash'], 'status':'nonce_conflict', 'expected_nonce':5522, 'original_nonce':5523}
    cumulative = 0; position = 0
    for outcome, source in zip(outcomes, value['source']['inputs']):
        if outcome['status'] != 'executed': continue
        receipt = outcome['receipt']
        cumulative += int(receipt['gasUsed'],16)
        receipt['cumulativeGasUsed'] = hex(cumulative)
        receipt['transactionIndex'] = hex(position); position += 1
        outcome['differing_fields'] = [k for k in receipt if receipt[k] != source['original_receipt'][k]]
    base['matches_original_receipts'] = False; value['baseline_verified'] = False
    return seal(value)

class TraceReaderTests(unittest.TestCase):
    def assertRejected(self, value):
        seal(value)
        self.assertFalse(verify_trace(value))
        with self.assertRaises(ClientError): TraceResult.parse(value)

    def test_actual_four_prefix_typed_rows_preserve_adverse_outcomes(self):
        value = report()
        with patch.object(Client, '_request', side_effect=AssertionError('No HTTP operation')):
            parsed = TraceResult.parse(value)
        self.assertEqual(parsed.report, value)
        self.assertTrue(parsed.baseline_verified)
        self.assertEqual(parsed.runtime_seconds, 14.539113)
        rows = parsed.transactions
        self.assertEqual([r.original_receipt.gas_used for r in rows], [208144,234720,175305,178980])
        self.assertEqual([len(r.original_receipt.logs) for r in rows], [8,10,6,8])
        self.assertEqual([r.candidate.status for r in rows], ['skipped','executed','executed','nonce_conflict'])
        self.assertEqual(rows[1].candidate.receipt.gas_used, 245136)
        self.assertEqual(rows[1].candidate.differing_fields, ('gasUsed','cumulativeGasUsed','transactionIndex','logs'))
        self.assertIsNone(rows[3].candidate.receipt)
        self.assertEqual((rows[3].candidate.expected_nonce, rows[3].candidate.original_nonce), (5522,5523))

    def test_original_one_prefix_and_separate_v01_contract(self):
        value = json.loads((DATA / 'canonical-mainnet-prefix.result.json').read_text())
        self.assertTrue(verify_trace(value)); self.assertFalse(verify(value))
        with self.assertRaises(ClientError): RunResult.parse(value)
        self.assertEqual(len(TraceResult.parse(value).transactions), 1)
        from test_sdk import artifact
        self.assertFalse(verify_trace(artifact()))
        self.assertTrue(verify(artifact()))

    def test_hash_tamper_versions_and_nonfinite_numbers(self):
        value = report(); value['runtime_seconds'] = 1; self.assertFalse(verify_trace(value))
        for path, bad in [(['trace_version'],'1'), (['execution_kind'],'fixture'),
                          (['plan','trace_version'],'1'), (['runtime_seconds'],True),
                          (['runtime_seconds'],-1), (['runtime_seconds'],float('inf')),
                          (['runtime_seconds'],float('nan'))]:
            value = report(); set_path(value,path,bad)
            self.assertFalse(verify_trace(value))
            with self.assertRaises(ClientError): TraceResult.parse(value)

    def test_reordered_object_keys_keep_same_hash_and_differences(self):
        value = json.loads(json.dumps(report()), object_pairs_hook=lambda pairs:dict(reversed(pairs)))
        self.assertTrue(verify_trace(value))
        self.assertEqual(TraceResult.parse(value).artifact_id, report()['artifact_id'])

    def test_exact_shapes_source_pins_and_prefix_order(self):
        cases = [(['unexpected'],'x'), (['plan','source','chain_id'],True),
                 (['source','parent','chain_id'],2), (['source','parent','block_number'],19000000),
                 (['plan','source','block_hash'],'latest'), (['source','header','timestamp'],1710338135),
                 (['source','header','gas_limit'],30000001), (['source','block_transaction_count'],3),
                 (['plan','through_index'],True), (['plan','through_index'],32),
                 (['plan','skip_indices'],[1,0]), (['plan','skip_indices'],[0,0]),
                 (['plan','skip_indices'],[4]), (['source','inputs',1,'index'],0),
                 (['source','inputs',1,'hash'],report()['source']['inputs'][0]['hash']),
                 (['source','inputs',0,'nonce'],5523), (['source','inputs',0,'raw'],'0x03c0')]
        for path,bad in cases:
            with self.subTest(path=path,bad=bad):
                value=report(); set_path(value,path,bad); self.assertRejected(value)
        value=report(); del value['source']['header']['base_fee']; self.assertRejected(value)

    def test_resealed_receipt_identities_types_targets_and_logs(self):
        cases = [('transactionHash','0x'+'11'*32), ('from','0x'+'12'*20),
                 ('type','0x1'), ('to','0x'+'13'*20), ('logsBloom','0x00'),
                 ('status','0x2'), ('gasUsed','0x00'), ('gasUsed','0x'+'f'*65),
                 ('logs',[{'address':'0x'+'11'*20,'topics':['0x'+'aa'*32]*5,'data':'0x'}])]
        for name,bad in cases:
            for branch in ['source','baseline','candidate']:
                with self.subTest(name=name,branch=branch):
                    value=report()
                    if branch=='source': value[branch]['inputs'][1]['original_receipt'][name]=bad
                    else: value[branch]['outcomes'][1]['receipt'][name]=bad
                    self.assertRejected(value)

    def test_resealed_difference_fields_and_match_flags(self):
        cases = [(['candidate','outcomes',1,'differing_fields'],[]),
                 (['candidate','outcomes',1,'differing_fields'],['gasUsed','gasUsed']),
                 (['candidate','outcomes',1,'differing_fields'],['unknown']),
                 (['candidate','matches_original_receipts'],True),
                 (['baseline','matches_original_receipts'],False),
                 (['baseline_verified'],False), (['baseline_verified'],1),
                 (['candidate','outcomes',1,'receipt','cumulativeGasUsed'],'0x1'),
                 (['candidate','outcomes',1,'receipt','transactionIndex'],'0x1')]
        for path,bad in cases:
            with self.subTest(path=path):
                value=report(); set_path(value,path,bad); self.assertRejected(value)

    def test_skip_and_same_parent_nonce_cannot_be_concealed(self):
        for field,bad in [('original_nonce',5522), ('expected_nonce',5523)]:
            value=report(); value['candidate']['outcomes'][3][field]=bad; self.assertRejected(value)
        value=report(); value['plan']['skip_indices']=[]; self.assertRejected(value)
        value=report(); value['candidate']['outcomes'][3]=deepcopy(value['baseline']['outcomes'][3])
        receipt=value['candidate']['outcomes'][3]['receipt']
        receipt['transactionIndex']='0x2'
        receipt['cumulativeGasUsed']=hex(245136+185721+178980)
        value['candidate']['outcomes'][3]['differing_fields']=['cumulativeGasUsed','transactionIndex']
        self.assertRejected(value)

    def test_unmatched_rejected_baseline_is_readable_without_false_verification(self):
        value=unmatched_baseline(report(),'rejected')
        parsed=TraceResult.parse(value)
        self.assertFalse(parsed.baseline_verified)
        self.assertEqual(parsed.transactions[0].baseline.status,'rejected')
        self.assertEqual(parsed.transactions[3].baseline.expected_nonce,5522)

    def test_not_mined_queued_input_advances_only_its_own_branch_nonce(self):
        value=unmatched_baseline(report(),'not_mined')
        parsed=TraceResult.parse(value)
        self.assertFalse(parsed.baseline_verified)
        self.assertEqual(parsed.transactions[3].baseline.status,'executed')
        self.assertEqual(parsed.transactions[3].candidate.status,'nonce_conflict')

    def test_all_omissions_preserve_typed_absence(self):
        value=report(); value['plan']['skip_indices']=[0,1,2,3]
        value['candidate']['outcomes']=[{'index':i,'hash':tx['hash'],'status':'skipped'} for i,tx in enumerate(value['source']['inputs'])]
        parsed=TraceResult.parse(seal(value))
        self.assertTrue(parsed.baseline_verified)
        self.assertTrue(all(row.candidate.receipt is None for row in parsed.transactions))

    def test_caller_report_and_typed_rows_cannot_mutate_snapshot(self):
        value=report(); parsed=TraceResult.parse(value); ident=parsed.artifact_id
        value['candidate']['outcomes'][3]['expected_nonce']=0
        copy=parsed.report; copy['baseline_verified']=False
        self.assertTrue(parsed.baseline_verified); self.assertEqual(parsed.artifact_id,ident)
        self.assertEqual(parsed.transactions[3].candidate.expected_nonce,5522)
        with self.assertRaises(FrozenInstanceError): parsed.transactions[1].candidate.receipt.gas_used=0
        self.assertNotIn(ident,repr(parsed))

    def test_bounds_status_types_and_duplicate_fields(self):
        for path,bad in [(['candidate','outcomes',0,'status'],[]), (['candidate','outcomes',0,'status'],{}),
                         (['assumptions'],['x'*4001]), (['source','header','base_fee'],2**256),
                         (['source','inputs',0,'raw'],'0x'+'00'*131072)]:
            value=report(); set_path(value,path,bad); self.assertRejected(value)
        value=report(); value['source']['header']['base_fee']=2**256-1
        self.assertTrue(verify_trace(seal(value))) # Integer metadata, not execution truth.
        value=report(); value['self']=value; self.assertFalse(verify_trace(value))

    def test_rlp_noncanonical_and_unsupported_shapes(self):
        for raw in ['0x', '0x00', '0x03c0', '0x01f800', '0x02c0', '0x81ff', '0xf90001c0', '0xc18100']:
            with self.subTest(raw=raw),self.assertRaises(ValueError): _signed_metadata(raw)

    def test_original_signed_legacy_access_list_and_dynamic_fee_metadata(self):
        value=json.loads((DATA/'signed-local-inputs.json').read_text())
        self.assertEqual(value['kind'],'synthetic')
        targets=['0x'+'ef'*20,'0x'+'ab'*20,'0x'+'cd'*20]
        self.assertEqual([_signed_metadata(raw)[:3] for raw in value['raw_transactions']],
                         [(i,i,target) for i,target in enumerate(targets)])

    def test_supported_unprotected_legacy_and_total_access_keys(self):
        raws=json.loads((DATA/'signed-local-inputs.json').read_text())['raw_transactions']
        fields,_=_rlp(bytes.fromhex(raws[0][2:]))
        for parity in [27,28,37,38]:
            fields[-3]=parity
            self.assertEqual(_signed_metadata('0x'+encode_rlp(fields).hex())[:3],
                             (0,0,'0x'+'ef'*20))
        fields[-3]=39
        with self.assertRaises(ValueError):_signed_metadata('0x'+encode_rlp(fields).hex())
        fields,_=_rlp(bytes.fromhex(raws[1][4:]))
        fields[-4]=[[bytes.fromhex('ab'*20),[bytes(32)]*32] for _ in range(8)]
        self.assertEqual(_signed_metadata('0x01'+encode_rlp(fields).hex())[0],1)
        fields[-4][0][1].append(bytes(32))
        with self.assertRaises(ValueError):_signed_metadata('0x01'+encode_rlp(fields).hex())

    def test_resealed_impossible_gas_revert_and_contract_receipts(self):
        original=json.loads((DATA/'canonical-mainnet-prefix.result.json').read_text())
        self.assertEqual(_signed_metadata(original['source']['inputs'][0]['raw'])[3],297348)
        def update_receipts(value, change):
            for receipt in [value['source']['inputs'][0]['original_receipt'],
                            value['baseline']['outcomes'][0]['receipt']]:
                receipt.update(change)
        for change in [{'gasUsed':hex(30000000),'cumulativeGasUsed':hex(30000000)},
                       {'status':'0x0'}, {'contractAddress':'0x'+'12'*20}]:
            value=deepcopy(original);update_receipts(value,change);self.assertRejected(value)
        value=deepcopy(original)
        update_receipts(value,{'status':'0x0','logs':[],'logsBloom':'0x'+'00'*256})
        self.assertTrue(verify_trace(seal(value))) # Consistent fabricated revert, not EVM proof.
        value['source']['inputs'][0]['original_receipt']['logsBloom']='0x'+'01'*256
        value['baseline']['outcomes'][0]['receipt']['logsBloom']='0x'+'01'*256
        self.assertRejected(value)

    def test_regular_file_import_duplicate_keys_bad_json_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'trace.json'; path.write_bytes((DATA/'canonical-mainnet-prefix-four.result.json').read_bytes())
            self.assertEqual(load_trace(path).report,report())
            path.write_text('{"a":1,"a":2}')
            with self.assertRaises(ClientError): load_trace(path)
            path.write_text('{')
            with self.assertRaises(ClientError): load_trace(path)
            with path.open('wb') as output:output.write(b' '* (8*1024*1024+1))
            with self.assertRaises(ClientError): load_trace(path)
            with self.assertRaises(ClientError): load_trace(Path(tmp))
            with self.assertRaises(ClientError): load_trace(Path(tmp)/'missing')
            if hasattr(os,'mkfifo'):
                fifo=Path(tmp)/'pipe'; os.mkfifo(fifo)
                with self.assertRaises(ClientError): load_trace(fifo)

if __name__=='__main__': unittest.main()
