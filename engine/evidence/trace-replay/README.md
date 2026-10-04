# Canonical transaction-prefix evidence

This candidate adds original signed transaction replay separately from v0.1
archived-state actions and recorded-agent simulations. It does not establish
full-block/opcode/state-root replay or a reconstructed economy.

## Actual archive execution

On October 1, 2026 the explicit native developer CLI replayed the first transaction
of Ethereum block 19,000,000 from parent 18,999,999 using Anvil/cast v1.8.3 and
the public dRPC archive transport. Both branches used the original Shanghai
header context and chain ID 1, without funding, code overrides, impersonation,
nonce repair or upstream writes. The candidate omitted that transaction.

```bash
export PYTHONPATH=src
export SSL_CERT_FILE=/etc/ssl/cert.pem
export ENTROTTER_RPC_URL=https://eth.drpc.org
python -m entrotter_engine trace-run tests/data/canonical-mainnet-prefix.json --native -o evidence/trace-replay/mainnet-prefix.json
```

The operator PATH selected the verified Foundry v1.8.3 binaries and a local
quality-tool virtual environment. The OS certificate bundle stayed verified;
TLS was not disabled. This is a native developer result, not local Docker proof
or a clean-install benchmark. The new CI step separately executes the same
plan through the default bounded worker and requires a matched original receipt.

The [raw result](mainnet-prefix.json) preserves the signed bytes, source pins,
original/local projected receipts,8 ordered logs,208,144 gas, elapsed time and
limitations. `baseline_verified` is true; the candidate explicitly records the
omission. Actual block hash is
`0xcf384012b91b081230cdf17a3f7dd370d8e67056058af6b272b3d54aa2714fac`;
transaction hash is
`0xc9ab90a1796613b0fbccb33827de583901d4c0775e89c0f25d604b7c3a71771e`.
Receipt block hashes/roots/end state are outside the comparison. This is a
technical receipt case, not an agent evaluation or profitability claim.

The first PublicNode attempt returned a missing original receipt and refused
execution, with no fixture substitution. A bounded availability probe also found
no historical receipt at Flashbots and a transport error at Llama; dRPC returned
the pinned receipt. Archive availability and future rate limits are not promised.

## Tests and independent review

The local full suite passed 241 tests in 31.739s; 27 focused trace tests also passed.
Actual local Anvil exercises legacy/type-1/type-2 signature byte equality,
success, revert/log receipts, paired forks, skipped-input nonce conflicts,
explicit rejection, source/prefix mismatch and closed nodes after errors.
Host/protocol/CLI mocks separately exercise exact envelopes, full-input binding,
resealed foreign plans, input file type/size, timeout/output cleanup and no
native fallback. Those mocks do not prove kernel isolation.

The new Docker test executes a signed synthetic three-transaction fixture
inside the existing no-network quota-constrained image. It is artificially
funded and never substitutes for the separate archive check. See the workflow
and current-head PR check/artifact links for observed Docker results; those
results were pending when this evidence commit was prepared.

Independent software review found a caller-mutation defect: the candidate could
receive invalid changed skip indices after validation. Snapshotting finite JSON
before validation/use fixed it; the regression and re-review passed. Eight
independent focused checks passed without another archive/model call. This is
software review, not an approving GitHub review.

Actual independent Anvil probes also confirmed the parent-state pool limitation:
a later sender's spend can reject while its funding transaction is merely queued,
then succeed after funding mines. The feature records rejection and leaves such
a baseline unverified. It does not mine transactions in separate blocks or patch
balances to conceal this gap. A separate gas/order probe preserved two 21,000 gas
transactions in FIFO order in a 51,000 gas block despite larger requested limits.
Both probe sessions exited and their ports closed.

Full lint/format/type checks and the complete Bandit scan pass. All 23 findings
remain reviewed and visible across 23 production/script sources; no rules or
advisories are suppressed. Runtime dependencies remain empty. The locked tool/
build graph, worker image and native inventories retain their separate CI gates.
See [summary.json](summary.json) for source hashes and current measurements.

## Remaining scope

Same-block funding admission, other fork eras/transaction types, full-block and
opcode/state-root replay, a trace schema/SDK/viewer integration and broader
oracle/divergence cases remain open. Runtime metadata varies across executions;
identical outcomes do not promise byte-identical artifacts. The v0.1 contracts
are unchanged and reject this different result family. Independent protected-main
approval, candidate integration/publication and competition submission remain
separate gates. No production key, model call, mainnet write, deployment or
formal submission occurred for this change.
