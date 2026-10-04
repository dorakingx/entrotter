# Trace contract candidate

This candidate starts from tested scenarios commit
`3a78ecca24334ae87119a5a0b64c84ba6dd71de1` and adds the distinct trace plan/result
wire family implemented by engine candidate
`0d4faf7d4feda817499ea19e8797a0e03504fbad`. All original v0.1 schemas, scenario and
benchmark inputs, and dependency locks remain unchanged.

The complete offline suite passed 23 tests in 1.407 seconds, including nine new
contract tests. Before implementation, those nine tests failed because the trace
family was unavailable. Ruff lint/format, mypy on all six Python sources, and the
full default-rule Bandit scan with `--ignore-nosec` pass. Existing successful
dependency audits belong to the unchanged tested base; no fresh advisory audit
or candidate CI result is asserted here.

Independent source review requested the exact committed engine report in place
of an earlier ignored native attempt. The fixture now matches
`0d4faf7d4feda817499ea19e8797a0e03504fbad:evidence/trace-replay/mainnet-prefix.json`
byte-for-byte. All nine affected contract tests passed in 0.989 seconds after
that correction; unchanged checks were reused. Documentation links passed all
14 links across seven documents, with no errors, timeouts or exclusions.

The original public plan and an existing native historical receipt replay are
copied byte-for-byte. This schema change performs no archive, model or EVM run.
The report's recorded first transaction uses 208,144 gas and has eight logs;
the candidate skips it. Schema validity does not establish those execution facts.
Shape-valid semantic violations and stale hashes remain accepted by deliberate
tests so consumers cannot mistake this validator for the engine's verifier.

Sorted skips, prefix/order/source correspondence, aggregate serialized bytes,
signature/hash checks and receipt equivalence require runtime validation. The
confirmed parent-state pool admission limitation and broader block/state/opcode
limits remain open. Independent source review found no remaining actionable
issue after the fixture correction. Candidate CI, required human GitHub approval
and protected integration remain pending. Commands, source hashes and logs are in
[the contract evidence](evidence/trace-contracts/summary.json).
