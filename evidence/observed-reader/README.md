# Offline observed-price SDK reader

This candidate adds standalone typed inspection of the supported engine40
`aave-v3-ethereum-weth-price` observation wrapper. It validates content IDs, the
complete nested trace, fixed ABI/phase/query/head/code/classification bindings,
then exposes frozen typed prices, feed fields and finite errors. The SDK needs
no engine dependency or import, HTTP server, archive access, model or chain call.
The [SDK usage example](../../README.md#read-historical-price-observations-offline)
reads the recorded fixture directly.

`tests/data/observed-price32.json` is byte-identical to the actual supported
[native32 engine record](https://github.com/entrotter/engine/tree/40bea57e25ab94c0d0f6136b4c3a5af4a99e6a1d/evidence/owned-consumer-observations/historical-32),
SHA2567010848300c353310fb78dab7f377daea4226633e49af3c1a384bcb3a579ba9d.
It covers32-of181/skip12 and four consumer/producer phases: baseline price
257082415000→256292441874, candidate unchanged257082415000, raw USD unit1e8.
All32 full baseline receipts and19 structural candidate differences are retained.
This reader performs no new replay.

Six compact synthetic controls are exact copies of the reviewed
[viewer controls](https://github.com/entrotter/entrotter.github.io/blob/a19d3b17fcf44e58a237b622de8cef89842eb6e7/tests/data/observed-controls.json),
SHA256b68865916ac365e2ca1093c16439b4baaa628e14b3b2e209f36596f2c09bba67.
They preserve engine40-sealed golden classifications and IDs for2**200 integers,
missing source/head, zero code, future feed and negative signed answers. They
are deliberate mutations, not additional chain evidence.

- [Local results/source and wheel bindings](summary.json), [copy provenance](provenance.json).
- [Complete45-test log](units.log), including9 new observed groups,22 resealed
  contradictions,5 RPC diagnostic mutations, immutable snapshots and file bounds.
- [Full6-source Bandit report](bandit.json) and [scope bindings](security-scope.json):
  no findings or skipped rules; normal Ruff/mypy pass for all production source.
- [Fresh isolated wheel readback](wheel-isolation.json): no engine import available,
  typed marker present, direct observed report and prior four-prefix reader pass.

The public v0.1 HTTP/action/model and separate trace formats remain unchanged.
Regular input is bounded at8 MiB and observation rows at64 KiB; duplicate keys
and excessive integer tokens are rejected. Internal consistency is not provider/
deployed-code authenticity, signature recovery, signed strategy/profit or
full-block/root/opcode proof. Every value can still be forged consistently and
resealed. Matching receipts and complete price views are distinct facts.

Component current-head CI, root pin integration, independent human main approval
and Pages remain separate. Packages are not published. Original regression/test
assertion mistakes are retained privately and scoped in the summary; no passing
result substitutes for new chain or market validation.
