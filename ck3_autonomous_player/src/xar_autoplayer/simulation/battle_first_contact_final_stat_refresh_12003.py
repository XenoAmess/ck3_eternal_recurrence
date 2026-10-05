"""Source-bound Character stage to constructor final Entry cache writes.

Exact .3: 247AB32/41 -> 2651070 -> 2657AC0, special 26344C0 ->
2C06B00/2C06D30. Inputs are explicit conditional stages or current observations;
neither kind is an inferred historical baseline. No native calls are made.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Mapping

from .battle_current_adapter import CurrentBattleCondition
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, _Calculation,
    from_raw_numeric_inputs_12003, native_wrap32_12003, native_wrap64_12003,
)

Q_12003 = 100000
FINAL_SIDE_CALLS_12003 = ("247AB32", "247AB41")


@dataclass(frozen=True, slots=True)
class PersonStatStage12003:
    character_full_id: int | None
    stage: str
    context: NativeModifierContext12003 | Mapping[str, object] | None
    skill_cache_points: tuple[int | None, ...] | None
    carrier_1c0_present: bool | None = None
    carrier_350_raw: int | None = None
    carrier_358_raw: int | None = None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class KnightEffectivenessStage12003:
    selected_character_full_id: int | None
    stage: str
    context: NativeModifierContext12003 | Mapping[str, object] | None
    operand_raw: tuple[int | None, ...] | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class EntrySixStatCache12003:
    effective_max_size: int
    effective_siege_raw: int
    effective_damage_raw: int
    effective_toughness_raw: int
    effective_pursuit_raw: int
    effective_screen_raw: int


@dataclass(frozen=True, slots=True)
class KnightStatStageInputs12003:
    linked_character_full_id: int | None
    linked_prowess_points: int | None
    linked_stage: str
    effectiveness: KnightEffectivenessStage12003
    loaded_damage_multiplier: int | None
    loaded_toughness_multiplier: int | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class KnightStatStageResult12003:
    linked_character_full_id: int | None
    selected_character_full_id: int | None
    stat_cache: EntrySixStatCache12003 | None
    effectiveness_raw: int | None
    ready: bool
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    actual_game_days_advanced: int = 0
    full_entry_ready: bool = False


@dataclass(frozen=True, slots=True)
class FinalEntryStatInput12003:
    side_index: int
    bucket: str
    bucket_index: int
    native_carmy_id: int
    regiment_id: int
    target_province_id: int
    call_site: str
    stat_cache: EntrySixStatCache12003 | None
    source_provenance: Mapping[str, object] | None = None
    knight_character_full_id: int | None = None


@dataclass(frozen=True, slots=True)
class FirstContactFinalStatRefreshResult12003:
    condition: CurrentBattleCondition
    bounded_refresh_ready: bool
    refreshed_entry_count: int
    missing_inputs: tuple[str, ...]
    entry_ledger: tuple[Mapping[str, object], ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    historical_stage_observed: bool = False
    actual_game_days_advanced: int = 0
    full_entry_ready: bool = False


def knight_effectiveness_fixed_mul_12003(a: int, b: int) -> int:
    """2C4D680 signed64 product; large branch decomposes the signed maximum."""
    a, b = native_wrap64_12003(a), native_wrap64_12003(b)
    bound, mask = 3037000499, (1 << 64) - 1

    def trunc_q(value: int) -> int:
        value = native_wrap64_12003(value)
        return -(abs(value) // Q_12003) if value < 0 else value // Q_12003

    if ((a + bound) & mask) <= 2 * bound and ((b + bound) & mask) <= 2 * bound:
        return trunc_q(native_wrap64_12003(a * b))
    minimum, maximum = sorted((a, b))
    quotient = trunc_q(maximum)
    remainder = native_wrap64_12003(
        maximum - native_wrap64_12003(quotient * Q_12003))
    fraction = trunc_q(native_wrap64_12003(remainder * minimum))
    return native_wrap64_12003(
        native_wrap64_12003(quotient * minimum) + fraction)


def _context(value):
    if isinstance(value, NativeModifierContext12003):
        return value
    return from_raw_numeric_inputs_12003(
        {"context": value} if isinstance(value, Mapping) else None).context


def _skill(points, index):
    value = points[index] if isinstance(points, (tuple, list)) and index < len(points) else None
    return native_wrap32_12003(value) if type(value) is int else None


def person_stage_from_chain_projection_12003(
    chain_result, skill_cache_result, *,
    carrier_1c0_present: bool | None,
    carrier_350_raw: int | None = None, carrier_358_raw: int | None = None,
    source_provenance: Mapping[str, object] | None = None,
) -> PersonStatStage12003:
    """Connect an explicit chain frontier and a cache projection of that context.

    The actual chain frontier name is retained even when preparation is partial.
    A cache result must identify the same full Character. Caller provenance must
    describe the cache inputs; this adapter never substitutes a current final
    context or changes a frontier into the constructor's final stage.
    """
    character = chain_result.character_full_id
    points = (skill_cache_result.final_cache_points
              if skill_cache_result.character_id == character else None)
    return PersonStatStage12003(
        character, chain_result.stage, chain_result.context, points,
        carrier_1c0_present, carrier_350_raw, carrier_358_raw,
        {"chain_ready": chain_result.ready,
         "chain_missing_inputs": tuple(chain_result.missing_inputs),
         "chain_source_ledger": deepcopy(chain_result.source_ledger),
         "cache_source_ledger": deepcopy(skill_cache_result.ledger),
         "external_source": deepcopy(source_provenance)})


def effectiveness_from_person_stage_12003(
    selected: PersonStatStage12003,
) -> KnightEffectivenessStage12003:
    if selected.carrier_1c0_present is False:
        carrier = (0, 0)
    elif selected.carrier_1c0_present is True:
        carrier = (selected.carrier_350_raw, selected.carrier_358_raw)
    else:
        carrier = (None, None)
    # C4..C9 read EC,D8,E4,E8,DC,E0, unlike the six-skill storage order.
    operands = tuple(
        None if (point := _skill(selected.skill_cache_points, index)) is None
        else point * Q_12003 for index in (5, 0, 3, 4, 1, 2))
    return KnightEffectivenessStage12003(
        selected.character_full_id, selected.stage, selected.context,
        (Q_12003, *carrier, *operands), selected.source_provenance)


def knight_inputs_from_person_stages_12003(
    linked: PersonStatStage12003, selected: PersonStatStage12003, *,
    loaded_damage_multiplier: int | None,
    loaded_toughness_multiplier: int | None,
    source_provenance: Mapping[str, object] | None = None,
) -> KnightStatStageInputs12003:
    """Selection is a caller-supplied 28BFC70 outcome, separate from prowess."""
    return KnightStatStageInputs12003(
        linked.character_full_id, _skill(linked.skill_cache_points, 5), linked.stage,
        effectiveness_from_person_stage_12003(selected),
        loaded_damage_multiplier, loaded_toughness_multiplier, source_provenance)


def knight_inputs_from_current_observation_12003(
    knights: Mapping[str, object], member: Mapping[str, object], *,
    source_provenance: Mapping[str, object] | None = None,
) -> KnightStatStageInputs12003:
    """Consume the existing normalized combat_v3 knight leaf without new fields."""
    raw = member.get("effectiveness_context")
    raw = raw if isinstance(raw, Mapping) else {}
    modifiers, operands = raw.get("modifier_raw"), raw.get("operand_raw")
    valid_modifiers = isinstance(modifiers, (tuple, list)) and len(modifiers) == 9
    context = NativeModifierContext12003(PropertyContainer12003(
        tuple(range(0xC1, 0xCA)), tuple(modifiers) if valid_modifiers else None,
        9 if valid_modifiers else None))
    return KnightStatStageInputs12003(
        member.get("character_id"), member.get("prowess"),
        "frozen_current_character_values",
        KnightEffectivenessStage12003(
            raw.get("character_id"), "frozen_current_character_values", context,
            tuple(operands) if isinstance(operands, (tuple, list)) else None,
            {"source_kind": "current_effectiveness_context_observation",
             "observation": deepcopy(raw)}),
        knights.get("loaded_damage_multiplier"),
        knights.get("loaded_toughness_multiplier"), source_provenance)


def compute_knight_stat_cache_at_stage_12003(
    inputs: KnightStatStageInputs12003,
) -> KnightStatStageResult12003:
    calc = _Calculation()
    selected = inputs.effectiveness
    if type(inputs.linked_character_full_id) is not int:
        calc.gap("linked_character_full_id")
    if type(selected.selected_character_full_id) is not int:
        calc.gap("selected_character_full_id")
    context, effectiveness, terms = _context(selected.context), Q_12003, []
    for index, key in enumerate(range(0xC1, 0xCA)):
        operand = calc.i64(calc.item(
            selected.operand_raw, index, f"operand_raw[{index}]"), f"operand_raw[{index}]")
        if operand == 0:
            modifier, term, branch = None, 0, "zero_operand_skips_property"
        elif operand is None:
            modifier, term, branch = None, None, "missing_operand"
        else:
            # Reuse the existing exact sparse mode0 reader. Weighted rows are
            # not demanded by this getter and are not manufactured as empty.
            modifier = calc.context_value(context, key, 0)
            term = (None if modifier is None else
                    knight_effectiveness_fixed_mul_12003(modifier, operand))
            branch = "mode0_scaled_property"
        effectiveness = (None if effectiveness is None or term is None else
                         native_wrap64_12003(effectiveness + term))
        terms.append({"key": key, "operand_q64": operand, "modifier_q64": modifier,
                      "term_q64": term, "accumulated_q64": effectiveness, "branch": branch})
    prowess = calc.i32(inputs.linked_prowess_points, "linked_prowess_points")
    damage = calc.i32(inputs.loaded_damage_multiplier, "loaded_damage_multiplier")
    toughness = calc.i32(inputs.loaded_toughness_multiplier, "loaded_toughness_multiplier")
    common = (None if prowess is None or effectiveness is None else
              native_wrap64_12003(max(1, prowess) * effectiveness))
    ready = not calc.missing
    stats = (EntrySixStatCache12003(
        0, 0, native_wrap64_12003(common * damage),
        native_wrap64_12003(common * toughness), 0, 0) if ready else None)
    return KnightStatStageResult12003(
        inputs.linked_character_full_id, selected.selected_character_full_id,
        stats, effectiveness, ready, tuple(calc.missing),
        {"source": "26344C0->2C06D30->28BFC70->2C06B00/2C4D680",
         "linked_stage": inputs.linked_stage, "selected_stage": selected.stage,
         "linked_prowess_points": prowess, "prowess_lower_bound": 1,
         "effectiveness_terms": tuple(terms), "common_wrap64_product": common,
         "loaded_damage_multiplier": damage, "loaded_toughness_multiplier": toughness,
         "property_lookups": tuple(calc.lookups),
         "selected_source": deepcopy(selected.source_provenance),
         "external_source": deepcopy(inputs.source_provenance),
         "province_used_by_special_branch": False, "alive_gate_added": False,
         "constructor_final_stage_inferred": False})


def final_entry_input_from_knight_stage_12003(
    result: KnightStatStageResult12003, *, side_index: int, entry,
    target_province_id: int, source_provenance: Mapping[str, object] | None = None,
) -> FinalEntryStatInput12003:
    return FinalEntryStatInput12003(
        side_index, entry.bucket, entry.bucket_index, entry.native_carmy_id,
        entry.state.regiment_id, target_province_id, FINAL_SIDE_CALLS_12003[side_index],
        result.stat_cache, {"knight_stage": deepcopy(result.ledger),
                           "missing_inputs": result.missing_inputs,
                           "external_source": deepcopy(source_provenance)},
        result.linked_character_full_id)


def apply_first_contact_final_stat_refresh_12003(
    condition: CurrentBattleCondition,
    stat_inputs: tuple[FinalEntryStatInput12003, ...],
) -> FirstContactFinalStatRefreshResult12003:
    """Apply only the supplied endstage six-cache getter outputs in native order.

    Missing rows retain their entering cache and are listed as unrefreshed.
    Count/identity/result accounts and the original observed snapshot are kept.
    This models the final refresh call, not the intervening effect mutations.
    """
    ledger, missing, sides, refreshed = [], [], [], 0
    for side in condition.sides:
        updated = list(side.entries)
        for bucket in ("levy", "men_at_arms"):
            for position, entry in enumerate(side.entries):
                if entry.bucket != bucket:
                    continue
                identity = (side.side_index, bucket, entry.bucket_index,
                            entry.native_carmy_id, entry.state.regiment_id)
                candidates = tuple(row for row in stat_inputs if
                    (row.side_index, row.bucket, row.bucket_index,
                     row.native_carmy_id, row.regiment_id) == identity)
                operand = candidates[0] if len(candidates) == 1 else None
                reason = ("missing_endstage_stats" if not candidates else
                          "ambiguous_endstage_occurrence" if len(candidates) != 1 else
                          "different_combat_province" if operand.target_province_id != condition.province_id else
                          "different_final_side_call" if operand.call_site != FINAL_SIDE_CALLS_12003[side.side_index] else
                          "different_linked_character" if operand.knight_character_full_id is not None and
                          operand.knight_character_full_id != entry.knight_character_id_raw else
                          "partial_stat_calculation" if operand.stat_cache is None else None)
                detail = {"identity": identity, "call_site": FINAL_SIDE_CALLS_12003[side.side_index],
                          "combat_province_id": condition.province_id, "ready": reason is None,
                          "unrefreshed_reason": reason,
                          "source": None if operand is None else deepcopy(operand.source_provenance)}
                if reason is not None:
                    missing.append(f"side{side.side_index}.{bucket}[{entry.bucket_index}].{reason}")
                else:
                    stats = operand.stat_cache
                    source = deepcopy(dict(entry.source_entry))
                    source.update({name: getattr(stats, name) for name in (
                        "effective_max_size", "effective_siege_raw", "effective_damage_raw",
                        "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw")})
                    source["conditional_final_stat_refresh_12003"] = deepcopy(detail)
                    updated[position] = replace(entry,
                        effective_damage_raw=stats.effective_damage_raw,
                        state=replace(entry.state, toughness_raw=stats.effective_toughness_raw,
                                      pursuit_raw=stats.effective_pursuit_raw,
                                      screen_raw=stats.effective_screen_raw),
                        source_entry=source)
                    detail["six_cache_fields"] = vars_six_stats(stats)
                    refreshed += 1
                ledger.append(detail)
        sides.append(replace(side, entries=tuple(updated)))
    return FirstContactFinalStatRefreshResult12003(
        replace(condition, sides=tuple(sides)), not missing, refreshed,
        tuple(missing), tuple(ledger),
        {"source": "247AB32 side0;247AB41 side1->2651070->2657AC0",
         "scope_kind": "caller_supplied_final_six_cache_refresh",
         "combat_province_id": condition.province_id,
         "six_cache_offsets": ("30_i32", "38_q64", "40_q64", "48_q64", "50_q64", "58_q64"),
         "entry_quantities_and_headers_preserved": True,
         "current_final_used_as_prior": False,
         "intervening_effects_evaluated_here": False,
         "full_person_preparation_ready": False})


def vars_six_stats(stats: EntrySixStatCache12003) -> Mapping[str, int]:
    return {name: getattr(stats, name) for name in (
        "effective_max_size", "effective_siege_raw", "effective_damage_raw",
        "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw")}
