# Safe RPC diagnostics: unpublished reviewed candidate

The candidate preserves RuntimeError/RPCRejected compatibility, method allowlists,
the 4 MiB response cap and default worker/HTTP v0.1 failure envelopes. Trusted
Python errors expose finite codes and allowlisted methods; native trace CLI adds
only a fixed safe suffix. HTTP protocol/truncated-body/decode failures are normalized
without provider messages, body fragments, parameters or URLs.

[summary.json](summary.json) binds the final source/readiness, exact quality logs,
raw full scanner output and independent review. The [initial readiness](readiness.json)
and [source review](independent-review.json) are unchanged historical records.
The additive [full native proof](native-suite-proof.json) records 294 passing tests,
0 skips in 45.076 seconds with pinned Foundry 1.8.3. Its separate
[independent native review](root-native-suite-review.json) preserves the earlier
source-review timing and verifies the new full-suite proof. Final targeted tests pass
32 cases in 0.158 seconds; Ruff/format/mypy cover all 23 sources and full Bandit
retains the same 23 findings/rationales, 0 errors/skipped rules. Only two source
hash bindings changed; no rule/advisory suppression was added.

Actual loopback tests cover timeout, HTTP503, JSON-RPC rejection, malformed JSON
and a valid JSON body prematurely ending before Content-Length; owned threads and
ports close. The original transport accepted that truncated response. Hostile
exception/forged metadata tests verify privacy and native CLI propagation. The
[root pinned trace tests](root-trace-pinned.log) pass 22 cases. The earlier
[root wrong-version log](root-trace-wrong-version.log) preserves an Anvil 1.6.0
setup failure and 17 passing tests; it is not a passing 1.8.3 run.

Artifact mappings disclose each original/public SHA and any replacement of local
absolute checkout/tool paths. Ignored originals remain intact. Raw JSON/readiness,
quality and final passing logs are byte-identical unless the mapping says otherwise;
public sanitized logs cannot be used to recompute the originalprivate log hashes.
Intermediate edited test bytes for earlyregression logs were not frozen; the final
32-test proof binds only the final source. No old bytes/hash are invented.

This package is local author/source-review evidence, not current-head CI, Docker,
archive omission, provider-state truth, deployment or human GitHub approval.
Native002's original failure remains unknown. New classifications apply only to
new invocations. No production state, balances, nonces, signatures or deadlines
were repaired or expanded. Commit/push and required exact-head checks remain pending.
