"""Expose copied actual consumer return facts independently of loss inputs."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_observed_phase_contract_12004 import _ordered, _token_key


def _census(table):
    if not isinstance(table, Mapping):
        return False
    end = table.get("end_slot_raw_i32")
    controls = table.get("physical_controls")
    mask, tail = table.get("mask_raw_i32"), table.get("tail_distance_raw_u8")
    computed = ((mask + tail + 1) & 0xFFFFFFFF) if type(mask) is int and type(tail) is int else None
    if computed is not None and computed >= 1 << 31:
        computed -= 1 << 32
    return (table.get("controls_complete") is True and
            type(table.get("entries_identity")) is int and table["entries_identity"] > 0 and
            type(end) is int and 0 <= end <= 512 and computed == end and
            isinstance(controls, list) and len(controls) == end and
            all(type(value) is int and 0 <= value <= 255 for value in controls) and
            type(table.get("end_marker_control_raw_u8")) is int and
            0 < table["end_marker_control_raw_u8"] <= 255)


def _complete_vector(vector):
    if not isinstance(vector, Mapping):
        return False
    count, capacity = vector.get("count_raw_i32"), vector.get("capacity_raw_i32")
    ids = vector.get("ordered_full_ids_u32")
    return (vector.get("references_complete") is True and type(count) is int and
            type(capacity) is int and 0 <= count <= capacity and
            isinstance(ids, list) and len(ids) == count <= 128 and
            all(type(value) is int and 0 <= value < 1 << 32 for value in ids) and
            (count == 0 or vector.get("data_identity") not in (None, 0)))


def _binding(event, phase, exact_source, family_guard):
    missing = []
    if exact_source is not True:
        missing.append("exact_actual4_query_source")
    if family_guard is not True:
        missing.append("installed_current_consumer_family_guard")
    parent = event.get("parent")
    if not isinstance(parent, Mapping):
        return False, missing + ["owned_consumer_parent"]
    admitted = (event.get("capture_stage") == "natural_2A97EB0_entry_and_return" and
                parent.get("actual_entry_rva") == 0x2A97EB0 and
                parent.get("caller_return_rva") == 0x2A9A8EA and
                parent.get("exact_post_date_parent") is True and
                parent.get("active") is False and
                event.get("current_session_guard") is True and event.get("actual") is True and
                event.get("original_called") is True and event.get("original_returned") is True and
                type(parent.get("manager_identity")) is int and parent["manager_identity"] > 0 and
                _ordered(parent["phase_entry_event"], parent["entry_event"]) and
                _ordered(parent["entry_event"], event["returned_event"]))
    if not admitted:
        missing.append("exact_natural_consumer_entry_return_clock_thread_parent_binding")
    if not isinstance(phase, Mapping):
        return False, missing + ["exact_post_date_phase_record"]
    scope = phase["scope"]
    joined = (scope["observed"] is True and scope["phase"] == "post_date" and
              scope["actual_entry_rva"] == 0x2A9A570 and
              scope["primary_manager_identity"] == parent.get("manager_identity") and
              _token_key(scope["entry_event"]) == _token_key(parent["phase_entry_event"]) and
              scope["date_raw"] == parent["date_raw"] and
              scope["absolute_day_raw"] == parent["absolute_day_raw"] and
              phase["original_called"] is True and phase["original_returned"] is True and
              _ordered(event["returned_event"], phase["returned_event"]))
    if not joined:
        missing.append("exact_post_date_phase_token_manager_date_join")
    return not missing, missing


def project_observed_assault_consumer_outcome_12004(
    event, phase_record, *, exact_source, family_current_session_guard,
) -> dict:
    """Consume strict owned 37b/33 copies, without executing a loss projection.

    Readiness describes this captured callback. A later query does not make
    its returned queue/table the current frame or prove a future daily stage.
    End-marker controls are excluded, and pending occurrences keep full IDs
    and repeats. Queue growth may change backing while preserving its prefix.
    """
    result = {
        "projection_kind": "observed_actual_daily_assault_consumer_return_outcome",
        "source_contract_game_version": "1.20.0.4",
        "input_basis": "owned_natural_2A97EB0_entry_and_return; exact_post_date_phase_token_join",
        "scope": "captured_consumer_callback_only", "status": "unavailable",
        "actual_stage_return_observed": False, "outcome_ready": False,
        "lineage": None, "raw_return_bits": None, "raw_return_is_semantic_success": False,
        "capture_failure_flags": None,
        "entry_occupied_count_raw_i32": None, "returned_occupied_count_raw_i32": None,
        "returned_table_census_ready": False, "returned_table_empty": None,
        "returned_nonzero_physical_slots": None,
        "same_physical_table_observed": None, "control_transition_census_ready": False,
        "observed_cleared_physical_slots": None,
        "pending_comparison_ready": False, "pending_prefix_preserved": None,
        "entry_pending_count_raw_i32": None, "returned_pending_count_raw_i32": None,
        "observed_new_pending_full_id_occurrences": None,
        "intermediate_append_calls_observed": False,
        "missing_inputs": [], "table_missing_inputs": [], "pending_missing_inputs": [],
        "later_current_query_used": False, "returned_frame_used_to_fill_entry": False,
        "current_load_or_future_stage_inferred": False,
        "complete_numerical_loss_observed": False, "full_daily_assault_ready": False,
        "full_monthly_ready": False, "full_calendar_ready": False,
    }
    if not isinstance(event, Mapping):
        return {**result, "missing_inputs": ["owned_actual_assault_consumer_event"]}
    bound, binding_missing = _binding(event, phase_record, exact_source, family_current_session_guard)
    parent = event.get("parent") or {}
    result.update(raw_return_bits=event.get("raw_return_bits"),
                  capture_failure_flags=event.get("capture_failure_flags"),
                  actual_stage_return_observed=bound,
                  lineage={key: deepcopy(parent.get(key)) for key in
                           ("manager_identity", "entry_event", "phase_entry_event", "date_raw", "absolute_day_raw")})
    result["lineage"].update(journal_sequence=event.get("journal_sequence"),
                              returned_event=deepcopy(event.get("returned_event")))
    scope = phase_record.get("scope", {}) if isinstance(phase_record, Mapping) else {}
    result["lineage"].update(phase_session_identity=scope.get("session_identity"),
                              phase_game_state_identity=scope.get("game_state_identity"))
    before, after = event.get("entry_table"), event.get("returned_table")
    queue_before, queue_after = event.get("entry_pending_queue"), event.get("returned_pending_queue")
    for table, key in ((before, "entry_occupied_count_raw_i32"), (after, "returned_occupied_count_raw_i32")):
        if isinstance(table, Mapping):
            result[key] = table.get("occupied_count_raw_i32")
    for queue, key in ((queue_before, "entry_pending_count_raw_i32"), (queue_after, "returned_pending_count_raw_i32")):
        if isinstance(queue, Mapping):
            result[key] = queue.get("count_raw_i32")
    if not bound:
        return {**result, "status": "partial" if exact_source is True else "unavailable", "missing_inputs": binding_missing}

    table_missing = result["table_missing_inputs"]
    after_ready = _census(after) and type(after.get("occupied_count_raw_i32")) is int
    result["returned_table_census_ready"] = after_ready
    if after_ready:
        occupied_slots = [slot for slot, control in enumerate(after["physical_controls"]) if control != 0]
        result.update(returned_nonzero_physical_slots=occupied_slots,
                      returned_table_empty=after["occupied_count_raw_i32"] == 0 and not occupied_slots)
    else:
        table_missing.append("complete_copied_returned_control_and_count_census")
    if _census(before) and _census(after):
        same = all(before[key] == after[key] for key in
                   ("entries_identity", "mask_raw_i32", "tail_distance_raw_u8", "end_slot_raw_i32"))
        result["same_physical_table_observed"] = same
        if same:
            result.update(control_transition_census_ready=True,
                          observed_cleared_physical_slots=[slot for slot, (a, z) in
                              enumerate(zip(before["physical_controls"], after["physical_controls"]))
                              if a != 0 and z == 0])
        else:
            table_missing.append("same_entry_return_physical_storage_and_extent")
    else:
        table_missing.append("complete_entry_return_control_censuses_for_slot_comparison")

    pending_missing = result["pending_missing_inputs"]
    if _complete_vector(queue_before) and _complete_vector(queue_after):
        a, z = queue_before["ordered_full_ids_u32"], queue_after["ordered_full_ids_u32"]
        prefix = len(z) >= len(a) and z[:len(a)] == a
        result.update(pending_comparison_ready=True, pending_prefix_preserved=prefix,
                      observed_new_pending_full_id_occurrences=deepcopy(z[len(a):]) if prefix else None)
    else:
        pending_missing.append("complete_copied_entry_return_pending_occurrences")
    ready = (after_ready and result["control_transition_census_ready"] and result["pending_comparison_ready"])
    result.update(outcome_ready=ready, status="available" if ready else "partial",
                  missing_inputs=list(dict.fromkeys(table_missing + pending_missing)))
    return result
