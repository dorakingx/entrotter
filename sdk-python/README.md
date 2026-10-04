# Entrotter Python SDK

[Workspace setup](https://github.com/entrotter/entrotter#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

A Python 3.11+ standard-library client for the Entrotter local API. MIT licensed.
No API credential or chain access is needed for the unit tests.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```python
import json
from entrotter_sdk import Client, ClientError, verify

client = Client("http://127.0.0.1:8787")
print(client.health())
with open("scenario.json") as f:
    result = client.run(json.load(f))
assert verify(result.report)
assert client.get(result.artifact_id).artifact_id == result.artifact_id
```

The client verifies content hashes, refuses plaintext non-loopback URLs,
rejects URLs with embedded credentials, disables redirects, limits response
size and never automatically retries an experiment POST. Use `token=` when
ENTROTTER_API_TOKEN is configured on the engine. The SDK supports HTTPS for a
future properly secured service, but no such public service is currently shipped.

This package has not been published on PyPI. Install this source checkout with
`python3 -m pip install --no-deps -e .` or use the workspace bootstrap. Do not
install a similarly named registry package. Integrity does not establish
model correctness or financial safety.

## Read original transaction-prefix reports offline

The separate `trace_version: "0.1.0"` family from the engine's `trace-run`
command has an offline reader. It does not use the `/v1/runs` HTTP endpoint or
change v0.1 action/model-record results. No chain access or model call occurs:

```python
from entrotter_sdk import load_trace

replay = load_trace("transaction-replay.json")
print(replay.artifact_id, replay.baseline_verified)
for tx in replay.transactions:
    print(tx.index, tx.candidate.status, tx.candidate.differing_fields)
    if tx.candidate.status == "nonce_conflict":
        print(tx.candidate.original_nonce, tx.candidate.expected_nonce)
```

`TraceResult.parse(value)` accepts an in-memory report; `verify_trace(value)`
returns a boolean instead of raising `ClientError`. Typed transactions/outcomes,
receipts and ordered logs are immutable. `result.report` returns a fresh JSON
copy, so later caller mutations cannot alter the validated snapshot. The file
reader accepts only regular JSON files up to 8 MiB and rejects duplicate object
keys. It uses nonblocking open where available to refuse special files.

Validation covers exact versions/shapes, SHA-256 content integrity, bounded
prefix/raw inputs/logs, plan/source/parent/index binding and canonical RLP metadata
for original legacy/type-1/type-2 signatures. It binds type/nonce/target and typed
or protected-legacy chain fields to encoded metadata. Unprotected legacy v27/v28
is supported as in the engine; those bytes contain no chain ID. It does not recover
the sender, verify a signature
or recomputing the Ethereum transaction hash. Receipt identities and cumulative
gas/index order, signed gas ceilings, reverted log/bloom absence and contract
address consistency are checked. Access lists have at most 256 total storage
keys. Declared `differing_fields` must be the exact unique
set of observed receipt differences, and match flags must agree with outcomes.
Both branches use the same reported initial nonce anchors; accepted-but-unmined
transactions advance their branch's queue nonce, while rejection/omission does
not. An honestly unmatched/rejected baseline remains readable with its false flag.

These checks establish internal consistency, not trusted source state, actual
execution or oracle/market truth. `baseline_verified` is the engine's declared
receipt-match result, checked against the embedded original receipts; it is not
independently rerun by the SDK. Parent nonce anchors are inferred from reported
baseline outcomes, not independently attested. All values may be forged together
and resealed. SHA-256 is not provenance or financial validation.

The [actual four-prefix example and limitations](evidence/trace-reader/README.md)
retain the exact engine #30 default-worker artifact. Omitting transaction 0
changes gas/logs in 1 and 2 and leaves 3 at nonce 5,523 versus expected 5,522.
This technical case is separate from frozen model/holdout evaluation. Shanghai/
Ethereum-only prefix limits, same-block funding admission and full-block/root/
opcode/end-state limitations remain the engine's responsibility. Packages remain
unpublished and required protected-main approval is still pending.

## Read historical price observations offline

`load_observed_trace(path)` accepts the supported `observation_version: "0.1.0"`
wrapper from engine `trace-observe --native`. It validates both the
wrapper and nested transaction report without an engine import, server, RPC or
model call. The current fixed profile is `aave-v3-ethereum-weth-price`:

```python
from entrotter_sdk import load_observed_trace

observed = load_observed_trace("tests/data/observed-price32.json")
print(observed.artifact_id, observed.trace.baseline_verified)
for row in observed.observations:
    print(row.branch, row.phase, row.price, row.base_unit)
classification = observed.classification
if classification.complete_price_views:
    print("Candidate minus baseline, raw USD units:", classification.price_difference)
else:
    print("Price difference unproven:", classification.unproven_reasons)
```

Run this from the source checkout with `PYTHONPATH=src`; the example uses an
[actual recorded native replay](evidence/observed-reader/README.md), not a new chain
execution. Prices and feed fields are exact Python integers, including values
above2**53. Raw USD prices use the recorded1e8 base unit; the recorded difference
is789973126 raw units. Do not divide through a floating-point value when exact
formatting matters. Complete price views and matching baseline receipts are
separate facts; neither proves a signed consumer strategy or profit.

`ObservedTraceResult.parse(value)` and `verify_observed_trace(value)` provide
in-memory validation and boolean verification. Typed frozen `PriceObservation`
records include `ObservationHead`, `ObservationCode`, `PriceRound` and a tuple
of `ObservationError` values. Missing getters or heads are `None`, preserving
finite query/category/RPC diagnostics. `PriceClassification` exposes sorted
`unproven_reasons` and returns `None` for price deltas if any required view is
unproven. Negative feed answers remain readable as unproven evidence.

Validation checks fixed version/profile/scope, both content IDs, the complete
nested trace, four ordered phases, query success/error coverage, exact ABI widths,
address padding, uint80 round IDs and signed int256 answers. It binds phase heads
to the reported parent/block and recomputes price classification from raw values,
including timestamps, base unit/currency, source/aggregator and code identities.
A wrong classification remains invalid after resealing. These checks follow the
engine40 fixed-profile contract; they do not authenticate a provider or deployed
code. All fields can still be forged consistently and resealed.

The regular-file reader caps input at8 MiB, observations at64 KiB, rejects duplicate
JSON keys and caps integer tokens at512 characters. Result snapshots and nested
typed values are immutable; `.report` provides a fresh copy including raw ABI.
The original `load_trace`, action/model-record and HTTP APIs are unchanged.
Packages remain unpublished; human protected-main approval is separate.

## Read Aave account impact offline

`load_position` reads the separate fixed `aave-v3-ethereum-account` wrapper.
It checks all three content hashes, the complete price/trace report, admitted
account/plan, four phase heads, strict six-word ABI, finite errors and recomputed
classification. It imports no Engine and requires no RPC, Docker or model call:

```python
from entrotter_sdk import load_position

position = load_position("tests/data/aave-account-position13.json")
comparison = position.classification
if comparison.complete_account_views:
    print("Available borrowing, candidate minus baseline:",
          comparison.differences.available_borrows_base,
          "raw base units; denominator:", comparison.base_unit)
    print("Health factor difference:", comparison.differences.health_factor_wad)
else:
    print("Account difference unproven:", comparison.unproven_reasons)
```

Run from the source checkout with `PYTHONPATH=src`. The [original recorded
13-input Docker result and reader evidence](evidence/position-reader/README.md)
retains all original baseline receipts, 12 candidate receipts and omission12.
Its available-borrowing difference is81628966124 raw USD base units (denominator1e8),
and health-factor difference3852169807877337 WAD units (denominator1e18).
These are aggregate account measurements, not token balances, profit, a signed
loan or proof that WETH price is the sole cause. This reader performs no replay.

`PositionResult.parse(value)` and `verify_position(value)` offer in-memory and
boolean verification. `.prices` and `.trace` expose the existing typed readers.
Frozen `AccountObservation` values retain full head/code/configuration/error
identities; `AccountValues`, `AccountDifferences` and `PositionClassification`
keep exact Python integers and nullable differences. `.report` and `.plan`
return fresh copies. Inputs remain regular JSON within8 MiB; account rows
within64 KiB, duplicate keys and integer tokens over512 characters are refused.

Missing account/price views, changed initial values/code, unverified original
receipts or a failed Pool→addresses-provider→oracle binding keep all differences
null and explicit reasons. Zero debt retains raw uint256-max health, `no_debt`
status and a null normalized health difference. The observed base denomination
is reported only when the configured pool and oracle agree. Integrity is internal
consistency: provider/proxy implementation, EVM execution and financial safety
are not authenticated, and a producer can forge all values and reseal them.
The existing v0.1 action/model/HTTP and separate trace/price formats are unchanged.

## Quality checks

The CI quality job checks every production Python file under `src/` and `scripts/`
with Ruff lint/format, mypy including unannotated function bodies, and all default
Bandit rules with `--ignore-nosec`. Any finding fails; the complete report is
retained. A second check rejects empty/partial scans or skipped rules. This is
static analysis, not a proof that the client or remote engine is secure.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: --index-url https://pypi.org/simple -r requirements-quality.txt
.venv/bin/python -m pip check
.venv/bin/python -m ruff check src scripts
.venv/bin/python -m ruff format --check src scripts
.venv/bin/python -m mypy src scripts
mkdir -p .quality
.venv/bin/python -m bandit --ignore-nosec -r src scripts -f json -o .quality/bandit.json
.venv/bin/python scripts/check_security.py
.venv/bin/python scripts/check_dependency_manifest.py
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt --progress-spinner off -f json -o .quality/dependencies.json
.venv/bin/python -m build --no-isolation --wheel --outdir .quality/wheels
```

All 42 Python tool/build packages are version/hash locked; runtime dependencies
remain empty. The dependency gate rejects unpinned or unaudited build/runtime/
optional requirements. Advisory lookup errors fail; no advisories are ignored.
The Python runtime and operating system are outside this Python-package audit.
The workflow installs the wheel into a fresh venv with `--no-index --no-deps` and
checks its import and bundled `py.typed` marker in isolated Python mode. It does
not publish packages. The marker exposes existing type hints to consumers;
normal mypy checks do not establish full static typing of arbitrary JSON.

To update tools, edit `requirements-quality.in`, regenerate the complete hashed
lock with the pinned `pip-compile`, and rerun the quality job and unit matrix.
GitHub Actions use immutable commit IDs; full scan/audit reports and the wheel
are uploaded for review. Code examples and the real API are verified separately.
