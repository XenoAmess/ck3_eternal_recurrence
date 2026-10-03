"""Read-only commander candidates for a current player-controlled CUnit."""

from __future__ import annotations

from .public_unit_contract import canonical_public_cunit_token, public_cunit_id


QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY = (
    "game.command.query-army-commander-candidates-v1-for-army-N"
)
QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX = (
    "query-army-commander-candidates-v1-for-army-"
)


def query_army_commander_candidates_v1_step(army_id: int) -> str:
    subject = public_cunit_id(army_id, "army_id")
    return f"{QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX}{subject}"


def parse_query_army_commander_candidates_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX
    ):
        return None
    return canonical_public_cunit_token(
        step.removeprefix(QUERY_ARMY_COMMANDER_CANDIDATES_V1_STEP_PREFIX)
    )


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
) -> dict[str, object]:
    """Keep native eligibility and quality observations distinct."""
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
        copied_candidates.append({**row, "siege_phase_time_modifier_raw": phase_raw})
    _reason(value.get("unavailable_reason"), "unavailable_reason")
    return {**value, "current_commander": dict(current), "candidates": copied_candidates}


def _optional_id(value: object, name: str) -> int | None:
    if value is not None and (type(value) is not int or not 0 <= value <= 2**31 - 1):
        raise ValueError(f"{name} must be a full native int32 ID or null")
    return value


def _reason(value: object, name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
