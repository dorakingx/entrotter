"""Two distinct transports: read-only upstream and private local Anvil."""

from __future__ import annotations
import json
import socket
import ssl
from http.client import HTTPException
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import URLError, HTTPError


FAILURE_CODES = frozenset(
    {
        "unknown",
        "invalid_request",
        "timeout",
        "http_error",
        "connection_error",
        "tls_error",
        "invalid_response",
        "response_too_large",
        "rejected",
        "transport_error",
    }
)


class RPCError(RuntimeError):
    """Compatible exception with finite, provider-independent diagnostics."""

    __slots__ = ("_rpc_code", "_rpc_method")

    def __init__(self, *args, code="unknown", method=None):
        super().__init__(*args)
        RPCError.__dict__["_rpc_code"].__set__(self, code)
        RPCError.__dict__["_rpc_method"].__set__(self, method)

    @property
    def code(self):
        return safe_diagnostics(self)["code"]

    @property
    def method(self):
        return safe_diagnostics(self)["method"]

    @property
    def diagnostics(self):
        return safe_diagnostics(self)


def safe_diagnostics(error: RPCError) -> dict[str, str | None]:
    """Read base slots, ignoring forged subclass properties and untrusted values."""
    try:
        code = RPCError.__dict__["_rpc_code"].__get__(error, RPCError)
        method = RPCError.__dict__["_rpc_method"].__get__(error, RPCError)
    except (AttributeError, TypeError):
        code, method = "unknown", None
    return {
        "code": code if type(code) is str and code in FAILURE_CODES else "unknown",
        "method": method
        if type(method) is str and method in (LOCAL | OwnedTraceRPC.LOCAL_METHODS)
        else None,
    }


def transport_code(error: BaseException) -> str:
    """Use known types only: text, URLs, args and provider codes are not diagnostics."""
    if isinstance(error, HTTPError):
        return "http_error"
    if isinstance(error, TimeoutError):
        return "timeout"
    if isinstance(error, ssl.SSLError):
        return "tls_error"
    if isinstance(error, (ConnectionError, socket.gaierror)):
        return "connection_error"
    if isinstance(error, URLError):
        try:
            reason = error.reason
        except Exception:
            return "transport_error"
        if isinstance(reason, TimeoutError):
            return "timeout"
        if isinstance(reason, ssl.SSLError):
            return "tls_error"
        if isinstance(reason, (ConnectionError, socket.gaierror)):
            return "connection_error"
    return "transport_error"


class RPCRejected(RPCError):
    """An explicit JSON-RPC rejection, distinct from a transport timeout."""

    pass


READ_ONLY = {
    "eth_chainId",
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_getBalance",
    "eth_getCode",
    "eth_getTransactionReceipt",
    "eth_call",
}
LOCAL = READ_ONLY | {
    "web3_clientVersion",
    "eth_sendTransaction",
    "eth_getTransactionCount",
    "anvil_setBalance",
    "anvil_setCode",
    "anvil_impersonateAccount",
    "anvil_stopImpersonatingAccount",
    "evm_mine",
    "evm_setNextBlockTimestamp",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RPC:
    LOCAL_METHODS = LOCAL

    def __init__(self, url: str, *, local: bool = False, timeout: float = 10):
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RPCError("RPC requires an HTTP(S) URL", code="invalid_request")
        if parsed.username or parsed.password or parsed.fragment:
            raise RPCError(
                "RPC credentials must not use URL user-info; fragments are unsupported",
                code="invalid_request",
            )
        if local and (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"):
            raise RPCError(
                "Write-capable RPC must be a loopback Anvil instance owned by this run",
                code="invalid_request",
            )
        self.url, self.local, self.timeout = url, local, timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())
        self.next_id = 0

    def call(self, method: str, params: list | None = None):
        if type(method) is not str or method not in (
            self.LOCAL_METHODS if self.local else READ_ONLY
        ):
            raise RPCError(
                "RPC method is not allowed on this transport", code="invalid_request"
            )
        self.next_id += 1
        req_id = self.next_id
        body = json.dumps(
            {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or []}
        ).encode()
        req = Request(
            self.url,
            body,
            {"Content-Type": "application/json", "User-Agent": "Entrotter/0.1.0"},
            method="POST",
        )
        try:
            with self.opener.open(req, timeout=self.timeout) as response:
                expected_length = getattr(response, "length", None)
                raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise RPCError(
                    "RPC response too large", code="response_too_large", method=method
                )
            if (
                type(expected_length) is int
                and expected_length >= 0
                and len(raw) != expected_length
            ):
                raise RPCError(
                    "Invalid RPC response", code="invalid_response", method=method
                )
            result = json.loads(raw)
            if not isinstance(result, dict) or result.get("id") != req_id:
                raise RPCError(
                    "Invalid RPC response", code="invalid_response", method=method
                )
            if "error" in result:
                # Every provider field is untrusted, including nominally numeric codes.
                # Keep only the locally allowlisted method in user-facing diagnostics.
                raise RPCRejected(
                    f"RPC rejected {method}", code="rejected", method=method
                )
            if "result" not in result:
                raise RPCError(
                    "RPC response has no result", code="invalid_response", method=method
                )
            return result["result"]
        except RPCError:
            raise
        except (URLError, HTTPError, TimeoutError, OSError) as error:
            failure = RPCError(
                f"RPC request failed for {method}; check connectivity and archive access",
                code=transport_code(error),
                method=method,
            )
        except (ValueError, RecursionError, HTTPException):
            failure = RPCError(
                "Invalid RPC response", code="invalid_response", method=method
            )
        # Raise outside the private exception handler so neither message nor context
        # retains the provider's original exception/URL/response text.
        raise failure from None


class OwnedTraceRPC(RPC):
    """Signed replay/header writes for a node owned by AnvilSession only.

    Normal RPC, including normal local execution, still forbids raw broadcast.
    No impersonation, balance replacement or code replacement is permitted here.
    """

    LOCAL_METHODS = READ_ONLY | {
        "web3_clientVersion",
        "eth_getTransactionCount",
        "eth_sendRawTransaction",
        "evm_mine",
        "evm_setNextBlockTimestamp",
        "evm_setBlockGasLimit",
        "anvil_setCoinbase",
        "anvil_setNextBlockBaseFeePerGas",
        "anvil_setNextBlockPrevRandao",
    }

    def __init__(self, url: str):
        super().__init__(url, local=True, timeout=10)
