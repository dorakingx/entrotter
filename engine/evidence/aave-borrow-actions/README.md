# Supplied Aave supply and borrow actions

This October4 run exercises the actual archived Aave V3 Ethereum Pool through
the default bounded Docker worker. It extends the separate read-only account
comparison with an actionable experiment: supply collateral, compare a proposed
borrow under the built-in risk policy, then execute a supplied smaller borrow.
No new Python runtime dependency, model call or paid service is used.

## Reproduce and inspect

Follow the repository's bounded worker setup, using pinned Foundry1.8.3 and an
archive-capable Ethereum source. From the repository root:

```bash
export PYTHONPATH=src
export ENTROTTER_RPC_URL='https://YOUR_ARCHIVE_PROVIDER'
python3 scripts/aave_borrow.py --output aave-borrow-report.json
python3 scripts/aave_borrow.py --check evidence/aave-borrow-actions/report.json
python3 scripts/aave_borrow.py --recording evidence/aave-borrow-actions/recording.json --output replay.json
```

Only `--check` is offline. Execution and recorded replay require the configured
immutable worker and archive source. The retained report and recording were
written before scientific checks; the contributor script also saves its whole
returned report before checking. A changed observation refuses exact recorded
replay. No automatic retries, fixture substitution or native fallback are used.

## Inputs and actual results

The [scenario](../../tests/data/aave-borrow-actions.json) pins chain 1,
block 18999892, hash
`0xafd6a8c681f5e3b6ae9cba963e4b8dd7e3c9bf76fe45e0c3e145ccb2918b2ba6`.
Both local chain 31337 branches start with the same artificial 20 ETH native
balance and zero tracked tokens. Account impersonation is local only. There
is no token balance or contract-code override. Both supplied action lists are
wrap 10 ETH, approve 10 WETH, supply 10 WETH, propose borrowing 9 WETH, borrow 1 WETH.
Only candidate step 3 reaches the causal current-state policy; the final 1 WETH
action is supplied, not a policy-generated replacement.

| Exact local outcome | Baseline | Candidate |
| --- | --- | --- |
| First three actions | success, success, success | identical execution |
| Proposed 9 WETH borrow | mined revert,162805 gas | preflight rejected, hold/no transaction |
| Final1 WETH borrow | success | success |
| Final WETH raw units | 1000000000000000000 | 1000000000000000000 |
| Final variable-debt raw units | 1000000000000000000 | 1000000000000000000 |
| Final aWETH raw units | 10000000094454558462 | 10000000094454558462 |
| Total gas used | 723131 | 560326 |
| Gas cost wei | 11172440829680288 | 8750018396830500 |

Every tracked token uses 18 decimals. Both final receipts contain the actual
Pool `Borrow` event for this actor/beneficiary, amount 1e18, variable mode 2 and
referral 0. All nine transactions, complete receipts/logs, ten slots, exact token
deltas and the whole policy exchange remain in [report.json](report.json).
The native balance difference is 2422422432849788 wei; differing gas prices in
the final blocks also contribute. This is not profit or a predictive return.

[execution.json](execution.json) records first-run elapsed 20.419179708s and
no remaining Docker worker slot. The running local Docker VM/caches may be warm;
this is not a startup benchmark or speed comparison. [worker-image.json](worker-image.json)
binds all 22 engine modules and the Dockerfile, immutable base, archive and native
binary. Its image is local/unpublished; rebuilding does not establish a new
advisory scan. Current CI separately audits the rebuilt image and native inventory.

The existing keyless CI endpoint returned chain ID, pinned full block header
and Pool bytecode in [provider-readiness.json](provider-readiness.json).
The address constants reuse the retained
[January 4 address book](historical-AaveV3Ethereum.sol), original commit
`575eac6d595d5d15ba5e6ca9192a2f2a5c719022` from
[Aave's address book](https://github.com/bgd-labs/aave-address-book/blob/575eac6d595d5d15ba5e6ca9192a2f2a5c719022/src/AaveV3Ethereum.sol).
The original IPool blob identity and authored ABI notes and independent `cast keccak` topic are retained
in [borrow-interface-source.json](borrow-interface-source.json),
[borrow-abi.txt](borrow-abi.txt) and [borrow-topic.txt](borrow-topic.txt).
Successful calls/hashes do not authenticate the upstream provider or deployed code.

## Verification and limits

The second actual bounded run replays [recording.json](recording.json) and returns
the same entire 59506-byte report, SHA256
`e2db6ee04f2642e7e75ac53e8ad6212cd68b2ae4aab0ca7a4e06063f5f435622`.
[replay-report.json.gz](replay-report.json.gz) preserves the complete second output;
[replay-equality.json](replay-equality.json) records comparison and execution scope.
Input/checker refinements occurred afterward, without changing the execution API
or worker. The final script checks both retained outputs offline; current CI
separately executes the final script. No second-run timing claim is made.

The local native suite passed 385 tests in 83.539s with no skips before adding
the offline semantic controls. Five additional groups pass, rejecting resealed
false amounts, debt, gas, submission/revert status, observation head/future data,
native accounting, beneficiary/mode and provider metadata, plus FIFO/symlink,
oversized and duplicate-field inputs. Four ABI groups include independent
`cast calldata`, uint256/uint16 bounds and fixed mode 2. These are not one local
390-test run. The original locked dependency audit reports 0 vulnerabilities;
final 28 production/script files pass Ruff, formatting, mypy and full Bandit with
all 25 original findings unchanged. Only reviewed source hashes are refreshed.
Retained logs/results and [manifest.json](manifest.json) bind this scope.

Independent review found two checker issues: unbounded file admission and
missing observation-head binding. Both are fixed and covered by the controls.
The first producer failed before execution on a Dockerfile path; a type-check
failure was fixed by explicit action narrowing. [authoring-failures.json](authoring-failures.json)
distinguishes those setup/checker failures from actual EVM results.

This executes supplied actions on archived state using an artificial funded
actor, not original signed transactions, a real wallet strategy, economic
counterfactual forecasting or liquidation testing. Preflight/revert does not
establish the refusal cause. The policy is the existing built-in deterministic
current-state rule, with no LLM/model bill or future observation. The public
v0.1 scenario/result format and all existing CPU/memory/time/export/admission
controls remain unchanged. Protected human main approval, candidate Pages,
submission/media delivery and the continuing competition goal remain separate.
