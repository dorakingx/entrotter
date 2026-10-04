# Copy the selected public CLI recipe

Verified bundled examples now offer Copy setup commands and Copy inspection
command. Buttons write only the cached fixed public recipe through the native
Clipboard API after activation; they never read the clipboard or execute commands.
Codebox text, local filenames/imports and URL values cannot enter the copied text.
Unavailable or denied APIs show a plain manual-copy fallback without browser error
contents. Loading, rejected and local imports hide/clear recipes and feedback.

Only one clipboard write runs at a time. Its payload cannot be cancelled after
starting. If the report changes, old success/failure feedback is ignored and a new
verified example explains the pending request with a manual-copy option. New copy
controls wait until the earlier request settles, avoiding overlapping stale writes.
The old requested public text may still reach the clipboard; this is not a claim
that changing reports cancels clipboard operations.

[Actual checks](checks.json) bind136 Node/12 site tests and19JS/20typed checks with
152 complete reviewed findings. All151 existing source-span reasons remain exact;
one new fixed public-fixture read has an explicit rationale. The new VM regression
fails against the immutable05a source lacking the feature and passes on current
production functions. [Browser results](browser.json) summarize51 groups and bind
64 complete raw axe scans by hashes, with zero violations or JavaScript exceptions.
At390px all six recipes use actual keyboard-activated native write/readback; setup
and selected command bytes match, focused buttons remain focused and Tab continues
to the inspection codebox. At320px finite denied/missing API, held promise, sample
switch, local import and late-rejection controls verify serialization and clearing.
Original49 browser groups/assertions remain intact; all18 sample/viewport scans
include the new controls. The initial one-case focus probe found no defect and
supports no browser-wide focus guarantee. Contrast incompletes remain explicit;
no assistive-technology certification is claimed. Full raw originals remain retained.

[Current Aave view](view.json) uses production hash/view/async-agent functions.
All original59506-byte report fields and16 four-column rows remain unchanged except
appSHA. Prior CLI recipe/function/pins and actual six clean-clone inspection results
are reused unchanged; no new chain, model, RPC, authenticity, profit or performance
result is claimed. Current-head CI/publication, independent human-main approval
and live Pages remain separate. Goal continues; Discord is excluded.

The initial88a9bb2 CI quality job failed at ESLint (`holdCliCopy` was undeclared).
The original local lint log contained the same error, masked by a later successful
command; the initial review bound that log but missed its diagnostics. Those
original results are retained as failures. Referencing the same DevTools hook as
`globalThis.holdCliCopy` fixes the runner without weakening rules or changing
production, types or locks. Current full19-file ESLint has zero messages, types
and152 reviewed findings pass, and current real Chromium again passes51/64.
Initial CI independently passed51/64 browser and22 docs/126 links; its failed
quality run provides no new successful type/security/dependency audit claim.
