# Engine candidate status

## 2026-10-02 — Safe RPC diagnostics, unpublished candidate

RPC exceptions now expose only fixed codes and allowlisted methods, while native
trace CLI failures retain the existing explanation with a safe classification
suffix. Provider error data/messages, URLs, parameters and partial HTTP body bytes
are excluded. An actual loopback response with valid JSON but a prematurely ended
Content-Length was accepted by the prior transport and is now refused. The
RuntimeError/RPCRejected relationships, method allowlists, response cap, default
worker error envelope and HTTP v0.1 contract remain unchanged.

Targeted author checks cover hostile exceptions/forged metadata, native CLI
propagation, actual loopback timeout/HTTP/rejection/malformed/truncated responses,
owned server closure and existing trace validation/mining deadline behavior. Full
source static/security checks retain all 23 reviewed findings without suppression.
Exact author logs and frozen sources are preserved privately pending independent
source review. This is not a full native/Docker suite or current-head CI result;
there is no new archive run or retrospective classification of retained failures.
Protected integration, publication and independent approval remain pending.

## 2026-10-01 — Whole worker preparation deadline, PR #22

The current bounded archive candidate now prepares the image in an owned POSIX
session. An independent watchdog caps all preparation phases at 600 seconds and
kills that session on expiry or owner-lifetime pipe EOF, including owner SIGKILL.
The operator can choose a shorter timeout. The parent cleans staging and publishes
the manifest atomically after successful preparation. Runtime/worker source,
container configuration, archive hashes and report contracts are unchanged.

The blocked-download regression failed before the fix. Final local checks pass
204 engine tests, including 15 build tests exercising a real stalled HTTP body,
native blocking call, SIGTERM, owner SIGKILL, an ignoring descendant, timer/handler
restoration and manifest failure preservation. Use the pinned Foundry 1.8.3;
an initial run with the unrelated Homebrew 1.6.0 correctly rejected recorded
observations. Ruff, mypy and the full source-bound 24-finding Bandit policy pass.

An actual BuildKit RUN sleeping for 60 seconds was stopped in 10.013 seconds by
a 10-second budget. A guest /proc query found no remaining probe process. A
normal build produced the same immutable image and complete fixture artifact
e6a12db320dd37e8d37341fe202836d9442a7e428f89381223c9ab29faa479a6.
Evidence and the Docker probe source are in evidence/worker-build-deadline/.

Independent approval, protected integration and cross-repository pin promotion
remain pending. Owner SIGKILL can leave staging/config files; cache/image/VM
storage, arbitrary caller quotas and uninterruptible kernel faults are not bounded
by this change. No new model/archive replay, upstream transaction, image
publication or paid service was used. See the coordination repository for the
broader release gates; this does not establish full goal completion.

## 2026-10-01 — Bounded default-worker Docker metadata candidate

The default worker previously buffered Docker `info` and `ps` without byte caps.
An actual valid info response over 1 MiB failed the new refusal regression before
this fix. Fixed metadata queries now read at most 4 KiB per chunk and reject
information above 1 MiB or admission/owner output above 128 bytes before parsing.
Each query retains a ten-second pipe/client deadline, nonzero exit failure and
ownership/controller validation. Finally kills only its new client process group,
including descendants retaining stdout; it never kills the daemon or removes a
foreign worker. Cleanup uses the existing owner-label/full-ID protocol.

All 212 local native/unit tests pass with Foundry 1.8.3. Six new real-pipe cases
cover exact boundaries, oversized valid JSON, flooding, a full ten-second timeout
with an exited leader/ignoring child, EOF-before-exit/status, and cancellation.
The initial cancellation probe interrupted Popen internals rather than the reader;
its corrected selector-bound probe and final full suite pass. All 22 production
sources pass Ruff/mypy and the full scanner retains 23 findings, with no suppressed
rules. Two metadata launch sites are consolidated; this reduction is not evidence
of fewer vulnerabilities. Updated exact source/finding rationales need independent
review.

Actual dedicated ARM64 Docker returns 11,576 info bytes and confirms all required
controllers. A new image changes only isolated.py among 18 inputs. The first full
22-case Docker run retained 19 passing resource/admission/lifetime/build tests but
three native/worker equality cases used the wrong host Foundry version. Only those
three were retried with 1.8.3; all pass without source/expectation changes, including
complete fixture/local-Anvil/risk/recorded-model equality. This is combined local
coverage, not a single all-passing full invocation. Current-head complete CI is
linked separately in the PR; evidence/docker-metadata/summary.json binds the logs.

This fix covers only default-worker info/ps captures. Other scanner/tool responses,
whole-host overhead, abrupt owner SIGKILL, process-launch/kernel stalls, Docker
cache/image/VM storage and archive egress limits remain. Frozen historical/model
inputs are unchanged and no new archive/model call, protected merge, deployment,
package publication or submission occurred. Coordination still selects the prior
review candidate until this focused stacked PR is independently reviewed.

## October 1 — Contract identity reproducibility review and fix

An independent Codex source reviewer reproduced a real Anvil v1.8.3 defect:
case-aliased local contract keys with STOP/revert code produced success/21,000 gas
versus revert/21,006 gas when only insertion order changed. Canonical scenario
bytes were identical. All four owned guardians exited and their RPC ports closed.
The original source, inputs, script and observations are retained in
`evidence/local-contract-identity/`, separately from the fix.

