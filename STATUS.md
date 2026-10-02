# Verified implementation status

Updated 2026-10-02 JST. **Goal active; not submission-ready.** Implementation
and deployment checkpoints are recorded below. All six repositories exist publicly
under https://github.com/entrotter. Do not repeat archive bootstrap or overwrite
remote history. Use the existing six sibling Git checkouts and focused PRs.

Latest prepared selection: engine65c/PR33 with coordination execution snapshot530ebc2;
component CI and offline readers pass, while new combined CI and protected-main
approval remain pending. The [latest evidence](evidence/rpc-diagnostics-integration/README.md)
separates the classified native archive timeout from successful synthetic checks.
The older milestones below retain their original sources and measurements.

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

## October 1 — Submission index and current quick start

The submission index now separates the latest tested candidates (coordination
03f8786, engine d5b3003, SDK b0c2ba3, CLI a63a390, scenarios 3a78ecc and site
8671ab2) from the September recordings. It reflects the owner's current submission
authorization and the actual uploaded logo, while preserving unanswered personal
facts and the missing video URLs. The portal again shows October 6 11:00 UTC as
the opening time. YouTube upload requires an action-time terms confirmation; none
of the approved files has been transmitted. See the authenticated draft checkpoint.

All four updated quick-start shell blocks were extracted verbatim and executed in
a new temporary workspace in 24.352 seconds. Six public checkouts, fresh venv,
actual Foundry download, worker build/doctor, full fixture equality and local Anvil
verification pass. Docker was running with warm caches; installation/VM startup
are excluded. Complete report IDs match existing evidence. All 18 worker image
inputs and the integration checker match downloaded current-head CI artifacts;
engine's eight and coordination's five checks pass at their above immutable heads.
See evidence/quick-start-oct01/summary.json. No new model/archive call was made.

The dedicated VM was stopped and the pre-existing default VM left running. Lima
warned that its legacy symlink source share was not mounted; this walkthrough needs
no guest source share and does not revalidate the historical host-service mount
topology. Candidate reviews/integration and final submission remain uncompleted.

## October 1 — Canonical VM share and latest bounded host service

The dedicated Colima profile still pointed to the workspace compatibility symlink.
Lima did not mount that source. Its location now resolves directly to the same
existing empty host directory; quotas, read-only permissions and network settings
are unchanged, and the compatibility symlink is preserved. Actual shares include
that directory and Colima's cache, both read-only with EROFS write rejection.

The updated host-service guide's install block was executed on fresh guest paths
at engine d5b3003. The inactive previous application/configuration/unit and reports
were retained as backups. SDK b0c2ba3 and CLI a63a390 were fetched by immutable SHA.
All three guest worktrees are clean. Real CLI/SDK/API fixture and Anvil results
match the complete current quick-start reports. Real CPU throttling, task ceiling,
OOM-kill, two-second timeout and rejection of unbounded memory before main pass.

The guest has two CPUs, 2,054,631,424 bytes of usable memory, no swap and one
10 GiB writable disk. An additional 48,384,000-byte cloud-init ISO is kernel
read-only and is explicitly retained in the topology proof. The first probe's
single-total-disk assumption was corrected after direct inspection, without
excluding a writable device. App, reports, Docker and /tmp use the root filesystem.
API service is stopped with PID 0, not enabled at boot; no worker/probe units remain.
The dedicated VM is stopped after validation; the default VM is left untouched.

See evidence/host-service-oct01/. This verifies the optional guest deployment,
not universal host limits, hard host cache/backup storage bounds, independent
review or goal completion. The original hour expiry and live root exhaustion
remain untested; the scaled timer and actual block topology are the stated proof.

The public event page, FAQ and official rules were rechecked on October 1.
Section 5 still specifies October 12, 2026 at 23:59 PT (October 13 06:59 UTC /
15:59 JST), with administrator schedule-change rights. The FAQ still permits
all-chain entries. COMPETITION.md and DISCLOSURE.md now reflect the owner's
new authorization and the verified logo; historical September evidence is retained.
See evidence/submission-preparation/oct01-rules-recheck.json.

## October 1 — Optional bounded Linux CLI caller

The new focused candidate adds an operator-installed launcher for the existing
trusted CLI. One fixed transient unit per user manager atomically admits one job
without disturbing an incumbent. Before CLI execution, the actual cgroup guard
checks one CPU, 256 MiB, no swap, 64 tasks, descriptor/core limits and
NoNewPrivileges. The unit has a 180-second production lifetime and two-second stop
budget; pidfd monitors the original caller, including SIGKILL. The small dispatcher
remains outside the leaf cgroup and inside the measured guest deployment.

The first private EnvironmentFile specifier was rejected by the transient-unit
API; it now uses a concrete quoted absolute path. A real regression then proved
that the working folder could supply a fake CLI Python package. Adding Python
safe-path mode fixed it without changing the installed component pins. The final
source passes literal path/quote/environment tests, complete fixture equality,
actual owner SIGTERM/SIGKILL cleanup in under 0.12 seconds and full production
expiry in 180.170 seconds, with destinations preserved and doctor recovery.
Standalone real local Anvil and CLI-SDK-API fixture results equal complete current
quick-start reports. No model or archive call was made.

Four controller tests, two host-guard tests, six quality-policy tests and all
21 production-source quality checks pass. The same three frozen-provider type
diagnostics and all 75 prior security findings remain; three source-bound
subprocess reasons are added. This is author review, not independent approval.
The two guide blocks pass on the existing clean installed pins, including full
fixture equality; cold clone/setup is not claimed. Actual user-systemd enforcement
is separate from ordinary unit CI. See evidence/bounded-cli/summary.json.

Both API/CLI units are inactive with PID 0 and no owned worker remains. Colima
readback confirms the dedicated VM is stopped and the pre-existing default VM
is still running, left untouched. Direct native callers, other users/VMs, arbitrary
code, Docker daemon/build work and host hypervisor/cache/log/backup overhead remain
outside the helper's leaf budget. An API job may continue after its client dies
under the separate API/worker limits. Independent review, protected integration
and the remaining G1-G5 gates are still open; Discord remains excluded.

## October 1 — Worker build diagnostic budget candidate

