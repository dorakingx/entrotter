# Verified implementation status

Updated 2026-09-20 JST. **Goal active; not submission-ready.** This turn made
implementation and deployment progress. All six repositories now exist publicly
under https://github.com/entrotter. Do not repeat archive bootstrap or overwrite
remote history. Use the existing six sibling Git checkouts and focused PRs.

## Verified progress

- Foundry v1.8.3 release archive downloaded and SHA-256 checked against GitHub
  release metadata. Local executable: `../.tools/foundry-v1.8.3/anvil` from this
  coordination repo. `evidence/foundry-install.json` records exact version/digest.
- Full workspace check: **121 Python tests and 13 JavaScript tests passed**,
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

## Open gates and next actions

1. All current engine/scenario/viewer changes are merged and live. Five component
   repos now require passing CI and one PR approval, including admins. Apply the
   same protection to coordination after its evidence checkpoint merges.
2. Complete security/delivery: whole-process CPU/RSS/time/disk/concurrency bounds,
   SIGTERM handling, deeper RPC/API fault tests, lint/types/security/dependency and
   docs-link CI, remaining immutable dependencies, and branch protections.
3. Add constrained causal agent observations/actions and one real recorded agent;
   disclose model/prompt/limits/cost. Build three sourced cases and untouched
   holdouts. Current manually prescribed actions are not an integrated agent.
4. Compare the same task with direct Anvil scripting. Historical trace replay remains unsupported; never
   describe archived-state actions as a reconstructed counterfactual market.
5. Complete accessibility/link review and submission materials. Actual pitch/demo
   videos, three genuine target-user evaluations, joined-event verification and
   owner eligibility remain pending. Outreach and submission require owner approval.

No arbitrary user code execution, public engine, paid service, package publication,
mainnet transaction, customer outreach or competition submission was performed.
The current per-EVM memory bound is not a complete process sandbox. Preserve these
limits in the product and release-gates.json. Overall completion remains unproven.

## Historical: selective Typefully publishing — September 27, 2026

Retired at the owner's request on October 30, 2026. The implementation and setup
instructions below describe historical work, not an active feature or pending task.

- A focused branch from remote main `5401d56` adds an explicit Issues editorial
  queue for @entrotterxyz, Typefully Public API v2 single-X scheduling, daily/manual
  workflows, a candidate form, tests and `docs/social-publishing.md`. No engine or
  v0.1 scenario/result contracts change. No post is generated from commits.
- Forty-five mocked publication tests pass under normal and optimized Python.
  They cover monthly 0–9/10+ boundaries, cross-month/thread counts, 48-hour cooldown,
  priority/approval order, invalid copy, pagination, dry-run transport isolation,
  rate limits and crash-safe duplicate prevention. Twelve simulated runs schedule
  exactly ten posts even when Typefully history disappears. No real slot was used.
- Six existing coordination tests pass with the unchanged CI dependency pins,
  including a real temporary loopback SDK/API roundtrip. The first sandboxed socket
  bind failed; the authorized rerun passed. Ruff, mypy and full unsuppressed Bandit
  pass; both workflow files pass checksum-verified actionlint 1.7.12 and all three
  new YAML files parse. See `evidence/social-publishing/verification.json` and logs.
- Seven editorial labels and locked durable journal issue #50 were created and
  read back. A reservation precedes the only Typefully POST; an uncertain response
  freezes further attempts, while candidate completion labels wait for validated
  success. Successful journal records remain terminal even if candidate updates
  fail. `social:scheduled` does not claim X publication.
- Fresh secret-name inspection found neither required secret. No credentialed
  Typefully calls, live post, main merge or deployment occurred. Exclusive queue
  ownership, disabled Auto-Plug/Auto-Retweet and UTC calendar settings must be
  confirmed via `TYPEFULLY_QUEUE_READY=true`; another writer cannot be controlled
  atomically by these APIs. Setup/recovery limits are explicit in the guide.
- Protected main still requires independent approval plus integration,
  bounded-default, docs-links, host-bounds and quality. Four of those workflows are
  absent from current main and live on earlier review branches; this scoped PR
  does not bypass or weaken their integration requirement.


## October 30, 2026 — social publishing removed

The owner requested removal of remaining automatic SNS posting. Removed the
Typefully publisher, daily/manual publishing workflow, dedicated tests/workflow,
candidate issue form, setup guide, README link and active release-gate entry from
`feat/selective-social`. Historical evidence is retained without rewriting it.
The inspected remote `main` and current monorepo candidate contained no publisher.

GitHub PR #51, candidate #52 and journal #50 were closed without merging. Candidate
#52 no longer has publishing approval. The two Typefully Actions secrets and
`TYPEFULLY_QUEUE_READY` variable were deleted; the registered social test workflow
was disabled. No social workflow was running at inspection. No Typefully API call
or SNS publication was made. External Typefully account settings and any drafts
created independently of this repository were not inspected.

Verification: all six existing workspace tests passed on macOS with Python 3.13
using the unchanged CI dependency revisions in an isolated temporary sibling
workspace (`python3 -m unittest discover -s tests -p test_workspace.py -v`).
This includes a real loopback SDK/API roundtrip, CLI/report validation and fixture
contracts. `git diff --check` passed. Removed paths are absent, the release-gate
JSON parses, and no active publisher/configuration references remain outside this
historical status and the preserved evidence. No model or paid API was used.
