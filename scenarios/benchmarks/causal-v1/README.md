# Causal v1: frozen archived-state proposal evaluation

Five Ethereum/Uniswap v3 cases compare identical supplied proposals under three
controllers: execute without a policy, deterministic current-state preflight
risk rule, and a real model asked to follow the same risk objective. The purpose
is to test causal decision integration, failure avoidance and execution overhead.
This is not a test of forecasting, trading profitability or general model skill.

| Block | Split | Minimum USDC output for 1 WETH |
| --- | --- | --- |
| 17,000,000 | Evaluation | 1,500 |
| 18,000,000 | Evaluation | 2,000 |
| 19,000,000 | Previously explored development | 1,000,000 |
| 20,000,000 | Implementation holdout | 3,000 |
| 21,000,000 | Implementation holdout | 3,000 |

`manifest.json` fixes the complete scenario byte hashes, source chain/block/hash,
requested model alias, prompt digest, source-code pins and limits. Commit this
manifest before new protocol-state execution. `source-headers.json` contains the
header-only preparation reads; headers identify sources, not swap outcomes. The
last two cases were not queried for protocol state during preparation. Historical
knowledge and model pretraining may include all periods: these are unused cases
for this implementation, not a claim of unseen market data or a blind backtest.

Both branches override a disposable actor with 10 ETH, wrap 1 ETH and approve
exactly 1 WETH. Only the final swap slot is a decision. All policies use the same
0.3% fee pool, source state, deadline (source timestamp + 3,600 seconds), allowance,
500,000 requested gas and fixed output floor. Shared setup gas is included in
reported total gas but excluded from the decision budget. An action that passes
preflight may still fail when its block is mined 12 seconds later.

WETH/USDC units, gas, failed transactions, runtime and available resource usage
must be recorded for every case. There is no price path or portfolio valuation,
so profit and drawdown remain undefined. Failure and adverse outcomes must remain
in the result set; do not adjust the output floors after observing the holdouts.
Do not present a rule-following model as better than the same direct rule merely
because both avoid a revert. No statistical confidence claim is justified by
five hand-selected cases on one protocol.

Protocol references: [Uniswap Ethereum deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-ethereum-deployments)
and [Circle USDC contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
All actions execute on owned local Anvil forks. Upstream RPC access is read-only;
no live transaction is submitted and no real wallet keys are used. An archive
failure must remain an explicit failure, with no fixture replacement.
