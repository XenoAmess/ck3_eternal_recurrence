"""Standalone AF5 compensation snapshot query contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-compensation-af5-snapshot-v1"
)
QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-compensation-af5-snapshot-v1"
)
QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP}-"
)
_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS = {"status", "value", "unavailable_reason"}
_IDENTITY_KEYS = {
    "owner_character_id", "subject_character_id", "cycle_serial",
    "case_serial", "revision",
}
_READINESS_KEYS = {
    "player_owner_binding_ready", "portfolio_subject_binding_ready",
    "same_case_identity_ready", "same_frame_ready", "ready",
}


@dataclass(frozen=True)
class ZhongguoCompensationAf5SnapshotQueryV1:
    owner_character_id: int
    request_nonce: str


def _positive(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonce(value: object) -> str:
    if not isinstance(value, str) or _NONCE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a bounded ASCII token")
    return value


def query_zhongguo_compensation_af5_snapshot_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_compensation_af5_snapshot_v1_step(
    step: object,
) -> ZhongguoCompensationAf5SnapshotQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP_PREFIX
    ).split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0] or not parts[1] or len(parts[1]) % 2:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        if nonce.encode("ascii").hex() != parts[1]:
            return None
        return ZhongguoCompensationAf5SnapshotQueryV1(
            _positive(owner, "owner_character_id"), _nonce(nonce)
        )
    except (UnicodeDecodeError, ValueError):
        return None


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed(value: object, name: str, kind: type) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "available":
        raw = field["value"]
        if field["unavailable_reason"] is not None or isinstance(raw, bool) != (
            kind is bool
        ) or not isinstance(raw, kind):
            raise ValueError(f"{name} has an invalid available value")
    elif field["status"] == "unavailable":
        if field["value"] is not None or not isinstance(
            field["unavailable_reason"], str
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    else:
        raise ValueError(f"{name} has invalid status")
    return dict(field)


def _identity(value: object, name: str, *, revision: bool = False) -> dict[str, object]:
    keys = _IDENTITY_KEYS if revision else _IDENTITY_KEYS - {"revision"}
    raw = _exact(value, keys, name)
    return {key: _typed(raw[key], f"{name}.{key}", int) for key in raw}


def normalize_native_zhongguo_compensation_af5_snapshot_v1(
    value: object, *, expected_query: ZhongguoCompensationAf5SnapshotQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Normalize either the observable pre-action state or terminal state.

    Portfolio domain/stage may disappear after closure. Neither event presence
    nor an earlier promotion receipt is a prerequisite for this read.
    """
    frame = _exact(value, {
        "schema_version", "status", "capability", "source_backend_id",
        "request_nonce", "snapshot_revision", "date_raw", "paused",
        "player_character_id", "subject_character_id", "af5", "readiness",
        "terminal", "unavailable_reason",
    }, "af5_frame")
    if frame["schema_version"] != 1 or frame["capability"] != (
        QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_CAPABILITY
    ) or frame["source_backend_id"] != (
        "ck3-1.19.0.6-native-zhongguo-compensation-af5-snapshot-v1"
    ):
        raise ValueError("provider provenance changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce changed")
    if frame["snapshot_revision"] != expected_snapshot_revision or frame[
        "date_raw"
    ] != expected_date_raw or frame["paused"] is not True:
        raise ValueError("paused native frame changed")
    if frame["player_character_id"] != expected_player_character_id or (
        expected_query.owner_character_id != expected_player_character_id
    ):
        raise ValueError("played owner binding changed")
    _positive(frame["subject_character_id"], "subject_character_id")
    payload = _exact(frame["af5"], {"portfolio", "case", "m299", "m300"}, "af5")
    portfolio = _exact(payload["portfolio"], {
        "domain", "stage", "completed_cycle", "visible_pending", "result_identity",
    }, "af5.portfolio")
    normalized_portfolio = {
        key: _typed(portfolio[key], f"af5.portfolio.{key}", int)
        for key in ("domain", "stage", "completed_cycle")
    }
    normalized_portfolio["visible_pending"] = _typed(
        portfolio["visible_pending"], "af5.portfolio.visible_pending", bool
    )
    normalized_portfolio["result_identity"] = _identity(
        portfolio["result_identity"], "af5.portfolio.result_identity"
    )
    case = _exact(payload["case"], {
        "identity", "state", "active", "last_operation", "last_route",
        "repurchase_resolved", "unit_conserved", "result_case_serial",
    }, "af5.case")
    normalized_case = {
        "identity": _identity(case["identity"], "af5.case.identity", revision=True)
    }
    for key in ("state", "last_operation", "last_route", "result_case_serial"):
        normalized_case[key] = _typed(case[key], f"af5.case.{key}", int)
    for key in ("active", "repurchase_resolved", "unit_conserved"):
        normalized_case[key] = _typed(case[key], f"af5.case.{key}", bool)
    normalized_af5 = {"portfolio": normalized_portfolio, "case": normalized_case}
    for receipt_name in ("m299", "m300"):
        receipt = _exact(payload[receipt_name], {
            "identity", "state", "active", "consumed", "route",
        }, f"af5.{receipt_name}")
        normalized_receipt = {
            "identity": _identity(receipt["identity"], f"af5.{receipt_name}.identity")
        }
        for key in ("state", "route"):
            normalized_receipt[key] = _typed(receipt[key], f"af5.{receipt_name}.{key}", int)
        for key in ("active", "consumed"):
            normalized_receipt[key] = _typed(receipt[key], f"af5.{receipt_name}.{key}", bool)
        normalized_af5[receipt_name] = normalized_receipt
    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(raw, bool) for raw in readiness.values()):
        raise ValueError("readiness values must be boolean")
    if readiness["ready"] is not all(
        readiness[key] for key in _READINESS_KEYS - {"ready"}
    ):
        raise ValueError("readiness aggregate disagrees")
    if not isinstance(frame["terminal"], bool) or (
        frame["terminal"] and not readiness["ready"]
    ):
        raise ValueError("terminal requires an observable AF5 frame")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid provider status")
    if frame["status"] == "unavailable" and not isinstance(
        frame["unavailable_reason"], str
    ):
        raise ValueError("unavailable provider lacks reason")
    return {**frame, "af5": normalized_af5, "readiness": dict(readiness)}

