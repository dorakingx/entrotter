# Bounded Linux CLI caller

The default Docker worker caps the worker, but an ordinary Python CLI caller has
no separate CPU/memory/session budget. This optional operator launcher runs the
installed trusted CLI in a Linux systemd user service. It is proposed deployment
tooling, awaiting independent review; it does not change the CLI package, native
benchmarks, source pins or v0.1 result format.

| Boundary | Enforced setting |
| --- | --- |
| CLI supervisor and its ordinary children | One CPU, 256 MiB, no swap, 64 tasks, 256 file descriptors, no core files, NoNewPrivileges |
| Lifetime | 180 seconds, with at most two additional seconds for systemd stop |
| Admission | One fixed `entrotter-cli-bounded.service` per user manager; a duplicate fails without stopping its incumbent |
| Owner death | Linux pidfd watches the original caller; SIGTERM/SIGKILL cancel its owned child session |
| Docker worker, reports and VM | Existing separate worker/export limits and the dedicated VM envelope |

The [launcher](../scripts/bounded_cli.py) checks actual kernel limits before CLI
execution using the [host checker](../scripts/check_host_envelope.py). Missing
Linux cgroup v2, pidfd or service prerequisites fail; there is no native fallback.
It starts only `/usr/bin/python3 -P -m entrotter_cli` with the three fixed installed
source directories on `PYTHONPATH`. Safe-path mode prevents a report folder from
supplying an `entrotter_cli` package. Arguments never pass through a shell;
systemd environment expansion is disabled so spaces, quotes, `$HOME` and `%h` in
user paths retain their literal meaning. The private environment file is read
by the user manager, with no credentials placed in command arguments.

The tested versions are Linux arm64, Python 3.12.3 and systemd 255 in the
[dedicated VM](BOUNDED_HOST_SERVICE.md). The exact
[systemd options](https://github.com/systemd/systemd/blob/v255/man/systemd-run.xml)
and [Python safe-path semantics](https://github.com/python/cpython/blob/v3.12.3/Doc/using/cmdline.rst)
are documented by their upstream projects. This is an installed trusted-code
operator tool, not an arbitrary-command or untrusted-agent sandbox.

## Install and run in the dedicated guest

First install the engine, worker image, host checker and private `engine.env` using
the [host-service guide](BOUNDED_HOST_SERVICE.md#install-inside-the-guest).
The API can remain stopped for `--local` execution. From an inspected coordination
checkout containing this candidate, add the SDK, CLI and launcher:

```bash
set -eu
coordination_checkout=/path/to/this/entrotter/checkout
app_dir="$HOME/.local/share/entrotter"
test -f "$app_dir/check_host_envelope.py"
test -f "$HOME/.config/entrotter/engine.env"
if test ! -e "$app_dir/sdk"; then
  git clone https://github.com/entrotter/sdk-python.git "$app_dir/sdk"
  git -C "$app_dir/sdk" checkout --detach b0c2ba3bba411e548af44101ae06e879bd7b5dc0
fi
if test ! -e "$app_dir/cli"; then
  git clone https://github.com/entrotter/cli.git "$app_dir/cli"
  git -C "$app_dir/cli" checkout --detach a63a39000e03d151e80b5a9c47dd4df449281b93
fi
test "$(git -C "$app_dir/sdk" rev-parse HEAD)" = b0c2ba3bba411e548af44101ae06e879bd7b5dc0
test "$(git -C "$app_dir/cli" rev-parse HEAD)" = a63a39000e03d151e80b5a9c47dd4df449281b93
test -z "$(git -C "$app_dir/sdk" status --porcelain)"
test -z "$(git -C "$app_dir/cli" status --porcelain)"
if test -e "$app_dir/bounded_cli.py"; then
  cmp "$coordination_checkout/scripts/bounded_cli.py" "$app_dir/bounded_cli.py"
else
  cp "$coordination_checkout/scripts/bounded_cli.py" "$app_dir/bounded_cli.py"
fi
python3 "$app_dir/bounded_cli.py" doctor
```

The block refuses a changed existing launcher/source checkout; review an update
before replacing it. No public-registry Entrotter package or API key is needed.
Use normal CLI arguments after the helper, retaining the caller's working folder:

```bash
python3 "$HOME/.local/share/entrotter/bounded_cli.py" run fixture.json --local -o report.json
```

`fixture.json` must be an actual scenario, such as the pinned liquidity-shock
fixture. For API use, start the bounded API service separately and pass
`--api http://127.0.0.1:8787` instead of `--local`. Stop an active CLI job with
`systemctl --user stop entrotter-cli-bounded.service`. Failed transient units are
collected, permitting a new job. There is no boot enablement or automatic restart.

## Measured evidence and limits

[The explicit dedicated-VM test](../tests_host/check_bounded_cli.py) exercises
real Linux admission, kernel readback, owner SIGTERM/SIGKILL, literal paths and
a complete 180-second production budget. Install it beside the helper with
`fixture.json` and the expected `bounded-fixture.json`, then run it with Python.
Its stalled/trickling local HTTP server is deliberate fault injection, not a
successful engine, archive or model run. The test verifies preserved destinations,
post-fault doctor recovery and no owned worker remaining.

[October 1 evidence](../evidence/bounded-cli/summary.json) binds the final source
hashes to that test: production expiry took 180.170 seconds, and both owner-death
cases stopped in under 0.12 seconds. Standalone fixture, real local Anvil and
CLI→SDK→API fixture reports equal their complete previously verified reports.
The CWD package-spoof regression failed before `-P` and passes after it. Four
controller tests, actual kernel checks and complete source quality checks have
distinct evidence; ordinary unit CI does not run the dedicated-VM fault test.

Only CLI jobs started by this helper receive its leaf cgroup. Its small dispatcher
is outside that leaf but inside the separately measured VM when run there.
Other users, direct native callers, operator source/image changes and other VMs
remain outside this claim. A cancelled API client does not cancel an independent
API-server job; that service and the worker retain their own budgets. Docker
daemon/build work is outside the CLI cgroup. A forced kill can leave a worker
until its independent timer/removal, or staging files charged to existing export
budgets. The helper does not bound host hypervisor overhead, caches, backups or
logs, prove arbitrary-code isolation, or supply a hard archive egress firewall.
Independent review/integration and the other release gates remain open.
