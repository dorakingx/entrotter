# Website quality and numeric report input validation

Website PR [#11](https://github.com/entrotter/entrotter.github.io/pull/11), tracking
issue [#36](https://github.com/entrotter/entrotter/issues/36), closes a numeric display
coercion bug and adds complete source quality gates. A correctly hashed report
could contain an empty/whitespace metric and display it as zero, or use `0x10`
and display it as 16. Integrity alone does not establish valid report semantics.

Metrics now require finite JSON-style decimal/exponent strings, bounded to 100
characters. Raw integer formatting preserves exact units and rejects trailing
whitespace. Production report boundaries accept `unknown`, check objects and
scalars, and retain explicit DOM/error handling. The runtime remains plain
static JavaScript: no framework, package runtime, build step or upload service.
The HTML change is the script cache hash; CSS, schemas, public reports and the
owner's artwork remain byte-identical.

## Measured verification

The failing-before unit regression is retained. The final 21 JavaScript tests and
ten Python website tests pass. During compatibility review, the new object guard
was found to reject valid `source: null` on local-EVM reports. That development
regression is also retained and fixed: null/absent local sources are accepted,
while historical mode still requires its pin. The exact old/new production hash
and EVM view-model functions agree on all 19 existing public EVM reports. Their
full input hashes, artifact IDs and comparator are archived in the evidence folder.

The identical final Chromium runner was applied to the prior website and the
proposed source. The old site passes all previous 18 groups but fails the new
correctly-hashed invalid-metric import group. The fix passes all 19, including
six invalid numeric forms, clearing of stale values/downloads and recovery to a
valid sample without uploads. Both runs retain 14 full axe scans with zero
violations. Incomplete contrast results remain explicit in 13 scans and are
supplemented by the existing opaque-CSS calculation; this does not make those
items axe passes. Mobile/desktop screenshots are retained; the mobile viewport
was visually inspected. No chain, archive, model or Docker VM ran in this slice.

## Complete source and dependency gates

- ESLint recommended plus explicit dynamic-code restrictions and Prettier cover
  all eight tracked JavaScript files, including tooling, configs and tests.
- TypeScript 7 `checkJs` covers exactly those eight and the actual axe-core global
  declaration for DevTools injection. Strict null checks are enabled; implicit
  `any` is allowed in JS tooling. This is not a complete JSON schema validator.
- All 14 eslint-plugin-security rules run with inline suppression disabled.
  Thirty-two full findings remain visible, with individual author rationales and
  exact source/configuration/lock hashes. They concern bounded numeric grammar,
  inert indexed reads and trusted developer filesystem paths. Policy tests prove
  new/missing findings, changed bytes, empty scope, missing reasons, parser errors
  and suppressed findings fail. A real source-drift failure is also retained.
- Ruff lint/format, normal mypy and full Bandit cover the sole Python source, the
  website test module. No Bandit findings/errors remain. CI inventories tracked
  sources and rejects an empty Python scope.
- Exact Node versions and integrity hashes cover all 109 entries of the npm lock
  graph, including platform-optional compiler packages. This is not a claim that
  every optional package is installed or executed on each host. `npm audit`
  reports zero known vulnerabilities. All 42 hash-locked Python tool packages
  receive a strict audit with no known findings or skipped packages. The runtime
  website has no package dependency; these are developer/CI tools.

Generated dependency folders are excluded from first-party source scans and are
covered by their package audits. The first Linux run mistakenly linted Python's
vendored JavaScript inside `.venv`; its complete failed output is retained. The
fix excludes `.venv` consistently from lint/format/type/security discovery and
was verified locally with an actual in-repository Python environment. No source
file, security rule or advisory ID was suppressed to pass.

The Pages build now depends on unit, accessibility and quality jobs. All Actions
remain pinned to immutable commits. PRs do not build/deploy Pages, and protected
main still requires an independent approval. Full static findings and source,
configuration and lock digests are retained as CI artifacts.

Final Linux [Pages checks](https://github.com/entrotter/entrotter.github.io/actions/runs/35476090427)
and [documentation links](https://github.com/entrotter/entrotter.github.io/actions/runs/35476090431)
pass at `61740312f281f7e911e0eb6e9482a3c372cb1fae`. Downloaded complete source,
configuration/lock, retained-finding and Python identity inventories match local
verification. Linux repeats all 21 JS/ten Python tests and 19 browser groups with
14 zero-violation axe scans. Build/deploy are intentionally skipped on PRs.

## Reproduction and limits

Use the [website README](https://github.com/entrotter/entrotter.github.io/tree/ci/website-quality)
for exact `npm ci --ignore-scripts`, lint/format/type/security, unit, Python and
advisory commands. Run `npm run test:accessibility` with the installed Chromium.
`SITE_DIR` and `A11Y_OUTPUT` select a trusted local comparison checkout and output
folder; the checked runner starts/closes its own loopback server and browser.

`evidence/website-quality/summary.json` records source pins, counts, limitations
and hashes. Compressed axe JSON files preserve every original byte with separate
decompressed hashes. Source/security/package scan reports remain complete; local
path prefixes and trailing whitespace are normalized in text logs only.

The source-bound explanations are author-reviewed, not independent approval or
proof of safety. Package metadata audits do not scan native compiler/browser/host
internals. The viewer checks only the fields it needs, not complete financial or
causal validity. Chromium/axe evidence does not establish manual screen-reader or
full WCAG conformance. The proposed changes and prerequisite PR #10 still require
review, protected merge, deployment and live verification. Submission readiness
remains incomplete.
