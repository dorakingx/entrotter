# Offline schema contracts and scenario quality

The old result-schema test never supplied `agent`. A valid nested recording then
raised `Unresolvable: agent-recording.v0.1.schema.json` instead of validating.
Scenarios PR [#8](https://github.com/entrotter/scenarios/pull/8) fixes this with a
small standalone validator and a fully local registry of the three existing
v0.1 schemas. The failure is retained in `evidence/scenario-contracts/before.log`.
Issue [#34](https://github.com/entrotter/entrotter/issues/34) tracks this slice.

The helper follows jsonschema's documented [in-memory registry approach](https://python-jsonschema.readthedocs.io/en/stable/referencing/).
Schema URIs identify bundled resources; no HTTP/file retriever is configured.
Tests reject missing, HTTP and existing file-URI references and explicitly assert
that network and file-read mocks were never called. Other tests reject a missing
bundled schema and a malformed schema. Valid nested records pass; invalid choices,
extra executable fields, empty reasons and zero/33 exchanges fail at the nested
result path as well as in standalone recordings. Missing jsonschema now fails
imports. With `python -S`, the original seven-test suite passed with three schema
checks skipped; the updated suite fails instead. Both outputs are retained.

No schema, scenario, benchmark or manifest bytes changed. The catalog check now
includes `historical_scenarios` and compares the manifest to every fixture/EVM
input, rejecting missing, unlisted and duplicate entries. All five frozen cases
also pass JSON Schema validation alongside existing engine/source/split checks.
The preserved-input inventory contains exact before/after hashes.

## Scope and reproduction

From the proposed scenario checkout, follow its README to install the hash-locked
six-package schema lock. Run these commands with an actual sibling engine:

```bash
PYTHONPATH=../engine/src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m contract_validation --kind scenario fixtures/*.json evm/*.json benchmarks/causal-v1/cases/*.json
.venv/bin/python -m contract_validation --kind result ../entrotter/evidence/causal-v1/causal-uniswap-*.json ../entrotter/evidence/agent-local-*.json ../entrotter/evidence/historical-uniswap.json
```

Fourteen local tests pass separately against the frozen agent engine and proposed
bounded-worker engine on Python 3.13, without skips. Eleven scenario files and
19 existing public result envelopes pass; 12 contain agent recordings. The result
inputs come from coordination commit fcf27d69c20fff3eb31534434579aa62795cc786.
Exact source and result hashes are recorded in `evidence/scenario-contracts/`.
No Anvil, archive call, model call or Docker VM was needed for this verification.

Ruff lint/format, normal mypy with unannotated-body checking and an unsuppressed
Bandit scan cover all five tracked Python files, including four test files.
Bandit reports zero findings and errors. Hash-required binary-only installation,
`pip check` and strict advisory audits pass: all 48 quality-tool packages and all
six schema packages are checked, with no reported vulnerabilities or skipped
packages. The six are included in the 48; do not add the counts. No advisory IDs
or Bandit rules are excluded. The full reports are retained. CI pins Actions and
cross-repository sources and retains exact scanned source/schema/lock digests.

Linux verification also passed at scenario commit
`3a78ecca24334ae87119a5a0b64c84ba6dd71de1`:
[contracts](https://github.com/entrotter/scenarios/actions/runs/35474622711),
[quality](https://github.com/entrotter/scenarios/actions/runs/35474622690) and
[links](https://github.com/entrotter/scenarios/actions/runs/35474622683).
Each Python 3.11/3.12/3.13 engine-compatibility job passed 14 tests without skips;
the original-engine 3.12 job also validated all 19 recorded reports. Downloaded
CI source/schema/lock digests, complete advisory identities and link inputs match
local evidence. Tests overlap prior scenario suites; do not add them to the frozen
workspace total. `summary.json` hashes the complete retained evidence set.

## Limits and review

Wire shape does not authenticate a report or verify its content hash, exact causal
request binding, engine semantics, economic assumptions or financial correctness.
The unchanged result schema is an envelope: nested scenario/trace properties are
not fully constrained. The standalone command is a developer tool for intended
local files, not a resource-limited upload service. These checks do not claim a
new historical replay or another evaluation of previously used holdouts.

Normal typing and source/advisory scans do not prove security. The engine, website,
provider and other repositories retain their separate gates. The proposed scenario
change and its stacked base PRs require independent approval and merge. No branch
protection, frozen provider or evaluated input was altered. Overall submission
readiness remains incomplete.
