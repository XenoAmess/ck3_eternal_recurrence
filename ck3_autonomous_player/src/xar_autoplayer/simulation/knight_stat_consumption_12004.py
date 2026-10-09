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


def project_consumed_knight_stat_event_12004(event: Mapping) -> dict:
    """Consume one normalized event without equating its nine native contexts."""
    by_key = {row["property_key"]: row for row in event["contexts"]}
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
        value, detail = _modifier_at_consumption(row, key)
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
    inputs = KnightStatStageInputs12003(
        event["linked_character_id"], event["linked_prowess_points"], _STAGE,
        KnightEffectivenessStage12003(
            selected_id, _STAGE, numerical_context, tuple(operands),
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
    return {
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
        "source_stage": _STAGE,
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
        "entry_association_proven": False,
        "historical_stage_equivalence_proven": False,
        "shared_native_context_claimed": False,
        "actual_model_write_performed": False,
        "full_person_ready": False,
        "full_entry_ready": False,
    }


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
        "entry_association_proven": False,
        "historical_stage_equivalence_proven": False,
        "actual_model_write_performed": False,
        "full_person_ready": False,
        "full_entry_ready": False,
    }
