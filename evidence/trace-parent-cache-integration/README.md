# Bounded parent-read cache integration

The candidate selects engine `198139f` from [engine PR34](https://github.com/entrotter/engine/pull/34).
Exactly four current engine selectors change from65c; other component pins and
frozen native/agent/host compatibility variants remain unchanged. This source
selection awaits combined CI and protected-main approval.

The cache shares successful exact-parent-hash state reads and hash-checked parent
headers between private branches. Different keys fetch concurrently within the
existing bounds; matching eligible successes coalesce. Receipts, errors,
volatile reads and other blocks stay uncached. Original signed inputs, state,
headers and trace time limits are not repaired or extended.

## Component checks and retained failures

[Full independent artifact review](engine-CI.json) binds all8 exact-head checks,
25 source/security findings,20 wheel modules and21 image inputs. CI runs323
native tests with0 skips,323 units per Python3.11–3.14 with33 explicit Anvil
skips each, and25 actual Docker cases. Default Docker1/4-prefix reports preserve
whole previous receipt outcomes apart from runtime/artifact and one cache assumption.
These are distinct from the native32-prefix producer experiment below.

The required docs gate failed twice on existing GitHub HTML HTTP503 responses:
[first raw report](engine-docs-first.json), [second](engine-docs-second.json).
After all13 targets [recovered with the pinned bounded settings](engine-link-recovery.json),
only the failed existing job was rerun. The [successful third report](engine-docs.json)
contains143 successful links/0 errors/timeouts and16 exact document hashes.
Its complete merge tree matches198139f. [Action bindings](engine-doc-bindings.json)
retain the actual immutable action hashes; current coordinator Python formatting
has identical AST, not identical bytes. Assertions, exclusions and required
checks were not weakened. Passing code/runtime jobs were not repeated.

## Actual archived prefix outcome

The [engine source and raw experiment](https://github.com/entrotter/engine/tree/198139ff0b3bf37781b4232b27d8eeb0a5da5365/evidence/trace-parent-cache)
retain original32 signed transactions from Ethereum block18999892, skip12 and
the same150-second shared trace budget. Native005 completes in125.358s;
all32 complete projected baseline receipts match originals and preceding003.
Candidate executes31 original transactions. The producer feed answer changes
257082415000→256292441874 only in baseline; candidate retains the initial answer.
For the other31 transactions, gas/status/logs/bloom/identities match; later
position and cumulative gas change exactly by the omission. Both owned nodes
and the cache close, with independent PID/group/port/pipe checks. All four prior
failed experiments remain preserved. This is32 of181 transactions and a producer
case: no full-block/root/opcode/provider authenticity, dependent-consumer,
strategy/profit or speed/timeout-causality result follows. Native controls do
not provide the default Docker worker's whole-process resource quota proof.

## Cross-repository preparation

[Type evidence](local-types.json) checks21 production sources against198139f,
retaining the same3 explicit frozen provider diagnostics. The three actual
[offline reader steps](local-reader-execution.json) use the exact existing CI
assertions with only output paths changed. [Original-prefix](trace-reader.json),
[synthetic funding](trace-funding-reader.json) and [oracle/provider](trace-oracle-reader.json)
results preserve complete previous outcomes apart from the engine pin.
The viewer parser/sample are copied from exact b7 Git blobs so concurrent local
viewer development cannot affect these results. No chain/model call or fresh
rendered browser check is made by these preparation commands. The initial wrong
interpreter/cwd launcher executed no product code and is explicitly retained.

[Summary and public copy hashes](summary.json) distinguish current preparation
from earlier ccc/65c combined CI. New combined checks, protected main and Pages
publication remain open. Original recordings are not updated by these results.