Engine PR #26 at fa37380 is a focused branch on PR #22/d5b3003. Build diagnostics
previously inherited stdout/stderr without an output quota. They now merge into
a pipe, read at most 64 KiB per chunk and forward at most 1 MiB plus a 68-byte
notice to stderr. Further output is drained without accumulating it; nonzero
command status and the existing independent deadline/owned-session cleanup remain.
Successful stdout contains only the final JSON manifest summary. Runtime source
and image inputs are unchanged; no coordination dependency pin is promoted here.

A real noisy-command regression fails before the fix and retains exit 7 after it.
An endless producer stops under a shortened 0.4-second independent budget with
no active process group. All 206 local native/unit tests (17 builder tests) pass
with pinned Foundry 1.8.3; all 22 production files pass Ruff/mypy and the full
source-bound scan retains 24 findings. Actual dedicated Linux arm64 BuildKit
executes four RUN steps requesting 16 MiB and forwards exactly 1,048,644 stderr
bytes, no stdout and one notice. The checked-in Docker regression independently
passes and is now included in mandatory isolated CI. Full normal fixture equality
and unchanged image-input hashes pass after the normal build.

The first Dockerfile used an image ID as FROM and failed reference resolution.
A single-step probe then produced only 414,062 bytes, so it did not exercise the
helper quota; four steps do. These setup failures are distinct from final proof.
The probe image was removed only after its unique label/full ID matched, with no
worker left. Dedicated VM stop/default VM preservation are verified. Normal worker
image/cache stays local; no registry publication, model call or archive-RPC call.
See https://github.com/entrotter/engine/blob/fa3738078079ffa8f8350a26dca60b560d8aa32f/evidence/worker-build-output/summary.json.

Current-head CI and independent review are recorded in PR #26. Other Docker JSON
captures, daemon/BuildKit storage, image/cache/host overhead quotas and abrupt-death
staging/configuration leftovers remain open. The coordination STATUS/gate additions
were held as local checkpoints and are included in the following candidate-pin
preparation, without a separate status-only PR or CI run. All overall gates remain partial.

## October 1 — Latest tested candidate composition

This candidate builds on coordination PR #53/6a30402 and selects engine PR
#26/fa37380 in the bounded-source manifest, current integration job and actual
type dependency. Engine's eight and coordination's five existing checks pass;
the updated dependency combination still needs its own current-head checks.
Type checking against the clean fa37380 checkout passes with only the same three
frozen-provider diagnostics. Engine runtime modules and Dockerfile are unchanged
from d5b3003; SDK/CLI/schema/site pins and frozen model/benchmark inputs are retained.

This is proposed candidate composition, not protected main integration or approval.
The optional CLI helper and bounded builder can now be reviewed together using
immutable source snapshots. Fresh public reproduction and this candidate's CI
are recorded separately from the earlier October 1 measurements. Historical
service/topology proof remains the actual d5b3003 installation. GitHub's current
collaborator readback shows only the author; an independent reviewer identity is
requested, and no permission, review or branch-protection bypass is performed.

All four updated quick-start blocks then ran verbatim from a fresh temporary
workspace in 24.431 seconds, selecting coordination dcef3ee and engine fa37380.
All six public checkouts were clean, with a fresh pipless venv, network Foundry
download, worker build/doctor and complete fixture/local-Anvil equality. Docker
was already running with potentially warm caches; installation/startup is excluded.
The prior complete reports and recordings are reused unchanged. Current SDK/CLI/
scenario/site PR heads match the selected pins and their required checks pass;
website deployment jobs are intentionally skipped before review/merge.
See evidence/latest-candidate/summary.json. Main still requires one independent
approval with strict freshness/admin enforcement. No main merge or deployment is
claimed. The dedicated VM was stopped afterward; the default VM is preserved.

## October 1 — CLI agent execution and complete recorded replay candidate

CLI PR #10 at 87cfe4078dfaaaa3eebcbff65bcedc8d60013cc8 builds on the existing
export-budget candidate and uses the bounded engine c167193/SDK b0c2ba3 API.
`agent-run` exposes built-in risk decisions; `replay` derives recorded steps/gas
and requires complete JSON equality before private quota-protected export.
`inspect` displays choices/reasons/original provider provenance without an engine.
No provider/code loader, native fallback, agent HTTP endpoint or v0.1 change is added.

All 40 local units and four actual Docker groups pass; Linux repeats 40 units
on Python 3.11/3.12/3.13 and four real Docker groups in 3.783 seconds. Complete
original risk/model reports match; altered state refuses without replacing an
incumbent and recovers, while unavailable/legacy engine or image fails explicitly.
All six production files pass unsuppressed quality/security, with zero findings;
42 tool identities are audited without reported vulnerabilities. Downloaded
source/wheel/18-worker-input hashes match. Samples stay byte-identical; zero new
model/archive calls, no holdout tuning or new demand/agent advantage is claimed.
See https://github.com/entrotter/cli/pull/10 and that branch's evidence/agent-cli/.

The observed GitHub Actions `agent` check is added to CLI main's required checks:
six are now required there and 33 across the six repositories. Fresh full
protection readback preserves one independent approval, strict freshness/admin
enforcement and every unrelated setting. Older partial CLI PRs need the new job
before protected integration. Independent reviews remain empty; no merge,
deployment or submission occurred. Dedicated VM is stopped and default VM running
untouched, with no owned experiment worker left. Existing coordination PR #54
still selects fa37380/a63a390, explicitly distinct from this new tested candidate.
These status/gate/required-check records are held locally for the next substantive
candidate-pin/guide integration, without a status-only PR or additional CI run.

## October 1 — Latest agent CLI candidate composition

Coordination builds on #54/99a7f4f and selects tested engine #27/c167193 and
CLI #10/87cfe40 with the unchanged SDK/schema/site pins. Current bounded
integration/type inputs now use these exact sources. The frozen native/provider,
benchmark/holdout/report inputs are unchanged. Main still requires independent
review; this is preparation of a reviewable combination, not protected integration.

Bounded-agent clean reproduction now uses the actual standalone CLI replay,
verify and inspect commands. The old CLI pin fails that real clean-checkout
regression with missing-command exit 2. Updated public source fetches, new pipless
venv, network Foundry download, worker build and complete original model replay
then pass in 19.266 seconds. Docker/VM was running and caches may be warm; setup
installation/startup excluded. No model/archive call, new evaluation or retuning.
This source-bound measurement is separate from the later guide walkthrough.

