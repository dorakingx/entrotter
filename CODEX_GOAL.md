# Entrotter: persistent implementation goal

## Current owner policy — October 2, 2026

The active October 2 goal supersedes earlier initialization and submission
approval wording. Continue improving the demonstrated product until the official
deadline, currently **October 13, 2026 at 15:59 JST / 06:59 UTC**. Recheck the
[official rules](https://colosseum.com/legal/Crypto%20World%27s%20Fair%20Hackathon%20Rules.pdf)
at execution time; section 5 was checked again on October 2 and states October 12
at 23:59 Pacific. CI success, completed checklists, prepared PRs, readiness or
formal submission are checkpoints, not reasons to finish the improvement goal.

Resume the latest tested candidates and existing evidence, recordings and videos.
PR47's f1421ff remains an ancestor of the evolving PR55 candidate. Preserve its
work rather than returning to old main or the initial ZIP. Use current STATUS.md
and dependency pins, and verify remote heads before integration. Do not create a duplicate goal or session.

Once quality, required owner facts and submission materials are verified and the
portal is open, formal submission of the existing entry is already authorized
without another blanket approval. Confirm the server acceptance and exact code
and video versions. Continue authorized improvements afterward until the deadline;
do not alter an immutable submitted version. Authentication, terms, mandatory CI
and independent approval remain required. Unknown personal facts cannot be guessed.
Discord is excluded. Respect explicit owner stop or pause instructions.

## Mission

Build Entrotter into an independently reproducible, compelling, fully open-source
entry for Colosseum Crypto World's Fair. Aim for a grand-prize-quality product:
real user value, technically credible execution, differentiated insight, clean
contribution paths, a polished 3-minute live demo and an honest business case.
Winning is an external judging outcome, not a software acceptance test. Never
claim a win or declare the goal complete based on self-awarded scores.

The owner explicitly requests implementation, not another plan. Continue actual
implementation, tests, review, fixes and deployment until every actionable
acceptance gate below has evidence. Do not stop merely because scaffolding,
a README, a mock demo, a website or one passing test is complete. Avoid repeatedly
asking whether to continue. Within authorized access, resolve routine engineering
decisions yourself and record them.

## Binding constraints

- Organization: `entrotter`. Use an existing organization, verify the authenticated
  user's rights, and never publish under another account as a silent fallback.
- Six functional repositories from repositories.json. All NEW repositories public,
  all original code MIT licensed. Do not expose a pre-existing private repository.
- Publish only OSS docs and a read-only example report viewer to GitHub Pages at
  `https://entrotter.github.io/`. No custom domain, CNAME, DNS change, Vercel or
  paid hosting. The backend runs locally for this milestone.
- Read AGENTS.md, README.md, STATUS.md, evidence/, ROADMAP.md and backlog/ first.
  Inspect existing files and remote history before changing anything.
- Keep interfaces versioned, repositories independently testable, and PRs focused.
  Use English code/UI/docs. Preserve the supplied purple Entrotter mascot asset.
- Do not publish packages to npm/PyPI, buy services, announce partnerships,
  message users or broadcast live transactions without explicit authorization.
  Repository/Pages publication and conditional formal submission of the existing
  entry are already authorized under the current owner policy above.
- Never put real keys, RPC secrets, auth tokens or private user data in public Git.
  Do not disable secret scanning, tests, validation or branch protection to pass.

## Resume actions

1. Confirm the existing goal is active and inspect current candidate heads,
   relevant diffs and unresolved requirements in STATUS.md and release-gates.json.
   Reuse unchanged evidence; distinguish historical results from fresh execution.
2. Keep the existing six public repositories and compatibility paths. Do not
   repeat Git initialization, repository/Pages bootstrap or replace current work
   with the original archive. Inspect permissions when an action needs them.
3. Choose a concrete developer-value improvement, implement it, run relevant
   real tests, independently review and fix it, then integrate through required
   CI and independent approval. Verify publication rather than inferring it from
   a pushed branch or workflow file.
4. Record exact sources, environment, command, observed results and limitations.
   Preserve frozen model/holdout inputs; avoid extra CI or status-only commits
   merely to restate successful checks. Continue the next valuable improvement.

## Acceptance gates (all need evidence; do not check off intentions)

### G1. Reliable core, not a mock

- Real Anvil local execution passes for success, revert, rejected transaction,
  isolated baseline/candidate state and process cleanup after error/cancellation.
- Real archived-state execution works on at least one EVM chain and protocol
  using a pinned chain ID, block number/hash and contract addresses. Pin tool
  versions, scenario/action inputs and any overrides. Archive access failures
  must be explicit. Never silently substitute a synthetic fixture.
- Add ERC-20 state/decimals and a useful DeFi action adapter, not just native
  transfers. Include exact gas/receipt/state deltas. Never call token/native
  transfers "profit" without a defensible valuation model.
- Separate (a) archived-state action execution, (b) historical trace replay,
  and (c) model-based counterfactual simulation in APIs, docs and reports. Do
  not claim automatic reconstruction of a changed economy. For replay, explicitly
  handle nonce/order conflicts, state divergence, oracle inputs and missing state.
- Demonstrate baseline and changed decision from identical initial conditions.
  Include an adverse result, not only an improvement. Quantify missing assumptions.

### G2. Agent value and reproducibility

- Add a constrained agent interface accepting causal observations and producing
  typed actions. Never pass future observations to the policy.
- Integrate one real agent through recorded, auditable tool actions, with model,
  prompt/version, seed when available, limits and costs. Replay recorded actions
  deterministically; do not call an inherently nondeterministic LLM deterministic.
- Compare a non-agent baseline, a deterministic risk policy and the integrated
  agent over at least three sourced scenarios plus untouched holdout cases.
- Record runtime, failed transactions, gas, drawdown where meaningful, resource
  use, assumptions and source pins. No fake percentages, user counts or revenue.
- A contributor on a clean checkout must reproduce the offline example in under
  five minutes; benchmark this rather than asserting it. Run a clean-environment
  historical demonstration and provide the exact command and source requirements.

### G3. Security and software delivery

- Upstream RPC transports cannot broadcast transactions. Local writes target
  owned isolated nodes, not arbitrary user-specified RPC endpoints.
- Prove cleanup on timeout, cancellation and fault injection; cap CPU/memory/time,
  calldata, logs, disk use and concurrent work. No shared mutable fork sessions.
- Never execute untrusted agent code via direct Python import or a raw shell.
  Add a proper sandbox and egress restrictions before exposing external code
  execution. If not implemented, keep that capability disabled and document it.
- CI checks tests, lint/type checks, schemas, contract tests, dependency/security
  findings, broken docs links and a CLI-to-SDK-to-engine smoke test. Real EVM CI
  is distinct from offline tests. No empty green jobs or silently skipped gates.
- Each repo has README, MIT LICENSE, CONTRIBUTING, SECURITY, tests, PR/issue
  templates and scoped good-first-issues. Enable private vulnerability reporting
  where available. Protect main with reviewed PRs when supported; never pretend
  protection is enabled if the API or plan denies it.

### G4. Public OSS site

- Pages deployment succeeds at the default github.io address, no CNAME.
- The site is fast, responsive, keyboard accessible and English; dark/purple visual
  identity with restrained artwork, no visual clutter or fabricated adoption badges.
- Visitors can understand the problem, reproduce an example, inspect real report
  assumptions and find the right contributing repository quickly.
- Static report import stays in the browser. Do not upload private reports,
  wallet data, credentials or analytics. Do not turn Pages into commercial SaaS.
- Verify mobile/desktop rendering and artifact parsing, unsafe input handling,
  links and no unexpected third-party network requests.

### G5. Competition readiness and genuine demand

- Re-check https://colosseum.com/hackathon and the joined event for current rules,
  exact deadline/time zone, eligibility and required files. Do not rely on chat
  history for changing rules. Disclose prior development and AI assistance honestly.
- Prepare a pitch no longer than 2 minutes and an at-most-3-minute product demo
  (the authenticated 2026-09-20 submission form is stricter than the public FAQ). A draft/script is
  not a recorded video. Clearly distinguish recorded and pending deliverables.
- Show why an agent developer would use Entrotter instead of a few Anvil scripts
  or an existing simulator. Benchmark the same task and conditions, not slogans.
- Create a concise pricing/market hypothesis and interview script. Three
  genuine target-user evaluations remain a future validation target; the owner
  deferred them on 2026-09-20, so they are not a current submission gate. Do not
  invent completed evaluations.
  Outreach requires explicit owner authorization. Formal submission has standing
  conditional authorization under the current owner policy; missing facts, terms,
  review or a closed portal may still prevent it.
- Prepare a submission index linking exact code, demo, reports, reproducibility
  instructions, measured evidence, genuine feedback and known limitations.

## Execution loop

Work in this order: inspect -> choose highest-value open gate -> implement -> test
-> independently review -> fix -> update evidence/status -> commit/PR -> next gate.
Use parallel subagents for independent repos when the installed Codex supports
it, with explicit ownership and shared versioned contracts. Prefer vertical slices
and useful contributor issues over multiplying repositories or abstractions.

Use STATUS.md as a durable checkpoint. For every completed claim, record its
command, environment, observed result, artifact/log and commit SHA where available.
Update a machine-readable release-gates.json as well. Keep real and mocked tests
separate. Clean up processes and temporary resources before switching work.

Do not run forever without progress. If a gate requires missing credentials,
network access, paid compute, human feedback or approval, mark BLOCKED with the
smallest precise unblock action. Continue all independent authorized work; do
not report the overall goal complete. On session/usage limits, save a checkpoint,
next command and remaining gates so a later session resumes rather than restarts.
Do not claim that a file or /goal removes rate limits or guarantees background
execution. Respect the user's stop/pause requests and preserve work safely.

## Definition of done

All engineering gates have actual passing evidence, Pages is verified live,
all repos are public and usable by outside contributors, the real-chain demo
works, and submission materials distinguish verified results from hypotheses.
These conditions define a demonstrated quality checkpoint, not termination of
the October 2 improvement goal. Before the official deadline, continue the most
valuable authorized improvement even after readiness or formal submission. At
the deadline, audit and report the actual state and remaining limits; do not
label unverified requirements complete or guarantee winning. Report blockers
precisely, preserve results and next commands, and continue independent work.
