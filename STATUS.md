# Website status

## 2026-09-27 — Evergreen experiment console (review branch)

The existing website now presents the four-action Uniswap comparison at `/`,
with purple UFO artwork, orbital motion, a local command builder and a collapsible
v0.1 report explorer. Visible copy does not name a hackathon. The event subdirectory
has been removed from this source tree and the deployment allowlist.

The measured example and comparison validator were moved without changing their
bytes. Original wire-format names and pinned engine provenance remain intact.
No new execution, profitability result or live swap is claimed. Only this website
repository's code was changed; historical and unrelated PRs are preserved.

Validation performed on this change:

- Python site checks: 11 passed. The new root-integration regression initially
  failed before implementation, then passed.
- Node report checks: 29 passed across the original and comparison formats.
- Playwright Chromium at 1440×1000 and 390×844: four actions, recorded-result
  label, constraint decision, JSON download, command generation/input rejection,
  valid import, invalid import clearing results/download, legacy EVM and synthetic
  reports, no horizontal overflow, reduced motion and keyboard skip link passed.
- Local `/tokyo2026/` returns 404. Browser error/warning console is empty.
- Desktop, console and mobile screenshots were visually inspected; local images
  are in ignored `output/playwright/`. `git diff --check` passed.

The obsolete separate repository's Pages site was disabled through the GitHub API
under the owner's explicit removal authorization. Its Pages API and public
`https://entrotter.github.io/tokyo2026/` both returned 404 afterwards. The root
`https://entrotter.github.io/` still returned 200. This disables the temporary
publication; it does not delete the separate repository or its history.

The redesigned root is not yet live. PR #13 requires independent approval before
protected-main merge and Pages deployment. The local preview is not deployment
proof. No protection settings were changed and no unrelated PR was merged.

## 2026-10-01 — Integrating the current home into quality PR #11

The September entry above is historical: PR #13 is now merged. GitHub Pages
workflow 36259682938 succeeded for main d44af5d01f692e177af055338202695e5930c95f,
and the Pages API reports built. The quality candidate merges that main commit
while preserving the UFO home, console, measured example and collapsible archive.
The candidate itself still requires independent approval and later live checks.

The comparison importer now validates accessed object/scalar shapes from unknown
JSON, checks the displayed WETH/USDC pool and encoded fee, clears stale evidence
before loading and prevents a slower previous load from overwriting a newer one.
Opaque text surfaces preserve measurable contrast; the portal artwork retains
its glow. Keyboard chart alternatives, forced colors and scrollable regions
remain available in the archive. Both report wire formats remain compatible.

Fresh local validation on the combined working tree:

- 40 Node report/security-policy tests and 11 Python site tests passed.
- ESLint, Prettier, TypeScript checkJs, Ruff, mypy and full Bandit passed.
- All 14 security rules ran over 11 JavaScript sources; 12 type inputs were
  covered. All 51 findings retain individual source-bound author rationales.
  This is not independent approval or proof of security.
- Chromium 153.0.8010.12 and axe 4.13.0: 24 browser groups and 18 scans passed,
  with zero violations. Raw incomplete items and supplemental opaque-color
  calculations remain explicit. Console/import/race and all archive samples
  were checked at 1280, 390 and 320 CSS pixels. No uploads or third-party
  requests occurred. The 320px console screenshot was visually inspected.
- npm audit and the strict hash-locked Python dependency audit reported no
  known vulnerabilities. Lychee checked 31 links with zero errors/timeouts.

Local raw evidence remains in ignored output/playwright/ and .quality/; its
source hashes match the final runtime bytes. These are display checks using
existing evidence, not a new chain or model run. Manual assistive-technology
review and complete WCAG conformance remain unverified. PR builds do not deploy;
the independent main-branch approval and required jobs remain mandatory.

## 2026-10-01 — Inspectable recorded agent decisions

The candidate based on8671ab2 adds decision-time preflight/gas/execute-hold/reasons
beside candidate outcomes in the v0.1 archive. The existing local model report is
copied byte-identically; original requested alias, nondeterminism, unavailable
seed/cost and no measured model advantage remain disclosed. No model/archive
call, Docker startup, schema change or original recording rewrite occurred.

Independent source review found three P2 internal-consistency gaps: array choices
coerced to strings, proposals not tied to scenario actions and held outcomes
claiming success/nonzero gas. All are fixed and independently re-reviewed. Four
fully resealed contradictions fail before the fix and pass refusal afterwards.
All47 Node/11 Python tests, lint/format/types and full source scans pass. All55
static findings remain visible with reasons, retaining51 previous rationales and
reviewing4 new indexed-read/fixed-fixture filesystem findings; no rule is skipped.

Chromium153.0.8010.12/axe4.13.0 on Node22.23.1 pass28 groups and21 scans with zero
violations, including three viewports, hostile local imports, resealed failure/
clear/recovery, exact reasons/provenance and mobile keyboard horizontal scroll.
The320px screenshot was visually inspected and its table adjusted for readable
rows. All12 original agent reports still display with exact original hashes.
Raw incomplete axe items, source hashes and failures are preserved in
evidence/agent-decisions/. Initial unsupported Node20.2 and an EVM-test historical
source assumption were corrected before final verification.

Selected consistency checks do not authenticate imported data or reproduce full
engine/financial validation. Browser proof is not manual assistive-tech or full
WCAG certification. Current-head CI is separately required; independent GitHub
approval/protected integration/Pages live verification and submission remain open.

## October 2 — Separate signed-prefix report viewer candidate

Branch feat/trace-report-viewer builds from tested49914a2. New trace-report.mjs
and trace-viewer.mjs add a browser-only pane for the immutable engine817 actual
Docker four-prefix report, with exact source/parent/header, original signed
identities/nonces and original/baseline/candidate receipt comparisons. Existing
v0.1 app.js and original model/fixture reports remain byte-identical. The older
engine0d native one-prefix case is a separate test-only compatibility fixture.

Exact shape/integrity, RLP metadata, skip/index/receipt identity and type/target,
shared baseline-derived parent nonce anchors, cumulative gas, exact unique
receipt-difference sets and verification flags are checked before display.
Malformed resealed imports clear values/downloads and stale sample replies cannot
replace newer imports. Safe-integer numeric limits and unverified branches are
explicit; no authenticity, signature/Keccak, parent-state or EVM proof is claimed.

Author checks:63Node/11Python units, full lint/format/checkJs/Python checks pass.
All97 findings across14JS sources/15type inputs remain visible (all55 prior plus
42 individual explanations), no rule suppression;1Python source has zero full
Bandit findings. Node109/Python42 dependency audits report zero advisories.
Prior-source actual Chromium desktop/390/320px checks pass33groups and25axe scans, including
keyboard/import/reflow, exact receipt rows, inert hostile text, contradictory and
oversized imports, Python float/integer/Unicode imports, unverified recovery and
delayed-sample races. This browser proof precedes the final codepoint-length fix;
final exact-head CI will rerun the unchanged full browser harness. Imports emit
zero requests; only same-origin GETs occur. Manual assistive-tech/full WCAG remain
open. See evidence/trace-viewer for raw proof/source hashes and retained limits.

Independent root source followup resolves six compatibility/mutation findings with
zero remaining actionable findings within scope; public proof is retained. Mandatory
GitHub approval, exact-head CI and publication remain separate. No archive/model
call, new chain execution, local Docker/VM startup, deployment, protected merge,
media/holdout change or competition submission occurred. Discord is excluded.
