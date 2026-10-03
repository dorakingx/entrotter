# Entrotter submission index

**Saved project draft, not a submitted entry.** The owner approved the existing
videos and supplied the solo-participant facts on 2026-09-20. User evaluation is
deferred, with zero completed sessions. The authenticated event account now has
an [Entrotter draft](https://colosseum.com/arena/projects/entrotter); product details
are saved. Final submission opens October 6 at 11:00 UTC / 20:00 JST. Formal
post-submission editing is not yet verified. The owner now authorizes formal
submission once quality conditions and required personal facts are verified and
the portal is open, without another blanket approval. No outreach or final entry
was sent. Independent review, authentication and terms must still be respected.

## Product

**Entrotter — a local test bench for onchain agent decisions.** Start from a known
blockchain state, change one decision, and retain an experiment another developer
can inspect and reproduce. The initial audience hypothesis is small EVM agent
teams already maintaining their own simulation scripts.

The engine runs paired local Anvil branches or forks pinned historical state.
Versioned reports record assumptions, source pins, overrides, receipts, native and
ERC-20 units, constrained agent observations/actions and replay records. A static
viewer imports reports locally in the browser. No signing key or mainnet write is
required. Archived-state action execution is not historical transaction replay,
a prediction of future markets, or a measurement of profit.

## Submission materials

| Material | Artifact | Status |
| --- | --- | --- |
| Exact CLI inspection demo | [MP4](media/entrotter-demo-cli.mp4), [VTT](media/entrotter-demo-cli.vtt), [SRT](media/entrotter-demo-cli.srt) · 2:36.80 | Additional edited cut: real current CLI price/account text and complete0/synthetic incomplete3 script exits; preserves October 3 footage, soundtrack, captions and all prior media |
| Updated account-impact demo | [MP4](media/entrotter-demo-account.mp4), [VTT](media/entrotter-demo-account.vtt), [SRT](media/entrotter-demo-account.srt) · 2:36.80 | Additional current-viewer cut: two fresh bounded local calls, recorded account 13/card/receipt inspection, lossless bad-ID rejection and recovery; original owner-approved cut retained |
| Product demo | [MP4](media/entrotter-demo.mp4), [VTT](media/entrotter-demo.vtt), [SRT](media/entrotter-demo.srt) · 2:54.24 | Recorded actual Chromium interactions and bounded engine calls; owner approved |
| Product pitch | [Short MP4](media/entrotter-pitch-short.mp4), [VTT](media/entrotter-pitch-short.vtt) · 1:46.07 | New six-card pitch with confirmed solo-founder context; synthetic narration. The original 2:51.44 review cut is retained but exceeds the current form limit |
| Video production evidence | [Manifest](../evidence/submission-media/manifest.json) | Source pins, exact scripts/timelines, output hashes, execution and rendering checks |
| Pitch text and shot list | [Video scripts](VIDEO_SCRIPTS.md) | Exact narration, including hypotheses and limitations |
| Market/pricing/distribution | [Market hypotheses](MARKET.md) | Unvalidated, no fabricated TAM/customer/revenue claim |
| Target-user evaluation | [Evaluation protocol](EVALUATIONS.md) | Deferred by owner; zero completed records, no demand claim |
| Development/AI disclosure | [Disclosure](DISCLOSURE.md) | Supplied archive and substantial Codex assistance disclosed; owner reports event-period AI generation; original archive digest unavailable |
| Rules, deadline and eligibility | [Competition requirements](../docs/COMPETITION.md) | Public requirements rechecked; authenticated event draft verified; owner confirms eligibility |

The [account-impact recording evidence](../evidence/submission-account-demo/README.md)
binds viewer8aa0/Engine88c6 and the exact generated local report. The
[October 4 CLI edit](../evidence/submission-cli-demo/README.md) inserts actual
CLI24bbb91/SDKba4af51 offline outputs into three picture intervals; original
viewer footage and its earlier EVM calls are reused, not executed again.
Both additional cuts await human auditory review and supported-host delivery.
The [15 narration cues](../evidence/submission-account-demo/timeline.json), audio
packets and caption bytes remain unchanged in the CLI edit.

The original recordings label synthetic narration and their historical review
status; the owner has since approved them. The short pitch retains explicit
synthetic-narration disclosure and does not impersonate the founder. The
demo uses actual product UI, a clearly labelled recording console displaying real
process output, and generated report files. It does not stage successful output,
claim to be the founder speaking, or present the recording console as a product
feature. The pitch does not establish founder communication skills or market fit. No video platform has received an upload.

## Latest candidate sources

The October 4 candidate provides bounded local agent replay, supplied Aave
collateral/variable-borrow action comparison, exact recorded price/account
inspection and script completeness gates. Use the
[current pinned quick start](../docs/QUICK_START.md) to reproduce it.
`observed-inspect --format text` and `position-inspect --format text` retain exact
units; `--require-complete` on either verifier returns3 for valid but unproven
views or baseline receipts. Default JSON remains unchanged. This is inspection
of recorded evidence, not proof of profit, provider authenticity, a signed
consumer strategy or the full block's state.

| Component | Exact source | Candidate PR |
| --- | --- | --- |
| Last independently audited coordinator snapshot before the action composition | [d871e27](https://github.com/entrotter/entrotter/tree/d871e270c13285c249f66056f8e8b4ff37097049) | [#55](https://github.com/entrotter/entrotter/pull/55) |
| Bounded agent engine, Aave supply/variable borrow and historical price/account observations | [f53a66a](https://github.com/entrotter/engine/tree/f53a66a303e67ca4fbb4322a06b36b036f4db599) | [#35](https://github.com/entrotter/engine/pull/35) |
| Python SDK with offline typed signed-prefix and price/account observation inspection | [ba4af51](https://github.com/entrotter/sdk-python/tree/ba4af512784119f23b6dea63fd24c7f5d1fdde44) | [#7](https://github.com/entrotter/sdk-python/pull/7) |
| CLI with bounded replay, exact account/price text and completeness exits | [24bbb91](https://github.com/entrotter/cli/tree/24bbb916555ef18528300f995e127d50ff29167e) | [#10](https://github.com/entrotter/cli/pull/10) |
| Scenario/result and separate trace contracts | [8785bb0](https://github.com/entrotter/scenarios/tree/8785bb090c13390b783fe8c42f01b26f1d5e7c24) | [#11](https://github.com/entrotter/scenarios/pull/11) |
| Console, local source selection, recorded agent and Aave account inspection | [422d98a](https://github.com/entrotter/entrotter.github.io/tree/422d98a7cf753bfc9be9b86553cd76f3a549f70c) | [#16](https://github.com/entrotter/entrotter.github.io/pull/16) |

All five mandatory coordinator checks atd871e27 and all six CLI checks at24bbb91
passed their original attempts, with independent raw-artifact/source review.
The [price text composition](../evidence/observed-text-integration/README.md)
and [account/completeness composition](../evidence/require-complete-integration/README.md)
retain the exact commands, full outputs and scope. The [Aave action composition](../evidence/aave-action-integration/README.md)
selects Enginef53 and adds one offline Engine/CLI/SDK reader. All eight Engine
checks are successful, with isolated passing on attempt2 after an initial old
account-case failure of unknown cause; the new real-action output matches the
original report completely. Current coordinator CI remains a separate checkpoint
in [candidate PR55](https://github.com/entrotter/entrotter/pull/55). Runtime tooling,
locks, frozen inputs and previous videos keep their original versions.
Independent human approval and protected main/Pages integration remain pending.

Recordings preserve their actual sources: original September review cuts use the
versions listed below, the October 3 account cut uses viewer8aa0/CLI6965, and the
October 4 picture edit adds CLI24bbb91 outputs to that existing footage. The
current candidate viewer422d has its own browser/CI evidence; it was not used to
recapture the October 4 footage. Packages and images remain unpublished to
registries. Historical execution, archived provider, funding and adverse-case
records retain their own source pins and limitations in
[project status](../STATUS.md); later success does not explain earlier failures.

## Recorded review sources

| Component | Source | Review state |
| --- | --- | --- |
| Bounded causal-agent engine | [engine abb4662](https://github.com/entrotter/engine/tree/abb4662ce960e08b2aa3a2c8a1c10719339edccc) | [PR #21](https://github.com/entrotter/engine/pull/21), stacked prerequisites pending independent review |
| Viewer used in recording | [website 6174031](https://github.com/entrotter/entrotter.github.io/tree/61740312f281f7e911e0eb6e9482a3c372cb1fae) | [PR #11](https://github.com/entrotter/entrotter.github.io/pull/11), not deployed |
| Frozen evaluation implementation | [engine bb8b3e8](https://github.com/entrotter/engine/tree/bb8b3e8d32c7cbd49629d337758f30bfdf805045) | Original benchmark/source boundary retained |
| Frozen scenarios | [scenarios 5b71898](https://github.com/entrotter/scenarios/tree/5b718984ac67b8fb49e02f4dab676ae212d2aa58) | Original cases and evaluated holdouts unchanged |
| Reproduction evidence | [coordination 67b7d19](https://github.com/entrotter/entrotter/tree/67b7d19105495e314c308cd7e2e01ef254f37ca1) | [PR #39](https://github.com/entrotter/entrotter/pull/39), independent review pending |
| Public site | [entrotter.github.io](https://entrotter.github.io/) | Live current main console, distinct from the recording and unmerged accessibility/quality candidate |

Six public repositories: [coordination](https://github.com/entrotter/entrotter),
[engine](https://github.com/entrotter/engine), [SDK](https://github.com/entrotter/sdk-python),
[CLI](https://github.com/entrotter/cli), [scenarios](https://github.com/entrotter/scenarios),
and [viewer](https://github.com/entrotter/entrotter.github.io). Original project
code is MIT licensed. Packages and worker images are not published to registries.

## Evidence and differentiation

[Bounded reproduction](../docs/BOUNDED_AGENT_REPLAY.md) matched all 19 original
complete EVM reports, including 12 agent recordings, with no new agent-model call.
The October 3 account recording performs an additional real local risk run and
frozen-model replay. The October 4 CLI edit reuses those recorded calls and adds
only offline inspection and an explicitly synthetic incomplete-record control.
This proves a reproducible observation/action contract, not a better model.
[Fresh public bounded replay](../docs/BOUNDED_AGENT_INTEGRATION.md) now provides
a single measured checkout/build/replay/CLI-verification command, with Docker
setup prerequisites and exact current proposed pins.
[Historical evaluation](../docs/HISTORICAL_AGENT_EVALUATION.md) includes three
sourced cases plus two pre-frozen holdouts; those holdouts are now consumed. The
model matched the risk rule and was slower in every evaluated case.

[Direct Anvil comparison](../docs/DIRECT_ANVIL_COMPARISON.md) produced identical
common outcomes in six runs, with medians of 8.653 seconds for the bespoke script
and 8.689 for Entrotter. No speed or developer-productivity advantage is proven.
The proposed difference is reusable scenario validation, recorded causal decisions,
exact replay and a shareable report/inspection workflow. A few Anvil scripts may
be the right solution for a single bespoke experiment. Actual willingness to adopt
or pay for the broader workflow is still a hypothesis.

## Owner decisions and remaining submission requirements

- Doraking is the sole member; eligibility confirmed and no funding reported.
- The owner reports no Entrotter development before September 14, 2026, and
  event-period AI generation of the initial code and purple mascot.
- Education and previous employment are not disclosed. The mandatory current
  school-status field only offers Yes/No, so it remains unanswered.
- Existing videos are approved. The form requires a pitch of at most two minutes
  and a demo of at most three minutes, hosted on YouTube, Loom or Vimeo. The new
  short pitch passes a full decode/duration check; hosting is still pending.
- The October 1 authenticated draft shows the uploaded project logo
  `icon_trasparent_v2.png` (139 KB). Two supported video URLs are still missing.
  This supersedes the September 20 failed upload attempt.
- The saved required city needs owner verification; do not infer personal facts.
- User evaluations are deferred and are not a current owner-required gate.
- Independent GitHub approval and protected main/Pages integration remain open.
- Formal submission is authorized when the quality conditions and required facts
  are verified and the portal is open. The form confirms editable drafts before
  opening; post-submission editing remains unverified.

See the [October 1 authenticated draft readback](../evidence/submission-preparation/oct01-checkpoint.json)
and [original preparation evidence](../evidence/submission-preparation/summary.json).

The material is not a claim of a win, market validation or complete goal acceptance.


The historical [Aave price observation composition](../evidence/consumer-price-integration/README.md)
selected enginebd5527f and retained all other pins and recordings. Its actual
native006 original32/skip12 replay verifies full projected baseline receipts and
4 owned consumer view phases: baseline257082415000→256292441874, candidate
keeps257082415000. All8 component checks/complete raw artifacts and all5 local
SDK/Node22 reader steps pass. Subsequent9b49fe2 combined CI passed all5 original
mandatory checks and full raw review; that verified composition is historical.
Protected-main approval and live candidate Pages remain separate gates. These read-only observations
are distinct from signed consumer transactions, strategy/profit, full-block/root
or provider authenticity. Standard trace-run has no extra-view option at this
selected head; supported CLI work is separate. No new submission is claimed.


The [direct price-wrapper composition](../evidence/direct-observed-wrapper-integration/README.md)
selects engine40bea57/PR35 and viewera19d3b1/PR16. The engine's all8 and viewer's
all4 original mandatory checks and full raw independent reviews pass. The viewer
now accepts the original sealed wrapper directly, displaying four price phases
beside all32 receipt comparisons. The sixth mandatory integration case compares
its complete nested report, classification and raw price/address/unit/head/code
records with the engine validator; all6 exact local scripts pass, and prior5
complete outcomes remain unchanged except the viewer pin.

The prior coordinator213 composition passed all5 original checks and full raw
review. Its subsequent direct-wrapper composition d90f4a9 also passed all5
original checks and full independent raw review (workspace37049503304,
quality37049503150, docs37049503339). These are historical verified compositions;
the current SDKeb candidate's combined CI is recorded separately below. The
coordination execution snapshot row retains older verified source. Protected-main
human approval and Pages remain separate. Videos/model/holdouts and the
application draft are unchanged; no formal submission is claimed. Read-only prices establish no signed consumer
strategy, profit, provider authenticity or full-block/root/opcode result.


The [standalone SDK wrapper composition](../evidence/sdk-observed-integration/README.md)
selects SDKeb9921f, whose all5 original mandatory checks and complete raw review
pass. Python developers can inspect the supported original wrapper directly,
without importing the engine or creating an intermediate trace export. The sixth
mandatory reader compares the complete SDK snapshot, typed classification and
four full typed price/feed/address/unit/head/code/error records with engine40 and
viewera19. Its subsequent coordinator4b037fe passed all5 original required
checks and full independent raw review (workspace37096639467,
quality37096639463, docs37096639482; reviewSHA3d13d25613e0b6cee85ea8e305f65b78ccd7a79ded03b4fc708d8aa3cf7632ea).
That historical verified source selects CLI22; the newer CLI composition below
has a separate current-head CI gate. Human protected-main approval remains separate. Frozen recordings, model/holdouts and
submission draft remain unchanged; no new chain/model/browser or submission claim.


The [terminal price-wrapper composition](../evidence/cli-observed-integration/README.md)
selects CLI1ee3d3a, whose all6 original required checks and full raw independent
review pass. Developers can run observed-verify/observed-inspect without custom
Python or engine conversion. The sixth exact workflow reader runs both commands
and compares complete JSON classification, trace IDs/count and all four typed
records with the reviewed SDK/engine/viewer facts. First5 exact scripts and full
outcomes stay unchanged except the selected CLI pin. New combined candidate CI,
protected-main approval and Pages remain separate; no new chain/model/browser
execution or submission is claimed.


The [CLI execution composition](../evidence/cli-observed-run-integration/README.md)
selects d437ad1 after all six original mandatory checks and full raw independent
review pass. The guide now runs the fixed observation through the CLI, with
admitted-plan binding, quota export and cancellation. All seven unchanged offline
reader scripts preserve their complete outcome facts; only selected CLI and its
exact source hash change. The coordinator table identifies the last audited
execution snapshot, not this new selector update's combined CI. New combined CI,
human main approval, Pages and formal submission remain separate. Frozen media,
model/holdouts, timed walkthroughs and the unsubmitted draft are unchanged.


The historical [account inspection composition](../evidence/account-impact-integration/README.md)
at root670e selected Engine88c6, SDKba4 and CLI6965 after each component's full
required CI/raw review. All five root670e checks and full raw review SHA6753979f
subsequently passed. At that checkpoint the selected viewera19 did not support
account wrappers; the new viewer composition below adds that display coupling.
The recorded13-input case retains all4 views and exact deltas, not profit or a
signed strategy. The prior CLI c04d baseline-unverified failure remains documented
with unknown cause; later passing CI does not establish that cause. Human main
approval, Pages and formal submission remain separate. Frozen model, holdout and
media sources stay unchanged.


The proposed [account viewer composition](../evidence/viewer-position-integration/README.md)
selects viewer4c6e after all four original mandatory checks and full raw independent
review pass. The ninth offline reader compares the original13 wrapper and nine
explicit synthetic controls with full SDK/Node classification, four typed/raw
phases, plan, three seals and nested trace facts. The earlier eight readers retain
all executable assertions; only the eighth's now-stale display-limit sentence is
updated. Historical facts remain unchanged except the selected viewer pin and
that scope text. Component browser verification remains separate from new combined
CI, human protected-main approval and live Pages. No new chain/model/user run.


The subsequent root2e05 SDK-to-browser composition passed all5 original checks
and full independent raw review6868f253. The next
[account summary composition](../evidence/account-summary-integration/README.md)
selects viewer8aa0 after all4 current mandatory checks and full original raw
reviewd54be9be. Its two exact changes precede the address and wide table, with
accessible mobile stacking and explicit null/no-debt/sign handling. Existing
nine reader bodies, complete recorded outputs and frozen sources remain exact
apart from the selected viewer pin. New combined rootCI and human protected-main
approval remain separate from component CI. Existing approved recordings retain
their original source versions; this new UI is not yet in those recordings.
No fresh chain/model/user evaluation, deployment or formal submission is claimed.
