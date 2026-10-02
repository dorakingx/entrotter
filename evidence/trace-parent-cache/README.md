# Experiment-local parent read cache

This candidate reuses exact pinned-parent responses between independent signed
prefix branches without serializing unrelated upstream reads. It preserves
original signatures, state/header handling, receipt comparisons and limits;
it never repairs balances, nonces, code or provider responses.

## Local source and synthetic verification

The frozen [prelaunch source record](author/readiness.json), [final source record](author/final-readiness.json)
and [full-suite proof](author/full-proof.json) bind323 native tests passing in
75.836s with0 skips. Only an outcome update to STATUS followed terminal recording.
[Lint](author/lint.log), [formatting](author/format.log), [types](author/types.log)
and the [full Bandit report](author/bandit.json) cover25 production files and
retain all25 findings/rationales. The [stale-policy refusal](author/security-before-refresh.log)
preceded an [exact child-source hash refresh](author/policy-refresh.json).
[Wheel provenance](author/packaging.json) verifies20 modules and21 declared image
inputs; this is not an actual image build/scan or default-worker CI result.

Two actual HTTP concurrency controls [fail before](author/concurrency/regression-before.log)
and [pass after](author/concurrency/regression-after.log). The expanded23-case
run retains an [incorrect header-fixture failure](author/concurrency/loopback-final.log);
the [corrected header and owner-cancellation controls](author/concurrency/corrected-header-and-cancellation.log)
pass separately, and the final full suite includes all24 cache controls.
[Independent actual-helper controls](independent/concurrent-helper-review.json)
prove distinct-key concurrency, four-handler refusal, successful duplicate
coalescing, independently uncached receipts, error-owner wakeup, exact JSON
tokens/fresh IDs and owned child/group/port/pipe closure. Earlier
[owner-death/handler controls](independent/earlier-owner-and-handler-review.json)
and [uncached-receipt controls](independent/earlier-uncached-receipt-review.json)
retain their original source scope. [Final source review](independent/source-and-native-review.json)
verifies the current sources and explicitly retains earlier failures.

## One instrumented historical prefix

The [plan](native-005/plan.json), [exact worker request](native-005/worker-request.json),
[captured source](native-005/captured-source.json) and [report](native-005/report.json)
cover Ethereum block18999892, first32 of181 transactions, with skip[12].
[Prelaunch review](independent/native-005-prelaunch-review.json) verifies unchanged
150s shared trace,180s child,190s host and10s cleanup bounds, at most two Anvil
nodes plus exactly one fixed cache child. This invocation is instrumented native
execution, with no default Docker CPU/RSS/PID quota claim.

On this candidate checkout, the normal CLI can consume the portable plan:

```bash
export ENTROTTER_RPC_URL='https://YOUR_ARCHIVE_PROVIDER'
PYTHONPATH=src python3 -m entrotter_engine trace-run evidence/trace-parent-cache/native-005/plan.json -o prefix-report.json
```

That command uses the configured bounded worker; its new-head CI is pending.
For trusted native development, put Foundryv1.8.3 `anvil` on PATH and add
`--native`. The chosen provider must supply the pinned historical state; a new
execution can fail and runtime is not reproducible from metadata alone. Local
`.quality` paths in readiness are historical provenance, not prerequisites.
The four-phase getter records below come from separately reviewed research
instrumentation, whose host-bound harness remains private. The standard CLI
exports the unchanged trace report and does not produce those extra getter or
host-cleanup observations.

With the reviewed SDKee5523d installed, the frozen report is readable offline:

```bash
python3 - <<'PY'
from entrotter_sdk import load_trace
result = load_trace("evidence/trace-parent-cache/native-005/report.json")
print(result.baseline_verified, len(result.transactions), result.artifact_id)
PY
```

This reads existing bytes without an archive request or new execution.

[Execution review](independent/native-005-execution-review.json) verifies all32
complete projected baseline receipts against original source and prior baseline.
The candidate executes31 transactions and skips12; remaining gas/status/logs/bloom
and identities are unchanged, later indices shift by one and cumulative gas
falls by exactly336752, the omitted transaction's gas. [Getter observations](native-005/observations.json)
show identical initial heads/values: baseline price257082415000 becomes256292441874
with a round increment; candidate retains the parent value. All four phases have
zero getter errors. No dependent consumer effect or profit is established.

The report runtime is125.330162s; native elapsed125.358258s and host125.460378s.
[Cache ownership/counters](native-005/owned-cache.json) show1871 requests,
966 upstream reads,899 hits,960 entries/2640492 bytes,6 uncached responses,
6 aggregate errors and0 handler refusals. These counters do not identify error
causes. [Host node cleanup](native-005/host-owned-cleanup.json) and
[host cache cleanup](native-005/host-cache-cleanup.json) verify owned PID/group/port
closure; cache pipe closure is recorded separately. [SDK](independent/native-005-sdk-reader.json)
and [viewer](independent/native-005-viewer-reader.json) verify offline report
reading against published pins, without fresh browser/rendering/deployment checks.

## Retained failures and provenance

Four earlier full-suite failures remain in [final001](prior-failures/final-001-native.log),
[final002](prior-failures/final-002-native.log), [final003](prior-failures/final-003-native.log)
and [final004](prior-failures/final-004-native.log). The serialized cache candidate's
[later314-test pass](prior-failures/serialized314-full-proof.json) is historical.
Its [native004 failure](prior-failures/native-004/terminal-record.json) has
739 upstream reads/0 hits, failed initial latestRoundData and baseline mining,
and no baseline/candidate/report. [Independent failed-run review](independent/native-004-execution-review.json)
preserves that scope. Older001–003 failures remain privately immutable and are
bound in native005 prelaunch metadata. No baseline receipts are reconstructed
for native001/004. One changed-source success does not establish speed or the
cause of earlier timeouts.

[Copy provenance](provenance.json) records every original/public SHA and marks
local-path-only redaction. Reviews/readiness retain original private checksums;
redacted public copies deliberately have different hashes where listed. Original
records are unchanged. Static scanner documentation URLs and its fixed loopback
source template are retained; no provider URL, token, signing key or private
contact is included. Prelaunch records remain time-bound rather than rewritten
to describe the result. [Summary](summary.json) records current review/CI limits.

[Public-package review](independent/public-package-review.json), SHA
`e63de37fb74d96ea89af201ca57d33cfcda470a6c8c39f10ff7b1a96e70d84ae`,
verifies the61-file pre-addendum package and all58 copy bindings. This exact review
copy and the summary/README status mention are a publication addendum; the
original copy manifest and historical readiness records remain unchanged.

This is bounded prefix/projected-receipt and producer-state evidence, not
full-block replay, state-root/opcode equivalence, provider/oracle authentication,
market behavior, strategy benefit or complete G1. Exact-head eight-check CI,
artifact review and protected-main human approval remain separate pending gates.
