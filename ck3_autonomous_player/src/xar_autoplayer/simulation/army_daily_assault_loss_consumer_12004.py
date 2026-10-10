"""Actual4 daily group numerical consumer at an explicit preceding-stage entry.

This small adapter executes no refill, preparation, native write or release.
It reuses the qualified group allocator/writer kernel after rebasing a private
copy to independently supplied complete prior-write overlays. Missing overlay
items are unchanged only when their completeness premise is explicit.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from xar_autoplayer.bridge.army_daily_assault_loss_projection import (
    _key, project_current_daily_assault_loss_v1,
)
from xar_autoplayer.bridge.army_loss_allocation_projection import _signed_i32


def _stage_result(army: Mapping, stage: Mapping) -> dict:
    return {
        "projection_kind": "conditional_explicit_stage_daily_assault_loss_12004",
        "source_contract_game_version": "1.20.0.4",
        "source_consumer_rva": "0x2A97EB0",
        "reused_numeric_kernel_contract_version": "1.20.0.3",
        "army_id": army.get("army_id"),
        "stage_id": stage.get("stage_id"), "capture_id": stage.get("capture_id"),
        "manager_identity": stage.get("manager_identity"),
        "input_basis": stage.get("basis"),
        "status": "unavailable", "stage_input_ready": False,
        "stage_group_entry_budgets": [], "original_current_group_observations": [],
        "missing_inputs": [], "numerical_prefix": None,
        "prior_refill_ADD_count": 0, "native_writes_executed": 0,
        "actual_loss": False, "actual_daily_loss": False, "actual_effects": False,
        "actual_post_stage": None, "full_daily_assault_ready": False,
        "full_monthly_ready": False, "release_effects_ready": False,
    }


def _all_data(inputs: Mapping):
    for target in inputs.get("target_regiments", []):
        data = target.get("replenishment_records_v1")
        if isinstance(data, Mapping):
            yield data
    for group in inputs.get("groups", []):
        family = group.get("besieging_inputs_v1")
        if isinstance(family, Mapping):
            for occurrence in family.get("occurrences", []):
                for regiment in occurrence.get("regiments", []):
                    data = regiment.get("replenishment_records_v1")
                    if isinstance(data, Mapping):
                        yield data


def project_army_daily_assault_loss_stage_12004(
    army: Mapping, *, stage: Mapping,
) -> dict:
    """Consume one source-ordered table at a supplied immutable numerical stage.

    ``physical_chunks`` contains every preceding-stage physical change;
    ``regiment_currents`` contains every preceding target-cache write. Both
    completeness flags describe the supplied prior-write set, not global
    game knowledge. Table membership/resolution and other nonphysical inputs
    are explicitly fixed to this stage's normalized table/loss families.

    ``group_budget_outputs`` accepts continuation38 results aligned by native
    index and physical slot. Derived B/budget is a simulation operand; the
    original observed native scalar is preserved independently in this result.
    """
    result = _stage_result(army, stage)
    table = army.get("current_daily_assault_table_v1")
    if not isinstance(table, Mapping):
        return {**result, "missing_inputs": ["current_daily_assault_table_v1"]}
    for name in ("stage_id", "capture_id", "manager_identity", "basis"):
        if not stage.get(name):
            result["missing_inputs"].append(name)
    if stage.get("manager_identity") != table.get("manager_identity"):
        result["missing_inputs"].append("stage_manager_matches_table")
    empty = (table.get("physical_scan_ready") is True and
             table.get("header", {}).get("occupied_count_raw_i32") == 0 and
             not table.get("groups"))
    if not empty:
        for name in ("physical_overlay_complete_for_prior_writes",
                     "cache_overlay_complete_for_prior_writes"):
            if stage.get(name) is not True:
                result["missing_inputs"].append(name)
    if result["missing_inputs"]:
        return result
    if empty:
        return {**result, "status": "available", "stage_input_ready": True,
                "numerical_prefix": project_current_daily_assault_loss_v1(army)}
    original = army.get("current_daily_assault_loss_inputs_v1")
    if not isinstance(original, Mapping):
        return {**result, "missing_inputs": ["current_daily_assault_loss_inputs_v1"]}
    copied = deepcopy(dict(army))
    inputs = copied["current_daily_assault_loss_inputs_v1"]
    copied_table = copied["current_daily_assault_table_v1"]
    currents = {row["object_identity"]: row for row in stage.get("regiment_currents", [])}
    physical = {(row["persistent_regiment_id"], row["chunk_index"]): row
                for row in stage.get("physical_chunks", [])}
    prior_changes = {}
    prior_rows = list(original.get("target_regiments", []))
    for group in original.get("groups", []):
        for count in group.get("army_counts", []):
            prior_rows.extend(count.get("regiments", []))
    for target in prior_rows:
        key = _key(target)
        overlay = currents.get(key)
        if overlay is None:
            continue
        before, after = target.get("current_soldiers"), overlay.get("current_soldiers")
        difference = (_signed_i32(after - before)
                      if type(before) is int and type(after) is int else None)
        if difference != 0:
            prior_changes[key] = difference

    budget_outputs = {(row["group_native_index"], row["physical_slot_i64"]): row
                      for row in stage.get("group_budget_outputs", [])}
    entry_budgets = []
    observed = []
    for group in inputs.get("groups", []):
        index, slot = group["native_index"], group["physical_slot_i64"]
        old_family = group.get("besieging_inputs_v1")
        observed.append({"group_native_index": index, "physical_slot_i64": slot,
                         "native_current_expected_loss": group.get("native_current_expected_loss"),
                         "native_besieging_strength": old_family.get("native_besieging_strength")
                         if isinstance(old_family, Mapping) else None})
        output = budget_outputs.get((index, slot))
        if output is not None:
            # The existing kernel consumes this internal scalar before any
            # target delta. Preserve its native observation outward above.
            group["native_current_expected_loss"] = output.get("expected_loss")
            group["besieging_inputs_v1"] = deepcopy(output.get("besieging_inputs_v1"))
            basis = "independent_group_Province_B_stage_output"
        elif prior_changes:
            # A prior target write may change group eligible B. An old native
            # scalar cannot be substituted for this missing stage producer.
            group["native_current_expected_loss"] = None
            group["besieging_inputs_v1"] = None
            basis = "missing_independent_group_B_stage_output"
        else:
            basis = "native_current_scalar_no_prior_cached_target_writes"
        entry_budgets.append({"group_native_index": index, "physical_slot_i64": slot,
                              "expected_loss": group.get("native_current_expected_loss"),
                              "basis": basis})
        # 2A95720 reads cached ArRg values with flags0. Rebase each captured
        # Army whole baseline by every original occurrence of prior writes;
        # DATA sharing alone never refreshes another ArRg cache.
        for count in group.get("army_counts", []):
            baseline = count.get("native_whole_current_soldiers")
            if not prior_changes:
                continue
            ready = count.get("ready") is True and type(baseline) is int
            delta = 0
            for regiment in count.get("regiments", []):
                if regiment.get("identity_valid") is False:
                    continue
                key = _key(regiment)
                if regiment.get("identity_valid") is not True or key is None:
                    ready = False
                    break
                difference = prior_changes.get(key, 0)
                if difference is None:
                    ready = False
                    break
                delta = _signed_i32(delta + difference)
            count["native_whole_current_soldiers"] = _signed_i32(baseline + delta) if ready else None

    def replace_current(row, *, table_occurrence=False):
        key = _key(row)
        overlay = currents.get(key)
        if overlay is None:
            return
        if table_occurrence:
            row["current_raw_i32"] = overlay.get("current_soldiers")
        else:
            row["current_soldiers"] = overlay.get("current_soldiers")
            row["maximum_soldiers"] = overlay.get("maximum_soldiers")

    for target in inputs.get("target_regiments", []):
        replace_current(target)
    for group in copied_table.get("groups", []):
        for occurrence in group["arrgs"]["occurrences"]:
            replace_current(occurrence, table_occurrence=True)
    for group in inputs.get("groups", []):
        for count in group.get("army_counts", []):
            for regiment in count.get("regiments", []):
                replace_current(regiment)
    for data in _all_data(inputs):
        for record in data.get("records", []):
            overlay = physical.get((record.get("persistent_regiment_id"), record.get("chunk_index")))
            if overlay is None:
                continue
            if overlay.get("status") != "available":
                data["status"] = "unavailable"
                data["unavailable_reason"] = "explicit_stage_physical_input_unavailable"
                continue
            for name in ("current_soldiers", "maximum_soldiers", "state_raw"):
                if name in overlay:
                    record[name] = overlay[name]
            current, maximum = record.get("current_soldiers"), record.get("maximum_soldiers")
            record["effective_current_soldiers"] = maximum if record.get("state_raw") == 3 and current == 0 else current
    prefix = project_current_daily_assault_loss_v1(copied)
    return {**result, "status": prefix["status"], "stage_input_ready": True,
            "stage_group_entry_budgets": entry_budgets,
            "original_current_group_observations": observed,
            "numerical_prefix": prefix,
            "missing_inputs": prefix["missing_inputs"]}
