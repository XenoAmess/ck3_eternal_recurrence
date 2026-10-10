"""Join an owned historical PC to the actual selected per-Ci stat stage.

Inputs are the already composed Native64 postimage, Native65 owner projection,
and normalized Native66 consumed event with continuation12's derived lineage.
The adapter never composes the PC, repeats a native getter, or changes operands.
Unmatched Ci calls retain their own consumed PC and their original invocation.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass

from .battle_first_contact_final_stat_refresh_12003 import (
    KnightEffectivenessStage12003, KnightStatStageInputs12003,
)
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, _Calculation,
)
from .knight_stat_consumption_12004 import _modifier_at_consumption


_KEYS = tuple(range(0xC1, 0xCA))
_CONSUMED_STAGE = "native_wrapper_consumed_per_ci_contexts"
_JOINED_STAGE = "actual4_consumed_ci_with_owned_six_stage_postimage"


@dataclass(frozen=True, slots=True)
class EntryPersonStatStageJoin12004:
    inputs: KnightStatStageInputs12003
    historical_property_keys: tuple[int, ...]
    unmatched_property_keys: tuple[int, ...]
    property_inputs: tuple[Mapping[str, object], ...]
    source_ledger: Mapping[str, object]
    full_person_ready: bool = False
    full_entry_ready: bool = False
    actual_model_write_performed: bool = False
    actual_game_days_advanced: int = 0


def _identity(value: object) -> int | None:
    # Native64/65 emit hexadecimal identities; consumed records are normalized
    # integers. Preserve their actual value without equating Character and Model.
    if type(value) is int:
        return value
    if type(value) is str and value.startswith(("0x", "0X")):
        return int(value, 16)
    return None


def _selects_supplied_capture(
    row: Mapping, event: Mapping, postimage: Mapping, owner: Mapping,
) -> bool:
    lineage = row.get("preparation_stage_lineage")
    if (not isinstance(lineage, Mapping)
            or lineage.get("completed_preparation_lineage_proven") is not True):
        return False
    # The derived leaf proves the native return's completed capture/stage. This
    # join selects that exact supplied PC/owner, rather than a different capture
    # of the same Character. It does not rederive continuation12's proof.
    sequence = postimage.get("capture_sequence")
    context = _identity(postimage.get("context_identity"))
    selected = row.get("selected_character_id")
    return (
        postimage.get("historical_postimage_ready") is True
        and postimage.get("completion_observation_ready") is True
        and postimage.get("completion_matches_composition") is True
        and owner.get("historical_capture") is True
        and sequence is not None
        and sequence == owner.get("capture_sequence")
        and sequence == row.get("preparation_capture_sequence")
        and context is not None
        and context == _identity(owner.get("context_identity"))
        and context == row.get("preparation_context_identity")
        and context == row.get("context_identity")
        and row.get("preparation_model_identity") == _identity(owner.get("model_identity"))
        and selected is not None
        and selected == postimage.get("character_id")
        and selected == owner.get("owner_character_id")
        and selected == row.get("preparation_owner_character_id")
        and row.get("selected_character_identity") == _identity(owner.get("owner_character_identity"))
        and postimage.get("capture_thread_id") == owner.get("capture_thread_id")
        and postimage.get("capture_thread_id") == event.get("thread_id")
    )


def join_owned_person_postimage_to_knight_stage_12004(
    postimage: Mapping, preparation_owner: Mapping, consumed_event: Mapping,
) -> EntryPersonStatStageJoin12004:
    """Return explicit numerical stage inputs, with each native Ci independent.

    The caller supplies outputs from the existing historical composer/owner
    emitter and the normalized actual consumption family. A missing lineage
    leaves the original per-Ci numerical path usable; it is not a new gate for
    current battle calculations. No full Entry invocation is inferred here.
    """
    historical_context = NativeModifierContext12003(PropertyContainer12003(
        tuple(postimage["keys_u16"]), tuple(postimage["values_q64"]),
        len(postimage["keys_u16"])))
    by_key = {row["property_key"]: row for row in consumed_event["contexts"]}
    modifiers, operands, selected_ids, details, joined, unmatched = [], [], [], [], [], []
    for key in _KEYS:
        row = by_key.get(key)
        if row is None:
            modifiers.append(None)
            operands.append(None)
            selected_ids.append(None)
            unmatched.append(key)
            details.append({"property_key": key, "branch": "native_context_unobserved"})
            continue
        operands.append(row["operand_raw"])
        selected_ids.append(row["selected_character_id"])
        if _selects_supplied_capture(row, consumed_event, postimage, preparation_owner):
            calculation = _Calculation()
            value = (None if row["operand_raw"] == 0 else
                     calculation.context_value(historical_context, key, 0))
            modifiers.append(value)
            joined.append(key)
            details.append({
                "property_key": key,
                "branch": "owned_historical_postimage_selected_at_consumed_ci",
                "operand_raw": row["operand_raw"],
                "lookups": deepcopy(tuple(calculation.lookups)),
                "missing_inputs": tuple(calculation.missing),
                "preparation_stage_lineage": deepcopy(row["preparation_stage_lineage"]),
                "capture_sequence": postimage["capture_sequence"],
                "context_identity": row["context_identity"],
                "model_identity": row["preparation_model_identity"],
                "selected_character_id": row["selected_character_id"],
                "selected_character_identity": row["selected_character_identity"],
            })
        else:
            value, detail = _modifier_at_consumption(row, key)
            modifiers.append(value)
            unmatched.append(key)
            details.append({
                **detail,
                "historical_postimage_selected": False,
                "preparation_stage_lineage": deepcopy(row.get("preparation_stage_lineage")),
            })

    selected_id = (selected_ids[0] if selected_ids[0] is not None
                   and all(value == selected_ids[0] for value in selected_ids) else None)
    stage = _JOINED_STAGE if joined else _CONSUMED_STAGE
    # As in the existing projector, this is a nine-value numerical carrier.
    # It does not assert that a single native PC supplied all nine actual calls.
    numerical_context = NativeModifierContext12003(PropertyContainer12003(
        _KEYS, tuple(modifiers), len(_KEYS)))
    inputs = KnightStatStageInputs12003(
        consumed_event["linked_character_id"], consumed_event["linked_prowess_points"],
        _CONSUMED_STAGE,
        KnightEffectivenessStage12003(
            selected_id, stage, numerical_context, tuple(operands),
            {"source_kind": "owned_historical_and_actual_consumed_ci_inputs",
             "historical_property_keys": tuple(joined),
             "unmatched_property_keys": tuple(unmatched),
             "property_inputs": deepcopy(tuple(details)),
             "shared_native_context_claimed": False}),
        consumed_event["loaded_damage_multiplier"], consumed_event["loaded_toughness_multiplier"],
        {"source_family": "actual4_2c06d10_2c06ae0",
         "capture_sequence": consumed_event["sequence"],
         "origin": consumed_event["origin"],
         "wrapper_caller_return_rva": consumed_event["wrapper_caller_return_rva"],
         "output_cache_identity": consumed_event["output_cache_identity"]})
    return EntryPersonStatStageJoin12004(
        inputs, tuple(joined), tuple(unmatched), tuple(details),
        {"source_family": "actual4_2c06d10_2c06ae0",
         "postimage": deepcopy(postimage),
         "preparation_owner": deepcopy(preparation_owner),
         "consumed_contexts": deepcopy(consumed_event["contexts"]),
         "consumption_sequence": consumed_event["sequence"],
         "origin": consumed_event["origin"],
         "entry_association_proven": consumed_event["entry_association_proven"],
         "physical_entry_writeback": deepcopy(consumed_event.get("physical_entry_writeback")),
         "all_effectiveness_properties_joined": len(joined) == len(_KEYS),
         "original_operands_preserved": True,
         "historical_composition_repeated": False,
         "native_getter_replayed": False,
         "original_entry_invocation_inferred": False})
