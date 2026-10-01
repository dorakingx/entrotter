# Verified implementation status

Updated 2026-09-20 JST. **Goal active; not submission-ready.** Implementation
and deployment checkpoints are recorded below. All six repositories exist publicly
under https://github.com/entrotter. Do not repeat archive bootstrap or overwrite
remote history. Use the existing six sibling Git checkouts and focused PRs.

## Verified progress

- Foundry v1.8.3 release archive downloaded and SHA-256 checked against GitHub
  release metadata. Local executable: `../.tools/foundry-v1.8.3/anvil` from this
  coordination repo. `evidence/foundry-install.json` records exact version/digest.
- Full workspace check: **150 Python tests and 13 JavaScript tests passed**,
  including actual Anvil transfer/revert/rejection, state isolation, startup
  timeout/cancellation, missing receipt cleanup, token storage and decimal pins.
  Fault-injection tests are labelled; no real EVM test was silently replaced.
- Engine PRs #6 and #7 merged after passing Python matrix and dedicated real EVM
  CI. Current engine: `6a3e03341eccd44fcd04a990db21cc5509e0c84d`.
- Exact ERC-20 token deltas and legacy Uniswap v3 ABI builder implemented.
  Scenario PR #4 merged. Website PR #7 merged; follow-up improves summary units.
- Actual Ethereum block 19,000,000, hash
  `0xcf384012b91b081230cdf17a3f7dd370d8e67056058af6b272b3d54aa2714fac`:
  baseline swaps 1 WETH into 2,556.134769 USDC. Candidate's excessive minimum
  output reverts, retains 1 WETH and consumes gas. Initial tracked balances and
  native funding are identical. No portfolio valuation or profit is asserted.
- Two historical runs produced identical complete artifacts, measured at 9.365
  and 8.621 seconds. `evidence/historical-verification.json` records CPU and peak
  child RSS with measurement scope. `historical-uniswap.json` contains receipts.
- Offline example reproduced from fresh public dependency checkouts and a new
  venv without pip/system packages in 5.335 seconds. Exact pins and scope are in
  `evidence/clean-reproduction.json`; the coordination checkout was already present.
- The historical example also reproduced from clean public checkouts in a fresh
  venv in 13.877 seconds, matching the public artifact exactly. See
  `evidence/clean-historical-reproduction.json`.
- Initial Pages deployment succeeded and live HTML matched the repository.
  Browser checks covered desktop/mobile, negative fixture, hash rejection,
  hostile Unicode/HTML-like input, no upload/third-party requests and skip link.
  Latest EVM viewer is also verified live: deployment run 35453228118, commit
  `ab121348b0ffbec5650f9eadf0a0b11f639d9780`. See `evidence/browser-verification.json`.
- Private vulnerability reporting enabled and independently read back on all six
  repositories. `evidence/repository-security.json` records results.
- Official Colosseum event/rules checked: deadline October 12, 2026 at 23:59 PT
  = October 13 at 06:59 UTC / 15:59 JST. `docs/COMPETITION.md` links sources.

## Reproduction commands

From the parent workspace (not this repository):

```bash
PATH="$PWD/.tools/foundry-v1.8.3:$PATH" python3 entrotter/scripts/verify.py --require-anvil
python3 entrotter/scripts/reproduce_clean.py
# Add --historical with the archive/Foundry environment below for a clean fork run.
SSL_CERT_FILE=/etc/ssl/cert.pem PATH="$PWD/.tools/foundry-v1.8.3:$PATH" PYTHONPATH=engine/src ENTROTTER_RPC_URL=https://eth.drpc.org python3 entrotter/scripts/check_historical.py
```

The TLS bundle override is for this macOS Python installation; do not disable
certificate validation. Public archive service availability can change. PublicNode
served the 2024 block header but rejected state reads as pruned. dRPC served the
required historical state. Archive failure is explicit, never a synthetic fallback.

## New agent slice: verified locally, awaiting independent review

- Engine PR #8 (`bb8b3e8d32c7cbd49629d337758f30bfdf805045`) adds typed
  execute/hold decisions over current observations, a bounded gas budget and exact
  recorded replay. Its Python matrix and dedicated real-Anvil CI passed.
- Scenarios PR #5 (`828cfe37f2a2d6d7f2db868a0856a28c080b7a94`) defines the
  optional result recording schema; its validation CI passed. Both PRs are open,
  not merged. Main still requires an independent approval.
- A real `gpt-5.6-sol` Codex CLI policy completed two decisions on an artificial
  local-EVM transfer/revert example. Non-agent execution reverted once (42,006 gas);
  both deterministic risk and model policies executed the transfer and held the
  revert (21,000 gas). The model took 8.721 seconds versus risk 0.313 seconds; no
  model advantage is demonstrated. Model alias, exact prompt, usage, limits and
  unavailable seed/monetary cost are recorded, not invented.
- Complete model artifact `1d1de88d01cbe23c494f6a6f7ee7127d63629baac071def58c067506ddf5893b`
  reproduced exactly without a model call. Fresh public dependency checkouts and
  a stdlib-only venv reproduced it in **5.148 seconds**, including clone/setup.
  See `evidence/clean-agent-reproduction.json` and `docs/AGENT_EVALUATION.md`.
- Trusted CLI subprocess timeout/output/error handling and cleanup pass offline
  tests. This is not a general code sandbox or an egress firewall. No arbitrary
  providers can be selected through JSON/HTTP. Current dependency pins identify
  tested proposed engine/schema commits, pending independent review.

## Frozen historical agent evaluation completed

- Three sourced Ethereum/Uniswap states plus two implementation holdouts were
  evaluated with identical proposals and starting states. Scenario freeze commit
  `1ce15d9` predates new protocol-state execution; 19M remains explicitly explored.
  Scenarios PR #6 (`5b718984ac67b8fb49e02f4dab676ae212d2aa58`) has passing CI.
- At 17M and 20M all policies executed successful swaps. At 18M, 19M and 21M,
  prescribed swaps reverted while both risk/model policies held. Model and risk
  observations, choices, final metrics and token balances agree in every case.
  The model was slower in all five; no model superiority or portfolio PnL claimed.
- All ten risk/model reports replayed exactly from recordings on fresh forks.
  All 15 report hashes, ten agent schemas, and receipt-derived gas arithmetic
  passed post-run inspection. Evidence: `evidence/causal-v1/`, with the initial
  missing-RPC failure retained. See `docs/HISTORICAL_AGENT_EVALUATION.md`.
- Engine/agent schema/model integration remain pending independent review in
  engine #8, scenarios #5/#6 and coordination #8/#9.
  Coordination #8 integration CI passed. The holdouts are now evaluated; do not
  reuse them as untouched cases for a tuned policy. All source/prompt pins remain.

