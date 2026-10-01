# Shared CLI export retention

Engine [PR #20](https://github.com/entrotter/engine/pull/20) and standalone CLI
[PR #9](https://github.com/entrotter/cli/pull/9) address
[issue #30](https://github.com/entrotter/entrotter/issues/30). Both older writers
could create 129 distinct reports despite the existing 8 MiB per-report cap.
The proposed writers now share a private, durable ledger across output folders
and processes. These changes are unmerged and require independent review.

## Scope and operation

Matching clients allow at most **128 MiB of logical file content and 128 tracked
files**, including pending temporary output. The 8 MiB individual report cap is
unchanged. Replacing an existing tracked report must fit both old and new content
during the atomic write. Re-exporting identical tracked content requires no extra
space. A full or busy ledger rejects the export and preserves the old destination.
The API's dedicated artifact store keeps its separate 128 MiB/128-file budget.

The default bookkeeping directory is `~/.local/state/entrotter/export-budget-v1`.
Trusted operators may set `ENTROTTER_EXPORT_STATE_DIR` to an absolute path; all
participating clients must use the same actual private directory. It requires
owner-only permissions. Both commands show charged paths and incomplete writes:

```bash
python3 -m entrotter_engine exports
python3 -m entrotter_cli exports
```

The output contains local paths; it is for the operator and is not uploaded.
Remove unwanted completed reports yourself. After checking that no export is in
progress, an operator can remove an abandoned temporary file listed by `exports`.
The next admission refreshes accounting. Never delete/reset the ledger to free
quota: that would discard tracking of retained files. The software does not
automatically delete completed reports or crash leftovers.

Both packages vendor exactly the same stdlib-only protocol implementation; the
standalone CLI still has no engine runtime dependency. An exclusive nonblocking
POSIX file lock serializes admission. The reservation is flushed and fsynced,
including the containing directory, before output bytes can be created. The
output is fsynced and renamed atomically. The durable pending record survives
publication; a later inspection/admission recognizes the exact content hash.
Ambiguous crash states remain charged. Bookkeeping has its own bounded size.

These are cooperating-writer accounting limits, not a whole-filesystem quota.
Pre-existing untracked files, manual moves/renames, old/nonparticipating clients,
different state directories, filesystem metadata, caller processes, Docker images
and VM storage are outside the bound. POSIX is required. Native opt-out does not
disable the export budget. A remote API run can finish before the local export is
rejected; do not blindly rerun a completed experiment. No automatic POST retry
has been added.

## Verification

`bounded-worker-pins.json` identifies the exact proposed engine/CLI revisions.
The frozen historical engine, scenarios and `dependency-pins.json` are unchanged.
See [evidence](../evidence/export-budget/summary.json) for source hashes, logs,
CI run IDs, downloaded report verification and remaining limits.

- Fifteen filesystem tests in each package cover the actual 128 MiB and 128-file
  ceilings, replacement peaks, manual deletion, alias/symlink handling, unsafe
  metadata, fsync/publication failure and real competing OS processes.
- Real SIGKILL immediately before/after rename proves pending bytes stay charged
  and published content remains tracked. The rename pause is fault injection;
  the processes, locks, filesystem writes and signal are real.
- `scripts/check_export_budget.py` drives both actual CLIs. One writer fills 127
  slots, the other writes the 128th in another folder, and the next export fails.
  Inspection agrees, identical full-budget output succeeds, deletion recovers
  capacity and rejection preserves a previous untracked destination. A mixed
  package process race admits exactly one six-byte output under a ten-byte test
  budget. This filesystem check uses explicit-native synthetic fixture execution.
- The separate default Docker CLI-SDK-API check verifies fixture and real Anvil
  reports, shared worker admission, 507/503 errors, no POST retry and recovery.
  Local engine 164, CLI 30 and actual Docker 16 tests pass. These counts overlap
  earlier suites and must not be added to the frozen workspace test total.
- All engine and CLI Linux workflows pass. Complete quality scans retain the
  existing 24 engine findings and zero CLI findings; author-reviewed findings
  still require independent approval. Both 42-package Python advisory audits and
  actual worker OS/native advisory gates pass at their recorded database time.

Coordination [PR #31](https://github.com/entrotter/entrotter/pull/31) passes all
three integration jobs and links at proof commit `77a754e`. Downloaded Linux
source/checker/helper/image pins and full fixture/Anvil report IDs match local
evidence. Public clone/venv/image-build reproduction takes 6.278 seconds with
running Docker and warm build caches; this excludes cold installation/VM startup.
The initial workflow context rejection and its fix are retained.

No new historical or model-performance claim follows from this storage change.
Independent review, host/VM resource limits, broader repository delivery gates,
accessibility deployment and genuine user/submission evidence remain open.
