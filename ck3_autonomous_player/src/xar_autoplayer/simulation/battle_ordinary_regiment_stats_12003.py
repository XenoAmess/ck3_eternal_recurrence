"""Exact .3 ordinary damage from an explicit selected Character stage.

26344C0 -> 30C3BA0 -> 2C15610 consumes aggregate context and a loaded Q64
base. It does not use knight prowess, weighted rows, or the Province operand.
This module neither prepares a person context nor calls native code.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING

from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, _Calculation, from_raw_numeric_inputs_12003,
    native_wrap64_12003,
)

ORDINARY_DAMAGE_BASE_RVA_12003 = "5C69BC0"
ORDINARY_DAMAGE_KEYS_12003 = (0xB0, 0x1B3)
Q_12003 = 100000
if TYPE_CHECKING:
    from .battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003
ORDINARY_STAT_PARAMETERS_12003 = (
    ("siege_raw", "2C15B70", "5C69BD0", 0xB2, 0x1B2),
    ("damage_raw", "2C15610", "5C69BC0", 0xB0, 0x1B3),
    ("toughness_raw", "2C158C0", "5C69BC8", 0xB1, 0x1B4),
    ("pursuit_raw", "2C15E20", "5C69BE0", 0xB3, 0x1B5),
    ("screen_raw", "2C160D0", "5C69BD8", 0xB4, 0x1B6),
)


@dataclass(frozen=True, slots=True)
class OrdinaryDamageStageInputs12003:
    selected_character_full_id: int | None
    stage: str
    context: NativeModifierContext12003 | Mapping[str, object] | None
    loaded_base_damage_raw: int | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class OrdinaryDamageStageResult12003:
    selected_character_full_id: int | None
    stage: str
    damage_raw: int | None
    ready: bool
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_six_stat_getter_ready: bool = False
    actual_game_days_advanced: int = 0


@dataclass(frozen=True, slots=True)
class OrdinarySixStatStageResult12003:
    selected_character_full_id: int | None
    stage: str
    stat_cache: EntrySixStatCache12003 | None
    ready: bool
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_entry_ready: bool = False
    actual_game_days_advanced: int = 0


def calculate_ordinary_six_stat_stage_12003(
    *, selected_character_full_id: int | None, stage: str,
    context: NativeModifierContext12003 | Mapping[str, object] | None,
    loaded_bases: Mapping[str, object] | None,
    source_provenance: Mapping[str, object] | None = None,
) -> OrdinarySixStatStageResult12003:
    """Compute all six ordinary cache values from exact five getter operands."""
    from .battle_first_contact_final_stat_refresh_12003 import (
        EntrySixStatCache12003, knight_effectiveness_fixed_mul_12003,
    )

    calc = _Calculation()
    character = calc.i32(selected_character_full_id, "selected_character_full_id")
    if not isinstance(stage, str) or not stage:
        calc.gap("stage")
    selected = (context if isinstance(context, NativeModifierContext12003)
                else from_raw_numeric_inputs_12003({"context": context}).context)
    bases = loaded_bases if isinstance(loaded_bases, Mapping) else {}
    values, terms = [], []
    for name, getter, base_rva, add_key, mult_key in ORDINARY_STAT_PARAMETERS_12003:
        base = calc.i64(bases.get(name), "loaded_bases." + name)
        add = calc.context_value(selected, add_key, 0)
        mult = calc.context_value(selected, mult_key, 0)
        subtotal = native_wrap64_12003(base + add) if base is not None and add is not None else None
        factor = native_wrap64_12003(Q_12003 + mult) if mult is not None else None
        value = (knight_effectiveness_fixed_mul_12003(subtotal, factor)
                 if subtotal is not None and factor is not None else None)
        values.append(value)
        terms.append({"stat": name, "getter": getter, "base_rva": base_rva,
                      "base_raw": base, "add_key": add_key, "add_raw": add,
                      "mult_key": mult_key, "mult_raw": mult, "result_raw": value})
    ready = not calc.missing
    return OrdinarySixStatStageResult12003(character, stage,
        EntrySixStatCache12003(0, *values) if ready else None, ready, tuple(calc.missing),
        {"source": "26344C0->30C3BA0->five_named_Character_getters", "stage": stage,
         "source_kind": "explicit_named_stage", "getter_terms": tuple(terms),
         "property_lookups": tuple(calc.lookups), "ordinary_max_size_raw": 0,
         "province_operand_used": False, "person_context_prepared": False,
         "historical_stage_observed": False, "source_provenance": deepcopy(source_provenance)})


def ordinary_six_stats_from_combat_regiment_12003(
    regiment: Mapping[str, object], *, source_provenance: Mapping[str, object] | None = None,
) -> OrdinarySixStatStageResult12003:
    """Consume the optional normalized ordinary same-query source leaf."""
    leaf = regiment.get("ordinary_stat_inputs_v1")
    leaf = leaf if isinstance(leaf, Mapping) else {}
    return calculate_ordinary_six_stat_stage_12003(
        selected_character_full_id=leaf.get("selected_character_full_id"),
        stage="frozen_current_ordinary_selected_Character_context",
        context={"aggregate_properties": leaf.get("aggregate_properties")},
        loaded_bases=leaf.get("loaded_bases"), source_provenance=source_provenance)


def ordinary_six_stats_from_person_stage_12003(
    person_stage, *, loaded_bases: Mapping[str, object] | None,
    source_provenance: Mapping[str, object] | None = None,
) -> OrdinarySixStatStageResult12003:
    """Use the existing named PersonStatStage and observed runtime bases."""
    return calculate_ordinary_six_stat_stage_12003(
        selected_character_full_id=person_stage.character_full_id, stage=person_stage.stage,
        context=person_stage.context, loaded_bases=loaded_bases, source_provenance=source_provenance)


def ordinary_six_stats_to_final_stat_input_12003(
    stats: OrdinarySixStatStageResult12003, *, side_index: int, bucket: str,
    bucket_index: int, native_carmy_id: int, regiment_id: int, target_province_id: int,
):
    """Connect source-derived ordinary six stats to the existing final setter."""
    from .battle_first_contact_final_stat_refresh_12003 import FinalEntryStatInput12003, FINAL_SIDE_CALLS_12003
    return FinalEntryStatInput12003(side_index, bucket, bucket_index, native_carmy_id,
        regiment_id, target_province_id, FINAL_SIDE_CALLS_12003[side_index], stats.stat_cache,
        {"source": "ordinary_source_derived_five_getters_plus_max0",
         "selected_character_full_id": stats.selected_character_full_id,
         "stage": stats.stage, "source_ledger": deepcopy(stats.ledger)})


def calculate_ordinary_damage_stage_12003(
    inputs: OrdinaryDamageStageInputs12003,
) -> OrdinaryDamageStageResult12003:
    """Apply the native signed Q64 base/add/mult formula at the named stage."""
    from .battle_first_contact_final_stat_refresh_12003 import (
        knight_effectiveness_fixed_mul_12003,
    )

    calc = _Calculation()
    character = calc.i32(inputs.selected_character_full_id, "selected_character_full_id")
    if not isinstance(inputs.stage, str) or not inputs.stage:
        calc.gap("stage")
    context = (inputs.context if isinstance(inputs.context, NativeModifierContext12003)
               else from_raw_numeric_inputs_12003({"context": inputs.context}).context)
    base = calc.i64(inputs.loaded_base_damage_raw, "loaded_base_damage_raw")
    add = calc.context_value(context, ORDINARY_DAMAGE_KEYS_12003[0], 0)
    mult = calc.context_value(context, ORDINARY_DAMAGE_KEYS_12003[1], 0)
    after_add = (native_wrap64_12003(base + add)
                 if base is not None and add is not None else None)
    factor = native_wrap64_12003(Q_12003 + mult) if mult is not None else None
    value = (knight_effectiveness_fixed_mul_12003(after_add, factor)
             if after_add is not None and factor is not None else None)
    return OrdinaryDamageStageResult12003(
        character, inputs.stage, value if not calc.missing else None,
        not calc.missing, tuple(calc.missing),
        {"source": "26344C0->30C3BA0->2C15610", "loaded_base_rva": ORDINARY_DAMAGE_BASE_RVA_12003,
         "context_source": "selected Character 28C3AE0 aggregate only",
         "stage": inputs.stage, "source_kind": "explicit_named_stage",
         "base_damage_raw": base, "add_key": ORDINARY_DAMAGE_KEYS_12003[0],
         "add_raw": add, "after_add_raw": after_add,
         "mult_key": ORDINARY_DAMAGE_KEYS_12003[1], "mult_raw": mult,
         "factor_raw": factor, "damage_raw": value,
         "property_lookups": tuple(calc.lookups),
         "source_provenance": deepcopy(inputs.source_provenance),
         "remaining_six_stat_sources": ("2C158C0 toughness", "2C15B70 siege", "2C15E20 pursuit", "2C160D0 screen"),
         "negative_or_zero_clamped": False, "province_operand_used": False,
         "person_context_prepared": False, "historical_stage_observed": False})


def ordinary_damage_from_person_raw_numeric_inputs_12003(
    raw_numeric_inputs: Mapping[str, object] | None, *,
    selected_character_full_id: int | None, loaded_base_damage_raw: int | None,
    source_provenance: Mapping[str, object] | None = None,
) -> OrdinaryDamageStageResult12003:
    """Evaluate existing normalized current person operands as frozen current."""
    context = from_raw_numeric_inputs_12003(raw_numeric_inputs).context
    return calculate_ordinary_damage_stage_12003(OrdinaryDamageStageInputs12003(
        selected_character_full_id, "frozen_current_person_context", context,
        loaded_base_damage_raw, source_provenance))


def ordinary_damage_from_person_stage_12003(
    person_stage, *, loaded_base_damage_raw: int | None,
    source_provenance: Mapping[str, object] | None = None,
) -> OrdinaryDamageStageResult12003:
    """Accept the existing explicit PersonStatStage without preparing its context."""
    return calculate_ordinary_damage_stage_12003(OrdinaryDamageStageInputs12003(
        person_stage.character_full_id, person_stage.stage, person_stage.context,
        loaded_base_damage_raw, source_provenance))


def ordinary_damage_to_final_stat_input_12003(
    damage: OrdinaryDamageStageResult12003, *, side_index: int, bucket: str,
    bucket_index: int, native_carmy_id: int, regiment_id: int,
    target_province_id: int, siege_raw: int | None, toughness_raw: int | None,
    pursuit_raw: int | None, screen_raw: int | None,
):
    """Join damage with explicit same-stage remaining getters for final refresh.

    The native ordinary branch has real max_size zero. Missing any of the
    other four operands leaves the six-cache input partial; no target/current
    tuple is silently substituted. The caller supplies occurrence identity.
    """
    from .battle_first_contact_final_stat_refresh_12003 import (
        EntrySixStatCache12003, FinalEntryStatInput12003, FINAL_SIDE_CALLS_12003,
    )

    values = (siege_raw, damage.damage_raw, toughness_raw, pursuit_raw, screen_raw)
    ready = damage.ready and all(type(value) is int for value in values)
    stats = EntrySixStatCache12003(0, *(native_wrap64_12003(value) for value in values)) if ready else None
    return FinalEntryStatInput12003(
        side_index, bucket, bucket_index, native_carmy_id, regiment_id,
        target_province_id, FINAL_SIDE_CALLS_12003[side_index], stats,
        {"source": "ordinary_selected_Character_getter_stage",
         "selected_character_full_id": damage.selected_character_full_id,
         "stage": damage.stage, "damage_ledger": deepcopy(damage.ledger),
         "remaining_four_getters_source": "explicit_same_stage_inputs",
         "full_source_derived_six_stats": False})
