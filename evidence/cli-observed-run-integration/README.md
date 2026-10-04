# CLI historical price execution composition

The guide now runs fixed Aave/WETH observations with `entrotter_cli trace-observe`.
Exactly four selected CLI references advance 1ee3d3a to d437ad1 after its six
mandatory checks and full independent raw CI review pass. Engine c2eb, SDK eb,
viewer a19, schemas 878 and every frozen execution job remain unchanged.

The CLI adds bounded regular-plan parsing, independent admitted-plan/full SDK
validation, quota-protected atomic export and owned cancellation. Missing workers
fail without fallback. See the [concrete command](../../docs/QUICK_START.md#replay-historical-prices-through-the-bounded-worker)
and [original current CLI CI review](cli-ci-independent.json).

All seven exact offline reader scripts executed once with the new CLI. Complete
receipt, source, plan, classification and four raw/typed observation facts are
preserved; only selected CLI and its exact module hash change. The initial
post-run metadata comparison wrongly expected only a pin change; it was corrected
against old/new Git source hashes without rerunning readers or altering outcomes.
[Execution hashes](local-execution.json) and [provenance](provenance.json) explicitly
reuse the seven older full fact bodies to avoid duplicate report copies.

The CLI's fresh one-input Docker gate is separate from the Engine's recorded
32-input replay. No new CLI32, chain/model/browser, OS/Cargo/kernel audit or speed
comparison is claimed here. Read-only price dependence is not a signed consumer
strategy, profit, provider authentication or full-block/root proof. Current
combined CI, independent human main approval, Pages and submission remain separate.
