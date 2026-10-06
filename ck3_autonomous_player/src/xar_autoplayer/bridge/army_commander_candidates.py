"""Read-only commander candidates for a current player-controlled CUnit."""

from __future__ import annotations

from .public_unit_contract import canonical_public_cunit_token, public_cunit_id
from .army_commander_target_rolls import (
    commander_target_province_id,
    normalize_candidate_target_roll_bounds,
)


QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY = (
    "game.command.query-army-commander-candidates-v1-for-army-N"
)
QUERY_ARMY_COMMANDER_CANDIDATES_V1_FOR_TARGET_CAPABILITY = (
    "game.command.query-army-commander-candidates-v1-for-army-N-at-province-P"
)
QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX = (
    "query-army-commander-candidates-v1-for-army-"
)


def query_army_commander_candidates_v1_step(
    army_id: int, *, target_province_id: int | None = None
) -> str:
    subject = public_cunit_id(army_id, "army_id")
    step = f"{QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX}{subject}"
    if target_province_id is None:
        return step
    target = commander_target_province_id(target_province_id)
    return f"{step}-at-province-{target}"


def parse_query_army_commander_candidates_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX
    ):
        return None
    return canonical_public_cunit_token(
        step.removeprefix(QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX)
    )


def parse_query_army_commander_candidates_v1_for_target_step(
    step: object,
) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX
    ):
        return None
    subject_token, separator, target_token = step.removeprefix(
        QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX
    ).partition("-at-province-")
    if not separator:
        return None
    subject = canonical_public_cunit_token(subject_token)
    target = canonical_public_cunit_token(target_token)
    if subject is None or target is None or target == 0:
        return None
    return subject, target


def commander_query_army_scope(
    snapshot: dict[str, object], army_id: int
) -> dict[str, object]:
    subject = public_cunit_id(army_id, "army_id")
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        raise ValueError("commander query requires current player_armies")
    matches = [
        row for row in armies
        if isinstance(row, dict)
        and type(row.get("army_id")) is int
        and row.get("army_id") == subject
        and row.get("controllable") is True
    ]
    if len(matches) != 1:
        raise ValueError("army_id is outside the current controllable player scope")
    return matches[0]


