"""Default-off, paused, one-army actor role read with no gameplay action."""

from __future__ import annotations

import copy
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError

STEP_PREFIX = "query-war-actor-army-role-v1-"
_SCHEMA = "xar.war.actor-army-role-private.v1"
_PAYLOAD_KEYS = {
    "schema", "private_build", "read_only", "status", "unavailable_stage",
    "native_revision", "date_raw", "actor_character_id", "war_id", "public_army_id",
    "native_carmy_id", "owner_character_id", "current_province_id",
    "army_state", "in_combat", "retreating", "commander_status",
    "commander_character_id", "is_commander_of_requested_army",
    "knight_status", "knight_regiment_id", "is_knight_in_requested_army",
    "global_commander_or_knight_status", "safe_role_release", "date_credit",
}


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= 2**31 - 1:
        raise ValueError(f"{label} must be a positive int32")
    return value


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    diagnostics = snapshot.get("diagnostics")
    return (
        snapshot.get("episode_run_id"), snapshot.get("episode_character_id"),
        copy.deepcopy(diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None),
        copy.deepcopy(diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None),
        copy.deepcopy(diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None),
        snapshot.get("snapshot_id"), snapshot.get("revision"),
        snapshot.get("native_revision"), snapshot.get("date_raw"),
        snapshot.get("paused"), snapshot.get("map_ready"),
        copy.deepcopy(snapshot.get("played_character")),
        copy.deepcopy(snapshot.get("active_event")),
        copy.deepcopy(snapshot.get("pending_character_interaction")),
        copy.deepcopy(snapshot.get("hello_capabilities")),
        tuple(sorted((key, copy.deepcopy(value)) for key, value in snapshot.items()
                     if key.endswith("_supported") or key.endswith("_query_supported"))),
        copy.deepcopy(snapshot.get("player_armies")),
        copy.deepcopy(snapshot.get("active_wars")),
    )


def _role_bool(value: object, label: str) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise ValueError(f"{label} must be bool or null")
    return value


def _normalize(row: object, *, before: Mapping[str, object], actor: int,
               war_id: int, army_id: int) -> dict[str, object]:
    if not isinstance(row, Mapping) or set(row) != _PAYLOAD_KEYS:
        raise ValueError("role payload key set changed")
    if (row["schema"] != _SCHEMA or row["private_build"] is not True
            or row["read_only"] is not True
            or row["status"] not in {"available", "partial", "unavailable"}
            or isinstance(row["native_revision"], bool)
            or not isinstance(row["native_revision"], int)
            or row["native_revision"] != before.get("native_revision")
            or isinstance(row["date_raw"], bool)
            or not isinstance(row["date_raw"], int)
            or row["date_raw"] != before.get("date_raw")
            or isinstance(row["actor_character_id"], bool)
            or row["actor_character_id"] != actor
            or isinstance(row["war_id"], bool)
            or row["war_id"] != war_id
            or isinstance(row["public_army_id"], bool)
            or row["public_army_id"] != army_id
            or row["global_commander_or_knight_status"] != "unknown"
            or row["safe_role_release"] is not None
            or row["date_credit"] is not False):
        raise ValueError("role payload identity or policy changed")
    if not isinstance(row["unavailable_stage"], (str, type(None))):
        raise ValueError("unavailable stage malformed")
    if row["status"] == "available" and row["unavailable_stage"] is not None:
        raise ValueError("available role has unavailable stage")
    if row["status"] != "available" and not row["unavailable_stage"]:
        raise ValueError("partial/unavailable role needs typed stage")
    if not isinstance(row["army_state"], str) or not row["army_state"]:
        raise ValueError("army state malformed")
    if any(row[field] is not None and not isinstance(row[field], bool)
           for field in ("in_combat", "retreating")):
        raise ValueError("army state flags malformed")
    if row["status"] == "unavailable" and any(
        row[field] is not None for field in ("in_combat", "retreating")
    ):
        raise ValueError("unavailable role leaked army state flags")
    for field in ("native_carmy_id", "owner_character_id", "current_province_id",
                  "commander_character_id", "knight_regiment_id"):
        value = row[field]
        if value is not None:
            _positive(value, field)
    commander = _role_bool(row["is_commander_of_requested_army"], "commander")
    knight = _role_bool(row["is_knight_in_requested_army"], "knight")
    if (row["commander_status"] not in {"available", "absent", "unknown"}
            or row["knight_status"] not in {"available", "absent", "unknown"}):
        raise ValueError("role status malformed")
    if row["commander_status"] == "unknown" and (
        commander is not None or row["commander_character_id"] is not None
    ):
        raise ValueError("unknown commander cannot have boolean")
    if row["commander_status"] == "available" and (
        commander is None
        or row["commander_character_id"] is None
        or commander is not (row["commander_character_id"] == actor)
    ):
        raise ValueError("available commander identity changed")
    if row["knight_status"] == "unknown" and (
        knight is not None or row["knight_regiment_id"] is not None
    ):
        raise ValueError("unknown knight cannot have boolean")
    if row["knight_status"] == "available" and (
        knight is not True or row["knight_regiment_id"] is None
    ):
        raise ValueError("available knight identity changed")
    if row["commander_status"] == "absent" and (
        commander is not False or row["commander_character_id"] is not None
    ):
        raise ValueError("absent commander shape changed")
    if row["knight_status"] == "absent" and (
        knight is not False or row["knight_regiment_id"] is not None
    ):
        raise ValueError("absent knight shape changed")
    if knight is True and row["knight_regiment_id"] is None:
        raise ValueError("knight membership lacks regiment")
    if commander is True and row["commander_character_id"] != actor:
        raise ValueError("commander actor mismatch")
    if row["status"] == "available" and (commander is None or knight is None):
        raise ValueError("available role has unknown field")
    if row["status"] == "available" and row["current_province_id"] is None:
        raise ValueError("available role lacks current province")
    if row["status"] == "partial" and commander is not None and knight is not None:
        raise ValueError("partial role has no unknown field")
    if row["status"] != "unavailable" and (
        row["native_carmy_id"] is None or row["owner_character_id"] != actor
        or row["in_combat"] is None or row["retreating"] is None
    ):
        raise ValueError("bound army identity or state incomplete")
    if row["status"] == "unavailable" and any(
        row[field] is not None for field in
        ("native_carmy_id", "is_commander_of_requested_army",
         "is_knight_in_requested_army")
    ):
        raise ValueError("unavailable role leaked an assignment")
    return dict(row)


