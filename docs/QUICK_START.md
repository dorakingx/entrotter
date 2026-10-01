# Reproduce a local report from pinned public sources

This guide uses tested candidate commits awaiting independent review and main
integration. It is not a released package or evidence that the newer website is
deployed. The fixture is a synthetic scenario, not historical market replay.

## Requirements

- Python 3.11 or newer and Git, with a POSIX shell (Linux/macOS).
- Docker CLI and a running local Linux Docker daemon with cgroup v2 and a Unix
  socket. On macOS the daemon runs in a Linux VM; macOS alone cannot provide the
  worker's Linux resource controls. Configure your own local socket below.
- Internet access for public GitHub sources, the checksum-pinned Foundry release
  and the pinned container base image during setup. No wallet, model account or
  paid API key is required. The resulting fixture execution is offline.

Docker installation and VM startup are prerequisites, not part of the measured
five-minute reproduction claim. See [worker security](WORKER_SECURITY.md) for
the tested daemon and limits, and [bounded host service](BOUNDED_HOST_SERVICE.md)
for the optional Linux API-process and VM configuration.

The earlier [agent CLI candidate evidence](../evidence/latest-agent-cli/summary.json)
uses engine c167193 and CLI 87cfe40. Its automated clean public replay includes
five pinned dependency checkouts, a new pipless venv, actual Foundry download/build
and complete recorded-model equality through the standalone CLI. Docker was
running and caches may be warm; installation/VM startup is excluded. The complete
five-block guide walkthrough passed in 26.043 seconds with all six public
checkouts clean and complete fixture/local-Anvil/risk/model equality. That
measurement is recorded separately from the 19.266-second automated replay.

The earlier October 1 [24.431-second walkthrough](../evidence/latest-candidate/summary.json)
selected coordination dcef3ee/engine fa37380 and did not include the new agent CLI.
The [24.35-second run](../evidence/quick-start-oct01/summary.json) used coordination
03f8786/engine d5b3003. The [September 20 measurement](../evidence/quick-start/summary.json)
also retains its earlier pins. These are separate measurements with potentially
warm caches, not cold-machine setup benchmarks. The current commands select
coordination 2204fca, engine 6e13f34 and CLI 22b514c; SDK/schema pins are retained,
with the recorded-agent viewer at49914a2.

The prior [inspection-fix composition](../evidence/agent-inspection-integration/summary.json)
selects the independently code-reviewed CLI fix: extra typed-response fields
cannot replace an observation's displayed step, and malformed responses are
refused before replay execution. All six CLI checks pass with 42 units per Python
version and four actual Docker cases retaining original report equality. Code
review is distinct from protected-main approval. Combined current-head CI and its
clean reproduction artifacts are recorded in the candidate PR: fixture6.308s and
model6.830s belong to coordination328f4c1/enginec167193/CLI22b514c.

