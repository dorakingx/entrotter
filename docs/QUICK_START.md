# Reproduce a local report from pinned public sources

This guide uses tested candidate commits awaiting independent review and main
integration. It is not a released package or evidence that the newer website is
deployed. The fixture is a synthetic scenario, not historical market replay.

The proposed [standalone SDK price observation composition](../evidence/sdk-observed-integration/README.md)
selects engine40bea57, SDKeb9921f and viewera19d3b1. Its six offline integration cases pass
locally, including direct wrapper validation; combined current-head CI and human
main approval remain separate. The frozen Docker walkthrough below retains its
earlier2f6a56e/enginebd5527f source and measurements.

<a id="inspect-the-supported-historical-price-result-offline"></a>

## Inspect the historical price result locally

In an existing six-sibling checkout, select the reviewed viewer source:

```bash
git -C entrotter.github.io fetch --depth=1 origin a19d3b17fcf44e58a237b622de8cef89842eb6e7
git -C entrotter.github.io checkout --detach FETCH_HEAD
python3 -m http.server 8880 --bind 127.0.0.1 --directory entrotter.github.io
```

Open `http://127.0.0.1:8880/` and choose **Inspect recorded Aave price change** in the
transaction replay viewer. It validates the sealed wrapper and displays four
consumer/producer phases, exact USD prices, observed block and contract-code
identities alongside all32 receipts and the omission classification. You can
also import the original `observed-trace.json` from a supported CLI run directly.
Imports stay in the browser; the sample button fetches the local recorded file.
This inspection needs no Docker, Anvil, archive account or model call. It is a
local candidate preview; it does not confirm the latest source is deployed.

For Python inspection, select the standalone SDK in a second terminal:

```bash
git -C sdk-python fetch --depth=1 origin eb9921f30c1f0f3750140f66023e3b10d255cb20
git -C sdk-python checkout --detach FETCH_HEAD
PYTHONPATH=sdk-python/src python3 - <<'PYTHON'
from entrotter_sdk import load_observed_trace
observed = load_observed_trace("entrotter.github.io/reports/trace-observed-price32.json")
print(observed.classification)
print("Verified baseline receipts:", observed.trace.baseline_verified)
for row in observed.observations:
    print(row.branch, row.phase, row.price, row.base_unit)
PYTHON
```

