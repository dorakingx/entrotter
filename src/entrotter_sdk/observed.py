"""Offline fixed-profile price observations; no engine, HTTP or chain execution.

The fixed ABI/coverage/classifier contract follows engine40 consumer_observations.
Content integrity and reported read-only dependence do not prove EVM truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from .client import ClientError
from .trace import (
    MAX_TRACE_BYTES,
    TraceResult,
    _canonical,
    _hex,
    _require,
    _unique_object,
)

OBSERVATION_VERSION = "0.1.0"
PROFILE = "aave-v3-ethereum-weth-price"
ZERO = "0x" + "00" * 20
UNIT = 100_000_000
MAX_OBSERVATION_BYTES = 65536
PHASES = [
    (branch, phase)
    for branch in ("baseline", "candidate")
    for phase in ("before", "after")
]
SELECTORS = {
    "source": "0x92bf2be0",
    "price": "0xb3596f07",
    "base_currency": "0xe19f4700",
    "base_unit": "0x8c89b64f",
    "aggregator": "0x245a7bfc",
    "latest_round_data": "0xfeaf968c",
}
QUERIES = {"head", "oracle_code", "source_code", *SELECTORS}
CATEGORIES = {"rpc_error", "invalid_response", "unavailable"}
FAILURE_CODES = {
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
SCOPE = (
    "Owned-node read-only price views only; no signed consumer action, strategy, "
    "loan/liquidation/trade, benefit/profit, deployed-code/provider authentication, "
    "full-block/opcode/state-root proof or whole-process native sandbox."
)


def _word(value: Any) -> bytes:
    return _hex(value, size=32)


def _address(value: Any) -> str:
    raw = _word(value)
    if raw[:12] != bytes(12):
        raise ValueError("Invalid observation address ABI")
    return "0x" + raw[12:].hex()


def _uint(value: Any) -> int:
    return int.from_bytes(_word(value), "big")


def _round(value: Any) -> dict:
    raw = _hex(value, size=160)
    words = [int.from_bytes(raw[i : i + 32], "big") for i in range(0, 160, 32)]
    if words[0] >= 2**80 or words[4] >= 2**80 or words[2] > words[3]:
        raise ValueError("Invalid observation round ABI")
    answer = words[1] - 2**256 if words[1] >= 2**255 else words[1]
    return dict(
        zip(
            ("round_id", "answer", "started_at", "updated_at", "answered_in_round"),
            (words[0], answer, *words[2:]),
        )
    )


def _decode(name: str, value: Any) -> Any:
    if name in {"source", "base_currency", "aggregator"}:
        return _address(value)
    if name == "latest_round_data":
        return _round(value)
    return _uint(value)


def _classification(rows: list[dict], report: dict) -> dict:
    reasons: set[str] = set()
    decoded = []
    for row in rows:
        values = {name: _decode(name, value) for name, value in row["raw"].items()}
        decoded.append(values)
        if row["errors"] or set(values) != set(SELECTORS) or row["head"] is None:
            reasons.add("incomplete_views")
        if values.get("source", ZERO) == ZERO:
            reasons.add("source_unavailable")
        if values.get("base_currency") != ZERO or values.get("base_unit") != UNIT:
            reasons.add("unsupported_currency_or_unit")
        feed = values.get("latest_round_data", {})
        if (
            feed.get("answer", 0) <= 0
            or feed.get("round_id", 0) <= 0
            or feed.get("updated_at", 0) <= 0
            or feed.get("answered_in_round", 0) < feed.get("round_id", 0)
            or values.get("price") != feed.get("answer")
        ):
            reasons.add("feed_price_unproven")
        head = row["head"]
        if head is None or any(
            feed.get(field, 0) > head["timestamp"]
            for field in ("started_at", "updated_at")
        ):
            reasons.add("feed_timestamp_unproven")
        if values.get("aggregator", ZERO) == ZERO:
            reasons.add("aggregator_unavailable")
        if set(row["code"]) != {"oracle_code", "source_code"} or any(
            value["bytes"] == 0 for value in row["code"].values()
        ):
            reasons.add("code_unavailable")
    if len(rows) != 4:
        reasons.add("incomplete_phases")
    if len(rows) == 4:
        if any(rows[i]["code"] != rows[0]["code"] for i in range(1, 4)):
            reasons.add("code_identity_changed")
        if any(
            value.get("aggregator") != decoded[0].get("aggregator")
            for value in decoded[1:]
        ):
            reasons.add("aggregator_changed")
        if any(
            value.get("source") != decoded[0].get("source") for value in decoded[1:]
        ):
            reasons.add("source_changed")
        if decoded[0] != decoded[2]:
            reasons.add("initial_views_differ")
        if rows[0]["head"] != rows[2]["head"]:
            reasons.add("initial_heads_differ")
        # Receipt equality is not state equivalence; actual four views are retained.
    complete = not reasons
    return {
        "complete_price_views": complete,
        "baseline_receipts_verified": report["baseline_verified"],
        "unproven_reasons": sorted(reasons),
        "baseline_price": decoded[1].get("price") if complete else None,
        "candidate_price": decoded[3].get("price") if complete else None,
        "price_difference": decoded[3]["price"] - decoded[1]["price"]
        if complete
        else None,
    }


def _validate_rows(rows: Any, report: dict) -> None:
    if (
        not isinstance(rows, list)
        or len(rows) != 4
        or len(_canonical(rows)) > MAX_OBSERVATION_BYTES
    ):
        raise ValueError("Invalid observation row bound")
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "branch",
            "phase",
            "head",
            "raw",
            "code",
            "errors",
        }:
            raise ValueError("Invalid observation row shape")
        if (row["branch"], row["phase"]) != PHASES[i]:
            raise ValueError("Invalid observation phase binding")
        if not isinstance(row["raw"], dict) or not set(row["raw"]) <= set(SELECTORS):
            raise ValueError("Invalid observation ABI shape")
        for name, value in row["raw"].items():
            _decode(name, value)
        if not isinstance(row["code"], dict) or not set(row["code"]) <= {
            "oracle_code",
            "source_code",
        }:
            raise ValueError("Invalid observation code shape")
        for identity in row["code"].values():
            if (
                not isinstance(identity, dict)
                or set(identity) != {"bytes", "sha256"}
                or type(identity["bytes"]) is not int
                or not 0 <= identity["bytes"] <= MAX_OBSERVATION_BYTES
                or type(identity["sha256"]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None
            ):
                raise ValueError("Invalid observation code identity")
        errors = row["errors"]
        if not isinstance(errors, list) or len(errors) > 9:
            raise ValueError("Invalid observation error bound")
        failed = set()
        for error in errors:
            if (
                not isinstance(error, dict)
                or set(error)
                not in ({"query", "category"}, {"query", "category", "diagnostics"})
                or type(error["query"]) is not str
                or error["query"] not in QUERIES
                or error["query"] in failed
                or type(error["category"]) is not str
                or error["category"] not in CATEGORIES
            ):
                raise ValueError("Invalid observation diagnostic")
            failed.add(error["query"])
            if error["category"] == "rpc_error":
                diag = error.get("diagnostics")
                expected = (
                    "eth_getBlockByNumber"
                    if error["query"] == "head"
                    else "eth_getCode"
                    if error["query"].endswith("_code")
                    else "eth_call"
                )
                if (
                    not isinstance(diag, dict)
                    or set(diag) != {"code", "method"}
                    or type(diag["code"]) is not str
                    or diag["code"] not in FAILURE_CODES
                    or diag["method"] not in {expected, None}
                ):
                    raise ValueError("Invalid observation RPC metadata")
            elif "diagnostics" in error:
                raise ValueError("Unexpected observation RPC metadata")
        available = set(row["raw"]) | set(row["code"])
        if row["head"] is not None:
            head = row["head"]
            if (
                not isinstance(head, dict)
                or set(head) != {"number", "hash", "timestamp"}
                or type(head["number"]) is not int
                or type(head["timestamp"]) is not int
                or not 0 <= head["timestamp"] < 2**64
            ):
                raise ValueError("Invalid observation head")
            _hex(head["hash"], size=32)
            expected_number = report["source"]["parent"]["block_number"] + (i % 2)
            if head["number"] != expected_number or (
                i % 2 == 0 and head["hash"] != report["source"]["parent"]["block_hash"]
            ):
                raise ValueError("Observation parent/head binding differs")
            if (
                i % 2 == 1
                and head["timestamp"] != report["source"]["header"]["timestamp"]
            ):
                raise ValueError("Observation post timestamp differs")
            available.add("head")
        if available & failed or available | failed != QUERIES:
            raise ValueError("Observation query coverage differs")


def _checked_observed(value: object) -> bytes:
    try:
        _require(type(value) is dict)
        encoded = _canonical(value)
        _require(len(encoded) <= MAX_TRACE_BYTES)
        report = json.loads(encoded)
        _require(
            set(report)
            == {
                "observation_version",
                "profile",
                "trace_report",
                "trace_artifact_id",
                "observations",
                "classification",
                "scope",
                "artifact_id",
            }
        )
        _require(
            report["observation_version"] == OBSERVATION_VERSION
            and report["profile"] == PROFILE
            and report["scope"] == SCOPE
        )
        trace = TraceResult.parse(report["trace_report"])
        _require(report["trace_artifact_id"] == trace.artifact_id)
        _validate_rows(report["observations"], report["trace_report"])
        _require(
            _canonical(report["classification"])
            == _canonical(
                _classification(report["observations"], report["trace_report"])
            )
        )
        ident = report["artifact_id"]
        _require(
            type(ident) is str and re.fullmatch(r"[0-9a-f]{64}", ident) is not None
        )
        body = {key: data for key, data in report.items() if key != "artifact_id"}
        _require(hashlib.sha256(_canonical(body)).hexdigest() == ident)
        return encoded
    except (
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        OverflowError,
        ClientError,
    ):
        raise ClientError(
            "Observed trace report failed version, hash, size or internal-consistency checks"
        ) from None


def verify_observed_trace(value: object) -> bool:
    """Validate recorded wrapper/ABI/bindings; no provider or execution proof."""
    try:
        _checked_observed(value)
        return True
    except ClientError:
        return False


@dataclass(frozen=True)
class ObservationHead:
    number: int
    hash: str
    timestamp: int


@dataclass(frozen=True)
class ObservationCode:
    bytes: int
    sha256: str


@dataclass(frozen=True)
class ObservationError:
    query: str
    category: str
    code: str | None = None
    method: str | None = None


@dataclass(frozen=True)
class PriceRound:
    round_id: int
    answer: int
    started_at: int
    updated_at: int
    answered_in_round: int


@dataclass(frozen=True)
class PriceObservation:
    branch: str
    phase: str
    head: ObservationHead | None
    source: str | None
    price: int | None
    base_currency: str | None
    base_unit: int | None
    aggregator: str | None
    latest_round_data: PriceRound | None
    oracle_code: ObservationCode | None
    source_code: ObservationCode | None
    errors: tuple[ObservationError, ...]


@dataclass(frozen=True)
class PriceClassification:
    complete_price_views: bool
    baseline_receipts_verified: bool
    unproven_reasons: tuple[str, ...]
    baseline_price: int | None
    candidate_price: int | None
    price_difference: int | None


def _typed_observation(row: dict) -> PriceObservation:
    values = {name: _decode(name, value) for name, value in row["raw"].items()}
    head = ObservationHead(**row["head"]) if row["head"] is not None else None
    feed = (
        PriceRound(**values["latest_round_data"])
        if "latest_round_data" in values
        else None
    )
    oracle = (
        ObservationCode(**row["code"]["oracle_code"])
        if "oracle_code" in row["code"]
        else None
    )
    source = (
        ObservationCode(**row["code"]["source_code"])
        if "source_code" in row["code"]
        else None
    )
    errors = tuple(
        ObservationError(
            error["query"],
            error["category"],
            error.get("diagnostics", {}).get("code"),
            error.get("diagnostics", {}).get("method"),
        )
        for error in row["errors"]
    )
    return PriceObservation(
        row["branch"],
        row["phase"],
        head,
        values.get("source"),
        values.get("price"),
        values.get("base_currency"),
        values.get("base_unit"),
        values.get("aggregator"),
        feed,
        oracle,
        source,
        errors,
    )


@dataclass(frozen=True, init=False)
class ObservedTraceResult:
    _encoded: bytes = field(repr=False)

    def __init__(self, value: object):
        object.__setattr__(self, "_encoded", _checked_observed(value))

    @classmethod
    def parse(cls, value: object) -> ObservedTraceResult:
        return cls(value)

    @property
    def report(self) -> dict:
        """Return a fresh copy of the validated wrapper, including the raw ABI."""
        return json.loads(self._encoded)

    @property
    def artifact_id(self) -> str:
        return self.report["artifact_id"]

    @property
    def profile(self) -> str:
        return self.report["profile"]

    @property
    def trace(self) -> TraceResult:
        return TraceResult.parse(self.report["trace_report"])

    @property
    def observations(self) -> tuple[PriceObservation, ...]:
        return tuple(_typed_observation(row) for row in self.report["observations"])

    @property
    def classification(self) -> PriceClassification:
        value = self.report["classification"]
        value["unproven_reasons"] = tuple(value["unproven_reasons"])
        return PriceClassification(**value)


def _bounded_integer(text: str) -> int:
    _require(len(text) <= 512)
    return int(text)


def load_observed_trace(path: str | Path) -> ObservedTraceResult:
    """Read a regular JSON file within 8 MiB, rejecting duplicate keys offline."""
    try:
        with os.fdopen(
            os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)), "rb"
        ) as source:
            _require(stat.S_ISREG(os.fstat(source.fileno()).st_mode))
            raw = source.read(MAX_TRACE_BYTES + 1)
        _require(len(raw) <= MAX_TRACE_BYTES)
        return ObservedTraceResult.parse(
            json.loads(
                raw, object_pairs_hook=_unique_object, parse_int=_bounded_integer
            )
        )
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        raise ClientError(
            "Observed trace input must be a regular JSON file within 8 MiB with unique object keys"
        ) from None
