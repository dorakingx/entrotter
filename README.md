# Entrotter

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
| `entrotter/entrotter` | Roadmap, workspace, goal and submission evidence | Runtime business logic |
| `entrotter/engine` | Validation, experiments, Anvil, local API | Frontend or SDK |
| `entrotter/sdk-python` | HTTP client, typed results, hash checks | Engine internals |
| `entrotter/cli` | CLI and user-facing diagnostics | Protocol simulation |
| `entrotter/scenarios` | Schemas, fixtures and scenario provenance | Service execution |
| `entrotter/entrotter.github.io` | Documentation and report viewer | Wallet keys, accounts or backend compute |

Keep the six checkouts as sibling directories. Schema and API version 0.1.0
is the contract between them. Do not split further until there is an independent
contribution boundary that justifies another repository.

## Quick start without dependencies or an API key

Clone the public repositories as siblings first:

```bash
mkdir entrotter-workspace && cd entrotter-workspace
for repo in entrotter engine sdk-python cli scenarios entrotter.github.io; do
  git clone https://github.com/entrotter/$repo.git "$repo"
done
```

From that workspace folder:

```bash
export PYTHONPATH="$PWD/engine/src:$PWD/sdk-python/src:$PWD/cli/src"
python3 -m entrotter_cli doctor
python3 -m entrotter_cli run scenarios/fixtures/liquidity-shock.json --local -o report.json
python3 -m entrotter_cli verify report.json
python3 -m entrotter_cli inspect report.json
python3 entrotter/scripts/verify.py
```

For normal editable package installation, run `bash entrotter/scripts/bootstrap.sh`.
Do not install these names from a public package registry: they are not published.
The bootstrap installs the sibling source checkouts with `--no-deps` to avoid
accidentally resolving an unrelated package with the same name.

## Local API and SDK

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
  Install Foundry first. No mainnet RPC or wallet key is needed.
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