All 21 production files pass type checks against clean c167193/87cfe40 dependencies,
retaining the same three frozen provider diagnostics. The stale security source
review fails before refresh; all 78 full findings remain visible, with a changed
reproduction-loop scope/fingerprint author rationale. Independent review remains
pending. Source pins, guide/public measurements and current-head CI are recorded
separately in this candidate evidence and PR.

The corrected guide's five Bash blocks executed verbatim in a fresh temporary
public workspace in 26.043 seconds. All six checkouts were clean at their exact
immutable pins; a new pipless venv/network Foundry download/build/doctor and full
fixture/local-Anvil/risk/risk-replay/model-replay comparisons passed. The first
guide attempt incorrectly paired a candidate-only general scenario with the
original two-baseline-action risk report. Its complete equality check failed;
extracting the exact recorded scenario fixes the input mismatch without changing
reports, policy or consumed holdouts. Running Docker/potentially warm caches are
explicit prerequisites; this is not cold machine setup. Source service/CLI guides
retain separately tested older installation pins, without a new install claim.
See evidence/latest-agent-cli/summary.json; current-head CI remains separately
recorded in the PR. Main integration, independent review and submission gates stay open.

## October 1 — Independent agent-inspection review and fix

A separate Codex code reviewer found that a hash-resealed extra response `step`
could replace the causal observation step displayed by CLI `inspect`. Engine
execution already rejects that invalid typed response. CLI #10/22b514c now checks
exact response keys before inspection/replay and gives the observation step final
precedence. Three failing-before assertions become passing refusals, including
zero optional-engine calls and preserved incumbent exports. The reviewer then
confirmed resolution with focused checks; this is not a GitHub approving review.

All 42 local units and Linux units on Python 3.11/3.12/3.13 pass. All four actual
Docker groups reproduce the original complete risk/model reports in 2.935s with
no model call. Six current-head checks pass; downloaded six-source security,
CLI/SDK wheel and all 18 worker-input hashes match, including actual local SDK
bytes. The full scanner retains zero findings/skips and 42 locked packages have
no reported Python advisories. Public review/failure/fix evidence is in CLI's
`evidence/inspection-review/`; coordination selects this exact tested fix and
needs separate current-head CI. Prior PR55/2e12018 passed all five checks after
rerunning only its failed Docker-metadata job; its internal cause remains unknown.
The prior full guide timing belongs to its actual old pins; new clean replay
measurements are separate.

Independent GitHub approval remains empty; main protections and original reports
and evaluations stay intact. No model/archive evaluation, protected merge,
deployment, user outreach or submission occurred. The stopped dedicated VM is
not restarted for this parse-only local fix; Linux CI supplies fresh Docker proof.

## October 1 — Canonical local-contract identity fix composition

Independent engine source review found that two case spellings of the same
contract address can carry different code under identical canonical scenario
bytes. Actual Anvil v1.8.3 changed from success/21,000 gas to revert/21,006 gas
when only object insertion order changed. Engine #28/6e13f34 rejects duplicate
normalized addresses before native/default/agent execution and retains one valid
mixed-case address. The separate reviewer confirmed the fix; this is not a
GitHub approving review.

All eight engine current-head checks pass: 214 Linux native tests in31.108s,
22 actual Docker enforcement/lifetime/cleanup tests in213.988s and no test worker
left. Downloaded artifacts match all22 scanner sources,17 wheel modules and18
worker inputs. Full security scan retains23 reviewed findings without skips;
42 Python/26 image OS/1,126 signed native Cargo identities have zero reported
advisories, with172 non-Cargo signed entries explicitly outside the Cargo scan.
Base/native provenance and auditor/report/manifest hashes match. Host/kernel/VM
safety is not inferred from those inventories.

This existing coordination PR #55 now selects engine6e13f34 and CLI22b514c.
Frozen native/provider/benchmark/holdout/report and media inputs stay unchanged;
no new model/archive calls or local Docker/VM startup. Prior328f4c1 all-five CI
and its fixture6.308s/model6.830s measurements belong to enginec167193. The old
26.043s all-five-block guide run retains its original CLI87cfe40 sources. Neither
is a measurement of this new composition. Current combined CI must run on the
final guide commit; its exact artifact/readback links will be recorded in PR55.
See evidence/contract-identity-integration/summary.json. Mandatory independent
GitHub approval, protected integration/publication and personal/media/submission
gates remain open. Discord is discontinued and excluded.

## October 1 — Recorded-agent viewer composition

Viewer #14/49914a2 builds on8671ab2 and makes recorded reasons/choices and their
candidate outcomes inspectable, preserving original alias/nondeterminism/unknown
seed/cost and no measured model advantage. The original local model report is
copied byte-identically; all12 original agent reports retain valid hashes and
display. No new model/archive run or original-media/schema rewrite occurred.

Independent software review found and resolved3P2 consistency gaps: array-valued
choices, proposals not bound to scenario actions, and held outcomes claiming
success/nonzero gas. Four fully resealed regressions fail before the fix and now
refuse. Re-review confirms resolution; this is not an approving GitHub review.
All4 current-head site checks pass:47Node/11Python tests,28 realChromium groups,
21zero-violation axe scans and mobile keyboard scrolling. Downloaded18 source/
config/lock hashes,55 full security findings,11JS/12type inputs/14rules, Python
source/lock/42packages and109npm lock entries match, with0 reported advisories.
Raw incomplete axe/browser/advisory limits remain explicit. Mobile screenshots
were visually inspected. No import uploads or third-party requests occurred.

Coordination selects site49914a2 with unchanged engine6e/CLI22/SDK/schema pins.
Combined source pin/guide/index CI is separate from site proof; priorb724983
fixture5.853s/model5.637s belongs to site867. Frozen native/provider/benchmark/
consumed holdout/report/media sources stay distinct. See
evidence/agent-viewer-integration/summary.json. All protected-main approvals,
manual assistive-tech/full WCAG and live candidate publication/submission gates
remain open. Discord remains abandoned; no localDocker/VM startup.

## October 1 — Original signed transaction-prefix replay composition

