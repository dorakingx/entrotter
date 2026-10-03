# Offline Aave account reader

The SDK independently reads the fixed account wrapper without an Engine import,
server, archive access or model call. The [usage example](../../README.md#read-aave-account-impact-offline)
returns immutable exact integer collateral/debt/borrow-capacity/health values,
all four head/configuration/code/error records and typed nested price/trace views.
Internal consistency is distinct from source/execution authentication.

The sample is byte-identical to [Engine88c6cd0's original actual Docker13 record](https://github.com/entrotter/engine/blob/88c6cd0d00f466ed7e870bd57c118aa50984f8b1/evidence/aave-account-impact/position.json),
SHA256cd96e04c837fa1dcc6b6cf009d58adffe3ffdaebc9fbd5b3b900d71cd2912978.
All13 original baseline receipts and12 candidate receipts remain complete;
transaction12 is omitted. Available borrowing increases81628966124 raw base units
with denominator1e8; health factor increases3852169807877337 WAD units. Both
health values remain above one. This is a recorded partial-block aggregate
read-only account comparison, not a new replay, signed loan, liquidation, profit
or proof that the WETH price is the sole cause.

[Source/sample and local validation bindings](summary.json), [full unit log](units.log),
[full security scan](bandit.json), [security scope](security-scope.json) and
[isolated installed-wheel readback](wheel-isolation.json) retain actual checks.
The diagnostic tests deliberately mutate the original sample; they are synthetic,
including missing/configuration/initial/code failure, no-debt uint256-max and
2**200 values. None is additional chain evidence.

Regular-file bounds8MiB, rows64KiB, exact query coverage, duplicate-key refusal,
raw192-byte ABI, thresholds≤10000, provider/oracle address padding and three
seals/classifications are verified before typed access. Missing or unproven views
keep null deltas and finite reasons. Private RPC strings are never accepted as
diagnostics. A producer can forge all data consistently and reseal it. Sender
signatures, provider/state/proxy implementation, full-block/state-root/opcode
execution and financial correctness remain outside this reader's proof.

Current-head CI, CLI/viewer/coordinator integration, human main approval, live
Pages and submission remain separate. Original action/model/HTTP, trace and
price formats are unchanged; no registry package is published.
