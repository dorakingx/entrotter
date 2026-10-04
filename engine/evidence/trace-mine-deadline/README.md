# Archive-backed mining deadline and four-transaction evidence

The original native CLI repeatedly failed to mine the first four transactions of
pinned Ethereum block 19,000,000 within the ordinary ten-second RPC socket cap.
All four original inputs and receipts were available and all four signed inputs
were queued in the owned local node. The observed `evm_mine` failed at 10.003215s;
its owned port closed afterward. See [prior observation](prior-timeout-observation.json).
No original receipt, state, signature or nonce was repaired to make it succeed.

Only the owned mining call now receives the primitive's remaining shared
150-second deadline. This does not reset the budget, change the independent node
guardian or lengthen subsequent reads. `finally` restores the ordinary timeout on
success or error. Native cleanup still has the existing grace periods and is not
a whole-process CPU/RSS sandbox.

## Actual native reproduction

With verified Anvil/cast v1.8.3, Python 3.13.0 on Darwin arm64 and the verified OS
TLS bundle, the changed native CLI completed in 46.982404s:

```bash
export PYTHONPATH=src
export SSL_CERT_FILE=/etc/ssl/cert.pem
export ENTROTTER_RPC_URL=https://eth.drpc.org
python3 -m entrotter_engine trace-run tests/data/canonical-mainnet-prefix-four.json --native -o native-prefix-four.json
```

The [raw native report](native-prefix-four.json) contains four baseline receipt
projections exactly equal to their original canonical projections. Their gas is
208,144 / 234,720 / 175,305 / 178,980 and they contain 8 / 10 / 6 / 8 ordered logs.
Both branches fork the same pinned parent using the original Shanghai context.
There are no funding/code overrides, impersonation, new signatures or upstream
writes. The [plan](plan.json) omits only transaction 0.

After omission, transactions 1 and 2 execute using 245,136 and 185,721 gas. Gas,
cumulative gas, transaction index and ordered log content differ from their
original receipts. Transaction 3, from transaction 0's sender, cannot execute:
the preserved original nonce is 5,523 while the candidate expects 5,522. This
records a real state-dependent difference and nonce conflict. It is not a claim
of profit, model advantage, full-block equivalence or a reconstructed economy.

The terminal native run returned zero. After it and the full local suite, the
process executable inventory contained no live Anvil. The failed prior run has
a separately observed closed owned port. This execution uses explicit trusted
native mode; actual bounded execution is a separate CI gate, pending when this
evidence commit was prepared. CI retains the original one-transaction replay
and adds a mandatory default-worker four-transaction check without fixture fallback.

## Tests and review

The immutable previous source fails the slow-mining regression; the changed
source passes that regression, a near-deadline case and timeout/context cleanup
on mining failure. The complete local suite passes 244 tests in 31.741s, including
real synthetic Anvil. Full production lint/format/type checks pass. All 23 full
Bandit findings across 23 source files remain visible with no skipped rules;
only the changed source digest was refreshed after finding equality.

[Independent source review](independent-review.json) found no actionable defect
and independently passed three focused mocked tests. It inspected the existing
guardian and the prior failed observation; it did not repeat the native archive
execution. This review is distinct from protected-main GitHub approval.

See [summary](summary.json) for exact input, report and source-review digests.
The original model recordings, consumed evaluation holdouts and videos are
unchanged. No model call or local Docker/VM startup occurred. Same-block funding
pool admission, other eras/types, full-block/opcode/root/end-state execution,
trace SDK/viewer support and required independent GitHub approval remain open.
