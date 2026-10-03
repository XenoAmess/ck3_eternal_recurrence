"""Typed native commander assignment and independent observer verification."""

from __future__ import annotations

from .public_unit_contract import canonical_public_cunit_token, public_cunit_id


ASSIGN_ARMY_COMMANDER_V1_CAPABILITY = (
    "game.command.assign-army-commander-v1-army-N-to-character-N"
)
ASSIGN_ARMY_COMMANDER_V1_STEP_PREFIX = "assign-army-commander-v1-army-"
ARMY_COMMANDER_ASSIGNMENT_V1_SCHEMA = "ck3_12003_army_commander_assignment_v1"


def assign_army_commander_v1_step(army_id: int, commander_character_id: int) -> str:
    army = public_cunit_id(army_id, "army_id")
    commander = _character_id(commander_character_id, "commander_character_id")
    return f"{ASSIGN_ARMY_COMMANDER_V1_STEP_PREFIX}{army}-to-character-{commander}"


def parse_assign_army_commander_v1_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith(ASSIGN_ARMY_COMMANDER_V1_STEP_PREFIX):
        return None
    pieces = step.removeprefix(ASSIGN_ARMY_COMMANDER_V1_STEP_PREFIX).split("-to-character-")
    if len(pieces) != 2:
        return None
    army = canonical_public_cunit_token(pieces[0])
    character = canonical_public_cunit_token(pieces[1])
    if army is None or character is None:
        return None
    return army, character


def normalize_army_commander_assignment_v1(
    result: object,
    *,
    expected_army_id: int,
    expected_commander_character_id: int,
    expected_snapshot_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    step = assign_army_commander_v1_step(expected_army_id, expected_commander_character_id)
    if not isinstance(result, dict) or (
        result.get("step") != step
        or type(result.get("accepted")) is not bool
        or result.get("snapshot_revision") != expected_snapshot_revision
        or result.get("date_raw") != expected_date_raw
    ):
        raise ValueError("native commander assignment envelope disagrees with its source frame")
    value = result.get("army_commander_assignment")
    if not isinstance(value, dict) or (
        value.get("schema") != ARMY_COMMANDER_ASSIGNMENT_V1_SCHEMA
        or value.get("status") not in {"unavailable", "rejected", "submitted", "already_assigned"}
        or value.get("army_id") != expected_army_id
        or value.get("requested_commander_character_id") != expected_commander_character_id
    ):
        raise ValueError("native commander assignment identity/status is malformed")
    for key in ("native_carmy_id", "owner_character_id", "prior_commander_character_id"):
        if value.get(key) is not None:
            _character_id(value[key], key)
    for key in ("final_eligibility_observable", "native_command_validation_observable", "command_submitted", "verification_pending"):
        if type(value.get(key)) is not bool:
            raise ValueError(f"native commander assignment {key} must be boolean")
    for key in ("can_assign", "native_command_valid"):
        if value.get(key) is not None and type(value[key]) is not bool:
            raise ValueError(f"native commander assignment {key} must be boolean or null")
    if (
        value["final_eligibility_observable"] and type(value.get("can_assign")) is not bool
        or not value["final_eligibility_observable"] and value.get("can_assign") is not None
    ):
        raise ValueError("native commander assignment final eligibility disagrees with its observation status")
    if (
        value["native_command_validation_observable"] and type(value.get("native_command_valid")) is not bool
        or not value["native_command_validation_observable"] and value.get("native_command_valid") is not None
    ):
        raise ValueError("native commander command validity disagrees with its observation status")
    if value.get("unavailable_reason") is not None and not isinstance(value["unavailable_reason"], str):
        raise ValueError("native commander assignment reason must be a string or null")
    submitted = value["status"] == "submitted"
    if value["command_submitted"] is not submitted or value["verification_pending"] is not submitted:
        raise ValueError("native commander assignment submission status disagrees")
    if submitted and (
        result["accepted"] is not True
        or value.get("native_carmy_id") is None
        or value.get("owner_character_id") is None
        or value.get("can_assign") is not True
        or value.get("native_command_validation_observable") is not True
        or value.get("native_command_valid") is not True
    ):
        raise ValueError("native commander assignment submitted without validated native context")
    return dict(value)


def commander_assignment_readback_v1(
    assignment: dict[str, object],
    readback: dict[str, object],
    *,
    expected_date_raw: int,
) -> dict[str, object]:
    """Verify native observed identities; the requested ID alone proves nothing."""
    current = readback.get("current_commander")
    context_matches = (
        readback.get("status") in {"available", "partial"}
        and readback.get("date_raw") == expected_date_raw
        and readback.get("army_id") == assignment["army_id"]
        and assignment.get("native_carmy_id") is not None
        and readback.get("native_carmy_id") == assignment["native_carmy_id"]
        and assignment.get("owner_character_id") is not None
        and readback.get("owner_character_id") == assignment["owner_character_id"]
    )
    commander_matches = (
        isinstance(current, dict)
        and current.get("status") == "available"
        and current.get("character_id") == assignment["requested_commander_character_id"]
    )
    verified = context_matches and commander_matches
    return {
        "status": "verified" if verified else "verification_pending",
        "verified": verified,
        "army_context_matches": context_matches,
        "commander_matches": commander_matches,
        "observed_army_id": readback.get("army_id"),
        "observed_native_carmy_id": readback.get("native_carmy_id"),
        "observed_owner_character_id": readback.get("owner_character_id"),
        "observed_commander_character_id": current.get("character_id") if isinstance(current, dict) else None,
        "observed_date_raw": readback.get("date_raw"),
        "observed_snapshot_revision": readback.get("snapshot_revision"),
    }


def _character_id(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a non-negative full native int32 ID")
    return value
