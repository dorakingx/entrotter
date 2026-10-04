# Exact recorded Aave outcomes across CLI and browser

The candidate selects viewer [37c43d0](https://github.com/entrotter/entrotter.github.io/tree/37c43d0cf8be61dfd33253bc2d3401429ca9cd9b)
alongside Engine f53a66a, SDK ba4af51 and CLI 169b759. Choose **Ethereum · recorded
Aave supply and borrow** in the v0.1 explorer to inspect the original 59,506-byte
action recording. Native/ERC-20 initial/final/change and candidate-minus-baseline
values preserve all decimals; token addresses/units bind to scenario declarations.
Missing observations remain Unavailable and duplicate symbols retain addresses.
The general display checks selected integer/accounting consistency, not execution
authentication or valuation. All existing report contracts and videos are retained.

Both branches supply 10 WETH, propose borrowing 9 WETH and execute a supplied
1 WETH borrow. Baseline reverts on the larger proposal; candidate preflight holds.
Both finish with 1 WETH, 10.000000094454558462 aWETH and 1 variable-debt token.
The smaller action is supplied, not agent-generated. Artificial funding, local
impersonation, differing gas prices and archived-state scope remain explicit.
Native/gas differences are not profit. These are earlier recorded executions;
the current browser and offline reader do not run an EVM, model or upstream RPC.

## Current offline composition

The existing **Inspect recorded Aave supply and borrow actions offline** step in
[the integration workflow](../../.github/workflows/ci.yml) adds one Node command
that loads the exact production app in a VM with inert DOM and rejected fetch.
It verifies the original content seal and inspects native/token rows, source,
identities and the recorded hold. Awaiting the asynchronous agent view is required;
the initial reader missed that await and failed its required-field assertion.
Original failure outputs are retained privately; the corrected actual step passes
without weakened assertions. This VM check is distinct from actual browser tests.

The original four Engine/CLI/SDK command outputs match their complete prior
goldens. The fifth command matches every field of the selected public browser
view, including all sixteen four-column rows. Engine, CLI and viewer sample bytes
are identical; all 22 source/sample inputs match immutable selected Git commits.
[Reader results](local-reader-results.json), [step execution](local-reader.json)
and [source identities](immutable-sources.json) retain those exact observations.

Python reader processes deny socket connects; standalone CLI additionally denies
Engine imports, SDK HTTP calls and export-ledger construction. The production
browser app's fetch throws, its synchronous VM evaluation is bounded to two
seconds, and each command has a 30-second timeout. These are offline tripwires,
not a sandbox for arbitrary code. All other workflow content/steps remain exact
from coordinator 07389e3, apart from the selected viewer checkout and this step.
Frozen quality/dependency/host pins, old evidence and media are unchanged. Only
this updated five-command reader ran locally; remaining unchanged gates are
exercised by mandatory coordinator CI.

## Component evidence and publication limits

[Viewer CI](viewer-ci.json) links all four mandatory original-attempt1 checks.
The fresh Linux run passes 131 Node tests, 12 Python site tests, 47 browser groups
and 61 complete axe scans with zero violations/JavaScript errors. All 22 browser
runtime hashes match the exact published source. The source-bound security scan
retains 148 reviewed findings across 19 JS and 20 typed inputs; 137 inherited
reasons are exact, two obsolete contexts removed and eleven individually added.
An initial rationale-mapping defect was independently found and fixed before push.
All 109 Node and 42 Python locked dependency identities have zero reported
advisories. Documentation checks cover 17 documents, 103 links and 90 unique
targets with zero errors/timeouts/exclusions. Whole original ZIP entries, logs,
published blobs and actual merge tree match the independent review and parent
rehash. [Viewer implementation evidence](https://github.com/entrotter/entrotter.github.io/tree/37c43d0cf8be61dfd33253bc2d3401429ca9cd9b/evidence/aave-outcomes)
records actual source-bound browser and display-consistency controls.

Axe incomplete contrast items are retained separately from strict opaque-color
checks; mobile uses horizontal scrolling and these checks do not establish manual
screen-reader certification or complete WCAG conformance. Current coordinator CI,
independent source review, protected human main approval and live Pages remain
separate gates. No new local EVM/model/archive/browser/performance execution,
paid generation, package publication or formal submission is claimed. The goal
stays active through the official deadline; Discord and user evaluation are excluded.
