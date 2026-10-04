# Direct recorded price wrapper integration

The proposed composition promotes exactly two viewer selectors to
[a19d3b1 / PR16](https://github.com/entrotter/entrotter.github.io/pull/16), keeping
engine40, SDKee, CLI22, schemas878 and all frozen jobs/model/holdouts unchanged.
The sixth mandatory workflow reader now sends the original sealed observation
wrapper to the actual viewer codec, in addition to the existing engine validation,
quota-bound export and SDK inspection. This lets developers import a supported
CLI price report directly and inspect price phases beside receipt differences.
The [quick start](../../docs/QUICK_START.md) provides the local sample/import path.

All six exact workflow scripts ran once successfully in isolated output paths.
The first five scripts and complete results match the prior composition except
for the viewer pin. The sixth compares the complete nested report, full recorded
classification and four decoded consumer prices, producer answers, source and
aggregator addresses, base currency/unit, heads and code identities. BigInts
remain decimal strings in recorded results; no floating-point price conversion.
The nested trace retains all32 full baseline receipts, one omission and19
structural receipt differences. These checks inspect recorded bytes offline.
They do not execute a new historical replay, browser or model call.

- [Summary and scope](summary.json), [six exact local steps](local-execution.json),
  [typing and retained diagnostics](local-types.json), [workflow parsing](workflow-parse.json).
- [Direct wrapper result](trace-observed-reader.json), [signed-prefix result](trace-reader.json),
  [32-receipt classification](trace-comparison-reader.json), [earlier consumer record](trace-consumer-reader.json),
  [synthetic funding](trace-funding-reader.json), [oracle and missing-storage](trace-oracle-reader.json).
- [Viewer full raw independent CI review](viewer-ci-independent.json), with original
  [source/quality/browser run](https://github.com/entrotter/entrotter.github.io/actions/runs/37047157220)
  and [documentation run](https://github.com/entrotter/entrotter.github.io/actions/runs/37047157381).
  All4 required checks passed:94 Node/11 Python tests,39 browser groups,34 raw
  axe scans with0 violations,122 retained findings,109 npm/42 Python locked
  identities with0 reported advisories,13 documents/66 links. Contrast incompletes
  remain explicit. This source review is separate from human main approval.
- [Copy provenance](provenance.json) binds original/public bytes. An actual
  workspace prefix becomes `$WORKSPACE_ROOT`; raw CI downloads stay retained
  privately. Historical `.quality` paths identify evidence, not prerequisites.

Prior coordinator213 passed all5 original required checks and full independent
raw review: [workspace](https://github.com/entrotter/entrotter/actions/runs/37043199268),
[quality](https://github.com/entrotter/entrotter/actions/runs/37043199336),
[docs](https://github.com/entrotter/entrotter/actions/runs/37043199602).
Its fixture7.635240s/recorded-agent7.390132s use configured running Docker/cgroup-v2
and potentially warm caches, excluding installation and VM startup. They measure
that historical composition, not this proposed one or a speed advantage.

New combined current-head CI, independent human protected-main approval and
candidate Pages deployment remain separate gates. Read-only price dependence is
not signed consumer strategy, profit, provider/deployed-code authenticity or
full-block/root/opcode/defaultDocker32 proof. Videos and submitted versions are
unchanged; no formal submission is claimed.
