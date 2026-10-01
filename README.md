# Entrotter

[Workspace setup](https://github.com/entrotter/entrotter#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [First contributions](docs/FIRST_CONTRIBUTION.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

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

All six repositories are public at the links below. The documentation site is
live at https://entrotter.github.io/. Packages remain unpublished and the engine
runs locally. See STATUS.md for current verification and open acceptance gates.

## Repositories

| Repository | Owns | Does not own |
| --- | --- | --- |
| [entrotter/entrotter](https://github.com/entrotter/entrotter) | Roadmap, workspace, goal and submission evidence | Runtime business logic |
| [entrotter/engine](https://github.com/entrotter/engine) | Validation, experiments, Anvil, local API | Frontend or SDK |
| [entrotter/sdk-python](https://github.com/entrotter/sdk-python) | HTTP client, typed results, hash checks | Engine internals |
| [entrotter/cli](https://github.com/entrotter/cli) | CLI and user-facing diagnostics | Protocol simulation |
| [entrotter/scenarios](https://github.com/entrotter/scenarios) | Schemas, fixtures and scenario provenance | Service execution |
| [entrotter/entrotter.github.io](https://github.com/entrotter/entrotter.github.io) | Documentation and report viewer | Wallet keys, accounts or backend compute |

Keep the six checkouts as sibling directories. Schema and API version 0.1.0
is the contract between them. Do not split further until there is an independent
contribution boundary that justifies another repository.

<a id="quick-start-without-dependencies-or-an-api-key"></a>

## Quick start: reproduce the tested candidate locally

Follow the [pinned quick start](docs/QUICK_START.md) to fetch compatible public
source revisions, build the Docker worker and produce a verified offline report.
You need Python 3.11+, Git and a running local Linux Docker daemon with cgroup v2.
Setup downloads public build inputs; running the fixture afterward needs no
network, wallet or paid API key. There are no third-party Python runtime packages.

The guide selects tested candidate commits that still await independent review
and integration. Cloning all repositories at `main` currently selects an older
native runtime; it does not reproduce the candidate's bounded default.

For normal editable package installation, run `bash entrotter/scripts/bootstrap.sh`.
Do not install these names from a public package registry: they are not published.
The bootstrap installs the sibling source checkouts with `--no-deps` to avoid
accidentally resolving an unrelated package with the same name. Run it only after
the pinned checkout steps; it does not select candidate revisions, install Docker
or build/configure the worker. Build-time package tooling may require network access.

## Local API and SDK

After completing the quick start, keep its environment variables in both terminals.
For additional Linux API-process limits, use the optional
[bounded host service](docs/BOUNDED_HOST_SERVICE.md).

```bash
# Keep this port local. Optionally set ENTROTTER_API_TOKEN on both client and server.
python3 -m entrotter_engine serve --port 8787 --output artifacts
# In another terminal with the same PYTHONPATH:
python3 -m entrotter_cli run scenarios/fixtures/recovery-trap.json -o report.json
```

```python
import json
from entrotter_sdk import Client
scenario = json.load(open("scenarios/fixtures/liquidity-shock.json"))
result = Client().run(scenario)
print(result.artifact_id, result.report["comparison"])
```

## Three distinct execution modes

- `fixture`: deterministic synthetic price-path model. Runs entirely offline.
  Includes causally evaluated hold/circuit-breaker policies, fees, slippage,
  returns and maximum drawdown. Not historical market evidence.
- `evm-local`: real transactions in two private Anvil processes. Uses fake local
  funding, explicit transaction slots, target allowlists and receipt collection.
  The quick-start worker includes pinned Foundry. No host Foundry installation,
  mainnet RPC or wallet key is needed for this mode.
- `evm-fork`: clones an explicit historical block via the operator-supplied
  `ENTROTTER_RPC_URL`, checks its source chain/hash and runs supplied actions on
  local Anvil. Requires archive state. Does not replay later canonical blocks,
  future prices, MEV, counterparties or agent responses.

```bash
python3 -m entrotter_cli run scenarios/evm/local-branch-revert.json --local -o local-evm.json
# Set ENTROTTER_RPC_URL privately before running the next command.
python3 -m entrotter_cli run scenarios/evm/ethereum-state-fork.json --local -o historical-fork.json
```

EVM native/token balance changes are not PnL. Explicitly listed ERC-20 tokens
are tracked with verified decimals and exact raw-unit deltas. Every report contains its scenario, overrides, trace, assumptions and
SHA-256 digest. The digest detects content changes; it does not prove a simulator
or its economic assumptions are correct.

## Publish the OSS repositories and documentation

Inspect `scripts/publish.py`, then use an authenticated GitHub CLI account with
permission to create public repositories in the existing `entrotter` organization.
No custom domain is configured and no CNAME file is included.

```bash
python3 entrotter/scripts/publish.py          # dry run only
python3 entrotter/scripts/publish.py --apply  # creates public repos, pushes, enables Pages
```

The intended Pages address is `https://entrotter.github.io/`. The script prints
actual results; verify the Actions run and HTTP response before calling it live.
It refuses to replace a non-empty existing remote from a fresh local folder,
never changes a private repository to public, and never force-pushes.

Pages only serves the OSS project docs and public, synthetic example reports.
It does not run the engine, receive private report uploads, connect wallets,
process payments, or provide a commercial SaaS. No hosting spend is necessary
for the local software. Paid hosted compute is a later, separately approved task.

## Work toward the competition goal

Read `CODEX_GOAL.md`, `ROADMAP.md`, `STATUS.md` and `backlog/`. The goal is an
excellent, independently reproducible submission, not a claim that winning
can be guaranteed. Store measured evidence, real feedback and remaining risks.
Do not stop after building a landing page. Do not mark blockers as completed.

## Actual archived-state evidence

The [Uniswap scenario](https://github.com/entrotter/scenarios/blob/main/evm/ethereum-uniswap-slippage.json)
compares a successful 1 WETH swap with a reverted minimum-output intervention on
identical Ethereum block 19,000,000 state. Two runs yielded identical artifacts;
see `evidence/historical-verification.json` for timings and resource scope.

```bash
# Public endpoint used during verification; archive availability can change.
export ENTROTTER_RPC_URL=https://eth.drpc.org
PYTHONPATH=engine/src python3 entrotter/scripts/check_historical.py
```

Foundry v1.8.3 is required. On macOS, if Python lacks a certificate bundle, set
`SSL_CERT_FILE=/etc/ssl/cert.pem` to use the trusted OS bundle. Never disable TLS.
This is supplied-action execution on archived state, not historical trace replay,
a reconstructed alternative market, or an integrated-agent benchmark.

## Recorded model decisions

The experimental local controller now connects typed `execute`/`hold` model
responses to real Anvil execution and replays a full recording without another
model call. In the artificial transfer/revert example, the model and a simple
preflight rule made identical decisions; the rule was faster. See
[agent evaluation](docs/AGENT_EVALUATION.md) for receipts, measured timings,
metadata, exact replay commands and pending historical/holdout work. The engine
and schema PRs require independent review before this becomes a main-branch release.

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
