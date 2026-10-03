# Exact native and token outcomes in the candidate workspace

The candidate selects [CLI169b759](https://github.com/entrotter/cli/commit/169b759aff9280ce44fb0d15569c7ae0a4a40889)
with Enginef53a66a, SDKba4af51, scenarios8785 and viewer422d. Developers can run
`inspect --format text` on the original Aave action result to see exact native
and pinned ERC-20 initial/final/change amounts, candidate-minus-baseline
differences, gas cost/usage and revert/reject counts without manual scaling.
The [quick start](../../docs/QUICK_START.md#compare-supplied-aave-borrowing-actions)
includes the command. Default JSON is unchanged; missing records remain
Unavailable, and the display does not infer token roles or valuation.

## Original execution and readable result

This consumes the exact 59506-byte [Engine recording](https://github.com/entrotter/engine/tree/f53a66a303e67ca4fbb4322a06b36b036f4db599/evidence/aave-borrow-actions),
SHA256 `e2db6ee04f2642e7e75ac53e8ad6212cd68b2ae4aab0ca7a4e06063f5f435622`.
Its first bounded execution, recorded replay and current Engine CI output match
entirely. Those are earlier execution evidence; this composition runs readers.

At archived Ethereum block18999892, both supplied branches wrap/approve/supply
10 WETH, propose borrowing9 WETH, then borrow1 WETH. Only candidate step3 uses
the built-in current-state preflight policy. Baseline mines the9 WETH revert;
candidate holds without submitting that transaction. Both finish with1 WETH,
10.000000094454558462 aWETH and1 variable-debt token. Total gas723131 versus560326
appears in the [whole text output](inspect-text.stdout), alongside the reported
source/artifact identities, recorded hold and assumptions.

The smaller borrow is supplied, not an agent-generated replacement. Artificial
20 ETH funding, local impersonation and differing gas prices remain disclosed.
Balance differences are not profit. Hash and display unit/accounting checks do
not authenticate execution, provider state or the scenario's units. Complete
receipts remain in the original report; the text is a presentation of that data.

## One offline integration gate

The existing Aave reader step adds one fourth command, text inspection. Engine
semantic check, CLI verify and default JSON inspection preserve their original
three whole outputs. All four statuses/stdout/stderr and19 source/sample hashes
are saved before assertions. The text must match both this3013-byte golden and
the selected CLI's test golden; the selected CLI sample must equal the original
Engine report completely. All19 inputs match immutable selected Git sources.
See [reader results](local-reader-results.json), [step manifest](local-reader.json)
and [source identities](immutable-sources.json).

Each process denies socket connects; CLI paths additionally deny Engine import,
SDK HTTP requests and export-ledger construction. These are offline tripwires,
not a sandbox for arbitrary code. All other workflow content and step bodies are
unchanged except the selected bounded-default CLI checkout. Frozen dependency,
quality-variant and host-bounds pins, old evidence and media retain their bytes.
Only this updated four-command reader ran locally; original remaining gates
are exercised by mandatory coordinator CI, not redundantly rerun locally.

## Component checks and remaining publication gates

[CLI CI evidence](cli-ci.json) links all six current checks, successful on original
attempt1:107 tests on each Python3.11/3.12/3.13 with no skips,24 installed cases,
14 runtime module identities,11 scanned sources and42 locked Python dependencies
with zero reported advisories. Documentation checks cover14 documents/68 links:
67 successful, one unchanged inherited loopback exclusion, zero errors/timeouts.
Independent raw review and parent rehash cover whole logs, artifact ZIPs, wheels,
immutable sources and the published tree, which matches the actual CI merge tree.
The [CLI implementation evidence](https://github.com/entrotter/cli/tree/169b759aff9280ce44fb0d15569c7ae0a4a40889/evidence/result-text)
records exact integer/36-decimal controls and isolated installation. OS/Cargo/kernel
audits belong to separately pinned Engine evidence, not current CLI quality.

Current coordinator CI, independent review and branch publication are separate
from protected-main approval and live Pages. No fresh local EVM, RPC, model,
browser or performance run, paid generation, registry publication or formal
submission is claimed. Existing videos retain their original versions. Human
audio review and supported video delivery remain open; the improvement goal
stays active until the official deadline. Discord and user evaluations are excluded.
