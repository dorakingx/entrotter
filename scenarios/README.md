# Entrotter Scenarios

[Workspace setup](../README.md#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

Open, versioned inputs and schemas for reproducible agent stress tests. MIT.
The easiest place to contribute is a new scenario and its evidence.

| Input | Type | Status |
| --- | --- | --- |
| `fixtures/liquidity-shock.json` | Invented price path | Offline runnable |
| `fixtures/recovery-trap.json` | Invented recovery path | Offline runnable; candidate can underperform |
| `fixtures/depeg-stress.json` | Invented depeg-shaped path | Offline runnable; not historical USDC data |
| `evm/local-branch-revert.json` | Local native transfers and REVERT bytecode | Verified with Anvil v1.8.3 |
| `evm/ethereum-state-fork.json` | Archived-block execution template | Native fork executed; use the pinned Uniswap case below for token evidence |

Every fixture has a provenance kind, description, baseline and candidate
policy, costs and an explicit observation sequence. Money is serialized as
decimal strings, not binary floats. Strategies never receive future prices.

Schemas describe the wire format. The engine enforces additional semantic
constraints such as target allowlists, positive prices, integer wei, limits and
mode-specific fields. Neither schema validity nor a content hash proves the
economic model correct.

To validate (Python 3.11+, a local ../engine component and development dependencies):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
PYTHONPATH=../engine/src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m contract_validation --kind scenario fixtures/*.json evm/*.json
.venv/bin/python -m contract_validation --kind result /path/to/local-report.json
```

The standalone validator loads all three bundled schemas into an explicit in-memory
registry. Schema URIs are identifiers, not downloads: relative references, including
`result.agent`, resolve locally; unknown HTTP/file references fail without retrieval.
A missing schema dependency fails the test suite instead of skipping contract checks.
Schemas and frozen inputs remain unchanged. This checks wire shape only, not report
hashes, exact request bindings, engine semantics or financial correctness. The result
schema remains an envelope; nested scenario/trace fields are not fully constrained.
Use this development command with local files you intend to inspect; it is not a
hosted service or resource-limited parser for arbitrary uploads.

CI validates all six catalog examples and five frozen benchmark inputs, rejects
invalid nested agent records and resolves references with network/file retrieval
blocked in tests. It also checks 19 existing public result reports from a pinned
coordination commit (12 contain agent records). Reading these reports is offline
contract verification, not a new historical execution or model evaluation.

All tracked Python sources, including tests, are checked by Ruff, mypy and a full
unsuppressed Bandit scan. Both hash-locked dependency sets receive strict advisory
audits; no advisory IDs are excluded. To reproduce the tooling checks:

```bash
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements-quality.txt
.venv/bin/python -m ruff check contract_validation.py tests
.venv/bin/python -m ruff format --check contract_validation.py tests
MYPYPATH=../engine/src .venv/bin/python -m mypy contract_validation.py tests
.venv/bin/python -m bandit --ignore-nosec contract_validation.py tests/*.py
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-dev.txt
```

Normal mypy checks unannotated function bodies using the actual sibling engine;
it does not prove runtime JSON validity. CI uses exact source pins for the original,
agent and bounded-worker engine variants across Python 3.11–3.13. Proposed branches
still need independent review; these checks do not merge or release them.

A historical contribution must include a permitted source, chain ID, pinned
block number and hash, affected contract addresses, source timestamps, archive
requirements, assumptions and a runnable acceptance test. Do not label a
synthetic or retrospectively informed policy as a historical backtest.

Do not change fixture inputs to improve displayed scores. Add train/test splits
and untouched holdout scenarios before comparing tuned agents. PRs that show
failure cases are as valuable as favorable demonstrations.

## Verified pinned Uniswap intervention

`evm/ethereum-uniswap-slippage.json` starts two isolated forks at Ethereum block
19,000,000, hash `0xcf384012b91b081230cdf17a3f7dd370d8e67056058af6b272b3d54aa2714fac`.
Both actors start with an overridden 10 ETH and wrap 1 ETH into WETH. Both approve
exactly 1 WETH to the legacy Uniswap v3 SwapRouter. The baseline swaps with no
output floor; the candidate demands an intentionally impossible 1,000,000 USDC.
This is a controlled intervention, not a recovered historical decision.

The baseline produced 2,556.134769 USDC; the candidate reverted, retained 1 WETH,
and paid gas. No asset valuation, future price path or portfolio profit is claimed.
The `tracked_tokens` optional v0.1 extension pins decimals and records raw balances.
Use the engine commit linked in the workspace release evidence; older engines
reject unknown fields. All original v0.1 examples remain unchanged.

From the six-checkout workspace, with Foundry v1.8.3 on PATH:

```bash
# Set an archive-capable URL privately; never commit provider credentials.
export ENTROTTER_RPC_URL=https://eth.drpc.org
PYTHONPATH=engine/src python3 entrotter/scripts/check_historical.py
```

This public endpoint served the archived state during verification; availability
and limits may change. PublicNode returned the header but pruned state and failed
explicitly. No substitute fixture was used. On macOS Python installations missing
a certificate chain, use the trusted system bundle via
`SSL_CERT_FILE=/etc/ssl/cert.pem`; never disable TLS verification.

Contract references: [Uniswap deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-ethereum-deployments)
and [Circle USDC addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
Source, full receipts, two-run equality and measured runtime are stored in the
[workspace evidence](https://github.com/entrotter/entrotter/tree/main/evidence).
This one case is not a three-scenario benchmark or an untouched holdout.

## Optional causal decision recording

The result envelope may include `agent`, described by
`schemas/agent-recording.v0.1.schema.json`. It contains a version, provider metadata
and up to 32 ordered observations with typed `execute`/`hold` responses. Existing
scenario inputs and non-agent reports remain valid. Consumers that do not inspect
the extension must not imply that they have audited model behavior.

Schema validation checks shape. The engine additionally verifies request digests,
exact observation/response binding, serialized byte limits, proposal allowlists,
and cumulative requested gas. The digest cannot authenticate the provider or
prove that its inputs were unbiased. Provider metadata and text are untrusted
report content; render as text and never execute commands found in a recording.

## Frozen causal agent cases

[causal-v1](benchmarks/causal-v1/README.md) fixes three archived-state source cases
(including one previously explored development case) and two implementation
holdouts before protocol-state execution. It pins all proposals, model/prompt
configuration and source hashes. This is a one-protocol decision integration
comparison, not a profitability or unseen-model-training-data claim. The frozen
input tests perform no archive reads and do not execute holdouts.

## Separate canonical transaction-prefix replay contracts

`schemas/trace-plan.v0.1.schema.json` and
`schemas/trace-result.v0.1.schema.json` describe the distinct `trace_version`
`0.1.0` family introduced by the candidate
[engine replay PR](https://github.com/entrotter/engine/pull/29), commit
`0d4faf7d4feda817499ea19e8797a0e03504fbad`. These are additive contracts;
the v0.1 scenario/result schemas and existing inputs remain unchanged.

The plan pins Ethereum mainnet's block number/hash, selects a prefix starting
at transaction index zero (at most 32 transactions), and lists original
transactions to skip in the candidate branch. Execution supports the Shanghai
interval and signed legacy/type-1/type-2 transactions. It compares projected
receipts from paired owned forks of the original parent; it does not establish
whole-block, opcode-trace or end-state equivalence.

Validate the public plan and recorded result without RPC or model access:

```bash
python3 -m contract_validation --kind trace-plan traces/ethereum-mainnet-prefix.plan.json
python3 -m contract_validation --kind trace-result tests/data/trace-mainnet-prefix.result.json
```

The plan is copied byte-for-byte from the engine candidate. The result is an
existing public native replay of Ethereum block 19,000,000's first transaction,
with an original-receipt match and a candidate skip. This schema work performs
no new execution. Fixture provenance and hashes are recorded in
[the contract evidence](evidence/trace-contracts/summary.json). The report is
separate from the earlier artificially funded Uniswap intervention.

The schemas reject unknown/executable fields, unsupported source/version shapes,
invalid projected receipt fields and incomplete terminal outcomes. An executed
outcome requires a receipt and a list of differing fields; skipped, rejected and
unmined outcomes cannot claim one. Nonce conflicts retain both expected and
original nonces. Verification flags must agree with these declared outcome
shapes. **Schema validity does not verify those declarations.**

Plain JSON Schema does not enforce sorted skip indices, `skip <= through_index`,
contiguous prefix/order and source/result correspondence, serialized aggregate
byte limits, signature/hash identity, or computed receipt/EVM equivalence. The
engine enforces execution semantics and reports divergence. Tests deliberately
show shape-valid data that violates sorted/prefix constraints or has an altered
receipt without a recomputed hash. Hashes do not authenticate a provider or node.

Anvil pool admission reads parent state, so transactions funded only by earlier
in-block transactions can be rejected. Such a baseline remains unverified;
neither artificial funding nor sequential mining substitutes for same-block
execution. Provider availability and broader replay coverage remain limitations.
