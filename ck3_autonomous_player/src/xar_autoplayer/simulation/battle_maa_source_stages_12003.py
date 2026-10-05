"""Exact .3 MAA source-shaped baseline stages, independent of person prep."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING

from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, _Calculation, from_raw_numeric_inputs_12003,
    native_wrap32_12003, native_wrap64_12003,
)
from .battle_maa_regiment_stats_12003 import (
    MaaModifierScratch12003, MaaSixStatStageResult12003,
    _cache_values, apply_maa_six_stat_modifiers_12003,
    maa_modifier_scratch_from_person_stage_12003,
)

if TYPE_CHECKING:
    from .battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003, PersonStatStage12003

Q_12003 = 100000
EXTRA_GENERIC_KEYS_12003 = ((0x1C9, 0x1CA), (0x1C1, 0x1C2),
    (0x1C3, 0x1C4), (0x1C5, 0x1C6), (0x1C7, 0x1C8))


@dataclass(frozen=True, slots=True)
class MaaCultureContribution12003:
    definition_is_gdbo: bool | None
    definition_matches_selected_type: bool | None
    class_filter: int | None
    stats: EntrySixStatCache12003 | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class MaaExtraSourceStage12003:
    stage: str
    context: NativeModifierContext12003 | Mapping[str, object] | None
    holder_piety_rank: int | None
    class_add_keys_u16: tuple[int, ...] | None
    class_mult_keys_u16: tuple[int, ...] | None
    source_provenance: Mapping[str, object] | None = None


def add_maa_culture_contributions_12003(
    type_base: EntrySixStatCache12003 | None, *, selected_type_class: int | None,
    government_rows: tuple[MaaCultureContribution12003, ...] | None,
    global_rows: tuple[MaaCultureContribution12003, ...] | None, stage: str,
) -> MaaSixStatStageResult12003:
    """2551090 then2551290: add every actual admitted row, in source order."""
    from .battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003

    calc = _Calculation()
    selected_class = calc.i32(selected_type_class, "selected_type_class")
    if not isinstance(stage, str) or not stage:
        calc.gap("stage")
    outputs = _cache_values(calc, type_base, "type_base")
    terms = []
    for group, rows in (("government", government_rows), ("global", global_rows)):
        if not isinstance(rows, tuple):
            calc.gap(group + "_rows")
            continue
        for index, row in enumerate(rows):
            path = group + "_rows[" + str(index) + "]"
            if not isinstance(row, MaaCultureContribution12003):
                calc.gap(path)
                continue
            if type(row.definition_is_gdbo) is not bool:
                calc.gap(path + ".definition_is_gdbo")
                continue
            if row.definition_is_gdbo:
                if type(row.definition_matches_selected_type) is not bool:
                    calc.gap(path + ".definition_matches_selected_type")
                    continue
                if not row.definition_matches_selected_type:
                    terms.append({"group": group, "row_index": index, "status": "native_type_mismatch"})
                    continue
            class_filter = calc.i32(row.class_filter, path + ".class_filter")
            if class_filter is None or selected_class is None:
                continue
            if class_filter != -1 and class_filter != selected_class:
                terms.append({"group": group, "row_index": index, "status": "native_class_mismatch"})
                continue
            values = _cache_values(calc, row.stats, path + ".stats")
            for stat_index, value in enumerate(values):
                outputs[stat_index] = ((native_wrap32_12003 if stat_index == 0 else native_wrap64_12003)(outputs[stat_index] + value)
                    if outputs[stat_index] is not None and value is not None else None)
            terms.append({"group": group, "row_index": index, "status": "native_admitted",
                "values": tuple(values), "source_provenance": deepcopy(row.source_provenance)})
    ready = not calc.missing
    return MaaSixStatStageResult12003(stage, EntrySixStatCache12003(*outputs) if ready else None,
        ready, tuple(calc.missing), {"source": "30C3C50->2551090/2551290", "terms": tuple(terms),
            "selected_type_class": selected_class, "source_kind": "actual_loaded_type_and_callback_rows"})


def _extra_scratch(
    selected: MaaModifierScratch12003, extra: MaaExtraSourceStage12003 | None,
    *, class_row_present: bool | None,
) -> MaaModifierScratch12003:
    """30C2F80/30C3460 extra source operands; absent class does not read extra."""
    from .battle_first_contact_final_stat_refresh_12003 import knight_effectiveness_fixed_mul_12003

    calc = _Calculation()
    if class_row_present is False:
        return MaaModifierScratch12003(selected.selected_character_full_id, selected.stage,
            (0,) * 6, (Q_12003,) * 6, True, (), {"source": "30C2F80", "status": "native_class_absent_skip"})
    if class_row_present is not True:
        calc.gap("class_row_present")
    context = (extra.context if extra and isinstance(extra.context, NativeModifierContext12003)
               else from_raw_numeric_inputs_12003({"context": extra.context if extra else None}).context)
    if extra is None or not isinstance(extra.stage, str) or not extra.stage:
        calc.gap("extra.stage")
    rank = calc.i32(extra.holder_piety_rank if extra else None, "extra.holder_piety_rank")
    adds, factors, terms = [0], [Q_12003], []
    for index, (add_key, mult_key) in enumerate(EXTRA_GENERIC_KEYS_12003):
        add = calc.context_value(context, add_key, 0)
        mult = calc.context_value(context, mult_key, 0)
        dynamic = []
        for label, keys in (("add", extra.class_add_keys_u16 if extra else None),
                            ("mult", extra.class_mult_keys_u16 if extra else None)):
            key = calc.item(keys, index, "extra.class_" + label + "_keys_u16")
            if type(key) is not int:
                calc.gap("extra.class_" + label + "_keys_u16[" + str(index) + "]")
                dynamic.append(None)
            else:
                dynamic.append(calc.context_value(context, key & 0xFFFF, 0))
        rank_term = 0
        if index in (1, 2):
            key = 0x1CB if index == 1 else 0x1CC
            # 2C4D680 returns zero before sparse lookup for operand zero.
            if rank == 0:
                rank_term = 0
            else:
                value = calc.context_value(context, key, 0)
                rank_term = (knight_effectiveness_fixed_mul_12003(value, native_wrap64_12003(rank * Q_12003))
                             if value is not None and rank is not None else None)
        total_add = native_wrap64_12003(add + dynamic[0]) if add is not None and dynamic[0] is not None else None
        factor = (native_wrap64_12003(native_wrap64_12003(Q_12003 + mult + dynamic[1]) + rank_term)
                  if mult is not None and dynamic[1] is not None and rank_term is not None else None)
        adds.append(total_add)
        factors.append(factor)
        terms.append({"index": index + 1, "generic_add_key": add_key, "generic_mult_key": mult_key,
                      "rank_term_q64": rank_term, "add_q64": total_add, "factor_q64": factor})
    ready = not calc.missing
    return MaaModifierScratch12003(selected.selected_character_full_id,
        extra.stage if extra else selected.stage, tuple(adds) if ready else None,
        tuple(factors) if ready else None, ready, tuple(calc.missing),
        {"source": "30C2F80/30C3460", "terms": tuple(terms), "extra_holder_piety_rank": rank,
         "source_provenance": deepcopy(extra.source_provenance) if extra else None})


def construct_maa_baseline_stage_12003(
    culture_stage: MaaSixStatStageResult12003, *, person_stage: PersonStatStage12003,
    class_row_present: bool | None,
    class_add_keys_u16: tuple[int, ...] | None,
    class_mult_keys_u16: tuple[int, ...] | None,
    extra_source: MaaExtraSourceStage12003 | None,
    selector_mode: bool | None,
    selected_government_byte_4d6: int | None,
    selected_script_value_4e_q64: int | None, stage: str,
) -> MaaSixStatStageResult12003:
    """30C3C50 combined context/extra apply, then optional five-factor apply."""
    calc = _Calculation()
    selected = maa_modifier_scratch_from_person_stage_12003(person_stage,
        class_row_present=class_row_present, class_add_keys_u16=class_add_keys_u16,
        class_mult_keys_u16=class_mult_keys_u16)
    extra = _extra_scratch(selected, extra_source, class_row_present=class_row_present)
    for prefix, result in (("culture_stage", culture_stage), ("selected", selected), ("extra", extra)):
        if not result.ready:
            calc.gap(prefix + ".ready")
        for gap in result.missing_inputs:
            calc.gap(prefix + "." + gap)
    combined_adds, combined_factors = [], []
    for index in range(6):
        add = calc.item(selected.add_q64, index, "selected.add_q64")
        extra_add = calc.item(extra.add_q64, index, "extra.add_q64")
        factor = calc.item(selected.factor_q64, index, "selected.factor_q64")
        extra_factor = calc.item(extra.factor_q64, index, "extra.factor_q64")
        combined_adds.append(native_wrap64_12003(add + extra_add) if add is not None and extra_add is not None else None)
        combined_factors.append(native_wrap64_12003(factor + extra_factor - Q_12003)
                                if factor is not None and extra_factor is not None else None)
    combined = MaaModifierScratch12003(selected.selected_character_full_id, person_stage.stage,
        tuple(combined_adds) if not calc.missing else None, tuple(combined_factors) if not calc.missing else None,
        not calc.missing, tuple(calc.missing), {"source": "30C3C50 single combined scratch apply",
            "selected_ledger": deepcopy(selected.ledger), "extra_ledger": deepcopy(extra.ledger)})
    applied = apply_maa_six_stat_modifiers_12003(culture_stage.stat_cache, combined,
        stage=stage + ".combined_context_extra_apply")
    if type(selector_mode) is not bool:
        calc.gap("selector_mode")
    selector_factor = Q_12003
    if selector_mode is True:
        tag = calc.i32(selected_government_byte_4d6, "selected_government_byte_4d6")
        if tag == 5:
            raw = calc.i64(selected_script_value_4e_q64, "selected_script_value_4e_q64")
            selector_factor = max(0, raw) if raw is not None else None
    if selector_mode is True and selector_factor != Q_12003:
        selector_scratch = MaaModifierScratch12003(selected.selected_character_full_id, person_stage.stage,
            (0,) * 6, (Q_12003,) + (selector_factor,) * 5 if selector_factor is not None else None,
            selector_factor is not None, (), {"source": "30C3670", "max_factor_unchanged": True})
        applied = apply_maa_six_stat_modifiers_12003(applied.stat_cache, selector_scratch,
            stage=stage + ".selector_five_factor_apply")
    for gap in applied.missing_inputs:
        calc.gap(gap)
    if not isinstance(stage, str) or not stage:
        calc.gap("stage")
    ready = not calc.missing and applied.ready
    return MaaSixStatStageResult12003(stage, applied.stat_cache if ready else None,
        ready, tuple(calc.missing), {"source": "30C3C50 baseline source stages",
            "culture_ledger": deepcopy(culture_stage.ledger), "apply_ledger": deepcopy(applied.ledger),
            "selected_character_stage": person_stage.stage, "extra_stage": extra.stage,
            "selector_mode": selector_mode, "selector_factor_q64": selector_factor,
            "person_preparation_performed": False, "historical_stage_observed": False})


def apply_maa_accolade_aggregate_stage_12003(
    baseline: MaaSixStatStageResult12003, *, accolade_person_stage: PersonStatStage12003,
    class_row_present: bool | None, class_add_keys_u16: tuple[int, ...] | None,
    class_mult_keys_u16: tuple[int, ...] | None, stage: str,
) -> MaaSixStatStageResult12003:
    """30C4360 aggregate context apply after the completed baseline stage."""
    scratch = maa_modifier_scratch_from_person_stage_12003(accolade_person_stage,
        class_row_present=class_row_present, class_add_keys_u16=class_add_keys_u16,
        class_mult_keys_u16=class_mult_keys_u16)
    result = apply_maa_six_stat_modifiers_12003(baseline.stat_cache, scratch, stage=stage)
    return MaaSixStatStageResult12003(stage, result.stat_cache if baseline.ready else None,
        baseline.ready and result.ready, baseline.missing_inputs + result.missing_inputs,
        {"source": "30C4360->30C2860->2647B60", "baseline_ledger": deepcopy(baseline.ledger),
         "accolade_ledger": deepcopy(result.ledger)})
