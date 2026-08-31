"""Pure contract for the read-only Raiktor attacker-defeat truce primitive."""

from __future__ import annotations


_KEYS = {
    "schema_version",
    "backend_id",
    "status",
    "failure",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "owner_character_id",
    "toward_character_id",
    "evaluated_days",
    "pointer_shape_verified",
    "evaluator_double_read_stable",
    "same_frame_stable",
    "expiry_observable",
    "expiry_date_raw",
}

BACKEND_ID = "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"


def normalize_raiktor_surrender_truce(
    value: object,
    *,
    expected_war_id: int,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
) -> dict[str, object]:
    """Validate one exact-build, paused, stable evaluator observation.

    Version 1 deliberately exposes evaluated days but no inferred expiry date.
    The caller must not convert ``date_raw + 24 * days`` into a persisted-truce
    claim until that engine semantic has its own production observation.
    """
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native Raiktor surrender truce has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("backend_id") != BACKEND_ID
        or value.get("status") != "available"
        or value.get("failure") is not None
    ):
        raise ValueError("native Raiktor surrender truce is unavailable")

    war_id = _positive_int32(value.get("war_id"), "war_id")
    snapshot_revision = _positive_uint64(
        value.get("snapshot_revision"), "snapshot_revision"
    )
    native_revision = _positive_uint64(
        value.get("native_revision"), "native_revision"
    )
    date_raw = _signed_int32(value.get("date_raw"), "date_raw")
    attacker = _positive_int32(
        value.get("owner_character_id"), "owner_character_id"
    )
    defender = _positive_int32(
        value.get("toward_character_id"), "toward_character_id"
    )
    _non_negative_int32(
        value.get("active_casus_belli_database_index"),
        "active_casus_belli_database_index",
    )
    days = _non_negative_int32(value.get("evaluated_days"), "evaluated_days")
    if (
        war_id != _positive_int32(expected_war_id, "expected_war_id")
        or snapshot_revision
        != _positive_uint64(
            expected_snapshot_revision, "expected_snapshot_revision"
        )
        or native_revision
        != _positive_uint64(expected_native_revision, "expected_native_revision")
        or date_raw != _signed_int32(expected_date_raw, "expected_date_raw")
        or attacker
        != _positive_int32(
            expected_attacker_character_id,
            "expected_attacker_character_id",
        )
        or defender
        != _positive_int32(
            expected_defender_character_id,
            "expected_defender_character_id",
        )
    ):
        raise ValueError("native Raiktor surrender truce binding disagrees")
    if attacker == defender:
        raise ValueError("Raiktor surrender truce direction collapsed")
    if value.get("active_casus_belli_key") != "raiktor_claim_cb":
        raise ValueError("Raiktor surrender truce CB is not exact")
    if (
        value.get("paused") is not True
        or value.get("pointer_shape_verified") is not True
        or value.get("evaluator_double_read_stable") is not True
        or value.get("same_frame_stable") is not True
    ):
        raise ValueError("Raiktor surrender truce stability gate failed")
    if value.get("expiry_observable") is not False:
        raise ValueError("Raiktor surrender truce v1 must not claim expiry")
    if value.get("expiry_date_raw") is not None:
        raise ValueError("Raiktor surrender truce v1 invented an expiry date")

    # Keep the validated value lossless for later composition into the shared
    # war-termination response.  ``days`` is intentionally validated above.
    del days
    return dict(value)


def _positive_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0 or value > 2**31 - 1:
        raise ValueError(f"{label} is outside positive int32")
    return value


def _non_negative_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < 0 or value > 2**31 - 1:
        raise ValueError(f"{label} is outside non-negative int32")
    return value


def _signed_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < -(2**31) or value > 2**31 - 1:
        raise ValueError(f"{label} is outside int32")
    return value


def _positive_uint64(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{label} is outside positive uint64")
    return value
