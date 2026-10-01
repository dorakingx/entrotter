# Local worker security evidence

This slice adds native process guardians and an opt-in, bounded Docker execution
path. It is awaiting independent review in [engine #10](https://github.com/entrotter/engine/pull/10)
and [engine #11](https://github.com/entrotter/engine/pull/11), stacked on diagnostic
redaction [#9](https://github.com/entrotter/engine/pull/9). These changes are not on
main and do not complete G3. The frozen agent benchmark checkout is unchanged.

## Proven scope

Native Anvil children run under a lifetime-pipe guardian. Real tests terminate
the owner with SIGTERM/SIGKILL, kill the guardian, and exercise its watchdog.
The guardian has a 150-second node lifetime and up to two seconds of graceful
termination; it is not a CPU/RSS sandbox. The main-based guardian branch passed
88 tests; its real-EVM and Python-matrix CI passed. Simultaneous loss of owner
and guardian is outside that native mechanism's protection.

The optional `--isolated` CLI/API runs validated JSON through a local image
built from hash-verified Foundry v1.8.3 and a digest-pinned Python base. Docker
must report Linux cgroup v2 CPU, memory, swap and PID controllers before every
run. The host accepts only a verified report bound to the exact input scenario;
there is no native fallback on worker or runtime failure.

| Boundary | Configured limit / behavior | Actual verification |
| --- | --- | --- |
| CPU | One CPU quota | Three busy processes caused kernel throttling |
| RAM/swap | 512 MiB / zero swap | Kernel values read back; 64 MiB fault case allocating 128 MiB was OOM-killed |
| Processes/threads | 128 | Kernel value read back; lowered eight-slot fault case rejected fork with EAGAIN |
| Root/privileges | Read-only, UID 65534, no capabilities, no new privileges | Kernel/filesystem/process values checked |
| Temporary files | 64 MiB tmpfs, noexec; 16 MiB shared memory | Filling tmpfs failed with ENOSPC; direct script execution denied |
| Lifetime | Independent worker timer 180 s; host wait 190 s | Detached worker expires without host cooperation; SIGTERM and lost client cleanup tested |
| Input/output | 256 KiB / 8 MiB | Host boundary fault injection; exact fixture/local/historical report comparisons |
| Local networking | No external network in fixture/local mode | Fixed `--network=none` configuration; no host ports or bind mounts |
| Fork networking | Docker bridge, operator-owned archive URL | Real archived-state execution; no archive-host egress allowlist claimed |
| Persistence | Read-only root, no Docker logs, automatic container removal | Host verifies exact owned container absent after cleanup |

The original historical Ethereum 19M WETH/USDC report is byte-content-equivalent
as a parsed complete artifact in the isolated worker. Its SHA-256 artifact ID is
`6c358340e3b1227fccb4398802d30fefe27877aeacbacf8bd313c9c65c13a453`.
See `../evidence/isolated-worker-historical.json` for the measured time and
`../evidence/isolated-worker-image.json` for exact image/source/Foundry pins.
The historical run uses bridge networking and archive reads, never mainnet writes.

## Reproduction

Use engine commit recorded in `../evidence/worker-security.json`. Follow the
[engine worker instructions](https://github.com/entrotter/engine/blob/05448c3335440f19e619d1b71b449f4f0fb470d6/README.md#opt-in-isolated-local-worker)
from a clean checkout. A local Linux Docker daemon and verified native Foundry
are required for the dedicated tests; Docker absence fails them, not skips them.

```bash
export PYTHONPATH="$PWD/src"
export ENTROTTER_DOCKER_SOCKET=/var/run/docker.sock
python3 scripts/build_worker.py --output worker-image.json
export ENTROTTER_WORKER_IMAGE="$(python3 -c 'import json; print(json.load(open("worker-image.json"))["image_id"])')"
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests_isolated -v
python3 -m entrotter_engine run tests/data/local.json --isolated -o report.json
```

The build supports a digest-checked `--archive` local file. Image IDs depend on
architecture/build output, so use your generated manifest. No registry image
was published. Docker client commands use an empty temporary configuration;
registry credentials are not needed for the public base image.

For the macOS measurement a dedicated Colima profile used two CPUs, 2 GiB RAM
and a 10 GiB virtual disk. Its project-data share was a dedicated empty read-only
folder; Colima's managed cache was also mounted. The home directory was not
shared, and the user's existing Docker context/profile was not switched or
started. Public Docker pull initially stalled in the existing credential helper;
the task-owned client/helper were terminated and the fresh client configuration
succeeded. An initial local Python TLS failure was fixed with the trusted macOS
CA bundle, never by disabling certificate validation.

## Remaining gates

Native execution is still the default. The worker limits cover one experiment,
not the host's saved reports, image/VM disk, accepted HTTP connection threads,
or multiple independent CLI invocations. Python signal handling and Anvil
cleanup can add short termination grace; daemon/VM failure is not bounded by
the application's watchdog. Fork networking is not an egress firewall, and
trusted Docker administrators can inspect the archive URL. Arbitrary external
agent code remains disabled. Security/dependency audits, complete lint/types/
docs-link CI, independent approval and default-path decisions remain open.
