# Same-block funding candidate integration

This candidate selects [engine935558a/PR31](https://github.com/entrotter/engine/pull/31),
SDKee5523d, CLI22b514c, schemas8785bb0 and viewerb7c20ce. Only owned trace nodes
defer parent-state pool balance/fee/gas admission to ordered execution. Actual
EVM/block validation and resource/lifetime controls remain enabled; ordinary
profiles, signatures, balances and nonces are not repaired.

The engine's independently reviewed native synthetic case executes both original
signed transfers in one block with matching receipts. Omitting the funding
transfer leaves the dependent spend `not_mined`, without a receipt. Four focused
regressions and248 full native tests pass with no skips. Synthetic source
startup allocation is distinct from historical state or replay state repair.
All eight exact935 component checks pass first attempt. Root verifies24 actual
Docker cases (221.940s),248 Linux native tests (36.615s),23source/18wheel/19image
inputs,42Python/26OS/1126signed Cargo identities and11doc hashes. Four original
mainnet receipt projections match in the default bounded worker24.17299s; the
full result matches previous outcomes except runtime/hash and one admission
assumption. These environments are not a speed comparison. See the
[root component proof](root-engine-ci-verification.json) and [actual new report](bounded-mainnet-prefix-four.json).
The current SDK parses both actual current-head CI reports offline; exact
checksums/internal structure pass. This is still not archived same-block funding.

The [offline integration result](offline-result.json) executes the exact new CI
step: it binds the frozen synthetic report bytes, checks SDK typed baseline gas
21000/21000 and cumulative21000/42000, then calls the actual viewer module to
verify matching artifact identity and candidate skipped/not_mined/no-receipt
outcomes. Node22.23.1 and the setup action are pinned. This is codec inspection,
not a rendered browser run, new EVM execution or source authenticity proof.
All21 coordination type inputs pass with the same three frozen diagnostics.

The [previous reader composition](previous-reader-ci.json) at86a/968b passed
all five combined checks, full image/API/CLI/export/reproduction proof and54
document hashes. Those measurements retain engine817 and their actual scope.
The original four-transaction mainnet report, model decisions, holdouts and
video source versions remain unchanged. New-head combined CI is still required.

Full-block/roots/end-state/opcode and broader oracle/missing-state coverage remain
open. Synthetic funding proof does not establish archived same-block funding.
Human protected-main approval, candidate Pages deployment and competition
submission are separate gates; no merge, local Docker/VM startup, upstream write,
model generation, media upload or package publication occurred.

The immutable execution snapshot is [a253da8](https://github.com/entrotter/entrotter/tree/a253da8695fb2521702056dca286ed16b0aba44f).
The [source review](independent-source-review.json) has no actionable findings;
[summary](summary.json) records exact pins and remaining CI scope.
