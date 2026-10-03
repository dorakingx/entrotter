"""Original recorded account replay and explicitly synthetic diagnostic mutations."""
from dataclasses import FrozenInstanceError
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from entrotter_sdk import Client, ClientError, PositionResult, load_position, verify_position

DATA = Path(__file__).parent / "data/aave-account-position13.json"
FIELDS = ("total_collateral_base", "total_debt_base", "available_borrows_base",
          "liquidation_threshold_bps", "ltv_bps", "health_factor_wad")


def sample():
    return json.loads(DATA.read_bytes())


def seal(row):
    body = {k:v for k,v in row.items() if k != "artifact_id"}
    row["artifact_id"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return row


def raw(values):
    return "0x" + "".join(values[k].to_bytes(32, "big").hex() for k in FIELDS)


def unproven(row, reasons):
    row["classification"] = {
        "complete_account_views": False, "unproven_reasons": sorted(reasons),
        "baseline": None, "candidate": None, "differences": {k:None for k in FIELDS},
        "baseline_health_status": "unproven", "candidate_health_status": "unproven",
        "base_unit": None, "health_factor_unit": 10**18,
    }
    return seal(row)


class PositionReaderTests(unittest.TestCase):
    def reject(self, row):
        seal(row)
        self.assertFalse(verify_position(row))
        with self.assertRaises(ClientError): PositionResult.parse(row)

    def test_original_13_receipts_exact_integer_values_and_all_four_views(self):
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), "cd96e04c837fa1dcc6b6cf009d58adffe3ffdaebc9fbd5b3b900d71cd2912978")
        with patch.object(Client, "run", side_effect=AssertionError("HTTP forbidden")), patch.dict("sys.modules", {"entrotter_engine":None}):
            result = load_position(DATA)
        self.assertEqual(result.artifact_id, "5c67c4bcf4fc4de614153fc86c0c3814c188b4551212ce55ec9f533fa3e2ad4f")
        self.assertEqual(result.profile, "aave-v3-ethereum-account")
        self.assertEqual(result.account, "0x16aa9154557f1394089db90d3cbe212d9a7f33bb")
        self.assertTrue(result.trace.baseline_verified)
        self.assertEqual(len(result.trace.transactions), 13)
        self.assertEqual(result.prices.classification.price_difference, 789973126)
        c = result.classification
        self.assertTrue(c.complete_account_views)
        self.assertEqual(c.differences.available_borrows_base, 81628966124)
        self.assertEqual(c.differences.health_factor_wad, 3852169807877337)
        self.assertEqual(c.baseline.total_debt_base, 16199140199548)
        self.assertEqual(c.candidate.total_debt_base, 16219364581293)
        self.assertEqual((c.base_unit, c.health_factor_unit), (10**8, 10**18))
        self.assertEqual(c.baseline_health_status, "at_or_above_one")
        self.assertEqual([(x.branch,x.phase) for x in result.observations], [("baseline","before"),("baseline","after"),("candidate","before"),("candidate","after")])
        for i,row in enumerate(result.observations):
            self.assertEqual(row.account, result.account)
            self.assertEqual(row.head, result.prices.observations[i].head)
            self.assertEqual(row.provider,"0x2f39d218133afab8f2b819b1066c7e434ad94e9e")
            self.assertEqual(row.oracle,"0x54586be62e3c3580375ae3723c145253060ca0c2")
            self.assertEqual(row.pool_code.bytes,2400)
            self.assertEqual(row.errors,())

    def test_nested_mutation_and_typed_values_cannot_change_validated_snapshot(self):
        source = sample(); result = PositionResult.parse(source)
        source["observations"][0]["account"] = "0x" + "11"*20
        copy_report = result.report; copy_report["price_report"]["trace_report"]["baseline_verified"] = False
        copy_plan = result.plan; copy_plan["account"] = "0x" + "22"*20
        self.assertEqual(result.report, sample())
        with self.assertRaises(FrozenInstanceError): result.observations[0].values.total_debt_base = 0
        with self.assertRaises(FrozenInstanceError): result.classification.differences.available_borrows_base = 0
        with self.assertRaises(FrozenInstanceError): result.classification.candidate.health_factor_wad = 0

    def test_resealed_binding_profile_plan_head_and_classification_mismatches(self):
        changes = [
            lambda x:x.update(profile="arbitrary-profile"),
            lambda x:x.update(scope="profit"),
            lambda x:x["plan"].update(account="0x"+"11"*20),
            lambda x:x["plan"].update(url="https://private.invalid"),
            lambda x:x["plan"].update(position_version="9"),
            lambda x:x["plan"]["trace"].update(skip_indices=[]),
            lambda x:x["observations"][1]["head"].update(timestamp=x["observations"][1]["head"]["timestamp"]+1),
            lambda x:x["observations"][0].update(branch="candidate"),
            lambda x:x["classification"]["differences"].update(available_borrows_base=0),
            lambda x:x["classification"].update(complete_account_views=1),
            lambda x:x["classification"].update(base_unit=10**18),
            lambda x:x["price_report"]["classification"].update(price_difference=0),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                row=sample();change(row);self.reject(row)

    def test_exact_abi_word_width_padding_threshold_and_zero_debt_sentinel(self):
        values=sample()["classification"]["baseline"]
        for field,value in [("liquidation_threshold_bps",10001),("ltv_bps",10001),("total_debt_base",0)]:
            row=sample();v=copy.deepcopy(values);v[field]=value;row["observations"][1]["raw"]=raw(v);self.reject(row)
        for value in ["0x", "0x"+"00"*191, "0x"+"00"*193, True, "0x"+"gg"*192]:
            row=sample();row["observations"][0]["raw"]=value;self.reject(row)
        row=sample();row["observations"][0]["provider"]="0x"+"01"+"00"*31;self.reject(row)

    def test_missing_read_is_valid_unproven_and_keeps_finite_error(self):
        row=sample();row["observations"][1]["raw"]=None
        row["observations"][1]["errors"]=[{"query":"account_data","category":"rpc_error","diagnostics":{"code":"timeout","method":"eth_call"}}]
        result=PositionResult.parse(unproven(row,["incomplete_account_views"]))
        self.assertFalse(result.classification.complete_account_views)
        self.assertIsNone(result.classification.differences.available_borrows_base)
        self.assertIsNone(result.observations[1].values)
        self.assertEqual(result.observations[1].errors[0].code,"timeout")
        self.assertEqual(result.observations[1].errors[0].method,"eth_call")

    def test_configuration_initial_values_and_code_changes_prevent_economic_delta(self):
        changes=[
            (lambda x:x["observations"][1].update(oracle="0x"+"00"*12+"11"*20),["pool_oracle_binding_unproven"]),
            (lambda x:x["observations"][1]["code"].update(sha256="0"*64),["pool_code_identity_changed"]),
            (lambda x:x["observations"][0].update(raw=x["observations"][1]["raw"]),["initial_account_views_differ"]),
            (lambda x:x["observations"][1]["code"].update(bytes=0),["pool_code_identity_changed","pool_code_unavailable"]),
        ]
        for change,reasons in changes:
            with self.subTest(reasons=reasons):
                row=sample();change(row);r=PositionResult.parse(unproven(row,reasons))
                self.assertIsNone(r.classification.baseline)
                self.assertEqual(r.classification.unproven_reasons,tuple(sorted(reasons)))

    def test_diagnostic_coverage_bound_and_private_message_rejected(self):
        variants=[[],[{"query":"account_data","category":"unavailable"}],
            [{"query":"account_data","category":"rpc_error","diagnostics":{"code":"timeout","method":"eth_sendRawTransaction"}}],
            [{"query":"account_data","category":"invalid_response","message":"https://secret.invalid"}],
            [{"query":"account_data","category":"invalid_response"}]*2]
        for errors in variants:
            row=sample();row["observations"][1]["raw"]=None;row["observations"][1]["errors"]=errors;self.reject(unproven(row,["incomplete_account_views"]))
        row=sample();row["observations"][1]["errors"]=[{"query":"account_data","category":"invalid_response"}];self.reject(row)

    def test_no_debt_raw_max_has_no_normalized_health_difference(self):
        row=sample();values=copy.deepcopy(row["classification"]["baseline"])
        values.update(total_debt_base=0,health_factor_wad=2**256-1)
        for x in row["observations"]:x["raw"]=raw(values)
        row["classification"].update(baseline=copy.deepcopy(values),candidate=copy.deepcopy(values),
            differences={k:None if k=="health_factor_wad" else 0 for k in FIELDS},baseline_health_status="no_debt",candidate_health_status="no_debt")
        result=PositionResult.parse(seal(row))
        self.assertEqual(result.observations[1].values.health_factor_wad,2**256-1)
        self.assertEqual(result.classification.candidate_health_status,"no_debt")
        self.assertIsNone(result.classification.differences.health_factor_wad)

    def test_large_uints_and_liquidation_boundary_remain_exact(self):
        for health,status in [(10**18-1,"below_one"),(10**18,"at_or_above_one"),(2**200,"at_or_above_one")]:
            row=sample();values=copy.deepcopy(row["classification"]["baseline"])
            values.update(total_collateral_base=2**200,available_borrows_base=2**200,health_factor_wad=health)
            for x in row["observations"]:x["raw"]=raw(values)
            row["classification"].update(baseline=copy.deepcopy(values),candidate=copy.deepcopy(values),differences={k:0 for k in FIELDS},baseline_health_status=status,candidate_health_status=status)
            result=PositionResult.parse(seal(row))
            self.assertEqual(result.classification.baseline.total_collateral_base,2**200)
            self.assertEqual(result.classification.candidate_health_status,status)
            self.assertEqual(result.observations[0].values.health_factor_wad,health)

    def test_bound_duplicate_invalid_json_and_nonblocking_special_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"input.json"
            for data in [b'{"position_version":"0.1.0","position_version":"0.1.0"}',b' '* (8*1024*1024+1),b'{',b'['*10000,b'{"n":'+b'1'*513+b'}',b'\xff']:
                p.write_bytes(data)
                with self.assertRaises(ClientError):load_position(p)
            if hasattr(os,"mkfifo"):
                p.unlink();os.mkfifo(p)
                with self.assertRaises(ClientError):load_position(p)
            with self.assertRaises(ClientError):load_position(td)
            with self.assertRaises(ClientError):load_position(Path(td)/"missing")

if __name__ == "__main__":unittest.main()
