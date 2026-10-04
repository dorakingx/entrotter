# Exact generic result inspection in the terminal

`inspect --format text` makes a saved EVM action result readable without
manually dividing raw token/native amounts. It shows initial/final/change and
candidate-minus-baseline values for native balance and every pinned token,
native gas cost, gas usage, reverted/rejected counts, source pin, artifact ID,
recorded policy decisions and assumptions. Addresses distinguish identical
symbols. Every digit is retained through integer arithmetic; no float is used.
Default JSON remains unchanged; `--format json` is explicit. Fixture mode
retains the original model metrics/comparison with a synthetic label.

## Original sample and controls

[aave-borrow-result.json](../../tests/data/aave-borrow-result.json) is byte-for-byte
the [Enginef53 original action report](https://github.com/entrotter/engine/blob/f53a66a303e67ca4fbb4322a06b36b036f4db599/evidence/aave-borrow-actions/report.json):
59506 bytes, SHA256
`e2db6ee04f2642e7e75ac53e8ad6212cd68b2ae4aab0ca7a4e06063f5f435622`.
The [Engine execution packet](https://github.com/entrotter/engine/tree/f53a66a303e67ca4fbb4322a06b36b036f4db599/evidence/aave-borrow-actions)
retains the actual bounded archived-state run and recorded replay. This CLI
change performs recorded inspection only. Both artificial20 ETH/local impersonated
branches wrap/approve/supply10 WETH, propose borrowing9 WETH, then borrow1 WETH.
Only candidate step3 reaches the built-in preflight policy. The baseline's borrow
reverts; candidate holds. The final smaller borrow is supplied, not policy-generated.

[The entire text](../../tests/data/aave-borrow-result.txt) preserves exact1 WETH,
10.000000094454558462 aWETH and1 variable-debt token in both final branches.
It shows723131 versus560326 gas used and the recorded hold. The native-balance
difference includes differing gas prices; it is not profit. Generic roles and
values are not inferred from token symbols. Content hashes and local accounting
consistency do not authenticate provider state or the EVM execution.

Seven new [control groups](../../tests/test_result_text.py) cover the complete
original text and unchanged default JSON; missing token records versus true zero;
uint256 maximum/36 decimals/negative one-unit change/address casing; resealed
contradictory units/identity/duplicate/delta and invalid bool/float/overflow/sign/
padding; fixture/native-without-token modes; escaped free metadata; invalid format
and bad integrity. Mutations are synthetic controls, not additional EVM runs.
All outputs are built before printing, so contradictory displayed fields return1
without partial stdout. Missing records stay Unavailable. Network, API, Engine
import and export-ledger tripwires pass on the fixed inspected paths; these are
regression controls, not a general security sandbox.

## Executed verification

[Manifest](manifest.json) records the expected initial unsupported-option failure,
current7 groups, full107 tests in16.301 seconds with no skips,11-source Ruff/mypy/
Bandit checks and zero findings. Full original stdout/stderr/status are saved
privately before assertions, with hashes in [local checks](local-checks.json).
Timing is recorded test duration, not a performance comparison.

Current local unpublished CLI/SDK wheels were installed into a fresh venv with
`--no-index --no-deps`. Actual isolated `-I` inspection matches the whole text;
default JSON matches the original complete-output hash. All seven new groups
also pass against installed packages. [Installed execution](installed-execution.json)
and [provenance](installed-provenance.json) bind both wheel hashes, README,
sample/golden/source bytes, all14 runtime module hashes and relative installed
origins. Engine installation is absent. [Complete source scan](source-scan.json)
binds all11 production/script files without suppressed rules or findings.
Dependency pins/locks and frozen agent/price/account execution inputs remain
unchanged; their earlier executed results are historical reuse. Current mandatory
CI separately runs those original jobs, strict audits and the added installed
text/golden/controls. Independent review, publication, coordinator selection and
protected human main/Pages approval remain separate gates.
