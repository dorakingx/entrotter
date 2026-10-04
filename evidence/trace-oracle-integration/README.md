# Signed oracle and provider-fault report integration

The current reviewed source snapshote46b392 selects engine99fd3a6/PR32,
with SDKee5523d, CLI22b514c,
schemas8785bb0 and viewerb7c20ce. The engine adds four actual native regressions
and one direct bounded-image protocol case. Its only production change is an
accurate explanatory assumption; execution/security/v0.1 behavior is unchanged.
The [independent engine source/evidence review](root-engine-source-review.json)
verifies frozen signed inputs, fresh252-test native proof, nine node closures,
five fault/control proxies,23source/18wheel/42locked package bindings and the
same23 full reviewed security findings. Local image execution was not inferred.

Original signed CREATE inputs establish a synthetic parent oracle value10.
The signed update writes20 before a separate sender's consumer in one block.
Both original receipt projections match: gas26167/26438, cumulative26167/52605,
one consumer log word20. Omission preserves the consumer hash/signature but
reverts at25808gas with no logs. A normal read-only provider proxy verifies the
same receipts. Missing parent/code/balance explicitly fail; missing mining-time
storage instead produces a sealed **unverified** report without receipts.
Receipt absence alone cannot identify a provider error or attest state.

The [offline result](offline-result.json) runs the exact new CI step with the
actual typed SDK and viewer codec. It checks fixed bytes for positive, control
and missing-storage reports, success/revert gas/logs, artifact identity and an
unverified baseline without receipts. Node22.23.1 is pinned. Existing original
four-prefix and synthetic-funding reader steps also pass with the new dependency
pins; their original report bytes remain unchanged. This is offline inspection,
not new EVM/archive/model execution or rendered browser verification.

The [previous funding composition](previous-funding-ci.json) at8029/a253 passed
all five checks. Root verified21sources/78full retained findings/50packages/
19image inputs/55docs and complete API/CLI/admission/export/reproduction proof.
Clean fixture7.477365s and recorded model8.196629s belong to that exact composition
with Docker already running and potentially warm caches. Older prepared evidence
retains its historical pending-CI state; this proof does not overwrite it.

