# Bounded API host service

The Docker worker's limits do not limit its caller. This reference deployment runs
the local API and its Docker client inside a systemd user service in a dedicated
Linux VM. It adds an enforceable host-process budget without changing the engine,
SDK, CLI or v0.1 report format. It remains a proposed, operator-installed local
configuration requiring independent review, not a hosted multi-tenant service.

| Boundary | Limit and proof |
| --- | --- |
| API process and its ordinary children | One CPU quota, 256 MiB, no swap, 64 tasks, 256 file descriptors, no core files |
| Service session | One hour maximum plus up to 15 seconds to stop; no automatic restart |
| Worker | Existing one CPU, 512 MiB, 128 tasks and 180-second independent timer; one worker per daemon |
| Measured dedicated guest | Two vCPUs, 2 GiB configured memory, no swap, one 10 GiB writable block device |
| Reports | Existing separate 128 MiB/128-file API and cooperating CLI export budgets |
| Host shares | Read-only; actual attempted writes failed with EROFS |

`ExecStartPre` runs [the checker](../scripts/check_host_envelope.py) before the API.
It reads the actual cgroup v2 CPU/memory/swap/task controls and process limits,
and rejects absent, unlimited, malformed or excessive settings. Unit options
alone are not accepted as proof. The checker also requires NoNewPrivileges.
The [service](../deploy/entrotter-engine.service) uses a loopback-only engine and
rate-limits journal messages; it has no boot enablement section.

## Dedicated VM prerequisites

The measured environment is Colima 0.8.1, Linux arm64, Python 3.12.3 and systemd
255. [The example profile](../deploy/colima-entrotter.yaml) preserves the ordinary
Docker context and provides an explicit read-only mount instead of sharing the
operator's home directory. Choose a fresh profile and replace its placeholder
with an existing empty directory. Do not overwrite an existing profile's data.
Use the directory's canonical absolute path: a symlink mount source can fail to
mount after a workspace move. Preserve compatibility symlinks for other tools,
but do not rely on them as Lima mount sources. Verify the actual mount and an
EROFS write rejection before treating the configured read-only share as enforced.

Colima's [versioned configuration implementation](https://github.com/abiosoft/colima/blob/v0.8.1/environment/vm/lima/yaml.go)
is the source for the tested mapping; newer versions can have separate root/data
disks. Inspect the generated Lima configuration, `lsblk -b`, `/proc/meminfo`,
`/proc/swaps` and `findmnt` before relying on a capacity claim. Verify that guest
home, `/tmp` and `/var/lib/docker` use the bounded guest disk and every host share
is read-only. The service checker verifies process limits, not VM configuration.

A working systemd user manager and session bus are required. The test VM initially
lacked the `dbus-user-session` package; installation of Ubuntu's signed package
`1.14.10-4ubuntu4.1` resolved the transient-unit test prerequisite. User-manager
socket recovery was also needed during setup. Those setup failures are not
counted as successful application runs. On a dedicated Ubuntu guest, install
`dbus-user-session` if needed and start its user `dbus.socket`. User lingering may
be required to keep the manually started service running after SSH exits.

## Install inside the guest

Use an inspected coordination checkout containing this PR's files in the guest or
on its read-only share. Record its commit and the source hashes. The commands below
create a fresh application directory; they do not replace an existing installation.
The engine commit is the tested proposed revision, still awaiting independent
approval. A local Docker daemon, Git and Python are prerequisites.

