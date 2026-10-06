"""First hypothetical removal request using captured-current Army context."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_loss_allocation_projection import _signed_i32
from .army_manager_cleanup_projection import _OFFSETS, _ids, _project_bucket


def _select(occurrences: list | None, complete: bool, references: list, scope: str) -> dict:
    result = {"scope": scope, "input_prefix_ready": occurrences is not None,
        "sequence_complete": complete, "selection_ready": False,
        "known_invalid_prefix": [], "first_removal_call_request_ready": False,
        "first_removal_call_request": None, "selection_branch": None,
        "remaining_known_occurrences": [], "remaining_unknown_tail": not complete,
        "post_first_removal_state_required": False, "missing_inputs": []}
    if occurrences is None:
        return {**result, "missing_inputs": [scope + ".pending_occurrences"]}
    for ordinal, occurrence in enumerate(occurrences):
        raw = occurrence["raw_full_id_u32"]
        pending_index = occurrence.get("observed_stored_index")
        if pending_index is not None:
            candidates = [row for row in references if row["reference_scope"] == "current_pending"
                and row["pending_native_index"] == pending_index and row["raw_full_id_u32"] == raw]
        else:
            candidates = [row for row in references if row["reference_scope"] == "current_group_army"
                and row["group_native_index"] == occurrence.get("group_native_index")
                and row["group_army_native_index"] == occurrence.get("army_native_index")
                and row["raw_full_id_u32"] == raw]
        reference = candidates[0] if len(candidates) == 1 else None
        if reference is None or reference["native_army_identity_valid"] is None:
            return {**result, "remaining_known_occurrences": deepcopy(occurrences[ordinal:]),
                "missing_inputs": [{"sequence_index": ordinal, "raw_full_id_u32": raw,
                                    "operand": "captured_current_reference_identity_predicate"}]}
        if reference["native_army_identity_valid"] is False:
            result["known_invalid_prefix"].append({"sequence_index": ordinal,
                "occurrence": deepcopy(occurrence), "reference": deepcopy(reference)})
            continue
        resolution = reference["resolution"]
        full_id = resolution["selected_full_id_u32"]
        magic = reference["army_magic_14_raw_u32"]
        if (resolution["ready"] is not True or type(full_id) is not int or
                resolution["object_identity"] is None or magic != 0x41726D79 or full_id == 0xFFFFFFFF):
            return {**result, "remaining_known_occurrences": deepcopy(occurrences[ordinal:]),
                "missing_inputs": [{"sequence_index": ordinal,
                                    "operand": "actual_passed_Army_resolution_FullID_magic14"}]}
        request = {"sequence_index": ordinal, "reference_union_native_index": reference["native_index"],
            "raw_full_id_u32": raw, "stored_reference_i32": _signed_i32(raw),
            "passed_full_id_u32": full_id, "passed_army_id_i32": _signed_i32(full_id),
            "passed_object_identity": resolution["object_identity"],
            "passed_used_fallback": resolution["used_fallback"],
            "army_magic_14_raw_u32": magic, "native_army_identity_valid": True,
            "cleanup_target_index": reference["cleanup_target_index"],
            "reference_provenance": deepcopy(occurrence), "native_entry_rva": "0x2A978A0",
            "argument_basis": "captured_current_actual_selected_Army_pointer_and_FullID"}
        suffix = deepcopy(occurrences[ordinal + 1:])
        return {**result, "selection_ready": True, "selection_branch": "first_valid_current_receiver",
            "first_removal_call_request_ready": True, "first_removal_call_request": request,
            "remaining_known_occurrences": suffix,
            "post_first_removal_state_required": bool(suffix) or not complete}
    if complete:
        return {**result, "selection_ready": True, "selection_branch": "not_called"}
    return {**result, "missing_inputs": ["unknown_remaining_conditional_release_pending_tail"]}


def _cleanup(selection: Mapping, inputs: Mapping | None, *, transferred: bool) -> dict:
    basis = "conditional_standalone_transfer_then_first_top_helper" if transferred else "current_direct_top_helper"
    result = {"native_stage_rva": "0x2A98200", "stage_input_basis": basis,
        "status": "unavailable", "conditional_manager_cleanup_ready": False,
        "conditional_cleanup_branch": None, "passed_object_identity": None,
        "argument_full_id_u32": None, "argument_army_id_i32": None,
        "helper_resolution": None, "helper_object_identity": None,
        "helper_same_passed_pointer": None, "conditional_passed_army_identity_after_top_stage": None,
        "id_list_projections": [], "selected_bucket_cleanup_ready": False,
        "selected_bucket_index": None, "selected_bucket_rows_before": None,
        "conditional_selected_bucket_rows_after": None, "selected_bucket_removed_stored_indices": [],
        "records_b0_cleanup_ready": False, "records_b0_before": None,
        "conditional_records_b0_after": None, "records_b0_removed_count": None,
        "missing_inputs": [], "actual_cleanup": False, "actual_post_state": None}
    if selection["selection_ready"] is not True:
        return {**result, "missing_inputs": deepcopy(selection["missing_inputs"])}
    if selection["first_removal_call_request_ready"] is not True:
        return {**result, "status": "available", "conditional_manager_cleanup_ready": True,
                "conditional_cleanup_branch": "not_called"}
    request = selection["first_removal_call_request"]
    argument = request["passed_army_id_i32"]
    result.update(conditional_cleanup_branch="first_top_helper", passed_object_identity=request["passed_object_identity"],
        argument_full_id_u32=request["passed_full_id_u32"], argument_army_id_i32=argument,
        conditional_passed_army_identity_after_top_stage={
            "object_identity": request["passed_object_identity"], "full_id_u32": request["passed_full_id_u32"],
            "army_magic_14_raw_u32": request["army_magic_14_raw_u32"],
            "native_army_identity_valid": True, "basis": "source_top_stage_preserves_passed10_14_and_registry"})
    inputs = inputs if isinstance(inputs, Mapping) else {}
    lists = {row["manager_offset"]: row["ordered_army_ids"] for row in inputs.get("manager_id_lists", [])}
    for offset in _OFFSETS:
        observed = lists.get(offset)
        entry = [] if offset == "68" and transferred else observed
        ready = _ids(entry)
        projection = {"manager_offset": offset, "observed_ordered_army_ids": deepcopy(observed),
            "conditional_stage_entry_ordered_army_ids": deepcopy(entry) if ready else None,
            "stage_input_basis": "explicit_post_transfer_source_queue_empty" if offset == "68" and transferred else "captured_current_manager_list",
            "operation": "first_match_stable_remove" if offset == "50" else "first_match_swap_last_remove",
            "conditional_ready": ready, "conditional_ordered_army_ids_after": None, "removed_count": None}
        if ready:
            after = list(entry)
            removed = 0
            if argument in after:
                index = after.index(argument)
                if offset == "50":
                    after.pop(index)
                else:
                    after[index] = after[-1]
                    after.pop()
                removed = 1
            projection.update(conditional_ordered_army_ids_after=after, removed_count=removed)
        else:
            result["missing_inputs"].append(f"manager_id_lists[{offset}].ordered_army_ids")
        result["id_list_projections"].append(projection)

    index = request["cleanup_target_index"]
    targets = inputs.get("cleanup_targets", [])
    target = targets[index] if type(index) is int and 0 <= index < len(targets) else None
    if target is not None and target["argument_full_id_u32"] != request["passed_full_id_u32"]:
        target = None
    if target is None:
        result["missing_inputs"].append("actual_argument_specific_helper_resolution_and_bucket")
    else:
        resolution = target["helper_resolution"]
        result["helper_resolution"] = deepcopy(resolution)
        helper_id = resolution["selected_full_id_u32"]
        helper_identity = resolution["object_identity"]
        result["helper_object_identity"] = helper_identity
        if helper_identity is not None:
            result["helper_same_passed_pointer"] = helper_identity == request["passed_object_identity"]
        rows = target["bucket_rows"]
        count = target["bucket_count_raw_i32"]
        roster_ready = (type(count) is int and isinstance(rows, list) and
                        (count <= 0 and not rows or count > 0 and len(rows) == count and target["bucket_data_present"] is True))
        adapter_rows = [{"stored_index": row["native_index"], "observed_army_id": None,
                         "native_same_cleanup_army_pointer": row["native_same_helper_pointer"]}
                        for row in rows] if roster_ready else None
        # Reuse the qualified modulo30/pointer-match kernel with captured
        # source operands, without impersonating the old native candidate DTO.
        bucket_result = {"missing_inputs": []}
        _project_bucket(bucket_result, {
            "cleanup_resolved_army_id": _signed_i32(helper_id) if resolution["ready"] and type(helper_id) is int else None,
            "cleanup_used_fallback": resolution["used_fallback"] if resolution["ready"] else None,
            "selected_bucket_index": target["selected_bucket_index_u32"], "selected_bucket_rows": adapter_rows})
        ready = bucket_result.get("selected_bucket_cleanup_ready") is True
        result.update(selected_bucket_cleanup_ready=ready,
            selected_bucket_index=bucket_result.get("selected_bucket_index"),
            selected_bucket_rows_before=deepcopy(rows))
        if ready:
            removed = bucket_result["selected_bucket_removed_stored_indices"]
            result.update(selected_bucket_removed_stored_indices=removed,
                conditional_selected_bucket_rows_after=[deepcopy(row) for row in rows if row["native_index"] not in removed])
        else:
            result["missing_inputs"].extend(bucket_result["missing_inputs"])
    records = inputs.get("records_b0")
    if isinstance(records, list):
        after = deepcopy(records)
        index = 0
        while index < len(after):
            if after[index][0] == request["passed_full_id_u32"]:
                after[index] = after[-1]
                after.pop()
            else:
                index += 1
        result.update(records_b0_cleanup_ready=True, records_b0_before=deepcopy(records),
            conditional_records_b0_after=after, records_b0_removed_count=len(records) - len(after))
    else:
        result["missing_inputs"].append("records_b0")
    ready = (all(row["conditional_ready"] for row in result["id_list_projections"]) and
             result["selected_bucket_cleanup_ready"] and result["records_b0_cleanup_ready"])
    return {**result, "status": "available" if ready else "partial", "conditional_manager_cleanup_ready": ready}


def project_current_assault_first_removal_v1(army_strength: Mapping, release_projection: Mapping | None) -> dict:
    """Select current and derived-prefix requests under fixed current context.

    No future drain/tick or full2A978A0 lifecycle is replayed. For a selected
    first request, independent finite manager values describe either a direct
    current helper or an explicitly hypothetical transfer then first helper.
    """
    raw = army_strength.get("current_assault_removal_reference_inputs_v1")
    inputs = raw if isinstance(raw, Mapping) else None
    references = inputs["reference_occurrences"] if inputs else []
    pending = inputs["observed_pending_ids_i32"] if inputs else None
    if pending is None:
        old_queue = army_strength.get("monthly_daily_queue_inputs_v1")
        pending = old_queue.get("manager_army_id_list_2a5a8") if isinstance(old_queue, Mapping) else None
    current_occurrences = [{"stored_index": index, "stored_army_id_i32": value,
        "raw_full_id_u32": value & 0xFFFFFFFF, "observed_stored_index": index,
        "group_native_index": None, "army_native_index": None,
        "provenance": "observed_primary68_pending"} for index, value in enumerate(pending)] if isinstance(pending, list) else None
    derived_occurrences = None
    derived_complete = False
    if isinstance(release_projection, Mapping) and release_projection.get("conditional_post_release_pending_prefix_ready") is True:
        derived_occurrences = deepcopy(release_projection["conditional_post_release_pending_occurrences"])
        derived_complete = release_projection.get("conditional_post_release_pending_sequence_ready") is True
    current = _select(current_occurrences, current_occurrences is not None, references, "captured_current_pending")
    derived = _select(derived_occurrences, derived_complete, references,
                      "conditional_release_pending_prefix_using_captured_current_context")
    direct = _cleanup(current, inputs, transferred=False)
    transferred = _cleanup(derived, inputs, transferred=True)
    complete = direct["conditional_manager_cleanup_ready"] and transferred["conditional_manager_cleanup_ready"]
    any_ready = current["selection_ready"] or derived["selection_ready"]
    return {
        "projection_kind": "conditional_current_assault_first_removal_context",
        "source_contract_game_version": "1.20.0.3", "army_id": army_strength.get("army_id"),
        "status": "available" if complete else "partial" if any_ready else "unavailable",
        "input_basis": "captured_current_reference_identity_and_manager_context; explicitly_chosen_current_or_conditional_release_prefix",
        "current_pending_selection": current, "conditional_release_pending_selection": derived,
        "current_direct_top_helper": direct,
        "conditional_standalone_transfer_then_first_top_helper": transferred,
        "actual_removal": False, "actual_cleanup": False, "actual_effects": False,
        "actual_post_stage": None, "actual_post_registry": None,
        "future_drain_ready": False, "next_tick_ready": False,
        "full_ordered_removal_requests_ready": False, "full_army_lifecycle_ready": False,
        "full_daily_assault_ready": False, "full_regular_refill_ready": False,
        "full_monthly_ready": False, "full_calendar_ready": False, "live": False,
        "native_writes_executed": 0,
    }
