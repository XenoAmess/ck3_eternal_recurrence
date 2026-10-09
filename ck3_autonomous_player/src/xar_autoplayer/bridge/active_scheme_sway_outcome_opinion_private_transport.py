"""Independent exact-1.20 Sway material opinion read, without an event window.

The native producer measures the selected target's opinion of the actor and
its two dedicated modifiers. It supplies no phase or terminal attribution.
"""
from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, private_g2_query_snapshot_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, CK3_12004


STEP = "query-sway-outcome-opinion-v1-private"
SCHEMA = "xar.ck3.sway-outcome-opinion-v1"
PERMISSION = "allow_private_active_scheme_sway_outcome_opinion_query"
_KEYS = {
    "schema", "build", "available", "unavailable_reason", "snapshot_revision", "date_raw",
    "actor_character_id", "target_character_id", "target_opinion_of_actor",
    "scheme_sway_opinion", "sway_blocker_opinion", "instance_terminal_outcome_observed", "cancel_outcome_observed",
}


def _int32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value <= (1 << 31) - 1


def normalize_active_scheme_sway_outcome_opinion_v1(
    value: object, *, snapshot: Mapping[str, object], target_character_id: int,
) -> dict[str, object]:
    """Preserve actual raw modifier points, presence and legal zero separately."""
    if not isinstance(value, dict) or set(value) != _KEYS or value.get("schema") != SCHEMA:
        raise ValueError("native sway material-opinion schema is malformed")
    build = private_native_build_identity(snapshot)
    if build not in (CK3_12002, CK3_12003, CK3_12004) or value["build"] != build.game_version:
        raise ValueError("native sway material-opinion belongs to another exact build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or value["actor_character_id"] != actor.get("character_id")
            or value["target_character_id"] != target_character_id
            or value["snapshot_revision"] != snapshot.get("native_revision")
            or value["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native sway material-opinion differs from its current player/pair/frame")
    if (type(value["available"]) is not bool or not isinstance(value["unavailable_reason"], str)
            or value["instance_terminal_outcome_observed"] is not False
            or value["cancel_outcome_observed"] is not False
            or (value["available"] and not _int32(value["target_opinion_of_actor"]))
            or (not value["available"] and value["target_opinion_of_actor"] is not None)):
        raise ValueError("native sway material-opinion scalar fields are malformed")
    output = dict(value)
    for key in ("scheme_sway_opinion", "sway_blocker_opinion"):
        modifier = value[key]
        if (not isinstance(modifier, dict) or set(modifier) != {"observed", "present", "value"}
                or type(modifier["observed"]) is not bool or type(modifier["present"]) is not bool
                or (value["available"] and modifier["observed"] is not True)
                or (modifier["present"] and (modifier["observed"] is not True or not _int32(modifier["value"])))
                or (not modifier["present"] and modifier["value"] is not None)):
            raise ValueError("native sway material-opinion modifier measurement is malformed: " + key)
        output[key] = dict(modifier)
    return output


def query_active_scheme_sway_outcome_opinion_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if type(target_character_id) is not int or not 0 < target_character_id < (1 << 31):
        raise ValueError("private sway material-opinion target must be a positive full character ID")
    actor = private_g2_query_snapshot_v1(
        driver, include_native_command_history=False).get("played_character")
    if not isinstance(actor, Mapping) or type(actor.get("character_id")) is not int:
        raise BridgeUnavailableError("private sway material-opinion lacks the current player")
    if actor["character_id"] == target_character_id:
        raise ValueError("private sway material-opinion target must differ from the player")
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"actor_character_id": actor["character_id"], "target_character_id": target_character_id},
        timeout_seconds=timeout_seconds,
        include_native_command_history=False,
    )
    try:
        value = normalize_active_scheme_sway_outcome_opinion_v1(
            result.get("sway_outcome_opinion"), snapshot=before, target_character_id=target_character_id,
        )
        if (result.get("backend_id") != "native-headless"
                or result.get("status") != ("available" if value["available"] else "unavailable")):
            raise ValueError("native sway material-opinion envelope disagrees with its measurement")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "status": result["status"], "backend_id": result["backend_id"]}