## Direct Anvil comparison and diagnostic hardening

- The independent stdlib/JSON-RPC script and Entrotter executed the same frozen
  19M paired task three times each, in alternating order. All six outcomes match
  the source pin, every complete receipt, per-step native/token balances and gas.
  Observed median wall times: direct 8.653 seconds, Entrotter 8.689 seconds. This
  small network-dependent sample does not show a speed advantage. See
  `docs/DIRECT_ANVIL_COMPARISON.md` and `evidence/direct-anvil-comparison.json`.
- Entrotter additionally supplies reusable scenario validation, typed decision
  records/replay and a shareable report workflow. Contributor productivity and
  demand are not established by these measurements; genuine evaluations remain.
- Engine PR #9 (`ca9d5a7`) removes all provider error fields from user-facing RPC
  rejection diagnostics. Its regression tests failed before the patch and the
  isolated main-based checkout passed 83 tests with real Anvil afterward. See
  `evidence/engine-rpc-diagnostics-tests.log`. The primary engine checkout remains
  at the frozen benchmark commit; the fix awaits independent review and merge.
- Workspace tests pass 150 Python and 13 JavaScript tests without skips. The
  separate 83-test hardening run overlaps the suite and is not added to that total.

## Native lifecycle and optional bounded workers

- Engine PR #10 (`7f08a2b`) adds a lifetime-pipe guardian for owned Anvil nodes.
  Real owner SIGTERM/SIGKILL, guardian loss and watchdog checks passed in the
  88-test main-based suite; Python-matrix and real-EVM CI passed. Node lifetime
  is 150 seconds plus termination grace, not a native CPU/RSS sandbox.
- Engine PR #11 (`05448c3335440f19e619d1b71b449f4f0fb470d6`) adds explicit
  `run --isolated` / `serve --isolated` with a locally built immutable Docker
  image and verified Linux cgroup v2 controllers. Per-run limits: one CPU quota,
  512 MiB/no swap, 128 PIDs, read-only non-root rootfs, 64 MiB tmpfs and 16 MiB
  shared memory, 256 KiB input, 8 MiB output, and a 180-second worker timer.
- The main-based worker checkout passed 96 unit/native-Anvil tests. Actual Docker
  checks exercise kernel CPU throttling, OOM kills, fork exhaustion, full tmpfs,
  noexec, CLI/API report equality and signal/owner-loss cleanup. Dedicated local
  and Linux CI both passed all 10 tests, including an unattended 180.916-second
  local expiry. Linux run: 35458208203. See `evidence/worker-security.json`.
  No owned containers remained afterward; the dedicated VM is stopped and the
  existing Docker context/default profile is unchanged.
- The isolated historical 19M Uniswap run matched the complete existing public
  artifact exactly in 10.055 seconds. No archive URL or credentials are included
  in reports. Image inputs/source hashes are in `evidence/isolated-worker-image.json`.
- Native mode remains the default. Fork workers use bridge networking, not an
  archive-host egress firewall. Arbitrary agent code remains disabled. At that checkpoint, host report/image/VM storage,
  aggregate CLI concurrency and API connection threads still needed bounds.
  The newer host-budget slice below addresses API storage and connections. PRs #9/#10/#11 await independent review and are not merged.
  These test counts overlap previous engine suites; do not add them to the
  frozen workspace's 150 Python/13 JavaScript count.

## Host report storage and API connection bounds

- Engine PR #12 (`5e2663661cb26b17247ed34b2f31297095ba65e6`) bounds the
  dedicated API report directory to 128 MiB/128 files, individual reports to 8 MiB,
  and connections to eight handlers with a 240-second absolute socket deadline.
  Real file/process/socket tests cover capacity exhaustion, simultaneous writers,
  trickled headers, timeout recovery, wrong stored IDs and atomic write failure.
- Standalone CLI PR #5 (`d842c56bd9cf2c0845f5666b4ea0b02d2be34489`) enforces
  the same 8 MiB export limit and preserves prior destinations on failure without
  adding an engine dependency. Oversize/content-ID regressions failed before fixes.
- Engine 114 native/unit tests and CLI nine tests passed locally. Engine Python
  matrix, real-Anvil and actual-Docker CI, plus CLI Python matrix, all passed.
  A real CLI→SDK→API check verified fixture/Anvil reports, 507/503, no POST retry,
  saved/exported equality and recovery. `scripts/check_host_limits.py` makes it
  reproducible; its dedicated pinned CI job and existing workspace job both
  passed (run 35459506934). Linux and macOS artifact IDs agree. Frozen benchmark
  inputs are unchanged. See `evidence/host-resource-bounds.json`.
- These are application file-content limits, not whole-filesystem/VM quotas.
  Independent CLI export retention/concurrency, image/VM storage, native-default
  execution and complete CI hygiene remain open. Socket timeout does not forcibly
  cancel admitted native Python work. PRs remain unmerged pending independent review.

## Engine quality and Python dependency gates

- Engine PR #13 (`ba0adfb233b685f99f35cbbe33331fee83360504`) adds Ruff lint/
  formatting and mypy over all 17 production source/scripts, fixing 28 initial
  lint and 19 initial typing findings. JSON boundaries still need runtime validation.
- Full Bandit scanning retains 15 expected findings (13 low, two medium), with
  exact code/source hashes and per-finding reasons. No rules or advisory IDs are
  suppressed. Author-reviewed reasons still need independent approval; this is
  not a proof of security. Policy failure paths are tested.
- All 42 Python tool/build dependencies are version/hash locked; the strict audit
  reported no known vulnerabilities and no skipped packages. Runtime dependencies
  remain empty. All engine GitHub Actions now use immutable commit IDs.
- The local suite passed 121 tests with real Anvil. The full historical Uniswap
  artifact still matches exactly. An MIT-licensed wheel with no runtime dependencies
  built and reproduced the fixture from a fresh venv in isolated Python mode.
  See `docs/ENGINE_QUALITY.md` and `evidence/engine-quality.json` for exact scope.
- Linux quality checks passed. The first job omitted hidden generated report files
  from its upload; this was fixed with explicit hidden-file inclusion and an error
  on missing output. Final quality/native/Docker/matrix CI all passed; downloaded
  reports retain all 15 findings and the 42-package audit. The CI wheel's 14 Python
  files match the tested source. At that checkpoint, other repos, native/container-OS audits and
  docs-link gates remained open; subsequent slices are recorded below.

## Documentation links verified across all six repositories

