# Retained failing checks

`before.py` and `before.log` exercised engine parent
`6410c37663d37685a30effccd87844e1740b8637` and standalone CLI parent
`952bfb5aba14b674dd959035a5625fadbd2b07d1`. Each wrote 129 distinct reports:
the previous single-file cap did not impose aggregate retention. Temporary
test payloads were removed after observation.

`boolean-version.log` records an initial implementation accepting JSON `true`
as ledger version 1 through Python's boolean/integer equality. Strict integer
type validation fixes it; both packages retain the regression.

`moved-rename-hook.log` records an existing artifact failure-injection test
patching the removed `artifact.os.replace` location. The test now pauses/fails
the actual report rename in the shared helper, without failing bookkeeping
renames. It still verifies old-output preservation and temporary-file cleanup.

Final engine/CLI logs include these passing tests. Workspace prefixes in text
logs are normalized to `<workspace>` and trailing whitespace is stripped;
measurements and errors are preserved.

`workflow-context.json` retains the first coordination workflow rejection.
The new job-level environment used a runner context that is unavailable there.
The runner step now sets the shared directory through `GITHUB_ENV`; this does
not change runtime implementation or remove a test.
