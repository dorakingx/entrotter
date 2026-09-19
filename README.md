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
