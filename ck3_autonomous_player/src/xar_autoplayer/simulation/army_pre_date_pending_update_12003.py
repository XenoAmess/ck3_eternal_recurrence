"""Observed-current ordered2A92320 list/count and removal-request projection.

The native mutator is never invoked. Earlier2A9A360, remaining per-Army prefix,
physical table carry/growth and actual next callback state are separate.
"""
from __future__ import annotations

from copy import deepcopy
from math import copysign, inf, isnan
import struct
from typing import Mapping

_SENTINEL = 0xFFFFFFFF


def _i32(value: int) -> int:
    value &= _SENTINEL
    return value - (1 << 32) if value & (1 << 31) else value


def _hash(value: int) -> int:
    result = 0x811C9DC5
    for shift in (0, 8, 16, 24):
        result = ((result ^ ((value >> shift) & 255)) * 0x01000193) & _SENTINEL
    return result


def _f32(value: float | int) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _density_exceeds(count: int, mask: int, threshold_bits: int) -> bool:
    numerator, denominator = _f32(_i32(count + 1)), _f32(mask)
    if denominator == 0:
        density = float("nan") if numerator == 0 else copysign(inf, numerator * copysign(1, denominator))
    else:
        density = _f32(numerator / denominator)
    threshold = struct.unpack("<f", struct.pack("<I", threshold_bits))[0]
    # COMISS/JA does not select growth on an unordered comparison.
    return not isnan(density) and not isnan(threshold) and density > threshold


def _selected(resolution: Mapping) -> bool:
    return resolution.get("selected_object_ready") is True


def _dispatch(row: Mapping) -> tuple[bool | None, str]:
    if not _selected(row["original_army_resolution"]):
        return None, "army_selection_unavailable"
    if not _selected(row["combat_resolution"]) or row["combat_magic_0c_raw_u32"] is None:
        return None, "combat_operand_unavailable"
    if row["combat_magic_0c_raw_u32"] == 0x436F6D62:
        full = row["combat_resolution"]["selected_full_id_u32"]
        if full is None:
            return None, "combat_full_id_unavailable"
        if full != _SENTINEL:
            return False, "valid_combat_bypass"
    counter = row["army_counter_5c_raw_i32"]
    if counter is None:
        return None, "army_5c_unavailable"
    return (counter == 0, "pending_mutator_selected" if counter == 0 else "army_5c_bypass")


def _append_arm(row: Mapping) -> tuple[bool | None, int | None, str]:
    def result(append: bool, branch: str):
        full = row["append_full_id_u32"]
        if full is None:
            full = row["arrg_resolution"]["selected_full_id_u32"]
        return append, full if append else None, branch
    if not _selected(row["arrg_resolution"]) or row["current_38_raw_i32"] is None:
        return None, None, "arrg_current_unavailable"
    if row["current_38_raw_i32"] == 0:
        return result(True, "current_zero")
    if not _selected(row["contract_resolution"]) or row["contract_flag_b9_raw_u8"] is None:
        return None, None, "subject_contract_b9_unavailable"
    if row["contract_flag_b9_raw_u8"] != 0:
        return result(True, "subject_contract_b9_nonzero")
    if row["state_14c_raw_i32"] is None:
        return None, None, "arrg_14c_unavailable"
    if row["state_14c_raw_i32"] != 1:
        return result(False, "arrg_14c_not_one")
    if row["original_data_present"] is not True or not _selected(row["persistent_resolution"]):
        return None, None, "original_first_data_persistent_unavailable"
    war_id = row["persistent_war_id_13c_raw_u32"]
    if war_id is None:
        return None, None, "persistent_13c_unavailable"
    if war_id == _SENTINEL:
        return result(False, "persistent_13c_sentinel_skip")
    if not _selected(row["war_resolution"]) or row["war_magic_0c_raw_u32"] is None:
        return None, None, "selected_war_unavailable"
    if row["war_magic_0c_raw_u32"] != 0x5761725F:
        return result(True, "selected_war_magic_invalid")
    full = row["war_resolution"]["selected_full_id_u32"]
    if full is None:
        return None, None, "selected_war_full_id_unavailable"
    return result(full == _SENTINEL, "selected_war_full_id_invalid" if full == _SENTINEL else "valid_selected_war_skip")