```bash
set -eu
coordination_checkout=/path/to/this/entrotter/checkout
app_dir="$HOME/.local/share/entrotter"
config_dir="$HOME/.config/entrotter"
test ! -e "$app_dir"
test ! -e "$config_dir"
test ! -e "$HOME/.config/systemd/user/entrotter-engine.service"
mkdir -p "$app_dir" "$config_dir" "$HOME/.config/systemd/user"
chmod 700 "$app_dir" "$config_dir"
git clone https://github.com/entrotter/engine.git "$app_dir/engine"
git -C "$app_dir/engine" checkout --detach d5b30035b4a2a1c292db24f6caf81ed419a2684e
export PYTHONPATH="$app_dir/engine/src"
export ENTROTTER_DOCKER_SOCKET=/var/run/docker.sock
python3 "$app_dir/engine/scripts/build_worker.py" --output "$app_dir/worker-image.json"
image_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$app_dir/worker-image.json")
printf 'PYTHONPATH=%s\nENTROTTER_DOCKER_SOCKET=/var/run/docker.sock\nENTROTTER_WORKER_IMAGE=%s\n' \
  "$app_dir/engine/src" "$image_id" > "$config_dir/engine.env"
chmod 600 "$config_dir/engine.env"
cp "$coordination_checkout/scripts/check_host_envelope.py" "$app_dir/check_host_envelope.py"
cp "$coordination_checkout/deploy/entrotter-engine.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user start entrotter-engine.service
systemctl --user show entrotter-engine.service -p ActiveState -p ControlGroup -p MemoryMax -p TasksMax -p RuntimeMaxUSec
```

The API remains on `127.0.0.1:8787`. Keep it local. Check the service journal if
startup fails; never delete `ExecStartPre` or loosen quotas to obtain a green run.
Stop with `systemctl --user stop entrotter-engine.service`, then stop the VM when
finished. An hour-long session ends even if the user has left it unattended.

## Reproduce the enforcement checks

[The explicit Linux test](../tests_host/check_service.py) is separate from unit
policy tests. In the guest application directory it expects `engine`, `sdk` and
`cli` source trees, the checker, `fixture.json` (liquidity-shock) and `local.json`
(engine's local test input). The measured SDK/CLI pins are respectively
`b0c2ba3bba411e548af44101ae06e879bd7b5dc0` and
`a63a39000e03d151e80b5a9c47dd4df449281b93`. Copy the test beside the checker, then:

```bash
python3 "$HOME/.local/share/entrotter/check_service.py" --output /tmp/host-proof.json
```

Use a dedicated test VM: the test intentionally exercises bounded allocation,
fork admission and timeouts in uniquely named transient units. It executes actual
CLI→SDK→API fixture/Anvil runs, checks full stored/exported equality and hashes,
then verifies CPU throttling, EAGAIN at the task ceiling, OOM-kill, a two-second
scaled timeout, and refusal to start a main executable with unlimited memory.
Transient units are stopped/reset afterward. This is not a simulated resource test.

The [October 1 current-candidate evidence](../evidence/host-service-oct01/summary.json)
re-runs the documented fresh installation at engine d5b3003, SDK b0c2ba3 and CLI
a63a390 after repairing the legacy symlink mount source. Both full reports match
the current quick start; all four real resource probes and the startup guard pass.
The two actual host-share writes fail with EROFS. The extra 48,384,000-byte
cloud-init ISO is kernel read-only; every writable tested path uses the single
10 GiB root disk. Earlier [September 20 evidence](../evidence/host-service/summary.json) includes kernel
controls, full test results, source hashes, VM topology and read-only write probes.
The fixture and local-EVM artifact IDs match the earlier integration records.
The one-hour production expiry was read back, not waited out; the timer fault test
uses two seconds. Live root-disk exhaustion was not attempted: disk evidence is
actual block-device size, writable mount topology and rejection of host-share
writes. The existing report-quota tests cover application-level exhaustion.

## Boundaries that remain

Only processes run in this service receive its cgroup budget. Direct macOS/Python
callers, developer native opt-outs and independently started CLI processes do not
inherit it. Guest CLI clients remain inside the VM's aggregate resource boundary.
Docker daemon/build work is outside the service cgroup but inside the measured VM;
the worker has its own limits. Operator-selected images and Docker socket access
remain trusted, not an arbitrary-code sandbox or an archive-host egress firewall.

The 10 GiB claim covers the guest writable block device. Host hypervisor overhead,
Colima diagnostic logs, cached base-image downloads, backups and manually exported
files are outside that disk claim. VM capacity does not impose a hard whole-build
deadline, and abrupt host death can leave charged staging files. A service kill can
leave a worker until its independent timer and removal complete. These limits,
independent review/merge, and other release gates remain explicit.
