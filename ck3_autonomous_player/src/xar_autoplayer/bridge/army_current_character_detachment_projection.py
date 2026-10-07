"""Pure current Character operands and source-defined conditional reset values."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

_INVALID_ID = (1 << 32) - 1
_RESET_RAW_U64 = 0xFFFFFFFF029C77F8
_RESET_RAW_I64 = _RESET_RAW_U64 - (1 << 64)
_LIMITS = {"actual_callback_observed": False, "actual_resource_return_observed": False,
    "actual_after_state_observed": False, "full_detachment_transition_ready": False,
    "full_daily_ready": False, "full_monthly_ready": False,
    "full_character_detachment_suffix_ready": False, "future_date_ready": False,
    "actual_reset_observed": False, "source_reset_reached": False,
    "post_reset_origin_ready": False, "post_mutator_date_inputs_ready": False,
    "actual_next_occurrence_ready": False,
    "native_calls_executed": 0, "native_writes_executed": 0}


def _identity(value: object) -> bool:
    if type(value) is not str or not value.startswith("native:"):
        return False
    digits = value[7:]
    return digits.isascii() and digits.isdigit() and 0 <= int(digits) < 1 << 64


def _resolution(value: object) -> dict:
    return deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def _no_suffix(result: dict, branch: str) -> dict:
    result.update(current_extension_branch_ready=True, branch=branch,
        no_suffix=True, reset_inputs_required=False, reset_inputs_ready=True,
        source_defined_reset_descriptors_ready=True)
    return result


def _request(raw: Mapping, index: int) -> dict:
    character = _resolution(raw.get("character_resolution"))
    chain = {"arrg_resolution": _resolution(raw.get("arrg_resolution")),
        "army_full_id_140_u32": raw.get("army_full_id_140_u32"),
        "army_resolution": _resolution(raw.get("army_resolution")),
        "unit_full_id_124_u32": raw.get("unit_full_id_124_u32"),
        "unit_resolution": _resolution(raw.get("unit_resolution"))}
    result = {"request_index": index,
        "seed_incoming_native_index": raw.get("seed_incoming_native_index"),
        "arrg_identity": raw.get("arrg_identity"),
        "character_full_id_148_u32": raw.get("character_full_id_148_u32"),
        "observed_character_resolution": character,
        "observed_current_character_identity": character.get("object_identity"),
        "passed_province_identity": raw.get("passed_province_identity"),
        "independent_same_query_current_seed": True,
        "observed_current_extension": {
            "present": raw.get("current_extension_1b8_present"),
            "identity": raw.get("current_extension_1b8_identity"),
            "f8_raw_u32": raw.get("extension_f8_raw_u32"),
            "storage_100_raw64": raw.get("extension_100_raw64")},
        "observed_extension_reset_inputs_ready": raw.get("extension_reset_inputs_ready") is True,
        "observed_current_source_chain": chain,
        "current_source_chain_ready": raw.get("source_chain_ready") is True,
        "observed_current_saved_unit_identity": chain["unit_resolution"].get("object_identity"),
        "current_extension_branch_ready": False, "branch": None, "no_suffix": None,
        "reset_inputs_required": None, "reset_inputs_ready": False,
        "source_defined_reset_descriptors_ready": False,
        "source_defined_reset_descriptors": [], "missing_current_extension_inputs": [],
        "missing_optional_before_context": [], "remaining_stage_inputs": [], **_LIMITS}
    if type(raw.get("character_full_id_148_u32")) is int and raw["character_full_id_148_u32"] == _INVALID_ID:
        return _no_suffix(result, "invalid_character_full_id_no_suffix")
    present = raw.get("current_extension_1b8_present")
    if present is False:
        return _no_suffix(result, "null_current_character1b8_no_suffix")
    if present is not True:
        result["missing_current_extension_inputs"].append("current_extension_1b8_present")
        return result
    result.update(branch="nonnull_current_character1b8_conditional_reset_descriptors",
                  no_suffix=False, reset_inputs_required=True)
    extension = raw.get("current_extension_1b8_identity")
    if not _identity(extension):
        result["missing_current_extension_inputs"].append("current_extension_1b8_identity")
        return result
    for field in ("extension_f8_raw_u32", "extension_100_raw64"):
        if raw.get(field) is None:
            result["missing_optional_before_context"].append(field)
    result["source_defined_reset_descriptors"] = [
        {"target_role": "captured_initial_extension", "target_identity": extension,
         "field_offset": "0xF8", "before_current_raw_u32": raw.get("extension_f8_raw_u32"),
         "source_defined_after_raw_u32": _INVALID_ID,
         "source_defined_value_ready": True, "descriptor_ready": True,
         "source_reached": False, "actual_write_observed": False},
        {"target_role": "fresh_character1B8_reload_if_nonnull", "target_identity": None,
         "field_offset": "0x100", "conditional_on": "fresh_character1b8_reload_is_nonnull",
         "source_defined_after_raw_u64_hex": "0xFFFFFFFF029C77F8",
         "source_defined_after_raw64": _RESET_RAW_I64,
         "source_defined_value_ready": True, "descriptor_ready": True,
         "fresh_target_observed": False, "source_reached": False, "actual_write_observed": False}]
    result.update(current_extension_branch_ready=True, reset_inputs_ready=True,
        source_defined_reset_descriptors_ready=True,
        remaining_stage_inputs=["actual_reset_reached_and_fresh_character1b8_reload",
            "actual_post_reset_origin_selected_inputs_and_callee_effects",
            "reached28B2710_mutator_effects_and_actual_post_mutator_owner_context_date"])
    return result


def project_current_character_detachment_inputs_v1(raw: Mapping | None) -> dict:
    """Keep current observations separate from conditional source constants.

    Each incoming occurrence retains its passed Province and current chain.
    Reset stores do not need the old values. The second store targets a fresh
    later Character1B8 reload, whose identity is not the standing observation.
    No getter, mutator, reset, future-date evaluation or native call is replayed.
    """
    result = {"projection_kind": "current_character_detachment_suffix_v1",
        "source_parent_rva": "0x28CBE50", "source_parent_identity": None,
        "current_date_storage_raw64": None,
        "input_basis": "ordered_same_query_current_character_suffix_seeds",
        "seed_selection_ready": False, "seed_roster_ready": False,
        "status": "unavailable", "ready": False,
        "current_extension_inputs_ready": False,
        "requests": [], "known_current_input_prefix_count": 0,
        "independently_ready_request_indices": [], "no_suffix_request_indices": [],
        "conditional_reset_descriptor_request_indices": [],
        "current_source_chain_ready_request_indices": [],
        "missing_current_extension_inputs": [], "remaining_stage_inputs": [],
        "unavailable_reason": "native_current_character_detachment_family_absent", **_LIMITS}
    if not isinstance(raw, Mapping):
        return result
    result.update(source_parent_identity=raw.get("source_parent_identity"),
        current_date_storage_raw64=raw.get("current_date_storage_raw64"),
        seed_selection_ready=raw.get("seed_selection_ready") is True,
        seed_roster_ready=raw.get("seed_roster_ready") is True)
    rows = raw.get("requests")
    rows = rows if isinstance(rows, list) else []
    prefix_open = True
    for index, request in enumerate(rows):
        row = _request(request if isinstance(request, Mapping) else {}, index)
        result["requests"].append(row)
        if row["current_extension_branch_ready"]:
            result["independently_ready_request_indices"].append(index)
            if prefix_open:
                result["known_current_input_prefix_count"] += 1
            key = "no_suffix_request_indices" if row["no_suffix"] else "conditional_reset_descriptor_request_indices"
            result[key].append(index)
        else:
            prefix_open = False
        if row["current_source_chain_ready"]:
            result["current_source_chain_ready_request_indices"].append(index)
        result["missing_current_extension_inputs"].extend(
            f"requests[{index}].{field}" for field in row["missing_current_extension_inputs"])
        for field in row["remaining_stage_inputs"]:
            if field not in result["remaining_stage_inputs"]:
                result["remaining_stage_inputs"].append(field)
    for field in ("seed_selection_ready", "seed_roster_ready"):
        if result[field] is not True:
            result["missing_current_extension_inputs"].append(field)
    capture_unavailable = not rows and raw.get("status") == "unavailable"
    if capture_unavailable:
        result["missing_current_extension_inputs"].append("current_request_capture_unavailable")
    ready = result["seed_selection_ready"] and result["seed_roster_ready"] and all(
        row["current_extension_branch_ready"] for row in result["requests"]) and not capture_unavailable
    result.update(ready=ready, current_extension_inputs_ready=ready,
        status="available" if ready else ("unavailable" if capture_unavailable else "partial"),
        unavailable_reason=None if ready else "current_character_detachment_extension_inputs_partial")
    return result
