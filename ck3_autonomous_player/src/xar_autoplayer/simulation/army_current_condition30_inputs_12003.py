"""Pure inverse of the actual current receiver/root verdict; never a refresh replay."""
from __future__ import annotations
from copy import deepcopy

_LIMITS = ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
           'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready')


def _derive(row: dict) -> tuple[bool, int | None]:
    if not row['same_query_army_selection_matched'] or row['army_1d4_raw_u8'] is None:
        return False, None
    if row['army_1d4_raw_u8'] == 0:
        return True, 0
    unit = row['unit_resolution']
    ready = (unit['selected_object_ready'] and unit['object_identity'] is not None
             and row['unit_owner_174_raw_u32'] is not None
             and row['condition_owner_identity'] is not None and row['inline_condition_identity'] is not None
             and row['root_kind'] == 4 and row['root_subtype'] == 0
             and row['root_payload_u64'] == row['unit_owner_174_raw_u32']
             and row['root_construction'] == '9F9E20_normal_return'
             and row['native_current_condition_passed'] is not None)
    return ready, (0 if row['native_current_condition_passed'] else 1) if ready else None


def validate_current_army_condition30_declared_12003(raw: dict) -> None:
    for row in raw['occurrences']:
        ready, value = _derive(row)
        if (row['ready'] != ready or row['current_condition_30_inputs_ready'] != ready
                or row['derived_current_30_raw_u8'] != value):
            raise ValueError('condition30 declared current inverse/readiness disagrees with demanded inputs')
        if row['army_1d4_raw_u8'] == 0 and any(row[f] is not None for f in (
                'army_124_raw_u32', 'unit_owner_174_raw_u32', 'condition_owner_identity',
                'inline_condition_identity', 'root_kind', 'root_subtype', 'root_payload_u64',
                'root_construction', 'native_current_condition_passed')):
            raise ValueError('condition30 zero1D4 branch relabeled undemanded root/evaluation')
    references = raw['original_roster']
    count = references['count_raw_i32']
    rows = raw['occurrences']
    covered = (references['references_ready'] and count is not None and count >= 0 and len(rows) == count)
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row)[0] for row in rows)
    if (raw['raw_roster_references_ready'] != references['references_ready']
            or raw['original_army_selections_ready'] != selected
            or raw['current_condition_30_inputs_ready'] != ready or raw['ready'] != ready):
        raise ValueError('condition30 global readiness disagrees with original occurrences')
    if any(raw[field] for field in _LIMITS):
        raise ValueError('current condition inputs cannot claim actual refresh/later callback readiness')


def project_current_army_condition30_inputs_12003(raw: dict | None, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_army_condition30_inputs',
        'stage': 'observed_current_army_condition30_inputs', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'current_army_condition30_inputs_unavailable',
        'current_condition_30_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance), 'observed_current_army_condition30_inputs': deepcopy(raw),
        'native_calls_executed': 0, 'native_writes_executed': 0, 'actual_post_stage_observed': False,
        'future_tick_ready': False,
        **{field: False for field in _LIMITS},
    }
    if raw is None:
        return result
    validate_current_army_condition30_declared_12003(raw)
    result.update(status=raw['status'], ready=raw['ready'], unavailable_reason=None if raw['ready'] else raw['unavailable_reason'],
                  current_condition_30_inputs_ready=raw['current_condition_30_inputs_ready'])
    for row in raw['occurrences']:
        ready, value = _derive(row)
        result['occurrences'].append({
            'native_index': row['native_index'], 'raw_full_id_u32': row['raw_full_id_u32'],
            'original_army_resolution': deepcopy(row['original_army_resolution']),
            'same_query_army_selection_matched': row['same_query_army_selection_matched'],
            'actual_army_30_raw_u8': row['actual_army_30_raw_u8'],
            'native_current_condition_passed': row['native_current_condition_passed'],
            'ready': ready, 'derived_current_30_raw_u8': value,
            'current_condition_30_inputs_ready': ready,
            'unavailable_reason': None if ready else row['unavailable_reason'],
        })
    return result
