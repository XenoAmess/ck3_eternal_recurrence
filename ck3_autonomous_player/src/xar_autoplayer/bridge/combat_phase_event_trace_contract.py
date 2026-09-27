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

_COUNTER_OUTPUT_SOURCE = "native_resolve_counter_classes_after_0x23caf20"
_COUNTER_OUTPUT_FAILURE_FLAG = 1 << 20
_COUNTER_OUTPUT_ROW_KEYS = {
    "side_index", "countered_entry_count", "countering_entry_count",
    "context_raw", "class_count", "capacity", "retention_raw",
}
_COUNTER_OUTPUT_KEYS = {
    "source", "requested", "pair_complete", "count", "sides",
}
_COUNTER_OUTPUT_DIAGNOSTIC_KEYS = {
    "hook_calls", "target_calls", "first_failure_gate",
}
_EXPERIMENTAL_TRACE_FINISH_STEP = "experimental-combat-phase-event-trace-finish-v1"


def _bounded_int(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_runtime_counter_output_diagnostic_v1(
    managed_result: object,
) -> dict[str, object] | None:
    """Project the opt-in native counter readout as diagnostic evidence only.

    Old managed traces have no counter output and return ``None``. This helper
    never promotes an unverified readout to a forecast input.
    """
    if not isinstance(managed_result, dict):
        raise ValueError("managed combat trace is malformed")
    trace = managed_result.get("trace")
    if not isinstance(trace, dict):
        raise ValueError("managed combat trace lacks raw trace")
    if "runtime_counter_output" not in trace:
        return None
    output = trace["runtime_counter_output"]
    if not isinstance(output, dict) or set(output) not in (
        _COUNTER_OUTPUT_KEYS,
        _COUNTER_OUTPUT_KEYS | _COUNTER_OUTPUT_DIAGNOSTIC_KEYS,
    ):
        raise ValueError("runtime counter output has malformed keys")
    if _COUNTER_OUTPUT_DIAGNOSTIC_KEYS <= set(output):
        hook_calls = output["hook_calls"]
        target_calls = output["target_calls"]
        first_failure_gate = output["first_failure_gate"]
        if (not _bounded_int(hook_calls, 0, 2**32 - 1)
                or not _bounded_int(target_calls, 0, hook_calls)
                or not _bounded_int(first_failure_gate, 0, 5)
                or (first_failure_gate != 0 and target_calls == 0)):
            raise ValueError("runtime counter output diagnostic counters differ")
    if output["source"] != _COUNTER_OUTPUT_SOURCE or output["requested"] is not True:
        raise ValueError("runtime counter output source or request differs")
    pair_complete = output["pair_complete"]
    sides = output["sides"]
    count = output["count"]
    if (type(pair_complete) is not bool or not _bounded_int(count, 0, 2)
            or not isinstance(sides, list) or len(sides) != count):
        raise ValueError("runtime counter output pair shape is malformed")
    class_counts = []
    for index, side in enumerate(sides):
        if not isinstance(side, dict) or set(side) != _COUNTER_OUTPUT_ROW_KEYS:
            raise ValueError("runtime counter output side keys are malformed")
        if side["side_index"] != index or type(side["side_index"]) is not int:
            raise ValueError("runtime counter output side order differs")
        if not all(_bounded_int(side[key], 0, 2048) for key in (
            "countered_entry_count", "countering_entry_count",
        )):
            raise ValueError("runtime counter output entry count is malformed")
        if not _bounded_int(side["context_raw"], -(2**63), 2**63 - 1):
            raise ValueError("runtime counter output context is malformed")
        class_count = side["class_count"]
        capacity = side["capacity"]
        values = side["retention_raw"]
        if (not _bounded_int(class_count, 1, 4096)
                or not _bounded_int(capacity, class_count, 4096)
                or not isinstance(values, list) or len(values) != class_count
                or not all(_bounded_int(value, -(2**63), 2**63 - 1)
                           for value in values)):
            raise ValueError("runtime counter output vector is malformed")
        class_counts.append(class_count)
    if pair_complete and (count != 2 or class_counts[0] != class_counts[1]):
        raise ValueError("runtime counter output pair is incomplete")

    readiness = trace.get("readiness")
    checkpoint = managed_result.get("managed_checkpoint")
    failure_flags = trace.get("failure_flags")
    if (not _bounded_int(managed_result.get("schema_version"), 1, 1)
            or not _bounded_int(trace.get("schema_version"), 1, 1)
            or type(trace.get("status")) is not str
            or trace["status"] not in {"captured", "failed"}
            or not _bounded_int(failure_flags, 0, 2**32 - 1)
            or not isinstance(readiness, dict)
            or type(readiness.get("runtime_counter_output_pair_complete")) is not bool
            or readiness["runtime_counter_output_pair_complete"] is not pair_complete
            or type(readiness.get("bounded_capture_complete")) is not bool
            or not isinstance(checkpoint, dict)
            or any(type(checkpoint.get(key)) is not bool for key in (
                "recoverable_checkpoint_created", "exact_one_day_observed",
                "boundary_dates_match_checkpoint", "detours_uninstalled",
            ))):
        raise ValueError("runtime counter output evidence gates are malformed")
    if bool(failure_flags & _COUNTER_OUTPUT_FAILURE_FLAG) is pair_complete:
        raise ValueError("runtime counter output failure flag contradicts pair")
    observation_complete = (
        pair_complete and trace["status"] == "captured"
        and failure_flags == 0
        and readiness["bounded_capture_complete"]
        and all(checkpoint[key] for key in (
            "recoverable_checkpoint_created", "exact_one_day_observed",
            "boundary_dates_match_checkpoint", "detours_uninstalled",
        ))
    )
    return {
        "source": _COUNTER_OUTPUT_SOURCE,
        "requested": True,
        "diagnostic_observation_complete": observation_complete,
        "forecast_usable": False,
        "validation_status": "live_validation_pending",
        "pair_complete": pair_complete,
        "count": count,
        "sides": sides,
        "hook_diagnostic": (
            {key: output[key] for key in _COUNTER_OUTPUT_DIAGNOSTIC_KEYS}
            if _COUNTER_OUTPUT_DIAGNOSTIC_KEYS <= set(output) else None
        ),
    }


def normalize_experimental_counter_output_response_v1(
    frame: object, *, combat_id: int,
) -> dict[str, object] | None:
    """Consume one private finish response without entering the forecast path."""
    if not isinstance(frame, dict) or frame.get("type") != "command_result":
        raise ValueError("experimental counter response is malformed")
    if (not _bounded_int(frame.get("protocol_version"), 1, 1)
            or frame.get("ok") is not True):
        raise ValueError("experimental counter response protocol failed")
    result = frame.get("result")
    if (not isinstance(result, dict)
            or result.get("step") != _EXPERIMENTAL_TRACE_FINISH_STEP
            or result.get("accepted") is not True
            or result.get("private_build") is not True
            or result.get("production_trace_ready") is not False
            or result.get("combat_id") != combat_id
            or not _bounded_int(result.get("combat_id"), 1, 2**31 - 1)
            or not _bounded_int(result.get("managed_daily_sequence_token"), 1, 2**64 - 1)
            or type(result.get("status")) is not str
            or result["status"] not in {"bounded_trace_available", "trace_unavailable"}):
        raise ValueError("experimental counter response boundary differs")
    diagnostic = normalize_runtime_counter_output_diagnostic_v1(
        result.get("managed_trace"),
    )
    if diagnostic is None:
        return None
    if (diagnostic["diagnostic_observation_complete"]
            != (result["status"] == "bounded_trace_available")):
        raise ValueError("experimental counter response status disagrees with trace")
    return {
        "combat_id": combat_id,
        "managed_daily_sequence_token": result["managed_daily_sequence_token"],
        **diagnostic,
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