def normalize_army_commander_candidates_v1(
    value: object,
    *,
    expected_army_id: int,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_target_province_id: int | None = None,
) -> dict[str, object]:
    """Keep native eligibility, quality and independent unit/target reads distinct."""
    if not isinstance(value, dict):
        raise ValueError("native army_commander_candidates must be an object")
    if (
        value.get("schema") != "ck3_12003_army_commander_candidates_v1"
        or value.get("status") not in {"available", "partial", "unavailable"}
        or type(value.get("snapshot_revision")) is not int
        or value.get("snapshot_revision") != expected_snapshot_revision
        or type(value.get("date_raw")) is not int
        or value.get("date_raw") != expected_date_raw
        or type(value.get("army_id")) is not int
        or value.get("army_id") != public_cunit_id(expected_army_id, "army_id")
    ):
        raise ValueError("native army_commander_candidates frame binding disagrees")
    if expected_target_province_id is None:
        if value.get("target_province_id") is not None:
            raise ValueError("native commander target header was not requested")
    else:
        expected_target_province_id = commander_target_province_id(
            expected_target_province_id
        )
        if (
            type(value.get("target_province_id")) is not int
            or value.get("target_province_id") != expected_target_province_id
        ):
            raise ValueError("native commander target header disagrees")
    for name in ("native_carmy_id", "owner_character_id"):
        _optional_id(value.get(name), name)
    if (
        type(value.get("eligibility_mode")) is not int
        or value.get("eligibility_mode") != 1
        or value.get("collection_filter_now") is not False
        or value.get("collection_allow_guests") is not True
    ):
        raise ValueError("native commander candidates use the wrong player collection")
    current = value.get("current_commander")
    if not isinstance(current, dict) or current.get("status") not in {
        "available", "absent", "unavailable"
    }:
        raise ValueError("native current commander observation is malformed")
    current_id = _optional_id(current.get("character_id"), "current_commander.character_id")
    if (
        current.get("status") == "available" and current_id is None
        or current.get("status") == "absent" and current_id is not None
    ):
        raise ValueError("native current commander absence disagrees with its ID")
    _reason(current.get("unavailable_reason"), "current_commander.unavailable_reason")
    if type(value.get("candidate_collection_complete")) is not bool:
        raise ValueError("native candidate collection completion must be boolean")
    count = value.get("candidate_source_count")
    if type(count) is not int or count < 0:
        raise ValueError("native candidate_source_count must be non-negative")
    candidates = value.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("native commander candidates must be a list")
    copied_candidates = []
    for index, row in enumerate(candidates):
        if not isinstance(row, dict):
            raise ValueError(f"native commander candidate {index} must be an object")
        _optional_id(row.get("character_id"), "candidate.character_id")
        for name in ("available", "final_eligibility_observable", "quality_observable"):
            if type(row.get(name)) is not bool:
                raise ValueError(f"native candidate.{name} must be boolean")
        can_assign = row.get("can_assign")
        if (
            row["final_eligibility_observable"] and type(can_assign) is not bool
            or not row["final_eligibility_observable"] and can_assign is not None
        ):
            raise ValueError("native candidate CanAssign observation is malformed")
        for name in ("native_ai_base_quality", "generic_advantage_points"):
            amount = row.get(name)
            if (
                row["quality_observable"]
                and (type(amount) is not int or not -(2**31) <= amount <= 2**31 - 1)
                or not row["quality_observable"] and amount is not None
            ):
                raise ValueError(f"native candidate.{name} observation is malformed")
        # Older frozen readers omit this new observation; retain null,
        # never infer a zero modifier from generic quality or traits.
        phase_raw = row.get("siege_phase_time_modifier_raw")
        if phase_raw is not None and (
            type(phase_raw) is not int
            or not -(2**63) <= phase_raw <= 2**63 - 1
        ):
            raise ValueError("native candidate.siege_phase_time_modifier_raw must be signed Q100000 int64 or null")
        _reason(row.get("unavailable_reason"), "candidate.unavailable_reason")
        copied_row = {**row, "siege_phase_time_modifier_raw": phase_raw}
        # Missing remains missing and explicit null remains null. Target
        # observation never changes pool completeness, quality or CanAssign.
        if "target_roll_bounds" in row:
            copied_row["target_roll_bounds"] = normalize_candidate_target_roll_bounds(
                row["target_roll_bounds"],
                expected_target_province_id=expected_target_province_id,
            )
        copied_candidates.append(copied_row)
    _reason(value.get("unavailable_reason"), "unavailable_reason")
    normalized = {
        **value, "current_commander": dict(current), "candidates": copied_candidates
    }
    # Older frozen readers have no selected-unit speed block. Preserve that
    # absence rather than manufacture zero rates or commander-derived speeds.
    if "current_movement_speed" in value:
        normalized["current_movement_speed"] = _normalize_current_movement_speed(
            value["current_movement_speed"],
            expected_army_id=expected_army_id,
            expected_native_carmy_id=value.get("native_carmy_id"),
            expected_owner_character_id=value.get("owner_character_id"),
            expected_current_commander=current,
            expected_snapshot_revision=expected_snapshot_revision,
            expected_date_raw=expected_date_raw,
        )
    return normalized


