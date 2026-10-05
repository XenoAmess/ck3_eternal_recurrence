"""Current25895A0 term from observed19F and retained eligible opposite amounts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .battle_actual_opposite_effect_eligibility import (
    ActualOppositeEligibilityInputs, adapt_actual_opposite_effect_eligibility,
    evaluate_actual_opposite_effect_eligibility,
)
from .battle_first_contact_final_stat_refresh_12003 import knight_effectiveness_fixed_mul_12003
from .battle_trait_numeric_inputs_12003 import native_wrap64_12003


@dataclass(frozen=True)
class CurrentOwnModifierScope:
    scope: str
    amount_raw: int | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class CurrentOwnModifierSide:
    side_index: int
    selected_character_id_raw: int
    resolved_character_id_raw: int | None
    used_native_fallback: bool | None
    selection_unavailable_reason: str | None
    scopes: tuple[CurrentOwnModifierScope, ...]


@dataclass(frozen=True)
class ActualOwnNestedModifierInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    sides: tuple[CurrentOwnModifierSide, ...]
    opposite: ActualOppositeEligibilityInputs | None


def adapt_actual_own_nested_modifier(diagnostic: Mapping[str, object]) -> ActualOwnNestedModifierInputs | None:
    if diagnostic.get('current_frame_qualified') is not True or diagnostic.get('own_inputs') is None:
        return None
    source, own = diagnostic['source'], diagnostic['own_inputs']
    sides = tuple(CurrentOwnModifierSide(
        side['side_index'], side['selected_character_id_raw'],
        side['selection']['resolved_character_id_raw'], side['selection']['used_native_fallback'],
        side['selection']['unavailable_reason'],
        tuple(CurrentOwnModifierScope(scope, side[scope]['amount_raw'], side[scope]['unavailable_reason'])
              for scope in ('combat_side_aggregate', 'selected_character_aggregate')),
    ) for side in own['sides'])
    opposite = adapt_actual_opposite_effect_eligibility({
        'current_frame_qualified': True, 'source': source,
        'stored_inputs': diagnostic.get('stored_inputs'),
    })
    return ActualOwnNestedModifierInputs(source['combat_id'], source['province_id'],
        source['snapshot_revision'], source['observed_date_raw'], sides, opposite)


def evaluate_actual_own_nested_modifier(inputs: ActualOwnNestedModifierInputs) -> dict[str, object]:
    opposite = evaluate_actual_opposite_effect_eligibility(inputs.opposite) if inputs.opposite is not None else None
    sides = []
    for side in inputs.sides:
        eligibility = opposite['sides'][side.side_index] if opposite is not None else None
        scopes = {}
        for scope in side.scopes:
            total = eligibility['eligible_contribution_sum_raw'] if eligibility is not None else None
            zero = scope.amount_raw == 0
            ready = scope.amount_raw is not None and (zero or total is not None)
            contribution = (0 if zero else knight_effectiveness_fixed_mul_12003(
                native_wrap64_12003(-scope.amount_raw), total)) if ready else None
            reason = (scope.unavailable_reason if scope.amount_raw is None else None if ready
                      else eligibility['unavailable_reason'] if eligibility is not None
                      else 'current_opposite_retained_rows_not_published')
            scopes[scope.scope] = {
                'ready': ready, 'own_modifier_19F_raw': scope.amount_raw,
                'own_aggregate_source': 'actual_Combat_side_plus_110' if scope.scope == 'combat_side_aggregate'
                    else 'actual_native_resolved_selected_Character_28C3AE0',
                'zero_shortcircuit': zero, 'opposite_sum_required': scope.amount_raw is not None and not zero,
                'eligible_opposite_retained_sum_raw': total,
                'nested_contribution_raw': contribution, 'unavailable_reason': reason,
            }
        sides.append({'side_index': side.side_index, 'opposite_side_index': 1 - side.side_index,
            'selected_character_id_raw': side.selected_character_id_raw,
            'resolved_character_id_raw': side.resolved_character_id_raw,
            'used_native_fallback': side.used_native_fallback,
            'selection_unavailable_reason': side.selection_unavailable_reason, **scopes})
    return {'schema_version': 1, 'mode': 'actual_current_own_nested_modifier', 'scale': 100000,
            'modifier_id': 415, 'combat_id': inputs.combat_id, 'province_id': inputs.province_id,
            'snapshot_revision': inputs.snapshot_revision, 'observed_date_raw': inputs.observed_date_raw,
            'ready': all(scope['ready'] for side in sides
                         for scope in (side['combat_side_aggregate'], side['selected_character_aggregate'])),
            'sides': sides, 'opposite_eligibility': opposite,
            'own_amount_source': '2303700_cached_sparse_aggregate_plus_68',
            'product_source': '25895A0_wrap_negation_and_2C4D680_MAX_Q',
            'current_effect_points_used_as_amount': False, 'constructor_clamp_reconstructed': False,
            'future_contact_preview': False, 'complete_forecast_ready': False}