Engine #29/0d4faf7 adds a distinct trace-version result and default bounded CLI,
preserving the v0.1 action/model-record contracts. It reconstructs original
legacy/type-1/type-2 signatures, forks the pinned parent twice with Shanghai
header context, preserves order/nonces and explicitly reports omitted,
conflicting, rejected, unmined and receipt-diverged outcomes. Independent source
review found/fixed caller-input mutation; re-review passed. Ordinary/upstream RPC
still denies raw broadcast; only the owned trace profile permits signed inputs.

All eight exact-head checks pass first attempt: 241 Linux native tests in 33.082s,
23 actual Docker tests in 215.933s, 23 source/18 wheel/19 image input hashes verified.
Ethereum block 19,000,000 transaction 0 matches the original receipt's 208,144 gas
and 8 ordered logs through the default bounded CLI in 4.484323s. Its complete result
matches the native 9.951108s record except runtime/hash. No upstream write, model
generation or holdout retuning occurred. Image/native reports, inventories,
manifests and auditors match; 42 Python/26 OS/1,126 signed Cargo identities have zero
reported advisories, with 172 non-Cargo entries outside coverage. Database metadata
matches; the CI-recorded binary database digest cannot be locally rehashed from
the exported metadata alone. No local Docker/VM startup occurred.

Schemas #11/8785bb0 adds distinct offline trace-plan/result contracts. Independent
review corrected the example from an early ignored attempt to the exact committed
engine report. All five head checks pass: 23 tests on three Python/legacy-engine
compositions, 13 source/schema/lock hashes, six Python files fully scanned, zero
findings/skips and 48 tool/6 contract package identities without reported advisories.
All 19 original result shapes remain valid; schemas verify declared shape, not
signatures, hashes, sorted/cross-field input binding or EVM truth. The actual
default-worker mainnet report also validates against these new contracts.

This existing coordination PR55 selects engine0d4faf7 and schemas8785bb0, with
CLI22/SDKb0/site499 unchanged. Frozen native/provider/model/evaluation/consumed
holdout/report/media sources remain independent. Combined exact-head CI and guide
reproduction are separate from component proof; prior5c1/2204 timings retain
their actual old pins. See evidence/canonical-replay-integration/summary.json.

The full goal remains active. At most 32 original Shanghai-prefix transactions
are currently supported; Anvil parent-state pool admission can reject valid
same-block funding dependencies and must leave those baselines unverified.
Full-block/opcode/root/end-withdrawal equivalence, broader oracle/divergence cases
and trace SDK/viewer integration remain open. Software review is not protected
GitHub approval. No protected merge, candidate deployment, outreach, media upload
or formal competition submission occurred. Discord remains excluded.

The initial86f2014 combined run passed four jobs but quality refused: the worker
type-policy JSON still required6e while its checkout advanced0d. The immutable
assertion is retained. Updating that policy pin makes the existing local type
check pass against exact cleanbb8/0d/b0/22 sources with the same three frozen
diagnostics; no script, diagnostic rule or branch protection was weakened. The
failure log is preserved; corrected snapshot/head checks remain separate.

## October 1 — Mining deadline and actual four-transaction divergence

The prior coordination0690adf/cda73fe composition passed all five checks. Its
21 sources/78 full findings/50 audited packages/19 image inputs and complete
CLI/SDK/API/export/clean reports were independently verified. Fixture6.827s and
recorded-model7.350s belong to that engine0d composition with Docker already
running and potentially warm caches; they are not a cold/all-five-guide benchmark.
PR55 contains the exact job links and artifact readback. The stale type-policy
failure was corrected with the immutable assertion and three frozen diagnostics
retained, without changing production checkers or protections.

Engine#30/8176597 fixes an actual failure: all four original signed inputs were
captured/queued, but owned-local evm_mine exceeded the ordinary ten-second RPC
cap. Only mining now uses the primitive's remaining shared150-second deadline,
then restores ordinary reads in finally. The separate node guardian is unchanged.
The original source fails the new slow-mine regression; the fixed full local
suite passes244tests31.741s. Independent source and evidence/workflow follow-up
reviews found no actionable finding; these are not GitHub approving reviews.

All eight new head checks pass first attempt:244Linux native tests33.590s and
23actualDocker cases213.407s, with no test workers left. Downloaded23source/
18wheel/19image inputs match,23full findings are retained with no skips. Image/
native/manifest/auditor/inventory hashes match;42Python/26OS/1,126signedCargo
identities have zero reported advisories,172nonCargo entries remain outside that
scope. Database metadata matches; binary database digest is recorded by CI and
not locally rehashed from exported metadata. Host/VM safety is not inferred.

The actual first four transactions of Ethereum19M match every original receipt
projection in native46.982404s and default bounded14.539113s; complete results
match except runtime/hash. These different environments are not a speed comparison.
Omitting transaction0 changes gas/logs in1/2 and leaves3 at original nonce5523
versus expected5522. No funding/code/nonce repair, new model call or holdout/media
change occurred. See evidence/canonical-mine-integration/summary.json and linked
engine raw reports/observed prior failure/reviews for exact scope and hashes.

This candidate selects engine817 with unchanged CLI22/SDKb0/scenarios8785/site499.
Worker workflow and type-policy pins are updated together. New combined-head CI
and guide reproduction remain separate from component proof. Parent-state pool
funding admission, broader oracle/missing-state cases, full-block/opcode/end-state
and trace SDK/viewer integration remain open. All protected approvals/candidate
publication/personal/media/submission gates remain open; no local Docker/VM
startup, protected merge, media upload or formal submission occurred.

## October 2 — Typed signed-prefix inspection integration in progress

SDK#7/ee5523d adds a separate immutable offline trace reader. All five required
checks pass:36tests each on Python3.11/3.12/3.13,5production sources fully checked,
3installed wheel modules/marker verified,42exact locked audit identities and7doc
hashes match without findings/skips/advisories. Four independent consistency
findings were fixed and re-reviewed. The v0.1 HTTP client remains unchanged.

