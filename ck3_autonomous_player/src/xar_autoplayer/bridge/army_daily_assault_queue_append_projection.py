"""Bounded pre-release pending DWORD sequence after current assault requests."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_loss_allocation_projection import _signed_i32


def project_current_daily_assault_queue_append_v1(
    army_strength: Mapping, loss_projection: Mapping | None,
) -> dict:
    """Copy current pending occurrences and append only a qualified prefix.

    The standalone current-table invocation is explicit. Its earlier daily
    drain is not replayed, and9D11F0 record release has not run at this seam.
    Raw IDs retain their DWORD bits, native occurrence order and repetitions.
    """
    result = {
        "projection_kind": "conditional_current_daily_assault_queue_append",
        "source_contract_game_version": "1.20.0.3",
        "army_id": army_strength.get("army_id"),
        "stage": "conditional_pre_release_pending_queue",
        "input_basis": "same_query_primary68_pending_DWORD_occurrences_plus_"
                       "conditional_current_daily_assault_append_prefix",
        "status": "unavailable", "observed_pending_ready": False,
        "observed_pending_army_ids_i32": None, "observed_pending_occurrences": [],
        "known_append_prefix_ready": False, "append_requests_complete": False,
        "known_append_army_ids_i32": [], "known_append_occurrences": [],
        "conditional_pre_release_pending_prefix_ready": False,
        "conditional_pre_release_pending_prefix": None,
        "conditional_pre_release_pending_sequence_ready": False,
        "conditional_pre_release_pending_sequence": None,
        "conditional_pre_release_occurrences": None,
        "completed_loss_group_count": None, "observed_loss_group_count": None,
        "next_missing_group": None, "loss_missing_inputs": [], "missing_inputs": [],
        "stored_integer_bits": 32, "stored_integer_signed": True,
        "actual_append": False, "actual_effects": False,
        "actual_pre_release_pending_sequence": None, "actual_post_release_pending_sequence": None,
        "queue_execution_ready": False, "queue_drain_replayed": False,
        "record_release_effects_ready": False, "post_release_pending_ready": False,
        "next_day_pending_ready": False, "full_daily_assault_ready": False,
        "full_regular_refill_ready": False, "full_monthly_ready": False,
        "full_calendar_ready": False, "native_writes_executed": 0,
    }
    queue = army_strength.get("monthly_daily_queue_inputs_v1")
    pending = queue.get("manager_army_id_list_2a5a8") if isinstance(queue, Mapping) else None
    observed_ready = (isinstance(pending, list) and
                      all(type(value) is int and -(1 << 31) <= value < 1 << 31 for value in pending))
    observed_occurrences = []
    if observed_ready:
        observed_occurrences = [{"stored_index": index, "stored_army_id_i32": value,
            "raw_full_id_u32": value & 0xFFFFFFFF, "provenance": "observed_primary68_pending",
            "observed_stored_index": index, "append_request_index": None,
            "group_native_index": None, "army_native_index": None}
            for index, value in enumerate(pending)]
        result.update(observed_pending_ready=True, observed_pending_army_ids_i32=list(pending),
                      observed_pending_occurrences=observed_occurrences)
    else:
        result["missing_inputs"].append("monthly_daily_queue_inputs_v1.manager_army_id_list_2a5a8")

    if not isinstance(loss_projection, Mapping):
        result["missing_inputs"].append("current_daily_assault_loss_projection")
        result["status"] = "partial" if observed_ready else "unavailable"
        return result
    requests = loss_projection.get("ordered_queue_append_requests")
    groups = loss_projection.get("groups", [])
    completed = loss_projection.get("completed_group_count")
    complete = (loss_projection.get("queue_requests_ready") is True and
                loss_projection.get("sequential_numeric_ready") is True)
    prefix_evidence = (complete or (type(completed) is int and completed > 0) or
                       (isinstance(requests, list) and bool(requests)))
    prefix_ready = (loss_projection.get("physical_group_order_ready") is True and
                    isinstance(requests, list) and prefix_evidence)
    appended = []
    if prefix_ready:
        for index, request in enumerate(requests):
            raw = request.get("raw_full_id_u32") if isinstance(request, Mapping) else None
            if type(raw) is not int or not 0 <= raw < 1 << 32:
                prefix_ready = False
                appended = []
                break
            appended.append({
                "stored_index": len(pending) + index if observed_ready else None,
                "stored_army_id_i32": _signed_i32(raw), "raw_full_id_u32": raw,
                "provenance": "conditional_daily_assault_original_raw_ArmyID_append",
                "observed_stored_index": None, "append_request_index": index,
                "group_native_index": request["group_native_index"],
                "army_native_index": request["army_native_index"],
            })
    complete = complete and prefix_ready
    loss_missing = deepcopy(loss_projection.get("missing_inputs", []))
    next_group = None
    if not complete and isinstance(groups, list):
        for group in groups:
            if group.get("numeric_ready") is not True or group.get("queue_requests_ready") is not True:
                next_group = {"native_index": group.get("native_index"),
                    "physical_slot_i64": group.get("physical_slot_i64"),
                    "sequential_entry_reached": group.get("sequential_entry_reached") is True,
                    "missing_inputs": deepcopy(group.get("missing_inputs", []))}
                break
    if not prefix_ready:
        result["missing_inputs"].append("qualified_current_daily_assault_append_prefix")
    if not complete:
        result["missing_inputs"].append({"stage": "remaining_daily_assault_groups",
            "next_missing_group": next_group, "inputs": loss_missing})
    composite_prefix_ready = observed_ready and prefix_ready
    composite_ready = observed_ready and complete
    appended_ids = [row["stored_army_id_i32"] for row in appended]
    prefix = list(pending) + appended_ids if composite_prefix_ready else None
    occurrences = observed_occurrences + appended if composite_prefix_ready else None
    return {**result,
        "status": "available" if composite_ready else "partial" if observed_ready or prefix_ready else "unavailable",
        "known_append_prefix_ready": prefix_ready, "append_requests_complete": complete,
        "known_append_army_ids_i32": appended_ids, "known_append_occurrences": appended,
        "conditional_pre_release_pending_prefix_ready": composite_prefix_ready,
        "conditional_pre_release_pending_prefix": prefix,
        "conditional_pre_release_pending_sequence_ready": composite_ready,
        "conditional_pre_release_pending_sequence": list(prefix) if composite_ready else None,
        "conditional_pre_release_occurrences": occurrences,
        "completed_loss_group_count": completed,
        "observed_loss_group_count": loss_projection.get("observed_group_count"),
        "next_missing_group": next_group, "loss_missing_inputs": loss_missing,
    }
