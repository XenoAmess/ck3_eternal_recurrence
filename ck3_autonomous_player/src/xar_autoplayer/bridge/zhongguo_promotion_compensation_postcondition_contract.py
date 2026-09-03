"""Strict promotion/compensation postcondition query and facade contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Mapping


QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-promotion-compensation-postcondition-v1"
)
QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP: Final = (
    "query-zhongguo-promotion-compensation-postcondition-v1"
)
QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP}-"
)
_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS = {"status", "value", "unavailable_reason"}
_IDENTITY_KEYS = {
    "owner_character_id", "subject_character_id", "cycle_serial",
    "case_serial", "revision",
}
_READINESS_KEYS = {
    "player_owner_binding_ready", "portfolio_subject_binding_ready",
    "source_identity_ready", "result_identity_ready",
    "frozen_case_identity_ready", "promotion_choice_receipt_ready",
    "compensation_receipt_posted", "same_case_identity_ready",
    "revision_binding_ready", "receipt_serials_ready", "same_frame_ready",
    "ready",
}


@dataclass(frozen=True)
class ZhongguoPromotionCompensationQueryV1:
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


def query_zhongguo_promotion_compensation_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_promotion_compensation_v1_step(
    step: object,
) -> ZhongguoPromotionCompensationQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP_PREFIX
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
        return ZhongguoPromotionCompensationQueryV1(
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


def _identity(value: object, name: str) -> dict[str, object]:
    raw = _exact(value, _IDENTITY_KEYS, name)
    return {key: _typed(raw[key], f"{name}.{key}", int) for key in raw}


def normalize_native_zhongguo_promotion_compensation_v1(
    value: object, *, expected_query: ZhongguoPromotionCompensationQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    keys = {
        "schema_version", "status", "capability", "source_backend_id",
        "request_nonce", "snapshot_revision", "date_raw", "paused",
        "player_character_id", "subject_character_id",
        "promotion_compensation", "readiness", "unavailable_reason",
    }
    frame = _exact(value, keys, "promotion_compensation_frame")
    if frame["schema_version"] != 1 or frame["capability"] != (
        QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
    ) or frame["source_backend_id"] != (
        "ck3-1.19.0.6-native-zhongguo-promotion-compensation-postcondition-v1"
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
    payload = _exact(
        frame["promotion_compensation"],
        {"source_identity", "result_identity", "frozen_case",
         "promotion_choice", "compensation_receipt"},
        "promotion_compensation",
    )
    source = _identity(payload["source_identity"], "source_identity")
    result = _identity(payload["result_identity"], "result_identity")
    frozen_raw = _exact(payload["frozen_case"], {"identity", "frozen"}, "frozen_case")
    if frozen_raw["frozen"] is not True:
        raise ValueError("frozen case is not frozen")
    frozen = _identity(frozen_raw["identity"], "frozen_case.identity")
    choice_raw = _exact(
        payload["promotion_choice"],
        {"identity", "option_number", "receipt_serial", "active", "consumed"},
        "promotion_choice",
    )
    choice = {**choice_raw, "identity": _identity(choice_raw["identity"], "promotion_choice.identity")}
    for key in ("option_number", "receipt_serial"):
        choice[key] = _typed(choice_raw[key], f"promotion_choice.{key}", int)
    for key in ("active", "consumed"):
        choice[key] = _typed(choice_raw[key], f"promotion_choice.{key}", bool)
    receipt_raw = _exact(
        payload["compensation_receipt"],
        {"identity", "operation_id", "option_number", "receipt_serial",
         "active", "consumed", "posted"},
        "compensation_receipt",
    )
    receipt = {**receipt_raw, "identity": _identity(receipt_raw["identity"], "compensation_receipt.identity")}
    for key in ("operation_id", "option_number", "receipt_serial"):
        receipt[key] = _typed(receipt_raw[key], f"compensation_receipt.{key}", int)
    for key in ("active", "consumed", "posted"):
        receipt[key] = _typed(receipt_raw[key], f"compensation_receipt.{key}", bool)
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(value, bool) for value in readiness_raw.values()):
        raise ValueError("readiness values must be boolean")
    expected_ready = all(readiness_raw[key] for key in _READINESS_KEYS - {"ready"})
    if readiness_raw["ready"] is not expected_ready:
        raise ValueError("readiness aggregate disagrees")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid provider status")
    if frame["status"] == "unavailable" and not isinstance(
        frame["unavailable_reason"], str
    ):
        raise ValueError("unavailable provider lacks reason")
    return {
        **frame,
        "promotion_compensation": {
            "source_identity": source, "result_identity": result,
            "frozen_case": {"identity": frozen, "frozen": True},
            "promotion_choice": choice, "compensation_receipt": receipt,
        },
        "readiness": dict(readiness_raw),
    }


def bind_promotion_compensation_event_snapshots_v1(
    business_query: Mapping[str, object], source_event: Mapping[str, object],
    result_event: Mapping[str, object],
) -> dict[str, object]:
    """Bind a normalized business read to two normalized event snapshots."""

    business = dict(business_query)
    source_binding = source_event.get("binding")
    result_binding = result_event.get("binding")
    binding = business.get("binding")
    if not all(isinstance(item, Mapping) for item in (
        source_binding, result_binding, binding
    )):
        raise ValueError("source/result/business binding is missing")
    generation = binding.get("connection_generation")  # type: ignore[union-attr]
    if not _positive(generation, "connection_generation") or any(
        item.get("connection_generation") != generation
        for item in (source_binding, result_binding)
    ):
        raise ValueError("source/result connection generation drifted")
    if binding.get("snapshot_id") != result_binding.get("snapshot_id") or (
        binding.get("native_revision") != result_binding.get("native_revision")
    ):
        raise ValueError("business query is not bound to the result snapshot")
    business["binding"] = {
        **dict(binding),
        "source_snapshot_id": source_binding.get("snapshot_id"),
        "result_snapshot_id": result_binding.get("snapshot_id"),
        "source_revision": source_binding.get("revision"),
        "result_revision": result_binding.get("revision"),
        "source_native_revision": source_binding.get("native_revision"),
        "result_native_revision": result_binding.get("native_revision"),
    }
    return business