Viewer#15/b7c20ce adds distinct browser-only original-prefix inspection. Root review
resolved six codec/snapshot/bounds findings;63Node/11Python tests,21source hashes,
97full explained findings,42Python/109npm identities and11doc hashes match.
All four required checks pass. Downloaded Linux browser evidence passes33groups/
25raw axe scans with0violations;13source hashes and the runner match. Root inspected
1280/320px signed-prefix captures;390px, keyboard native chooser, invalid/resealed/
oversized inputs, delayed-load races, recovery and no-upload/third-party-request
gates pass. Incomplete contrast remains explicit;244opaque CSS comparisons are
supplemental, with no manual screen-reader/full WCAG certification claim.

Previous failures remain recorded: fd7 apt setup timed out, then retry exposed a
1280px native chooser harness failure. Actual Tab navigation fixes that gate;
0c again timed out during apt setup before the harness. Changing only Azure's
Ubuntu mirror URI to the official HTTPS archive fixes setup while preserving
signed apt, suites/components/keyring,10minute limit and every browser gate.
Root independently reviewed both concrete harness/setup fixes. No product source
changed in those fixes. The final Linux run passes, separately from prior attempts.

The prepared coordination composition adds the exact offline SDK/site/coordination
fixture-byte check and typed four-receipt/gas/log/nonce inspection. That workflow
step and21-source type policy pass locally with the three frozen diagnostics
retained; independent review of the four-file integration has no actionable
finding. The guide now gives actual SDK and local-viewer instructions. The immutable
execution snapshot is968b488, selecting SDKee5523d/siteb7c20ce; guide/index refs
match those exact pins. Final snapshot/docs re-review passes after fixing a missing public proof pointer;
combined exact-head CI remains pending, with evidence in final-review.json.
See evidence/trace-reader-integration/README.md. These are existing original
reports, not a new chain/model call or timing claim. Combined new-head CI remains
separate from the previous42eb191 five-check proof.

The full goal stays active: same-block funding admission, broader oracle/missing
state coverage and full-block/opcode/end-state scope remain open. Required GitHub
approval, candidate Pages publication, personal facts/terms and submission gates
remain separate. No localDocker/VM startup, protected merge, new model/holdout
evaluation, media upload, formal submission or Discord work occurred.

## October 2 — Same-block signed funding candidate preparation

The previous86a/968b reader composition passed all five first-attempt checks.
Downloaded21-source type inputs/three frozen diagnostics/78full retained findings/
50audited packages/19image inputs/54doc hashes match. Full API/CLI/admission,
normal and optimized exports, fixture and recorded-model reproduction pass;
clean fixture8.763215s and model8.018850s belong to engine817 with Docker already
running and potentially warm caches. These are not cold/full-guide measurements.
See evidence/trace-funding-integration/previous-reader-ci.json and existingPR55
job links. Public evidence in the older reader folder records its earlier prepared
state; current pass does not backfill those historical records.

EnginePR31/935558a defers parent-state pool balance/fee/gas checks only on owned
trace nodes. Actual ordered EVM/block validation, signatures, loopback/no-mining,
memory bound, guardian/deadline and ordinary profiles remain unchanged. Two
regressions fail before the fix; four focused and248 full native tests pass after
with0skips. Native synthetic funding produces two matching original signed
receipts, gas21000/21000 and cumulative21000/42000; omission leaves a dependent
spend unmined without a receipt. Invalid gas/fee/nonce inputs leave state unchanged.
No replay balance/nonce/code repairs or sequential different-block workaround.
Independent source/evidence review passes after redacting public local-installation
paths; ignored originals and test outcomes remain unchanged. All8 new-head checks pass first attempt:248 Linux native tests36.615s and24
actual Docker cases221.940s without skips. Root verifies23source/18wheel/19image/
42Python/26OS/1126signedCargo/11doc bindings, retained full findings and exact
original historical receipt projections. Current default four-prefix24.17299s
keeps the complete previous outcomes except runtime/hash and one accurate admission
assumption. Current SDK offline readback also passes. Database binary digest is
CI-recorded, not locally rehashed from exported metadata;172nonCargo entries remain
outside the Cargo audit. Synthetic image/protocol funding is distinct from the
actual default host historical case. Human GitHub approval remains separate.

The new immutable coordination source snapshot a253da8 selects engine935 with
unchanged SDKee/CLI22/schema8785/siteb7. Four-file source review has no actionable
findings;21-source types and the same three frozen diagnostics pass. The exact
new offline CI step checks the frozen synthetic report with the typed SDK and
actual viewer codec at Node22.23.1; baseline/adverse statuses, gas/cumulative and
absent candidate receipts match. Rendered browser and historical funding proof
are not inferred. See evidence/trace-funding-integration/README.md. The quick-start
and latest submission index select this snapshot; old report/model/holdout/video
sources and measurements retain their actual pins. New combined CI is pending.

Archived same-block funding, broader oracle/missing-state cases and full-block/
roots/end-state/opcode scope remain open. Protected human approvals, candidate
Pages publication, personal facts/terms and formal submission gates remain open.
No local Docker/VM startup, upstream writes, new model or holdout run, media upload,
protected merge, package publication, formal submission or Discord work occurred.

## October 2 — Signed oracle/provider candidate integration prepared

The previous8029/a253 funding composition passed all five checks. Downloaded
21source/78full retained findings/50audit/19image/55doc bindings and complete
API/CLI/admission/export/reproduction proof pass. Clean fixture7.477365s and
recorded model8.196629s retain engine935, running Docker and potentially warm
caches. The new evidence folder preserves that complete prior proof separately
from its older author preparation records.

Enginee849/PR32 adds four signed synthetic oracle/provider-fault native regressions
and one direct image/protocol case. Original update20 plus independent consumer
receipts match gas26167/26438; omission from parent10 preserves the consumer hash
but reverts at25808gas without logs. Normal read-only provider control verifies
receipts. Missing parent/code/balance explicitly fail; missing mining-time storage
produces an integrity-valid unverified report without receipts. Only one accurate
report assumption changes; state/signature repairs or inferred error causes are
not introduced.252localnative and252Linuxnative38.944s pass without skips. Root
source/evidence review verifies23source/18wheel/42lock and unchanged findings.
Two prior investigation raw files were overwritten by an ignored generator and
are unavailable; that loss is disclosed. Current separately saved native proof
is not presented under their old hashes.

