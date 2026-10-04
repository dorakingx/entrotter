# Open and share a bundled report directly

Run the local site, then open
`http://127.0.0.1:8000/?report=aave-borrow-actions#report-explorer`.
The v0.1 explorer opens automatically with the selected original Aave recording.
After verification, **Link to this example** links to that bundled sample. This
makes a specific developer example reproducible from one URL instead of manual
navigation through the source selector. All six selector names are supported.

One exact, allowlisted `report` parameter is accepted with a2048-character query
bound. Unknown names, repeated parameters, paths, external URLs and local-state
markers use the normal default. Generated URLs preserve the current HTTP(S)
origin and path while dropping credentials, unrelated query values and fragments.
Local imports, loading and errors have neither a visible example link nor href.
An imported copy of a public report remains a Local report. Original file data,
source contracts and historical execution claims remain unchanged.

## Current local verification

Three regression groups fail against the old behavior and pass now: allowlisted
query parsing with malformed/ambiguous controls, sanitized same-origin URL
creation, and actual production startup selecting the requested example. The full
suite passes134 Node tests and12 Python site tests with zero failures/skips.
Lint, formatting, checkJs and the security gate pass;19 JS/20 typed inputs retain
149 full findings. [Finding review](reviewed-new-findings.json) preserves all147
unchanged reasons by full fingerprint and contiguous source spans, removes one
moved test-reader context and individually reviews two fixed public-file reads.
No findings are suppressed; author review is separate from independent approval.
[Local command records](local-checks.json) bind successful whole-output hashes.
Public command labels and paths are normalized to omit the private local
executable location; original output hashes are unchanged.

[Chromium evidence](browser.json) binds runtime/tool/runner hashes and49 passed
groups/62 raw axe scans with zero violations and JavaScript exceptions. New
coverage checks automatic direct entry, keyboard link navigation, exact16 Aave
rows, unrelated query removal, local import without a request, invalid imports,
loading, stale sample completion after a newer import, valid recovery, and invalid
query defaults. The stale-response case awaits the actual production loadSample
Promise through parsing/hash/generation completion; response headers alone were
insufficient and independent review required the stronger wait. Normal selector
and keyboard navigation remain exercised separately. Original checks across
1280/390/320 CSS pixels remain mandatory. Imports make no network requests; all
observed requests remain same-origin GETs. Raw axe incomplete contrast records
and supplemental opaque-color checks remain explicit. This is not manual
screen-reader certification or complete WCAG conformance.

The first full run retained a timeout in the existing320px native file chooser
check, with cause unknown. An unchanged runner retry passed; the final changed
runner passes after the independent-review wait fix. Earlier unit, lint, type,
cache-prefix and stale-manifest failures are retained privately where available;
no assertions, caps or timeouts were weakened. Raw screenshots/scans and full
stdout/stderr remain local; current CI exports its own fresh evidence.

[Offline view](view.json) is the actual production view-model output under the
current app hash. All original report bytes, sixteen rows, identities, source,
agent rows and scope equal the [earlier view](../aave-outcomes/view.json); only
the app hash changes. The earlier view and evidence remain historical. This
release does not execute new EVM/RPC/model actions, benchmark performance, render
videos, imply profit, or authenticate execution/providers. Independent staged/CI
review, protected human approval and live Pages deployment remain separate gates.
