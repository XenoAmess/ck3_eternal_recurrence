"""Exact-build paused phase-event evaluator observation, without battle odds."""

from __future__ import annotations


QUERY_COMBAT_PHASE_EVENT_TRACE_V1_CAPABILITY = (
    "game.command.query-combat-phase-event-trace-v1-N"
)
QUERY_COMBAT_PHASE_EVENT_TRACE_V1_STEP_PREFIX = (
    "query-combat-phase-event-trace-v1-"
)

_STOCK_KEYS = (
    "commander_none", "commander_wounded", "commander_maimed",
    "commander_killed", "knight_none", "knight_berserker_attack",
    "knight_become_berserker", "knight_shieldmaiden_attack",
    "knight_becomes_incapable", "knight_wounded", "knight_maimed",
    "knight_killed", "knight_qualify_for_accolade",
)
_ROW_KEYS = {
    "global_load_index", "type_load_index", "event_key", "event_type",
    "empty_effect", "selector_role_applicable", "trigger_valid",
    "chance_evaluated_for_differential", "selector_would_evaluate_chance",
    "chance_raw", "int_weight", "positive_weight", "selector_eligible",
}
_TRACE_KEYS = {
    "combat_id", "date_raw", "target_province_id", "phase_raw", "phase",
    "phase_day", "evaluator_probe_ready", "production_trace_ready",
    "same_paused_frame_stable", "real_combat_side_scope",
    "all_scope_teardowns_complete", "unavailable_reason",
    "missing_production_readers", "cadence",
    "global_rng_unchanged_by_probe", "characters",
}


def query_combat_phase_event_trace_v1_step(combat_id: int) -> str:
    if isinstance(combat_id, bool) or not isinstance(combat_id, int) or not 1 <= combat_id <= 2**31 - 1:
        raise ValueError("combat_id must be a positive full-generation int32")
    return f"{QUERY_COMBAT_PHASE_EVENT_TRACE_V1_STEP_PREFIX}{combat_id}"


def parse_query_combat_phase_event_trace_v1_step(step: str) -> int | None:
    if not isinstance(step, str) or not step.startswith(QUERY_COMBAT_PHASE_EVENT_TRACE_V1_STEP_PREFIX):
        return None
    digits = step[len(QUERY_COMBAT_PHASE_EVENT_TRACE_V1_STEP_PREFIX):]
    if not digits or digits[0] == "0" or not digits.isascii() or not digits.isdecimal():
        return None
    value = int(digits)
    return value if 1 <= value <= 2**31 - 1 else None


def normalize_combat_phase_event_trace_v1(value: object, *, combat_id: int) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _TRACE_KEYS:
        raise ValueError("combat phase-event trace has malformed keys")
    if value.get("combat_id") != combat_id:
        raise ValueError("combat phase-event trace CombatID mismatch")
    ready = value.get("evaluator_probe_ready")
    if not isinstance(ready, bool) or value.get("production_trace_ready") is not False:
        raise ValueError("combat phase-event readiness is malformed")
    for key in (
        "same_paused_frame_stable", "real_combat_side_scope",
        "all_scope_teardowns_complete", "global_rng_unchanged_by_probe",
    ):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"combat phase-event {key} is malformed")
    if not isinstance(value.get("unavailable_reason"), str):
        raise ValueError("combat phase-event unavailable reason is malformed")
    missing = value.get("missing_production_readers")
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        raise ValueError("combat phase-event missing reader list is malformed")
    cadence = value.get("cadence")
    if not isinstance(cadence, dict) or set(cadence) != {"period_days", "current_phase_fires_events"}:
        raise ValueError("combat phase-event cadence is malformed")
    characters = value.get("characters")
    if not isinstance(characters, list):
        raise ValueError("combat phase-event characters are malformed")
    if ready:
        if not all(value.get(key) is True for key in (
            "same_paused_frame_stable", "real_combat_side_scope",
            "all_scope_teardowns_complete", "global_rng_unchanged_by_probe",
        )) or not characters or not missing:
            raise ValueError("combat phase-event evaluator proof is incomplete")
        for character in characters:
            if not isinstance(character, dict) or set(character) != {
                "character_id", "side_index", "ordered_army_commander",
                "selected_side_commander", "ordered_knight", "event_rows",
            }:
                raise ValueError("combat phase-event character row is malformed")
            rows = character["event_rows"]
            if not isinstance(rows, list) or len(rows) != len(_STOCK_KEYS):
                raise ValueError("combat phase-event stock row count differs")
            for index, row in enumerate(rows):
                if not isinstance(row, dict) or set(row) != _ROW_KEYS or row.get("event_key") != _STOCK_KEYS[index] or row.get("global_load_index") != index:
                    raise ValueError("combat phase-event loaded stock row differs")
                for key in (
                    "empty_effect", "selector_role_applicable", "trigger_valid",
                    "chance_evaluated_for_differential",
                    "selector_would_evaluate_chance", "positive_weight",
                    "selector_eligible",
                ):
                    if not isinstance(row.get(key), bool):
                        raise ValueError("combat phase-event stock row flag is malformed")
    elif characters:
        raise ValueError("unavailable combat phase-event trace invented characters")
    return value
