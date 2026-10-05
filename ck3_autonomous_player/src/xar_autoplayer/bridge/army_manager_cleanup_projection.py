"""First daily2A98200 manager cleanup, before later Army lifecycle effects."""
from __future__ import annotations

from typing import Mapping

from .army_daily_queue_transfer_projection import project_conditional_daily_id_transfer

_OFFSETS = ("50", "68", "80", "98", "c8", "158")


def _i32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _ids(value: object) -> bool:
    return isinstance(value, list) and all(_i32(item) for item in value)


def project_conditional_first_removal_manager_cleanup(
    army_strength: Mapping[str, object], transferprojection: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Use the first pre-mutation request to derive independent memberships.

    The actual FullID argument is re-resolved for the bucket. Native bucket
    removal compares pointers, while raw ID vectors use the original argument.
    No later cleanup, virtual destructor or subsequent queue stage is replayed.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_first_removal_manager_cleanup",
        "native_stage_rva": "0x2A98200",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "same_query_first_pre_mutation_occurrence",
        "status": "unavailable", "conditional_manager_cleanup_ready": False,
        "conditional_cleanup_branch": None, "candidate_selection_ready": False,
        "candidate_stored_index": None, "argument_army_id": None,
        "observed_queue_matches_transfer": None,
        "conditional_passed_army_identity_ready": False,
        "conditional_passed_army_identity_after_top_stage": None,
        "id_list_projections": [],
        "cleanup_resolved_army_id": None, "cleanup_used_fallback": None,
        "selected_bucket_index": None, "selected_bucket_cleanup_ready": False,
        "selected_bucket_rows_before": None, "conditional_selected_bucket_rows_after": None,
        "selected_bucket_removed_stored_indices": [],
        "records_b0_cleanup_ready": False, "records_b0_before": None,
        "conditional_records_b0_after": None, "records_b0_removed_count": None,
        "actual_cleanup": False, "actual_removal": False, "actual_post_state": None,
        "full_army_lifecycle_ready": False, "full_monthly_lifecycle_ready": False,
        "full_ordered_removal_requests_ready": False, "missing_inputs": [],
    }
    if army_strength.get("status") != "available":
        return {**result, "missing_inputs": ["available_same_query_army_strength"]}
    transfer = (transferprojection if isinstance(transferprojection, Mapping)
                else project_conditional_daily_id_transfer(army_strength))
    raw = army_strength.get("monthly_first_removal_cleanup_inputs_v1")
    inputs = raw if isinstance(raw, Mapping) else {}
    components = inputs.get("id_lists")
    lists = {item["manager_offset"]: item.get("ordered_army_ids") for item in (components if isinstance(components, list) else [])
             if isinstance(item, Mapping) and item.get("manager_offset") in _OFFSETS}
    if not isinstance(components, list):
        lists = {}
    observed_queue = lists.get("68")
    source_queue = transfer.get("source_manager_army_id_list_before")
    if _ids(observed_queue) and _ids(source_queue):
        matches = observed_queue == source_queue
        result["observed_queue_matches_transfer"] = matches
        if not matches:
            return {**result, "missing_inputs": ["manager_id_list_68_matches_transfer_source"]}

    if transfer.get("initial_removal_selection_ready") is not True:
        return {**result, "missing_inputs": ["first_initial_removal_selection"]}
    request = transfer.get("first_removal_call_request")
    found = inputs.get("candidate_found")
    if transfer.get("first_removal_call_request_ready") is not True:
        if found is not True:
            result.update(status="available", conditional_manager_cleanup_ready=True,
                          conditional_cleanup_branch="not_called", candidate_selection_ready=True)
        else:
            result["missing_inputs"] = ["native_candidate_disagrees_with_known_no_call"]
        return result

    if (not isinstance(request, Mapping) or found is not True
            or not _i32(inputs.get("candidate_stored_index"))
            or not _i32(inputs.get("argument_army_id"))
            or inputs["candidate_stored_index"] != request.get("stored_index")
            or inputs["argument_army_id"] != request.get("resolved_army_id")):
        return {**result, "missing_inputs": ["native_candidate_matches_first_removal_request"]}
    argument = inputs["argument_army_id"]
    result.update(candidate_selection_ready=True, conditional_cleanup_branch="cleanup",
                  candidate_stored_index=inputs["candidate_stored_index"], argument_army_id=argument,
                  conditional_passed_army_identity_ready=True,
                  conditional_passed_army_identity_after_top_stage={
                      "resolved_army_id": argument, "army_magic_14_raw": request.get("army_magic_14_raw"),
                      "native_army_identity_valid": request.get("native_army_identity_valid"),
                      "basis": "top_stage_preserves_passed_army_identity",
                  })
    missing: list[str] = result["missing_inputs"]
    for offset in _OFFSETS:
        observed = lists.get(offset)
        entry = transfer.get("conditional_source_manager_army_id_list_after_transfer") if offset == "68" else observed
        entry_ready = _ids(entry) and (offset != "68" or transfer.get("conditional_transfer_ready") is True)
        row: dict[str, object] = {
            "manager_offset": offset, "observed_ordered_army_ids": list(observed) if _ids(observed) else None,
            "conditional_stage_entry_ordered_army_ids": list(entry) if entry_ready else None,
            "stage_input_basis": "derived_post_transfer_source_queue" if offset == "68" else "same_query_manager_list",
            "operation": "first_match_stable_remove" if offset == "50" else "first_match_swap_last_remove",
            "conditional_ready": entry_ready, "conditional_ordered_army_ids_after": None,
            "removed_count": None,
        }
        if entry_ready:
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
            row.update(conditional_ordered_army_ids_after=after, removed_count=removed)
        else:
            missing.append(f"id_lists[{offset}].ordered_army_ids")
        result["id_list_projections"].append(row)

    _project_bucket(result, inputs)
    records = inputs.get("records_b0")
    record_ready = isinstance(records, list) and all(
        isinstance(words, list) and len(words) == 4
        and all(type(word) is int and 0 <= word < 1 << 32 for word in words) for words in records)
    if record_ready:
        before = [list(words) for words in records]
        after = [list(words) for words in records]
        index = 0
        while index < len(after):
            if after[index][0] == (argument & 0xFFFFFFFF):
                after[index] = after[-1]
                after.pop()
            else:
                index += 1
        result.update(records_b0_cleanup_ready=True, records_b0_before=before,
                      conditional_records_b0_after=after, records_b0_removed_count=len(before) - len(after))
    else:
        missing.append("records_b0")

    ready = (all(row["conditional_ready"] for row in result["id_list_projections"])
             and result["selected_bucket_cleanup_ready"] and result["records_b0_cleanup_ready"])
    result.update(conditional_manager_cleanup_ready=ready, status="available" if ready else "partial")
    return result


