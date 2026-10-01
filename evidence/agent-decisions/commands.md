# Recorded agent evidence verification

Use existing Node22.23.1 (repository requires Node20.19+) and the installed,
locked developer tools. No runtime dependency, model, archive RPC or Docker is used.

```bash
npm test
npm run lint
npm run format:check
npm run typecheck
npm run security
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m ruff check tests
.venv/bin/python -m ruff format --check tests
.venv/bin/python -m mypy tests
.venv/bin/python -m bandit --ignore-nosec tests/test_site.py
A11Y_OUTPUT=output/playwright/agent-evidence-final-layout npm run test:accessibility
```

The four hash-resealed contradictions are individual Node regression cases.
Browser imports also reseal request/report digests and verify failure clears
all agent rows/provenance/downloads, followed by valid recovery without uploads.
The final browser runner selects five public samples at1280/390/320 CSS pixels
and captures agent evidence screenshots. Every raw axe result is retained;
incomplete contrast and the separate opaque-color calculation stay explicit.

Compatibility checks load production app.js in Node vm with network-disabled
document/fetch stubs. For the three original agent-local reports and each
causal-v1/causal-uniswap report containing an agent, run checkHash(report) and
agentViewModel(report). All12 original input hashes/IDs and row counts are in
compatibility.json. This verifies existing display inputs; it is not a new
chain/model evaluation, economic validation or recording authentication.

Current-head CI links and downloaded source/dependency/browser verification will
be recorded in the PR without an extra source commit solely for CI results.
