# Archived oracle diagnostic: verified baseline, failed candidate

These two retained native diagnostics use engine
[99fd3a6](https://github.com/entrotter/engine/tree/99fd3a60a754f129c78d1324f2a01787a6538917)
and the unchanged first32 signed transactions of Ethereum block18999892.
Transaction12 updates the observed ETH/USD proxy's aggregator. The candidate
omits that transaction without changing any remaining signature or nonce.
Both paired executions fail; this is **not** complete historical oracle validation.

The first execution loses its in-memory baseline receipt outcomes when the
candidate fails. Its [raw failure](native-001/result.json) remains available;
those missing receipts cannot be reconstructed as proof of that invocation.
A separate recording fix saves the captured source and each completed branch
atomically before starting the next branch. Five offline fault/privacy tests
and the exact frozen harness were independently reviewed before diagnostic002.
The same32 inputs and150-second trace budget remain unchanged.

For diagnostic002, all32 baseline projected receipt objects equal the captured
original objects, including identities, status, gas/cumulative gas, price, ordered
log bytes and bloom. See the byte-preserved [captured source](native-002/captured-source.json),
[baseline branch](native-002/baseline-branch.json) and [independent review](native-002/root-review.json).
The owned-node getters observe the same pinned parent and initial answer
257082415000 in both branches; after the baseline the answer is256292441874.
Those integers are raw feed values, not profit or market-performance claims.

The candidate fails at owned-local `evm_mine`; no candidate branch result or final
protocol response exists. The original RPC transport discards the underlying
cause, so timeout, provider failure or another cause cannot be inferred from
elapsed time. The [raw failure](native-002/result.json) and
[final observations](native-002/observations.json) explicitly retain the unobserved
candidate-after marker. Both owned guardians exit0 and their ports close in each
attempt; independent final process/port checks confirm cleanup.

[summary.json](summary.json) pins hashes for16 byte-preserved raw/review files,
the original block/parent, source ABI commits, budgets and limitations. Full frozen
research harness, readiness, binary and CA metadata remain local; their original
hashes in terminal records are not hashes of regenerated public files. The public
bundle alone cannot recreate every local readiness binding.

This is explicit instrumented native execution, without Docker CPU/RSS/PID proof.
Provider-supplied receipts and getter responses do not establish provider truth,
oracle authentication, block/state roots, full-block/end-state/opcode equivalence
or an actual dependent consumer. No liquidation topic occurs in this prefix, which
does not exclude other internal consumers. The earlier synthetic oracle/control
and default-worker proofs remain separate. No state repair, narrowed successful
prefix, budget expansion or weakened assertion substitutes for the failed candidate.