- Checksum-pinned Lychee 0.24.2 checks each PR's tracked Markdown/HTML/CSS,
  including hidden templates, local files, fragments and public HTTP links.
  Six real-checker regression tests prove missing targets/fragments/CSS/HTTP 404
  failures, tracked-input coverage and rejection of an empty successful scan.
- All six local scans and all six GitHub link jobs passed: 102 successful link
  occurrences, one explicitly excluded local API example, no errors/timeouts.
  Downloaded CI reports match every local input hash; CI records its merge SHA.
  Complete results are in evidence/docs-links/summary.json and adjacent reports.
- README navigation now links workspace setup, contributing, security and license.
  Previously engine/SDK had zero extracted links and CLI only an excluded example.
  Consumer actions use immutable coordination commit ea74aec66c5234edb935e4b12c14ec686dc73f80.
  PRs: coordination #16, engine #14, SDK #5, CLI #6, scenarios #7, website #9.
  These are unmerged, pending independent review. Main required-check lists are
  unchanged. Static scanning does not complete the accessibility/dynamic UI gate.
- An existing host-bounds job failed at its CLI 503 assertion (run 35461539934).
  A local saturated-API probe reproduced five generic transport errors in 59 CLI
  attempts while all eight slots stayed occupied. It is not a link-check failure.
  The failure log/probe are retained; the subsequent fix and regression are
  recorded below. Frozen engine
  and historical scenario inputs remain unchanged.

## Saturated API response race: fix under review

- The earlier 503 failure is reproduced by a real socket that sends a POST body
  after the server has already emitted its response. Immediate close caused
  BrokenPipe; the new regression fails before the fix and passes afterward.
- Engine PR #15 adds bounded draining after half-closing the 503 output: at most
  320 KiB and 100 ms including send, without a new handler or admitted experiment.
  Idle/trickling rejected clients cannot extend the absolute grace. Slow or
  oversized senders can still see transport failure when the grace expires.
- All 124 native/unit tests passed locally. Ruff lint/format, mypy and full Bandit
  checks pass; all 15 finding fingerprints are unchanged. Only the reviewed API
  source hash changes. An existing deadline-abort test now correctly accepts FIN
  or reset while preserving timeout/recovery assertions; its failure is retained.
- The actual CLI→SDK→API check now requires 16 consecutive busy CLI responses and
  verifies no work, no replacement export, 507 handling, real Anvil reports and
  recovery. Local and Linux verification passed; full artifact IDs and checker hashes agree.
  The exact engine fix commit passed Python matrix, 124 native tests, all ten real
  Docker enforcement tests, quality and link jobs. Downloaded quality evidence
  retains 15 findings, audits 42 packages without known vulnerabilities, and the
  wheel's 14 Python files match source. Coordination integration/link CI passed.
  See evidence/overload-response/summary.json. PRs engine #15 and coordination #17
  remain unmerged pending review. This does not erase the original failed run or
  complete broader gates. Live Pages again returned 200 with exact source HTML.

## SDK and CLI quality gates

- SDK PR #6 and CLI PR #7 add Ruff lint/format, normal mypy, complete unsuppressed
  Bandit scans, strict advisory audits of all 42 locked tool/build packages, and
  fresh-wheel checks. SDK has no runtime dependencies. CLI builds its unpublished
  SDK dependency from exact source b0c2ba3bba411e548af44101ae06e879bd7b5dc0,
  verifies its dependency graph and never resolves it from a package registry.
- SDK 18 and CLI 13 local tests pass. The SDK now ships its verified `py.typed`
  marker. The CLI's optional engine stub describes only the v0.1 boundary; actual
  engine behavior is separately tested. Source scans cover four SDK/five CLI
  files, with zero findings/skips. Both 42-package audits report no known issues.
- A correctly hashed array/object mode previously raised TypeError. The SDK's
  failing regression is retained; it now emits ClientError, and CLI rejects the
  report without a traceback. All 16 existing archived-state/agent reports pass
  hash/parser checks. This does not constitute new historical/model execution.
- Fresh venv installs use only local wheels with `--no-index --no-deps`, confirm
  MIT metadata/source equality, and exercise SDK import and CLI doctor/verify/
  inspect without an engine package. Real CLI→SDK→API fixture/Anvil, quota and
  16-attempt overload/recovery checks pass locally. SDK and CLI quality/matrix/
  link CI passed. The newly pinned Linux cross-repository job also passed; exact
  source pins, checker hash and complete report IDs match local results. Downloaded
  SDK/CLI quality reports match every scanned source hash; both CI wheel contents
  and MIT/dependency metadata were checked. See docs/SDK_CLI_QUALITY.md and
  evidence/sdk-cli-quality/summary.json. Coordination PR #19 records the evidence;
  all three PRs remain unmerged and require independent review.

## Report viewer accessibility and browser CI

- Website PR #10 (`d7785e201a4de50b72623a1e7522762738abab54`) fixes skip-link
  focus, 339px page overflow at a 320px viewport, keyboard scrolling in report
  tables/JSON, accessible chart observation data and empty tables after errors.
  The earlier skip-link smoke check established scrolling, not focus transfer;
  this deeper regression records that distinction.
- The identical runner/Chromium 153 rejects the previous website (16 failed
  groups, two passed) and passes all 18 groups after changes on macOS and Linux.
  Fourteen axe scans per final run have zero violations. Incomplete contrast
  results remain explicit, with separate solid-CSS calculations; manual screen-
  reader certification and complete WCAG conformance are not claimed.
- Ten website Python and 13 JavaScript tests pass. Exact/integrity-locked browser
  development dependencies have no reported known npm advisories. They are excluded
  from deployment. Pages build depends on unit and browser jobs, and its actions
  are immutable. Linux run 35464241907 and links 35464241911 succeeded; downloaded
  source/runner hashes match local evidence. See docs/WEBSITE_ACCESSIBILITY.md and
  evidence/website-accessibility/summary.json for failures, screenshots and scope.
- Existing live HTML still matches main ab121348b0ffbec5650f9eadf0a0b11f639d9780
  with HTTP 200. Accessibility changes are unmerged and not deployed; independent
  review remains required. Owned browser/server and clean baseline worktree were
  removed. Frozen engine/scenario inputs are unchanged.

## Proposed bounded execution defaults

- Engine PR #16 (`dddba4a2c3efdd429e36520e8fc9d163888089e2`) routes public runner,
  CLI and API defaults through the existing bounded worker; missing configuration
  fails closed. Native execution requires an explicit developer opt-out. CLI PR
  #8 (`952bfb5aba14b674dd959035a5625fadbd2b07d1`) adds --local --native, rejects
  older unsupported engines and cannot override an API server's mode.
