"""Standalone owner-view Workforce snapshot query contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-workforce-owner-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-workforce-owner-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP}-"
)
_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS = {"status", "value", "unavailable_reason"}
_READINESS_KEYS = {
    "player_owner_binding_ready", "portfolio_subject_binding_ready",
    "case_identity_ready", "same_frame_ready", "ready",
}


@dataclass(frozen=True)
class ZhongguoWorkforceOwnerSnapshotQueryV1:
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


def query_zhongguo_workforce_owner_snapshot_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_workforce_owner_snapshot_v1_step(
    step: object,
) -> ZhongguoWorkforceOwnerSnapshotQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_STEP_PREFIX
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
        return ZhongguoWorkforceOwnerSnapshotQueryV1(
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


_GROUP_TYPES: Final = {
    "central": {
        "subject_character_id": int, "cycle_serial": int,
        "case_serial": int, "stage11_status": int,
    },
    "source": {
        "status": int, "owner_character_id": int, "subject_character_id": int,
        "p2c_cycle_serial": int, "p2c_case_serial": int,
        "al_cycle_serial": int, "al_case_serial": int,
    },
    "al_case": {
        "owner_character_id": int, "subject_character_id": int,
        "cycle_serial": int, "case_serial": int, "state": int,
        "active": bool, "revision": int,
    },
    "m360_receipt": {
        "owner_character_id": int, "subject_character_id": int,
        "cycle_serial": int, "case_serial": int, "state": int, "choice": int,
    },
    "portfolio": {
        "closed": bool, "status": int, "cycle_serial": int,
        "final_conservation_ok": bool, "terminal_history_accruing": bool,
        "history_cycle_count": int, "terminal_success": bool,
        "terminal_na": bool, "terminal_reason": int,
        "terminal_owned_operations": int, "terminal_skipped_manager_only": int,
        "terminal_skipped_charter": int,
    },
}


def normalize_native_zhongguo_workforce_owner_snapshot_v1(
    value: object, *, expected_query: ZhongguoWorkforceOwnerSnapshotQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Read the played owner's real Workforce subject and terminal receipt.

    The current Central subject remains authoritative before an M360 source
    exists, including the product's explicit not-applicable terminal branch.
    """
    frame = _exact(value, {
        "schema_version", "status", "capability", "source_backend_id",
        "request_nonce", "snapshot_revision", "date_raw", "paused",
        "player_character_id", "subject_character_id", "workforce", "readiness",
        "terminal", "terminal_kind", "unavailable_reason",
    }, "workforce_owner_frame")
    if frame["schema_version"] != 1 or frame["capability"] != (
        QUERY_ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_CAPABILITY
    ) or frame["source_backend_id"] != (
        "ck3-1.19.0.6-native-zhongguo-workforce-owner-snapshot-v1"
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
    payload = _exact(frame["workforce"], set(_GROUP_TYPES), "workforce")
    normalized = {}
    for group_name, kinds in _GROUP_TYPES.items():
        raw = _exact(payload[group_name], set(kinds), f"workforce.{group_name}")
        normalized[group_name] = {
            key: _typed(raw[key], f"workforce.{group_name}.{key}", kind)
            for key, kind in kinds.items()
        }
    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(raw, bool) for raw in readiness.values()):
        raise ValueError("readiness values must be boolean")
    if readiness["ready"] is not all(
        readiness[key] for key in _READINESS_KEYS - {"ready"}
    ):
        raise ValueError("readiness aggregate disagrees")
    if frame["terminal_kind"] not in {
        "none", "success", "history_accruing", "not_applicable",
    }:
        raise ValueError("invalid Workforce terminal kind")
    if not isinstance(frame["terminal"], bool) or (
        frame["terminal"] is not (frame["terminal_kind"] != "none")
    ) or (frame["terminal"] and not readiness["ready"]):
        raise ValueError("terminal requires an observable Workforce frame")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid provider status")
    if frame["status"] == "unavailable" and not isinstance(
        frame["unavailable_reason"], str
    ):
        raise ValueError("unavailable provider lacks reason")
    return {**frame, "workforce": normalized, "readiness": dict(readiness)}

