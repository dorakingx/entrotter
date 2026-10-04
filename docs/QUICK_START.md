# Reproduce Entrotter from one clone

This guide targets the migration candidate in dorakingx/entrotter. Formal transfer,
branch publication, required CI and independent main approval are separate gates.
Check [migration status](../MIGRATION_STATUS.md) before assuming this layout is on main.
Original reports, signed inputs, model recordings and videos are unchanged.

## Requirements

Git, Python 3.11+ and a POSIX shell support offline inspection. New execution
requires a local Docker daemon with cgroup v2 and the source-bound worker image.
Native EVM development/tests require Anvil v1.8.3. Website tests require Node
20.19+ (CI uses Node22). No Entrotter package is published to PyPI.

## 1. Clone once and inspect offline

After the migration branch is published:

```bash
git clone --branch migration/monorepo https://github.com/dorakingx/entrotter.git entrotter &&
cd entrotter &&
PYTHONPATH=cli/src:sdk-python/src python3 -m entrotter_cli verify cli/tests/data/aave-borrow-result.json &&
PYTHONPATH=cli/src:sdk-python/src python3 -m entrotter_cli inspect cli/tests/data/aave-borrow-result.json --format text
```

An existing migration checkout can run the two Python commands directly.
Inspection reads a recording; it makes no model, Docker or RPC call. Content
integrity does not authenticate execution or prove profit.

## 2. Build and configure the local worker

From the monorepo root:

```bash
export PYTHONPATH="$PWD/engine/src:$PWD/sdk-python/src:$PWD/cli/src"
export ENTROTTER_DOCKER_SOCKET=/var/run/docker.sock
python3 engine/scripts/build_worker.py --output worker-image.json
export ENTROTTER_WORKER_IMAGE="$(python3 -c 'import json; print(json.load(open("worker-image.json"))["image_id"])')"
```

Use your actual Unix Docker socket: Docker Desktop or Colima may use a path under
$HOME instead of /var/run/docker.sock. Build preparation verifies the pinned
Foundry archive and uses the installed local daemon. Read the
[engine worker instructions](../engine/README.md#default-bounded-local-worker) and
[security limits](../engine/SECURITY.md). A missing daemon or invalid image fails;
normal execution never falls back to native. Rebuild after runtime source changes.
The backend and Anvil must stay local.

## 3. Run, verify and inspect

```bash
python3 -m entrotter_cli run scenarios/fixtures/liquidity-shock.json --local -o report.json
python3 -m entrotter_cli verify report.json
python3 -m entrotter_cli inspect report.json --format text
python3 -m entrotter_cli exports
```

This is an invented offline price path, not historical trading performance.
Exports use the existing private quota ledger. Do not reset it while retaining outputs.

<a id="4-run-agent-decisions-and-replay-the-recorded-model"></a>

## Recorded model replay

With the bounded worker configured:

```bash
python3 -m entrotter_cli replay evidence/agent-local-codex.json -o replayed.json
python3 -m entrotter_cli verify replayed.json
```

This replays saved decisions on local Anvil without a new model call. Frozen
benchmarks retain their original source/prompt/holdout identities; migration
is not a new model evaluation or evidence of advantage.

<a id="compare-supplied-aave-borrowing-actions"></a>

## Compare supplied Aave borrowing actions

```bash
python3 engine/scripts/aave_borrow.py --check engine/evidence/aave-borrow-actions/report.json
python3 -m entrotter_cli inspect engine/evidence/aave-borrow-actions/report.json --format text
```

The recorded baseline9 WETH borrow reverts while the built-in candidate holds;
both later execute a supplied1 WETH borrow. Artificial20 ETH funding and local
impersonation remain explicit. Exact balances and gas are not financial returns.
For new archived-state execution, configure your own archive-capable
ENTROTTER_RPC_URL privately and run the same script with --output instead of --check.
Do not put credentials in a report, shell history, screenshot or public issue.

<a id="optional-original-transaction-prefix-replay"></a>
<a id="replay-historical-prices-through-the-bounded-worker"></a>
<a id="compare-historical-aave-account-impact"></a>

## Original prefix, price and account records

```bash
python3 -m entrotter_cli observed-inspect website/reports/trace-observed-price32.json --format text
python3 -m entrotter_cli position-inspect website/reports/aave-account-impact13.json --format text
```

These are offline checks of existing partial-prefix recordings. The
[engine guide](../engine/README.md#original-transaction-prefix-replay) describes
bounded trace execution and its archive prerequisites. Missing state, provider
latency and unsupported queries remain failures or explicitly unproven results.
No report author-supplied address, model or executable becomes runtime configuration.

## Local viewer and checks

```bash
python3 -m http.server 8880 --bind 127.0.0.1 --directory website
```

Open http://127.0.0.1:8880/?report=aave-borrow-actions#report-explorer.
Imports stay in the browser and do not call an RPC. The new hosted static site is
[entrotter.vercel.app](https://entrotter.vercel.app/); the migration candidate's
publication is separate from its initial reviewed deployment.

Install the hash-locked developer requirements when running contract/quality
checks. With Anvil and the current worker configured, run:

```bash
python3 scripts/verify.py --require-anvil
```

Fresh results go to evidence/monorepo-verification; old evidence is not overwritten.
A clean-clone reproduction uses scripts/reproduce_clean.py --bounded or
--bounded-agent. It clones only the current local monorepo into a temporary
directory, builds the worker and verifies exact output; it is distinct from a
fresh public GitHub clone, which remains a publication gate.

## Preserved native model experiments

The historical benchmark/check_agent helpers require their original clean
Enginebb8 source. They refuse the current bounded Engine before execution;
they are distinct from the current CLI replay. To prepare that exact source
without an old Org fetch:

```bash
git worktree add --detach .quality/frozen-engine bb8b3e8d32c7cbd49629d337758f30bfdf805045
```

Only an explicitly selected PYTHONPATH pointing to .quality/frozen-engine/src
can run those native development helpers. Their CPU/RSS, image and host scope
retain the original documented limits. Model generation remains explicitly
opt-in; frozen evidence and holdouts must never be overwritten.
