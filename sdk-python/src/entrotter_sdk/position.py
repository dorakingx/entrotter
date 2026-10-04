"""Offline fixed-profile Aave account observations; no engine or chain execution.

The closed ABI/coverage/classification contract follows Engine 88c6cd0.
Hash and consistency verification do not authenticate a provider or EVM state.
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
from . import observed as price
from .observed import (
    ObservedTraceResult,
    ObservationHead,
    ObservationCode,
    ObservationError,
)
from .trace import (
    MAX_TRACE_BYTES,
    TraceResult,
    _canonical,
    _hex,
    _require,
    _unique_object,
)

VERSION = "0.1.0"
PROFILE = "aave-v3-ethereum-account"
# Historical January 4, 2024 address-book reference, not deployment authentication.
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
PROVIDER = "0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"
PROVIDER_SELECTOR = "0x0542975c"
ORACLE_SELECTOR = "0xfca513a8"
QUERIES = {"pool_code", "account_data", "provider", "oracle"}
SELECTOR = "0xbf92857c"  # getUserAccountData(address), six uint256 words.
FIELDS = (
    "total_collateral_base",
    "total_debt_base",
    "available_borrows_base",
    "liquidation_threshold_bps",
    "ltv_bps",
    "health_factor_wad",
)
SCOPE = (
    "Owned-node read-only Aave account views. Differences compare the submitted "
    "transaction-prefix branches; they do not isolate price as the sole cause. "
    "No signed consumer action, loan/liquidation execution, profit, provider or "
    "proxy-implementation authentication, full-block/state-root proof. "
    "All-account base-currency values, not token balances; WAD health factor, "
    "basis-point thresholds. Native execution has no whole-process sandbox."
)


def decode_account(raw: Any) -> dict[str, int]:
    value = _hex(raw, size=192)
    values = [int.from_bytes(value[i : i + 32], "big") for i in range(0, 192, 32)]
    if values[3] > 10000 or values[4] > 10000:
        raise ValueError("Account thresholds exceed basis-point range")
    if values[1] == 0 and values[5] != 2**256 - 1:
        raise ValueError("Zero-debt health factor must retain the uint256 sentinel")
    return dict(zip(FIELDS, values))


def _health_status(value: dict | None) -> str:
    if value is None:
        return "unproven"
    if value["total_debt_base"] == 0:
        return "no_debt"
    return "below_one" if value["health_factor_wad"] < 10**18 else "at_or_above_one"


def classify(rows: list[dict], observed: dict) -> dict:
    reasons = set()
    if not observed["classification"]["complete_price_views"]:
        reasons.add("price_views_unproven")
    if not observed["trace_report"]["baseline_verified"]:
        reasons.add("baseline_receipts_unverified")
    values = [
        decode_account(row["raw"]) if row["raw"] is not None else None for row in rows
    ]
    if len(rows) != 4 or any(
        row["errors"] or row["raw"] is None or row["code"] is None for row in rows
    ):
        reasons.add("incomplete_account_views")
    if any(row["code"] is None or row["code"]["bytes"] == 0 for row in rows):
        reasons.add("pool_code_unavailable")
    if len(rows) == 4:
        if any(row["code"] != rows[0]["code"] for row in rows[1:]):
            reasons.add("pool_code_identity_changed")
        if values[0] != values[2]:
            reasons.add("initial_account_views_differ")
    if any(
        row["provider"] is None
        or price._address(row["provider"]) != PROVIDER
        or row["oracle"] is None
        or price._address(row["oracle"]) != ORACLE
        for row in rows
    ):
        reasons.add("pool_oracle_binding_unproven")
    complete = not reasons
    baseline = values[1] if complete else None
    candidate = values[3] if complete else None
    differences = {
        name: candidate[name] - baseline[name]
        if candidate is not None and baseline is not None
        else None
        for name in FIELDS
    }
    if (
        baseline is not None
        and candidate is not None
        and (baseline["total_debt_base"] == 0 or candidate["total_debt_base"] == 0)
    ):
        differences["health_factor_wad"] = None
    return {
        "complete_account_views": complete,
        "unproven_reasons": sorted(reasons),
        "baseline": baseline,
        "candidate": candidate,
        "differences": differences,
        "baseline_health_status": _health_status(baseline),
        "candidate_health_status": _health_status(candidate),
        "base_unit": price.UNIT if complete else None,
        "health_factor_unit": 10**18,
    }


def _validate_rows(rows: Any, plan: dict, observed: dict) -> None:
    if (
        not isinstance(rows, list)
        or len(rows) != 4
        or len(_canonical(rows)) > price.MAX_OBSERVATION_BYTES
    ):
        raise ValueError("Invalid account observation bound")
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "branch",
            "phase",
            "raw",
            "provider",
            "oracle",
            "code",
            "errors",
            "account",
            "head",
        }:
            raise ValueError("Invalid account observation shape")
        if (row["branch"], row["phase"]) != price.PHASES[i]:
            raise ValueError("Invalid account observation phase")
        if row["account"] != plan["account"] or _canonical(row["head"]) != _canonical(
            observed["observations"][i]["head"]
        ):
            raise ValueError("Account/head binding differs")
        if row["raw"] is not None:
            decode_account(row["raw"])
        for name in ("provider", "oracle"):
            if row[name] is not None:
                price._address(row[name])
        code = row["code"]
        if code is not None and (
            not isinstance(code, dict)
            or set(code) != {"bytes", "sha256"}
            or type(code["bytes"]) is not int
            or not 0 <= code["bytes"] <= price.MAX_OBSERVATION_BYTES
            or type(code["sha256"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", code["sha256"]) is None
        ):
            raise ValueError("Invalid pool code identity")
        errors = row["errors"]
        if not isinstance(errors, list) or len(errors) > 4:
            raise ValueError("Invalid account diagnostic bound")
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
                or error["category"] not in {"rpc_error", "invalid_response"}
            ):
                raise ValueError("Invalid account diagnostic")
            failed.add(error["query"])
            if error["category"] == "rpc_error":
                diag = error.get("diagnostics")
                method = "eth_getCode" if error["query"] == "pool_code" else "eth_call"
                if (
                    not isinstance(diag, dict)
                    or set(diag) != {"code", "method"}
                    or type(diag["code"]) is not str
                    or diag["code"] not in price.FAILURE_CODES
                    or type(diag["method"]) not in {str, type(None)}
                    or diag["method"] not in {method, None}
                ):
                    raise ValueError("Invalid account RPC diagnostic")
            elif "diagnostics" in error:
                raise ValueError("Unexpected account RPC diagnostic")
        available = ({"pool_code"} if code is not None else set()) | (
            {"account_data"} if row["raw"] is not None else set()
        )
        available |= {name for name in ("provider", "oracle") if row[name] is not None}
        if available & failed or available | failed != QUERIES:
            raise ValueError("Account query coverage differs")


def _checked_position(value: object) -> bytes:
    try:
        _require(type(value) is dict)
        encoded = _canonical(value)
        _require(len(encoded) <= MAX_TRACE_BYTES)
        result = json.loads(encoded)
        _require(
            set(result)
            == {
                "position_version",
                "profile",
                "plan",
                "price_report",
                "observations",
                "classification",
                "scope",
                "artifact_id",
            }
        )
        _require(
            result["position_version"] == VERSION
            and result["profile"] == PROFILE
            and result["scope"] == SCOPE
        )
        plan = result["plan"]
        _require(
            type(plan) is dict and set(plan) == {"position_version", "trace", "account"}
        )
        _require(
            plan["position_version"] == VERSION
            and type(plan["account"]) is str
            and re.fullmatch(r"0x[0-9a-f]{40}", plan["account"]) is not None
            and plan["account"] != price.ZERO
        )
        observed = ObservedTraceResult.parse(result["price_report"])
        _require(_canonical(observed.trace.report["plan"]) == _canonical(plan["trace"]))
        _validate_rows(result["observations"], plan, observed.report)
        _require(
            _canonical(result["classification"])
            == _canonical(classify(result["observations"], observed.report))
        )
        ident = result["artifact_id"]
        _require(
            type(ident) is str and re.fullmatch(r"[0-9a-f]{64}", ident) is not None
        )
        body = {key: data for key, data in result.items() if key != "artifact_id"}
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
            "Position report failed version, hash, size or internal-consistency checks"
        ) from None


def verify_position(value: object) -> bool:
    """Verify recorded consistency only; no provider or execution authentication."""
    try:
        _checked_position(value)
        return True
    except ClientError:
        return False


@dataclass(frozen=True)
class AccountValues:
    total_collateral_base: int
    total_debt_base: int
    available_borrows_base: int
    liquidation_threshold_bps: int
    ltv_bps: int
    health_factor_wad: int


@dataclass(frozen=True)
class AccountDifferences:
    total_collateral_base: int | None
    total_debt_base: int | None
    available_borrows_base: int | None
    liquidation_threshold_bps: int | None
    ltv_bps: int | None
    health_factor_wad: int | None


@dataclass(frozen=True)
class AccountObservation:
    branch: str
    phase: str
    account: str
    head: ObservationHead | None
    values: AccountValues | None
    provider: str | None
    oracle: str | None
    pool_code: ObservationCode | None
    errors: tuple[ObservationError, ...]


@dataclass(frozen=True)
class PositionClassification:
    complete_account_views: bool
    unproven_reasons: tuple[str, ...]
    baseline: AccountValues | None
    candidate: AccountValues | None
    differences: AccountDifferences
    baseline_health_status: str
    candidate_health_status: str
    base_unit: int | None
    health_factor_unit: int


def _typed_observation(row: dict) -> AccountObservation:
    return AccountObservation(
        row["branch"],
        row["phase"],
        row["account"],
        ObservationHead(**row["head"]) if row["head"] is not None else None,
        AccountValues(**decode_account(row["raw"])) if row["raw"] is not None else None,
        price._address(row["provider"]) if row["provider"] is not None else None,
        price._address(row["oracle"]) if row["oracle"] is not None else None,
        ObservationCode(**row["code"]) if row["code"] is not None else None,
        tuple(
            ObservationError(
                error["query"],
                error["category"],
                error.get("diagnostics", {}).get("code"),
                error.get("diagnostics", {}).get("method"),
            )
            for error in row["errors"]
        ),
    )


@dataclass(frozen=True, init=False)
class PositionResult:
    _encoded: bytes = field(repr=False)

    def __init__(self, value: object):
        object.__setattr__(self, "_encoded", _checked_position(value))

    @classmethod
    def parse(cls, value: object) -> PositionResult:
        return cls(value)

    @property
    def report(self) -> dict:
        """Return a fresh complete snapshot, retaining all raw ABI fields."""
        return json.loads(self._encoded)

    @property
    def artifact_id(self) -> str:
        return self.report["artifact_id"]

    @property
    def profile(self) -> str:
        return self.report["profile"]

    @property
    def account(self) -> str:
        return self.report["plan"]["account"]

    @property
    def plan(self) -> dict:
        return self.report["plan"]

    @property
    def prices(self) -> ObservedTraceResult:
        return ObservedTraceResult.parse(self.report["price_report"])

    @property
    def trace(self) -> TraceResult:
        return self.prices.trace

    @property
    def observations(self) -> tuple[AccountObservation, ...]:
        return tuple(_typed_observation(row) for row in self.report["observations"])

    @property
    def classification(self) -> PositionClassification:
        value = self.report["classification"]
        value["unproven_reasons"] = tuple(value["unproven_reasons"])
        for name in ("baseline", "candidate"):
            value[name] = (
                AccountValues(**value[name]) if value[name] is not None else None
            )
        value["differences"] = AccountDifferences(**value["differences"])
        return PositionClassification(**value)


def load_position(path: str | Path) -> PositionResult:
    """Read at most 8 MiB of regular JSON with unique keys, entirely offline."""
    try:
        with os.fdopen(
            os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)), "rb"
        ) as source:
            _require(stat.S_ISREG(os.fstat(source.fileno()).st_mode))
            raw = source.read(MAX_TRACE_BYTES + 1)
        _require(len(raw) <= MAX_TRACE_BYTES)
        return PositionResult.parse(
            json.loads(
                raw, object_pairs_hook=_unique_object, parse_int=price._bounded_integer
            )
        )
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        raise ClientError(
            "Position input must be a regular JSON file within 8 MiB with unique object keys"
        ) from None
