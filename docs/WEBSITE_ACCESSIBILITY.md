# Report viewer accessibility evidence

Website [PR #10](https://github.com/entrotter/entrotter.github.io/pull/10), commit
`d7785e201a4de50b72623a1e7522762738abab54`, fixes keyboard focus and narrow-screen
report access. It is stacked on the documentation-link PR and remains unmerged.
The [tracking issue](https://github.com/entrotter/entrotter/issues/20) and
[complete evidence summary](../evidence/website-accessibility/summary.json)
distinguish proposed behavior from the deployed site.

## Observed problems and resulting behavior

The old skip link scrolled to main but left focus on the body. Main and linked
sections now accept programmatic fragment focus without adding extra Tab stops.
At 320 CSS pixels, navigation and the scenario selector previously expanded the
page to 339 pixels. They now fit the viewport, with readable stacked metrics.

The metric table, EVM action table and full JSON are named, focusable scroll
regions. Keyboard users can scroll them without dragging. Metric and observation
rows have explicit headers; the fixture chart includes a collapsed table of every
exact observation string, preserving decimal precision. The live status announces
a complete update once. Failed imports clear and hide invalid data; selecting a
valid example restores it. Forced colors preserve dashed/solid chart distinctions.

## Verification

The same standalone runner and Chromium `153.0.8010.12` tested the clean previous
checkout `692bb467bda71078f37bbeb1658f42f3f7212f7f` and the proposed site. Before:
16 check groups failed, two passed. After: all 18 passed on macOS (Node 20.2.0)
and Linux CI (Node 22.23.2). A group's first assertion stops that group, so these
counts are not independent accessibility violation counts.

Checks cover four samples at 1280, 390 and 320 CSS pixels; actual keyboard skip,
selection and native local-file chooser; exact observation values; horizontal and
vertical keyboard scrolling; hostile Unicode/HTML-like import without execution
or requests; tamper rejection/recovery; forced colors/reduced motion; 404 recovery;
and no JavaScript exceptions, uploads or third-party requests. Ten existing Python
and 13 JavaScript tests also passed. These overlap earlier workspace tests.

Playwright 1.63.0 and axe-core 4.13.0 are exact-version development dependencies,
with integrity-locked transitive playwright-core. They are not deployed. Local
and CI npm advisory audits report zero known vulnerabilities in these three
installed packages. This does not audit the browser binary or operating system.

Each final run contains 14 full axe scans with zero violations. Axe still marks
some clipped/decorative nodes as incomplete for color contrast. All raw results
are retained, with separate opaque-solid-CSS ratios (minimum 8.272882630259412:1,
required 4.5:1); unknown incomplete rules or unsupported visual effects fail.
This calculation is not an axe pass or complete contrast certification.
The initial desktop diagnostic used Chrome 152; it is identified separately from
the same-browser regression. Initial test-harness errors and the error-state
empty-table issue are retained in a log, not counted as final passes.

[Linux website CI](https://github.com/entrotter/entrotter.github.io/actions/runs/35464241907)
and the [link job](https://github.com/entrotter/entrotter.github.io/actions/runs/35464241911)
both succeeded. Downloaded CI evidence matches every local site/lockfile and
runner hash. Raw axe JSON is stored losslessly as gzip, with compressed and raw
hashes in the summary; selected local/Linux screenshots and complete summaries
are committed. Logs normalize trailing whitespace; coordination test logs also replace the local
workspace prefix with `/workspace`. All 20 coordination tests pass after supplying
the required sibling PYTHONPATH; the initial missing-import setup failure is retained. The original CI artifact
also includes all screenshots. Desktop and 320px screenshots were inspected;
platform system fonts differ. Automated checks do not replace manual
assistive-technology review or establish complete WCAG conformance. A 320px
viewport is not a hardware/browser zoom measurement.

## Reproduce and deploy

In the website checkout at the proposed commit:

```bash
npm ci --ignore-scripts
npx --no-install playwright install chromium
npm audit
npm run test:accessibility
```

The runner starts/closes its own loopback server and browser. Its output lives in
`output/playwright/`. To compare the old checkout, create a detached Git worktree
at the old commit and set `SITE_DIR` and a separate `A11Y_OUTPUT` when invoking the
same runner. An expected failure exits nonzero; do not suppress it in CI.

All Pages workflow actions are commit-pinned. Both unit and browser jobs must pass
before main can build its allowlisted Pages artifact. PR runs intentionally skip
build/deploy. Main still requires independent review; its existing required-check
configuration was not weakened or changed.

[Live publication read-back](../evidence/website-accessibility/live-publication.json)
returned HTTP 200 and exact HTML equality with main
`ab121348b0ffbec5650f9eadf0a0b11f639d9780`. The new accessibility changes are **not
yet deployed**. After review/merge, verify the actual Pages run and live browser
behavior before updating that claim. Overall competition readiness remains open.