The immutable coordination source snapshot27c39fe selects enginee849 with the
other dependency/frozen/model/holdout/media pins unchanged. Four source files pass
independent review;21type inputs retain the same three frozen diagnostics. The
exact new offline SDK/site step verifies three fixed positive/control/storage
reports, receipt success/revert/gas/logs and unverified receipt absence. Existing
original four-prefix/funding reader steps also pass with current pin metadata.
See evidence/trace-oracle-integration/README.md. Component isolated CI twice failed at
the historical1 default worker after25Docker tests passed216.086/216.203s; later
full4/image/native audits did not run. Both full failures are preserved; cause
remains unknown despite healthy same-source readonly followup. Further blind
retries stopped; a failure-only bounded diagnostic is being implemented for
independent review. Combined new-head CI is not started.

Archived oracle/funding, provider authenticity and full-block/root/end-state/opcode
scope remain open. Protected human approvals, candidate Pages publication, owner
facts/terms and formal submission remain separate gates. No local Docker/VM
startup, upstream write, new model/holdout/media run, protected merge, package
publication, formal submission or Discord work occurred. Overall goal active.


## October 2 — Failure-only diagnostic reviewed and real divergence retained

EnginePR32/aac525c adds a reviewed trusted test-only diagnostic; production23
source/script bytes,18wheel modules,19image inputs and policy remain unchanged.
Root review fixes owner-cleanup/descriptor-close fault paths and missing-code
TLS classification. Three regressions fail before fixes;15focused tests pass
0.729s, including real embedded invalid-input execution. Root separately executes
three such cases without Docker/network and checks17source/evidence hashes plus
11original/redacted copies. Published failure records retain raw trailing spaces;
no evidence-normalization or secret/state substitution occurs.

Seven exact-head checks pass:267Linux native tests41.207s without skips,
four267-test unit matrices with31real-Anvil skips each,23full reviewed source
findings/42exact locked packages/18wheel modules and13document hashes. Isolated
CI36913460373 passes25Docker tests217.511s, mainnet1 original receipt9.143445s
and all4baseline receipts29.610351s. Candidate transaction2 is not_mined without
a receipt; the unchanged status assertion fails. Later exact-plan diagnostic
completes normally, so the original cause remains unknown. Cleanup passes;
subsequent image/native advisory gates do not run. No blind retry or all8 claim.

Root independently verifies raw bindings and both actual reports through SDKee
and viewerb7 codec, preserving the failed candidate outcome. Current partial
proof/reports/followup are in evidence/trace-oracle-integration. Local four-pin
edits select aac;21types and all3offline reader steps pass, independent pin review
has no findings. Earlier27source snapshot/docs preparation remains local; no new
immutable composition, combined CI or publication is claimed. Public8029/a253
with engine935 remains the latest fully tested composition. A controlled
same-invocation node-log observer is under investigation; no original provider
cause is inferred from receipt absence or a successful later repeat.

All full-goal gates remain active, including archived oracle/funding and
full-block/root/end-state/opcode scope, protected human approval, candidate Pages
publication, required facts/terms and formal submission. No local Docker/VM,
upstream write, new model/holdout/media operation, merge, package publication,
formal submission or Discord work occurred in this step.


## October 2 — Integrated observer native proof independently reviewed

The failure-only trusted diagnostic now binds finite owned-node events to its
actual worker envelope, baseline/candidate branch and unchanged original input
indices. Normal mandatory commands and23production sources remain byte-identical
to aac. Frozen source/fixture/binary/protocol evidence and raw original/control/
missing-storage reports pass independent root inspection; all three also pass
SDKee and the actual viewerb7 codec. Normal and adverse receipts match unchanged;
injected missing storage produces bound execution-skip counts2/1 with complete
EOF/no truncation. Seven nodes, eight readers and two proxy handlers/listeners/
ports close, and source oracle/nonces remain unchanged. See
[evidence and limits](evidence/trace-oracle-integration/README.md).

Fourteen focused observer tests, one separately added real collector-descendant
regression and15existing diagnostic tests pass. The collector regression proves
its own bounded timeout/descriptor/group cleanup; original trace failure survives
secondary collection errors. Final15-test source is separately frozen; no claim
that earlier14tests executed the later file. Packaging and required new-head CI
are pending. The old historical candidate failure is preserved and its cause is
unknown; later/synthetic diagnostics do not replace it. Full G1–G5 remain active,
and no new composition, protected merge, Pages publication or submission occurs.
Discord remains excluded.


## October 2 — Current component all eight verified; composition prepared

Engine99fd/PR32 passes all8first-attempt checks. Root verifies complete raw23
source/18wheel/19image/42Python/26OS/1126signedCargo/14docs and282native0skip,
25Docker217.324s, default1/4 receipts and complete prior935report values except
runtime/hash/exact added assumption. Current candidate4 has expected skipped/
executed/executed/nonce_conflict statuses. Actual SDKee/siteb7 codec checks the
current report hashes/statuses. Conditional diagnostic is skipped; prior failed
reports and unknown cause remain separate. No retry, weakened assertion or claim
of actual observed Docker/historical helper dispatch. See
[evidence](evidence/trace-oracle-integration/README.md).

Reviewed sourcee46 selects99fd through four exact selectors only;21type inputs
retain the same3frozen diagnostics and all3exact offline workflow steps pass.
Other dependencies, frozen scenarios, recorded model/holdout/media stay unchanged.
Current source/docs remain local pending consolidated publication and all5combined
checks. Previous public8029/a253/935 remains the fully tested public composition.
Human protected-main approval and candidate Pages publication remain separate.
Full G1–G5 and official submission stay active; Discord excluded.


## October 2 — Published affc805 composition: all five first-attempt checks

The current public PR55 compositionaffc805/sourcee46 selects engine99fd,
SDKee/CLI22/schema8785/viewerb7. All5first-attempt checks pass. Root independently
verifies21source/78full retained findings/50locked packages/19image/56docs and
complete API/CLI/shared admission/normal-optimized exports/3offline reader proof.
Clean fixture7.169045s and recorded model replay7.622255s preserve exact artifacts;
Docker/cgroup-v2 was running and caches may be warm, installation/VM startup
excluded. No new model/holdout call or current rendered-browser proof. Separate
native compatibility jobs keep their frozen variants; current logs and older
uploaded browser/archive/model evidence are not conflated.

