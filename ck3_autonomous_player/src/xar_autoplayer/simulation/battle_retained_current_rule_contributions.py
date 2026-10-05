"""Pure current-context contributions, qualified separately by native source."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .battle_retained_constructor_geometry import CurrentLoadedRetainedRuleEffect
from .combat_core import trunc_div_toward_zero, wrap_int64


def _append_fixed_mul_2586c90(left_raw: int, right_raw: int) -> int:
    """Exact inline MAX/Q slow branch, shared source with 2C4D680.

    Reuses the closed algorithm of knight_effectiveness_fixed_mul_12003 in the
    parallel final-stat module; the generic MIN/Q helper has different rounding.
    """
    if -3037000499 <= left_raw <= 3037000499 and -3037000499 <= right_raw <= 3037000499:
        return wrap_int64(trunc_div_toward_zero(wrap_int64(left_raw * right_raw), 100000))
    minimum, maximum = sorted((left_raw, right_raw))
    integral = trunc_div_toward_zero(maximum, 100000)
    remainder = wrap_int64(maximum - wrap_int64(integral * 100000))
    fractional = trunc_div_toward_zero(wrap_int64(remainder * minimum), 100000)
    return wrap_int64(wrap_int64(integral * minimum) + fractional)


@dataclass(frozen=True, slots=True)
class CurrentRetainedRuleContributionInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    holding_defender: bool
    effects: tuple[CurrentLoadedRetainedRuleEffect, ...]
    holding_status: str
    province_multiplier_raw: int | None
    province_has_holding: bool | None
    holding_modifier_raw: int | None
    commander_status: str
    selected_character_id_raw: int
    used_native_fallback: bool | None
    defender_adjacency_excluded: bool | None


@dataclass(frozen=True, slots=True)
class CurrentRetainedRuleContribution:
    stage: str
    side_index: int
    ready: bool
    selected: bool | None
    applied: bool | None
    effect_key: str | None
    effect_advantage_points: int | None
    multiplier_raw: int | None
    signed_contribution_raw: int | None
    missing_input: str | None


def adapt_current_retained_rule_contributions(diagnostic: Mapping[str, object]):
    if diagnostic.get('current_rule_context_frame_qualified') is not True:
        return None
    context = diagnostic.get('current_rule_context')
    if context is None:
        return None
    source = diagnostic['source']
    loaded = diagnostic['current_loaded_rule_effects']
    holding, commander = context['holding_multiplier'], context['commander_exclusion']
    return CurrentRetainedRuleContributionInputs(
        combat_id=source['combat_id'], province_id=source['province_id'],
        snapshot_revision=source['snapshot_revision'], observed_date_raw=source['observed_date_raw'],
        holding_defender=diagnostic['holding_defender'],
        effects=tuple(CurrentLoadedRetainedRuleEffect(
            stage=row['stage'], side_index=row['side_index'], rules_pointer_offset=row['rules_pointer_offset'],
            status=row['status'], key=row['key'], advantage_points=row['advantage_points'],
        ) for row in (loaded['rows'] if loaded else ())),
        holding_status=holding['status'], province_multiplier_raw=holding['province_multiplier_raw'],
        province_has_holding=holding['province_has_holding'], holding_modifier_raw=holding['holding_modifier_raw'],
        commander_status=commander['status'], selected_character_id_raw=commander['selected_character_id_raw'],
        used_native_fallback=commander['used_native_fallback'], defender_adjacency_excluded=commander['defender_adjacency_excluded'],
    )


def evaluate_current_retained_rule_contributions(inputs: CurrentRetainedRuleContributionInputs):
    effects = {row.stage: row for row in inputs.effects}
    holding_multiplier = None
    if inputs.holding_status == 'available':
        holding_multiplier = wrap_int64(inputs.province_multiplier_raw +
            (inputs.holding_modifier_raw if inputs.province_has_holding else 0))
    rows = []
    for stage, side in (('attacker_adjacency', 0), ('defender_adjacency', 1), ('holding_defender', 1)):
        effect = effects.get(stage)
        ready, selected, applied, multiplier, contribution, missing = True, None, None, None, None, None
        if stage == 'holding_defender' and not inputs.holding_defender:
            selected, applied, contribution = False, False, 0
        elif stage == 'holding_defender' and holding_multiplier is None:
            ready, missing = False, 'current_holding_multiplier'
        elif stage == 'holding_defender' and holding_multiplier <= 0:
            selected, applied, multiplier, contribution = True, False, holding_multiplier, 0
        elif effect is None or effect.status == 'unavailable':
            ready, missing = False, 'current_loaded_'+stage+'_effect'
        elif effect.status == 'not_selected':
            selected, applied, contribution = False, False, 0
        elif stage == 'defender_adjacency' and inputs.commander_status != 'available':
            selected, ready, missing = True, False, 'current_selected_attacker_commander_flag_1A4'
        else:
            selected = True
            applied = stage != 'defender_adjacency' or not inputs.defender_adjacency_excluded
            multiplier = holding_multiplier if stage == 'holding_defender' else 100000
            unsigned = _append_fixed_mul_2586c90(effect.advantage_points * 100000, multiplier) if applied else 0
            contribution = unsigned if side == 0 else wrap_int64(-unsigned)
        rows.append(CurrentRetainedRuleContribution(
            stage=stage, side_index=side, ready=ready, selected=selected, applied=applied,
            effect_key=effect.key if effect else None,
            effect_advantage_points=effect.advantage_points if effect else None,
            multiplier_raw=multiplier, signed_contribution_raw=contribution, missing_input=missing,
        ))
    return {'schema_version': 1, 'mode': 'actual_current_context_retained_rule_contributions',
            'ready': all(row.ready for row in rows), 'scale': 100000,
            'combat_id': inputs.combat_id, 'province_id': inputs.province_id,
            'snapshot_revision': inputs.snapshot_revision, 'observed_date_raw': inputs.observed_date_raw,
            'current_holding_multiplier_raw': holding_multiplier,
            'selected_attacker_character_id_raw': inputs.selected_character_id_raw,
            'selected_attacker_used_native_fallback': inputs.used_native_fallback,
            'rows': [asdict(row) for row in rows], 'complete_advantage_ready': False,
            'historical_constructor_append_observed': False}
