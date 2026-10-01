# Same-block signed funding admission

The candidate defers pool balance, gas and fee admission checks only for owned
trace nodes using Foundryv1.8.3's `--disable-pool-balance-checks`. Actual ordered
EVM execution and aggregate block gas checks remain enabled. Normal profiles,
read-only upstream RPC, owned trace method restrictions, original signatures and
headers, input limits, guardian and shared execution deadline remain unchanged.

An independent [native investigation](investigation.json) against the exact
Foundry commit confirms the original problem and supported mechanism. The
[raw probes](prior-and-deferred-probes.json) show two original signed transfers
executed in one block when admission is deferred. Omitted funding, reversed
order, invalid gas/fee and nonce-gap cases cannot produce invalid receipts.
[Balance/nonce follow-ups](state-probes.json) confirm balances and nonces reflect
only actual execution. All eleven probe nodes exited and their ports closed.
Synthetic A starts with1ETH and B with0 through a startup allocation; no replay
balance/nonce/code patch, impersonation or different-block mining is substituted.
No private signing keys are retained.

The independent source fixture uses disposable synthetic signatures, then the
production `run_trace_native` forks its pinned parent for both branches. Two
[regressions fail before the fix](regression-before.log): the trace launch lacks
the option and the real original-receipt baseline is unverified. After the fix,
[four focused regressions](regression-after.log) and the [full248-test native
suite](native-suite.log) pass with0skips in33.137seconds. This full-suite time is
not a product benchmark. The [native synthetic report](synthetic-prefix.json)
verifies two original receipts,21000gas each and cumulative21000/42000. Omitting
the funding transfer leaves the dependent spend `not_mined`, with no receipt.
The tests also require no state mutation on invalid gas/fee/nonce inputs and
closed owned nodes. Its0.266237second runtime measures only synthetic paired
native replay, not historical, cold setup or whole-process isolation performance.

The initial full-suite attempt used an ignored author evidence runner without a
`__main__` guard. Spawned store-test children recursively started the suite and
broke a barrier. That [author-runner failure](author-runner-failure.log) remains
visible. Public failure logs replace local installation paths with generic
`/workspace` paths; unchanged raw originals remain in the ignored author cache.
The ignored runner was corrected; no product/store test was changed to
obtain the fresh complete pass.

[Full static checks](static-checks.json) pass across23production/script sources.
The [full Bandit report](bandit.json) retains23explicitly reviewed findings and
zero skips/errors. The [stale-source gate](security-before-refresh.log) correctly
failed before the exact source policy refresh; the [refreshed gate](security.log)
passes. Only two changed source hashes and the shifted Popen line-number
fingerprint were refreshed, with its existing fixed-launch rationale expanded.
All42locked quality/build dependencies have no reported advisories. A fresh
wheel builds; source and fixture hashes are recorded in [the summary](summary.json).

A new no-network isolated-image test executes the worker protocol against these
same frozen signatures. It has not run locally: no Docker/VM was started. Direct
image/protocol execution is distinct from the production host default-client
helper and its lifecycle. Existing actual default-worker mainnet, image/native
provenance and cleanup CI gates remain unchanged and must run at the candidate
head. This evidence does not assert bounded-worker success before that CI.

Prior engine817 historical receipt results remain in their original evidence;
this new synthetic result does not revalidate archive execution. SDKee5523d and
viewerb7c20ce separately inspect the existing trace contract offline. No new
model/holdout/media result, source authenticity or economic advantage follows.
Full-block/root/end-state/withdrawal/opcode and broader oracle/missing-state
coverage remain open. The [independent source/evidence review](independent-review.json)
passes with no remaining actionable findings, including public log redaction and
unchanged SDKee/viewerb7 offline report compatibility. Its pre-publication hashes
are retained; only review-status prose changes afterward. Exact-head CI and
required human protected-main approval remain separate gates. No merge, deployment,
submission, upstream write or package/image publication occurred.
