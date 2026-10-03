# Exact account comparison in the terminal

`position-inspect --format text` presents the already verified SDK account
classification with exact integer scaling. Default and explicit JSON preserve
all previous output bytes. This is an offline presentation change, not a new
historical replay, model evaluation, performance benchmark or deployment.

The [recorded sample](../../tests/data/aave-account-position13.json) retains its
original SHA-256 `cd96e04c837fa1dcc6b6cf009d58adffe3ffdaebc9fbd5b3b900d71cd2912978`.
Its [expected text](../../tests/data/aave-account-position13.txt) shows all three
source IDs,13 original transactions/skip12, all six account fields, health
status and limits. Capacity differs816.28966124 USD and health differs
0.003852169807877337; this does not prove profit or a signed loan strategy.

From the six-repository workspace with SDKba4 sources:

```bash
PYTHONPATH=cli/src:sdk-python/src python3 -m entrotter_cli position-inspect cli/tests/data/aave-account-position13.json --format text
PYTHONPATH=cli/src:sdk-python/src python3 -m unittest discover -s cli/tests -v
```

Current local full83 tests, including8 formatter groups, pass without skips.
The controls independently reseal synthetic mutations accepted by the SDK:
uint256 precision, positive/negative/zero differences, basis points, health at
one, no-debt transitions and valid-unproven records. Unsealed and resealed
inconsistent artifacts and duplicate JSON are refused with empty stdout.
A guard rejects network, Engine and export-ledger use for the original record.

[Verification](local-verification.json) binds current sources, raw local logs,
original JSON output hashes and both wheel contents. A fresh no-index installation
of the newly built CLI and original SDKba4 CI wheel runs with Python `-I`,
matching the complete expected text and original10,298-byte JSON output.
All seven CLI and five SDK module bytes, UTF-8 README metadata and RECORD hashes
match their sources. Full Ruff/format/mypy checks and unsuppressed Bandit cover
all nine production/script files with no findings or skipped rules; the complete
[scan](bandit.json) and [quality output](quality.log) are retained.

The compressed [full units](unit-tests-passed.log.gz) retain complete passing
output, including all eight formatter groups.
Earlier expected missing-option regression, scope-wrap expectation mismatch and
local authoring/patch failures are retained in the ignored local checkpoint;
the manifest distinguishes them from final passes. No timeout/assertion/gate was
weakened. Independent review corrected a JSON wording overstatement: it includes
typed observation details; the original input retains raw ABI words. Locks, sample bytes, SDK/Engine pins, validators, execution, quotas and
original required CI contexts are unchanged. Quality CI adds installed text
inspection plus a full byte comparison without removing original wheel checks.
Fresh current-head CI, independent review and protected main approval remain
separate gates; no current Pages or formal submission is claimed by these files.