- Three default-path checks failed before the change and a FIFO input timed out.
  Inputs now require regular files and bounded reads. Afterward 129 unit/native
  engine tests, ten real Docker tests, 15 CLI tests and 20 coordination tests pass.
  Default runner/engine CLI/API and standalone CLI results agree; missing workers
  preserve exports. An independent idle worker expired after 181.405 seconds.
- Actual default CLI-SDK-API fixture/Anvil, 507, 16 busy responses and recovery
  pass. The default archived 19M run matches the complete prior artifact in
  10.097 seconds. A fresh public checkout, venv, image build and verified default
  fixture run took 11.682 seconds with an already-running daemon and warm caches.
  No cold-machine installation or new model/market-performance claim is made.
- Engine/CLI quality, matrix, native/Docker and link CI passed. Downloaded scans
  match source; engine retains 15 findings, CLI has none, and each 42-package audit
  reports no known vulnerabilities. Downloaded MIT wheels match source and pass
  a fresh installed default-run/failure-preservation check. Coordination
  PR #23's three integration jobs passed (35465814576), plus links 35465814613.
  Downloaded source/runner/artifact pins agree; Linux clean default reproduction
  took 7.444 seconds including Foundry download, with warm Docker build caches.
  The dedicated VM is stopped, no owned workers remain and Docker context is unchanged.
- See docs/BOUNDED_DEFAULT.md, bounded-worker-pins.json and
  evidence/bounded-default/summary.json. Both changes remain unmerged, the frozen
  engine/scenario checkouts are unchanged, and the separate agent branch is not
  incorporated. Aggregate CLI admission/retention and image/VM disk remain open.

## Proposed admission shared by independent CLI/API processes

- Engine PR #17 (`0718b20e47a2b69dcd6ac2ac7112f189131f9ec6`) reserves one
  worker container name per configured Docker daemon. Preflight rejection is API
  429; a simultaneous creation conflict can return 422 because Docker reserves
  names before they appear in queries. No automatic retry or native fallback is
  introduced. Cleanup filters a unique owner label and removes only the full ID.
- Both real CLI/API checks failed at parent dddba4a. The final source passes 135
  unit/native-Anvil tests and 15 actual Docker tests, including a synchronized
  two-process creation race, timeout/recovery and an unstarted occupied slot.
  The real idle worker expired after 181.203 seconds and subsequent runs worked.
  These suites overlap prior engine evidence; do not add them to frozen totals.
- Ruff/mypy, full Bandit review and docs links pass. Downloaded Linux quality
  reports retain all 15 findings, match the local full scan, and audit all 42
  Python packages without reported known vulnerabilities. All 14 Python files
  in the MIT wheel match source. Actual standalone CLI-SDK-API worker occupancy,
  one-POST 429 rejection, preserved exports/incumbent, 507/503 and recovery pass.
  All five engine Linux workflows, including 15 real Docker tests, passed at
  the exact source commit. Coordination PR #25 passed all three integration jobs
  (35467629251) and links (35467629252); downloaded pins, checker, image source
  and complete report IDs agree. Fresh public clone/venv/build reproduction took
  7.638 seconds on Linux with running Docker and warm build caches, not a cold
  machine install. No owned workers remain; the dedicated VM is stopped.
- See docs/DAEMON_WORKER_ADMISSION.md. Frozen benchmark checkouts remain unchanged.
  This limits cooperating default worker containers on one daemon, not caller
  processes, old/native clients, multiple daemons or image/export/VM storage.
  Containers abandoned before entrypoint start may require operator recovery;
  no daemon-failure guarantee or public multi-tenant safety is asserted.
  Independent review/merge remains required; the overall goal stays active.

## Worker image advisory and provenance gate verified; review pending

- The prior actual worker scan reported 151 Debian package findings and six pip
  findings; a signed distroless alternative still reported 130 findings. Full
  inventories are retained. The selected digest-pinned public Chainguard Python
  3.14 base and built worker inventory 26 packages, including Python/libc/TLS,
  with no known reported findings at the recorded database timestamp.
- Engine commit `a9741942d9a4a87de62f9b9b90fb6cbe7d092648` adds checksum-pinned
  Cosign/Trivy, exact signing identity/image/source checks, database freshness,
  mandatory core-package coverage and failure on every finding. All severities
  and unfixed issues remain enabled. Native Anvil inventory is still outside
  coverage; the checksum-verified binary's individual digest is recorded.
- Local 142 unit/native-Anvil and 16 real Docker tests pass. The initial CPU
  probe failed under Python 3.14's changed multiprocessing default; it now uses
  explicit fork and asserts child exit codes plus actual throttling. The first
  failure is retained. Ruff/mypy/full 20-finding Bandit policy and 42-package
  Python advisory checks pass. Actual standalone CLI-SDK-API integration passes,
  and two 19M fork runs match the complete existing artifact (9.528/9.150 seconds).
  All five engine Linux workflows pass, including 16 Docker checks and the
  complete image signature/advisory gate (35469285580). Downloaded inventories,
  source/auditor pins, signatures and report hashes are verified. Coordination
  proof b6bd48b passes all three integration jobs (35469413504) and links
  (35469413528). Public-source clone/venv/build reproduction took 20.672 seconds
  locally and 5.017 seconds on Linux, with running Docker and warm caches.
  Engine PR #18 and coordination PR #27 remain unmerged; independent review is
  required. No owned workers remain; the dedicated VM is stopped and the
  original Docker context/default profile are unchanged.
- See docs/WORKER_IMAGE_AUDIT.md and evidence/worker-image-audit/. This does not
  close native dependency, host caller/disk, independent review or submission
  gates. Frozen engine/scenario checkouts remain unchanged.

## Native release provenance and signed Cargo inventory: verified, review pending

- Engine PR #19 (`6410c37663d37685a30effccd87844e1740b8637`) adds a separate
  native release gate. Both Foundry 1.8.3 Linux archives have verified exact
  upstream workflow/issuer/source-commit attestations; their signed Anvil hashes
  match the real builder manifests. The complete downloaded SPDX inventory must
  equal its signed predicate. An intentional wrong certificate source pin fails.
- Actual arm64/amd64 scans cover every one of 1,126 signed Cargo identities and
  versions with no reported findings. All severities/unfixed issues remain
  enabled. The other 172 entries are listed explicitly outside Cargo coverage.
  This is an upstream whole-checkout SBOM, not an exact linked Anvil inventory;
  compiler/C-library/build-system completeness is not established.