Both SDK and viewer validate the wrapper's four price observations and preserve
the complete nested transaction report. The SDK exposes exact integer prices,
round/head/code records and finite errors; missing or unproven price deltas are
`None`. It needs no engine import or conversion. Its [component evidence](https://github.com/entrotter/sdk-python/tree/eb9921f30c1f0f3750140f66023e3b10d255cb20/evidence/observed-reader)
records45 tests on each supported Python version and a separate isolated wheel.

The source is an actual native32-of181/skip12 replay with four fixed Aave/WETH
phases. Read-only dependence is not signed consumer strategy, profit or
full-block/provider authenticity. If you need a separate trace-family JSON file,
use the engine's normal quota-bound `write_trace` export; the [engine's exact
export/replay command and original scope](https://github.com/entrotter/engine/tree/40bea57e25ab94c0d0f6136b4c3a5af4a99e6a1d/evidence/owned-consumer-observations/historical-32)
also documents pinned Anvil and read-only historical state access for a new replay.

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
coordination 2f6a56e, enginebd5527f, schemas8785bb0 and CLI22b514c; SDK and
signed-prefix reader/viewer pins are ee5523d/b1cfb00. Older timings do not measure
this new signed-prefix inspection composition.

The prior [inspection-fix composition](../evidence/agent-inspection-integration/summary.json)
selects the independently code-reviewed CLI fix: extra typed-response fields
cannot replace an observation's displayed step, and malformed responses are
refused before replay execution. All six CLI checks pass with 42 units per Python
version and four actual Docker cases retaining original report equality. Code
review is distinct from protected-main approval. Combined current-head CI and its
clean reproduction artifacts are recorded in the candidate PR: fixture6.308s and
model6.830s belong to coordination328f4c1/enginec167193/CLI22b514c.

The prior [contract identity composition](../evidence/contract-identity-integration/summary.json)
selects engine6e13f34. An independent source reviewer reproduced different Anvil
outcomes for canonically equal local contract maps differing only in key order.
Duplicate normalized contract addresses now refuse before native/default/agent
work; a single mixed-case address remains valid. All eight engine checks pass
with214 native tests and22 actual Docker enforcement/cleanup cases. The original
records remain unchanged. Current combined CI and clean reproduction results are
recorded in [candidate PR55](https://github.com/entrotter/entrotter/pull/55);
the older timings above do not measure this new composition. Independent GitHub
approval and protected integration remain pending.

The prior [parent-read cache composition](../evidence/trace-parent-cache-integration/README.md)
selects engine198139f/PR34. All8 exact component checks and independent full
source/wheel/image/security/receipt review pass. Exact-parent reads share bounded
cache entries; distinct keys progress independently and receipts stay uncached.
The same original32/skip12/150s native producer experiment now completes with all32
baseline receipts matching originals; prior failures remain preserved. It is
separate from the mandatory default Docker1/4-prefix cases. No dependent-consumer,
profit, full-block/root/provider-authenticity or speed claim follows.

The earlier404e8db/198 composition passed all5 combined checks and its independent
full artifact review; its clean fixture6.779s/model7.012s measurements retain that
source selection and running Docker/cgroup-v2/warm-cache scope.

The prior [receipt comparison composition](../evidence/trace-comparison-integration/README.md)
selects viewerb1cfb00/PR16. All4 component checks and independent complete Linux
artifact review pass. The display groups original receipt differences while
retaining every field, and identifies the loaded input count/omissions. All4 local
workflow reader steps pass, including the unchanged native00532-report inspection:
12 exact matches,1 omission,19 position/cumulative-gas-only differences and no
changed execution receipt fields. This is offline recorded evidence inspection,
not a fresh chain run or contract-state/consumer/profit conclusion. New combined
CI, protected-main human approval and live candidate Pages remain separate.


The previous bb9cada/engine198/viewerb1cf composition passed all5 combined checks
and full artifact review. Its fixture6.276s/model5.564s measurements retain the
running Docker/cgroup-v2 and potentially warm-cache scope above.

The current [Aave price observation composition](../evidence/consumer-price-integration/README.md)
selects enginebd5527f. All8 component checks and independent complete artifact
review pass;25 production source files remain byte-identical to198139f. The
recorded native006 case verifies original32 receipts and Aave/WETH read-only
price dependence from matching initial owned state. The baseline price changes
257082415000→256292441874 while omission keeps257082415000, in100000000 base units.
A fifth mandatory SDK/Node22 integration case checks every receipt, raw ABI word,
phase/head binding and returned code identity. All5 local reader steps and21-source
type checks with3 explicit frozen diagnostics pass. No fresh archive/model/browser
execution occurs in those reader steps. Standard trace-run does not collect extra
consumer views at this selected head; its public research package has the fixed
observation harness. New combined CI, protected-main human approval and current
candidate Pages remain separate. Read-only price dependence proves no signed
consumer action, strategy, profit, full-block/root or provider authenticity.

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
git -C entrotter fetch --quiet --depth=1 https://github.com/entrotter/entrotter.git 2f6a56e533935c93f4688c13feeeaa0e771c427a
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

## Optional original transaction-prefix replay

The [signed-prefix composition](../evidence/canonical-mine-integration/summary.json)
retains the historical engine#30 receipt evidence and separate schema#11.
The [funding composition](../evidence/trace-funding-integration/README.md) selects
engine#31 for the same-block admission fix; the current
[oracle/provider composition](../evidence/trace-oracle-integration/README.md) adds
signed causal oracle and missing-state coverage at engine#32. From `entrotter-candidate`, an operator
with an archive-capable `ENTROTTER_RPC_URL` can run
`python3 -m entrotter_engine trace-run engine/tests/data/canonical-mainnet-prefix-four.json -o transaction-replay.json`
using the configured bounded worker. It forks the original parent with canonical
header context, preserves original signatures/order/nonces, and records candidate
omissions/conflicts or receipt differences. Missing parent/account state can fail
explicitly; mining-time storage failures can instead leave transactions unmined
and the baseline unverified. Receipt absence alone cannot identify the cause or
attest provider state; no fixture state or oracle response is substituted.

The prior engine817 CI replay matched all four original Ethereum 19M receipt
projections in 14.539113s, including gas 208,144 / 234,720 / 175,305 / 178,980 and
8 / 10 / 6 / 8 ordered logs. Omitting transaction 0 changes gas/logs in 1 and 2,
and leaves transaction 3 at original nonce 5,523 versus expected 5,522. Complete
output matches the native 46.982404s result except runtime/hash. These different
environments are not a speed comparison. The [raw bounded report](../evidence/canonical-mine-integration/bounded-mainnet-prefix-four.json)
is a separate technical receipt case with no new model/holdout evaluation.
Both branches share a 150-second primitive budget; only owned mining gets its
remaining deadline, and ordinary reads resume afterward. This archive step is
outside the timed offline guide walkthrough.

The result uses the separate `trace_version` family. The selected SDK candidate
has an offline typed reader; the original v0.1 HTTP client remains separate.
Read the frozen actual report without archive access or a new execution:

```bash
python3 - <<'PY'
from entrotter_sdk import load_trace
report = load_trace("entrotter/evidence/canonical-mine-integration/bounded-mainnet-prefix-four.json")
print(report.artifact_id, report.baseline_verified)
for tx in report.transactions:
    print(tx.index, tx.candidate.status, tx.candidate.differing_fields)
    if tx.candidate.status == "nonce_conflict":
        print(tx.candidate.original_nonce, tx.candidate.expected_nonce)
PY
```

In the checked-out local site, open **Inspect a historical prefix**, expand
**Open signed-prefix replay** and select **Load recorded four-transaction case**.
The recorded file is byte-identical to the SDK and coordination fixture. A freshly
generated `transaction-replay.json` can instead be opened through **Open local
signed-prefix JSON**. Imports stay in the browser and make no network request.
The viewer shows original, baseline and candidate gas/logs, exact receipt fields,
omissions, differences and nonce conflicts; an unverified baseline remains explicit.

See [reader composition evidence](../evidence/trace-reader-integration/README.md)
for component checks and the separate combined-head CI/publication scope.
The SDK/browser check checksums and selected internal relationships; they do not
recover signatures, authenticate a provider or prove EVM/source/financial truth.
Browser numeric integer fields are limited to exact JavaScript safe integers;
hex quantities remain exact. At most32 original transactions in Ethereum's
Shanghai interval are supported. Owned trace nodes defer parent-state pool
balance/fee/gas admission to actual ordered EVM/block execution. Native synthetic
same-block funding and an adverse omission are verified; accepted transactions
can remain unmined and receive no receipt. No funding or nonce repair occurs.
The synthetic signed oracle case verifies that omitting an in-prefix update makes
the original consumer revert. Provider fault/control cases distinguish explicit
errors from unverified storage-failure reports. Archived same-block funding,
archived oracle cases, provider state authenticity and full-block/opcode/root/
end-state equivalence remain open. See the pinned engine README
for complete limits and upstream write denial. This inspection is outside all
previous timed guide walkthroughs; frozen model/holdout/media sources are unchanged.

## Optional synthetic oracle and provider-fault inspection

Read the frozen native regression reports offline from the selected engine.
They use a synthetic oracle, not historical prices or an external oracle service:

```bash
python3 - <<'PY'
from entrotter_sdk import load_trace
for name in ("native-oracle-prefix.json", "native-provider-control.json", "native-missing-storage.json"):
    report = load_trace("engine/evidence/trace-oracle-provider/" + name)
    print(name, "baseline verified:", report.baseline_verified)
    for tx in report.transactions:
        receipt = tx.candidate.receipt
        print(tx.index, tx.candidate.status,
              "receipt status:", receipt.status if receipt else None,
              "gas:", receipt.gas_used if receipt else None)
PY
```

The first two reports verify both original receipts. Omitting update0 preserves
consumer1's signature and produces an executed reverted receipt, status0 with
25808gas and no logs. `executed` means it was mined; inspect receipt status for
success or revert. The missing-storage report has an unverified baseline and no
receipts. Its known fault cause comes from separate regression controls, not the
report's missing receipts. Neither checksums nor receipt equality authenticate
provider state or external oracle truth.

Open these files with **Open local signed-prefix JSON** in the local viewer.
The [integration evidence](../evidence/trace-oracle-integration/README.md) records
offline SDK/codec checks separately from the existing rendered browser CI. This
optional inspection is outside all previous guide timing measurements.

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
