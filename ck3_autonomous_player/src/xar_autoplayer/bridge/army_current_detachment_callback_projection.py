"""Pure current actual4 DATA cleanup under explicit normal resource return."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

_DLTD = 0x446C7464
_LIMITS = {"actual_callback_observed": False, "actual_resource_return_observed": False,
    "actual_after_state_observed": False, "full_detachment_transition_ready": False,
    "full_daily_ready": False, "full_monthly_ready": False,
    "actual_outer_wrapper_mode_observed": False, "outer_wrapper_complete": False,
    "outer_store_or_registry_invalidation_ready": False, "actual_next_occurrence_ready": False,
    "native_calls_executed": 0, "native_writes_executed": 0}


def _identity(value: object) -> bool:
    if type(value) is not str or not value.startswith("native:"):
        return False
    digits = value[7:]
    return digits.isascii() and digits.isdigit() and 0 <= int(digits) < 1 << 64


def _i32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _missing(result: dict, field: str) -> dict:
    result["missing_inputs"].append(field)
    return result


def _record_cleanup(incoming: Mapping, known: object) -> dict:
    count = incoming.get("data_count_2c_raw_i32")
    result = {"ready": False, "branch": None, "captured_count_i32": count,
        "completed_record_prefix_count": 0, "record_results": [],
        "conditional_count_after_i32": None, "missing_inputs": [],
        "record_call_mode_edx": 0, "native_calls_executed": 0,
        "native_writes_executed": 0}
    if not _i32(count):
        return _missing(result, "data_count_2c_raw_i32")
    if count <= 0:
        result.update(ready=True, branch="captured_nonpositive_count_skip_then_zero",
                      conditional_count_after_i32=0)
        return result
    result["branch"] = "captured_positive_count_ordered_mode0_records"
    records = incoming.get("records")
    records = records if isinstance(records, list) else []
    for index in range(count):
        record = records[index] if index < len(records) and isinstance(records[index], Mapping) else {}
        item = {"native_index": index, "record_identity": record.get("record_identity"),
            "observed_vtable_identity": record.get("vtable_identity"),
            "selected_slot0_target_identity": record.get("slot0_target_identity"),
            "call_mode_edx": 0, "ready": False, "normal_return_noop": False,
            "game_reads": None, "game_writes": None, "selected_resource_calls": None,
            "missing_inputs": []}
        result["record_results"].append(item)
        if not _identity(item["record_identity"]):
            item["missing_inputs"].append("record_identity")
        if not _identity(known):
            item["missing_inputs"].append("known_mode0_record_callback_identity")
        if not _identity(item["selected_slot0_target_identity"]):
            item["missing_inputs"].append("actual_record_slot0_target_identity")
        elif _identity(known) and item["selected_slot0_target_identity"] != known:
            item["missing_inputs"].append("selected_record_callback_effects_not_source_closed")
        if item["missing_inputs"]:
            result["missing_inputs"].extend(f"records[{index}].{field}" for field in item["missing_inputs"])
            return result
        item.update(ready=True, normal_return_noop=True, game_reads=0,
                    game_writes=0, selected_resource_calls=0)
        result["completed_record_prefix_count"] += 1
    result.update(ready=True, conditional_count_after_i32=0)
    return result


def _incoming(raw: Mapping, known: Mapping, index: int) -> dict:
    observed = {name: raw.get(name) for name in ("arrg_primary_vtable_identity",
        "arrg_primary_slot0_target_identity", "data_pointer_present", "data_buffer_identity",
        "data_count_2c_raw_i32", "data_capacity_28_raw_i32", "data_allocator_identity",
        "data_allocator_vtable_identity", "data_allocator_slot10_target_identity")}
    result = {"incoming_index": index,
        "seed_incoming_native_indices": deepcopy(raw.get("seed_incoming_native_indices", [])),
        "arrg_identity": raw.get("arrg_identity"), "arrg_full_id_u32": raw.get("arrg_full_id_u32"),
        "observed_current_header": observed, "observed_ordered_records": deepcopy(raw.get("records", [])),
        "independent_current_seed": True, "input_ready": False,
        "selected_callback_target_ready": False, "conditional_core_entry_ready": False,
        "record_cleanup_required": None, "record_cleanup_ready": False,
        "record_cleanup": None, "resource_call_required": None,
        "resource_call_descriptor_ready": False, "conditional_resource_call": None,
        "normal_resource_return_assumed": True,
        "source_parent_wrapper_mode_i32": known.get("source_parent_wrapper_mode_i32"),
        "conditional_selected_parent_mode0_wrapper_ready": False,
        "conditional_outer_sized_free_selected": (False
            if type(known.get("source_parent_wrapper_mode_i32")) is int
            and known["source_parent_wrapper_mode_i32"] == 0 else None),
        "conditional_direct_after_header_ready": False,
        "conditional_direct_after_header": None, "completed_source_prefix": [],
        "branch": None, "ready": False, "missing_inputs": [], **_LIMITS}
    target = raw.get("arrg_primary_slot0_target_identity")
    expected = known.get("known_primary_slot0_target_identity")
    for field, value in (("arrg_identity", raw.get("arrg_identity")),
            ("known_primary_slot0_target_identity", expected),
            ("known_core_identity", known.get("known_core_identity"))):
        if not _identity(value):
            _missing(result, field)
    if not _identity(target):
        _missing(result, "arrg_primary_slot0_target_identity")
    elif _identity(expected) and target != expected:
        _missing(result, "selected_primary_callback_core_not_source_closed")
    if result["missing_inputs"]:
        return result
    result.update(selected_callback_target_ready=True, conditional_core_entry_ready=True)
    result["completed_source_prefix"].append("known_selected_wrapper_enters_core")
    present = raw.get("data_pointer_present")
    if type(present) is not bool:
        return _missing(result, "data_pointer_present")
    result["input_ready"] = True
    count, capacity = raw.get("data_count_2c_raw_i32"), raw.get("data_capacity_28_raw_i32")
    after = {"primary_vtable_identity": known.get("known_primary_vtable_identity"),
        "secondary_vtable_identity": known.get("known_secondary_base_vtable_identity"),
        "tag_14_raw_u32": _DLTD, "data_pointer_present": present,
        "data_buffer_identity": raw.get("data_buffer_identity"),
        "data_count_2c_raw_i32": count if _i32(count) else None,
        "data_capacity_28_raw_i32": capacity if _i32(capacity) else None,
        "known_field_names": ["tag_14_raw_u32"], "preserved_context_missing": []}
    for field in ("primary_vtable_identity", "secondary_vtable_identity"):
        if _identity(after[field]):
            after["known_field_names"].append(field)
        else:
            _missing(result, "known_" + field)
    if present is False:
        result.update(branch="null_data_skips_cleanup_and_resource",
            record_cleanup_required=False, record_cleanup_ready=True, resource_call_required=False,
            resource_call_descriptor_ready=True)
        after.update(data_pointer_present=False, data_buffer_identity=None)
        after["known_field_names"].extend(("data_pointer_present", "data_buffer_identity"))
        for field in ("data_count_2c_raw_i32", "data_capacity_28_raw_i32"):
            if after[field] is not None:
                after["known_field_names"].append(field)
            else:
                after["preserved_context_missing"].append(field)
        result["completed_source_prefix"].append("null_DATA20_skips_EBA050_and_allocator")
    else:
        result.update(branch="nonnull_data_cleanup_then_conditional_resource_return",
            record_cleanup_required=True, resource_call_required=True)
        if not _identity(raw.get("data_buffer_identity")):
            return _missing(result, "data_buffer_identity")
        cleanup = _record_cleanup(raw, known.get("known_mode0_record_callback_identity"))
        result["record_cleanup"] = cleanup
        result["record_cleanup_ready"] = cleanup["ready"]
        result["completed_source_prefix"].extend(
            f"record[{position}]_mode0_noop" for position in range(cleanup["completed_record_prefix_count"]))
        if not cleanup["ready"]:
            result["missing_inputs"].extend(cleanup["missing_inputs"])
            return result
        result["completed_source_prefix"].append("EBA050_stores_count2C_zero")
        allocator_fields = ("data_allocator_identity", "data_allocator_vtable_identity",
                            "data_allocator_slot10_target_identity")
        descriptor = {"allocator_identity": raw.get(allocator_fields[0]),
            "allocator_vtable_identity": raw.get(allocator_fields[1]),
            "selected_slot10_target_identity": raw.get(allocator_fields[2]),
            "buffer_identity": raw.get("data_buffer_identity"), "r8d_size": 8,
            "normal_return_assumed": True, "executed": False,
            "internal_effects_modeled": False}
        result["conditional_resource_call"] = descriptor
        result["resource_call_descriptor_ready"] = all(_identity(raw.get(field)) for field in allocator_fields)
        if not result["resource_call_descriptor_ready"]:
            result["missing_inputs"].extend(field for field in allocator_fields if not _identity(raw.get(field)))
        after.update(data_pointer_present=False, data_buffer_identity=None,
                     data_count_2c_raw_i32=0, data_capacity_28_raw_i32=0)
        after["known_field_names"].extend(("data_pointer_present", "data_buffer_identity",
            "data_count_2c_raw_i32", "data_capacity_28_raw_i32"))
        result["completed_source_prefix"].append("assumed_normal_allocator_return_then_clear20_and28")
    result["completed_source_prefix"].append("write_Dltd_tag_and_secondary_base_vtable")
    result["conditional_direct_after_header"] = after
    result["conditional_direct_after_header_ready"] = all(_identity(after[field])
        for field in ("primary_vtable_identity", "secondary_vtable_identity"))
    # A missing resource descriptor leaves the complete record-cleanup result
    # available. The after-header is a conditional post-return value only.
    result["ready"] = result["conditional_direct_after_header_ready"] and (
        not present or result["resource_call_descriptor_ready"])
    result["conditional_selected_parent_mode0_wrapper_ready"] = result["ready"] and (
        type(known.get("source_parent_wrapper_mode_i32")) is int
        and known["source_parent_wrapper_mode_i32"] == 0)
    return result


def project_current_detachment_callback_inputs_v1(raw: Mapping | None) -> dict:
    """Project independent current cores and the source-selected mode0 wrapper.

    Every unique incoming pointer retains its original seed alias indices.
    No result is fed into another seed's captured current input. Allocator
    internals are not inspected; after-header values explicitly assume normal
    resource return and are never labeled observed after-state.
    """
    result = {"projection_kind": "conditional_current_detachment_callback_v1",
        "status": "unavailable", "ready": False, "seed_selection_ready": False,
        "seed_roster_ready": False, "current_date_storage_raw64": None,
        "source_parent_wrapper_mode_i32": None,
        "input_basis": "independent_observed_current_detachment_callback_seeds_12004",
        "source_core_rva": "0x2632DD0", "source_record_cleanup_rva": "0xEBA050",
        "normal_resource_return_assumed": True, "resource_internal_effects_modeled": False,
        "outer_wrapper_mode": None, "incoming": [], "independently_ready_incoming_indices": [],
        "conditional_mode0_wrapper_ready_incoming_indices": [],
        "record_cleanup_ready_incoming_indices": [], "missing_inputs": [],
        "unavailable_reason": "native_current_detachment_callback_family_absent", **_LIMITS}
    if not isinstance(raw, Mapping):
        return result
    result.update(seed_selection_ready=raw.get("seed_selection_ready") is True,
        seed_roster_ready=raw.get("seed_roster_ready") is True,
        current_date_storage_raw64=raw.get("current_date_storage_raw64"),
        source_parent_wrapper_mode_i32=raw.get("source_parent_wrapper_mode_i32"))
    rows = raw.get("incoming")
    rows = rows if isinstance(rows, list) else []
    for index, incoming in enumerate(rows):
        row = _incoming(incoming if isinstance(incoming, Mapping) else {}, raw, index)
        result["incoming"].append(row)
        if row["ready"]:
            result["independently_ready_incoming_indices"].append(index)
        if row["record_cleanup_ready"]:
            result["record_cleanup_ready_incoming_indices"].append(index)
        if row["conditional_selected_parent_mode0_wrapper_ready"]:
            result["conditional_mode0_wrapper_ready_incoming_indices"].append(index)
        result["missing_inputs"].extend(f"incoming[{index}].{field}" for field in row["missing_inputs"])
    for field in ("seed_selection_ready", "seed_roster_ready"):
        if result[field] is not True:
            result["missing_inputs"].append(field)
    ready = result["seed_selection_ready"] and result["seed_roster_ready"] and all(
        row["ready"] for row in result["incoming"])
    status = "available" if ready else (
        "unavailable" if raw.get("status") == "unavailable" and not rows else "partial")
    result.update(ready=ready, status=status,
        unavailable_reason=None if ready else "current_detachment_callback_inputs_partial")
    return result
