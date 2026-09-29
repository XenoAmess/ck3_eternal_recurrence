"""Strict read-only contract for the exact H2743 preaction existing truce slot."""

from __future__ import annotations


QUERY_STEP = "query-h2743-preaction-existing-truce-v1"
CAPABILITY = "game.command.query-h2743-preaction-existing-truce-v1"
EPISODE = "native-29829-2bc2d599f7f9"
CHECKPOINT_SHA256 = "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9"
DATE_RAW = 53217264
WAR_ID = 16777231
OWNER_ID = 30097
TOWARD_ID = 29829
WIRE_KEYS = {
    "schema", "backend_id", "war_id", "owner_character_id", "toward_character_id",
    "episode_id_claim", "episode_authenticated_here", "checkpoint_sha256_claim",
    "checkpoint_bytes_authenticated_here", "status", "snapshot_revision", "date_raw",
    "same_frame_stable", "preaction_existing_expiry_observable",
    "preaction_existing_expiry_date_raw", "post_surrender_actual_expiry_date_raw",
    "script_candidate_days", "effect_projection_complete", "material_complete",
    "recommended_outcome", "action_literal", "unavailable_reason",
}
OUTER_KEYS = {
    "step", "accepted", "query_sequence", "snapshot_revision",
    "h2743_preaction_existing_truce", "backend_id",
}


def normalize_result(value: dict[str, object], *, native_revision: int) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != OUTER_KEYS:
        raise ValueError("H2743 outer result fields differ")
    sequence = value.get("query_sequence")
    if (value.get("step") != QUERY_STEP or value.get("accepted") is not True
            or value.get("backend_id") != "native-headless"
            or type(sequence) is not int or sequence < 1
            or type(native_revision) is not int or native_revision < 1
            or type(value.get("snapshot_revision")) is not int
            or value.get("snapshot_revision") != native_revision):
        raise ValueError("H2743 outer result identity differs")
    wire = value.get("h2743_preaction_existing_truce")
    if not isinstance(wire, dict) or set(wire) != WIRE_KEYS:
        raise ValueError("H2743 truce wire fields differ")
    fixed = {
        "schema": "xar.ck3.h2743_preaction_existing_truce.v1",
        "backend_id": "ck3-1.19.0.6-native-h2743-existing-truce-v1",
        "war_id": WAR_ID, "owner_character_id": OWNER_ID, "toward_character_id": TOWARD_ID,
        "episode_id_claim": EPISODE, "episode_authenticated_here": False,
        "checkpoint_sha256_claim": CHECKPOINT_SHA256,
        "checkpoint_bytes_authenticated_here": False,
        "snapshot_revision": native_revision, "date_raw": DATE_RAW,
        "post_surrender_actual_expiry_date_raw": None, "script_candidate_days": None,
        "effect_projection_complete": False, "material_complete": False,
        "recommended_outcome": None, "action_literal": None,
    }
    if any(wire.get(key) != expected or type(wire.get(key)) is not type(expected)
           for key, expected in fixed.items()):
        raise ValueError("H2743 truce wire source, frame, or unknown future fields differ")
    status = wire.get("status")
    expiry = wire.get("preaction_existing_expiry_date_raw")
    reason = wire.get("unavailable_reason")
    if status == "existing_truce":
        if (wire.get("same_frame_stable") is not True
                or wire.get("preaction_existing_expiry_observable") is not True
                or type(expiry) is not int or expiry <= DATE_RAW or reason is not None):
            raise ValueError("H2743 existing slot is not stable and future dated")
    elif status == "no_existing_truce":
        if (wire.get("same_frame_stable") is not True
                or wire.get("preaction_existing_expiry_observable") is not False
                or expiry is not None or reason != "no_existing_truce"):
            raise ValueError("H2743 no-slot result differs")
    elif status == "unavailable":
        if (wire.get("same_frame_stable") is not False
                or wire.get("preaction_existing_expiry_observable") is not False
                or expiry is not None or not isinstance(reason, str) or not reason):
            raise ValueError("H2743 unavailable result falsely exposes an expiry")
    else:
        raise ValueError("H2743 truce status differs")
    return wire