- All 149 local unit/native tests pass, including seven negative policy tests.
  Ruff/mypy covers 19 source/scripts and full Bandit keeps 24 reviewed findings
  (20 low, four medium). Runtime Python source, Dockerfile and frozen historical
  inputs are unchanged. All five engine Linux workflows pass. Actual-worker run
  35470277261 passes 16 Docker tests and both full native/image advisory gates;
  downloaded signed inventory, binary/archive/source/auditor/report hashes match.
  Its 26 OS packages and 1,126 Cargo packages have no reported findings.
- Coordination proof 573b6c3 passes all three integration jobs (35470453881) and
  links (35470453897). Downloaded pins, checker, full artifact IDs and runtime
  image manifest agree with the prior verified execution. Public clone/venv/build
  reproduction takes 5.928 seconds on Linux with running Docker and warm caches.
  Engine PR #19 and coordination PR #29 remain unmerged. The dedicated/default
  VM profiles remain stopped; no local VM was started for this audit-only slice.
- See docs/NATIVE_RELEASE_AUDIT.md and evidence/native-release-audit/. Compressed
  raw evidence retains full signatures and inventories with original-byte hashes.
  Independent review/merge and the overall goal remain pending.

## Shared CLI export retention: implemented, review pending

- Engine PR #20 (`0d3857839b2187541e573bec2e58042ad5bf0b45`) and CLI PR #9
  (`a63a39000e03d151e80b5a9c47dd4df449281b93`) share an identical private
  export ledger. Matching clients sharing one state directory retain at most
  128 MiB/128 files including pending writes, across output folders and processes.
  The 8 MiB per-report cap and separate API artifact-store quota remain.
- Reservations are fsynced before output creation. Real competing processes and
  SIGKILL before/after atomic publication prove that pending bytes stay charged
  and completed output remains tracked. Inspection commands list charged paths;
  the operator decides which reports or abandoned temporary files to remove.
  Identical tracked output is idempotent at capacity; replacement needs peak room.
- Both previous writers admitted 129 files. Retained failing checks also exposed
  boolean ledger-version acceptance and an outdated rename fault-injection hook;
  both are fixed. Final local engine 164, CLI 30 and actual Docker 16 tests pass.
  Fifteen export tests per package exercise the real production ceilings and
  smaller fault budgets. Counts overlap earlier suites; do not sum them.
- All five engine and all three CLI Linux workflows pass. Downloaded complete
  scans match source and local findings: engine 24, CLI zero; both 42-package
  Python audits have no reported vulnerabilities. MIT wheel sources, shared
  helper and dependency metadata match. Actual arm64/amd64 images match the
  current source manifest; 26 OS packages and 1,126 signed Cargo identities
  have no reported findings at the recorded database time.
- Both actual CLIs agree on 128 shared slots, reject the next output, preserve
  old destinations and recover after manual deletion. Separate actual default
  Docker CLI-SDK-API fixture/Anvil/admission/507/503/no-retry checks pass. No new
  historical or model-performance claim is made. Coordination PR #31 passes all
  three integration jobs (35472379661) and links (35472379628) at 77a754e.
  Downloaded source/checker/helper/image pins and full report IDs agree. Public
  clone/venv/build reproduction takes 6.278 seconds on Linux with running Docker
  and warm build caches, not a cold installation. The initial workflow context
  rejection is retained and fixed. Frozen historical inputs remain unchanged.
  No owned workers remain; dedicated/default VM profiles are stopped and the
  original Docker context is unchanged.
- See docs/SHARED_EXPORT_BUDGET.md and evidence/export-budget/. This bounds
  cooperating file-content writers, not pre-existing untracked files, operator
  moves/renames, older clients, distinct roots, filesystem metadata, host caller
  processes, images or VM storage. Never reset the ledger to free quota.
  Both PRs remain unmerged and require independent review; the goal stays active.

## Coordination quality and optimized verification: verified, review pending

- Issue #32 adds lint/type/security/dependency gates over all 19 executable
  coordination Python sources and hidden production action helpers. Ruff lint
  covers all 19; formatting covers 18. The historical Codex provider remains
  byte-identical to its pre-execution freeze, enforced by an exact source hash.
- Mypy checks every tool against its actual pinned agent or worker engine variant.
  Three existing optional-pipe/selector diagnostics in the frozen provider are
  retained with exact messages, source/version pins and individual rationales.
  Other groups have no errors. No engine stubs or missing-import suppression is
  introduced; this is normal typing, not strict or runtime JSON validation.
- An actual optimized-Python regression shows mismatched wheel source could reach
  installation because asserts were disabled. The fix uses explicit exceptions
  for 83 predicates; AST comparison confirms predicates/lazy messages are retained.
  The installed-module path guard is explicit too. The regression and real
  optimized cross-CLI shared-export capacity/recovery checks now pass.
- All 26 local coordination tests and six actual Lychee regressions pass. Recorded
  model decisions replay exactly on real Anvil with the unchanged full artifact
  1d1de88d01cbe23c494f6a6f7ee7127d63629baac071def58c067506ddf5893b.
  No new archive/model call or model-performance claim is made. Full Bandit retains
  75 author-reviewed findings; 50 hash-locked Python packages have no reported
  known vulnerabilities. The schema-only lock is covered by that same audit.
- All coordination Actions are now pinned by commit. Existing three integration
  jobs remain, with an added optimized export check and a separate quality job.
  PR #33 passes all three integration jobs (35473712013), quality (35473711997)
  and links (35473711998) at proof f05eae7. Its frozen-dependency workspace job
  passes 156 Python and 13 JavaScript tests without skips, including six new
  coordination tests; do not add overlapping hardened-engine suites. Full scan/type/dependency
  reports match local source, locks and retained findings. Normal/optimized CLI
  checks agree, fixture/Anvil artifact IDs and image sources match prior evidence.
  Public clone/venv/build reproduction takes 6.748 seconds with running Docker and
  warm caches; no cold-installation claim. Initial YAML and Python-conditional
  dependency failures are retained and fixed without relaxing validation.
- See docs/COORDINATION_QUALITY.md and evidence/coordination-quality/. No local VM
  was started; both profiles remain stopped and no matching Anvil process remains.
  Frozen historical inputs remain unchanged. Independent review and overall goal
  completion remain pending.

## Scenario contracts and quality: verified, review pending

- Scenarios PR #8 (`3a78ecca24334ae87119a5a0b64c84ba6dd71de1`) fixes a
  reproduced result-schema reference failure using a fully local schema registry.
  Valid nested agent recordings now pass; invalid choices/extensions/reasons and
  exchange counts fail. Unknown relative, HTTP and file references fail without
  retrieval attempts. Missing schema dependencies fail instead of skipping tests.
- All three schema files and every scenario/benchmark/manifest remain byte-identical.
  The catalog test now includes historical scenarios and detects missing, unlisted
  or duplicate examples; all five frozen cases also receive schema validation.
  Fourteen tests pass locally against both agent and worker engine variants.
