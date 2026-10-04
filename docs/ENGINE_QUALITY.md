# Engine quality and Python dependency evidence

[Engine PR #13](https://github.com/entrotter/engine/pull/13), based on the proposed
host resource limits, adds executable quality gates rather than a checklist.
It remains unmerged pending independent review. The frozen agent benchmark
checkout and its recorded results are unchanged.

## Checked scope

- Ruff's configured lint rules and formatter cover all 17 production Python files
  under `src/` and `scripts/`. Initial inspection found 28 lint findings; formatting
  and one unused exception binding were fixed. Test files run separately.
- Mypy checks all 17 files, including unannotated function bodies. Initial
  inspection found 19 errors. Explicit types/guards now describe Decimal exponents,
  fixture trace rows, initialized Anvil/RPC/pipe state and extracted archive streams.
  Runtime JSON schema validation remains necessary; no fully typed JSON claim is made.
- Bandit runs every default rule with `--ignore-nosec`. Its complete JSON report
  retains 15 expected findings: 13 low and two medium. These concern trusted
  subprocess launches, a literal HTTPS release download and a container tmpfs
  specification. Each has a code fingerprint and concrete author-written rationale.
- The review policy binds the hash of every production file, scanner version and
  exact findings. Changed source, new/disappeared/changed findings, partial/failed
  scans, skipped checks and missing rationales fail. No rule or severity is hidden.
  The policy is not independent security approval; its rationales need PR review.
- All 42 Python tool/build packages are pinned and hash-locked. `pip-audit --strict`
  queried Python advisories with zero skipped packages and no reported known
  vulnerabilities at the recorded scan time. The runtime dependency list is empty;
  setuptools is pinned at 84.0.0. The manifest gate prevents declared runtime,
  optional-runtime or build requirements from silently escaping the audited lock.
- Engine GitHub Actions use verified commit IDs. Local installation used
  `--require-hashes --only-binary=:all:`; the Linux CI creates a fresh tool venv.

Hash verification and wheel-only installation follow the
[pip secure-install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/).
The [Bandit configuration reference](https://bandit.readthedocs.io/en/latest/config.html)
explains scanner rules and exclusions; this workflow runs the full default rule
set and keeps findings visible instead of adding exclusions.

## Behavior preserved

The local suite passed 121 tests with actual Anvil and no skips. Seven tests
specifically prove that the review/dependency policies reject changed findings,
empty/failed/partial scans, missing rationale and unpinned/uncovered dependencies.
A changed production file also caused the actual security gate to fail before
its reviewed hash was refreshed; the redacted failure log is retained.

A real Ethereum 19M Uniswap run matched the complete previously published artifact
`6c358340e3b1227fccb4398802d30fefe27877aeacbacf8bd313c9c65c13a453` after the source
changes. This remains supplied-action archived-state execution, not trace replay
or a repeated agent benchmark. Most diff lines are mechanical formatting.

The wheel built successfully with MIT metadata and no runtime dependencies. A
fresh venv installed that local wheel with `--no-index --no-deps`; isolated Python
mode loaded the installed package and reproduced the exact fixture artifact.
The wheel was not published. The initial smoke-check path assertion treated
macOS `/var` and `/private/var` aliases differently; filesystem normalization fixed
the checker, which then reran successfully in another fresh venv.

## Reproduce and inspect

Use the engine revision in `../evidence/engine-quality.json` and the commands in
its README quality section. `requirements-quality.in` contains direct tool pins;
`requirements-quality.txt` locks the complete graph. `security-reviewed.json`
contains exact findings, rationales and source hashes. Generated Bandit/advisory
reports and the built wheel are uploaded by the quality workflow.

The first Linux quality job passed but did not upload hidden `.quality/` files.
The follow-up sets `include-hidden-files: true` and fails missing uploads. Evidence
records the successful artifact download and inspected reports, not just job status.

## Remaining limits

This covers the engine branch, not every repository or the separate unmerged
agent branch. Other repositories still need corresponding quality gates, and
broken-doc-link checks remain open. Python package advisories do not cover Anvil,
the Python/OpenSSL runtime, container OS packages, the Docker daemon or malicious
code that a scanner fails to recognize. JSON typing is not strict end-to-end.
The native-default execution decision, aggregate CLI/image/VM budgets, independent
reviews, user evaluations and submission deliverables are still open. G3 and the
overall competition goal remain incomplete.