def _project_bucket(result: dict[str, object], inputs: Mapping[str, object]) -> None:
    resolved, fallback, phase = (inputs.get("cleanup_resolved_army_id"),
                                inputs.get("cleanup_used_fallback"), inputs.get("selected_bucket_index"))
    rows = inputs.get("selected_bucket_rows")
    operands_ready = (_i32(resolved) and type(fallback) is bool and type(phase) is int
                      and phase == (resolved & 0xFFFFFFFF) % 30)
    if operands_ready:
        result.update(cleanup_resolved_army_id=resolved, cleanup_used_fallback=fallback,
                      selected_bucket_index=phase)
    if (not operands_ready or not isinstance(rows, list) or not all(
            isinstance(row, Mapping) and type(row.get("stored_index")) is int
            and row["stored_index"] == index
            and (row.get("observed_army_id") is None or _i32(row["observed_army_id"]))
            and type(row.get("native_same_cleanup_army_pointer")) is bool
            for index, row in enumerate(rows))):
        result["missing_inputs"].append("second_resolution_and_selected_bucket_pointer_occurrences")
        return
    before = [dict(row) for row in rows]
    after = [dict(row) for row in rows if not row["native_same_cleanup_army_pointer"]]
    result.update(selected_bucket_cleanup_ready=True, selected_bucket_rows_before=before,
                  conditional_selected_bucket_rows_after=after,
                  selected_bucket_removed_stored_indices=[row["stored_index"] for row in rows
                                                         if row["native_same_cleanup_army_pointer"]])
