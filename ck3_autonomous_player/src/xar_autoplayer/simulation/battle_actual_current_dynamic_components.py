"""Immutable actual component groups with optional direct-total comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CurrentNativeComponent:
    raw: int | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class CurrentSelectedCharacterSource:
    resolved_character_id_raw: int | None
    used_native_fallback: bool | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class CurrentDynamicComponentSide:
    side_index: int
    current_roll_points: int
    selected_character_id_raw: int
    selection: CurrentSelectedCharacterSource
    relation: CurrentNativeComponent
    commander: CurrentNativeComponent
    side_aggregate: CurrentNativeComponent
    observed_direct_total_raw: int | None


@dataclass(frozen=True)
class ActualCurrentDynamicComponentInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    sides: tuple[CurrentDynamicComponentSide, ...]


def _wrap64(value: int) -> int:
    return ((value + (1 << 63)) % (1 << 64)) - (1 << 63)


def adapt_actual_current_dynamic_components(
    diagnostic: Mapping[str, object],
) -> ActualCurrentDynamicComponentInputs | None:
    if diagnostic.get('current_frame_qualified') is not True:
        return None
    current = diagnostic.get('current_inputs')
    if current is None:
        return None
    source = diagnostic['source']
    direct = diagnostic.get('direct_inputs')
    sides = []
    for index, row in enumerate(current['sides']):
        selected = row['selection']
        def component(name, key='total_raw'):
            value = row[name]
            return CurrentNativeComponent(value[key], value['unavailable_reason'])
        sides.append(CurrentDynamicComponentSide(
            row['side_index'], row['current_roll_points'], row['selected_character_id_raw'],
            CurrentSelectedCharacterSource(selected['resolved_character_id_raw'],
                                           selected['used_native_fallback'], selected['unavailable_reason']),
            component('relation', 'kind_raw'), component('commander'), component('side_aggregate'),
            direct['sides'][index]['side_dynamic_total_raw'] if direct is not None else None,
        ))
    return ActualCurrentDynamicComponentInputs(
        source['combat_id'], source['province_id'], source['snapshot_revision'],
        source['observed_date_raw'], tuple(sides),
    )


def evaluate_actual_current_dynamic_components(
    inputs: ActualCurrentDynamicComponentInputs,
) -> dict[str, object]:
    sides = []
    for side in inputs.sides:
        ready = side.commander.raw is not None and side.side_aggregate.raw is not None
        total = _wrap64(side.current_roll_points * 100000 + side.commander.raw + side.side_aggregate.raw) if ready else None
        comparable = ready and side.observed_direct_total_raw is not None
        def component(value):
            return {'ready': value.raw is not None, 'raw': value.raw,
                    'unavailable_reason': value.unavailable_reason}
        sides.append({
            'side_index': side.side_index, 'role': 'attacker' if side.side_index == 0 else 'defender',
            'ready': ready, 'current_roll_points': side.current_roll_points,
            'selected_character_id_raw': side.selected_character_id_raw,
            'selection': {'ready': side.selection.resolved_character_id_raw is not None,
                          'resolved_character_id_raw': side.selection.resolved_character_id_raw,
                          'used_native_fallback': side.selection.used_native_fallback,
                          'unavailable_reason': side.selection.unavailable_reason},
            'relation': component(side.relation), 'commander': component(side.commander),
            'side_aggregate': component(side.side_aggregate),
            'side_total_from_components_raw': total,
            'observed_direct_total_raw': side.observed_direct_total_raw,
            'matches_observed_direct_total': total == side.observed_direct_total_raw if comparable else None,
            'components_minus_direct_raw': _wrap64(total - side.observed_direct_total_raw) if comparable else None,
        })
    return {
        'schema_version': 1, 'mode': 'actual_current_combat_native_dynamic_components',
        'ready': all(side['ready'] for side in sides), 'scale': 100000,
        'combat_id': inputs.combat_id, 'province_id': inputs.province_id,
        'snapshot_revision': inputs.snapshot_revision, 'observed_date_raw': inputs.observed_date_raw,
        'sides': sides, 'relation_source': 'actual_combat_2589810',
        'selected_source': 'actual_combat_94_3DC_generation_5C67568_fallback_5C67570',
        'commander_source': 'actual_selected_character_2589E10_null_explanation',
        'side_aggregate_source': 'actual_combat_side_110_25899C0_null_explanation',
        'commander_includes_selected_character_relation_aggregate': True,
        'fine_source_rows_ready': False, 'nested_opposite_19F_eligibility_published': False,
        'native_state_refreshed': False, 'future_contact_preview': False, 'complete_forecast_ready': False,
    }
