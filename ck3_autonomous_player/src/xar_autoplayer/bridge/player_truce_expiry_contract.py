"""Exact actual4 observation of the played character's persisted directional truce."""
from __future__ import annotations

from collections.abc import Mapping

QUERY_PLAYER_TRUCE_EXPIRY_V1_CAPABILITY = "game.command.query-raiktor-actual-truce-expiry-v1-N"
QUERY_PLAYER_TRUCE_EXPIRY_V1_STEP_PREFIX = "query-raiktor-actual-truce-expiry-v1-"
PLAYER_TRUCE_EXPIRY_V1_BACKEND_ID = "ck3-1.20.0.4-native-player-truce-expiry-v1"
PLAYER_TRUCE_EXPIRY_V1_BUILD = "1.20.0.4"
PLAYER_TRUCE_EXPIRY_V1_EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def player_truce_expiry_toward_id(value: object) -> int:
    if type(value) is not int or not 1 <= value <= 2**31 - 1:
        raise ValueError("toward_character_id must be a positive full signed CharacterID")
    return value


def player_truce_expiry_revision(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    return value


def query_player_truce_expiry_v1_step(toward_character_id: object) -> str:
    return QUERY_PLAYER_TRUCE_EXPIRY_V1_STEP_PREFIX + str(player_truce_expiry_toward_id(toward_character_id))


def player_truce_expiry_query_actor(snapshot: Mapping[str, object]) -> int:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("player truce-expiry query requires a ready paused map")
    actor = snapshot.get("played_character")
    if not isinstance(actor, dict) or actor.get("alive") is not True:
        raise ValueError("player truce-expiry query lacks a living played character")
    actor_id = actor.get("character_id")
    if type(actor_id) is not int or not 0 <= actor_id <= 2**31 - 1:
        raise ValueError("player truce-expiry query lacks a full current played CharacterID")
    return actor_id


def normalize_player_truce_expiry_v1(
    result: object, *, expected_toward_character_id: int,
    expected_owner_character_id: int, expected_snapshot_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    toward_id = player_truce_expiry_toward_id(expected_toward_character_id)
    if not isinstance(result, dict) or set(result) != {
        "step", "accepted", "query_sequence", "snapshot_revision",
        "raiktor_actual_truce_expiry", "backend_id", "read_only", "date_raw",
    }:
        raise ValueError("player truce-expiry requires every agreed envelope field")
    if (result.get("step") != query_player_truce_expiry_v1_step(toward_id)
            or result.get("accepted") is not True or result.get("read_only") is not True
            or result.get("backend_id") != "native-headless"):
        raise ValueError("player truce-expiry transport acknowledgement is malformed")
    sequence = result.get("query_sequence")
    if type(sequence) is not int or not 1 <= sequence <= 2**64 - 1:
        raise ValueError("player truce-expiry query_sequence must be a positive uint64")
    if (type(expected_snapshot_revision) is not int or not 0 <= expected_snapshot_revision <= 2**64 - 1
            or type(result.get("snapshot_revision")) is not int
            or result["snapshot_revision"] != expected_snapshot_revision):
        raise ValueError("player truce-expiry differs from the native snapshot revision")
    if (type(expected_date_raw) is not int or not -(2**31) <= expected_date_raw <= 2**31 - 1
            or type(result.get("date_raw")) is not int or result["date_raw"] != expected_date_raw):
        raise ValueError("player truce-expiry differs from the paused date")
    if type(expected_owner_character_id) is not int or not 0 <= expected_owner_character_id <= 2**31 - 1:
        raise ValueError("player truce-expiry requires the current full owner CharacterID")
    payload = result.get("raiktor_actual_truce_expiry")
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "backend_id", "ck3_build", "executable_sha256",
        "status", "snapshot_revision", "current_date_raw", "owner_character_id",
        "toward_character_id", "native_has_truce", "actual_expiry_observable",
        "expiry_date_raw", "same_frame_stable", "readiness", "temporal_semantics",
        "unavailable_reason",
    }:
        raise ValueError("player truce-expiry requires every agreed DTO field")
    sha = payload.get("executable_sha256")
    if (type(payload.get("schema_version")) is not int or payload["schema_version"] != 1
            or payload.get("backend_id") != PLAYER_TRUCE_EXPIRY_V1_BACKEND_ID
            or payload.get("ck3_build") != PLAYER_TRUCE_EXPIRY_V1_BUILD
            or not isinstance(sha, str) or sha.upper() != PLAYER_TRUCE_EXPIRY_V1_EXECUTABLE_SHA256):
        raise ValueError("player truce-expiry lacks exact actual4 provenance")
    for field, expected in (
        ("snapshot_revision", expected_snapshot_revision), ("current_date_raw", expected_date_raw),
        ("owner_character_id", expected_owner_character_id), ("toward_character_id", toward_id),
    ):
        if type(payload.get(field)) is not int or payload[field] != expected:
            raise ValueError(f"player truce-expiry {field} differs from the current query")
    for field in ("native_has_truce", "actual_expiry_observable", "same_frame_stable", "readiness"):
        if type(payload.get(field)) is not bool:
            raise ValueError(f"player truce-expiry {field} must be boolean")
    if payload.get("temporal_semantics") != "post_application_persisted_relation_state":
        raise ValueError("player truce-expiry temporal semantics changed")
    if payload.get("status") == "available":
        expiry = payload.get("expiry_date_raw")
        if (payload["native_has_truce"] is not True or payload["actual_expiry_observable"] is not True
                or payload["same_frame_stable"] is not True or payload["readiness"] is not True
                or type(expiry) is not int or not expected_date_raw < expiry <= 2**31 - 1
                or payload.get("unavailable_reason") is not None):
            raise ValueError("available player truce-expiry observation is incomplete")
    elif payload.get("status") == "no_truce":
        if (payload["native_has_truce"] is not False or payload["actual_expiry_observable"] is not False
                or payload.get("expiry_date_raw") is not None or payload["same_frame_stable"] is not True
                or payload["readiness"] is not False or payload.get("unavailable_reason") != "native_has_truce_false"):
            raise ValueError("no-truce observation is malformed")
    else:
        raise ValueError("successful player truce-expiry transport cannot carry an unknown state")
    return dict(payload)
