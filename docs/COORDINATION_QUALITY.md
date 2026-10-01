# Coordination tooling quality

[Issue #32](https://github.com/entrotter/entrotter/issues/32) tracks lint, type,
security and dependency gates for all executable Python coordination tools and
the shared documentation action. Historical evidence, frozen engine/scenario
inputs and the exact pre-evaluation Codex adapter remain unchanged.

## Verification must survive optimized Python

The prior wheel verifier skipped source/dependency checks under `python -O` and
could reach installation with mismatched wheel source. A retained regression
uses an actual optimized Python process and an intentionally wrong local wheel;
subprocess installation is intercepted to avoid executing its contents. It fails
before the fix and passes afterward. Eighty-three `assert` statements are now
explicit conditional exceptions. Their predicates and lazy messages remain;
optimization cannot remove them. The embedded installed-package path check also
uses an explicit exception.

The shared export checker additionally passes under optimized Python with real
CLI subprocesses, filesystem admission/rejection, inspection and recovery. This
is a synthetic filesystem check, not a new historical or model measurement.

## Complete source scope, with the frozen adapter disclosed

`scripts/quality_scope.py` discovers production Python recursively under `scripts`
and `.github`, including hidden production action helpers. Unit tests and archived
evidence are separate inputs, not executable production tools. Current coverage
is 19 files. Ruff lint covers all production files. Formatting covers 18: the
Codex adapter's exact bytes are part of the historical benchmark freeze and are
enforced by a hash instead of changing its formatting.

Mypy checks unannotated function bodies against the real pinned source interfaces.
Agent tools use the frozen agent engine; worker tools use the proposed bounded
engine/CLI and SDK; general tools use the locked development environment. There
are no fabricated engine stubs or missing-import suppressions. Imported dependency
implementation diagnostics belong to their owning repositories; this is normal
mypy, not strict typing or runtime JSON validation.

**Three existing diagnostics remain visible in the frozen adapter:** the optional
stdout pipe at registration/close and the selector's integer-or-file-object type.
That adapter constructs stdout with `PIPE` and registers only its file object.
The exact source, mypy version, diagnostic strings and individual reasons are in
`quality-inputs.json`. Raw mypy exits 1 for that group; `check_types.py` accepts only
those exact reviewed findings. New, missing or changed diagnostics fail. Other
groups have zero errors. Independent approval of these reasons is still required.
Historical source is not silently changed to make a formatter or type checker green.

Full Bandit scanning uses all rules and ignores `nosec` comments. The current 75
findings remain in the report with exact source/finding hashes and per-call reasons
in `security-reviewed.json`. They concern developer subprocesses, trusted PATH and
the fixed public Pages content check. Author review is not independent security
approval or proof that the tools are safe for untrusted code. Unexpected findings,
source changes, scanner failures or skipped checks reject the gate.

## Dependencies and CI

Fifty Python tool/browser/schema packages are exactly pinned with distribution
hashes. Install with `--require-hashes --only-binary=:all:` from the official PyPI
index. `check_dependencies.py` verifies every declared dependency and installed
version, including the smaller schema-contract lock used by integration CI. The
strict advisory scan has no suppressions, skips or reported findings at the
recorded check time. Local engine/SDK/CLI imports come from exact source commits,
not similarly named public registry packages. Browser/Node/native binaries and
the host are outside this Python package audit.

All coordination workflow actions are now pinned to immutable commits. YAML
syntax is parsed separately; GitHub validates workflow schema/context semantics.
Inline workflow snippets are outside the Python source-file scan. Existing
frozen, host-bounds and default-worker integration jobs remain. The new job checks
source quality, dependencies and negative gate tests, retaining full reports.
The default-worker job also checks optimized export validation. The reusable docs
action retains its six real Lychee/HTTP/filesystem regressions.

From the coordination checkout, use a fresh venv and the exact dependencies in
`quality-inputs.json`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: --index-url https://pypi.org/simple -r requirements-quality.txt
.venv/bin/python -m ruff check scripts .github/actions/docs-links/check.py
.venv/bin/python -m ruff format --check scripts .github/actions/docs-links/check.py
.venv/bin/python scripts/check_types.py --agent-engine ../engine --worker-engine ../.worktrees/engine-security --sdk ../sdk-python --cli ../.worktrees/cli-bounded
.venv/bin/python scripts/check_security.py
.venv/bin/python scripts/check_dependencies.py
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt
```

The worktree names above describe this development workspace; supply your own
clean checkouts of the declared pins. Evidence and commands are recorded in
[the evidence summary](../evidence/coordination-quality/summary.json).
[PR #33](https://github.com/entrotter/entrotter/pull/33) passes quality, links and
all three integration jobs at `f05eae7`. Downloaded full reports agree with local
source hashes, dependency locks, retained diagnostics and complete report IDs.
Normal/optimized export outputs agree. Public clone/venv/build reproduction takes
6.748 seconds with running Docker and warm build caches; cold installation and
VM startup are excluded. Initial YAML and Python 3.12 conditional-dependency
failures are preserved with their fixes. The proposed change remains unmerged.
Scenario/website/agent-branch quality, host resource
limits, independent review, accessibility deployment and real submission/user
evidence remain separate open gates.
