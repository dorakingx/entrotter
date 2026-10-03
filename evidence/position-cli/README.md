# CLI account replay and offline inspection

The [usage commands](../../README.md#compare-historical-aave-account-impact)
run a closed account plan through the optional default Engine and inspect it
through the standalone SDK. Existing v0.1 action/model and price commands remain
unchanged; the account format adds no HTTP, native fallback or metadata-selected
executable/ABI/contract/RPC.

The recorded inspection sample is byte-identical to SDKba4 and Engine88c6's
[original defaultDocker13 result](https://github.com/entrotter/engine/blob/88c6cd0d00f466ed7e870bd57c118aa50984f8b1/evidence/aave-account-impact/position.json),
SHAcd96e04c837fa1dcc6b6cf009d58adffe3ffdaebc9fbd5b3b900d71cd2912978.
New CLI actual execution is a separate experiment, with complete original13
receipts/12remaining+skip12 and all four account/price/config/code/head records
compared against that golden record. Original signatures, nonces, timestamps,
source and plan remain intact; only runtime/content IDs may differ. No new
model call, provider/state/proxy authentication or whole-block proof is claimed.

[Source/sample and validation bindings](summary.json), [full offline/unit log](units.log),
[full actual Docker log](actual-tests.log), [current actual result](actual/position.json),
[launch source/image](actual/launch.json), [default result summary](actual/success-summary.json),
[missing worker](actual/missing-worker.json) and [cancellation](actual/cancelled.json)
retain the exact results. [Full security scan](bandit.json), [scope](security-scope.json)
and [installed wheel evidence](wheel-isolation.json) are distinct from chain tests.
Dispatch fakes and invalid-input mutations are explicitly synthetic.

Available borrowing differs81628966124 raw base units (denominator1e8); health
3852169807877337 WAD units (denominator1e18), both health factors above one.
This is aggregate account dependence, not token balances, profit, a signed loan,
liquidation or evidence that WETH price is the sole cause. Missing/incomplete
configuration or views retain null differences and reasons; no-debt rawmax has
no normalized health delta. Status0 reports valid inspection/export, not financial
correctness. All values can still be forged consistently and resealed.

Engine150/worker180 caps are unchanged. Native host preparation, configured
running Docker/VM/cache/image storage and authenticated archive truth remain
operator scope; kernel/resource evidence belongs to the separate Engine controls.
Cancellation after atomic commit cannot roll it back; forced death retains the
shared export ledger's documented behavior. Frozen original agent/fixed-price
CI gates stay intact; mandatory new actual3 uses separately pinned SDK/Engine.
Current-head CI, coordinator integration, human main approval, Pages and submission
are separate. Packages remain unpublished.
