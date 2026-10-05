"""Finite conditional24E3430 caller stores beside the loss subsystem.

Counter addends and final tail gate use original caller budgets, not physical
casualties. The manager+2A5A8 operation is an ordered raw-ID append; its later
consumer and full monthly applied outcome are outside this model.
"""
from __future__ import annotations

from typing import Mapping

from ..simulation.battle_trait_numeric_inputs_12003 import native_wrap32_12003 as _i32


def _integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < 1 << (bits - 1)


def project_conditional_monthly_caller_effects(
    army_strength: Mapping[str, object], budget_projection: Mapping[str, object],
) -> dict[str, object]:
    """Project byte/date, physical side-counter cells and the ordered ID list.

    A nullable input block does not hide independently known stores. No-side
    is a legal skip; fallback references alias one War object per side, while
    repeated resolved War IDs reload their derived cell before the next add.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_finite_monthly_caller_effects",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "same_query_original_budgets_observed_counter_cells_and_derived_loss_subsystem",
        "status": "unavailable", "conditional_caller_effects_ready": False,
        "actual_effects": False, "actual_loss": False, "actual_post_state": None,
        "actual_caller_passed_date_raw64": None,
        "full_monthly_applied_loss_ready": False,
        "army_byte_22_before": None,
        "conditional_byte_22_after": None, "conditional_byte_22_ready": False,
        "supply_update_date_before_raw64": None,
        "conditional_supply_update_date_raw64": None,
        "conditional_supply_update_date_ready": False,
        "conditional_date_input_basis": "current_frame_date_storage_as_explicit_entry_argument",
        "native_date_pointer_origin": "GameState+8",
        "native_date_pointer_origin_source_closed": True,
        "war_counter_increment_soldiers": None, "war_counter_ready": False,
        "war_counter_writes": [], "war_counter_skipped_occurrences": [],
        "conditional_war_counter_cells_after": None,
        "tail_original_budget_total_soldiers": None,
        "tail_conditional_post_loss_current_soldiers": None,
        "id_append_decision_ready": False, "conditional_id_append_required": None,
        "manager_army_id_list_2a5a8_before": None,
        "conditional_manager_army_id_list_2a5a8_after": None,
        "conditional_manager_army_id_list_ready": False,
        "id_collection_operation": "ordered_raw_DWORD_append_without_deduplication",
        "id_collection_growth_basis": "conditional_on_ordinary_successful_native_allocation_if_needed",
        "missing_inputs": [],
    }
    if army_strength.get("status") != "available":
        return {**result, "missing_inputs": ["available_same_query_army_strength"]}
    raw_inputs = army_strength.get("monthly_caller_effect_inputs_v1")
    inputs = raw_inputs if isinstance(raw_inputs, Mapping) else {}
    raw_clock = army_strength.get("army_update_clock_v1")
    clock = raw_clock if isinstance(raw_clock, Mapping) else {}
    missing: list[str] = result["missing_inputs"]

    #24E4D10 writes this byte before any admission rejection. Its current
    # value is an observation, not a prerequisite for the conditional store.
    result.update(army_byte_22_before=inputs.get("army_byte_22_raw"),
                  conditional_byte_22_after=1, conditional_byte_22_ready=True)
    previous_date = clock.get("last_supply_update_date_storage_raw64")
    result["supply_update_date_before_raw64"] = previous_date
    admitted = budget_projection.get("supply_updater_admitted")
    if admitted is True:
        # The daily dispatcher source passes this GameState+8 storage pointer.
        # Its observed current64 value is the explicit hypothetical entry
        # value; the future event-time value is still not observed.
        date_key = "current_date_storage_raw64"
        date = inputs.get(date_key)
    elif admitted is False:
        date_key = "last_supply_update_date_storage_raw64"
        date = previous_date
    else:
        date_key, date = "supply_updater_admission", None
    if _integer(date, 64):
        result.update(conditional_supply_update_date_raw64=date,
                      conditional_supply_update_date_ready=True)
    else:
        missing.append(date_key)

    supply = budget_projection.get("supply_budget_soldiers")
    siege = budget_projection.get("siege_budget_soldiers")
    raid = budget_projection.get("raid_budget_soldiers")
    if _integer(supply, 32) and _integer(siege, 32):
        increment = _i32(supply + siege)
        result["war_counter_increment_soldiers"] = increment
        if increment <= 0:
            result.update(war_counter_ready=True, conditional_war_counter_cells_after=[])
        else:
            _project_war_cells(result, inputs, increment)
    else:
        missing.extend(key for key, value in (
            ("supply_budget_soldiers", supply), ("siege_budget_soldiers", siege)
        ) if not _integer(value, 32))

    if all(_integer(value, 32) for value in (supply, siege, raid)):
        total = _i32(_i32(siege + raid) + supply)
        result["tail_original_budget_total_soldiers"] = total
        if total <= 0:
            result.update(id_append_decision_ready=True, conditional_id_append_required=False)
        else:
            sequence = budget_projection.get("same_input_conditional_loss_sequence_v1")
            sequence = sequence if isinstance(sequence, Mapping) else {}
            current = sequence.get("conditional_final_current_soldiers")
            if sequence.get("conditional_sequence_ready") is True and _integer(current, 32):
                result.update(tail_conditional_post_loss_current_soldiers=current,
                              id_append_decision_ready=True,
                              conditional_id_append_required=current <= 0)
            else:
                missing.append("derived_loss_subsystem_final_current_soldiers")
    else:
        missing.extend(key for key, value in (
            ("supply_budget_soldiers", supply), ("siege_budget_soldiers", siege),
            ("raid_budget_soldiers", raid)
        ) if not _integer(value, 32))

    current_list = inputs.get("manager_army_id_list_2a5a8")
    list_ready = isinstance(current_list, list) and all(_integer(value, 32) for value in current_list)
    if list_ready:
        result["manager_army_id_list_2a5a8_before"] = list(current_list)
    if result["id_append_decision_ready"]:
        if not list_ready:
            missing.append("manager_army_id_list_2a5a8")
        elif result["conditional_id_append_required"]:
            army_id = army_strength.get("native_carmy_id")
            if _integer(army_id, 32):
                result.update(conditional_manager_army_id_list_2a5a8_after=[*current_list, army_id],
                              conditional_manager_army_id_list_ready=True)
            else:
                missing.append("native_carmy_id")
        else:
            result.update(conditional_manager_army_id_list_2a5a8_after=list(current_list),
                          conditional_manager_army_id_list_ready=True)

    result["missing_inputs"] = list(dict.fromkeys(missing))
    ready = all(result[key] for key in (
        "conditional_byte_22_ready", "conditional_supply_update_date_ready",
        "war_counter_ready", "conditional_manager_army_id_list_ready"))
    result.update(conditional_caller_effects_ready=ready,
                  status="available" if ready else "partial")
    return result


def _project_war_cells(
    result: dict[str, object], inputs: Mapping[str, object], increment: int,
) -> None:
    rows = inputs.get("war_counter_rows")
    if not isinstance(rows, list):
        result["missing_inputs"].append("war_counter_rows")
        return
    cells: dict[tuple[object, ...], dict[str, object]] = {}
    complete = True
    for row in rows:
        if not isinstance(row, Mapping) or row.get("status") != "available":
            index = row.get("stored_index") if isinstance(row, Mapping) else None
            result["missing_inputs"].append(f"war_counter_rows[{index}].available_operands")
            complete = False
            break
        side = row.get("native_selected_side")
        if side == -1:
            result["war_counter_skipped_occurrences"].append({
                "stored_index": row["stored_index"], "war_reference_id": row["war_reference_id"],
                "reason": "native_actor_membership_neither_side",
            })
            continue
        counter = row.get("native_counter_30_raw")
        fallback, war_id = row.get("used_fallback"), row.get("resolved_war_id")
        if (type(side) is not int or side not in (0, 1) or type(fallback) is not bool
                or not _integer(counter, 32) or (not fallback and not _integer(war_id, 32))):
            result["missing_inputs"].append(f"war_counter_rows[{row['stored_index']}].selected_counter_cell")
            complete = False
            break
        key = ("fallback", side) if fallback else ("war", war_id, side)
        cell = cells.setdefault(key, {
            "cell_kind": "fallback" if fallback else "resolved_war",
            "resolved_war_id": None if fallback else war_id,
            "native_selected_side": side, "initial_counter_30_raw": counter,
            "conditional_counter_30_raw": counter, "write_occurrences": 0,
        })
        before = cell["conditional_counter_30_raw"]
        after = _i32(before + increment)
        cell.update(conditional_counter_30_raw=after, write_occurrences=cell["write_occurrences"] + 1)
        result["war_counter_writes"].append({
            "stored_index": row["stored_index"], "war_reference_id": row["war_reference_id"],
            "resolved_war_id": war_id, "used_fallback": fallback,
            "native_selected_side": side, "same_query_counter_30_raw": counter,
            "conditional_counter_before_raw": before,
            "original_budget_increment_soldiers": increment,
            "conditional_counter_after_raw": after,
        })
    if complete:
        result.update(war_counter_ready=True, conditional_war_counter_cells_after=list(cells.values()))