CI36925370461(workspace),36925370527(quality),36925370525(docs) and the exact full
root proof SHA7d1d2709c971ea780adf24790c88b1cc9e8306fd893020e8078753ef48207b49
are recorded in existing PR55; local .quality/oracle-integration/ci-verification.json
and its raw artifacts are the durable full proof. Public pre-CI preparation docs
are historical snapshots; this local completion checkpoint is held for the next
substantive change instead of a status-only commit/extra CI. Human GitHub approval
remains0; strict main protection/one approval/admin enforcement stay enabled.
Candidate Pages publication, required owner facts/Terms and formal submission
remain open. Archived oracle/provider authenticity/full-block/root/end-state/
opcode scope and earlier intermittent failure cause remain unresolved. Full goal
active; Discord excluded. No protected merge, package publication or submission.


## October 2 — Archived oracle baseline preserved; candidate still fails

The active October2 owner policy continues improvement until the official
October13 15:59JST deadline; official section5 was rechecked during this work.
Current public candidates remain coordinatoraffc805/engine99fd, with their earlier
all5/all8 checks scoped to those exact heads. PR47f142 is an ancestor ofaffc805.

A bounded read-only discovery identifies original signed transaction12 updating
the ETH/USD aggregator in Ethereumblock18999892. Two explicit native diagnostic
attempts preserve the same first32 inputs, skip12 and150s trace budget. Both
paired executions fail. Native001 loses in-memory baseline receipts on candidate
failure; a separately reviewed atomic recording fix addresses that evidence loss.
Five offline fault/privacy tests pass, without changing production source for
these diagnostic attempts. Root independently reviews native002's72frozen
bindings and all32 complete projected baseline receipts against captured originals.
Initial owned parent/getter values match; baseline answer changes257082415000
to256292441874. Candidateevm_mine fails; underlying cause and omission outcome
remain unknown because the original transport discarded the cause. Both attempts'
owned guardians exit0 and ports close; final OS/port checks confirm cleanup.

See [retained raw evidence and limits](evidence/archived-oracle-diagnostic/README.md).
No default Docker/archive omission/actual consumer/provider authenticity/full-block
claim follows. Existing errors remain preserved. A product RPC diagnostic change
is now being implemented so future failures can expose safe finite causes without
provider URLs/messages. New source tests/review/publication/required CI remain
separate from the historical99fd/affc805 checks. Protected integration, Pages,
owner facts/video Terms and formal submission remain open; Discord excluded.


## October 2 — Safe RPC diagnostics selected; archive timeout classified

The previous public158fbc0/engine99fd composition passes all5 first-attempt
checks and complete independent21-source/78-findings/50-package/19-image/
57-document/API/CLI/admission/export/3-reader artifact review. Clean fixture
6.674s and recorded-model6.853s retain original report identities, with Docker
already running/potentially warm caches and installation/VM startup excluded.
These measurements belong to the previous composition, not the new selection.

Engine65c2833/PR33 adds finite private-safe RPC transport diagnostics and rejects
valid-JSON truncated HTTP responses. All8 current-head checks and complete fresh
artifact review pass:294 Linux native tests0 skips/47.122s, four294-test unit jobs
with31 explicit Anvil skips each,25 actual Docker tests/214.044s,23 source/security
findings,18 wheel modules,42 Python/26 OS/1126 signed Cargo packages,19 image inputs
and15 documentation hashes. Default worker/HTTP envelopes remain unchanged;
detailed codes cross trusted Python/native CLI only. Historical component records
remain distinct. The current bounded/quality selection promotes65c through four
exact selectors; frozen native/agent/host variants and all other pins are unchanged.
Local21-source type checks retain3 frozen diagnostics, and all3 exact offline
SDK/viewer reader steps retain complete previous outcomes apart from the engine pin.
New combined CI and protected-main approval are separate pending gates.

Actual native diagnostic003 retains the same32 signed inputs, skip12 and shared
150s trace budget. Independent review verifies72 frozen bindings, source and all
32 full projected baseline receipts byte-identical to002, identical initial owned
parent/getters and baseline feed update. Candidateevm_mine is classified as an RPC
transport timeout in this invocation:152.059s child/152.162s host. The underlying
archive/miner/provider cause remains unknown; no retrospective001/002 cause or
candidate branch/final protocol result is inferred. Both guardians exit0, ports
close and final independent OS/port checks pass. Earlier public evidence remains
unchanged. See [raw evidence and full limitations](evidence/rpc-diagnostics-integration/README.md).

A separate bounded parent-state read cache is under implementation on a local
engine branch. No cache performance/archive success is established yet. Source
review, actual synthetic outcome/duplicate-read/cleanup controls and required CI
precede any new archived paired run. No time budget, signed input, nonce, funding,
state or header repair substitutes for a successful original-scope run. Main
approval, candidate Pages, owner facts/video Terms and formal submission remain
open; the full G1–G5 improvement goal is active and Discord is excluded.


## October 2 — Concurrent parent cache: original prefix completes

Engine198139f/PR34 shares bounded pinned-parent reads without serializing distinct
keys; receipts/errors/volatile reads remain uncached. All8 exact component checks
and independent full source/wheel/image/security/receipt artifact review pass:
323 native tests/74.006s/0 skips, four323-unit jobs/33 explicit Anvil skips each,
25 actual Docker tests/216.854s,25 production sources/findings,20 wheel modules,
21 image inputs,42 locked Python packages,26 OS packages and1126 signed Cargo
identities with0 reported advisories.172 native components remain outside Cargo
advisory coverage; the non-exported database binary is not locally rehashed.

The first two mandatory docs attempts failed on6 then3 existing GitHub HTML
HTTP503 links. After13 targets recovered with the pinned bounded settings, only
the failed existing job was rerun. Attempt3 passes143 links/0 errors/timeouts,
16 exact document hashes and complete merge-tree equality to198139f. Failures
are retained; no exclusions, assertions, source or required gate were weakened.

