"""Exact-build contract for persisted one-way truce expiry observation."""

from __future__ import annotations


QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY = (
    "game.command.query-raiktor-actual-truce-expiry-v1-N"
)
QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX = (
    "query-raiktor-actual-truce-expiry-v1-"
)
RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_BACKEND_ID = (
    "ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1"
)


def parse_query_raiktor_actual_truce_expiry_v1_step(
    step: object,
) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
    ):
        return None
    value = step.removeprefix(
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
    )
    if (
        not value
        or not value.isascii()
        or not value.isdecimal()
        or value.startswith("0")
    ):
        return None
    parsed = int(value)
    return parsed if 0 < parsed <= 2**31 - 1 else None


def normalize_raiktor_actual_truce_expiry_v1(
    result: object,
    *,
    expected_step: str,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    if not isinstance(result, dict):
        raise ValueError("actual truce-expiry result must be an object")
    expected_keys = {
        "step",
        "accepted",
        "query_sequence",
        "snapshot_revision",
        "raiktor_actual_truce_expiry",
        "backend_id",
    }
    if set(result) != expected_keys:
        raise ValueError("actual truce-expiry result fields changed")
    if result.get("step") != expected_step or result.get("accepted") is not True:
        raise ValueError("actual truce-expiry transport acknowledgement is malformed")
    sequence = result.get("query_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence <= 0:
        raise ValueError("actual truce-expiry query_sequence must be positive")
    if result.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("actual truce-expiry snapshot revision mismatch")
    payload = result.get("raiktor_actual_truce_expiry")
    if not isinstance(payload, dict):
        raise ValueError("actual truce-expiry payload must be an object")
    fields = {
        "schema_version",
        "backend_id",
        "status",
        "snapshot_revision",
        "current_date_raw",
        "owner_character_id",
        "toward_character_id",
        "native_has_truce",
        "actual_expiry_observable",
        "expiry_date_raw",
        "same_frame_stable",
        "readiness",
        "temporal_semantics",
        "unavailable_reason",
    }
    if set(payload) != fields:
        raise ValueError("actual truce-expiry payload fields changed")
    if payload.get("schema_version") != 1:
        raise ValueError("actual truce-expiry schema_version must be 1")
    if payload.get("backend_id") != RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_BACKEND_ID:
        raise ValueError("actual truce-expiry backend_id changed")
    if payload.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("actual truce-expiry payload revision mismatch")
    toward = parse_query_raiktor_actual_truce_expiry_v1_step(expected_step)
    if toward is None or payload.get("toward_character_id") != toward:
        raise ValueError("actual truce-expiry toward identity mismatch")
    for name in ("current_date_raw", "owner_character_id", "toward_character_id"):
        value = payload.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"actual truce-expiry {name} must be an integer")
    for name in (
        "native_has_truce",
        "actual_expiry_observable",
        "same_frame_stable",
        "readiness",
    ):
        if not isinstance(payload.get(name), bool):
            raise ValueError(f"actual truce-expiry {name} must be boolean")
    if payload.get("temporal_semantics") != (
        "post_application_persisted_relation_state"
    ):
        raise ValueError("actual truce-expiry temporal semantics changed")
    status = payload.get("status")
    if status == "available":
        expiry = payload.get("expiry_date_raw")
        current = payload.get("current_date_raw")
        if (
            payload.get("native_has_truce") is not True
            or payload.get("actual_expiry_observable") is not True
            or payload.get("same_frame_stable") is not True
            or payload.get("readiness") is not True
            or isinstance(expiry, bool)
            or not isinstance(expiry, int)
            or not isinstance(current, int)
            or expiry <= current
            or payload.get("unavailable_reason") is not None
        ):
            raise ValueError("available actual truce-expiry proof is incomplete")
    elif status == "no_truce":
        if not (
            payload.get("native_has_truce") is False
            and payload.get("actual_expiry_observable") is False
            and payload.get("expiry_date_raw") is None
            and payload.get("same_frame_stable") is True
            and payload.get("readiness") is False
            and payload.get("unavailable_reason") == "native_has_truce_false"
        ):
            raise ValueError("no-truce observation is malformed")
    else:
        raise ValueError("successful transport cannot carry unavailable state")
    return dict(payload)
