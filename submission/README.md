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
| Product demo | [MP4](media/entrotter-demo.mp4), [VTT](media/entrotter-demo.vtt), [SRT](media/entrotter-demo.srt) · 2:54.24 | Recorded actual Chromium interactions and bounded engine calls; owner approved |
| Product pitch | [Short MP4](media/entrotter-pitch-short.mp4), [VTT](media/entrotter-pitch-short.vtt) · 1:46.07 | New six-card pitch with confirmed solo-founder context; synthetic narration. The original 2:51.44 review cut is retained but exceeds the current form limit |
| Video production evidence | [Manifest](../evidence/submission-media/manifest.json) | Source pins, exact scripts/timelines, output hashes, execution and rendering checks |
| Pitch text and shot list | [Video scripts](VIDEO_SCRIPTS.md) | Exact narration, including hypotheses and limitations |
| Market/pricing/distribution | [Market hypotheses](MARKET.md) | Unvalidated, no fabricated TAM/customer/revenue claim |
| Target-user evaluation | [Evaluation protocol](EVALUATIONS.md) | Deferred by owner; zero completed records, no demand claim |
| Development/AI disclosure | [Disclosure](DISCLOSURE.md) | Supplied archive and substantial Codex assistance disclosed; owner reports event-period AI generation; original archive digest unavailable |
| Rules, deadline and eligibility | [Competition requirements](../docs/COMPETITION.md) | Public requirements rechecked; authenticated event draft verified; owner confirms eligibility |

The original recordings label synthetic narration and their historical review
status; the owner has since approved them. The short pitch retains explicit
synthetic-narration disclosure and does not impersonate the founder. The
demo uses actual product UI, a clearly labelled recording console displaying real
process output, and generated report files. It does not stage successful output,
claim to be the founder speaking, or present the recording console as a product
feature. The pitch does not establish founder communication skills or market fit. No video platform has received an upload.

## Latest candidate sources

These are the October 2 candidate sources, still awaiting independent approval
and protected integration. Follow the [current pinned quick start](../docs/QUICK_START.md)
instead of rebuilding from moving main branches. The recordings below retain
their original source versions.

The execution snapshot below contains the optional bounded Linux CLI launcher,
the canonical contract identity fix and original signed transaction-prefix replay.
The [prior four-prefix receipt evidence](../evidence/canonical-mine-integration/summary.json)
binds its original engine817/schema sources, receipt match and exact inputs.
The prefix is a separate technical case. The new
[funding composition](../evidence/trace-funding-integration/README.md) verifies
native synthetic same-block funding and an adverse omission without state repair.
The [oracle/provider composition](../evidence/trace-oracle-integration/README.md)
adds native signed update/consumer causal proof and actual read-only fault/control
coverage, including an integrity-valid unverified storage-failure report. Archived
funding/oracle, provider authenticity and full-block/end-state remain open. The
[recorded-agent viewer evidence](../evidence/agent-viewer-integration/summary.json)
adds original decision/provenance inspection and preserves original reports. Current
combined checks and public reproduction measurements are recorded in
[candidate PR55](https://github.com/entrotter/entrotter/pull/55). Prior walkthroughs
retain their actual older pins. Guide and evidence updates occur in later
documentation commits with the same production tools; this snapshot is proposed
code, not an independently approved release.

| Component | Exact source | Candidate PR |
| --- | --- | --- |
| Coordination execution snapshot, dependency pins and Linux CLI helper | [e46b392](https://github.com/entrotter/entrotter/tree/e46b392a4047bd680e5c03feb6bdc1a05a02269b) | Current composition builds on [#54](https://github.com/entrotter/entrotter/pull/54) |
| Bounded agent engine, contract identity and signed transaction-prefix replay | [99fd3a6](https://github.com/entrotter/engine/tree/99fd3a60a754f129c78d1324f2a01787a6538917) | [#32](https://github.com/entrotter/engine/pull/32) |
| Python SDK with offline typed signed-prefix inspection | [ee5523d](https://github.com/entrotter/sdk-python/tree/ee5523ded16488af32d1f64040f1996cd002f8f3) | [#7](https://github.com/entrotter/sdk-python/pull/7) |
| CLI | [22b514c](https://github.com/entrotter/cli/tree/22b514cbba2ecd0c41ae99c330f8396c97acebf2) | [#10](https://github.com/entrotter/cli/pull/10) |
| Scenario/result and separate trace contracts | [8785bb0](https://github.com/entrotter/scenarios/tree/8785bb090c13390b783fe8c42f01b26f1d5e7c24) | [#11](https://github.com/entrotter/scenarios/pull/11) |
| Console, recorded agent and signed-prefix inspection, accessibility and quality | [b7c20ce](https://github.com/entrotter/entrotter.github.io/tree/b7c20ce2c080427fe0742a1afcb5dbc49277de70) | [#15](https://github.com/entrotter/entrotter.github.io/pull/15) |

The [signed-prefix reader composition](../evidence/trace-reader-integration/README.md)
adds SDK and browser inspection of the actual four-receipt case. SDK all5checks
and viewer all4checks pass; root artifact verification confirms33Linux browser
groups/25raw axe scans without reported violations. Checksums and internal
relationships do not authenticate source state or prove economic/EVM truth.
The previous8029/a253 funding composition passed all five combined checks and55
document hashes, with complete API/CLI/export and both offline reader proofs. The
new oracle/provider composition requires its own exact-head CI. No new
video/model/holdout result is implied.

The earlier diagnostic successor [engineaac525c](https://github.com/entrotter/engine/tree/aac525c8279005a3a8468fe3928e691c3ce80148)
has seven successful checks but a failed four-prefix candidate gate: all original
receipts match, while one changed-branch transaction lacks a receipt. A later
diagnostic succeeds and does not establish the first failure's cause. The
[partial proof](../evidence/trace-oracle-integration/diagnostic-ci-partial.json)
keeps those outcomes separate. The current engine99fd passes all eight checks
on its first attempt, including normal default1/4 and image/native advisory gates.
[Independent full proof](../evidence/trace-oracle-integration/root-engine-full-CI.json)
binds those raw reports and audits. Its conditional observation diagnostic was
skipped, so the original failure cause remains unknown. Current coordinatione46
in the table is reviewed but unpublished; combined CI remains a separate gate.
The latest fully tested public composition remains8029/a253 with engine935.


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
The new demo performs an additional real local risk run and frozen-model replay.
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
