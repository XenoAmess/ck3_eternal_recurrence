"""Project the PCs actually consumed by the nine native Knight stat operands.

Each Ci retains its own copied PC. The numerical nine-value projection below is
an input adapter, not an invented shared native context or a historical Model.
The observed wrapper output stays separate for an independent comparison.
"""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping

from ..bridge.knight_stat_consumption_contract_12004 import (
    normalize_knight_stat_consumption_12004,
)
from .battle_first_contact_final_stat_refresh_12003 import (
    KnightEffectivenessStage12003,
    KnightStatStageInputs12003,
    compute_knight_stat_cache_at_stage_12003,
)
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, _Calculation,
)

_KEYS = tuple(range(0xC1, 0xCA))
_CACHE_FIELDS = {
    "max_size": "effective_max_size",
    "siege_value_raw": "effective_siege_raw",
    "damage_raw": "effective_damage_raw",
    "toughness_raw": "effective_toughness_raw",
    "pursuit_raw": "effective_pursuit_raw",
    "screen_raw": "effective_screen_raw",
}
_STAGE = "native_wrapper_consumed_per_ci_contexts"


def _modifier_at_consumption(row: Mapping, key: int) -> tuple[object, dict]:
    operand = row["operand_raw"]
    pc = row["consumed_pc"]
    detail = {
        "property_key": key,
        "operand_raw": operand,
        "selected_character_id": row["selected_character_id"],
        "selected_character_identity": row["selected_character_identity"],
        "context_identity": row["context_identity"],
        "consumed_pc_identity": pc["identity"],
        "context_matches_preparation": row["context_matches_preparation"],
        "owner_matches_preparation": row["owner_matches_preparation"],
        "pc_matches_preparation_post": row["pc_matches_preparation_post"],
    }
    if operand == 0:
        # The existing exact getter's zero operand does not demand a property.
        return None, {**detail, "branch": "zero_operand_skips_property", "lookups": ()}
    block = pc["properties"]
    if not pc["ready"] or block is None:
        return None, {**detail, "branch": "consumed_pc_unavailable",
                      "reason": pc["reason"], "lookups": ()}
    context = NativeModifierContext12003(PropertyContainer12003(
        (None if block["keys_u16"] is None else tuple(block["keys_u16"])),
        (None if block["values_q64"] is None else tuple(block["values_q64"])),
        pc["count_i32"]))
    calculation = _Calculation()
    value = calculation.context_value(context, key, 0)
    return value, {**detail, "branch": "actual_consumed_pc_mode0",
                   "lookups": deepcopy(tuple(calculation.lookups)),
                   "missing_inputs": tuple(calculation.missing)}


def _owned_preparation_inputs_at_consumption(event: Mapping) -> tuple[dict, tuple]:
    """Use only the capture retained at this Ci, with its completed source proof.

    Equal owned copies may share the existing composition/adapter result. A
    Character ID or capture sequence alone cannot select another Ci's capture.
    No subsequent current-model or historical query supplies these inputs.
    """
    eligible = [row for row in event["contexts"]
                if isinstance(row.get("preparation_stage_lineage"), Mapping)
                and row["preparation_stage_lineage"]["completed_preparation_lineage_proven"] is True
                and isinstance(row.get("preparation_capture_at_consumption"), Mapping)]
    if not eligible:
        return {}, ()
    from ..bridge.battle_person_six_stage_capture_12004 import (
        FIELD_NAME, emit_captured_person_preparation_model_12004,
    )
    from .battle_person_six_stage_postimage_12004 import compose_captured_six_stage_postimage_12004
    # The qualified adapter imports _modifier_at_consumption from this module.
    # Import it only after this consumer module is fully initialized.
    from .battle_entry_person_stage_join_12004 import join_owned_person_postimage_to_knight_stage_12004

    cached, overrides, ledger = [], {}, []
    for row in eligible:
        capture = row["preparation_capture_at_consumption"]
        preparation = capture.get("preparation_model")
        if (not capture.get("aggregate_postimage_comparison_ready")
                or preparation is None or not preparation["ready"]):
            continue
        joined = None
        for retained, prior in cached:
            if retained == capture:
                joined = prior
                break
        if joined is None:
            section = {"character_id": capture["character_id"], FIELD_NAME: capture}
            postimage = compose_captured_six_stage_postimage_12004(section)
            owner = emit_captured_person_preparation_model_12004(section)
            joined = join_owned_person_postimage_to_knight_stage_12004(postimage, owner, event)
            cached.append((capture, joined))
            ledger.append({
                "capture_sequence": capture["capture_sequence"],
                "capture_thread_id": capture["capture_thread_id"],
                "completion_thread_id": capture["query_thread_id"],
                "character_id": capture["character_id"],
                "character_identity": capture["character_identity"],
                "context_identity": capture["context_identity"],
                "model_identity": owner["model_identity"],
                "completion_matches_composition": postimage["completion_matches_composition"],
                "source": "same_ci_owned_preparation_capture_at_consumption",
            })
        key = row["property_key"]
        if key not in joined.historical_property_keys:
            continue
        index = key - 0xC1
        detail = deepcopy(joined.property_inputs[index])
        detail["consumed_pc_identity"] = row["consumed_pc"]["identity"]
        detail["preparation_capture_source"] = "same_ci_owned_preparation_capture_at_consumption"
        # Only this row's retained capture authorizes replacement of this Ci.
        overrides[key] = (joined.inputs.effectiveness.context.aggregate_properties.values_q64[index], detail)
    return overrides, tuple(ledger)


