# Failed historical gate and bounded diagnostic candidate

At e84980e, seven required checks passed: full252Linux native tests with0skips,
four252-test unit matrices (31Anvil-dependent skips each),23-source full
quality/23retained findings/42exact Python lock identities/18wheel modules,
and12document hashes. The isolated job passed all25Docker tests, including the
new oracle case, in216.086s, then the existing first default-host mainnet replay
failed after about2.84s. One unchanged-head isolated-only diagnostic retry again
passed25Docker tests in216.203s and failed that same gate after about3.89s.
Both always-container-cleanup gates passed. See [attempt1](isolated-attempt1.log)
and [attempt2](isolated-attempt2.log). No exported historical report or later
image/native advisory checks are claimed; all eight required gates are incomplete.

Both retained image manifests match all19current inputs. Read-only dRPC chain,
pinned target/parent headers and original208144gas/8log receipt subsequently
passed. This does **not** identify the original failure as transient. A local
default Python CA issuer refusal is recorded separately; using the existing
hash-locked Mozilla CA bundle retains full TLS/hostname verification and does
not establish the Linux worker's original cause. No third blind retry or
speculative runtime/state repair was made.

The test-only failure diagnostic preserves the unchanged immutable image,
same fixed worker slot and fresh ownership label, daemon admission,1CPU,
512MiB memory/no additional swap,128PIDs, read-only/non-root/tmpfs/caps controls,
and archive bridge. It calls the unchanged data-only worker protocol on the
exact failed one- or four-prefix plan. Instrumentation records source capture,
fork startup, header/account/queue, mining and receipts. The primitive retains
one shared150-second trace budget; entrypoint180s and host190s bounds remain.
Host output is capped16KiB; checkpoints32 and exception-chain inspection8 nodes.

Only finite allowlisted error **types**, method/phase/transport enums and optional
strict integer TLS-verification/HTTP codes are returned. Exception messages,
args, dynamic class names, URLs, params, raw stderr and tracebacks stay private.
The host checks exact shape and request binding before accepting anything.
Unsafe output is discarded. Client session/descriptor shutdown nests owner-ID
container cleanup, preserving the primary error separately from cleanup errors;
foreign busy slots are refused. The normal failed gate stays failed even if
the diagnostic completes. This adds no public arbitrary-code/runtime feature
or fixture fallback, and no egress-firewall or authenticity guarantee.

Fifteen focused tests pass in0.729s, including real embedded entrypoint
execution for empty, invalid-object and oversized input with no network. They use real stdlib process/session/pipe
behavior and mocked Docker admission/removal, **not** a local Docker/kernel or
upstream execution claim. Root review found descriptor-close and missing-code
TLS-classification gaps; [three regressions failed before fixes](helper-regression-before.log)
and [all14 now pass](helper-regression-after.log). The additive
[15-test entrypoint regression run](helper-entrypoint-regression.log) validates
finite failure JSON, request binding, zero stderr and actual embedded imports. Production23source/script hashes,
existing security policy,18wheel modules and19image inputs remain unchanged.
The helper is outside production scanner/type coverage and requires independent
source/privacy/lifetime review. [Summary](summary.json) and
[copy/redaction provenance](copy-provenance.json) retain exact scope and hashes.

[Independent source/privacy/lifecycle review](independent-review.json) passed
with no remaining actionable finding. Its immutable readiness record retains
the pre-review source/evidence hashes. New-head CI remains pending; this review
is separate from protected-main human approval. No local Docker/VM,
new model/holdout/media operation, upstream write, merge or deployment. Current
published composition remains coordinator8029/engine935; prepared integration
stays unpushed until all mandatory component gates pass. Prior nine-node raw
evidence loss remains disclosed in the enclosing oracle evidence.
