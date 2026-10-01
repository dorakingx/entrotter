#!/usr/bin/env python3
"""Standalone stdlib/JSON-RPC implementation of the frozen 19M paired task.

No Entrotter runtime imports. This deliberately supports one audited input only;
there is no general RPC endpoint, code loader, wallet key or agent execution API.
"""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

CASE = (
    Path(__file__).resolve().parents[2]
    / "scenarios/benchmarks/causal-v1/cases/19000000.json"
)
CASE_SHA256 = "2059263c6e3eb9dfd8ef3549ef82f1e070225dcb5430c6301349da51d4a4d02f"


class DirectError(RuntimeError):
    pass


class Rejected(DirectError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ReadOnlyRPC:
    methods = {"eth_chainId", "eth_getBlockByNumber"}

    def __init__(self, url):
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise DirectError("Invalid archive URL")
        self.url = url
        self.opener = build_opener(ProxyHandler({}), NoRedirect())
        self.identifier = 0

    def call(self, method, params=None):
        if method not in self.methods:
            raise DirectError("Method forbidden on this transport")
        self.identifier += 1
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self.identifier,
                "method": method,
                "params": params or [],
            }
        ).encode()
        req = Request(
            self.url,
            body,
            {"Content-Type": "application/json", "User-Agent": "Entrotter/0.1.0"},
        )
        try:
            with self.opener.open(req, timeout=10) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise DirectError("RPC response too large")
            result = json.loads(raw)
        except (URLError, OSError, ValueError):
            raise DirectError("RPC transport/JSON failure; no fallback") from None
        if not isinstance(result, dict) or result.get("id") != self.identifier:
            raise DirectError("Invalid RPC response identity")
        if "error" in result:
            raise Rejected("RPC rejected the request")
        if "result" not in result:
            raise DirectError("Missing RPC result")
        return result["result"]


class OwnedRPC(ReadOnlyRPC):
    methods = ReadOnlyRPC.methods | {
        "web3_clientVersion",
        "eth_getBalance",
        "eth_call",
        "anvil_setBalance",
        "anvil_impersonateAccount",
        "anvil_stopImpersonatingAccount",
        "evm_setNextBlockTimestamp",
        "eth_sendTransaction",
        "evm_mine",
        "eth_getTransactionReceipt",
    }

    def __init__(self, port):
        if type(port) is not int or not 1 <= port <= 65535:
            raise DirectError("Owned node port must be an integer")
        super().__init__(f"http://127.0.0.1:{port}")


def load_case():
    raw = CASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CASE_SHA256:
        raise DirectError("This comparison only admits the frozen 19M scenario bytes")
    return json.loads(raw)


@contextmanager
def fork(source, url):
    binary = shutil.which("anvil")
    if not binary:
        raise DirectError("Anvil is required")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [
            binary,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--chain-id",
            "31337",
            "--no-mining",
            "--silent",
            "--accounts",
            "0",
            "--memory-limit",
            "67108864",
            "--fork-url",
            url,
            "--fork-block-number",
            str(source["block_number"]),
            "--no-storage-caching",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    rpc = OwnedRPC(port)
    try:
        deadline = time.monotonic() + 25
        while True:
            if process.poll() is not None or time.monotonic() > deadline:
                raise DirectError("Owned Anvil startup failed or timed out")
            try:
                if "anvil" not in rpc.call("web3_clientVersion").lower() or rpc.call(
                    "eth_chainId"
                ) != hex(31337):
                    raise DirectError("Unexpected owned node identity")
                break
            except DirectError:
                time.sleep(0.1)
        head = rpc.call("eth_getBlockByNumber", ["latest", False])
        if head["hash"].lower() != source["block_hash"].lower():
            raise DirectError("Local fork source hash differs")
        yield rpc, int(head["timestamp"], 16)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def uint_call(rpc, address, data):
    value = rpc.call("eth_call", [{"to": address, "data": data}, "latest"])
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        raise DirectError("Token observation must be one ABI word")
    return int(value, 16)


def balances(rpc, actor, tokens):
    return {
        "native_wei": str(int(rpc.call("eth_getBalance", [actor, "latest"]), 16)),
        "tokens_raw": {
            t["address"]: str(
                uint_call(rpc, t["address"], "0x70a08231" + actor[2:].zfill(64))
            )
            for t in tokens
        },
    }


def run_direct():
    scenario = load_case()
    url = os.environ.get("ENTROTTER_RPC_URL")
    if not url:
        raise DirectError("ENTROTTER_RPC_URL is required; no fork performed")
    upstream = ReadOnlyRPC(url)
    source = scenario["source"]
    if int(upstream.call("eth_chainId"), 16) != source["chain_id"]:
        raise DirectError("Wrong upstream chain")
    header = upstream.call("eth_getBlockByNumber", [hex(source["block_number"]), False])
    if (
        header["hash"].lower() != source["block_hash"].lower()
        or int(header["number"], 16) != source["block_number"]
    ):
        raise DirectError("Wrong upstream source block")
    result: dict[str, Any] = {
        "source": {**source, "timestamp": int(header["timestamp"], 16)},
        "branches": [],
    }
    for policy in ["execute", "preflight"]:
        deadline = time.monotonic() + 120
        with fork(source, url) as (rpc, timestamp):
            actor, tokens = scenario["actor"], scenario["tracked_tokens"]
            rpc.call(
                "anvil_setBalance", [actor, hex(int(scenario["actor_balance_wei"]))]
            )
            rpc.call("anvil_impersonateAccount", [actor])
            for token in tokens:
                if uint_call(rpc, token["address"], "0x313ce567") != token["decimals"]:
                    raise DirectError("Token decimals differ from pin")
            initial = balances(rpc, actor, tokens)
            steps, gas, cost = [], 0, 0
            for index, slot in enumerate(scenario["steps"]):
                if time.monotonic() > deadline:
                    raise DirectError("Branch time limit exceeded")
                action = slot["candidate"]
                transaction = {
                    "from": actor,
                    "to": action["to"],
                    "data": action.get("data", "0x"),
                    "value": hex(int(action.get("value_wei", "0"))),
                    "gas": hex(action["gas"]),
                }
                execute = True
                if policy == "preflight" and index == 2:
                    try:
                        rpc.call("eth_call", [transaction, "latest"])
                        execute = action["gas"] <= 500000
                    except Rejected:
                        execute = False
                rpc.call("evm_setNextBlockTimestamp", [timestamp + 12 * (index + 1)])
                status, receipt, tx_hash = "noop", None, None
                if execute:
                    try:
                        tx_hash = rpc.call("eth_sendTransaction", [transaction])
                    except Rejected:
                        status = "rejected"
                rpc.call("evm_mine")
                if tx_hash is not None:
                    receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
                    if receipt is None:
                        raise DirectError("Missing mined receipt")
                    status = (
                        "success" if int(receipt["status"], 16) == 1 else "reverted"
                    )
                    used = int(receipt["gasUsed"], 16)
                    gas += used
                    cost += used * int(receipt["effectiveGasPrice"], 16)
                steps.append(
                    {
                        "status": status,
                        "receipt": receipt,
                        "balances": balances(rpc, actor, tokens),
                    }
                )
            final = balances(rpc, actor, tokens)
            rpc.call("anvil_stopImpersonatingAccount", [actor])
            result["branches"].append(
                {
                    "policy": policy,
                    "initial": initial,
                    "steps": steps,
                    "final": final,
                    "gas_used": str(gas),
                    "gas_cost_wei": str(cost),
                }
            )
    return result


if __name__ == "__main__":
    print(json.dumps(run_direct(), indent=2))
