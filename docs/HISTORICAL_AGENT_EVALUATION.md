# Frozen archived-state agent comparison

The model matched the deterministic preflight rule on all five source cases and took longer in every case. This benchmark demonstrates constrained decision integration and exact recorded replay; it does not demonstrate an advantage for an LLM.

| Ethereum block | Split | Prescribed final swap | Risk/model choice | Prescribed gas | Risk/model gas | Risk / model seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 17,000,000 | evaluation | success | execute | 216,505 | 216,505 | 9.111 / 13.806 |
| 18,000,000 | evaluation | reverted | hold | 234,844 | 91,090 | 10.125 / 13.662 |
| 19,000,000 | development | reverted | hold | 222,793 | 91,090 | 8.533 / 12.549 |
| 20,000,000 | holdout | success | execute | 221,862 | 221,862 | 10.877 / 15.779 |
| 21,000,000 | holdout | reverted | hold | 222,785 | 91,090 | 10.621 / 17.789 |

Times are single paired baseline/candidate runs, including archive reads and model generation where applicable. Run order is fixed, network/cache variability is uncontrolled, and no statistical confidence interval is claimed. Shared wrap/approve gas is included. These are five independent experiments, not an aggregate portfolio.

At block 17M, the executed 1 WETH swap returned 1,860.850781 USDC; at block 20M it returned 3,806.643610 USDC. In the other three cases the prescribed swap reverted, while the policies held and retained 1 WETH after setup. There is no future price path or valuation model: balances are not profit, and drawdown is undefined.

## Freeze and provenance

The [scenario freeze](https://github.com/entrotter/scenarios/commit/1ce15d9) preceded every new protocol-state execution. Manifest SHA-256 is `f147489fcde8de04be6a9de459fe011018488bd75e66a84de55f6a8a35ed030e`. Only headers were queried during preparation. Cases 20M and 21M were unused by this implementation until the evaluation split completed, and the policy/prompt/thresholds were unchanged before opening them. Case 19M was previously explored and is explicitly a development case. Historical knowledge and model pretraining may cover every period: these holdouts do not establish unseen market generalization.

The evaluator was committed as `52da502344a25b5549ac40f5de4cce7a4ce73b24` before execution; the provider and engine are pinned in the frozen manifest. An initial evaluation invocation omitted `ENTROTTER_RPC_URL` and failed before RPC or model calls. Its unchanged failure record is retained in `evidence/causal-v1/attempts/evaluation-missing-rpc.json`. The same frozen evaluation was then run with the documented public archive endpoint. No output-floor, scenario, prompt or policy substitution occurred.

All ten risk/model artifacts were independently rerun from their complete recordings and matched exactly, including observations and receipts. For each case, the model and risk policy received identical requests and ended with identical metrics/token state. `evidence/causal-v1/review.json` records digest/schema checks and independent receipt gas arithmetic. The full reports record model alias, prompt, usage, limits and unavailable seed/cost fields. These are content-addressed audit records, not cryptographic provider authentication.

## Reproduction

Use the dependency commits in `dependency-pins.json`, Foundry v1.8.3, and the same frozen provider source. The evaluator verifies the manifest, proposal byte hashes, prompt/provider digests and clean engine commit before execution. The engine/scenario/coordination PRs still await independent review; proposed commit pins are not an approved release.

```bash
export ENTROTTER_RPC_URL=https://eth.drpc.org
# Add SSL_CERT_FILE=/etc/ssl/cert.pem for the macOS Python trust-store setup if needed.
PYTHONPATH=engine/src python3 entrotter/scripts/benchmark_agent.py --split evaluation --replay-only
PYTHONPATH=engine/src python3 entrotter/scripts/benchmark_agent.py --split holdout --replay-only
```

Replay reads archived source state but makes no model call. Missing/pruned source state, a changed observation or any receipt divergence fails explicitly. The generated evaluation/holdout summaries are preserved; replay writes separate summaries. New model generation consumes account usage and requires an explicit `--generate-model` invocation; existing generation summaries are never overwritten. The evaluated holdouts must not be reused as untouched cases when tuning a new policy.

## Limits and next comparison

These five hand-selected cases all use one protocol and the same simple preflight objective. Contracts and funding are supplied interventions on archived state, not recovered historical agent decisions, later canonical blocks or a reconstructed market. Fork execution uses pinned Anvil with no explicit hardfork override, so this does not establish canonical historical gas costs. Current-state preflight can differ from the next mined block. Failure avoidance does not prove an approval or swap is economically safe.

The [same-task direct Anvil comparison](DIRECT_ANVIL_COMPARISON.md) is now measured. Whole-process resource controls, genuine target-user evaluations and independent PR approval remain open. The useful question is whether Entrotter makes experiments easier to reproduce and audit, not whether a model can outperform the exact rule it was told to follow.
