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
FRAME_CLAIM_KEYS = {
    "snapshot_id", "revision", "native_revision", "date_raw",
    "actor_character_id", "episode_run_id", "war_id", "connection_generation",
}


def frame_claim_from_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    """Bind a fresh paused read to the actual native frame, never a saved ID."""
    if not isinstance(snapshot, dict):
        raise ValueError("H2743 frame is absent")
    native = snapshot.get("native_revision")
    public = snapshot.get("revision")
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    wars = snapshot.get("active_wars")
    if (type(native) is not int or native < 1 or type(public) is not int
            or public < 1 or snapshot.get("snapshot_id") != f"native:{native}"
            or snapshot.get("date_raw") != DATE_RAW or snapshot.get("paused") is not True
            or snapshot.get("map_ready") is not True
            or snapshot.get("episode_run_id") != EPISODE
            or not isinstance(played, dict) or played.get("alive") is not True
            or type(played.get("character_id")) is not int
            or played["character_id"] != TOWARD_ID
            or not isinstance(diagnostics, dict)
            or type(diagnostics.get("connection_generation")) is not int
            or diagnostics["connection_generation"] < 1
            or not isinstance(wars, list)):
        raise ValueError("H2743 paused source frame identity differs")
    matched = [war for war in wars if isinstance(war, dict)
               and type(war.get("war_id")) is int and war["war_id"] == WAR_ID]
    if (len(matched) != 1 or matched[0].get("player_side") != "defender"
            or matched[0].get("player_is_primary_war_leader") is not True
            or type(matched[0].get("primary_opponent_character_id")) is not int
            or matched[0]["primary_opponent_character_id"] != OWNER_ID
            or matched[0].get("targeted_title_ids") != [2128]):
        raise ValueError("H2743 paused WarID or primary parties differ")
    return {
        "snapshot_id": snapshot["snapshot_id"], "revision": public,
        "native_revision": native, "date_raw": DATE_RAW,
        "actor_character_id": TOWARD_ID, "episode_run_id": EPISODE,
        "war_id": WAR_ID,
        "connection_generation": diagnostics["connection_generation"],
    }


def require_frame_claim(claim: dict[str, object] | None,
                        snapshot: dict[str, object]) -> dict[str, object]:
    if not isinstance(claim, dict) or set(claim) != FRAME_CLAIM_KEYS:
        raise ValueError("H2743 explicit before-frame claim is absent or malformed")
    actual = frame_claim_from_snapshot(snapshot)
    if any(type(claim[key]) is not type(value) or claim[key] != value
           for key, value in actual.items()):
        raise ValueError("H2743 explicit before-frame claim drifted")
    return actual


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