An ignored generator overwrote two earlier investigation raw files. Their
original bytes are unavailable; the engine discloses the loss and preserves the
original aggregate/review and initial raw proof. Current native evidence is a
separately named fresh run; old hashes are never presented as revalidated bytes.
See the pinned [engine disclosure](https://raw.githubusercontent.com/entrotter/engine/e84980edd3945d405bf118790b8166c95bd75c7b/evidence/trace-oracle-provider/evidence-handling.json).

New engine exact-head CI and this composition's exact-head CI are separate gates;
see summary.json and PR55 for their current states. Synthetic oracle/control/
fault proof does not establish archived oracle service, external price truth,
full-block/roots/end-state/opcode equivalence or provider state authenticity.
Human protected-main approval, candidate Pages publication and submission remain
open. No local Docker/VM startup, upstream write, new model/holdout/media run,
protected merge, package publication or Discord work occurred.

## Earlier diagnostic successor: failed gate preserved

At [engineaac525c](https://github.com/entrotter/engine/tree/aac525c8279005a3a8468fe3928e691c3ce80148),
seven checks pass; the [isolated job](https://github.com/entrotter/engine/actions/runs/36913460373/job/110541575793)
passes25Docker tests in217.511s and verifies the original mainnet1 receipt in
9.143445s. The four-prefix run takes29.610351s and matches all four original
receipts exactly. Its candidate instead returns
`skipped / executed / not_mined / nonce_conflict`; transaction2 has no receipt.
The unchanged exact candidate assertion fails. The image/native advisory gates
after that failure do not run, so all eight checks remain incomplete.

The [failed actual report](diagnostic-mainnet-prefix-four.json) retains that
outcome; [one-prefix report](diagnostic-mainnet-prefix.json) is separate.
The [later exact-plan diagnostic](diagnostic-followup.json) succeeds with the
expected candidate statuses and verified cleanup. It cannot identify why the
original invocation lacked a receipt or substitute for the failed gate. No
state repair, synthetic fallback, assertion relaxation or blind retry follows.

[Root partial artifact inspection](diagnostic-ci-partial.json) verifies the
raw23source/23retained findings/18wheel/42locked package/19image input/13docs
bindings and267Linux native tests without skips. Four unit matrices each have
267tests with31real-Anvil skips. SDKee and the actual viewerb7 codec retain the
failed report's checksum, exact baseline receipts and missing candidate receipt;
no fresh rendered-browser or provider-authenticity claim is made.

[Earlier four-file pin review](diagnostic-pin-review.json),21-source types and the three
exact offline reader steps pass with aac metadata. Snapshot27 remains local and
unpublished; it describes the earlier e849 preparation. No new immutable
composition/combined CI is published before all mandatory component checks pass.
The already tested public8029/a253 composition continues to select engine935.
The integrated observer and new99fd component proof are recorded below.


## Integrated observer: synthetic native evidence

The diagnostic-only helper now observes finite allowlisted events from its own
owned Anvil invocation, with the full worker-envelope checksum, branch and
original input indices. The fixed `backend` filter,131072-byte scan cap and
8192-byte line cap retain no raw logs or provider exception text. EOF, truncation
and reader errors distinguish incomplete observation. The original150-second
execution budget, ownership, resource bounds and mandatory normal replay commands
remain unchanged.

[Root integrated review](root-integrated-observer-review.json) checks33frozen
source bindings,23production sources and the workflow unchanged from aac, the
Anvil binary and signed fixture, exact protocol payload and all three saved
reports through SDKee and the actual viewerb7 codec. Full baseline/candidate
receipts equal the raw unobserved control. Injected missing storage yields
baseline `not_mined / not_mined`, candidate `skipped / not_mined`, and two/one
bound execution-skip observations. Seven nodes, eight readers and two proxy
listeners/handlers/ports close; source state is unchanged. These are synthetic
native diagnostics, not normal Docker dispatch or the original historical cause.

Fourteen focused observer tests and the separately added collector-descendant
regression pass; the final test file is preserved separately from the earlier
14-test source. The existing15diagnostic tests also pass. Primary RPC failure is
retained if diagnostic collection fails. A held descendant output pipe reaches
the shared collection deadline and is closed with its owned process group.
The integrated component is now published at99fd; the current full CI proof is
recorded below. Previous mandatory failures remain intact and their cause is
unknown. Composition publication and protected-main approval are separate.


## Current exact-head component proof; combined CI pending

[Engine99fd](https://github.com/entrotter/engine/tree/99fd3a60a754f129c78d1324f2a01787a6538917)
passes all eight checks on its first attempt. [Independent raw verification](root-engine-full-CI.json)
binds23source/23full findings/18wheel/19image/42Python/26OS/1126signedCargo/
14doc hashes and282native tests without skips. Four282-test unit matrices retain
31real-Anvil skips each. [Isolated CI](https://github.com/entrotter/engine/actions/runs/36922529032)
passes25Docker tests217.324s, original1 replay7.021339s and original4 replay
19.281316s. These are recorded observations, not a speed comparison.

[Current one-prefix report](verified-mainnet-prefix.json) and
[current four-prefix report](verified-mainnet-prefix-four.json) preserve all
previous935source/plan/baseline/candidate values except runtime, checksum and the
exact added missing-state assumption. Candidate4 is
`skipped / executed / executed / nonce_conflict`. SDKee and the actual viewerb7
codec independently retain these report checksums and statuses. Image/native
advisories and owner cleanup pass. The conditional diagnostic is **skipped**,
so this is not evidence of observed historical/Docker diagnostic dispatch or a
cause for the earlier failure.

[Final four-selector review](observer-pin-review.json) preserves every other
source/dependency/frozen/model/holdout byte. Sourcee46,21type inputs with the same
three frozen diagnostics, and all three exact offline SDK/viewer step bodies
pass. [Package copy/privacy review](root-integrated-observer-package-review.json)
keeps earlier14-test bytes separate from the final additive15-test file. Current
composition preparation is unpublished; all five combined checks, human approval,
candidate Pages publication and submission remain open.