- Python 3.11/3.12/3.13 Linux jobs pass all 14 tests without skips. All 19 existing
  public result envelopes, including 12 agent records, pass offline validation.
  No historical/model execution or Docker VM was needed. The v0.1 envelope still
  does not fully constrain nested scenario/trace fields or verify hashes/semantics.
- Ruff, normal mypy and full unsuppressed Bandit cover all five Python sources,
  including tests; no type/security findings. Strict audits report no known issues
  or skipped packages across 48 locked tools and six schema dependencies (a subset).
  Immutable Actions, binary-only hashed installs and all 11 docs-link occurrences
  pass. Downloaded CI source/schema/lock hashes and complete inventories match local.
  Contracts run 35474622711, quality 35474622690, links 35474622683 all pass.
- See docs/SCENARIO_CONTRACTS.md and evidence/scenario-contracts/. PR #8 and its
  stacked prerequisites require independent review/merge. Website and separate
  agent-branch quality, broader resource/delivery and submission gates remain open.

## Website quality and decimal inputs: verified, review/deployment pending

- Website PR #11 (`61740312f281f7e911e0eb6e9482a3c372cb1fae`) fixes a
  reproduced display bug: correctly hashed blank/whitespace or non-decimal metrics
  could appear as ordinary numbers. Inputs now pass explicit scalar/object checks;
  invalid imports clear prior data and recover without uploads. The zero-build
  static runtime, public report/schema/mascot bytes and CSS are preserved.
- All eight JS files pass ESLint/Prettier and normal TypeScript checkJs with strict
  null checks (implicit-any remains allowed for tooling). All 14 JS security rules
  retain 32 source-bound author-reviewed findings. Negative policy tests and a real
  source-drift failure prove silent acceptance is rejected. Python tests also pass
  Ruff/mypy/full Bandit with no findings. No rule/advisory ID is suppressed.
- Local and Linux verification pass 21 JavaScript and ten Python tests, 19 real
  browser groups and 14 zero-violation axe scans. The identical runner fails the
  new malformed-metric browser case against the prior source while passing its
  other 18 groups. Incomplete contrast/manual-assistive-technology limits remain.
  An introduced source:null compatibility regression was caught and fixed; all
  19 archived EVM reports retain exact hash acceptance and old/new view models.
- Integrity locks cover 109 Node package entries including platform-optional tools;
  42 hash-locked Python packages are audited strictly without known findings/skips.
  No deployed package runtime is added. The first Linux lint scanned vendored JS
  in .venv; the failed log is retained and generated-environment scope is fixed.
  Final Pages checks (35476090427) and docs links (35476090431) pass. Downloaded
  source/config/lock hashes, all retained findings and Python identities match local.
- Quality now gates Pages builds alongside units/browser checks. PR build/deploy
  jobs intentionally skip; this is not a new deployment. See docs/WEBSITE_QUALITY.md
  and evidence/website-quality/. Independent approval/merge, live verification,
  separate agent-branch quality and remaining release/submission gates stay open.

## Bounded causal-agent integration: exact replay, review pending

- Engine PR #21 (`abb4662ce960e08b2aa3a2c8a1c10719339edccc`) integrates the
  frozen causal-agent implementation into the hardened worker. Risk decisions and
  JSON recorded replay share default quotas, daemon admission and owned cleanup;
  arbitrary trusted providers require explicit `run_agent_native`. There is no
  HTTP/CLI agent endpoint, provider loader, model call or native fallback.
- Internal request/response envelopes bind the complete selection, gas budget and
  recording. Public v0.1 contracts stay unchanged. Scenario/recording/full input/
  full output bounds are 256 KiB/3 MiB/4 MiB/8 MiB. Native custom callbacks still
  have no whole-process/egress sandbox; fork workers retain a general bridge.
- All 19 archived public EVM reports re-execute as exactly equal JSON artifacts
  in the final bounded image: 16 historical and three local runs, including
  12 recorded agent replays. Original engine/scenario checkouts, prompt/provider,
  benchmark and reports remain unchanged. No model generation or advantage claim.
- Native/unit coverage reaches 189 tests and real Docker coverage 21 tests,
  including frozen model replay, large recordings, gas/state divergence and
  cleanup/recovery. All 22 production sources pass Ruff/mypy/full Bandit with the
  existing 24 source-bound author findings retained, not suppressed. All 42 Python
  dependencies, 26 image OS packages and 1,126 signed-SBOM Cargo entries pass
  strict advisory checks with coverage limitations preserved. All 17 wheel
  modules match source. Linux checks all pass: units 35477273945, Anvil
  35477273947, Docker/supply-chain 35477273936, quality 35477273927 and links
  35477273922. Downloaded hashes/fingerprints/inventories match local. No owned
  containers remain and the dedicated VM is stopped. See
  docs/BOUNDED_AGENT_REPLAY.md and evidence/bounded-agent/.
- Protected review/merge and cross-repository pin integration remain open. The
  frozen coordination benchmark scripts deliberately still target their original
  experimental native API. No main change, package/image publication, deployment,
  outreach, new holdout evaluation or submission was performed.

## Submission videos and review package: recorded, owner review pending

- Actual continuous Chromium recordings now produce a **2:51.44 pitch** and
  **2:54.24 demo**, with local synthetic English narration and visible/separate
  captions. Both complete H.264/AAC files decode without errors; timing, streams,
  eight pitch layouts and representative final frames are checked. Human
  listening review and founder/team context remain pending.
- The demo inspects the earlier adverse Ethereum/Uniswap report, executes two
  real bounded local-EVM calls and imports the newly generated report. Frozen
  model replay equals the complete original artifact; zero new agent-model or
  archive calls occur. Invalid hash rejection clears prior data and recovers.
  All browser requests are same-origin loopback GETs, with no page errors.
- `submission/README.md` links the actual files, exact code/report sources,
  unvalidated market/pricing hypotheses, three-session evaluation protocol and
  prior-work/AI/media disclosure. No user sessions, customer quotes or revenue
  are invented. The original archive's dates/rights and owner facts need review.
- Public event/rules rechecked. Registration navigation reached an account-create
  page, so joined state remains unverified; no fields or agreements were submitted.
  No outreach or final entry was sent. See `evidence/submission-media/manifest.json`
  for hashes, precise executed helpers, audio/model provenance and scope limits.
  The recording console is explicitly a production aid, not a shipped feature.
- Coordination PR #40 passes all five checks at proof `75ab1b6`: integration
  35479125753, quality 35479125787 and docs links 35479125785. All eight public
  media/caption/probe files read back with exact hashes (15,411,176 bytes). Local
  docs checks passed all 149 occurrences. CI/publication records are retained.
