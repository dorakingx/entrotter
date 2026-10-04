"""Independent ABI checks; archived execution is recorded separately, never mocked."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest

from entrotter_engine.defi import (
    aave_supply,
    aave_borrow_variable,
    approve,
    wrap_native,
)
from entrotter_engine.models import ValidationError, validate

POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
ACTOR = "0x1000000000000000000000000000000000000001"


class AaveActionTests(unittest.TestCase):
    @unittest.skipUnless(
        shutil.which("cast"), "Foundry cast required for independent ABI comparison"
    )
    def test_supply_and_variable_borrow_match_solidity_abi(self):
        for amount, referral in [(1, 0), (2**255 + 99, 65535)]:
            for helper, signature, args in [
                (
                    aave_supply,
                    "supply(address,uint256,address,uint16)",
                    [WETH, str(amount), ACTOR, str(referral)],
                ),
                (
                    aave_borrow_variable,
                    "borrow(address,uint256,uint256,uint16,address)",
                    [WETH, str(amount), "2", str(referral), ACTOR],
                ),
            ]:
                with self.subTest(signature=signature, amount=amount):
                    actual = helper(
                        pool=POOL,
                        asset=WETH,
                        amount=amount,
                        on_behalf_of=ACTOR,
                        referral_code=referral,
                    )
                    expected = subprocess.check_output(
                        ["cast", "calldata", signature, *args], text=True
                    ).strip()
                    self.assertEqual(actual["data"], expected)
                    self.assertEqual(actual["to"], POOL)
                    self.assertEqual(actual["gas"], 500000)
                    self.assertNotIn("value_wei", actual)

    def test_amount_referral_and_addresses_are_bounded_before_any_execution(self):
        for helper in [aave_supply, aave_borrow_variable]:
            base = {"pool": POOL, "asset": WETH, "amount": 1, "on_behalf_of": ACTOR}
            for field, values in {
                "amount": [-1, 2**256, True, "1", 0.5],
                "referral_code": [-1, 65536, True, "0"],
                "pool": ["0x123", None],
                "asset": ["0x" + "g" * 40],
                "on_behalf_of": [ACTOR + "00"],
            }.items():
                for value in values:
                    with (
                        self.subTest(helper=helper.__name__, field=field, value=value),
                        self.assertRaises(ValidationError),
                    ):
                        helper(**{**base, field: value})
            self.assertEqual(
                helper(**{**base, "pool": "0x" + POOL[2:].upper()})["to"], POOL
            )

    def test_borrow_mode_is_fixed_and_zero_amount_keeps_protocol_semantics(self):
        kwargs = {"pool": POOL, "asset": WETH, "amount": 0, "on_behalf_of": ACTOR}
        for helper in [aave_supply, aave_borrow_variable]:
            self.assertTrue(helper(**kwargs)["data"].startswith("0x"))
        with self.assertRaises(TypeError):
            aave_borrow_variable(**kwargs, interest_rate_mode=1)

    def test_fork_example_uses_current_builders_and_identical_proposals(self):
        scenario = json.loads(
            (Path(__file__).parent / "data/aave-borrow-actions.json").read_text()
        )
        validate(scenario)
        self.assertEqual(scenario["mode"], "evm-fork")
        self.assertEqual(
            scenario["source"],
            {
                "chain_id": 1,
                "block_number": 18999892,
                "block_hash": "0xafd6a8c681f5e3b6ae9cba963e4b8dd7e3c9bf76fe45e0c3e145ccb2918b2ba6",
            },
        )
        self.assertEqual(scenario.get("local_contracts", {}), {})
        expected = [
            wrap_native(WETH, 10**19),
            approve(WETH, POOL, 10**19),
            aave_supply(pool=POOL, asset=WETH, amount=10**19, on_behalf_of=ACTOR),
            aave_borrow_variable(
                pool=POOL, asset=WETH, amount=9 * 10**18, on_behalf_of=ACTOR
            ),
            aave_borrow_variable(
                pool=POOL, asset=WETH, amount=10**18, on_behalf_of=ACTOR
            ),
        ]
        self.assertEqual(
            scenario["steps"], [{"baseline": a, "candidate": a} for a in expected]
        )
        self.assertEqual(scenario["actor"], ACTOR)
        self.assertEqual(scenario["actor_balance_wei"], str(2 * 10**19))
        self.assertEqual(len(scenario["tracked_tokens"]), 3)