def _normalize_current_movement_speed(
    value: object,
    *,
    expected_army_id: int,
    expected_native_carmy_id: object,
    expected_owner_character_id: object,
    expected_current_commander: dict[str, object],
    expected_snapshot_revision: int,
    expected_date_raw: int,
) -> dict[str, object] | None:
    """Retain independent native total rates for the selected current CUnit."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("native current_movement_speed must be an object or null")
    if (
        value.get("schema") != "ck3_12003_army_current_movement_speed_v1"
        or value.get("source") != "native_selected_cunit_movement_rates"
        or type(value.get("snapshot_revision")) is not int
        or value.get("snapshot_revision") != expected_snapshot_revision
        or type(value.get("date_raw")) is not int
        or value.get("date_raw") != expected_date_raw
        or type(value.get("context_observable")) is not bool
    ):
        raise ValueError("native current_movement_speed frame/source is malformed")
    context_observable = value["context_observable"]
    identity_fields = (
        "public_cunit_id", "native_carmy_id", "owner_character_id",
        "current_commander_character_id",
    )
    for name in identity_fields:
        _optional_id(value.get(name), f"current_movement_speed.{name}")
    for name in ("current_province_id", "move_target_province_id"):
        amount = value.get(name)
        if amount is not None and (
            type(amount) is not int or not 1 <= amount <= 2**31 - 1
        ):
            raise ValueError(f"current_movement_speed.{name} must be a ProvinceID or null")
    count = value.get("route_source_count")
    if count is not None and (
        type(count) is not int or not 0 <= count <= 2**31 - 1
    ):
        raise ValueError("current_movement_speed.route_source_count must be non-negative or null")
    if value.get("route_read_status") not in {
        "not_attempted", "complete_empty", "complete_nonempty", "target_only",
        "invalid_header", "unresolved_entry",
    }:
        raise ValueError("native current_movement_speed route_read_status is malformed")
    if context_observable:
        if (
            value.get("public_cunit_id") != public_cunit_id(expected_army_id, "army_id")
            or value.get("native_carmy_id") is None
            or value.get("owner_character_id") is None
            or expected_native_carmy_id is not None
            and value.get("native_carmy_id") != expected_native_carmy_id
            or expected_owner_character_id is not None
            and value.get("owner_character_id") != expected_owner_character_id
        ):
            raise ValueError("native current_movement_speed selected-unit identity disagrees")
        if (
            expected_current_commander.get("status") in {"available", "absent"}
            and value.get("current_commander_character_id")
            != expected_current_commander.get("character_id")
        ):
            raise ValueError("native current_movement_speed current commander disagrees")
        state_code = value.get("army_state_code")
        if (
            type(state_code) is not int or not -(2**31) <= state_code <= 2**31 - 1
            or not isinstance(value.get("army_state"), str)
            or type(value.get("in_combat")) is not bool
            or type(value.get("retreating")) is not bool
        ):
            raise ValueError("native current_movement_speed army state is malformed")
    elif any(value.get(name) is not None for name in (
        *identity_fields, "current_province_id", "move_target_province_id",
        "route_source_count", "army_state_code", "army_state", "in_combat",
        "retreating",
    )):
        raise ValueError("unavailable current_movement_speed context must retain null fields")
    normalized = dict(value)
    for name, getter in (
        ("land", "0x24AA940"),
        ("naval", "0x24AAC00"),
        ("current_edge", "0x24AB5C0"),
    ):
        rate = value.get(name)
        if not isinstance(rate, dict):
            raise ValueError(f"native current_movement_speed.{name} must be an object")
        status = rate.get("status")
        allowed = {"available", "unavailable"}
        if name == "current_edge":
            allowed.add("not_applicable")
        if (
            status not in allowed
            or type(rate.get("scale")) is not int
            or rate.get("scale") != 100000
            or rate.get("native_getter_rva") != getter
        ):
            raise ValueError(f"native current_movement_speed.{name} status/scale/source is malformed")
        raw = rate.get("raw")
        if (
            status == "available"
            and (type(raw) is not int or not -(2**63) <= raw <= 2**63 - 1)
            or status != "available" and raw is not None
        ):
            raise ValueError(f"native current_movement_speed.{name}.raw must match its native status")
        _reason(rate.get("unavailable_reason"), f"current_movement_speed.{name}.unavailable_reason")
        if status == "not_applicable" and (
            value.get("route_read_status") != "complete_empty"
            or rate.get("unavailable_reason") != "empty_route"
        ):
            raise ValueError("native current edge is not applicable only for an observed empty route")
        normalized[name] = dict(rate)
    return normalized


def _optional_id(value: object, name: str) -> int | None:
    if value is not None and (type(value) is not int or not 0 <= value <= 2**31 - 1):
        raise ValueError(f"{name} must be a full native int32 ID or null")
    return value


def _reason(value: object, name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
