"""Selected refill through finite monthly effects in fixed captured context."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from .army_associated_refill_current_projection import project_conditional_associated_refill_current
from .army_monthly_loss_budget_projection import construct_conditional_monthly_loss_budgets
from .army_monthly_caller_effect_projection import project_conditional_monthly_caller_effects
from .army_post_refill_land_supply_rate_projection import project_conditional_post_refill_land_supply_rate


def _i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _selected_union(army: Mapping[str, object]) -> tuple[dict, dict, list]:
    candidates: dict[int, list[Mapping]] = {}
    source_data = army.get("regiment_replenishment_records_v1")
    if isinstance(source_data, list):
        for row in source_data:
            candidates.setdefault(row["army_regiment_id"], []).append(row)
    province = army.get("current_province_supply_contributors_v1")
    if isinstance(province, Mapping):
        for occurrence in province["occurrences"]:
            if occurrence["included"] is not True:
                continue
            for row in occurrence["regiments"]:
                data = row["replenishment_records_v1"]
                if row["native_supply_loss_eligible"] is True and data is not None:
                    candidates.setdefault(row["army_regiment_id"], []).append(data)
    selected = {}
    missing = []
    for identity, aliases in candidates.items():
        complete = [row for row in aliases if row["status"] == "available"]
        snapshot = complete[0] if complete else aliases[0]
        if any(row != snapshot for row in complete[1:]):
            missing.append({"army_regiment_id": identity,
                            "inputs": ["consistent_same_physical_ArRg_DATA"]})
            continue
        selected[identity] = snapshot
    union = project_conditional_associated_refill_current({
        "status": "available", "army_id": army.get("army_id"),
        "regiment_replenishment_records_v1": list(selected.values()),
        "regiment_strengths": [{"army_regiment_id": identity} for identity in selected],
    })
    return union, selected, missing


def _subject_frame(army: Mapping[str, object], union: Mapping, selected: Mapping) -> tuple[dict, dict]:
    frame = deepcopy(dict(army))
    source_rows = army.get("regiment_strengths")
    rows = source_rows if isinstance(source_rows, list) else []
    refreshes = {row["army_regiment_id"]: row for row in union["regiment_refreshes"]}
    physical = {(row["persistent_regiment_id"], row["chunk_index"]): row
                for row in union["physical_chunks"] if row["status"] == "available"}
    derived_rows, derived_data, missing = [], [], []
    counts = {flags: 0 for flags in range(4)}
    ready = {flags: isinstance(source_rows, list) for flags in range(4)}
    all_current_ready = isinstance(source_rows, list)
    for observed in rows:
        identity = observed["army_regiment_id"]
        refresh = refreshes.get(identity)
        current_ready = refresh is not None and refresh["current_maximum_ready"]
        row = deepcopy(observed)
        row.update(current_soldiers=refresh["current_soldiers"] if current_ready else None,
                   maximum_soldiers=refresh["maximum_soldiers"] if current_ready else None)
        derived_rows.append(row)
        if not current_ready:
            all_current_ready = False
            missing.append({"army_regiment_id": identity,
                            "inputs": refresh["missing_inputs"] if refresh else ["selected_subject_DATA_refresh"]})
        for flags in range(4):
            tier_known = row.get("siege_tier_observable") is True
            eligible = row.get("native_supply_loss_eligible")
            if (flags & 1 and tier_known and row["siege_tier"] > 0
                    or flags & 2 and eligible is False):
                continue
            if (flags & 1 and not tier_known or flags & 2 and type(eligible) is not bool
                    or not current_ready):
                ready[flags] = False
            else:
                counts[flags] = _i32(counts[flags] + row["current_soldiers"])
        snapshot = selected.get(identity)
        if snapshot is None:
            continue
        data = deepcopy(snapshot)
        data["source"] = "derived_selected_refill_DATA"
        for record in data["records"]:
            key = (record["persistent_regiment_id"], record["chunk_index"])
            change = physical.get(key)
            if change is None:
                record.update(status="unavailable",
                              unavailable_reason="selected_refill_physical_current_unavailable",
                              current_soldiers=None, maximum_soldiers=None,
                              effective_current_soldiers=None)
                if data.get("native_loss_writer_skipped") is not True:
                    data.update(status="partial", ready=False,
                                unavailable_reason="selected_refill_physical_DATA_partial")
            else:
                current, maximum = change["current_soldiers"], change["maximum_soldiers"]
                record.update(current_soldiers=current, maximum_soldiers=maximum,
                              effective_current_soldiers=maximum if record["state_raw"] == 3 and current == 0 else current)
        derived_data.append(data)
    # Unknown selected current must never leak initial rows into the automatic
    # loss sequence. Independent eligible counts/budget branches still survive.
    frame["regiment_strengths"] = derived_rows if all_current_ready else None
    frame["regiment_replenishment_records_v1"] = derived_data
    frame["current_soldiers"] = counts[0] if ready[0] else None
    frame["maximum_soldiers"] = (_i32(sum(row["maximum_soldiers"] for row in derived_rows))
                                if all_current_ready else None)
    losses = dict(army.get("loss_application_inputs_v1") or {})
    fields = ("whole_soldiers", "definition_le_zero_soldiers", "supply_eligible_soldiers",
              "definition_le_zero_supply_eligible_soldiers")
    for flags, name in enumerate(fields):
        losses[name] = counts[flags] if ready[flags] else None
    frame["loss_application_inputs_v1"] = losses
    return frame, {
        "input_basis": "derived_selected_refill_physical_DATA_and_source_current_maximum_refresh",
        "current_maximum_ready": all_current_ready,
        "regiment_strengths": derived_rows, "DATA": derived_data,
        "count_by_native_flags": {str(flags): counts[flags] if ready[flags] else None for flags in range(4)},
        "count_ready_by_native_flags": {str(flags): ready[flags] for flags in range(4)},
        "missing_inputs": missing,
    }


def _label_sequence(sequence: dict | None) -> None:
    if sequence is None:
        return
    sequence["input_basis"] = "derived_selected_refill_rate_stock_budget_and_loss_subsystem"
    sequence["initial_state_basis"] = "derived_selected_refill_DATA_and_ArRg_current_maximum"
    for stage in sequence.get("passes", []):
        stage["input_basis"] = "derived_selected_refill_or_prior_writer_stage"
        for request in stage.get("requests", []):
            writer = request.get("conditional_chunk_writeback")
            if isinstance(writer, dict):
                writer["input_basis"] = "derived_same_stage_DATA_and_explicit_writer_request"


def project_selected_refill_monthly_supply_assembly_v1(
    army: Mapping[str, object], *, joined_land_rate: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Join qualified kernels without replacing any observed row or output.

    Capacity and all owner/Province/commander/admission/modifier predicates are
    explicit captured context. This does not reconstruct manager preparation,
    calendar entry, other refresh statistics or an actual post-stage snapshot.
    """
    result = {
        "projection_kind": "conditional_selected_refill_monthly_supply_assembly",
        "source_contract_game_version": "1.20.0.3", "army_id": army.get("army_id"),
        "native_carmy_id": army.get("native_carmy_id"),
        "status": "unavailable", "conditional_assembly_ready": False,
        "input_basis": "one_selected_core_invocation_per_observed_persistent_cache_in_fixed_captured_context",
        "captured_context_premise": ["owner", "current_Province_and_occurrence_order", "commander",
                                     "admission_and_supply_eligibility", "loaded_modifiers_and_capacity"],
        "capacity_input_basis": "observed_current_capacity_held_in_explicit_fixed_captured_context",
        "observed_supply_stock_raw": army.get("current_supply_raw"),
        "observed_supply_capacity_raw": army.get("current_supply_capacity_raw"),
        "observed_monthly_rate_raw": army.get("current_supply_change_monthly_raw"),
        "selected_refill_union": None, "derived_subject_frame": None,
        "joined_post_refill_land_rate": None, "rate_required_by_updater": None,
        "selected_land_rate_ready": False, "selected_land_rate_raw": None,
        "conditional_post_stock_ready": False, "conditional_post_stock_raw": None,
        "conditional_budgets_ready": False, "conditional_loss_sequence_ready": False,
        "conditional_caller_effects_ready": False,
        "conditional_physical_refill_ready": False, "conditional_physical_loss_ready": False,
        "monthly_loss_budgets": None, "monthly_caller_effects": None, "missing_inputs": [],
        "scale": 100000, "soldiers_scale": 1,
        "actual_replenishment": False, "actual_loss": False, "actual_effects": False,
        "actual_post_stage_current": None, "actual_post_supply_usage_soldiers": None,
        "full_regular_refill_ready": False, "full_monthly_ready": False,
    }
    if army.get("status") != "available":
        result["missing_inputs"] = ["available_same_query_strength"]
        return result
    union, selected, union_missing = _selected_union(army)
    frame, subject = _subject_frame(army, union, selected)
    land = (deepcopy(dict(joined_land_rate)) if joined_land_rate is not None
            else project_conditional_post_refill_land_supply_rate(army))
    rate_ready = land["conditional_full_land_rate_ready"]
    rate = land["conditional_post_refill_supply_rate_raw"] if rate_ready else None
    frame["current_supply_change_monthly_raw"] = rate
    budgets = construct_conditional_monthly_loss_budgets(frame)
    budgets["input_basis"] = "derived_selected_refill_current_DATA_counts_and_land_rate; fixed_captured_capacity_and_context"
    sequence = budgets["same_input_conditional_loss_sequence_v1"]
    _label_sequence(sequence)
    effects = project_conditional_monthly_caller_effects(frame, budgets)
    effects["input_basis"] = "derived_selected_refill_budget_and_loss_sequence_with_captured_date_and_counter_cells"
    required = budgets["supply_updater_admitted"] is not False
    missing = list(subject["missing_inputs"])
    missing.extend(union_missing)
    if required and not rate_ready:
        missing.append({"stage": "selected_full_land_rate", "inputs": land["missing_inputs"]})
    for stage, projection in (("stock_and_budgets", budgets), ("finite_caller_effects", effects)):
        if projection["missing_inputs"]:
            missing.append({"stage": stage, "inputs": projection["missing_inputs"]})
    sequence_ready = sequence is not None and sequence["conditional_sequence_ready"]
    if sequence is not None and not sequence_ready:
        missing.append({"stage": "derived_four_pass_loss_sequence", "inputs": sequence["missing_inputs"]})
    ready = (budgets["post_supply_ready"] and budgets["conditional_budgets_ready"]
             and sequence_ready and effects["conditional_caller_effects_ready"])
    any_ready = (subject["current_maximum_ready"] or rate_ready or budgets["admission_ready"]
                 or any(budgets[f"{prefix}_budget_ready"] for prefix in ("supply", "siege", "raid")))
    return {
        **result, "status": "available" if ready else "partial" if any_ready else "unavailable",
        "conditional_assembly_ready": bool(ready), "selected_refill_union": union,
        "derived_subject_frame": subject, "joined_post_refill_land_rate": land,
        "rate_required_by_updater": required, "selected_land_rate_ready": rate_ready,
        "selected_land_rate_raw": rate, "conditional_post_stock_ready": budgets["post_supply_ready"],
        "conditional_post_stock_raw": budgets["conditional_post_supply_raw"],
        "conditional_budgets_ready": budgets["conditional_budgets_ready"],
        "conditional_loss_sequence_ready": bool(sequence_ready),
        "conditional_caller_effects_ready": effects["conditional_caller_effects_ready"],
        "conditional_physical_refill_ready": union["associated_chunks_ready"],
        "conditional_physical_loss_ready": sequence["conditional_physical_chunks_ready"] if sequence else False,
        "monthly_loss_budgets": budgets, "monthly_caller_effects": effects, "missing_inputs": missing,
    }


def project_selected_refill_monthly_assemblies_v1(
    armies: Sequence[Mapping[str, object]], *, joined_land_rates: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rates = {row["army_id"]: row for row in joined_land_rates}
    return [project_selected_refill_monthly_supply_assembly_v1(
        army, joined_land_rate=rates.get(army.get("army_id"))) for army in armies]
