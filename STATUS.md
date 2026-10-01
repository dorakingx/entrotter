# CLI candidate status

## October 1 — Built-in agent execution and recorded replay

The CLI adds `agent-run` for the bounded built-in risk policy and `replay` for a
verified complete agent report. Replay derives original steps/gas budget, verifies
complete returned equality before export and never calls a model. `inspect`
displays the original decisions/reasons/provider provenance without an engine.
The optional engine stub includes this API; no runtime dependency, external
provider loader, native fallback or v0.1 report/schema change is introduced.

The missing-command regression fails before the change. Final engine-free units,
actual local Docker tests and production quality results are bound in
evidence/agent-cli/summary.json. Existing frozen model/risk samples are copied
byte-for-byte with exact provenance, not regenerated or retuned. New actual CI
pins engine c167193 and SDK b0c2ba3; package/unit jobs remain engine-free. Current
head CI, independent review and branch-protection coverage are recorded separately
in the PR/coordination checkpoint. A workflow definition is not execution evidence.

Main integration/deployment/submission remain pending. This is data-only replay
of supplied actions under matching observations, not later-block historical trace
replay, new agent advantage or full host/daemon/VM resource isolation. The original
model's unknown served snapshot/cost and nondeterminism remain disclosed.