- No product source changed. Review branches are still unmerged/undeployed. No
  containers remain; the owned preview processes are closed and both VM profiles
  are stopped. The incorrect unused export-state environment setting is disclosed;
  export used the ordinary shared ledger, which was not reset. Independent review
  of this material, human listening/fact checking and genuine demand remain open.

## Public bounded-agent checkout and cross-repository integration

- The bounded CI/type/dependency pins now select engine `abb4662`, plus the
  quality-checked scenario/viewer branches. Independent approval is
  still pending. Frozen benchmark dependency pins, provider source, historical
  reports and native compatibility jobs are unchanged.
- `scripts/reproduce_clean.py --bounded-agent` fetches five public dependencies,
  creates a new stdlib-only venv, builds the bounded worker, replays the original
  local model recording and runs standalone CLI verify/inspect through the SDK.
  Complete artifact equality passes in **20.403 seconds** locally. The companion
  bounded fixture passes in **18.588 seconds**. Docker/VM installation/startup are
  excluded and build caches may be warm; no cold-machine claim is made.
- The preserved `--agent` native path still exactly reproduces the same report
  in 4.420 seconds. No new model or archive call, policy tuning or public report
  replacement occurred. New `--output` keeps measurements separate from old files.
- Actual default CLI-SDK-API fixture/Anvil, admission, quota/preservation and
  overload/recovery checks pass on the new engine, as do ordinary/optimized
  cross-CLI export checks. Ruff/mypy passes; all 75 security findings remain
  source-bound and visible, all 50 locked Python packages have no reported
  findings, and six quality policy tests pass. New flag fails before the change;
  the stale source-security review also correctly rejects before refresh.
- PR #41 passes all five Linux checks at `5dba8e4`: integration 35479672160,
  quality 35479672206 and links 35479672162. Fresh public bounded replay takes
  6.673 seconds and fixture reproduction 6.962 seconds with running Docker/warm
  caches. Downloaded source/image inventories, complete artifact IDs, full security
  fingerprints, type reports and all dependency identities match local evidence.
  No workers remain; both local VM profiles are stopped.
- See docs/BOUNDED_AGENT_INTEGRATION.md and evidence/bounded-agent-integration/.
  No product/schema changes or new deployment. Independent review/integration,
  host caller/image/VM storage limits and human submission gates remain open.

## Required CI coverage enforced on all six main branches

- Required checks increased from 13 to 32 across the six repositories, adding
  quality, dependency/security, documentation, worker and browser jobs already
  observed passing at the exact commits in `required-checks.json`.
- GitHub protection was read back after the additive update and rechecked before
  this documentation change. Every check is bound to GitHub Actions app 15368.
  Strict freshness, one independent approval, admin enforcement and all unrelated
  protection settings are preserved. No branch was merged or deployed.
- Older partial PRs may lack the newly required workflows. Review and integrate
  the cumulative workflow changes before promotion; do not remove required checks
  to merge an older slice. Scenario matrix check names contain immutable engine
  pins and need a deliberate protection update when those names change.
- See [required checks](docs/REQUIRED_CHECKS.md) and
  `evidence/required-check-coverage/verification.json`. G3 remains partial because
  review/integration and the other recorded resource limits are still open.

## Worker setup archive bounds

