"""Pure current actual4 store admission and independent pre-callback writes."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

_U32 = (1 << 32) - 1
_LIMITS = {"actual_callback_observed": False, "actual_resource_return_observed": False,
    "actual_after_state_observed": False, "full_detachment_transition_ready": False,
    "full_daily_ready": False, "full_monthly_ready": False,
    "actual_store_method_return_observed": False, "actual_registry_after_state_observed": False,
    "callback_effects_replayed": False, "zeroing_effects_replayed": False,
    "registry_invalidation_ready": False, "actual_next_occurrence_ready": False,
    "native_calls_executed": 0, "native_writes_executed": 0}


def _unsigned(value: object, bits: int = 32) -> bool:
    return type(value) is int and 0 <= value < 1 << bits


def _identity(value: object) -> bool:
    if type(value) is not str or not value.startswith("native:"):
        return False
    digits = value[7:]
    return digits.isascii() and digits.isdigit() and 0 <= int(digits) < 1 << 64


def _skip(result: dict, branch: str) -> dict:
    result.update(admission_ready=True, admitted=False, branch=branch,
        conditional_skip_return=False, pre_callback_updates_required=False,
        pre_callback_updates_ready=True, pre_callback_updates=[], callback_selected=False)
    return result


def _request(raw: Mapping, store: Mapping, index: int) -> dict:
    requested = raw.get("requested_full_id_u32")
    result = {"request_index": index,
        "seed_incoming_native_indices": deepcopy(raw.get("seed_incoming_native_indices", [])),
        "incoming_arrg_identity": raw.get("incoming_arrg_identity"),
        "requested_full_id_u32": requested, "observed_index_low24_u32": raw.get("index_low24_u32"),
        "source_index_low24_u32": None, "independent_current_request": True,
        "observed_slot_identity": raw.get("slot_identity"),
        "observed_selected_pointer_present": raw.get("selected_pointer_present"),
        "observed_selected_object_identity": raw.get("selected_object_identity"),
        "observed_selected_full_id_10_raw_u32": raw.get("selected_full_id_10_raw_u32"),
        "observed_trailing_slot_scan": deepcopy(raw.get("trailing_slot_scan", [])),
        "admission_ready": False, "admitted": None, "branch": None,
        "conditional_skip_return": None, "pre_callback_updates_required": None,
        "pre_callback_updates_ready": False, "pre_callback_updates": [],
        "callback_selected": None, "selected_callback_descriptor_ready": False,
        "selected_callback_descriptor": None, "source_completed_prefix": [],
        "missing_admission_inputs": [], "missing_pre_callback_inputs": [],
        "missing_callback_descriptor_inputs": [], **_LIMITS}
    flag = store.get("store_48_raw_u8")
    if not _unsigned(flag, 8):
        result["missing_admission_inputs"].append("store_48_raw_u8")
        return result
    result["source_completed_prefix"].append("read_store48")
    if flag != 0:
        return _skip(result, "nonzero_store48_false_return")
    if not _unsigned(requested):
        result["missing_admission_inputs"].append("requested_full_id_u32")
        return result
    slot_index = requested & 0xFFFFFF
    result["source_index_low24_u32"] = slot_index
    count = store.get("slot_count_2c_raw_u32")
    if not _unsigned(count):
        result["missing_admission_inputs"].append("slot_count_2c_raw_u32")
        return result
    result["source_completed_prefix"].append("unsigned_low24_below_slot_count_comparison")
    if slot_index >= count:
        return _skip(result, "unsigned_index_out_of_range_false_return")
    present = raw.get("selected_pointer_present")
    if type(present) is not bool:
        result["missing_admission_inputs"].append("selected_slot_object_pointer_present")
        return result
    result["source_completed_prefix"].append("read_actual_selected_slot_pointer")
    if present is False:
        return _skip(result, "null_selected_slot_pointer_false_return")
    selected = raw.get("selected_full_id_10_raw_u32")
    if not _unsigned(selected):
        result["missing_admission_inputs"].append("selected_full_id_10_raw_u32")
        return result
    result["source_completed_prefix"].append("compare_selected_object10_with_complete_requested_id")
    if selected != requested:
        return _skip(result, "selected_full_id_mismatch_false_return")
    result.update(admission_ready=True, admitted=True, branch="matching_selected_full_id_admitted",
                  pre_callback_updates_required=True, callback_selected=True)
    active = store.get("active_count_3c_raw_u32")
    # The mark's source store is independent of its old captured value.
    result["pre_callback_updates"].append({"field": "registry_mark_4a_raw_u8",
        "before": store.get("registry_mark_4a_raw_u8"), "after": 1,
        "source_defined_write_ready": True, "executed": False})
    if _unsigned(active):
        result["pre_callback_updates"].insert(0, {"field": "active_count_3c_raw_u32",
            "before": active, "after": (active - 1) & _U32,
            "source_defined_write_ready": True, "executed": False})
        result["pre_callback_updates_ready"] = True
    else:
        result["missing_pre_callback_inputs"].append("active_count_3c_raw_u32")
    mode = store.get("source_parent_wrapper_mode_i32")
    descriptor = {"selected_object_identity": raw.get("selected_object_identity"),
        "selected_primary_vtable_identity": raw.get("selected_primary_vtable_identity"),
        "selected_slot0_target_identity": raw.get("selected_slot0_target_identity"),
        "source_parent_wrapper_mode_i32": mode, "mode_is_source_constant": True,
        "execution_observed": False, "effects_replayed": False}
    result["selected_callback_descriptor"] = descriptor
    for field in ("selected_object_identity", "selected_primary_vtable_identity", "selected_slot0_target_identity"):
        if not _identity(descriptor[field]):
            result["missing_callback_descriptor_inputs"].append(field)
    if type(mode) is not int or mode != 0:
        result["missing_callback_descriptor_inputs"].append("source_parent_wrapper_mode_i32")
    result["selected_callback_descriptor_ready"] = not result["missing_callback_descriptor_inputs"]
    return result


def project_current_detachment_store_inputs_v1(raw: Mapping | None) -> dict:
    """Answer admission from current store operands without evolving the store.

    Later callback, reached4226F10, table reload, high-water scan and free-list
    writes require their actual post-call inputs. Captured trailing slots are
    retained as current observations only. Each request uses the same captured
    store; no prior projected request invalidates another's current seed.
    """
    result = {"projection_kind": "current_detachment_store_admission_v1",
        "source_parent_rva": "0x2A9E620", "source_parent_identity": None,
        "source_parent_wrapper_mode_i32": None, "current_date_storage_raw64": None,
        "input_basis": "independent_same_query_current_arrg_registry_requests",
        "seed_selection_ready": False, "seed_roster_ready": False,
        "status": "unavailable", "ready": False, "admission_ready": False,
        "observed_current_registry": None, "requests": [],
        "completed_admission_prefix_count": 0, "independently_ready_request_indices": [],
        "admitted_request_indices": [], "skipped_request_indices": [],
        "pre_callback_updates_ready_request_indices": [],
        "missing_admission_inputs": [], "post_callback_full_id_u32": None,
        "actual_store_method_return": None,
        "remaining_stage_inputs": [],
        "unavailable_reason": "native_current_detachment_store_family_absent", **_LIMITS}
    if not isinstance(raw, Mapping):
        return result
    result.update(source_parent_identity=raw.get("source_parent_identity"),
        source_parent_wrapper_mode_i32=raw.get("source_parent_wrapper_mode_i32"),
        current_date_storage_raw64=raw.get("current_date_storage_raw64"),
        seed_selection_ready=raw.get("seed_selection_ready") is True,
        seed_roster_ready=raw.get("seed_roster_ready") is True)
    result["observed_current_registry"] = {field: raw.get(field) for field in (
        "registry_identity", "store_48_raw_u8", "slot_count_2c_raw_u32", "slot_table_identity",
        "active_count_3c_raw_u32", "registry_mark_4a_raw_u8", "high_water_38_raw_u32", "free_head_40_raw_u32")}
    rows = raw.get("requests")
    rows = rows if isinstance(rows, list) else []
    prefix_open = True
    for index, request in enumerate(rows):
        row = _request(request if isinstance(request, Mapping) else {}, raw, index)
        result["requests"].append(row)
        if row["admission_ready"]:
            result["independently_ready_request_indices"].append(index)
            if prefix_open:
                result["completed_admission_prefix_count"] += 1
            result["admitted_request_indices" if row["admitted"] else "skipped_request_indices"].append(index)
        else:
            prefix_open = False
        if row["admitted"] is True and row["pre_callback_updates_ready"]:
            result["pre_callback_updates_ready_request_indices"].append(index)
        result["missing_admission_inputs"].extend(
            f"requests[{index}].{field}" for field in row["missing_admission_inputs"])
    for field in ("seed_selection_ready", "seed_roster_ready"):
        if result[field] is not True:
            result["missing_admission_inputs"].append(field)
    request_capture_unavailable = not rows and raw.get("status") == "unavailable"
    if request_capture_unavailable:
        result["missing_admission_inputs"].append("current_request_capture_unavailable")
    ready = result["seed_selection_ready"] and result["seed_roster_ready"] and all(
        row["admission_ready"] for row in result["requests"]) and not request_capture_unavailable
    status = "available" if ready else (
        "unavailable" if raw.get("status") == "unavailable" and not rows else "partial")
    if result["admitted_request_indices"]:
        result["remaining_stage_inputs"] = ["actual_selected_callback_effects_and_postcallback_object10",
            "reached4226F10_effects", "actual_postcall_table20_and_registry_fields"]
    result.update(ready=ready, admission_ready=ready, status=status,
        unavailable_reason=None if ready else "current_detachment_store_admission_inputs_partial")
    return result
