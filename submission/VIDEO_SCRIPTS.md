# Exact video narration and scene order

Synthetic narration; recorded review materials, not a founder impersonation.

## Pitch

### 1. ENTROTTER / EXPERIMENTAL 0.1

Before an onchain agent gets production permissions, its decisions need a reproducible test.

Entrotter lets a developer start from known blockchain state, change a decision, and keep a record another developer can inspect.

### 2. THE DEVELOPER PROBLEM

A passing simulation alone does not explain a decision. Which block did it use? Which balances were overridden? What information reached the policy?

Our hypothesis is that teams need these answers together, instead of scattered across scripts, terminal logs, and screenshots.

### 3. ONE REVIEWABLE EXPERIMENT

Entrotter runs baseline and candidate actions from identical initial state in separate Anvil instances. A constrained policy sees the current proposal, current state, and completed actions, not future steps.

It can hold, or execute the unchanged proposal. The report keeps source pins, receipts, token units, assumptions, and the recorded decisions.

### 4. MEASURED / OPEN REVIEW BRANCH

The current review branch reproduces all nineteen existing EVM reports as exactly equal complete artifacts, including twelve agent recordings, without calling a model again.

One hundred eighty nine native and unit tests, and twenty one real Docker tests, verify behavior and resource controls. All results and limitations are public.

### 5. WHAT THE EVIDENCE DOES NOT SAY

The model matched the deterministic risk rule in the five evaluated historical cases, and took longer. A same-task comparison also showed no speed advantage over a direct Anvil script.

The proposed value is a reusable, reviewable experiment and replay record. It is not a claim of smarter trading, future prediction, or profit.

### 6. INITIAL USER / HYPOTHESIS

The initial audience is small EVM agent teams that already write simulation scripts and need a teammate to reproduce a questionable decision.

The first validation target is three genuine developer sessions: run their own case, reproduce a colleague's result, and identify what would make this workflow useful. Those sessions have not happened yet.

### 7. BUSINESS / UNVALIDATED

The local engine and viewer are MIT licensed. A business hypothesis is paid team collaboration around shared scenarios and reviews, while local execution stays open source.

Ninety nine dollars per team per month is an interview anchor, not a live offer or validated willingness to pay. There are no verified customer or revenue claims.

### 8. TRY THE EVIDENCE

Start with the public example, inspect the assumptions, then bring one decision you need to explain. The site and six repositories provide the code and measured evidence.

The bounded agent integration still needs independent review. Team details and demand validation remain pending. This presentation uses synthetic narration and discloses Codex assisted development.

## Demo

### 1. 01 / THE REAL VIEWER

This is Entrotter, a local test bench for onchain agent decisions. The recording uses the actual report viewer and the bounded engine review branch.

The narration is synthetic. The browser interactions and process outputs are real; no wallet or production signing key is used.

### 2. 02 / AN ADVERSE OUTCOME

Choose the Ethereum and Uniswap example. Both branches start at the same pinned historical state, with explicitly artificial funding.

The baseline swap succeeds. The changed minimum output makes the candidate transaction revert. Native and token balance changes are exact units, not a claim of profit.

### 3. 03 / INSPECT THE ASSUMPTIONS

The source section records Ethereum block nineteen million and its hash. The receipts show which supplied actions succeeded or reverted, and their gas use.

These are actions re-executed against archived state. The experiment does not reconstruct later market behavior, transaction ordering, or future prices.

### 4. 04 / ACTUAL BOUNDED EXECUTION

Now the recording console starts real Python calls to the configured Docker worker. First, the built-in risk policy evaluates a local transfer and a reverting proposal.

Then it replays the previously recorded model decisions against fresh observations. The complete result must match the original artifact, or the command fails.

### 5. 05 / AN EXACT REPLAY

The risk policy executes the transfer and holds the reverting proposal. The recorded model replay produces the original content identifier, with complete JSON equality.

No model is called during this replay. The worker uses one CPU, five hundred twelve mebibytes of memory, and an independent lifetime limit. Native custom providers are a separate, unsandboxed path.

### 6. 06 / OPEN THE GENERATED RESULT

Open the result that the command just generated. The viewer shows the baseline revert and the candidate hold from that exact local experiment.

The source JSON preserves the recorded observations, typed choices, provider metadata and assumptions. A content hash detects changed content; it does not establish that a model is correct.

### 7. 07 / REJECT ALTERED CONTENT

Here is the same report with a deliberately incorrect content hash. The viewer rejects it and clears the previous result.

Loading the original generated report recovers normally. Local imports stay in this browser; the recording checks that no upload or third-party request occurs.

### 8. 08 / REPRODUCE AND REVIEW

The broader check reproduced nineteen existing reports, including twelve agent records. The evaluated model matched the risk rule; no model advantage is claimed.

Use the public code and evidence to reproduce a case of your own. This integration is an open review branch, not a claim of a merged release or a finished competition submission.
