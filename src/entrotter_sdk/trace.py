"""Offline signed-prefix inspection; integrity is not signature or EVM proof."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any

from .client import ClientError

MAX_TRACE_BYTES = 8 * 1024 * 1024
MAX_INPUT_BYTES = 256 * 1024
UINT256 = 2**256 - 1
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
RECEIPT_FIELDS = {
    "type",
    "status",
    "gasUsed",
    "cumulativeGasUsed",
    "effectiveGasPrice",
    "transactionIndex",
    "transactionHash",
    "from",
    "logsBloom",
    "to",
    "contractAddress",
    "logs",
}


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError("Inconsistent or unsupported trace data")


def _object(value: Any, fields: set[str]) -> dict:
    _require(type(value) is dict and set(value) == fields)
    return value


def _integer(value: Any, lower: int = 0, upper: int = UINT256) -> int:
    _require(type(value) is int and lower <= value <= upper)
    return value


def _array(value: Any, lower: int, upper: int) -> list:
    _require(type(value) is list and lower <= len(value) <= upper)
    return value


def _hex(value: Any, size: int | None = None, maximum: int = 65536) -> bytes:
    _require(
        type(value) is str and re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", value) is not None
    )
    length = (len(value) - 2) // 2
    _require(length <= maximum and (size is None or length == size))
    return bytes.fromhex(value[2:])


def _quantity(value: Any) -> int:
    _require(
        type(value) is str
        and re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})", value) is not None
    )
    return int(value, 16)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def _rlp(raw: bytes, start: int = 0, depth: int = 0) -> tuple[Any, int]:
    """Decode bounded canonical RLP, without hashes or signature recovery."""
    _require(depth <= 4 and start < len(raw))
    prefix = raw[start]
    if prefix < 128:
        return raw[start : start + 1], start + 1
    is_list = prefix >= 192
    offset = 192 if is_list else 128
    length = prefix - offset
    begin = start + 1
    if length > 55:
        width = length - 55
        _require(1 <= width <= 3 and begin + width <= len(raw) and raw[begin] != 0)
        length = int.from_bytes(raw[begin : begin + width], "big")
        _require(length >= 56)
        begin += width
    end = begin + length
    _require(end <= len(raw))
    if not is_list:
        _require(length != 1 or raw[begin] >= 128)
        return raw[begin:end], end
    values = []
    cursor = begin
    while cursor < end:
        value, cursor = _rlp(raw, cursor, depth + 1)
        _require(cursor <= end)
        values.append(value)
    return values, end


def _rlp_integer(value: Any) -> int:
    _require(type(value) is bytes and len(value) <= 32 and (not value or value[0] != 0))
    return int.from_bytes(value, "big")


def _signed_metadata(value: Any) -> tuple[int, int, str | None, int]:
    raw = _hex(value, maximum=131071)
    _require(bool(raw))
    kind = raw[0] if raw[0] < 128 else 0
    _require(kind in {0, 1, 2})
    body = raw[1:] if kind else raw
    fields, end = _rlp(body)
    fields = _array(
        fields,
        9 if kind == 0 else 11 if kind == 1 else 12,
        9 if kind == 0 else 11 if kind == 1 else 12,
    )
    _require(end == len(body))
    if kind:
        _require(_rlp_integer(fields[0]) == 1)
        nonce = _rlp_integer(fields[1])
        gas_index = 3 if kind == 1 else 4
        _require(_rlp_integer(fields[-3]) in {0, 1})
        access = _array(fields[-4], 0, 256)
        key_count = 0
        for entry in access:
            _array(entry, 2, 2)
            _require(type(entry[0]) is bytes and len(entry[0]) == 20)
            keys = _array(entry[1], 0, 256)
            key_count += len(keys)
            _require(key_count <= 256)
            for key in keys:
                _require(type(key) is bytes and len(key) == 32)
        if kind == 2:
            _require(_rlp_integer(fields[2]) <= _rlp_integer(fields[3]))
        else:
            _rlp_integer(fields[2])
    else:
        nonce = _rlp_integer(fields[0])
        gas_index = 2
        _rlp_integer(fields[1])
        _require(_rlp_integer(fields[-3]) in {27, 28, 37, 38})
    gas_limit = _rlp_integer(fields[gas_index])
    _require(21000 <= gas_limit <= 30000000)
    target = fields[gas_index + 1]
    _require(type(target) is bytes and len(target) in {0, 20})
    _rlp_integer(fields[gas_index + 2])
    calldata = fields[gas_index + 3]
    _require(type(calldata) is bytes and len(calldata) <= 65536)
    _require(1 <= _rlp_integer(fields[-2]) < SECP256K1_N)
    _require(1 <= _rlp_integer(fields[-1]) <= SECP256K1_N // 2)
    return kind, nonce, "0x" + target.hex() if target else None, gas_limit


def _receipt(value: Any, header: dict) -> dict:
    receipt = _object(value, RECEIPT_FIELDS)
    _require(
        receipt["type"] in ("0x0", "0x1", "0x2") and receipt["status"] in ("0x0", "0x1")
    )
    gas = _quantity(receipt["gasUsed"])
    cumulative = _quantity(receipt["cumulativeGasUsed"])
    _require(21000 <= gas <= cumulative <= header["gas_limit"])
    _quantity(receipt["effectiveGasPrice"])
    _quantity(receipt["transactionIndex"])
    for key, size in (("transactionHash", 32), ("from", 20), ("logsBloom", 256)):
        _hex(receipt[key], size)
    for key in ("to", "contractAddress"):
        if receipt[key] is not None:
            _hex(receipt[key], 20)
    _require(receipt["to"] is None or receipt["contractAddress"] is None)
    if receipt["status"] == "0x0":
        _require(
            receipt["logs"] == []
            and receipt["contractAddress"] is None
            and receipt["logsBloom"] == "0x" + "00" * 256
        )
    for log in _array(receipt["logs"], 0, 512):
        _object(log, {"address", "topics", "data"})
        _hex(log["address"], 20)
        for topic in _array(log["topics"], 0, 4):
            _hex(topic, 32)
        _hex(log["data"])
    _require(len(_canonical(receipt)) <= MAX_INPUT_BYTES)
    return receipt


def _receipt_binding(receipt: dict, source: dict, metadata: tuple) -> None:
    _require(receipt["transactionHash"].lower() == source["hash"].lower())
    _require(receipt["from"].lower() == source["sender"].lower())
    _require(_quantity(receipt["type"]) == metadata[0])
    target = receipt["to"].lower() if receipt["to"] is not None else None
    _require(target == metadata[2])
    _require(_quantity(receipt["gasUsed"]) <= metadata[3])


def _branch(
    value: Any,
    inputs: list,
    metadata: list,
    header: dict,
    skipped: list[int],
    anchors: dict[str, int],
) -> bool:
    branch = _object(value, {"anvil_version", "outcomes", "matches_original_receipts"})
    _require(
        type(branch["anvil_version"]) is str
        and 1 <= len(branch["anvil_version"]) <= 1000
    )
    _require(type(branch["matches_original_receipts"]) is bool)
    outcomes = _array(branch["outcomes"], len(inputs), len(inputs))
    expected = dict(anchors)
    cumulative = 0
    executed = 0
    matches = True
    for index, (outcome, source, signed) in enumerate(zip(outcomes, inputs, metadata)):
        _require(type(outcome) is dict)
        status = outcome.get("status")
        extra = (
            {"receipt", "differing_fields"}
            if status == "executed"
            else {"expected_nonce", "original_nonce"}
            if status == "nonce_conflict"
            else set()
        )
        _object(outcome, {"index", "hash", "status"} | extra)
        _require(_integer(outcome["index"], 0, 31) == index)
        _hex(outcome["hash"], 32)
        _require(outcome["hash"].lower() == source["hash"].lower())
        _require(
            type(status) is str
            and status
            in {"executed", "skipped", "nonce_conflict", "rejected", "not_mined"}
        )
        _require((status == "skipped") == (index in skipped))
        sender = source["sender"].lower()
        if status == "skipped":
            matches = False
            continue
        if status == "nonce_conflict":
            _require(_integer(outcome["original_nonce"]) == source["nonce"])
            _require(_integer(outcome["expected_nonce"]) == expected[sender])
            _require(source["nonce"] != expected[sender])
        else:
            _require(source["nonce"] == expected[sender])
            if status in {"executed", "not_mined"}:
                expected[sender] += 1
        if status == "executed":
            receipt = _receipt(outcome["receipt"], header)
            _receipt_binding(receipt, source, signed)
            cumulative += _quantity(receipt["gasUsed"])
            _require(_quantity(receipt["cumulativeGasUsed"]) == cumulative)
            _require(_quantity(receipt["transactionIndex"]) == executed)
            executed += 1
            differences = _array(outcome["differing_fields"], 0, 12)
            _require(all(type(f) is str and f in RECEIPT_FIELDS for f in differences))
            actual = {
                key
                for key in RECEIPT_FIELDS
                if receipt[key] != source["original_receipt"][key]
            }
            _require(
                len(set(differences)) == len(differences) and set(differences) == actual
            )
            matches = matches and not actual
        else:
            matches = False
    _require(branch["matches_original_receipts"] == matches)
    return matches


def _validate(report: dict) -> None:
    _object(
        report,
        {
            "trace_version",
            "execution_kind",
            "plan",
            "source",
            "baseline",
            "candidate",
            "baseline_verified",
            "runtime_seconds",
            "assumptions",
            "artifact_id",
        },
    )
    _require(
        report["trace_version"] == "0.1.0"
        and report["execution_kind"] == "canonical_transaction_prefix_replay"
    )
    _require(type(report["baseline_verified"]) is bool)
    runtime = report["runtime_seconds"]
    _require(type(runtime) in (int, float) and math.isfinite(runtime) and runtime >= 0)
    for assumption in _array(report["assumptions"], 1, 32):
        _require(type(assumption) is str and 1 <= len(assumption) <= 4000)
    plan = _object(
        report["plan"], {"trace_version", "source", "through_index", "skip_indices"}
    )
    _require(plan["trace_version"] == "0.1.0")
    spec = _object(plan["source"], {"chain_id", "block_number", "block_hash"})
    _require(_integer(spec["chain_id"]) == 1)
    block = _integer(spec["block_number"], 1, 2**64 - 1)
    _hex(spec["block_hash"], 32)
    count = _integer(plan["through_index"], 0, 31) + 1
    skips = _array(plan["skip_indices"], 0, count)
    for index in skips:
        _integer(index, 0, count - 1)
    _require(skips == sorted(set(skips)))
    source = _object(
        report["source"], {"parent", "header", "inputs", "block_transaction_count"}
    )
    parent = _object(source["parent"], {"chain_id", "block_number", "block_hash"})
    _require(
        _integer(parent["chain_id"]) == 1
        and _integer(parent["block_number"], 0, 2**64 - 2) == block - 1
    )
    _hex(parent["block_hash"], 32)
    header = _object(
        source["header"],
        {"timestamp", "gas_limit", "base_fee", "coinbase", "prevrandao"},
    )
    _integer(header["timestamp"], 1681338455, 1710338134)
    _integer(header["gas_limit"], 21000, 30000000)
    _integer(header["base_fee"])
    _hex(header["coinbase"], 20)
    _hex(header["prevrandao"], 32)
    _integer(source["block_transaction_count"], count, header["gas_limit"] // 21000)
    inputs = _array(source["inputs"], count, count)
    _require(len(_canonical(inputs)) <= MAX_INPUT_BYTES)
    metadata = []
    seen_hashes: set[str] = set()
    next_nonce: dict[str, int] = {}
    cumulative = 0
    for index, value in enumerate(inputs):
        tx = _object(
            value, {"index", "hash", "sender", "nonce", "raw", "original_receipt"}
        )
        _require(_integer(tx["index"], 0, 31) == index)
        _hex(tx["hash"], 32)
        _hex(tx["sender"], 20)
        _integer(tx["nonce"])
        _require(tx["hash"].lower() not in seen_hashes)
        seen_hashes.add(tx["hash"].lower())
        signed = _signed_metadata(tx["raw"])
        _require(tx["nonce"] == signed[1])
        sender = tx["sender"].lower()
        _require(sender not in next_nonce or tx["nonce"] == next_nonce[sender])
        next_nonce[sender] = tx["nonce"] + 1
        original = _receipt(tx["original_receipt"], header)
        _receipt_binding(original, tx, signed)
        cumulative += _quantity(original["gasUsed"])
        _require(
            _quantity(original["cumulativeGasUsed"]) == cumulative
            and _quantity(original["transactionIndex"]) == index
        )
        metadata.append(signed)
    baseline = _object(
        report["baseline"], {"anvil_version", "outcomes", "matches_original_receipts"}
    )
    baseline_outcomes = _array(baseline["outcomes"], count, count)
    anchors: dict[str, int] = {}
    for tx, outcome in zip(inputs, baseline_outcomes):
        _require(type(outcome) is dict)
        sender = tx["sender"].lower()
        if sender not in anchors:
            anchors[sender] = (
                _integer(outcome.get("expected_nonce"))
                if outcome.get("status") == "nonce_conflict"
                else tx["nonce"]
            )
    matched = _branch(baseline, inputs, metadata, header, [], anchors)
    _require(report["baseline_verified"] == matched)
    _branch(report["candidate"], inputs, metadata, header, skips, anchors)


def _checked(value: object) -> bytes:
    try:
        _require(type(value) is dict)
        encoded = _canonical(value)
        _require(len(encoded) <= MAX_TRACE_BYTES)
        report = json.loads(encoded)
        _validate(report)
        ident = report["artifact_id"]
        _require(
            type(ident) is str and re.fullmatch(r"[0-9a-f]{64}", ident) is not None
        )
        body = {key: data for key, data in report.items() if key != "artifact_id"}
        _require(hashlib.sha256(_canonical(body)).hexdigest() == ident)
        return encoded
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        raise ClientError(
            "Trace report failed version, hash, size or internal-consistency checks"
        ) from None


def verify_trace(value: object) -> bool:
    """Check integrity/internal consistency; not recovered sender or EVM truth."""
    try:
        _checked(value)
        return True
    except ClientError:
        return False


@dataclass(frozen=True)
class TraceLog:
    address: str
    topics: tuple[str, ...]
    data: str


@dataclass(frozen=True)
class TraceReceipt:
    transaction_type: int
    status: int
    gas_used: int
    cumulative_gas_used: int
    effective_gas_price: int
    transaction_index: int
    transaction_hash: str
    sender: str
    to: str | None
    contract_address: str | None
    logs_bloom: str
    logs: tuple[TraceLog, ...]


def _typed_receipt(receipt: dict) -> TraceReceipt:
    return TraceReceipt(
        _quantity(receipt["type"]),
        _quantity(receipt["status"]),
        _quantity(receipt["gasUsed"]),
        _quantity(receipt["cumulativeGasUsed"]),
        _quantity(receipt["effectiveGasPrice"]),
        _quantity(receipt["transactionIndex"]),
        receipt["transactionHash"],
        receipt["from"],
        receipt["to"],
        receipt["contractAddress"],
        receipt["logsBloom"],
        tuple(
            TraceLog(log["address"], tuple(log["topics"]), log["data"])
            for log in receipt["logs"]
        ),
    )


@dataclass(frozen=True)
class TraceOutcome:
    index: int
    hash: str
    status: str
    receipt: TraceReceipt | None
    differing_fields: tuple[str, ...]
    expected_nonce: int | None
    original_nonce: int | None


def _typed_outcome(outcome: dict) -> TraceOutcome:
    return TraceOutcome(
        outcome["index"],
        outcome["hash"],
        outcome["status"],
        _typed_receipt(outcome["receipt"]) if outcome["status"] == "executed" else None,
        tuple(outcome.get("differing_fields", [])),
        outcome.get("expected_nonce"),
        outcome.get("original_nonce"),
    )


@dataclass(frozen=True)
class TraceTransaction:
    index: int
    hash: str
    sender: str
    nonce: int
    raw: str
    original_receipt: TraceReceipt
    baseline: TraceOutcome
    candidate: TraceOutcome


@dataclass(frozen=True, init=False)
class TraceResult:
    _encoded: bytes = field(repr=False)

    def __init__(self, value: object):
        object.__setattr__(self, "_encoded", _checked(value))

    @classmethod
    def parse(cls, value: object) -> TraceResult:
        return cls(value)

    @property
    def report(self) -> dict:
        """Return a fresh copy; caller mutations cannot alter validated contents."""
        return json.loads(self._encoded)

    @property
    def artifact_id(self) -> str:
        return self.report["artifact_id"]

    @property
    def baseline_verified(self) -> bool:
        return self.report["baseline_verified"]

    @property
    def runtime_seconds(self) -> float:
        return self.report["runtime_seconds"]

    @property
    def transactions(self) -> tuple[TraceTransaction, ...]:
        report = self.report
        return tuple(
            TraceTransaction(
                tx["index"],
                tx["hash"],
                tx["sender"],
                tx["nonce"],
                tx["raw"],
                _typed_receipt(tx["original_receipt"]),
                _typed_outcome(baseline),
                _typed_outcome(candidate),
            )
            for tx, baseline, candidate in zip(
                report["source"]["inputs"],
                report["baseline"]["outcomes"],
                report["candidate"]["outcomes"],
            )
        )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    value: dict[str, Any] = {}
    for key, item in pairs:
        _require(key not in value)
        value[key] = item
    return value


def load_trace(path: str | Path) -> TraceResult:
    """Read a bounded regular JSON file offline; reject duplicate object keys."""
    try:
        with os.fdopen(
            os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)), "rb"
        ) as source:
            _require(stat.S_ISREG(os.fstat(source.fileno()).st_mode))
            raw = source.read(MAX_TRACE_BYTES + 1)
        _require(len(raw) <= MAX_TRACE_BYTES)
        return TraceResult.parse(json.loads(raw, object_pairs_hook=_unique_object))
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        raise ClientError(
            "Trace input must be a regular JSON file within 8 MiB with unique object keys"
        ) from None
