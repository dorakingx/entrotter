# Host report and API budgets

The proposed changes in [engine #12](https://github.com/entrotter/engine/pull/12)
and [CLI #5](https://github.com/entrotter/cli/pull/5) bound saved reports and local
API connections. They are tracked by [coordination #12](https://github.com/entrotter/entrotter/issues/12)
and require independent review before merge. They preserve v0.1 JSON and the
frozen agent benchmark engine checkout.

## Behavior and verification

| Boundary | Behavior | Evidence |
| --- | --- | --- |
| API report directory | 128 MiB of file contents, 128 regular singly linked files; zero-byte lock excluded | Actual default limits tested with existing files and a sparse quota-sized file |
| Individual report | At most 8 MiB for API reads/saves and both CLI export paths | Oversized read/export rejected; original destination preserved |
| Concurrent writers | Nonblocking POSIX file lock across cooperating processes | Two real OS processes competing for one available file slot produced one saved report |
| Atomic writes | Exclusive private temporary file, fsync, atomic rename | Injected replace failure preserved original and removed temporary file |
| Existing storage | Unrelated and crash-leftover files count; no automatic pruning | Quota tests retain those files and reject new writes |
| Artifact identity | Stored bytes must verify and match requested SHA-256 ID | Regression returned 200 before patch and 500 after; symlink/FIFO/oversized files rejected |
| Connection count | Eight handlers; excess connections return 503 without another handler | Eight real idle TCP connections saturated the server; closing one restored health access |
| Connection age | 10-second inactivity timeout, 240-second absolute socket deadline | Same production timer path tested at 0.2/0.25 seconds with idle and continuously trickled headers |
| Capacity responses | 507 for full report directory; 503 for connection/store contention | Real CLI/SDK/API checks observed status, no automatic POST retry and no overwritten export |

These are file-content/application quotas. They do not limit filesystem metadata,
noncooperating local programs, arbitrary export directories, image storage or VM
storage. The server requires a trusted dedicated local directory and POSIX locks.
Socket expiry shuts down the transport; already admitted native Python work
continues until its own execution budget ends. Native CPU/RSS limits remain an
open default-path decision. The optional worker's kernel limits are documented
separately in [WORKER_SECURITY.md](WORKER_SECURITY.md).

## Reproduce the full client path

Use the exact engine, SDK and CLI revisions in
`../evidence/host-limits-integration.json`. The engine is the proposed host-bounds
branch, not the frozen agent-evaluation branch. Install verified Foundry v1.8.3,
then from the workspace root:

```bash
PATH="<verified-foundry-directory>:$PATH" \
PYTHONPATH=engine/src:sdk-python/src:cli/src \
python3 entrotter/scripts/check_host_limits.py --output host-limits-check.json
```

The checker refuses dirty dependency checkouts and records their commit IDs and
its own source hash. It executes the real CLI subprocess, SDK transport and local
API for fixture and real Anvil success/revert scenarios. SDK reads, saved JSON and
CLI exports must contain equal complete reports. It then fills a deliberately
lowered two-file store, verifies idempotence and 507, and saturates eight actual
idle connections to verify SDK/CLI 503 and recovery. No archive, model, external
RPC or wallet is used. This is integration evidence, not a speed benchmark.

A separate `host-bounds` CI job checks out these proposed source revisions by
immutable commit. The existing frozen workspace integration job and historical
benchmark pins remain unchanged. Engine Python-matrix/native-Anvil/Docker jobs
and CLI Python-matrix jobs also run separately. Local counts are not added to
older overlapping workspace totals.

## Operator recovery

A 507 leaves saved reports intact. Export or delete unwanted files locally and
retry deliberately; POST is never retried automatically. A repeated identical
report needs no additional slot/bytes when the directory is within quota. A 503
means the connection cap or store lock was busy; wait for admitted work or close
unused clients. There is no remotely accessible report-deletion endpoint.

Remaining G3 work includes the native/default execution decision, aggregate CLI
concurrency/retention and image/VM storage policy, full lint/type/dependency/
security/docs-link CI, immutable action pins and independent reviews. Fork-worker
networking is not an egress firewall, and arbitrary external code stays disabled.
