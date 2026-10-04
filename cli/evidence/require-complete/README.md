# Recorded comparison completeness in scripts

`position-verify --require-complete` and `observed-verify --require-complete`
let automation stop at a valid but unproven recorded comparison. Ordinary
verification remains status0 for internally consistent incomplete records.
The opt-in policy requires both complete views and original baseline-receipt
agreement: success0, unproven3 with unchanged full stdout JSON and finite stderr
reasons, invalid input1 with no JSON, argument error2. Inspection and execution
commands reject this option. This does not authenticate providers or prove
source execution, signed strategy, investment quality or profit.

The [regression tests](../../tests/test_require_complete.py) exercise the actual
CLI process: original output SHA equality; all six existing price controls;
missing account and nested price evidence; unmatched baseline receipts even
when all price views are complete; zero/negative differences; health below one;
no debt and debt transitions; malformed/resealed contradictions and duplicate
keys; rejected options; Engine/network/export-ledger guards. Nine groups pass,
and the full92-test suite passes without skips. Controls are synthetic changes
to old source records, not newly executed EVM results.

Local Python3.13 verification ran Ruff lint/format, mypy on all9 production/script
files, and full Bandit without disabled rules or findings. The fresh CLI wheel
and unchanged SDKba4 CI wheel were installed without registry access into a
fresh environment without an Engine. Every7 CLI/5 SDK module, embedded README
and hashed RECORD entry matched the source; all9 exit-contract groups, complete
stdout goldens and existing2052-byte terminal golden passed. The installed
quality workflow now runs those same exit-contract groups after its old checks.

[Source hashes, package provenance and exact scope](local-verification.json),
[full passing test log](unit.log.gz) and [full security scan](bandit.json) record
these local checks. Original argparse and accidentally malformed synthetic
fixture failures remain in ignored raw local evidence, with their scope in the
manifest. No validation assertion, error behavior or timeout was weakened.
Current-head mandatory CI and independent review are separate evidence. Neither
this change nor a green PR claims protected-main integration, live Pages,
new video, formal submission or achievement of the continuing improvement goal.