Validation now refuses duplicate normalized local contract addresses before any
node/Docker client for native, normal bounded and bounded-agent entrypoints.
One legitimate mixed-case override is preserved unchanged. Both-order refusal
regressions fail before the fix and pass afterward; all 214 native/unit tests pass
in 29.765s with pinned Foundry. Lint/format/type checks cover all 22 production
files. The full scanner retains all 23 findings and unchanged rationales; stale
source review fails before refreshing only the models.py source hash. Follow-up
independent code review confirms resolution; it is not a GitHub approval.

Actual current-head Linux native/Docker/image/native-provenance CI remains a
separate gate linked in this focused PR. No archive/model call, Docker/VM startup,
protected merge, deployment or submission occurred. Frozen report/holdout/source
inputs and v0.1 contracts are unchanged. Coordination still selects tested c167193
until a separately validated source promotion; main protection is retained.

## Same-block signed funding: native fix prepared, CI pending

The `fix/trace-funding-admission` candidate starts from tested engine8176597.
Only owned trace nodes defer parent-state pool balance/gas/fee admission to
actual ordered EVM/block execution. Two regressions fail before the fix; four
focused real-native regressions and248full native tests pass with0skips. Existing
RPC denial, fixed headers/signatures, guardian/memory/deadline and all v0.1
contracts remain. Full23-source lint/format/types and23retained Bandit findings
pass;42locked dependency identities have0reported advisories, fresh wheel built.
An ignored author runner's spawn-guard failure remains distinct from the fresh
required full pass. See [scope and raw evidence](evidence/trace-funding-admission/README.md).

This is disposable synthetic native funding proof, not a new historical replay,
model/holdout result or Docker-isolation measurement. A new no-network image
protocol case is pending CI; separate host default mainnet/image/native provenance
and cleanup gates remain unchanged. Existing SDKee/siteb7 offline inspection and
engine817 historical proof retain their exact prior sources. No Docker/VM startup,
upstream write, key retention, merge, deployment or submission occurred. Independent source/evidence review passed with no remaining actionable findings;
its exact pre-publication hashes are preserved. Exact-head CI and mandatory
human GitHub approval remain separate; overall goal active.

## Signed oracle dependency and provider-state coverage prepared

The `test/trace-oracle-provider-state` candidate starts from tested935558a/PR31.
Four actual native regressions cover signed CREATE parent setup, original
signed same-block oracle update20 plus an independent sender's consumer, adverse
omission from parent value10, and read-only local provider fault/control cases.
Both original receipts match gas26167/26438 and the consumer word20 log; omission
preserves its signature and reverts at25808gas with no logs. Source nonces/state
remain unchanged by replay. This is synthetic causal receipt proof, not profit,
historical price, oracle service or complete state truth.

Missing parent/code/balance explicitly fail; missing mining-time storage instead
can produce a sealed unverified `not_mined` baseline without receipts. The only
production change explains that receipt absence cannot identify the cause or
attest parent state. No state/signature repair, fallback or inferred error cause
was added. New direct image/protocol coverage awaits exact-headCI; default host
dispatch/lifecycle and historical gates remain separate unchanged checks.

After a preserved new-test import failure, four focused cases and252full native
tests pass with0skips/errors/failures. Full23-source lint/format/types and all23
retained scanner findings pass;42locked Python packages have0advisories. Nine
oracle/fault nodes and five proxy threads/ports close successfully. A diagnostic
generator's prior nine-node raw JSON/report overwrite is explicitly disclosed;
original aggregate investigation/root review and initial raw observations remain,
while the fresh current native proof uses a separate non-overwriting destination.
See [raw evidence and exact scope](evidence/trace-oracle-provider/README.md).

Independent source/privacy/evidence review passed with no remaining actionable
findings; three fresh reports also pass unchanged SDKee/siteb7 offline validators.
Original pre-publication hashes and evidence-loss disclosure remain preserved.
All eight exact-headCI checks are pending. No local Docker/VM, new archive/model/holdout/media operation,
upstream write, retained key, merge or deployment. Prior engine935/PR31 all-eight
CI and coordinator8029 evidence remain distinct; the overall goal remains active.

## Separate diagnostic same-invocation observation prepared

Published aac/PR32 has seven successful required checks and one failed isolated
check:25Docker tests and first-prefix default replay passed; the four-prefix
baseline matched originals, while candidate transaction2 was `not_mined`. A later
separate diagnostic completed; the original cause remains unknown. Later image
and native advisory gates did not run. No blind retry or weakened assertion.

The failure-only test helper now observes its own guardian invocation with a
fixed backend log filter, bounded finite event/index/EOF/truncation metadata and
exact worker envelope SHA/branch binding. All23production sources and normal
mandatory workflow commands remain unchanged. Owned reader/session cleanup and
primary replay error preservation have focused regressions. A frozen integrated
native synthetic control preserves full original receipts; missing storage emits
same-invocation execution-skip2/1 with an unverified baseline. All seven owned
nodes, eight readers and two proxy threads/ports close; source state is unchanged.
This is diagnostic observability, not the cause of the original historical fail,
a normal default-worker pass, profit or provider/state attestation.

See [frozen proof and precise test/evidence scope](evidence/trace-oracle-provider/same-run-observer/README.md).
Final independent source/privacy/evidence review passed; new-head required CI
and protected-main human approval remain separate. No local Docker/VM or new
archive/model/holdout/media operation. Current public composition remains
coordinator8029/engine935; unpublished integration awaits all component gates.
Overall goal active, with earlier raw-evidence loss disclosure retained.