def query_actor_army_role_private_v1(
    driver: object, *, actor_character_id: int, public_army_id: int,
    expected_war_id: int, expected_episode_run_id: str,
    expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_actor_army_role_query", False) is not True:
        raise UnsupportedStepError("private actor army role query is disabled")
    actor = _positive(actor_character_id, "actor_character_id")
    army_id = _positive(public_army_id, "public_army_id")
    war_id = _positive(expected_war_id, "expected_war_id")
    if not isinstance(expected_episode_run_id, str) or not expected_episode_run_id:
        raise ValueError("expected_episode_run_id must be nonempty")
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    player = before.get("played_character")
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    armies = before.get("player_armies")
    wars = before.get("active_wars")
    diagnostics = before.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None
    bridge_pid = diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    matching_wars = [row for row in wars if isinstance(row, Mapping) and row.get("war_id") == war_id] if isinstance(wars, list) else []
    allied = matching_wars[0].get("allied_armies") if len(matching_wars) == 1 else None
    if (before.get("revision") != expected_revision
            or before.get("episode_run_id") != expected_episode_run_id
            or before.get("episode_character_id") != actor
            or isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0
            or isinstance(bridge_pid, bool) or not isinstance(bridge_pid, int) or bridge_pid <= 0
            or diagnostics.get("connected") is not True
            or not isinstance(hello, Mapping)
            or before.get("paused") is not True
            or before.get("map_ready") is not True
            or not isinstance(player, Mapping)
            or player.get("alive") is not True
            or player.get("character_id") != actor
            or isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or native_revision <= 0
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not isinstance(armies, list)
            or sum(isinstance(row, Mapping) and row.get("army_id") == army_id
                   for row in armies) != 1
            or not any(isinstance(row, Mapping) and row.get("army_id") == army_id
                       and row.get("owner_character_id") == actor for row in armies)
            or not isinstance(allied, list)
            or sum(isinstance(row, Mapping) and row.get("army_id") == army_id
                   for row in allied) != 1
            or not any(isinstance(row, Mapping) and row.get("army_id") == army_id
                       and row.get("owner_character_id") == actor for row in allied)):
        raise BridgeUnavailableError("actor army role requires exact episode, war and one current paused owned allied army")
    request_id = "war-actor-army-role-" + uuid.uuid4().hex
    step = STEP_PREFIX + str(actor) + "-" + str(war_id) + "-" + str(army_id)
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None or frame.get("type") != "command_result" or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id:
        raise BridgeUnavailableError("actor army role command_result missing or mismatched")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("actor army role native query RED: " + str(frame.get("error")))
    result = frame.get("result")
    if (not isinstance(result, Mapping)
            or set(result) != {"step", "accepted", "status", "private_build",
                                   "read_only", "actor_army_role", "backend_id"}
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "partial", "unavailable"}
            or result.get("private_build") is not True
            or result.get("read_only") is not True
            or result.get("backend_id") != "native-headless"):
        raise BridgeUnavailableError("actor army role envelope changed")
    try:
        role = _normalize(result["actor_army_role"], before=before,
                          actor=actor, war_id=war_id, army_id=army_id)
    except ValueError as error:
        raise BridgeUnavailableError(f"actor army role payload malformed: {error}") from error
    if result["status"] != role["status"]:
        raise BridgeUnavailableError("actor army role status mismatch")
    after = driver.take_snapshot()
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError("actor army role crossed its paused frame")
    return {
        "status": role["status"], "private_build": True, "read_only": True,
        "advertised": False, "backend_id": "native-headless",
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "queried_episode_run_id": expected_episode_run_id,
        "queried_war_id": war_id,
        "queried_connection_generation": generation,
        "queried_bridge_pid": bridge_pid,
        "date_raw": date_raw, "actor_army_role": role,
        "global_role_ready": False, "safe_role_release_ready": False,
        "date_advance_ready": False,
    }
