# Direct Anvil comparison

The standalone Anvil script and Entrotter produced identical common outcomes in all six measured runs. The observed median runtimes were similar; this experiment does not demonstrate a speed advantage for Entrotter.

| Method | Run 1 | Run 2 | Run 3 | Median |
| --- | --- | --- | --- | --- |
| direct | 9.398 s | 8.653 s | 8.553 s | 8.653 s |
| entrotter | 8.926 s | 8.689 s | 8.591 s | 8.689 s |

The task is the unchanged causal-v1 Ethereum block 19,000,000 development case: two isolated forks, 10 ETH artificial funding, wrap 1 ETH, approve 1 WETH, and compare a prescribed swap against a current-state preflight policy. The 1,000,000 USDC floor makes the prescribed swap revert. Both implementations spend 222,793 gas in that branch and 91,090 gas in the policy branch, which holds after the same setup.

Equality covers the source pin, initial/final native and raw token balances, every intermediate balance, transaction status, complete mined receipts, total gas and exact receipt-derived gas cost. The direct script imports only Python standard-library modules and communicates directly with owned Anvil nodes through JSON-RPC. It shares the frozen transaction JSON and Anvil executable, not the Entrotter runner, transport, ABI builder or risk-policy implementation.

The direct script is deliberately limited to one byte-hashed, audited input. It does not implement general scenario validation, typed agent observation/response records, deterministic recording replay, the SDK/API or the browser artifact viewer. Entrotter produces those additional outputs alongside the common projection. This is a feature distinction, not measured contributor productivity or proof of demand. For a single bespoke experiment, the direct script is a valid alternative.

## Measurement limits

Each timing includes source verification, two fresh forks, setup, policy execution, per-step state collection and cleanup; disk serialization is excluded. Order alternates across three repetitions. Archive/network caching and OS scheduling are uncontrolled, and the small sample does not support statistical speed claims. Child CPU and cumulative peak RSS are recorded with their scope, not misrepresented as hard quotas. No setup time, coding time or user success rate was measured.

This task was already explored during development and is not a new holdout. There is no portfolio valuation, historical transaction replay or future-price prediction. The source code was committed as `384d4ab` before measurement; exact script hashes, environment, run order and all common outcomes are in `evidence/direct-anvil-comparison.json`.

## Reproduce

Use the pinned engine commit and Foundry v1.8.3 from the release evidence. From the six-checkout workspace:

```bash
export ENTROTTER_RPC_URL=https://eth.drpc.org
# For this macOS Python setup, add SSL_CERT_FILE=/etc/ssl/cert.pem if needed.
python3 entrotter/scripts/direct_anvil_case.py
PYTHONPATH=engine/src python3 entrotter/scripts/benchmark_direct.py
```

The standalone command needs no Entrotter runtime or model account. The comparison command refuses to overwrite committed benchmark evidence. To run a new measurement, use a separate checkout and archive its existing evidence file first; preserve the old record. Missing archive access fails explicitly and no transaction is sent upstream.

The next demand question is whether teams value a reusable scenario/recording/review workflow enough to replace bespoke scripts. Three genuine user evaluations remain required before claiming that they do.
