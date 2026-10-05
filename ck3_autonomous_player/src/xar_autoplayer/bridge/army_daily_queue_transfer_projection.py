"""Finite same-input daily ordered ArmyID transfer and first removal request.

The daily consumer drains the logical source before resolving each temporary
ID. Initial resolution observations apply only until its first removal call;
later occurrences need the state produced by that call and its virtual tree.
"""
from __future__ import annotations

from typing import Mapping


def _i32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _u32(value: object) -> bool:
    return type(value) is int and 0 <= value < 1 << 32


def project_conditional_daily_id_transfer(
    army_strength: Mapping[str, object],
) -> dict[str, object]:
    """Project a conditional logical transfer and at most one native request.

    Known invalid initial occurrences make no removal call. The first valid
    occurrence selects2A978A0(primaryManager, Army*), including a valid fallback
    Army. A remaining suffix never reuses initial predicates after that call.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_daily_army_id_transfer",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "same_query_ordered_source_ids_and_initial_native_army_resolution",
        "conditional_transfer_basis": "explicit_consumer_entry_with_ordinary_successful_native_transfer",
        "status": "unavailable", "conditional_transfer_ready": False,
        "transfer_branch": None,
        "source_manager_army_id_list_before": None,
        "conditional_temporary_ordered_army_ids": None,
        "conditional_source_manager_army_id_list_after_transfer": None,
        "initial_removal_selection_ready": False,
        "initial_invalid_prefix_occurrences": [],
        "first_removal_call_request": None,
        "first_removal_call_request_ready": False,
        "remaining_occurrences": [], "post_removal_stage_required": False,
        "remaining_occurrences_basis": None, "missing_inputs": [],
        "actual_transfer": False, "actual_removal": False,
        "actual_source_queue_after": None, "actual_removal_post_state": None,
        "full_ordered_removal_requests_ready": False,
        "full_monthly_lifecycle_ready": False,
    }
    if army_strength.get("status") != "available":
        return {**result, "missing_inputs": ["available_same_query_army_strength"]}
    raw_inputs = army_strength.get("monthly_daily_queue_inputs_v1")
    inputs = raw_inputs if isinstance(raw_inputs, Mapping) else {}
    source_ids = inputs.get("manager_army_id_list_2a5a8")
    if not isinstance(source_ids, list) or not all(_i32(value) for value in source_ids):
        return {**result, "missing_inputs": ["manager_army_id_list_2a5a8"]}

    #2A9FA10 transfers all stored DWORDs and sets source count0 on both
    # allocator paths. Empty count bypasses that call in2A9A590 entirely.
    result.update(
        conditional_transfer_ready=True,
        transfer_branch="transfer" if source_ids else "not_called",
        source_manager_army_id_list_before=list(source_ids),
        conditional_temporary_ordered_army_ids=list(source_ids),
        conditional_source_manager_army_id_list_after_transfer=[],
    )
    if not source_ids:
        result.update(status="available", initial_removal_selection_ready=True)
        return result

    rows = inputs.get("initial_army_resolution_rows")
    for index, raw_id in enumerate(source_ids):
        row = rows[index] if isinstance(rows, list) and index < len(rows) else None
        if not _initial_resolution_available(row, index, raw_id):
            result.update(
                status="partial", remaining_occurrences=_occurrences(source_ids, index),
                remaining_occurrences_basis="unknown_initial_resolution",
                missing_inputs=[f"initial_army_resolution_rows[{index}].available_identity"],
            )
            return result

        occurrence = {
            "stored_index": index, "raw_army_reference_id": raw_id,
            "resolved_army_id": row["resolved_army_id"],
            "used_fallback": row["used_fallback"],
            "army_magic_14_raw": row["army_magic_14_raw"],
            "native_army_identity_valid": row["native_army_identity_valid"],
        }
        if not row["native_army_identity_valid"]:
            result["initial_invalid_prefix_occurrences"].append({
                **occurrence, "reason": "native_army_magic_or_full_id_invalid",
            })
            continue

        suffix = _occurrences(source_ids, index + 1)
        result.update(
            initial_removal_selection_ready=True, first_removal_call_request_ready=True,
            first_removal_call_request={
                **occurrence, "native_entry_rva": "0x2A978A0",
                "receiver_basis": "primary_army_manager",
                "argument_basis": "same_query_initial_native_army_resolution",
            },
            remaining_occurrences=suffix, post_removal_stage_required=bool(suffix),
            remaining_occurrences_basis="requires_post_removal_stage_frames" if suffix else None,
            missing_inputs=["post_removal_stage_full_id_slot_and_virtual_effects"] if suffix else [],
            status="partial" if suffix else "available",
        )
        return result

    result.update(status="available", initial_removal_selection_ready=True)
    return result


def _initial_resolution_available(row: object, index: int, raw_id: int) -> bool:
    if not isinstance(row, Mapping) or row.get("status") != "available":
        return False
    resolved = row.get("resolved_army_id")
    magic = row.get("army_magic_14_raw")
    identity = row.get("native_army_identity_valid")
    return (
        type(row.get("stored_index")) is int and row["stored_index"] == index
        and _i32(row.get("raw_army_reference_id")) and row["raw_army_reference_id"] == raw_id
        and _i32(resolved) and _u32(magic)
        and type(row.get("used_fallback")) is bool and type(identity) is bool
        and identity == (magic == 0x41726D79 and resolved != -1)
    )


def _occurrences(source_ids: list[int], start: int) -> list[dict[str, int]]:
    return [{"stored_index": index, "raw_army_reference_id": source_ids[index]}
            for index in range(start, len(source_ids))]
