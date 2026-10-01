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

The [latest candidate walkthrough](../evidence/latest-candidate/summary.json)
completed in 24.431 seconds: six clean public checkouts, a fresh pipless venv,
actual Foundry download/build/doctor, and complete fixture/local-Anvil equality.
Docker was running with potentially warm base/build caches; installation and VM
startup are excluded. The guide's four shell blocks were executed verbatim, with
the documented local socket, OS TLS bundle and a private temporary export ledger
supplied in the environment. This is not a cold-machine setup benchmark.

The earlier October 1 commands were [executed from a fresh workspace](../evidence/quick-start-oct01/summary.json)
in 24.35 seconds, including source fetches, venv creation, the Foundry download,
image build and both report checks. That measurement used coordination 03f8786
and engine d5b3003. The commands below now select coordination dcef3ee (including
the optional Linux CLI helper) and engine fa37380 (including the bounded build
diagnostic stream). The SDK, CLI, schema and console pins are unchanged. Docker was already running and image/build
caches were warm; installation and VM startup are excluded. The
[September 20 measurement](../evidence/quick-start/summary.json) uses earlier pins
and remains separate. Neither measurement is a cold-machine setup benchmark.

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
git -C entrotter fetch --quiet --depth=1 https://github.com/entrotter/entrotter.git dcef3ee06af060b17b52e0f3d59c060a9ab17fd6
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