The current [contract identity composition](../evidence/contract-identity-integration/summary.json)
selects engine6e13f34. An independent source reviewer reproduced different Anvil
outcomes for canonically equal local contract maps differing only in key order.
Duplicate normalized contract addresses now refuse before native/default/agent
work; a single mixed-case address remains valid. All eight engine checks pass
with214 native tests and22 actual Docker enforcement/cleanup cases. The original
records remain unchanged. Current combined CI and clean reproduction results are
recorded in [candidate PR55](https://github.com/entrotter/entrotter/pull/55);
the older timings above do not measure this new composition. Independent GitHub
approval and protected integration remain pending.

## 1. Fetch a compatible snapshot

Run from a directory where `entrotter-candidate` does not exist. The initial
`mkdir` refuses an existing destination. These commands use a frozen coordination
snapshot and its five dependency pins rather than moving branches. Keep all six
repositories as siblings; do not run this over an existing development workspace.

```bash
set -eu
mkdir entrotter-candidate
cd entrotter-candidate
git init --quiet entrotter
git -C entrotter fetch --quiet --depth=1 https://github.com/entrotter/entrotter.git 2204fcad3dfe329d433806126ee68adb796925b6
git -C entrotter checkout --quiet --detach FETCH_HEAD
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

pins = json.loads(Path("entrotter/bounded-worker-pins.json").read_text())
for name, sha in pins.items():
    subprocess.run(["git", "init", "--quiet", name], check=True)
    subprocess.run(["git", "-C", name, "fetch", "--quiet", "--depth=1",
                    f"https://github.com/entrotter/{name}.git", sha], check=True)
    subprocess.run(["git", "-C", name, "checkout", "--quiet", "--detach", "FETCH_HEAD"], check=True)
    actual = subprocess.check_output(["git", "-C", name, "rev-parse", "HEAD"], text=True).strip()
    if actual != sha:
        raise SystemExit(f"Unexpected source revision: {name}")
    print(name, actual)
PY
python3 -m venv --without-pip .venv
export PYTHONPATH="$PWD/engine/src:$PWD/sdk-python/src:$PWD/cli/src"
```

All commands below run from this new workspace in the same shell. No Python
package installation is needed. The detached checkouts preserve reproducibility;
create a branch in the appropriate repository before making contributions.

## 2. Build and configure the local worker

Set `ENTROTTER_DOCKER_SOCKET` to your daemon's local Unix socket. For a conventional
Linux installation, this is usually `/var/run/docker.sock`. For the dedicated
Colima profile described in the host-service guide, it is
`$HOME/.colima/entrotter/docker.sock`. Do not point it at a remote Docker service.

```bash
export ENTROTTER_DOCKER_SOCKET="${ENTROTTER_DOCKER_SOCKET:-/var/run/docker.sock}"
test -S "$ENTROTTER_DOCKER_SOCKET"
.venv/bin/python engine/scripts/build_worker.py --output worker-image.json
export ENTROTTER_WORKER_IMAGE="$(.venv/bin/python -c 'import json; print(json.load(open("worker-image.json"))["image_id"])')"
.venv/bin/python -m entrotter_cli doctor
```

The builder verifies the daemon and upstream checksums and builds locally; it
does not publish an image. Preparation has a 600-second lifetime cap, with a
separate watchdog for blocked downloads/builds, and forwards at most 1 MiB of build
diagnostics plus one explicit truncation notice. A previously downloaded release archive can be passed
with `--archive /absolute/path/to/release.tar.gz`; it is still checksum-verified.
Image IDs vary by architecture/build; use the manifest from your own build.
On macOS, if Python needs the OS certificate bundle, set
`SSL_CERT_FILE=/etc/ssl/cert.pem`. Do not disable TLS verification.

## 3. Run, verify and inspect

```bash
.venv/bin/python -m entrotter_cli run scenarios/fixtures/liquidity-shock.json --local -o report.json
.venv/bin/python -m entrotter_cli verify report.json
.venv/bin/python -m entrotter_cli inspect report.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path

actual = json.loads(Path("report.json").read_text())
expected = json.loads(Path("entrotter.github.io/reports/liquidity-shock.json").read_text())
if actual != expected:
    raise SystemExit("Report differs from the pinned public fixture")
print("Complete report matches the pinned public fixture")
PY
```

`report.json` remains in your workspace. Inspect its assumptions, baseline and
candidate outcomes. Digest verification detects changed content; the additional
comparison above checks the complete known fixture result. Neither check proves
the economic model is accurate. Choose a new `-o` path to preserve the result of
an earlier run.

The same configured worker can run real local Anvil without archive access:

```bash
.venv/bin/python -m entrotter_cli run scenarios/evm/local-branch-revert.json --local -o local-evm.json
.venv/bin/python -m entrotter_cli verify local-evm.json
```

Keep the exported socket, image and `PYTHONPATH` when starting a local API as
shown in the [README](../README.md#local-api-and-sdk). Per-worker controls do not
cap the entire host CLI, Docker build cache or VM; the optional
[bounded CLI](BOUNDED_CLI.md) and host service have separate scope. Missing worker configuration fails instead of falling back to
native execution.

## 4. Run agent decisions and replay the recorded model

The built-in risk policy needs no model account. The model example re-executes
already recorded choices; no model is called. Both use the bounded local worker,
with synthetic local EVM state and no archive access. Decision steps and the
original requested-gas budget are recovered from the recording for replay.
The recorded risk example contains two explicit baseline transactions. Extract
its embedded scenario so the original input is reproduced exactly; the general
local example above has an empty baseline.

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

reference = json.loads(Path("cli/tests/data/agent-risk-local.json").read_text())
Path("recorded-agent-scenario.json").write_text(json.dumps(reference["scenario"]))
PY
.venv/bin/python -m entrotter_cli agent-run recorded-agent-scenario.json --steps 0 1 -o risk-agent.json
.venv/bin/python -m entrotter_cli replay risk-agent.json -o risk-replayed.json
.venv/bin/python -m entrotter_cli replay cli/tests/data/agent-recorded-local.json -o model-replayed.json
.venv/bin/python -m entrotter_cli verify model-replayed.json
.venv/bin/python -m entrotter_cli inspect model-replayed.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path

for actual, reference in [
    ("risk-agent.json", "cli/tests/data/agent-risk-local.json"),
    ("risk-replayed.json", "cli/tests/data/agent-risk-local.json"),
    ("model-replayed.json", "cli/tests/data/agent-recorded-local.json"),
]:
    if json.loads(Path(actual).read_text()) != json.loads(Path(reference).read_text()):
        raise SystemExit(f"Complete agent report differs: {actual}")
print("Risk execution/replay and recorded-model replay match complete original reports")
PY
```

Inspect displays the original decisions, reasons and provider provenance. The
sample keeps its nondeterministic generation, requested model alias and unknown
original monetary cost. Zero new model calls during replay does not mean the
original generation was free or deterministic. This is supplied-action replay
under matching observations, not later-block historical trace replay or new model
quality/holdout evidence. Invalid or diverged replay preserves an existing output.
The optional Linux service/CLI installation guides retain their separately tested
operator pins; this walkthrough does not claim those service installs were repeated.

## Inspect recorded decisions in the local viewer

From `entrotter-candidate`, serve the checked-out site with
`python3 -m http.server 8000 --bind 127.0.0.1 --directory entrotter.github.io`.
Open `http://127.0.0.1:8000`, expand the **v0.1 report explorer** and select
**Local EVM · recorded model decisions**, or import `model-replayed.json`.
The table joins the original preflight/budget/choice/reason to candidate outcomes.
Original model alias, nondeterminism, unavailable seed/cost and no measured model
advantage remain disclosed. No new model call or upload occurs.

The [tested viewer composition](../evidence/agent-viewer-integration/summary.json)
selects site49914a2/#14. Independent source review resolved three resealed-record
consistency gaps;47Node/11Python tests and28 browser groups/21axe scans pass in
its four required checks. Imported data is not authenticated and selected display
checks do not replace full engine validation. Current combined CI and clean
reproduction artifacts are in [PR55](https://github.com/entrotter/entrotter/pull/55).
All older measurements retain their actual pins; candidate review/publication and
manual assistive-technology/full WCAG checks remain separate gates.
Stop this local static server with Ctrl-C when finished. The timed walkthrough
above does not include this optional viewer step or claim a cold installation.

## Measurement and cleanup

For a timed, automated public-checkout reproduction, run
`python3 entrotter/scripts/reproduce_clean.py --bounded --output reproduction.json`
with the same socket configured. It creates another temporary workspace, builds
the image and compares the complete fixture. That temporary workspace/report is
removed afterward; only the requested evidence JSON remains. A running daemon
and potentially warm image caches must be disclosed alongside the timing.

The walkthrough itself starts no API server. Completed runs remove their worker
containers. Source checkouts, the venv, reports, worker image and Docker build
cache remain for reuse. Stop a dedicated VM when finished if it is not serving
other work. Never delete another project's containers, images or volumes.
