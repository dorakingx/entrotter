# Bounded agent integration and exact archived-report reproduction

[Engine PR #21](https://github.com/entrotter/engine/pull/21) integrates the causal
agent contract into the hardened worker at
`abb4662ce960e08b2aa3a2c8a1c10719339edccc`, based on
`0d3857839b2187541e573bec2e58042ad5bf0b45` (PR #20). It carries the original
causal observations/decisions from frozen agent
`bb8b3e8d32c7cbd49629d337758f30bfdf805045`; that checkout, the scenarios,
provider source, prompt, benchmark inputs and original reports stay unchanged.
[Tracking issue #38](https://github.com/entrotter/entrotter/issues/38) covers this
integration. The code and stacked prerequisites require independent approval.

## What is now bounded

The new Python `run_agent(scenario, *, decision_steps, recording=None,
max_requested_gas=2000000)` either uses the built-in current-state risk policy or
replays data-only recorded choices. It always enters the configured Docker worker;
no fallback, external provider import, shell command or model call is available.
Ordinary `run`, CLI and API defaults retain the same bounded execution. Agent
execution is not added to HTTP or CLI in this slice.

Risk/replay share the daemon's one-worker admission slot and owner-specific
cleanup. They inherit one CPU, 512 MiB/no swap, 128 PID/thread slots, read-only
non-root execution, 64 MiB temporary storage, 16 MiB shared memory, and independent
180-second worker / 190-second host timers. Local cases run with network disabled;
fork cases retain the documented general archive bridge. This is not arbitrary
code egress isolation or a sandbox for a malicious operator-selected image.

The private transport has a separate version (`1`) and response digest binding to
the complete input. Selection, cumulative requested gas and recording are part
of that digest. Public scenario/result/agent schemas remain v0.1. Scenarios retain
256 KiB, recordings 3 MiB, complete agent input 4 MiB and complete worker output
8 MiB bounds. The worker initially reads at most 4 MiB plus one byte, then rejects
ordinary scenario messages over 256 KiB. Host Python object construction and
serialization are not kernel bounded by this transport policy.

The **unmerged prototype** Python API `run_agent(scenario, controller)` is now
explicit `run_agent_native(scenario, controller)` for trusted custom providers.
Those callbacks execute caller code in the host with no whole-process CPU/RSS or
egress sandbox; before/after deadline checks cannot interrupt a hung callback.
Frozen benchmark scripts keep their original dependency pins and API. This change
does not publish a package or claim a new recorded model generation.

## Measurements and retained evidence

- 189 native/unit tests with actual Foundry 1.8.3, including provider failure and
  cancellation cleanup, causal/future boundaries and exact frozen model replay.
  Python 3.11–3.14 offline jobs each discover 189 tests and explicitly skip the
  19 Anvil-dependent cases; the separate Anvil job runs all 189 without skips.
- 21 real Docker tests, including five new agent groups: risk/native equality,
  exact recorded-model replay, a recording larger than 256 KiB, state/budget
  divergence and recovery, and a tight cumulative requested-gas budget. Existing
  real kernel CPU/OOM/PID/tmpfs controls and owner-loss/SIGTERM tests remain active.
- All 19 original EVM reports are re-executed under the final bounded image and
  compared as complete JSON objects, including content IDs: 16 archived-state
  executions and three local cases, with 12 agent recordings replayed. No model
  was called, policy retuned, holdout added, or source report rewritten. This is
  compatible reproduction, not a new evaluation of model quality or advantage.
- All 22 production Python files pass Ruff lint/format and normal mypy, without
  ignores added. Full Bandit retains all 24 expected findings (20 low/four medium)
  with source/finding hashes and author rationales; the stale review fails before
  refresh. These rationales still need independent review.
- Strict audits cover all 42 hash-locked Python tools, 26 detected worker OS
  packages and all 1,126 Cargo package entries in Foundry's signed upstream SBOM,
  with no known findings or skipped Python packages. The SBOM's 172 non-Cargo
  entries and compiler/build/host/daemon limitations remain disclosed.
- All 17 packaged Python module bytes match local source and the downloaded Linux
  wheel. CI Bandit fingerprints/source inventory and Python dependency identities
  match local exactly. No runtime dependency or schema changes are introduced.

The first protocol regression fails against the pre-integration checkout because
the agent module/entrypoint is absent. During integration, three mypy diagnostics
required concrete annotations/guards; test expectations were corrected to accept
the prototype's distinct `AgentError` type. No checks or scanner rules were
suppressed. The first full local Docker run preceded a module-docstring-only edit;
its image manifest is retained separately. The repeated final-source native/Docker suites, archived-report executions and
CI use the final source and manifests below. See the evidence summary for exact run/log distinctions.

Local final image: `sha256:626ca28986b4ca5da93df1438a705f1757bb35afcd42f77b539bab7d66d7a485`.
Source digest: `fba06f6dd633858f91dd89d4f48a51c8447696f32e9eb3820302d09bcb379f42`.
The ARM64 worker runs Python 3.14.7 and Anvil 1.8.3; host Python is 3.13 on macOS.
The dedicated two-CPU, 2 GiB Colima VM and image setup are prerequisites, not part
of per-case timing. Historical reads use the public archive endpoint previously
used for the frozen benchmark. Generation cost is zero new model calls; RPC
availability/charges depend on the operator's chosen provider.

## Reproduce

From a separate engine checkout at the integration commit, configure the local
Docker Unix socket and build the image using the engine README. Install the
verified native Foundry version for comparisons and run:

```bash
export PYTHONPATH="$PWD/src"
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests_isolated -v
python3 - <<'PY'
import json
from pathlib import Path
from entrotter_engine.runner import run_agent
reference = json.loads(Path("tests/data/agent-recorded-local.json").read_text())
actual = run_agent(reference["scenario"], decision_steps=[0, 1], recording=reference["agent"])
assert actual == reference
print(actual["artifact_id"])
PY
```

The local example needs no model, archive access or signing key. The 19-report
comparison additionally requires the existing coordination evidence checkout and
archive access via `ENTROTTER_RPC_URL`. Iterate the 15 `causal-v1/causal-uniswap-*.json`
reports, three `agent-local-*.json` reports and `historical-uniswap.json`. For agent
reports, select the recorded observation steps, use the first request's
`limits.remaining_requested_gas` as the initial budget, and pass the unmodified `agent` object; for
non-agent reports use `runner.run`. Compare the entire returned object with its
reference, not only metrics. Input/output file hashes and each case's elapsed
seconds are recorded in `evidence/bounded-agent/reproduction/summary.json`.

Linux checks all passed on the exact commit:
[units](https://github.com/entrotter/engine/actions/runs/35477273945),
[native Anvil](https://github.com/entrotter/engine/actions/runs/35477273947),
[Docker and signed image/native audits](https://github.com/entrotter/engine/actions/runs/35477273936),
[quality](https://github.com/entrotter/engine/actions/runs/35477273927), and
[docs links](https://github.com/entrotter/engine/actions/runs/35477273922).
The independent idle timer was observed at 180.311 seconds in Linux CI.
Downloaded AMD64 image manifests contain the same source digests as local ARM64;
image/binary IDs correctly differ by architecture. The artifact's `.quality`
directory name is omitted in the evidence copy so Git tracks its entire contents.
Raw large inventories/logs are losslessly gzipped, with decompressed hashes retained.

Run URLs, complete audit inventories, source/image pins, logs and artifact hashes
are in `evidence/bounded-agent/summary.json`. Kernel/transport quotas do not cover
host caller overhead, image/VM storage, noncooperating clients or arbitrary native
providers. Historical trace replay, independent security/merge review, website
deployment, manual accessibility checks, real user feedback and final submission
requirements remain open. No new model advantage or live-site change is claimed.
