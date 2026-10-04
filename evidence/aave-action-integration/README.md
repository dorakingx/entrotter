# Inspect supplied Aave actions across the candidate workspace

The candidate selects Enginef53a66a with SDKba4af51, CLI24bbb91, scenarios8785
and viewer422d. The Engine adds pure Aave supply/variable-borrow builders and a
five-action archived-state experiment. The existing standalone CLI and SDK can
already validate and inspect its complete v0.1 result; this composition makes
that combination reproducible from the [quick start](../../docs/QUICK_START.md#compare-supplied-aave-borrowing-actions).
The frozen benchmark, quality dependency variants and earlier recordings keep
their original pins. Current protected publication is separate from old main.

## Exact result and execution scope

The [Engine packet](https://github.com/entrotter/engine/tree/f53a66a303e67ca4fbb4322a06b36b036f4db599/evidence/aave-borrow-actions)
contains the whole 59506-byte report, scenario, causal recording, all receipts,
ABI/source identities, local first execution and actual bounded recorded replay.
The two outputs match completely, SHA256
`e2db6ee04f2642e7e75ac53e8ad6212cd68b2ae4aab0ca7a4e06063f5f435622`.
Its artifact ID is
`728cfe26dcd40ed9bc08d28c5d8c9a088a7a8b6ad22b83a07285af9084175b00`.

Both branches use pinned Ethereum block18999892, artificial20 ETH funding and
local impersonation. Both supplied lists wrap/approve/supply10 WETH, propose
borrowing9 WETH, then borrow1 WETH. Only candidate step3 uses the built-in causal
preflight risk policy. The baseline mines a revert using162805 gas; the candidate
holds without submitting that transaction. Both supplied final actions succeed,
ending with1 WETH and1 WETH variable debt each. Total gas is723131 versus560326.
The smaller borrow is supplied, not an agent-generated replacement. Native-balance
difference includes different gas prices; it is not profit. No original signed
strategy, future-market prediction or authenticated provider-state claim is made.

## New offline composition

The added CI step runs the Engine example's semantic checker and the selected
standalone CLI's `verify`/`inspect` on that exact original report. Network connects
are denied in each process; CLI execution additionally denies Engine import,
HTTP client requests and export-ledger creation. Entire stdout/stderr/status and
all source hashes are saved before assertions. Source size/hash and all three
whole outputs must match the retained original/installed outputs:
[check](check.stdout), [verification](verify.stdout), [inspection](inspect.stdout).
The general CLI summary retains native metrics, assumptions and the recorded
decision; the example checker exposes exact borrowed-token/debt units, while the
whole report retains the complete token and receipt tables.

[Local reader results](local-reader-results.json) and [step/pin manifest](local-reader.json)
record the one new successful local gate. All prior workflow step bodies remain
identical except the selected Engine checkout. Original reader results are reused,
not separately rerun locally. Earlier actual installed CLI/SDK calls are retained
in [installed execution](installed-execution.json); [all13 installed module hashes](installed-sources.json)
match immutable CLI24/SDKba4 Git bytes. The new source-checkout gate is distinct
from that earlier isolated installed-package execution.

## Current CI and limits

Enginef53 has all eight mandatory checks successful: seven original attempt1
checks plus isolated attempt2. Isolated attempt1 retained an old account-case
baseline `not_mined` at index9 and skipped the new action step. Its cause remains
unknown. One unchanged, non-authoritative diagnostic completed, then only the
failed job was retried without source, timeout, checker or limit changes. Attempt2
passed the old account gate and the new action execution, whose whole output
matches the local first run and recorded replay. [Engine CI summary](engine-ci.json)
links current runs and the independently reviewed raw evidence identity.

Current coordinator CI separately runs this composition and its existing native,
Docker, admission, cancellation, security and documentation gates. Local offline
inspection is not a fresh EVM, model, archive, browser or speed test. Existing
video/source versions are preserved. Independent human main approval, latest
Pages publication, human audio review, supported-host delivery and formal
submission remain separate. The improvement goal stays active until the official
competition deadline; Discord and deferred user evaluations stay excluded.
