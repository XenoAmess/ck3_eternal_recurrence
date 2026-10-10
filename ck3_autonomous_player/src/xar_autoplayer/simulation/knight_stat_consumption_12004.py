"""Project the PCs actually consumed by the nine native Knight stat operands.

Each Ci retains its own copied PC. The numerical nine-value projection below is
an input adapter, not an invented shared native context or a historical Model.
The observed wrapper output stays separate for an independent comparison.
"""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping

from ..bridge.knight_stat_consumption_contract_12004 import (
    _identity, normalize_knight_stat_consumption_12004,
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


def _modifier_at_consumption(row: Mapping, key: int, *,
                             owned_preparation_pc: Mapping | None = None) -> tuple[object, dict]:
    operand = row["operand_raw"]
    pc = row["consumed_pc"] if owned_preparation_pc is None else owned_preparation_pc
    detail = {
        "property_key": key,
        "operand_raw": operand,
        "selected_character_id": row["selected_character_id"],
        "selected_character_identity": row["selected_character_identity"],
        "context_identity": row["context_identity"],
        "consumed_pc_identity": row["consumed_pc"]["identity"],
        "context_matches_preparation": row["context_matches_preparation"],
        "owner_matches_preparation": row["owner_matches_preparation"],
        "pc_matches_preparation_post": row["pc_matches_preparation_post"],
    }
    if owned_preparation_pc is not None:
        detail["preparation_source_pc_identity"] = owned_preparation_pc["identity"]
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
    return value, {**detail, "branch": ("actual_consumed_pc_mode0" if owned_preparation_pc is None
                                      else "transferred_owned_preparation_pc_mode0"),
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


def _physical_aggregate_pc(copy: Mapping) -> dict | None:
    keys, values = copy["block78_keys"], copy["blocke0_values"]
    count, value_count = keys["raw"]["count_i32"], values["raw"]["count_i32"]
    bits = values["values_q64_raw_bits"]
    ordered_keys = keys["raw"]["keys_u16"]
    model = copy["scope"]["model_identity"]
    if (not keys["payload_copy_complete"] or not values["payload_copy_complete"]
            or not keys["raw"]["key_elements_ready"] or count is None or count < 0
            or count != value_count or ordered_keys is None or bits is None
            or len(ordered_keys) != count or len(bits) != count
            or model == 0 or keys["raw"]["storage_identity"] != model + 0x78
            or values["raw"]["model_identity"] != model
            or values["raw"]["block_identity"] != model + 0xE0
            or (count > 0 and (keys["raw"]["data_identity"] in (None, 0)
                               or values["raw"]["data_identity"] in (None, 0)))):
        return None
    return {
        "ready": True, "admitted": True, "reason": None, "identity": model + 0x78,
        "count_i32": count, "weight_q100000": 0,
        "properties": {"keys_u16": ordered_keys,
                       "values_q64": [item if item < 2**63 else item - 2**64 for item in bits]},
    }


def _transferred_preparation_pc_for_ci(row: Mapping, thread: int) -> tuple[dict | None, dict]:
    proof = {
        "property_key": row["property_key"], "ready": False,
        "prepared_metadata_matches": None, "b_before_to_a_after_payload_equal": None,
        "b_before_matches_retained_preparation_pc": None, "a_after_matches_consumed_pc": None,
        "source": "same_ci_owned_completed_preparation_pc_through_copied_transfer",
        "later_current_query_used": False, "generic_postimages_complete": False,
        "full_person_ready": False, "full_entry_ready": False,
    }
    lineage = row.get("installed_transfer_lineage")
    if not isinstance(lineage, Mapping) or not lineage["installed_identity_associated"]:
        return None, {**proof, "reason": "installed_identity_not_associated"}
    records = lineage.get("capture_at_consumption", {}).get("records", [])
    record = records[0] if records else None
    physical = record.get("physical_postimage") if record is not None else None
    capture = row.get("preparation_capture_at_consumption")
    if not isinstance(physical, Mapping) or not isinstance(capture, Mapping):
        return None, {**proof, "reason": "owned_physical_or_preparation_copy_unavailable"}
    stage, comparison = record["stage"], physical["comparison"]
    before_b = _physical_aggregate_pc(physical["before"]["b"])
    after_a = _physical_aggregate_pc(physical["after"]["a"])
    prepared = capture.get("preparation_model")
    completed = capture.get("post_six_aggregate")
    if before_b is None or after_a is None or prepared is None or completed is None:
        return None, {**proof, "reason": "independent_physical_pc_or_preparation_copy_partial"}
    post = completed["pc"]
    actual = row["consumed_pc"]
    model_b, model_a = stage["model_b_identity"], stage["model_a_identity"]
    descriptor = stage["preparation"]
    selected, full_id = row["selected_character_identity"], row["selected_character_id"]
    metadata = (
        capture["configured"] and capture["historical_capture"] and capture["capture_observed"]
        and capture["capture_complete"] and capture["ready"] and capture["raw_counts_ready"]
        and capture["aggregate_postimage_comparison_ready"] and capture["capture_sequence"] != 0
        and capture["capture_sequence"] == descriptor["preparation_capture_sequence"] == row["preparation_capture_sequence"]
        and _identity(capture["source_return_rva"], "transfer.preparation.source_return_rva") == 0x291CEA9
        and sum(1 << item["index"] for item in capture["stages"] if item["observed"]) == 0x3F
        and prepared["observed"] and prepared["ready"] and prepared["owner_matches_capture"] is True
        and descriptor["observed"] and descriptor["preparation_capture_complete"]
        and model_b != 0 and model_a != 0 and selected not in (None, 0) and full_id is not None
        and capture["character_id"] == full_id == prepared["owner_character_id"] == descriptor["preparation_owner_character_id"]
        and _identity(capture["character_identity"], "transfer.preparation.character") == selected
        == _identity(prepared["owner_character_identity"], "transfer.preparation.owner")
        == descriptor["preparation_character_identity"] == descriptor["preparation_owner_character_identity"]
        and _identity(prepared["model_identity"], "transfer.preparation.model") == descriptor["preparation_model_identity"] == model_b
        and _identity(capture["context_identity"], "transfer.preparation.context") == descriptor["preparation_context_identity"] == model_b + 0x10
        and _identity(post["identity"], "transfer.preparation.pc") == before_b["identity"] == model_b + 0x78
        and row["context_identity"] == model_a + 0x10 and actual["identity"] == after_a["identity"] == model_a + 0x78
        and thread != 0 and capture["capture_thread_id"] == capture["query_thread_id"] == thread
        == descriptor["preparation_capture_thread_id"] == descriptor["preparation_completion_thread_id"]
        and comparison["preparation_descriptor_matches_before_b"] is True
        and comparison["preparation_threads_match_original"] is True)
    proof["prepared_metadata_matches"] = bool(metadata)
    complete = (completed["observed"] and post["ready"] and post["admitted"] is True
                and post["count_i32"] is not None and post["count_i32"] >= 0 and post["properties"] is not None
                and post["properties"]["keys_u16"] is not None and post["properties"]["values_q64"] is not None
                and len(post["properties"]["keys_u16"]) == len(post["properties"]["values_q64"]) == post["count_i32"])
    consumed_complete = (actual["ready"] and actual["admitted"] is True
                         and actual["count_i32"] is not None and actual["count_i32"] >= 0 and actual["properties"] is not None
                         and actual["properties"]["keys_u16"] is not None and actual["properties"]["values_q64"] is not None
                         and len(actual["properties"]["keys_u16"]) == len(actual["properties"]["values_q64"]) == actual["count_i32"])
    proof["b_before_to_a_after_payload_equal"] = (
        before_b["count_i32"] == after_a["count_i32"] and before_b["properties"] == after_a["properties"])
    if complete:
        proof["b_before_matches_retained_preparation_pc"] = (
            before_b["count_i32"] == post["count_i32"] and before_b["properties"] == post["properties"])
    if consumed_complete:
        proof["a_after_matches_consumed_pc"] = (
            after_a["count_i32"] == actual["count_i32"] and after_a["properties"] == actual["properties"])
    ready = (metadata and physical["before"]["configured"] and physical["after"]["configured"]
             and comparison["same_original_observation_ready"] and comparison["original_transfer_returned"]
             and comparison["model_pair_matches_transfer"] and comparison["snapshot_scopes_match_transfer"]
             and comparison["same_clock_and_thread"] is True and comparison["completion_after_begin"] is True
             and comparison["block78_keys"]["a_payload_equals_b_before"] is True
             and comparison["blocke0_values"]["a_payload_equals_b_before"] is True
             and all(proof[field] is True for field in ("b_before_to_a_after_payload_equal",
                    "b_before_matches_retained_preparation_pc", "a_after_matches_consumed_pc")))
    proof.update(ready=bool(ready), record_sequence=record["record_sequence"], capture_sequence=capture["capture_sequence"],
                 preparation_pc_identity=_identity(post["identity"], "transfer.preparation.pc"),
                 b_before_pc_identity=before_b["identity"], a_after_pc_identity=after_a["identity"],
                 consumed_pc_identity=actual["identity"], reason=None if ready else "copied_preparation_transfer_ci_relation_unproven")
    if not ready:
        return None, proof
    # Use the retained preparation's actual completed properties. Its original
    # B PC identity remains separate from the after-A and consumed-Ci copies.
    return {"ready": True, "admitted": True, "reason": None,
            "identity": _identity(post["identity"], "transfer.preparation.pc"), "count_i32": post["count_i32"],
            "properties": post["properties"], "weight_q100000": 0}, proof


def project_consumed_knight_stat_event_12004(event: Mapping) -> dict:
    """Consume one normalized event without equating its nine native contexts."""
    by_key = {row["property_key"]: row for row in event["contexts"]}
    owned_inputs, owned_ledger = _owned_preparation_inputs_at_consumption(event)
    transferred_inputs, transferred_ledger = {}, []
    for row in event["contexts"]:
        lineage = row.get("installed_transfer_lineage")
        records = lineage.get("capture_at_consumption", {}).get("records", []) if isinstance(lineage, Mapping) else []
        if (isinstance(lineage, Mapping) and ("physical_postimage_owned_at_consumption" in lineage
                or any("physical_postimage" in record for record in records))):
            pc, proof = _transferred_preparation_pc_for_ci(row, event["thread_id"])
            transferred_ledger.append(proof)
            if pc is not None and row["property_key"] not in owned_inputs:
                transferred_inputs[row["property_key"]] = pc
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
        elif key in transferred_inputs:
            value, detail = _modifier_at_consumption(row, key, owned_preparation_pc=transferred_inputs[key])
            detail["historical_postimage_selected"] = True
            detail["preparation_capture_source"] = "same_ci_owned_completed_preparation_pc_through_copied_transfer"
            if "preparation_stage_lineage" in row:
                detail["preparation_stage_lineage"] = deepcopy(row["preparation_stage_lineage"])
        else:
            value, detail = _modifier_at_consumption(row, key)
            if "preparation_stage_lineage" in row:
                detail["preparation_stage_lineage"] = deepcopy(row["preparation_stage_lineage"])
                detail["historical_postimage_selected"] = False
        if "installed_transfer_lineage" in row:
            transfer = row["installed_transfer_lineage"]
            detail["installed_transfer_lineage"] = deepcopy(transfer)
            detail["installed_identity_associated"] = (
                transfer is not None and transfer["installed_identity_associated"])
            # The independent preparation/transfer/Ci payload proof selects
            # this row's retained B PC; identity association alone cannot.
            detail["transfer_numeric_postimage_selected"] = key in transferred_inputs
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
    source_stage = ("actual4_consumed_ci_with_owned_transferred_preparation_pc" if transferred_inputs else
                    "actual4_consumed_ci_with_owned_six_stage_postimage" if owned_inputs else _STAGE)
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
    if any("installed_transfer_lineage" in row for row in event["contexts"]):
        associated, transfer_inputs = [], []
        for row in event["contexts"]:
            lineage = row.get("installed_transfer_lineage")
            if lineage is None:
                continue
            if lineage["installed_identity_associated"]:
                associated.append(row["property_key"])
            transfer_inputs.append({
                "property_key": row["property_key"],
                "selected_character_id": row["selected_character_id"],
                "selected_character_identity": row["selected_character_identity"],
                "consumed_context_identity": row["context_identity"],
                "installed_identity_associated": lineage["installed_identity_associated"],
                "lineage": deepcopy(lineage),
            })
        result["installed_transfer_stage_join"] = {
            "associated_property_keys": tuple(associated),
            "unmatched_property_keys": tuple(key for key in _KEYS if key not in associated),
            "property_inputs": tuple(transfer_inputs),
            "source": "same_ci_owned_installed_transfer_before_getter",
            "later_current_query_used": False,
            "generic_postimages_complete": False,
            "numeric_postimage_substitution_performed": bool(transferred_inputs),
            "original_operands_preserved": True,
            "entry_association_inferred": False,
        }
    if transferred_ledger:
        result["installed_transfer_pc_stage_join"] = {
            "historical_property_keys": tuple(key for key in _KEYS if key in transferred_inputs),
            "unmatched_property_keys": tuple(key for key in _KEYS if key not in transferred_inputs),
            "property_inputs": tuple(transferred_ledger),
            "source": "same_ci_owned_completed_preparation_pc_through_copied_transfer",
            "later_current_query_used": False, "original_operands_preserved": True,
            "generic_postimages_complete": False, "full_person_ready": False, "full_entry_ready": False,
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
