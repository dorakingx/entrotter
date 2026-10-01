# Recorded causal agent evaluation

This is a verified integration slice, not a completed historical agent benchmark.
The local test uses invented balances, a native transfer and a tiny reverting
contract on actual disposable Anvil processes. It contains no market data.

## Measured local comparison

Every policy receives the same two proposals and identical initial state. The
non-agent case executes both. The risk policy and model are given the same
execute-if-preflight-succeeds objective, so this test measures integration and
cost of obtaining decisions; it does not establish an advantage for an LLM.

| Policy | Decisions | Reverted transactions | Gas used | Paired run wall time |
| --- | --- | --- | --- | --- |
| Non-agent | Execute, execute | 1 | 42,006 | 0.318 s |
| Deterministic risk | Execute, hold | 0 | 21,000 | 0.313 s |
| Codex model | Execute, hold | 0 | 21,000 | 8.721 s |

Both recorded policy runs reproduced the entire artifact exactly. Model replay
took 0.326 seconds and made no model call. These are single-run measurements,
not statistical estimates. The model did not outperform the simpler rule in this
case and took substantially longer. No future price series or portfolio valuation
is available; drawdown and profit are undefined, not zero.

The model was requested as `gpt-5.6-sol`, reasoning effort low, using operator-
authenticated `codex-cli 0.145.0`. The CLI does not expose an immutable served
snapshot, sampling seed or monetary bill. These remain explicitly unavailable.
Two completed calls reported 9,967 input tokens and 162 output tokens, with zero
observed CLI tool calls. This is recorded usage, not a fabricated dollar estimate.
The earlier connection attempt with `gpt-5.4-mini` was rejected as unsupported
for this ChatGPT account; it produced no benchmark decision. The adapter was then
explicitly configured with the supported model, without fallback inside a run.

Full current observations, typed decisions, prompt/version, provider metadata,
usage and receipt/gas evidence are in `evidence/agent-local-codex.json`.
`evidence/agent-model-verification.json` records runtime and child-resource scope.
The content hash detects changes; it does not authenticate the provider or prove
that the policy was uninformed by hindsight. The local fixture was used during
development and is not a holdout.

## Reproduce without model generation

Use the dependency commits in `dependency-pins.json`. The engine and schema
changes currently await independent approval in engine PR #8 and scenarios PR #5;
these pins identify the tested proposed changes, not an approved release.
From the six-checkout workspace with Foundry v1.8.3 on PATH:

```bash
PYTHONPATH=engine/src python3 entrotter/scripts/check_agent.py --replay entrotter/evidence/agent-local-codex.json
python3 entrotter/scripts/reproduce_clean.py --agent
```

The second command clones five public dependencies into a temporary workspace,
creates a fresh venv without pip/system site packages, replays the recorded model
responses, verifies and inspects the report via the CLI, and compares the complete
artifact. The coordination checkout and recorded evidence must already be present.
It does not invoke Codex, need account authentication or contact a model provider.

New model generation is an explicit local operator action and consumes account
usage. It is excluded from CI and from the replay command:

```bash
PYTHONPATH=engine/src python3 entrotter/scripts/check_agent.py --generate-model --model gpt-5.6-sol
```

The installed trusted CLI must be version 0.145.0 and already authenticated. On
this macOS Python installation, set `SSL_CERT_FILE=/etc/ssl/cert.pem` if needed.
The model name is an alias and availability can change. New generation may choose
different reasons or actions and produce a different artifact; it is not claimed
to be deterministic.

## Boundaries and remaining work

The adapter invokes a fixed installed CLI without a shell in an empty temporary
working directory. It ignores user configuration, sets the project document byte
limit to zero, disables web search and the listed execution/plugin/app/browser
features, and uses a read-only CLI sandbox. The response must be one typed final
message with one completed usage record; unexpected tool/error events fail the
run. Per-decision time is capped at 50 seconds and stdout at 128 KiB. Timeout,
oversized output, failure and cancellation reap the owned subprocess group.
Only a small environment allowlist is forwarded; RPC URLs and engine tokens are
excluded. Stderr is discarded to avoid publishing authentication diagnostics.

This adapter is for trusted local operators. A CLI subprocess is not a general
sandbox for untrusted agent code, and rejection of a tool event occurs after that
event. There is no independent egress firewall or hard whole-process CPU/RSS/disk
quota. Arbitrary downloaded code execution and HTTP-selected providers remain
disabled. The current-state preflight can differ from the next execution block.

The subsequent [historical comparison](HISTORICAL_AGENT_EVALUATION.md) completed
three sourced cases and two pre-frozen implementation holdouts with exact replay.
The [same-task direct Anvil comparison](DIRECT_ANVIL_COMPARISON.md) is now measured; broader resource controls remain open.
Results retain adverse outcomes and make no claims of future-profit prediction
or model superiority.
