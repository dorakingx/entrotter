# Entrotter Python SDK

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

## End-to-end example

Run the bundled synthetic report entirely offline (no engine, API key, or chain
access):

```bash
PYTHONPATH=src python3 examples/roundtrip.py
```

```text
Verified fixture artifact: 83c48e06dc754a1066f159c03d9046f13091945ec062d5a77a999f9a95616d74
Hash integrity passed; this does not establish model correctness or financial safety.
```

The example verifies the v0.1 artifact, writes and reloads it from a temporary
directory, and prints its hash. The fixture is explicitly synthetic; a valid
hash proves byte integrity only, not that a model or financial result is
correct.

To make an optional request to an engine you run locally, provide an existing
scenario JSON and the local API origin:

```bash
PYTHONPATH=src python3 examples/roundtrip.py \
  --api http://127.0.0.1:8787 --scenario path/to/scenario.json
```

If the engine requires a bearer token, set `ENTROTTER_API_TOKEN` in the
environment. The SDK does not print or persist it. Run POST requests are never
automatically retried. The temporary output is removed when the example exits.
