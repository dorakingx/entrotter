# Bounded default execution

[Engine PR #16](https://github.com/entrotter/engine/pull/16) and
[CLI PR #8](https://github.com/entrotter/cli/pull/8) change the proposed default from
native execution to the existing Docker worker. They are unmerged and require
independent review. [Issue #22](https://github.com/entrotter/entrotter/issues/22)
tracks this migration. Exact tested revisions are in
[bounded-worker-pins.json](../bounded-worker-pins.json); frozen benchmark pins
are unchanged. The separate agent branch is not incorporated into this change.

## Behavior

The public `runner.run`, engine CLI `run`, `serve`/`EngineServer` and standalone
CLI `run --local` use the configured bounded worker. This includes fixtures.
Missing Docker, an invalid immutable image ID, exceeded limits or an invalid
worker result fail execution; there is no native fallback. The input scenario
and complete report hash must match before the host accepts a result.

Existing per-experiment limits now apply to normal execution: one CPU quota,
512 MiB RAM/no swap, 128 process/thread slots, read-only non-root filesystem,
64 MiB no-exec tmpfs and 16 MiB shared memory, 256 KiB input, 8 MiB output, and
180-second independent worker lifetime. The host waits at most 190 seconds,
then performs bounded cleanup. Docker/VM failure is outside application lifecycle
guarantees. Fork networking remains a general bridge for archive reads, not an
archive-host egress firewall. Arbitrary external agent code stays disabled.

Native development is explicit: engine `--native`, standalone CLI `--local
--native`, Python `run_native`, or operator-owned `EngineServer(..., isolated=False)`.
It has no whole-process CPU/RSS sandbox. HTTP clients and scenario JSON cannot
choose native mode. The container calls run_native internally within its kernel
limits; it does not recursively start Docker. Older engines without the explicit
native primitive are rejected by the proposed standalone CLI instead of silently
using their previous default.

Local file reads now check the opened descriptor, reject non-regular files and
read only the admitted size plus one byte. A FIFO previously waited indefinitely
for a writer; the regression is retained. Existing export destinations survive
worker/input failures. JSON v0.1 and exact report contents are unchanged.

## Actual verification

[Complete evidence](../evidence/bounded-default/summary.json) retains failures,
full scans, source pins, image inputs, installed-wheel results and test logs.

- Three default-entrypoint regressions failed before the change; the FIFO case
  timed out after two seconds. All 129 unit/native tests pass after it, with real
  Anvil. Existing native tests explicitly select that path; they are not presented
  as Docker verification.
- All ten actual Docker checks pass. The default runner/engine CLI/API reproduce
  complete native fixture/Anvil artifacts. Kernel CPU throttling, OOM, PID/tmpfs
  exhaustion, noexec, privileges and lifetime cleanup are exercised. An idle
  detached worker expired after 181.405 seconds without host cooperation.
- The separate CLI passes 15 tests. Actual default local CLI runs match the API's
  fixture and EVM artifacts; missing worker configuration preserves prior exports.
  Explicit native fixture opt-in still reproduces the same artifact. Real SDK/API
  reads, 507 capacity errors, 16 busy CLI responses without retries/work and
  recovery also pass.
- The public default runner reproduces the complete existing 19M Uniswap artifact
  in 10.097 seconds. This uses archived state and supplied local-fork actions;
  it is not a new model evaluation, historical trace replay or profit measurement.
- Fresh public checkouts plus a venv without third-party Python runtime packages,
  worker image build, CLI execution and exact public-report comparison took
  11.682 seconds locally. Docker was already running; Foundry was predownloaded
  and image/build caches were warm. This is not a cold-machine Docker installation
  benchmark. The script includes build time and enforces a five-minute threshold.
- Ruff/mypy pass. The full engine Bandit report retains 15 unchanged findings;
  five changed source hashes were reviewed without suppressing rules. The CLI
  scan has no findings/skips. Both locked 42-package advisory audits report no
  known vulnerabilities. Independent security review is still required.
- All engine and CLI matrix/native/Docker/quality/link jobs passed at the recorded
  commits. Downloaded scans match the source. Downloaded MIT wheels contain the
  exact source files and expected dependencies. A fresh venv installed only those
  wheels with `--no-index --no-deps`; Python `-I` verified package location,
  default local execution and failed-worker export preservation.

The dedicated coordination `bounded-default` CI job builds the source-bound
image and runs the full CLI/SDK/API check and clean public reproduction. [Run 35465814576](https://github.com/entrotter/entrotter/actions/runs/35465814576)
passed all three integration jobs; [links](https://github.com/entrotter/entrotter/actions/runs/35465814613)
also passed. Downloaded pins, checker hash, full artifact IDs and image source
hashes match local evidence across arm64/amd64. Linux clean reproduction took
7.444 seconds, including a fresh Foundry download; the same job's Docker
image/build caches were warm. The dedicated local VM is stopped with no owned
workers left, and the existing Docker context/default profile are unchanged.
Existing frozen workspace and native host-budget jobs keep their source pins.

## Reproduce

Use the engine/SDK/CLI pins above and the tested coordination checkout. Follow
that engine README to build the local image and configure
`ENTROTTER_DOCKER_SOCKET` and `ENTROTTER_WORKER_IMAGE`. The Docker endpoint must be
a local Unix socket with Linux cgroup v2; no image is pulled from an Entrotter
registry. The builder uses pinned base/release inputs and publishes nothing.

```bash
# From a workspace with the proposed pinned checkouts:
PYTHONPATH=engine/src:sdk-python/src:cli/src \
  python3 entrotter/scripts/check_host_limits.py \
  --worker-manifest worker-image.json --output bounded-default-check.json
# Includes fresh public source checkouts, a fresh venv, image build and execution:
python3 entrotter/scripts/reproduce_clean.py --bounded
# Optional predownloaded release archive is still SHA-256 checked:
python3 entrotter/scripts/reproduce_clean.py --bounded --foundry-archive /path/to/release.tar.gz
```

`check_default_wheels.py --help` documents the source, wheel, reference report and
output arguments for the installed-CI-wheel check. It requires the same configured
worker and never resolves packages from a registry. Neither the API nor the CLI
accepts arbitrary worker image/socket settings from a scenario.

## Remaining scope

Independent CLI invocations still have no aggregate admission/retention quota;
image/VM disk policy is also open. Explicit native development, the separate
agent branch, native/container-OS audits, remaining repository quality gates,
independent merges and post-merge deployment verification remain outstanding.
This migration strengthens normal execution without declaring G3 or the overall
competition goal complete.
