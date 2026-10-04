# Offline trace reader evidence

This candidate reads the separate engine `trace_version: "0.1.0"` family through
immutable typed transactions, outcomes, receipts and logs. It performs no HTTP,
archive, model or EVM call. Existing `Client`, `RunResult`, `verify` and the
`/v1/runs` wire contract remain separate and unchanged.

The frozen [four-prefix fixture](../../tests/data/canonical-mainnet-prefix-four.result.json)
is byte-identical to the actual engine817 default-worker report, artifact
`cf1b51833babf17c1b39c5d37af0ff7945da43422e2efc3453d36e72b2d0810f`,
SHA-256 `1bc41a9375017d601f0a8a027ca59977afedbbb109f5089b5b09eaac3f831db2`.
Its original/baseline projected receipts match; omission0 changes gas/logs1/2
and causes original nonce5523 versus expected5522 in3. Runtime14.539113seconds
belongs to that original execution, not this reader or a new benchmark.
See the [engine execution scope](https://github.com/entrotter/engine/blob/8176597af994dddb7a3dc6721db623580ebc9601/evidence/trace-mine-deadline/README.md).

The separate one-prefix fixture is the original engine0d native report, not an
independent new execution. The signed0/1/2 vectors are public synthetic local
inputs with artificial funds/code, not historical evidence or signature recovery.
[Fixture and wheel provenance](fixture-and-wheel-provenance.json) records byte
comparisons; [summary](summary.json) records source scope and limitations.

All36 SDK tests pass, including18 trace tests. These cover exact bounds/shapes,
legacy/typed RLP metadata, source/plan/index/receipt binding, signed gas ceilings,
revert/call consistency, cumulative gas and branch nonce progression, exact unique
receipt differences/flags, honest rejected or unmined baseline data, immutable
snapshots, regular-file/nonblocking import, duplicate keys and malformed/oversized
inputs. Resealed contradictions are checked even when SHA-256 is recomputed.
A coherent fabricated revert is deliberately accepted: metadata consistency does
not prove actual execution, source authenticity, signature validity or finance.

The full5-source Ruff lint/format, mypy and unsuppressed Bandit scan pass with
zero findings/skipped rules. [Full scan](bandit.json), [source coverage](security-scope.json)
and [unit output](unit.log) are retained. A fresh isolated venv installs the wheel
with no network/dependencies, confirms3 module bytes and `py.typed`, and reads
actual gas/nonce outcomes. CI independently reruns the Python matrix, full static
scope,42-package locked advisory audit, docs and fresh installed-wheel proof.
The [independent initial review](independent-review.json) found four actionable
metadata/receipt gaps. The [follow-up review](independent-followup-review.json)
confirmed all four fixes with focused offline regressions and no remaining
actionable finding. These source reviews are not GitHub approving reviews.
Local results are not yet a remote CI or protected-main approval claim.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m ruff check src scripts
python3 -m ruff format --check src scripts
python3 -m mypy src scripts
python3 -m bandit --ignore-nosec -r src scripts -f json -o .quality/bandit.json
python3 scripts/check_security.py
python3 -m build --no-isolation --wheel --outdir .quality/wheels
```

No package publication, deployment, protected merge, new model call, holdout
reuse, media upload or competition submission occurs in this change.
