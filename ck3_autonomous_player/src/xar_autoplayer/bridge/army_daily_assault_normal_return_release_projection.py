"""Count-driven current assault record release under an explicit normal return."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_daily_assault_allocator_witness_contract import ARMY_ALLOCATOR_RVA, ARRG_ALLOCATOR_RVA
from .army_loss_allocation_projection import _signed_i32


def _vector_release(vector: Mapping, role: str) -> dict:
    header = vector.get("release_header_v1")
    header = header if isinstance(header, Mapping) else None
    witness = vector.get("allocator_witness")
    result = {
        "role": role, "release_branch": None, "normal_return_ready": False,
        "observed_release_header_v1": deepcopy(header),
        "observed_allocator_witness": deepcopy(witness),
        "known_store_requests": [], "conditional_header_before_free_call": None,
        "buffer_release_call_request": None,
        "conditional_post_header": None, "conditional_post_header_ready": False,
        "header_missing_inputs": [], "missing_inputs": [],
    }
    if header is None:
        return {**result, "missing_inputs": ["release_header_v1"]}
    before = {key: header[key] for key in
              ("data_present", "data_identity", "count_raw_i32", "capacity_raw_i32")}
    present = header["data_present"]
    if present is False:
        partial = [key for key in ("count_raw_i32", "capacity_raw_i32") if before[key] is None]
        return {**result, "release_branch": "actual_null_data_skip_all_stores",
                "normal_return_ready": True, "conditional_post_header": before,
                "conditional_post_header_ready": not partial, "header_missing_inputs": partial}
    if present is not True:
        return {**result, "missing_inputs": ["release_header_v1.data_present"]}
    #9D11F0 zeroes this count before dispatch. It remains a known prefix
    # request when the actual dynamic receiver's effects cannot be modeled.
    result.update(release_branch="nonnull_before_allocator_call",
        known_store_requests=[{"field": "count_raw_i32", "value": 0, "timing": "before_buffer_release_call"}],
        conditional_header_before_free_call={**before, "count_raw_i32": 0})
    expected = ARRG_ALLOCATOR_RVA if role == "ArRg" else ARMY_ALLOCATOR_RVA
    canonical = (isinstance(witness, Mapping) and witness.get("actual_read_ready") is True and
                 witness.get("matches_expected") is True and witness.get("expected_rva_u32") == expected)
    result["buffer_release_call_request"] = {
        "buffer_identity": header["data_identity"], "element_width": 4,
        "actual_allocator_identity": witness.get("actual_identity") if isinstance(witness, Mapping) else None,
        "expected_allocator_rva_u32": expected,
        "actual_canonical_receiver": canonical, "source_dispatch_rva": "0x8571C0" if canonical else None,
    }
    if not canonical:
        reason = "actual_noncanonical_allocator_effects" if isinstance(witness, Mapping) and witness.get("matches_expected") is False else "actual_canonical_allocator_witness"
        return {**result, "missing_inputs": [reason]}
    after = {"data_present": False, "data_identity": None, "count_raw_i32": 0, "capacity_raw_i32": 0}
    return {**result, "release_branch": "nonnull_canonical_normal_return",
            "normal_return_ready": True, "conditional_post_header": after,
            "conditional_post_header_ready": True,
            "known_store_requests": result["known_store_requests"] + [
                {"field": "data_identity", "value": None, "timing": "after_buffer_release_normal_return"},
                {"field": "capacity_raw_i32", "value": 0, "timing": "after_buffer_release_normal_return"}]}


def project_current_daily_assault_normal_return_release_v1(
    army_strength: Mapping, queue_projection: Mapping | None,
) -> dict:
    """Project source cleanup independently of missing numerical group inputs.

    The premise is a standalone observed-current-table invocation reaching
    cleanup with ordinary returning numerical calls. The selected canonical
    callbacks release raw buffers only. Queue execution and future stages are
    separate, and all captured inputs remain observations rather than writes.
    """
    result = {
        "projection_kind": "conditional_current_daily_assault_normal_return_release",
        "source_contract_game_version": "1.20.0.3", "army_id": army_strength.get("army_id"),
        "stage": "conditional_current_table_cleanup_normal_return",
        "normal_return_premise": "standalone_observed_current_table_invocation_reaches_cleanup; ordinary_returning_numerical_calls",
        "status": "unavailable", "conditional_table_cleanup_ready": False,
        "cleanup_branch": None, "observed_occupied_count_raw_i32": None,
        "conditional_occupied_count_raw_i32": None,
        "observed_physical_controls": None, "conditional_physical_controls": None,
        "record_release_prefix": [], "table_control_count_prefix": [],
        "untouched_captured_group_slots": [], "next_missing_record": None,
        "header_partial_fields": [], "missing_inputs": [],
        "preserved_pre_release_pending_prefix_ready": False,
        "preserved_pre_release_pending_prefix": None,
        "conditional_post_release_pending_prefix_ready": False,
        "conditional_post_release_pending_prefix": None,
        "conditional_post_release_pending_sequence_ready": False,
        "conditional_post_release_pending_sequence": None,
        "conditional_post_release_pending_occurrences": None,
        "queue_missing_inputs": [],
        "actual_record_release": False, "actual_effects": False,
        "actual_post_table": None, "actual_post_release_pending_sequence": None,
        "queue_execution_ready": False, "queue_drain_replayed": False,
        "Army_removal_replayed": False, "next_day_pending_ready": False,
        "full_daily_assault_ready": False, "full_regular_refill_ready": False,
        "full_monthly_ready": False, "full_calendar_ready": False, "live": False,
        "native_writes_executed": 0,
    }
    queue_prefix_ready = (isinstance(queue_projection, Mapping) and
                          queue_projection.get("conditional_pre_release_pending_prefix_ready") is True)
    queue_complete = (isinstance(queue_projection, Mapping) and
                      queue_projection.get("conditional_pre_release_pending_sequence_ready") is True)
    if queue_prefix_ready:
        result.update(preserved_pre_release_pending_prefix_ready=True,
            preserved_pre_release_pending_prefix=deepcopy(queue_projection["conditional_pre_release_pending_prefix"]))
    if isinstance(queue_projection, Mapping):
        result["queue_missing_inputs"] = deepcopy(queue_projection.get("missing_inputs", []))
    else:
        result["queue_missing_inputs"] = ["current_daily_assault_queue_append_projection"]
    table = army_strength.get("current_daily_assault_table_v1")
    if not isinstance(table, Mapping):
        return {**result, "status": "partial" if queue_prefix_ready else "unavailable",
                "missing_inputs": ["current_daily_assault_table_v1"]}
    occupied = table["header"]["occupied_count_raw_i32"]
    controls = deepcopy(table["physical_controls"])
    result.update(observed_occupied_count_raw_i32=occupied,
        conditional_occupied_count_raw_i32=occupied,
        observed_physical_controls=deepcopy(controls), conditional_physical_controls=controls,
        untouched_captured_group_slots=[group["physical_slot_i64"] for group in table["groups"]])
    if type(occupied) is not int:
        return {**result, "status": "partial" if queue_prefix_ready else "unavailable",
                "missing_inputs": ["header.occupied_count_raw_i32"]}
    if occupied <= 0:
        result.update(cleanup_branch="signed_nonpositive_occupied_count_skip_all_release",
                      conditional_table_cleanup_ready=True)
    else:
        result["cleanup_branch"] = "positive_occupied_count_scan_from_slot0"
        control_map = {row["physical_slot_i64"]: row for row in controls}
        group_map = {group["physical_slot_i64"]: group for group in table["groups"]}
        slot = 0
        remaining = occupied
        while remaining > 0:
            control = control_map.get(slot)
            byte = control["control_raw_u8"] if control is not None else None
            end = table["header"]["end_slot_raw_i32"]
            if control is None and slot == end:
                byte = table["header"]["end_marker_control_raw_u8"]
            if byte is None:
                result["next_missing_record"] = {"physical_slot_i64": slot,
                    "missing_operand": "actual_cleanup_scan_control_byte", "remaining_occupied_count_raw_i32": remaining}
                result["missing_inputs"] = ["actual_cleanup_scan_control_byte"]
                break
            if byte == 0:
                slot += 1
                continue
            group = group_map.get(slot)
            if group is None:
                operand = "uncaptured_end_marker_record_payload" if slot == end else "uncaptured_nonzero_control_record_payload"
                result["next_missing_record"] = {"physical_slot_i64": slot, "control_raw_u8": byte,
                    "missing_operand": operand, "remaining_occupied_count_raw_i32": remaining}
                result["missing_inputs"] = [operand]
                break
            record = {"native_index": group["native_index"], "physical_slot_i64": slot,
                      "normal_return_ready": False, "vectors": []}
            for key, role in (("arrgs", "ArRg"), ("armies", "Army")):
                vector = _vector_release(group[key], role)
                record["vectors"].append(vector)
                for field in vector["header_missing_inputs"]:
                    result["header_partial_fields"].append({"physical_slot_i64": slot, "role": role, "field": field})
                if not vector["normal_return_ready"]:
                    result["next_missing_record"] = {"physical_slot_i64": slot,
                        "native_index": group["native_index"], "role": role,
                        "missing_operand": deepcopy(vector["missing_inputs"]),
                        "remaining_occupied_count_raw_i32": remaining}
                    result["missing_inputs"] = [{"physical_slot_i64": slot, "role": role,
                                                "inputs": deepcopy(vector["missing_inputs"])}]
                    break
            result["record_release_prefix"].append(record)
            if len(record["vectors"]) != 2 or not all(vector["normal_return_ready"] for vector in record["vectors"]):
                break
            record["normal_return_ready"] = True
            after = _signed_i32(remaining - 1)
            result["table_control_count_prefix"].append({"physical_slot_i64": slot,
                "control_before_raw_u8": byte, "conditional_control_after_raw_u8": 0,
                "occupied_count_before_raw_i32": remaining, "conditional_occupied_count_after_raw_i32": after})
            control_map[slot]["control_raw_u8"] = 0
            result["untouched_captured_group_slots"].remove(slot)
            remaining = after
            result["conditional_occupied_count_raw_i32"] = remaining
            slot += 1
        if remaining <= 0:
            result["conditional_table_cleanup_ready"] = True
    cleanup_ready = result["conditional_table_cleanup_ready"]
    post_prefix_ready = cleanup_ready and queue_prefix_ready
    post_complete = cleanup_ready and queue_complete
    result.update(
        status="available" if post_complete else "partial",
        conditional_post_release_pending_prefix_ready=post_prefix_ready,
        conditional_post_release_pending_prefix=deepcopy(result["preserved_pre_release_pending_prefix"]) if post_prefix_ready else None,
        conditional_post_release_pending_sequence_ready=post_complete,
        conditional_post_release_pending_sequence=deepcopy(queue_projection["conditional_pre_release_pending_sequence"]) if post_complete else None,
        conditional_post_release_pending_occurrences=deepcopy(queue_projection["conditional_pre_release_occurrences"]) if post_prefix_ready else None,
    )
    return result
