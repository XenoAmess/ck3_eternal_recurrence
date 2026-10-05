"""Closed .3 MAA context/apply/end-stage arithmetic on named real operands.

This module does not construct the 30C3C50 baseline or a person context. The
caller supplies the exact intermediate stage and actual environment vectors.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING

from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, _Calculation, _trunc_q,
    from_raw_numeric_inputs_12003, native_wrap32_12003, native_wrap64_12003,
)

if TYPE_CHECKING:
    from .battle_first_contact_final_stat_refresh_12003 import (
        EntrySixStatCache12003, FinalEntryStatInput12003, PersonStatStage12003,
    )

Q_12003 = 100000
MAA_GENERIC_KEYS_12003 = (
    (0xFFFF, ()), (0x1BF, (0x1C0, 0x1B2)),
    (0x1B7, (0x1B8, 0x1B3)), (0x1B9, (0x1BA, 0x1B4)),
    (0x1BB, (0x1BC, 0x1B5)), (0x1BD, (0x1BE, 0x1B6)),
)
MAA_ENVIRONMENT_ORDER_12003 = (
    "type_terrain", "type_definition", "type_province",
    "linked_terrain", "linked_definition", "linked_province",
)
_CACHE_FIELDS = (
    "effective_max_size", "effective_siege_raw", "effective_damage_raw",
    "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw",
)


@dataclass(frozen=True, slots=True)
class MaaModifierScratch12003:
    selected_character_full_id: int | None
    stage: str
    add_q64: tuple[int, ...] | None
    factor_q64: tuple[int, ...] | None
    ready: bool
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class MaaSixStatStageResult12003:
    stage: str
    stat_cache: EntrySixStatCache12003 | None
    ready: bool
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_getter_construction_ready: bool = False
    full_entry_ready: bool = False
    actual_game_days_advanced: int = 0


def maa_modifier_scratch_from_person_stage_12003(
    person_stage: PersonStatStage12003, *, class_row_present: bool | None,
    class_add_keys_u16: tuple[int, ...] | None = None,
    class_mult_keys_u16: tuple[int, ...] | None = None,
    source_provenance: Mapping[str, object] | None = None,
) -> MaaModifierScratch12003:
    """30C2860/30C2D40 aggregate values for the actual selected class row.

    An observed absent class row is native zero; an unknown row is a gap.
    The six key tuples are the loaded row words, not inferred from class names.
    """
    calc = _Calculation()
    character = calc.i32(person_stage.character_full_id, "selected_character_full_id")
    if not isinstance(person_stage.stage, str) or not person_stage.stage:
        calc.gap("stage")
    if type(class_row_present) is not bool:
        calc.gap("class_row_present")
    context = (person_stage.context if isinstance(person_stage.context, NativeModifierContext12003)
               else from_raw_numeric_inputs_12003({"context": person_stage.context}).context)
    adds, factors, terms = [], [], []
    for index, (generic_add, generic_mults) in enumerate(MAA_GENERIC_KEYS_12003):
        add = calc.context_value(context, generic_add, 0)
        mult_values = [calc.context_value(context, key, 0) for key in generic_mults]
        class_add, class_mult = 0, 0
        if class_row_present is True:
            class_values = []
            for label, keys in (("add", class_add_keys_u16), ("mult", class_mult_keys_u16)):
                key = calc.item(keys, index, "class_" + label + "_keys_u16")
                if type(key) is not int:
                    calc.gap("class_" + label + "_keys_u16[" + str(index) + "]")
                    class_values.append(None)
                else:
                    class_values.append(calc.context_value(context, key & 0xFFFF, 0))
            class_add, class_mult = class_values
        total_add = native_wrap64_12003(add + class_add) if add is not None and class_add is not None else None
        total_factor = Q_12003
        for value in (*mult_values, class_mult):
            total_factor = (native_wrap64_12003(total_factor + value)
                            if total_factor is not None and value is not None else None)
        adds.append(total_add)
        factors.append(total_factor)
        terms.append({"index": index, "generic_add_key": generic_add,
                      "generic_mult_keys": generic_mults,
                      "add_q64": total_add, "factor_q64": total_factor})
    ready = not calc.missing
    return MaaModifierScratch12003(character, person_stage.stage,
        tuple(adds) if ready else None, tuple(factors) if ready else None,
        ready, tuple(calc.missing), {"source": "30C2860/30C2D40",
            "class_row_present": class_row_present, "terms": tuple(terms),
            "property_lookups": tuple(calc.lookups), "person_context_prepared": False,
            "source_provenance": deepcopy(source_provenance)})


def _cache_values(calc: _Calculation, cache: EntrySixStatCache12003 | None, path: str):
    values = []
    for index, name in enumerate(_CACHE_FIELDS):
        raw = getattr(cache, name, None)
        values.append((calc.i32 if index == 0 else calc.i64)(raw, path + "." + name))
    return values


def apply_maa_six_stat_modifiers_12003(
    base_stage: EntrySixStatCache12003 | None, scratch: MaaModifierScratch12003,
    *, stage: str,
) -> MaaSixStatStageResult12003:
    """2647B60/2647CA0 apply; max_size uses two Q divisions and low32."""
    from .battle_first_contact_final_stat_refresh_12003 import (
        EntrySixStatCache12003, knight_effectiveness_fixed_mul_12003,
    )

    calc = _Calculation()
    for gap in scratch.missing_inputs:
        calc.gap("scratch." + gap)
    if not scratch.ready:
        calc.gap("scratch.ready")
    if not isinstance(stage, str) or not stage:
        calc.gap("stage")
    base_values = _cache_values(calc, base_stage, "base_stage")
    outputs, terms = [], []
    for index, base in enumerate(base_values):
        add = calc.i64(calc.item(scratch.add_q64, index, "scratch.add_q64"), "scratch.add_q64[" + str(index) + "]")
        factor = calc.i64(calc.item(scratch.factor_q64, index, "scratch.factor_q64"), "scratch.factor_q64[" + str(index) + "]")
        subtotal = (native_wrap64_12003((base * Q_12003 if index == 0 else base) + add)
                    if base is not None and add is not None else None)
        value = (knight_effectiveness_fixed_mul_12003(subtotal, factor)
                 if subtotal is not None and factor is not None else None)
        if index == 0 and value is not None:
            value = native_wrap32_12003(_trunc_q(value))
        outputs.append(value)
        terms.append({"index": index, "base": base, "subtotal_q64": subtotal,
                      "factor_q64": factor, "output": value})
    ready = not calc.missing
    return MaaSixStatStageResult12003(stage,
        EntrySixStatCache12003(*outputs) if ready else None, ready, tuple(calc.missing),
        {"source": "2647B60/2647CA0", "base_stage_source": "explicit_intermediate_operands",
         "scratch_stage": scratch.stage, "terms": tuple(terms),
         "scratch_ledger": deepcopy(scratch.ledger), "damage_toughness_floor_applied": False})


def finish_maa_environment_stage_12003(
    base_after_modifiers: MaaSixStatStageResult12003, *, stage: str,
    definition620_present: bool | None,
    components: Mapping[str, EntrySixStatCache12003 | None],
    source_province_id: int | None,
    linked_character_full_ids: tuple[int, ...] | None,
    source_provenance: Mapping[str, object] | None = None,
) -> MaaSixStatStageResult12003:
    """30C4360 ordered environment adds and final MAA damage/toughness floor.

    The baseline must be the actual stage after Character/+120/selector-mode
    and accolade modifiers. Each component is an actual returned six-vector;
    missing required vectors stay gaps, while a false guard skips both terms.
    """
    from .battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003

    calc = _Calculation()
    if not isinstance(stage, str) or not stage:
        calc.gap("stage")
    province = calc.i32(source_province_id, "source_province_id")
    if type(definition620_present) is not bool:
        calc.gap("definition620_present")
    if not isinstance(linked_character_full_ids, tuple):
        calc.gap("linked_character_full_ids")
    else:
        for index, value in enumerate(linked_character_full_ids):
            calc.i32(value, "linked_character_full_ids[" + str(index) + "]")
    if not base_after_modifiers.ready:
        calc.gap("base_after_modifiers.ready")
        for gap in base_after_modifiers.missing_inputs:
            calc.gap("base_after_modifiers." + gap)
    outputs = _cache_values(calc, base_after_modifiers.stat_cache, "base_after_modifiers")
    terms = []
    for name in MAA_ENVIRONMENT_ORDER_12003:
        if name in ("type_definition", "linked_definition") and definition620_present is False:
            terms.append({"component": name, "status": "native_guard_skipped"})
            continue
        values = _cache_values(calc, components.get(name), "components." + name)
        for index, value in enumerate(values):
            outputs[index] = ((native_wrap32_12003 if index == 0 else native_wrap64_12003)(outputs[index] + value)
                              if outputs[index] is not None and value is not None else None)
        terms.append({"component": name, "values": tuple(values), "after_add": tuple(outputs)})
    before_floor = tuple(outputs)
    for index in (2, 3):
        if outputs[index] is not None:
            outputs[index] = max(Q_12003, outputs[index])
    ready = not calc.missing
    return MaaSixStatStageResult12003(stage,
        EntrySixStatCache12003(*outputs) if ready else None, ready, tuple(calc.missing),
        {"source": "30C4360 environment end stage", "base_stage": base_after_modifiers.stage,
         "base_ledger": deepcopy(base_after_modifiers.ledger), "source_province_id": province,
         "linked_character_full_ids": linked_character_full_ids, "terms": tuple(terms),
         "before_damage_toughness_floor": before_floor,
         "source_provenance": deepcopy(source_provenance), "historical_stage_observed": False})


def maa_six_stats_to_final_stat_input_12003(
    stats: MaaSixStatStageResult12003, *, side_index: int, bucket_index: int,
    native_carmy_id: int, regiment_id: int, target_province_id: int,
) -> FinalEntryStatInput12003:
    """Connect a complete conditional MAA getter stage to the final setter API."""
    from .battle_first_contact_final_stat_refresh_12003 import FinalEntryStatInput12003, FINAL_SIDE_CALLS_12003

    return FinalEntryStatInput12003(side_index, "men_at_arms", bucket_index, native_carmy_id,
        regiment_id, target_province_id, FINAL_SIDE_CALLS_12003[side_index], stats.stat_cache,
        {"source": "explicit_MAA_closed_arithmetic_stage", "stage": stats.stage,
         "source_ledger": deepcopy(stats.ledger), "full_getter_construction_ready": stats.full_getter_construction_ready})
