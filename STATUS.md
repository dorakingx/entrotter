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
