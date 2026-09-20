# Entrotter Python SDK

[Workspace setup](https://github.com/entrotter/entrotter#quick-start-without-dependencies-or-an-api-key) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

A Python 3.11+ standard-library client for the Entrotter local API. MIT licensed.
No API credential or chain access is needed for the unit tests.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```python
import json
from entrotter_sdk import Client, ClientError, verify

client = Client("http://127.0.0.1:8787")
print(client.health())
with open("scenario.json") as f:
    result = client.run(json.load(f))
assert verify(result.report)
assert client.get(result.artifact_id).artifact_id == result.artifact_id
```

The client verifies content hashes, refuses plaintext non-loopback URLs,
rejects URLs with embedded credentials, disables redirects, limits response
size and never automatically retries an experiment POST. Use `token=` when
ENTROTTER_API_TOKEN is configured on the engine. The SDK supports HTTPS for a
future properly secured service, but no such public service is currently shipped.

This package has not been published on PyPI. Install this source checkout with
`python3 -m pip install --no-deps -e .` or use the workspace bootstrap. Do not
install a similarly named registry package. Integrity does not establish
model correctness or financial safety.

## Quality checks

The CI quality job checks every production Python file under `src/` and `scripts/`
with Ruff lint/format, mypy including unannotated function bodies, and all default
Bandit rules with `--ignore-nosec`. Any finding fails; the complete report is
retained. A second check rejects empty/partial scans or skipped rules. This is
static analysis, not a proof that the client or remote engine is secure.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: --index-url https://pypi.org/simple -r requirements-quality.txt
.venv/bin/python -m pip check
.venv/bin/python -m ruff check src scripts
.venv/bin/python -m ruff format --check src scripts
.venv/bin/python -m mypy src scripts
mkdir -p .quality
.venv/bin/python -m bandit --ignore-nosec -r src scripts -f json -o .quality/bandit.json
.venv/bin/python scripts/check_security.py
.venv/bin/python scripts/check_dependency_manifest.py
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r requirements-quality.txt --progress-spinner off -f json -o .quality/dependencies.json
.venv/bin/python -m build --no-isolation --wheel --outdir .quality/wheels
```

All 42 Python tool/build packages are version/hash locked; runtime dependencies
remain empty. The dependency gate rejects unpinned or unaudited build/runtime/
optional requirements. Advisory lookup errors fail; no advisories are ignored.
The Python runtime and operating system are outside this Python-package audit.
The workflow installs the wheel into a fresh venv with `--no-index --no-deps` and
checks its import and bundled `py.typed` marker in isolated Python mode. It does
not publish packages. The marker exposes existing type hints to consumers;
normal mypy checks do not establish full static typing of arbitrary JSON.

To update tools, edit `requirements-quality.in`, regenerate the complete hashed
lock with the pinned `pip-compile`, and rerun the quality job and unit matrix.
GitHub Actions use immutable commit IDs; full scan/audit reports and the wheel
are uploaded for review. Code examples and the real API are verified separately.
