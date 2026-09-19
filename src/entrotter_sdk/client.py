"""Standard-library HTTP client. A run POST is never retried automatically."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

class ClientError(RuntimeError):
    pass

def verify(report: dict) -> bool:
    if not isinstance(report, dict) or report.get("schema_version") != "0.1.0":
        return False
    ident = report.get("artifact_id")
    if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{64}", ident):
        return False
    try:
        body = {k: v for k, v in report.items() if k != "artifact_id"}
        data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
        return hashlib.sha256(data).hexdigest() == ident
    except (ValueError, TypeError, RecursionError):
        return False

@dataclass(frozen=True)
class RunResult:
    artifact_id: str
    mode: str
    report: dict

    @classmethod
    def parse(cls, value: dict) -> "RunResult":
        if not verify(value):
            raise ClientError("Result is missing a valid content hash or schema version")
        if value.get("mode") not in {"fixture", "evm-local", "evm-fork"}:
            raise ClientError("Unknown result mode")
        if not all(isinstance(value.get(x), dict) for x in ["scenario", "baseline", "candidate", "comparison"]):
            raise ClientError("Malformed result envelope")
        return cls(value["artifact_id"], value["mode"], value)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Client:
    def __init__(self, base_url: str = "http://127.0.0.1:8787", *, token: str | None = None, timeout: float = 300):
        url = urlsplit(base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            raise ClientError("Supply an HTTP(S) API URL without embedded credentials")
        if url.query or url.fragment or url.path not in {"", "/"}:
            raise ClientError("API URL must be an origin, without a path, query or fragment")
        if url.scheme != "https" and url.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ClientError("Plain HTTP is only allowed on loopback")
        if not 0 < timeout <= 600:
            raise ClientError("timeout must be within 0-600 seconds")
        self.base_url = base_url.rstrip("/")
        self.token, self.timeout = token, timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode()
            if len(data) > 262144:
                raise ClientError("Scenario exceeds 256 KiB")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            req = Request(self.base_url + path, data=data, headers=headers, method=method)
            with self.opener.open(req, timeout=self.timeout) as r:
                content = r.read(16 * 1024 * 1024 + 1)
            if len(content) > 16 * 1024 * 1024:
                raise ClientError("Result exceeds the 16 MiB client limit")
            result = json.loads(content)
            if not isinstance(result, dict): raise ClientError("Invalid JSON response")
            return result
        except HTTPError as e:
            raise ClientError(f"Engine returned HTTP {e.code}; POST requests are not automatically retried") from None
        except (URLError, OSError, ValueError):
            raise ClientError("Engine is unavailable or returned invalid JSON") from None

    def health(self) -> dict:
        return self._request("GET", "/health")

    def run(self, scenario: dict) -> RunResult:
        return RunResult.parse(self._request("POST", "/v1/runs", scenario))

    def get(self, artifact_id: str) -> RunResult:
        if not re.fullmatch(r"[0-9a-f]{64}", artifact_id):
            raise ClientError("artifact_id must be a SHA-256 hex digest")
        result = RunResult.parse(self._request("GET", f"/v1/runs/{artifact_id}"))
        if result.artifact_id != artifact_id:
            raise ClientError("Server returned a different artifact")
        return result
