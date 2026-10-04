# Entrotter

[Workspace setup](#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [First contributions](docs/FIRST_CONTRIBUTION.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

**A time machine for onchain agents.**

Rewind a state. Change a decision. Inspect the evidence.

Entrotter is local-first, MIT-licensed simulation software, not a trading website
or a price predictor. The intended users are teams evaluating onchain agents
before giving them production permissions.

## Current release: experimental 0.1.0

This workspace contains a working offline stress-test engine, a loopback-only
API, a Python SDK, a CLI, and a static report/documentation site. It also includes
an Anvil adapter for paired local or archived-state EVM execution. Genuine Anvil
and archive-RPC validation is a separate gate: do not infer it from offline tests.
See `STATUS.md` and `evidence/` for exactly what has and has not run.

The source is being migrated to the single public MIT repository
`dorakingx/entrotter`; formal transfer and the migration PR are pending.
The independently reviewed static viewer is live at https://entrotter.vercel.app/.
Packages remain unpublished and the backend runs locally. See
[MIGRATION_STATUS.md](MIGRATION_STATUS.md) for exact completed and pending gates.

## Components

| Folder | Owns |
| --- | --- |
| Project root | Roadmap, goal, integration tooling and submission evidence |
| [engine/](engine/README.md) | Validation, local experiments, Anvil and API |
| [sdk-python/](sdk-python/README.md) | HTTP client, typed results and integrity checks |
| [cli/](cli/README.md) | Commands and developer diagnostics |
| [scenarios/](scenarios/README.md) | Schemas, fixtures and source provenance |
| [website/](website/README.md) | Static OSS documentation and read-only inspection |

One clone contains all components. The v0.1 JSON/API contract, component licenses
and author notices are preserved. Choose a small component-scoped contribution;
there is no sibling-checkout or additional Entrotter repository requirement.

<a id="quick-start-without-dependencies-or-an-api-key"></a>

## Quick start: inspect a recorded result

To see what an Entrotter report contains, you need Git and Python 3.11+ on
macOS or Linux. The CLI already includes the original Aave recording, so this
path needs no Docker, package installation, wallet or API key. Setup downloads
public source; verification and inspection afterward run locally.

After formal transfer and publication of the migration branch, clone it once.
Until independent main integration, use the explicit migration branch rather
than assuming main already contains the new layout. From an empty directory:

```bash
git clone --branch migration/monorepo https://github.com/dorakingx/entrotter.git entrotter &&
cd entrotter &&
PYTHONPATH=cli/src:sdk-python/src python3 -m entrotter_cli verify cli/tests/data/aave-borrow-result.json &&
PYTHONPATH=cli/src:sdk-python/src python3 -m entrotter_cli inspect cli/tests/data/aave-borrow-result.json --format text
```

For a local checkout of this migration candidate, start at `cd entrotter` and
run the two Python commands. Historical source identities are recorded in
[migration-manifest.json](migration-manifest.json); fresh one-clone validation
is a separate migration gate.

The text shows exact native/token balance changes, gas, failed transactions and
assumptions. In this recording, the supplied baseline 9 WETH borrow reverts while
the candidate preflight policy holds; the later supplied 1 WETH borrow succeeds
in both branches. This reads an existing report. It does not run new chain
transactions or prove model advantage, execution authenticity or financial return.
Hash verification checks content integrity. The pinned sources are reviewed
candidates awaiting independent human-main approval, not published packages.
Read the [recording and limits](engine/evidence/aave-borrow-actions/README.md)
and [executed walkthrough evidence](evidence/recorded-quick-start/README.md).

## Run a new simulation

Follow the [single-clone guide](docs/QUICK_START.md) for local source setup,
bounded Docker configuration and simulation. All components are in this clone;
no old Org checkout or registry Entrotter package is required. Docker absence or
an invalid source-bound image fails execution without a native fallback.

For offline inspection, the CLI needs only `cli/src:sdk-python/src`. For
execution and the local API, include `engine/src` and configure the worker first.
The optional archive RPC credential stays in the operator's private environment.
No command broadcasts a transaction to an upstream chain.

## Static website and publication

The new static project is [entrotter.vercel.app](https://entrotter.vercel.app/).
The initial reviewed site is published; this migration branch has not yet been
transferred, independently integrated or published. See [MIGRATION_STATUS.md](MIGRATION_STATUS.md).

From this repository root, `python3 scripts/publish.py` stages the explicit
public allowlist into `website/_site`. [Hosting instructions](docs/HOSTING.md)
explain the new Vercel configuration. The retired Org/Pages bootstrap command
fails closed. Backend execution stays local.

## Work toward the competition goal

Follow [CODEX_GOAL.md](CODEX_GOAL.md), the current [status](STATUS.md) and
[release gates](release-gates.json). Historical evidence below remains unchanged;
migration, tests, deployment and submission are checkpoints rather than goal completion.

## Actual archived-state evidence

The [Uniswap scenario](https://raw.githubusercontent.com/entrotter/scenarios/8785bb090c13390b783fe8c42f01b26f1d5e7c24/evm/ethereum-uniswap-slippage.json)
compares a successful 1 WETH swap with a reverted minimum-output intervention on
identical Ethereum block 19,000,000 state. Two runs yielded identical artifacts;
see `evidence/historical-verification.json` for timings and resource scope.

```bash
# Public endpoint used during verification; archive availability can change.
export ENTROTTER_RPC_URL=https://eth.drpc.org
PYTHONPATH=engine/src python3 scripts/check_historical.py
```

Foundry v1.8.3 is required. On macOS, if Python lacks a certificate bundle, set
`SSL_CERT_FILE=/etc/ssl/cert.pem` to use the trusted OS bundle. Never disable TLS.
This is supplied-action execution on archived state, not historical trace replay,
a reconstructed alternative market, or an integrated-agent benchmark.

## Recorded model decisions

These development records retain their original source and measurement scope.
Use the current single-clone guide for bounded execution and Vercel hosting.

The proposed [recorded-agent viewer](https://github.com/entrotter/entrotter.github.io/pull/14)
lets contributors open the v0.1 report explorer and select **Local EVM · recorded
model decisions**. It places preflight, gas budget, execute/hold and reasons beside
candidate receipts while preserving original model/cost uncertainty. The current
[pinned quick start](docs/QUICK_START.md) selects that tested candidate; independent
approval and live publication remain pending. Original media and model evaluation
inputs retain their separate versions.


The experimental local controller now connects typed `execute`/`hold` model
responses to real Anvil execution and replays a full recording without another
model call. In the artificial transfer/revert example, the model and a simple
preflight rule made identical decisions; the rule was faster. See
[agent evaluation](docs/AGENT_EVALUATION.md) for receipts, measured timings,
metadata, exact replay commands and pending historical/holdout work. The engine
and schema PRs require independent review before this becomes a main-branch release.

The [pinned quick start](docs/QUICK_START.md#4-run-agent-decisions-and-replay-the-recorded-model)
now includes proposed standalone CLI risk execution and complete recorded-model
replay. These commands reuse original decisions and make no new model call;
independent review and main integration remain pending.

The [frozen historical comparison](docs/HISTORICAL_AGENT_EVALUATION.md) now includes
three sourced cases and two previously unused implementation holdouts. All ten
risk/model recordings replayed exactly on fresh forks. The model matched the
preflight rule and took longer in every case; evidence retains that adverse result.

The [direct Anvil comparison](docs/DIRECT_ANVIL_COMPARISON.md) independently
reproduced the same receipts and state in six runs. Median runtimes were similar;
Entrotter's additional value is its reusable scenario, recording and artifact
workflow, which still needs genuine user validation.

The [local worker security evidence](docs/WORKER_SECURITY.md) records real kernel
resource-limit and process-lifecycle checks for the proposed opt-in Docker path.
This remains under review; native defaults and aggregate storage/concurrency
limits are open gates.

The [host resource bounds](docs/HOST_RESOURCE_LIMITS.md) add proposed API report
quotas, connection limits and safe CLI exports, with real CLI/SDK/API fault and
recovery evidence. These PRs remain subject to independent review.

[Documentation link checks](docs/LINK_CHECKS.md) describe the shared CI policy,
local reproduction, full result artifacts and the limits of static link scanning.

[SDK and CLI quality evidence](docs/SDK_CLI_QUALITY.md) records independent source,
dependency, packaging and real API checks, including the local SDK provenance.

[Report viewer accessibility evidence](docs/WEBSITE_ACCESSIBILITY.md) records
keyboard/reflow regressions, exact chart alternatives and actual Linux browser
CI. These proposed changes still await review and deployment.

[Bounded default execution](docs/BOUNDED_DEFAULT.md) records the proposed change
from opt-in workers to normal CLI/API execution with kernel limits. Its separate
source pins and migration instructions require a local Docker daemon. The quick
start uses this candidate; frozen native benchmarks retain their original pins.

[Shared daemon worker admission](docs/DAEMON_WORKER_ADMISSION.md) records the
proposed one-worker default across independent CLI/API processes, ownership-safe
cleanup, real contention tests and explicit recovery limits.

[Shared CLI export retention](docs/SHARED_EXPORT_BUDGET.md) records proposed
cross-process saved/pending report limits, crash recovery and operator inspection.

[Coordination quality](docs/COORDINATION_QUALITY.md) records complete tooling scans,
optimized-Python verification, locked dependencies and frozen-source exceptions.

[Offline schema contracts](docs/SCENARIO_CONTRACTS.md) records local reference
resolution, mandatory checks, frozen input compatibility and scenario quality CI.

[Website quality](docs/WEBSITE_QUALITY.md) records numeric input regressions,
complete source checks, retained findings and actual browser/CI evidence.

The proposed [bounded agent integration](docs/BOUNDED_AGENT_REPLAY.md) reproduces
all 19 existing EVM reports under the worker quotas, including 12 agent-recording
replays without model calls. This is verified on an open branch; independent
approval and dependency-pin integration remain pending.

[Current account-impact demo](submission/media/entrotter-demo-account.mp4) shows exact account changes, receipt evidence and altered-file rejection in 2:36.80; its [source-bound recording evidence](evidence/submission-account-demo/README.md) distinguishes new local execution from recorded historical inspection. Original approved media remains unchanged.

[Submission review package](submission/README.md) includes recorded pitch/demo
videos, measured evidence, explicit AI/prior-work disclosure and unvalidated
market/evaluation plans. Owner review and genuine demand validation remain open.

[Fresh bounded agent reproduction](docs/BOUNDED_AGENT_INTEGRATION.md) combines
immutable public checkouts, a new venv and worker build, exact recorded-agent replay
and standalone CLI verification. Docker/VM setup is a measured-scope prerequisite.

[Required CI checks](docs/REQUIRED_CHECKS.md) records the enforced main-branch
policy, successful source checkpoints and migration of older partial PRs.

[Bounded API host service](docs/BOUNDED_HOST_SERVICE.md) adds a verified Linux
service envelope and dedicated-VM operating profile, with measured scope limits.

[Bounded Linux CLI](docs/BOUNDED_CLI.md) adds an optional per-user caller budget,
atomic admission and owner-death cleanup, with actual production-timer evidence.