Actual native005 retains original32 signed inputs from block18999892, skip12
and shared150s trace cap. It completes in125.358s with all32 complete projected
baseline receipts byte-equal to originals and003; candidate executes31 and skips12.
Initial owned heads/getters match. Baseline producer answer changes257082415000
to256292441874; candidate keeps the initial answer. Other31 gas/status/logs/bloom/
identity fields match; later position/cumulative gas shifts exactly by omission.
Owned2 Anvil nodes and cache PID/groups/ports/pipes close, independently probed.
Cache1871 requests/966 upstream/899 hits includes6 aggregate errors of unknown
cause. Prior001–004 failed runs remain immutable. This32-of181 native producer
case establishes no dependent-consumer/strategy/profit/full-block/root/opcode/
provider-authenticity/default Docker32 or speed/timeout-causality result.

The current coordinator selection changes exactly4 engine selectors65c→198;
frozen native/agent/host variants and other components are unchanged. Local21-
source type checks retain3 explicit frozen diagnostics; all3 offline SDK/Node
reader steps preserve complete prior outcomes exceptenginepin. Exact b7 Git
blobs insulate that parser proof from concurrent local viewer development.
See [component and preparation evidence](evidence/trace-parent-cache-integration/README.md).
The previousccc/65c composition passes all5 combined checks and its clean replay
measurements retain their original scope. New combined CI, protected-main human
approval and candidate Pages publication remain separate. No main merge, new
video, package publication or formal submission is claimed. Goal active through
the officialOctober13 15:59JST deadline, recheckedOctober2; Discord excluded.


## October 2 — Original receipt comparison enters the pinned composition

Viewerb1cfb00/PR16 classifies candidate differences against original projected
receipts, retains every exact differing field and distinguishes omitted/unavailable
receipts. Import captions show actual32/through31/skip12 separately from the
recorded four-input sample. Independent local source/visual review and fresh Linux
CI artifacts pass: all4 required first attempt,66 Node/11 Python tests,15 JS/16
type inputs,99 unsuppressed source-bound findings,109 npm/42 Python identities
with0 reported advisories,36 browser groups/28 raw axe scans0 violations. Contrast
incomplete results remain; no manual accessibility certification is claimed.
All56 committed source/evidence blobs,22 quality hashes,15 browser input hashes,
12 documents/51 links and the complete synthetic merge tree match the head.

The current execution snapshotbaf58f4 selects viewerb1cf through exactly2 pins,
retaining engine198, SDKee, CLI22b, schemas878 and every frozen compatibility
variant. One mandatory integration step inspects the original native00532 report
through both SDK and the actual Node viewer validator/classifier. Engine/fixture
bytes matchSHA72b9765731a77c06df1200a2dcf46f74cb7f512758ab35029ae9cef2c6ef2120;
all32 baseline receipts equal originals. Candidate omits12; the later19 full
receipts differ only by index-1/cumulativegas-336752. Summary12matches/1omission/
19structural/0execution differences preserves all32 classification records.
All4 exact local workflow reader steps pass; other3 complete outcomes match prior
404e8db except viewer pin. Initial private checkout guards refused old direct
CLI/schema branches before executing any product code; exact pinned worktrees
resolved the setup. No EVM/archive/model/browser call was added by this integration.

The404e8db/198 composition's all5 required CI/full raw review and clean fixture
6.779s/model7.012s timings remain historical, with running Docker/cgroup-v2,
potentially warm caches and installation/VM startup excluded. Current composition
CI and protected-main human approval/Pages remain separate. See
[exact source and reader evidence](evidence/trace-comparison-integration/README.md).
Original32 native producer proof is not a dependent-consumer/profit/full-block/
provider-authenticity result. Videos/model/holdout inputs remain unchanged; formal
submission is not claimed. Goal remains active; official rules section5 rechecked
October2 11:37:37UTC still endsOctober12 23:59PT/October13 15:59JST. Discord excluded.


## October 2 — Recorded Aave consumer price dependence enters integration

Enginebd5527f/PR34 publishes the actual native006 original32-of181 Ethereum
block18999892/skip12 paired replay and fixed owned Aave/WETH view records. All32
complete projected baseline receipts equal originals; candidate executes31.
Aave price matches producer answer in all4 phases: baseline257082415000→
256292441874, candidate keeps257082415000; base unit100000000. Same initial owned
heads/getters, nonempty/stable returned oracle/proxy code and closed owned2Anvil+
cache are independently reviewed. Runtime132.703s retains original shared150s
cap. Seven cache aggregate errors have unknown cause. Read-only dependence does
not establish signed consumer action/strategy/profit/full-block/root/opcode/
provider authenticity/default Docker32 or timeout/speed causality.

The public component's all8 first-attempt checks and complete source/wheel/image/
dependency/docs review pass:323 native0skips/25Docker/33 research controls,
25 production sources unchanged from198,20 wheel/21 image inputs,42 Python/
26OS/1126 signed Cargo identities with0 reported advisories,17 documents/164 links.
172 native components remain outside Cargo advisory coverage; non-exported
security database binary is not rehashed. The63 published changed blobs and57
provenance copies are verified. Publication-time pending CI is superseded by the
later component review, while both original records remain preserved.

Exactly4 selected engine references now point198→bd; other components and every
frozen native/agent/host variant are unchanged. A fifth mandatory integration
step inspects native006 through SDKee and actual Node22.23.1 viewerb1cf. It checks
all32 receipts/classifications,4 strict raw ABI consumer/producer phases, pinned
initial head and post number/timestamp, currency/unit/source and returned code
identities. All5 offline cases pass; complete previous4 outcomes remain unchanged
exceptenginepin. Local21-source typing retains3 explicit frozen diagnostics.
These are recorded-byte inspections, no new EVM/archive/model/browser execution.
See [scope, source bindings and full outputs](evidence/consumer-price-integration/README.md).

The previous bb9cada/engine198/viewerb1cf composition passed all5 first-attempt
checks and full artifact review; its clean fixture6.276s/model5.564s retains
running Docker/cgroup-v2 and potentially warm caches, excluding installation/VM
startup. That verified snapshot is historical. Independent preparation review
and new bd-composition CI precede publication. Protected
main human approval and candidate Pages remain separate; standard selected
trace-run does not yet collect extra consumer views. Supported observation CLI
work is isolated on a separate engine branch. Videos and model/holdout inputs
are unchanged; no formal submission or overall G1–G5 completion is claimed.
Goal remains active through the officialOctober13 15:59JST deadline, freshly
recheckedOctober2 13:26UTC; Discord excluded.