def project_consumed_knight_stat_event_12004(event: Mapping) -> dict:
    """Consume one normalized event without equating its nine native contexts."""
    by_key = {row["property_key"]: row for row in event["contexts"]}
    owned_inputs, owned_ledger = _owned_preparation_inputs_at_consumption(event)
    modifiers, operands, details = [], [], []
    selected_ids = []
    for key in _KEYS:
        row = by_key.get(key)
        if row is None:
            modifiers.append(None)
            operands.append(None)
            selected_ids.append(None)
            details.append({"property_key": key, "branch": "native_context_unobserved"})
            continue
        if key in owned_inputs:
            value, detail = owned_inputs[key]
        else:
            value, detail = _modifier_at_consumption(row, key)
            if "preparation_stage_lineage" in row:
                detail["preparation_stage_lineage"] = deepcopy(row["preparation_stage_lineage"])
                detail["historical_postimage_selected"] = False
        modifiers.append(value)
        operands.append(row["operand_raw"])
        selected_ids.append(row["selected_character_id"])
        details.append(detail)

    selected_id = (selected_ids[0] if selected_ids[0] is not None
                   and all(value == selected_ids[0] for value in selected_ids) else None)
    # These are nine resolved numerical operands. This temporary value carrier
    # makes no claim that one native PC supplied every Ci lookup.
    numerical_context = NativeModifierContext12003(PropertyContainer12003(
        _KEYS, tuple(modifiers), len(_KEYS)))
    source_stage = ("actual4_consumed_ci_with_owned_six_stage_postimage" if owned_inputs else _STAGE)
    inputs = KnightStatStageInputs12003(
        event["linked_character_id"], event["linked_prowess_points"], _STAGE,
        KnightEffectivenessStage12003(
            selected_id, source_stage, numerical_context, tuple(operands),
            {"source_kind": "per_ci_consumed_native_pc_projection",
             "consumed_contexts": deepcopy(event["contexts"]),
             "shared_native_context_claimed": False}),
        event["loaded_damage_multiplier"], event["loaded_toughness_multiplier"],
        {"source_family": "actual4_2c06d10_2c06ae0",
         "capture_sequence": event["sequence"],
         "output_cache_identity": event["output_cache_identity"]})
    calculated = compute_knight_stat_cache_at_stage_12003(inputs)
    projected = (None if calculated.stat_cache is None else {
        wire: getattr(calculated.stat_cache, member)
        for wire, member in _CACHE_FIELDS.items()
    })
    observed = deepcopy(event["observed_output"])
    comparison_ready = calculated.ready and observed["ready"]
    field_matches = {field: (projected[field] == observed[field]
                            if comparison_ready else None)
                     for field in _CACHE_FIELDS}
    physical = deepcopy(event.get("physical_entry_writeback"))
    physical_ready = (calculated.ready and physical is not None
                      and physical["entry_cache"]["ready"])
    physical_matches = {
        field: (projected[field] == physical["entry_cache"][field]
                if physical_ready else None)
        for field in _CACHE_FIELDS
    }
    result = {
        "sequence": event["sequence"],
        "thread_id": event["thread_id"],
        "observed_date_raw": event["observed_date_raw"],
        "origin": event["origin"],
        "wrapper_caller_return_rva": event["wrapper_caller_return_rva"],
        "regiment_id": event["regiment_id"],
        "target_province_id": event["target_province_id"],
        "linked_character_id": event["linked_character_id"],
        "linked_character_identity": event["linked_character_identity"],
        "selected_character_ids": tuple(selected_ids),
        "selected_character_id": selected_id,
        "output_cache_identity": event["output_cache_identity"],
        "native_return_identity": event["native_return_identity"],
        "ready": calculated.ready,
        "missing_inputs": tuple(calculated.missing_inputs),
        "source_stage": source_stage,
        "modifier_raw": tuple(modifiers),
        "operand_raw": tuple(operands),
        "property_inputs": tuple(details),
        "consumed_contexts": deepcopy(event["contexts"]),
        "projected_effectiveness_raw": calculated.effectiveness_raw,
        "projected_output": projected,
        "calculation_ledger": deepcopy(calculated.ledger),
        "observed_output": observed,
        "comparison_ready": comparison_ready,
        "field_matches": field_matches,
        "matches_observed_output": (all(field_matches.values()) if comparison_ready else None),
        "physical_entry_writeback": physical,
        "physical_entry_comparison_ready": physical_ready,
        "physical_entry_field_matches": physical_matches,
        "projection_matches_physical_entry_cache": (
            all(physical_matches.values()) if physical_ready else None),
        "wrapper_output_physical_comparison_ready": (
            physical["wrapper_output_comparison_ready"] if physical is not None else False),
        "wrapper_output_matches_physical_entry_cache": (
            physical["wrapper_output_matches_entry_cache"] if physical is not None else None),
        "entry_association_proven": event["entry_association_proven"],
        "historical_stage_equivalence_proven": False,
        "shared_native_context_claimed": False,
        "actual_model_write_performed": False,
        "full_person_ready": False,
        "full_entry_ready": False,
    }
    if any("preparation_stage_lineage" in row or "preparation_capture_at_consumption" in row
           for row in event["contexts"]):
        result["preparation_stage_join"] = {
            "historical_property_keys": tuple(key for key in _KEYS if key in owned_inputs),
            "unmatched_property_keys": tuple(key for key in _KEYS if key not in owned_inputs),
            "owned_capture_compositions": owned_ledger,
            "source": "same_ci_owned_preparation_capture_at_consumption",
            "later_current_query_used": False,
            "original_operands_preserved": True,
            "installed_model_transfer_inferred": False,
            "original_entry_invocation_inferred": False,
        }
    return result


def project_knight_stat_consumption_12004(value: object) -> dict | None:
    """Normalize a whole optional query leaf, then project every retained event."""
    normalized = normalize_knight_stat_consumption_12004(value)
    if normalized is None:
        return None
    return {
        "source_schema": normalized["schema"],
        "build_version": normalized["build_version"],
        "executable_sha256": normalized["executable_sha256"],
        "configured": normalized["configured"],
        "observer_installed": normalized["observer_installed"],
        "oldest_available_sequence": normalized["oldest_available_sequence"],
        "latest_sequence": normalized["latest_sequence"],
        "overwritten_events": normalized["overwritten_events"],
        "reason": normalized["reason"],
        "events": [project_consumed_knight_stat_event_12004(event)
                   for event in normalized["events"]],
        "physical_entry_associated_event_count": sum(
            bool(event["entry_association_proven"]) for event in normalized["events"]),
        "entry_association_proven": any(
            event["entry_association_proven"] for event in normalized["events"]),
        "historical_stage_equivalence_proven": False,
        "actual_model_write_performed": False,
        "full_person_ready": False,
        "full_entry_ready": False,
    }