def _reference_values(refs: Mapping) -> list[int] | None:
    return [r["raw_full_id_u32"] for r in refs["occurrences"]] if refs["references_ready"] else None


def project_current_pre_date_pending_update_v1(army: Mapping) -> dict:
    """Replay current observed pending operands in original Army occurrence order."""
    family = army.get("current_pre_date_pending_update_inputs_v1")
    result = {
        "status": "unavailable", "ready": False, "unavailable_reason": "current_pre_date_pending_update_inputs_unavailable",
        "source": "same_input_conditional_current_pre_date_pending_update_v1",
        "input_basis": "same_capture_observed_current_pre_date_pending_context",
        "native_source_rva": "2A99DC0/2A92320", "native_mutator_invocations": 0,
        "fixed_captured_nonphysical_context": True, "normal_helper_return_assumed": True,
        "occurrences": [], "pending_lists": [], "removal_append_requests": [],
        "conditional_removal_queue_full_ids_u32": None, "combined_removal_queue_ready": False,
        "conditional_skip_2a99b40_occurrence_indices": [], "completed_original_occurrence_count": 0,
        "pending_counts_and_removal_requests_ready": False, "updated_pending_values_ready": False,
        "actual_pre_date_callback_ready": False, "actual_tomorrow_roster_ready": False,
        "full_daily_assault_ready": False, "full_monthly_ready": False, "native_writes": 0,
    }
    if family is None:
        return result
    rows = family["occurrences"]
    references = family["original_roster"]
    initial_queue = _reference_values(family["removal_queue"])
    physical: dict[int, dict] = {}
    # Union only genuinely captured current probes; later direct insertions overlay it.
    for row in rows:
        for probe in row["pending_setup"]["probes"]:
            slot = probe["physical_slot_i64"]
            current = physical.setdefault(slot, {"control": probe["control_raw_u8"], "key": probe["key_raw_full_id_u32"]})
            if current["control"] is None:
                current["control"] = probe["control_raw_u8"]
            if current["key"] is None:
                current["key"] = probe["key_raw_full_id_u32"]
    working: dict[int, dict] = {}
    map_count: int | None = None
    stopped = False
    stop_reason = None
    for row in rows:
        index = row["native_index"]
        decision = {
            "native_index": index, "raw_full_id_u32": row["raw_full_id_u32"],
            "selected_army_full_id_u32": row["original_army_resolution"]["selected_full_id_u32"],
            "status": "not_reached" if stopped else "partial", "ready": False,
            "unavailable_reason": "earlier_original_occurrence_incomplete" if stopped else None,
            "pending_mutator_selected": None, "dispatch_branch": None, "pending_setup_branch": None,
            "pending_count_before": None, "pending_count_after": None, "arrg_selection_ledger": [],
            "appended_full_ids_u32": None, "removal_requested": None,
            "skip_2a99b40_and_24df3c0": None,
        }
        result["occurrences"].append(decision)
        if stopped:
            continue
        called, branch = _dispatch(row)
        decision.update(pending_mutator_selected=called, dispatch_branch=branch)
        reason = branch if called is None else None
        if called is False:
            decision.update(status="available", ready=True, removal_requested=False, skip_2a99b40_and_24df3c0=False,
                            unavailable_reason=None)
            result["completed_original_occurrence_count"] += 1
            continue
        setup = row["pending_setup"]
        target = setup["target_army_full_id_u32"]
        decision["selected_army_full_id_u32"] = target if called else decision["selected_army_full_id_u32"]
        candidate = deepcopy(working.get(target)) if target is not None else None
        inserted_slot = None
        next_map_count = map_count
        if called and target is None:
            reason = "selected_army_full_id_unavailable"
        if called and candidate is None and reason is None:
            mask = setup["mask_raw_i32"]
            if setup["entries_present"] is not True or mask is None:
                reason = "pending_map_header_unavailable"
            else:
                slot, distance = _i32(_hash(target)) & mask, 1
                while reason is None:
                    observed = physical.get(slot)
                    if observed is None or observed["control"] is None:
                        reason = "evolving_pending_probe_unobserved"
                        break
                    control = observed["control"]
                    if control < distance:
                        decision["pending_setup_branch"] = "direct_empty"
                        tail, threshold = setup["insertion_tail_raw_u8"], setup["insertion_threshold_bits_u32"]
                        count = next_map_count if next_map_count is not None else setup["map_count_raw_i32"]
                        if tail is None or threshold is None or count is None:
                            reason = "pending_insertion_header_unavailable"
                        elif distance > tail or _density_exceeds(count, mask, threshold):
                            reason = "pending_table_growth_unmodeled"
                        elif control != 0:
                            reason = "pending_table_carried_collision_unmodeled"
                        else:
                            candidate = {"army_full_id_u32": target, "initial_count": 0, "count": 0, "values": [],
                                         "appended_values": [], "setup_branch": "direct_empty"}
                            inserted_slot = (slot, distance)
                            next_map_count = _i32(count + 1)
                        break
                    if observed["key"] is None:
                        reason = "pending_probe_key_unavailable"
                        break
                    if observed["key"] == target:
                        decision["pending_setup_branch"] = "existing_key"
                        refs = setup["existing_references"]
                        count = refs["count_raw_i32"]
                        if count is None:
                            reason = "existing_pending_count_unavailable"
                        else:
                            candidate = {"army_full_id_u32": target, "initial_count": count, "count": count,
                                         "values": _reference_values(refs), "appended_values": [], "setup_branch": "existing_key"}
                        break
                    slot += 1
                    distance = (distance + 1) & 255
        elif called and candidate is not None:
            decision["pending_setup_branch"] = "evolving_existing_key"
        appended: list[int | None] = []
        if reason is None and called:
            arrg_refs = row["original_arrg_references"]
            if not arrg_refs["references_ready"]:
                reason = "original_arrg_references_incomplete"
            else:
                for arrg in row["arrg_occurrences"]:
                    append, full, arm = _append_arm(arrg)
                    decision["arrg_selection_ledger"].append({"native_index": arrg["native_index"],
                        "raw_full_id_u32": arrg["raw_full_id_u32"], "append": append, "append_full_id_u32": full, "branch": arm})
                    if append is None:
                        reason = arm
                        break
                    if append:
                        appended.append(full)
        if reason is not None:
            decision["unavailable_reason"] = reason
            stopped, stop_reason = True, reason
            continue
        before = candidate["count"]
        after = _i32(before + len(appended))
        candidate["count"] = after
        candidate["appended_values"].extend(appended)
        if candidate["values"] is not None and all(value is not None for value in appended):
            candidate["values"].extend(appended)
        else:
            candidate["values"] = None
        working[target] = candidate
        if inserted_slot is not None:
            physical[inserted_slot[0]] = {"control": inserted_slot[1], "key": target}
            map_count = next_map_count
        original_count = row["original_arrg_references"]["count_raw_i32"]
        remove = after == original_count
        decision.update(status="available", ready=True, unavailable_reason=None, pending_count_before=before,
                        pending_count_after=after, appended_full_ids_u32=appended if all(v is not None for v in appended) else None,
                        removal_requested=remove, skip_2a99b40_and_24df3c0=remove)
        if remove:
            result["removal_append_requests"].append({"native_index": index, "army_full_id_u32": target})
            result["conditional_skip_2a99b40_occurrence_indices"].append(index)
        result["completed_original_occurrence_count"] += 1
    result["pending_lists"] = [{"army_full_id_u32": record["army_full_id_u32"], "initial_count": record["initial_count"],
        "conditional_count": record["count"], "conditional_full_ids_u32": record["values"],
        "appended_full_ids_u32": record["appended_values"] if all(v is not None for v in record["appended_values"]) else None,
        "values_ready": record["values"] is not None, "initial_setup_branch": record["setup_branch"]}
        for record in working.values()]
    count = references["count_raw_i32"]
    complete = references["references_ready"] and count is not None and result["completed_original_occurrence_count"] == count
    values_ready = complete and all(record["values"] is not None for record in working.values())
    result["pending_counts_and_removal_requests_ready"] = complete
    result["updated_pending_values_ready"] = values_ready
    result["ready"] = complete and values_ready
    result["status"] = "available" if result["ready"] else "partial"
    result["unavailable_reason"] = None if result["ready"] else stop_reason or (
        "updated_pending_values_incomplete" if complete else "original_roster_references_incomplete")
    if initial_queue is not None:
        result["conditional_removal_queue_full_ids_u32"] = initial_queue + [r["army_full_id_u32"] for r in result["removal_append_requests"]]
        result["combined_removal_queue_ready"] = complete
    return result
