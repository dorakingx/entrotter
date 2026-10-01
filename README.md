# Entrotter documentation and report explorer

[Workspace setup](https://github.com/entrotter/entrotter#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

A zero-build static OSS website for GitHub Pages. HTML, CSS and plain JavaScript.
No framework, npm install, third-party script, tracking, wallet connection or
public backend is required. User-provided report files stay in the browser.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
# Open http://127.0.0.1:8000, not file:// (sample JSON uses fetch).
python3 -m unittest discover -s tests -v
# Node 20.19+; no npm install is required
npm test
```

The examples include synthetic offline fixtures and a real archived-state Uniswap
intervention. Neither establishes historical trading performance. The explorer verifies
SHA-256 hashes and renders synthetic fixtures and EVM reports. The pinned Uniswap example includes
source hashes, receipt statuses, gas and exact native/token units. The example
re-executes supplied actions against archived state; it is not historical replay.

The browser converts decimal strings to JavaScript numbers for visualization
only. The original exact strings remain in the JSON and the expandable observation table. Do not treat chart labels
as an exact financial ledger. No imported file is uploaded or saved remotely.

## Deployment

Repository name: `entrotter/entrotter.github.io` (public).
Intended address: https://entrotter.github.io/ . No custom domain or CNAME.
Configure Settings > Pages > Source as GitHub Actions, or use the parent
workspace's reviewed `scripts/publish.py --apply`. Push to main triggers
`.github/workflows/pages.yml`. A workflow file alone is not proof of a live site.

The deploy artifact contains only index.html, 404.html, style.css, app.js, comparison.mjs, report-validation.mjs, trace-report.mjs, trace-viewer.mjs, public
assets, schemas and public example reports. It never uploads the repository root,
private logs or a local .env. Pull requests run checks; only main deploys.

This site is for OSS documentation and public example inspection, not payment
processing or a commercial SaaS. The local engine is a separate executable.

## Assets and tests

The purple mascot derives from the owner's supplied Entrotter artwork; no
third-party brand assets or font files are bundled. UI fonts use system fallbacks.
A Content Security Policy limits script/network use to same origin.
All imported strings are inserted with textContent, never as HTML.

Run the parent workspace's `scripts/browser_check.py` for an optional Playwright
smoke test, hash verification, malformed import handling and screenshots.

## Browser accessibility checks

Serving the site and running the unit tests require no npm packages. The optional
browser development tools are exact-version locked in package-lock.json:

```bash
npm ci --ignore-scripts
npx --no-install playwright install chromium
npm audit
npm run test:accessibility
```

The standalone runner starts and closes its own loopback server and Chromium.
It checks all five public samples at 1280, 390 and 320 CSS pixels, skip-link
focus, keyboard sample selection/local-file import, exact chart data, scrollable
tables/JSON, error clearing, reduced motion, forced colors and the 404 page.
Hostile imported text remains inert; requests must be same-origin GETs.
The experiment console is also checked at all three widths, including local
command validation, malformed/oversized imports, recovery and a delayed sample
response racing a newer import. It uses its own unchanged UTF-8 wire format;
the older v0.1 reports continue to use their ASCII canonicalization.
Playwright and axe are development tools and are never deployed to Pages.

Full axe results, screenshots and a summary with source/tool hashes are written
to output/playwright/ (ignored by Git). All axe violations fail the job. Unknown
incomplete rules fail too; incomplete color-contrast results remain in the raw
report, with a separate strict calculation for opaque solid CSS colors. That
calculation is not an axe pass. Manual assistive-technology review and complete
WCAG conformance are not asserted. The 320px viewport check is not a hardware
zoom measurement. No real RPC or model execution is needed for this display test.

The Pages workflow runs these checks and a strict dependency advisory audit on
pull requests; the unit, browser and quality jobs must pass before main can build a
Pages artifact. Main still requires independent PR approval. To compare another
local checkout with exactly the same runner and browser, set SITE_DIR and a
separate A11Y_OUTPUT directory when invoking the script.


## Code quality and input validation

The runtime remains plain static files with no npm dependencies or build step.
Development tools require Node 20.19+ (CI uses Node 22). Exact tool versions and
integrity hashes are in package-lock.json; installation uses `--ignore-scripts`.

```bash
npm ci --ignore-scripts
npm run lint
npm run format:check
npm run typecheck
npm run security
npm test
npm audit
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements-quality.txt
.venv/bin/python -m ruff check tests
.venv/bin/python -m ruff format --check tests
.venv/bin/python -m mypy tests
.venv/bin/python -m bandit --ignore-nosec tests/*.py
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt
```

ESLint recommended rules and explicit no-eval/dynamic-code rules cover all tracked
JavaScript. TypeScript `checkJs` covers those same files and the actual axe-core
global declaration used by the browser runner. Strict null checks are enabled;
`noImplicitAny` is disabled for the JavaScript tooling. Production report inputs
use `unknown` with object/scalar checks; this is not a complete result-schema or
financial-semantics validator. Ruff, normal mypy and full Bandit also check the
Python website tests. CI discovers the tracked sources and refuses empty scans.

All 14 rules from eslint-plugin-security run without inline suppressions. Full
findings are saved in `.quality/security.json` before the source-bound review
policy is checked. `security-reviewed.json` retains 97 findings with individual
rationales (bounded numeric grammar, inert indexed reads and trusted developer
file operations). It pins every JS/declaration source and tool configuration/lock;
source drift, new/missing findings or missing rationale fail the gate. These are
author-reviewed explanations, not independent approval or proof of security.
The policy's negative tests run with the existing Node unit suite. Scanner
pattern coverage and advisory data have limits; no rule or advisory ID is hidden.

A correctly hashed report can still contain invalid display metrics. Blank,
whitespace and non-decimal forms such as `0x10` now fail instead of becoming zero
or another ordinary value. Display metrics accept finite JSON-style decimal or
exponent strings of at most 100 characters; raw token integers remain exact.
The browser test imports six such invalid files with newly computed valid hashes,
checks that all previous values/downloads clear, then reloads a valid sample.
Imports make no network request. Existing report/schema/mascot files are unchanged.

Quality, browser and unit jobs all gate Pages builds; PRs never deploy. After an
independent reviewer approves and merges the changes, verify the live deployment
separately before calling this implementation released.

## Recorded agent evidence

Open the v0.1 report explorer and select **Local EVM · recorded model decisions**.
The original [model report](https://github.com/entrotter/entrotter/blob/b724983a6c24fbe20473111565c8639714cb1bb0/evidence/agent-local-codex.json)
is copied byte-for-byte into `reports/agent-local-codex.json`; its artifact ID and
original requested model alias, prompt version, nondeterminism, unavailable seed
and generation cost remain unchanged. Loading it makes no model call. In this
local transfer/revert case the model chose the same actions as the preflight risk
rule and took longer; there is no measured model advantage.

The decision table joins each recorded observation step, current-state preflight,
requested/remaining gas, execute/hold choice and reason to its candidate outcome.
The viewer checks request digests, exact typed response keys/string choices,
ordered steps and prior-action history, scenario proposal equality, matching
trace decisions/actions, hold/rejection outcomes and success/revert receipt
status/gas/hash consistency. It hides and clears agent evidence after invalid
imports and when switching to a report without an agent. Imported text stays
inert; original raw JSON remains available.

These are selected internal consistency checks, not full engine validation,
authentication of an imported recording or proof of execution/model provenance.
A hash can be recomputed by an author. The original generation cost is distinct
from deterministic recorded replay. Browser regression tests also import
hash-resealed contradictions, hostile Unicode reasons and subsequent valid
recovery without uploads. Existing local/archived-state agent reports remain
compatible; this display work adds no new chain/model evaluation or schema.

## The experiment console

The home page combines the four-action Uniswap comparison and the existing v0.1
report explorer. There is no event-specific subpage. The purple UFO and orbital
visuals reuse existing project artwork. The interface identifies recorded results,
local imports and reproducible execution distinctly; the website never runs swaps.

`comparison.mjs` renders the console; `report-validation.mjs` checks its data.
The immutable measured example is in `assets/examples/action-comparison.json`.
Its original wire format and provenance are preserved for compatibility. The
original v0.1 reports remain in `reports/` and use the existing v0.1 `app.js` validator.
The reproduction link pins the existing runner commit while that code awaits review.

Run `npm test` for both report formats, and the Python tests above for the home
page contract and deployment allowlist. Browser verification covers desktop/mobile,
local imports, malformed input, command generation and the earlier report explorer.

Publication remains protected-main-only. An open PR is not a deployed result.

## Original signed-prefix replay viewer

Open **Inspect a historical prefix** and load the recorded four-transaction case,
or import a separate `trace_version: "0.1.0"` JSON file. The browser displays the
pinned source/parent/Shanghai header, original signed transaction identities and
nonces, original versus baseline/candidate gas and log counts, and exact receipt
fields/log bytes. Skipped, rejected, unmined and nonce-conflicting outcomes remain
visible; an unmatched baseline is explicitly **UNVERIFIED**. The existing v0.1
scenario/model explorer remains separate and unchanged.

`reports/trace-mainnet-prefix-four.json` preserves the exact actual default-worker
report from [engine817 / PR30](https://github.com/entrotter/engine/blob/8176597af994dddb7a3dc6721db623580ebc9601/evidence/trace-mine-deadline/README.md),
isolated CI run36878173559, artifact `cf1b51833babf17c1b39c5d37af0ff7945da43422e2efc3453d36e72b2d0810f`.
It matches all four original receipt projections and shows gas/log changes plus a
preserved nonce conflict after omission0. Its 14.539113s Docker runtime and the
46.982404s native run use different environments and are not a speed comparison.
The older engine0d one-transaction native report is a separate test-only fixture;
neither case is new model evaluation, profit, or an untouched holdout.

The browser checks the exact separate family shape, SHA-256, receipt identities,
original prefix/nonces, same-parent inferred nonce progression, cumulative gas,
plan skips, every receipt difference and declared verification flags. Canonical
RLP decoding binds raw type/nonce/destination, chain ID when encoded, and bounded
envelope fields. Supported unprotected legacy signatures (27/28) have no chain ID.
Object-key order does not matter; declared differences must be an exact unique
field set. Bundled trace schemas are byte-identical to scenarios8785 and serve as
wire-contract references; JavaScript additionally checks display relationships.

Imports are limited to 8 MiB, source inputs/individual receipts 256 KiB, prefixes 32,
logs 512/topics 4, raw wire envelopes 131071 bytes, and log/calldata 64 KiB. Text
limits count Unicode codepoints (assumptions 4000, Anvil version 1000). Numeric JSON
integer fields must fit the browser's safe-integer range; larger numeric JSON
integers are rejected rather than rounded. Hex uint256 quantities remain exact BigInt.
Imports never fetch, upload, select an RPC, or execute code. Imported strings use
textContent. Invalid files clear all trace values/downloads; stale sample loads
cannot replace a newer local import. Validation takes a synchronous deep snapshot
before hashing, isolating displayed rows from later caller mutations. Canonical
hashing preserves Python ASCII escaping and float runtime spelling; integral runtime
metadata also permits the exact Python integer encoding of that same number.

These are consistency/integrity checks, not authenticity, Ethereum Keccak hash
verification, recovered-sender/signature verification, parent-state nonce
attestation or EVM proof. A report author can recompute a checksum. Parent-state
pool admission can reject valid same-block funding; broader oracle/missing-state,
full-block/opcode/root/end-withdrawal and alternate-market coverage remain open.
Original in-prefix oracle updates remain; external responses are not invented.
This proposed browser view does not add a trace HTTP endpoint or run a transaction.
Protected review and live publication remain separate gates.