- Engine [PR #22](https://github.com/entrotter/engine/pull/22), commit
  `2c843842dc57387150e3bb080c720bc94ce18bc5`, bounds archive staging to 256 MiB,
  hashes in at most 1 MiB chunks before extraction, and rejects FIFO/device inputs.
  A 300-second transfer budget is checked between reads with ten-second HTTP
  socket timeouts; it is not a hard deadline for DNS, filesystem I/O or builds.
- The oversized-input regression fails before the fix. All 196 local unit/native
  tests pass, including seven new regressions. Ruff/mypy and the complete
  24-finding security policy pass; stale source review correctly rejects first.
  All eight Linux engine checks pass, including real EVM and Docker enforcement;
  run 35480730300 exercises the updated network-download build path.
- A real build from the pinned 121,395,735-byte arm64 archive and an actual Docker
  fixture pass. Worker source digest remains `fba06f6dd633858f91dd89d4f48a51c8447696f32e9eb3820302d09bcb379f42`,
  and the complete report equals native execution. No runtime/schema change
  or new model/archive-RPC evaluation occurred. Both local VM profiles are stopped.
- Bounded reproduction, quality and integration pins now select this proposed
  engine commit. Frozen native/benchmark variants remain unchanged. The engine PR
  contains before/after logs, exact source hashes and image/smoke evidence under
  `evidence/worker-build-inputs/`; see `evidence/worker-build-inputs.json` here
  for integration checkpoints. Independent approval/merge is still pending.
- Caller-process limits, image/build-cache/VM storage and SIGKILL staging leftovers
  remain open. This setup fix does not complete G3 or authorize public hosting.

## Scoped first contributions available in all six repositories

- A GitHub audit found open `good first issue` tasks only in SDK and CLI. Four
  scoped documentation tasks now cover coordination #44, engine #23, scenarios #9
  and website #12, each with starting files, acceptance checks and evidence limits.
  Existing SDK #1 and CLI #1 are reused rather than duplicated.
- All six issue bodies, open states and labels were read back from GitHub.
  `evidence/first-contribution-paths.json` records URLs and body hashes;
  [first contributions](docs/FIRST_CONTRIBUTION.md) provides a visible entry point
  from README and CONTRIBUTING. No assignment or customer outreach was performed.
- This completes the missing issue-availability portion of G3. The tasks themselves
  are open contributor opportunities, not claimed implementation, accessibility
  evaluation, adoption or completed release gates. Independent review and the
  previously recorded resource/submission limitations remain open.

## Reference bounded API host service

- A systemd user service now applies one CPU quota, 256 MiB/no swap, 64 tasks,
  descriptor/core limits and a one-hour session limit to the API caller process.
  The startup checker reads actual kernel settings and refuses missing or excessive
  controls. This is a proposed operator-installed Linux mode, not a universal cap
  on arbitrary Python/CLI callers or a public service.
- The dedicated Colima 0.8.1 guest reports two CPUs, 2 GiB configured RAM/no swap
  and a 10 GiB writable disk containing home/tmp/Docker data. Host-share write
  attempts fail with EROFS. Disk exhaustion and the one-hour expiry are not claimed
  tested; a two-second scaled timeout is exercised instead.
- Actual VM CLI-SDK-API fixture and real-Anvil results exactly match stored reports
  and the earlier complete artifact IDs. CPU throttling, task admission EAGAIN,
  OOM-kill, timeout and refusal of an unbounded service start all pass. The API
  remains healthy after fault probes; no worker/probe units remain afterward.
  The service was then stopped, remains disabled at boot, and both local VM
  profiles are verified stopped.
- Two new policy tests, six existing policy tests, full type checking on 20 sources
  and the complete 75-finding security policy pass. Initial user-bus setup failures
  were resolved before the successful run, not silently skipped. See
  docs/BOUNDED_HOST_SERVICE.md and evidence/host-service/summary.json.
- This narrows the API-host/guest-storage gap for the measured operating profile.
  Ordinary host callers, hypervisor/log/cache overhead, whole-build deadlines,
  protected integration and human submission gates remain open.

## Candidate onboarding reproduced from the published commands

- README now links a complete pinned quick start instead of calling setup
  dependency-free and cloning moving main branches. The guide fetches coordination
  `98f11012934e92fadbbf0ae1ab8552c19d069ce7` and its five compatible public pins,
  prepares the worker, and retains a verified report for inspection.
- All four shell blocks were extracted verbatim and executed in a new temporary
  workspace. Six checkouts, a fresh venv without pip, the actual Foundry download,
  worker build, fixture and real local-Anvil checks passed in 25.57 seconds.
  The full fixture equals the pinned public sample. This used a running Docker
  daemon and warm base/build caches; installation/VM startup are excluded.
- `evidence/quick-start/` contains the commands, output, image manifest, both
  reports and hashes. No model or archive-RPC call was needed. Worker cleanup
  left no owned containers; the dedicated VM was stopped after verification.
- Candidate review/main integration remains pending. This repairs the onboarding
  path; it is not a package release, website deployment or new user evaluation.

## Open gates and next actions

1. The earlier EVM/viewer changes are merged and live; new agent PRs above are open. All
   six repositories now require passing CI and one PR approval, including admins.
   Current protection read-back is in evidence/required-check-coverage/. Future
   PRs need a reviewer distinct from the author; do not bypass these protections.
2. Complete security/delivery: whole-process CPU/RSS/time/disk/concurrency bounds,
   SIGTERM handling, deeper RPC/API fault tests, lint/types/security/dependency and
   remaining repo quality CI, immutable dependencies, and branch protections.
3. Obtain independent review of the agent and benchmark PRs. Further policy
   tuning needs new unused cases; these two holdouts are now evaluated. The original
   archived Uniswap report remains a manually prescribed intervention example.
4. The same-task direct Anvil comparison is now measured. Continue the remaining
   security/delivery gates next: host caller/storage budgets, review/integration of the
   proposed bounded default and shared daemon admission,
   and protected review/merge of the bounded-agent integration and its current
   dependency pins. Preserve the frozen engine checkout; use an isolated worktree.
   A dedicated local Colima profile now provides a verified Linux cgroup v2
   Docker daemon. The opt-in worker is tested in engine PR #11; native execution
   remains the main-branch default until PR #16 is reviewed and merged. See docs/WORKER_SECURITY.md and its measured evidence.
   Historical trace replay remains unsupported; do not imply a reconstructed market.
5. Obtain independent review of the accessibility PR, deploy through protected main,
   and verify the live site; manual assistive-technology evaluation remains open.
   Review the recorded pitch/demo and submission package. Three genuine target-user
   evaluations, joined-event verification, owner eligibility/facts and founder
   context remain pending. Outreach and submission require owner approval.

No arbitrary user code execution, public engine, paid service, package publication,
mainnet transaction, customer outreach or competition submission was performed.
The current per-EVM memory bound is not a complete process sandbox. Preserve these
limits in the product and release-gates.json. Overall completion remains unproven.


## Owner decisions and authenticated submission draft — September 20

The owner approved the existing demo/pitch, confirmed solo participation as
Doraking, eligibility and no funding, and deferred user evaluations as a current
submission gate. The owner reports that the initial code and mascot were newly
AI-generated for this event, with no Entrotter development before September 14.
Personal education/work details are withheld; do not invent them.

The authenticated Colosseum account now has project 14185 / Entrotter, with product
answers, source links, contact information and partial founder profile saved.
Final submission opens October 6 at 11:00 UTC / 20:00 JST. Draft editing is
confirmed; post-submission editing is not. Submission remains conditional and
has not occurred. The required school-status Yes/No answer remains blank.

The actual form limits pitch to two minutes and accepts only YouTube/Loom/Vimeo
video URLs. A new 106.0675-second pitch has been generated with synthetic narration,
confirmed founder context and explicit limitations; complete decode passes.
Existing demo and original recording evidence are unchanged. Logo upload was
rejected by the browser file-chooser transport, and supported video hosting is
pending. See evidence/submission-preparation/summary.json. Independent GitHub
review/main integration and newer Pages deployment also remain pending.

## October 1 — Current console and whole worker preparation budget

Website PR #11 now merges the current UFO/experiment-console main into the
accessibility and quality candidate. Its 8671ab2 head passes all four required
GitHub checks, with 40 JavaScript/11 Python tests and 24 browser groups/18
zero-violation axe scans locally. Five live site files match main d44af5d;
that publication is distinct from this unmerged candidate. Review remains pending.

Engine PR #22 at d5b3003 adds a 600-second cap across POSIX image preparation,
with a separate owned-session watchdog and an owner-lifetime pipe. Actual stalled
HTTP, a native blocking call, SIGTERM, ignoring descendants and owner SIGKILL are
tested. A real 60-second BuildKit RUN stops in 10.013 seconds with a ten-second
budget, with no guest probe process remaining. All 204 tests pass using pinned
Foundry 1.8.3, and the unchanged image produces the exact existing fixture.
Full source-bound security review retains 24 findings; Ruff/mypy pass. Historical
build-input evidence remains separate. See evidence/worker-build-deadline.json.

This coordination candidate promotes only the bounded worker/site pins and their
quality/integration checkout pins. Frozen agent/native benchmark revisions remain
unchanged. Current-head integration CI and independent reviews remain pending.
The dedicated Entrotter VM used for validation was stopped; the already-running
default VM was left running. SIGKILL can leave staging/config files; cache/image,
VM storage, arbitrary caller quotas and uninterruptible kernel faults remain limits.

The owner has broadened submission authorization: when quality conditions and
required facts are verified and the portal is open, submit without another blanket
approval and verify server-side acceptance and exact code/video versions. Do not
guess required school status or bypass review, authentication or terms. Supported
video-host links/logo and the school answer remain unfinished; the September 20
authenticated form's opening time still requires rechecking at submission.
Discord was abandoned by the owner and is excluded from work/submission gates.
