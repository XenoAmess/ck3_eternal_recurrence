"""Conditional24E3430 four-pass loss subsystem from one normalized query.

Budgets are explicit current readonly operands, not a future updater result.
Only associated physical current stores and2633340 current/max are replayed;
every intermediate frame is derived, never a new native observation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes

SCALE = 100_000


def _i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _trunc0(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // abs(denominator)
    return -quotient if numerator < 0 else quotient


def project_conditional_army_loss_sequence(army: Mapping[str, object]) -> dict[str, object]:
    """Interleave allocation, associated writer and refresh in stored order.

The next pass recounts conditional current. Within a pass its denominator
decreases by the OLD current, and its budget by the requested whole quantity.
Writer skip, chunk aliases and refresh gains cannot replace those updates.
"""
    result: dict[str, object] = {
        "projection_kind": "conditional_four_pass_loss_subsystem",
        "source_contract_game_version": "1.20.0.3",
        "status": "unavailable", "conditional_sequence_ready": False,
        "actual_loss": False, "actual_post_stage_current": None,
        "input_basis": "one_query_DATA_order_predicates_and_explicit_readonly_budgets",
        "intermediate_state_basis": "derived_writer_and_current_maximum_refresh",
        "passes": [], "missing_inputs": [],
        "conditional_final_regiment_strengths": None,
        "conditional_final_current_soldiers": None,
        "conditional_physical_chunks_after": None,
        "conditional_physical_chunks_ready": False,
        "conditional_physical_current_delta": None,
    }
    operands = army.get("loss_application_inputs_v1")
    rows = army.get("regiment_strengths")
    if (army.get("status") != "available" or not isinstance(operands, Mapping)
            or operands.get("status") != "available" or not isinstance(rows, list)):
        return {**result, "missing_inputs": ["available_same_query_loss_inputs_and_regiments"]}
    budgets = tuple(operands.get(field) for field in (
        "current_supply_loss_budget", "siege_loss_budget", "raid_loss_budget"))
    if any(type(value) is not int or not -(1 << 31) <= value < 1 << 31 for value in budgets):
        return {**result, "missing_inputs": ["signed32_loss_budgets"]}
    supply, siege, raid = budgets
    combined = _i32(siege + raid)
    result.update(supply_budget_soldiers=supply, siege_budget_soldiers=siege,
                  raid_budget_soldiers=raid, combined_siege_raid_budget_soldiers=combined)
    if supply > 0 or combined > 0:
        if any(row.get("siege_tier_observable") is not True for row in rows):
            result["missing_inputs"].append("per_regiment_definition_siege_tier")
        if supply > 0 and any(type(row.get("native_supply_loss_eligible")) is not bool for row in rows):
            result["missing_inputs"].append("per_regiment_native_2a956d0")
        if result["missing_inputs"]:
            return result

    state = deepcopy(dict(army))
    working_rows = state["regiment_strengths"]
    data_rows = state.get("regiment_replenishment_records_v1", [])
    physical_complete = all(any(
        data.get("army_regiment_id") == row["army_regiment_id"]
        and data.get("status") == "available" for data in data_rows
    ) for row in working_rows)
    before_physical: dict[tuple[int, int], int] = {}
    final_physical: dict[tuple[int, int], dict[str, int]] = {}
    for data in data_rows:
        for record in data.get("records", []):
            if record.get("status") != "available":
                continue
            key = (record["persistent_regiment_id"], record["chunk_index"])
            before_physical[key] = record["current_soldiers"]
            final_physical[key] = {
                "persistent_regiment_id": key[0], "chunk_index": key[1],
                "current_soldiers": record["current_soldiers"],
                "maximum_soldiers": record["maximum_soldiers"],
            }

    def apply_writer(request: Mapping[str, object]) -> tuple[dict[str, object], bool]:
        try:
            writer = project_observed_writer_chunk_changes(state, request)
        except ArithmeticError as error:
            writer = {"chunk_writeback_ready": False,
                      "missing_inputs": ["native_signed_division_result"],
                      "native_arithmetic_error": str(error)}
        if not writer["chunk_writeback_ready"]:
            return writer, False
        if writer["writer_skipped"]:
            return writer, True
        refresh = writer["conditional_raised_regiment_refresh"]
        if not refresh["current_maximum_ready"]:
            return writer, False
        changes = {(chunk["persistent_regiment_id"], chunk["chunk_index"]): chunk
                   for chunk in writer["physical_chunks_after"]}
        # Every occurrence reloads the same physical key. Later writer calls
        # must receive updated aliases rather than the initial query records.
        for data in data_rows:
            for record in data.get("records", []):
                key = (record["persistent_regiment_id"], record["chunk_index"])
                if key in changes:
                    record.update(current_soldiers=changes[key]["current_soldiers"],
                                  maximum_soldiers=changes[key]["maximum_soldiers"])
                    record["effective_current_soldiers"] = (
                        record["maximum_soldiers"] if record["state_raw"] == 3
                        and record["current_soldiers"] == 0 else record["current_soldiers"])
        final_physical.update(changes)
        for row in working_rows:
            if row["army_regiment_id"] == request["army_regiment_id"]:
                row.update(current_soldiers=refresh["current_soldiers"],
                           maximum_soldiers=refresh["maximum_soldiers"])
        return writer, True

    def run_pass(phase: str, budget: int, flags: int) -> tuple[int, bool]:
        preferred = phase.endswith("preferred")
        projection: dict[str, object] = {
            "phase": phase, "request_budget_soldiers": budget,
            "input_basis": "derived_conditional_stage" if result["passes"] else "observed_initial_stage",
            "native_filter_flags": flags, "requests": [],
        }
        if budget <= 0:
            projection.update(status="not_called", native_eligible_total_soldiers=None,
                              capped_request_budget_soldiers=0,
                              caller_overflow_residual_soldiers=0,
                              remaining_request_budget_soldiers=budget,
                              remaining_eligible_soldiers=None)
            result["passes"].append(projection)
            return 0, True
        selected = [row for row in working_rows
                    if (not flags & 1 or row["siege_tier"] <= 0)
                    and (not flags & 2 or row["native_supply_loss_eligible"])]
        total = 0
        for row in selected:
            total = _i32(total + row["current_soldiers"])
        remaining = capped = min(budget, total)
        overflow = _i32(budget - capped)
        projection.update(status="available", native_eligible_total_soldiers=total,
                          capped_request_budget_soldiers=capped,
                          caller_overflow_residual_soldiers=overflow if preferred else 0,
                          unallocated_residual_overflow_soldiers=0 if preferred else overflow)
        complete = True
        for row in selected:
            if remaining <= 0 or total <= 0:
                break
            # selected keeps references, so even repeated stored ArRg IDs read
            # their latest conditional current immediately before this call.
            current = row["current_soldiers"]
            product = _i32(current * remaining)
            quantity = _trunc0(product, total)
            request = {
                "army_regiment_id": row["army_regiment_id"],
                "current_soldiers_read": current,
                "remaining_budget_before": remaining, "remaining_eligible_before": total,
                "multiply_signed32": product, "requested_soldiers": quantity,
                "writer_quantity_raw": quantity * SCALE, "writer_quantity_scale": SCALE,
            }
            writer, complete = apply_writer(request)
            request["conditional_chunk_writeback"] = writer
            projection["requests"].append(request)
            if not complete:
                refresh = writer.get("conditional_raised_regiment_refresh") or {}
                result["missing_inputs"].append({
                    "phase": phase, "army_regiment_id": row["army_regiment_id"],
                    "inputs": writer.get("missing_inputs", []) + refresh.get("missing_inputs", []),
                })
                projection["status"] = "partial"
                break
            remaining = _i32(remaining - quantity)
            total = _i32(total - current)
        projection.update(remaining_request_budget_soldiers=remaining,
                          remaining_eligible_soldiers=total)
        result["passes"].append(projection)
        return overflow, complete

    for prefix, budget, preferred_flags, residual_flags in (
        ("supply", supply, 3, 2), ("siege_raid", combined, 1, 0),
    ):
        overflow, complete = run_pass(f"{prefix}_preferred", budget, preferred_flags)
        if complete:
            _, complete = run_pass(f"{prefix}_residual", overflow, residual_flags)
        if not complete:
            result["status"] = "partial"
            return result
    final_rows = [{"army_regiment_id": row["army_regiment_id"],
                   "current_soldiers": row["current_soldiers"],
                   "maximum_soldiers": row["maximum_soldiers"], "scale": 1}
                  for row in working_rows]
    final_current = 0
    for row in final_rows:
        final_current = _i32(final_current + row["current_soldiers"])
    return {
        **result, "status": "available", "conditional_sequence_ready": True,
        "conditional_final_regiment_strengths": final_rows,
        "conditional_final_current_soldiers": final_current,
        "conditional_physical_chunks_ready": physical_complete,
        "conditional_physical_chunks_after": list(final_physical.values()) if physical_complete else None,
        "conditional_physical_current_delta": sum(
            chunk["current_soldiers"] - before_physical[key]
            for key, chunk in final_physical.items()) if physical_complete else None,
    }
