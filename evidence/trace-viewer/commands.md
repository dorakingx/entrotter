# Signed-prefix viewer author checks

Use Node22.23.1 (`PATH=/opt/homebrew/bin:$PATH`) and the existing hash-locked Python venv.
No dependency lock or model/account setting changed. Development checks do not
execute EVM transactions. The two recorded receipt fixture files preserve original evidence byte-for-byte.
Compatibility unit vectors are locally Python-sealed metadata only; the wide raw
envelope does not claim a valid signature, execution, or new chain evidence.

```bash
npm test
.venv/bin/python -m unittest discover -s tests -v
npm run lint
npm run format:check
npm run typecheck
npm run security
.venv/bin/python -m ruff check tests
.venv/bin/python -m ruff format --check tests
.venv/bin/python -m mypy tests
.venv/bin/python -m bandit --ignore-nosec -f json tests/*.py
npm audit --json
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt
npm run test:accessibility
git diff --check
```

The full security scanner refused stale reviewed source hashes before refresh;
all55 prior findings are retained and42 additional findings have individual
rationales. No security rule or dependency advisory was suppressed. New browser
checks first exposed asynchronous keyboard-scroll/focus test synchronization;
the corrected harness waits for actual scrolling and confirms file-input focus.
The prior-source full browser run passes33groups/25axe scans, preserving all
existing cases plus Python float/integer/Unicode import compatibility. It precedes
the final codepoint-length fix (browser.json records exact source hashes); final
exact-head CI runs the full harness. Final source passes63Node units and full
source-bound lint/format/types/security; unchanged11Python units and locked
dependency audits are reused.
Full scan/audit results and screenshots are here; all detailed axe scans remain
in ignored output/playwright and are collected by unchanged CI artifact controls.
Four new trace axe results are also retained here as compressed raw reports.
Independent review and CI for the proposed source are separate from author checks.

Independent source review found six compatibility/mutation defects; before-fix
regressions reproduced float/hash, mutation, raw-bound, DEL and codepoint failures.
Version/gas/revert-bloom consistency guards were included in that same batch.
All affected regressions now pass. Public independent-review.json records source
hashes and52additional independent numeric codec probes; it is software review,
not GitHub human approval, authenticity/EVM certification or a deployment claim.
