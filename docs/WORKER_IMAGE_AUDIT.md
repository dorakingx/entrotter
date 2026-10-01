# Worker image provenance and package advisory checks

[Tracking issue](https://github.com/entrotter/entrotter/issues/26).
The worker image now uses a digest-pinned public Chainguard Python 3.14 base.
The engine verifies its exact signing identity with checksum-pinned Cosign and
scans the actual locally built image ID using checksum-pinned Trivy. All detected
vulnerabilities fail the gate, including low, unknown and unfixed findings.
No advisory IDs, packages or severities are suppressed.

## Why the base changed

The prior Python 3.12 Debian worker's actual scan inventoried 87 OS packages and
an installed pip distribution. It reported 151 OS findings (65 unique IDs) and
six pip findings. The OS findings had no vendor fixed version in that database;
all six pip findings had upstream fixes. The compiled Python interpreter and
native Anvil binary were not inventoried by that scan. These counts describe
package findings, not demonstrated exploitability of Entrotter.

A signed Google distroless Python 3.13 base was also measured: 38 packages and
130 findings. Its smaller size did not satisfy the unchanged advisory policy.
The selected signed Wolfi base inventoried 26 packages, including its packaged
Python interpreter, libc and TLS libraries, with no known reported findings.
These are observed results at recorded database timestamps, not proof that the
image or application has no vulnerabilities.

The final worker has no installed shell, package-manager command or importable
pip module. An upstream pip bootstrap wheel remains an inventoried OS package.
Anvil is the same checksum-verified Foundry 1.8.3 release binary, whose individual
SHA-256 is now recorded in the build manifest. No registry account, paid image,
image publication or package publication was used.

## Fail-closed gate

Run the engine builder and then `scripts/check_image_security.py --manifest
worker-image.json --output .quality/image-security` with `PYTHONPATH=src` and the
same local Docker socket. The scanner uses private empty configuration and ignore
files, a minimal environment, all OS/language package types and every severity.
It checks the exact image/source identity, core runtime package coverage, scanner
version, database age (at most one day) and unexpired update window. Raw package
inventories, findings, base signature, tool/database/report hashes and logs are
retained even when findings cause failure. Tool acquisition or signature failures
stop the job; seven separately labelled policy-fixture tests exercise rejection.

## Runtime verification and limits

Python 3.14 changed the default Linux multiprocessing start method. The initial
CPU probe's child functions defined through `python -c` therefore failed to start;
its failing log is retained. The probe now explicitly selects fork and asserts
all child exit codes before asserting actual cgroup throttling. Production worker
code does not use multiprocessing. A new real image test checks the interpreter,
Anvil and absence of shell/package commands.

Evidence is under `evidence/worker-image-audit/`, including the prior and alternate
full scans, the final scan/signature, native/Docker logs and full archived-report
comparison. Local arm64 and Linux amd64 image IDs and native binary hashes are
platform-specific; source manifests and complete result artifacts must agree.
Counts overlap earlier suites and must not be added to frozen benchmark totals.

The scan does not cover native Anvil's Rust dependency graph when no embedded
inventory is detected, nor the host kernel, Docker daemon or VM. Native dependency
coverage, independent review/merge, host caller/export/image/VM disk budgets and
remaining submission gates stay open. The frozen agent/scenario checkouts remain
unchanged. This is experimental local software, not a hosted multi-tenant service.

Upstream references: [Chainguard signature verification](https://edu.chainguard.dev/chainguard/containers/security-and-compliance/verifying-chainguard-images-and-metadata-signatures-with-cosign/),
[Trivy native Rust inventory coverage](https://github.com/aquasecurity/trivy/blob/v0.74.0/docs/guide/coverage/language/rust.md).

## Verified checkpoint

[Engine PR #18](https://github.com/entrotter/engine/pull/18), commit
`a9741942d9a4a87de62f9b9b90fb6cbe7d092648`, passes 142 unit/native tests and
16 actual Docker tests. All five engine workflows pass; Linux image-audit run
35469285580 retained the actual amd64 inventory and exact base signature.
Downloaded raw report hashes and source/auditor pins agree with local evidence.
Both architectures inventory 26 packages without reported findings.

[Coordination PR #27](https://github.com/entrotter/entrotter/pull/27), proof commit
`b6bd48bb17cd950e5a12a7d766276291b33a35da`, passes all three integration jobs
(run 35469413504) and links (35469413528). Local CLI-SDK-API and Linux result IDs,
source manifest and checker hashes agree. Two actual bounded 19M fork runs match
the complete previous report in 9.528 and 9.150 seconds. Public dependency clone,
fresh venv, worker build and fixture verification took 20.672 seconds locally
and 5.017 seconds on Linux with running Docker and warm caches; VM installation
and startup are excluded. No new performance or market advantage is asserted.

The dedicated VM is stopped, no owned workers remain, and the original Docker
context/default profile are unchanged. Both PRs remain unmerged pending
independent approval. All broader limitations above remain release gates.
