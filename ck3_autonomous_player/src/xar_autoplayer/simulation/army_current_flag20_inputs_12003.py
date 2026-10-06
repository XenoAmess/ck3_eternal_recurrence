"""Source-zero/native current Army20 projection; never a changed-stage replay."""
from __future__ import annotations
from copy import deepcopy

_LIMITS = ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
           'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready')


def _derive(row: dict) -> tuple[bool, int | None]:
    if not row['same_query_army_selection_matched'] or row['army_1d4_raw_u8'] is None:
        return False, None
    if row['army_1d4_raw_u8'] == 0:
        return True, 0
    if not row['native_getter_returned'] or row['native_getter_20_raw_u8'] is None:
        return False, None
    return True, row['native_getter_20_raw_u8']


def validate_current_army_flag20_declared_12003(raw: dict) -> None:
    for row in raw['occurrences']:
        ready, value = _derive(row)
        if (row['ready'] != ready or row['current_flag20_inputs_ready'] != ready
                or row['derived_current_20_raw_u8'] != value):
            raise ValueError('flag20 declared current value/readiness disagrees with actual demanded getter')
        if row['native_getter_returned'] != (row['native_getter_20_raw_u8'] is not None):
            raise ValueError('flag20 actual getter return/value association disagrees')
        if row['army_1d4_raw_u8'] == 0 and (row['native_getter_returned'] or row['native_getter_20_raw_u8'] is not None):
            raise ValueError('flag20 zero1D4 branch relabeled undemanded native call')
    refs = raw['original_roster']
    count = refs['count_raw_i32']
    rows = raw['occurrences']
    covered = (refs['references_ready'] and count is not None and count >= 0 and len(rows) == count)
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row)[0] for row in rows)
    if (raw['raw_roster_references_ready'] != refs['references_ready']
            or raw['original_army_selections_ready'] != selected
            or raw['current_flag20_inputs_ready'] != ready or raw['ready'] != ready):
        raise ValueError('flag20 global readiness disagrees with original occurrences')
    if any(raw[field] for field in _LIMITS):
        raise ValueError('current flag20 cannot claim actual refresh or later callback readiness')


def project_current_army_flag20_inputs_12003(raw: dict | None, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_army_flag20_inputs',
        'stage': 'observed_current_army_flag20_inputs', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'current_army_flag20_inputs_unavailable',
        'current_flag20_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance), 'observed_current_army_flag20_inputs': deepcopy(raw),
        'native_calls_executed': 0, 'native_writes_executed': 0, 'actual_post_stage_observed': False,
        'future_tick_ready': False, **{field: False for field in _LIMITS},
    }
    if raw is None:
        return result
    validate_current_army_flag20_declared_12003(raw)
    result.update(status=raw['status'], ready=raw['ready'], unavailable_reason=None if raw['ready'] else raw['unavailable_reason'],
                  current_flag20_inputs_ready=raw['current_flag20_inputs_ready'])
    for row in raw['occurrences']:
        ready, value = _derive(row)
        result['occurrences'].append({
            'native_index': row['native_index'], 'raw_full_id_u32': row['raw_full_id_u32'],
            'original_army_resolution': deepcopy(row['original_army_resolution']),
            'same_query_army_selection_matched': row['same_query_army_selection_matched'],
            'actual_army_20_raw_u8': row['actual_army_20_raw_u8'], 'army_1d4_raw_u8': row['army_1d4_raw_u8'],
            'native_getter_returned': row['native_getter_returned'], 'native_getter_20_raw_u8': row['native_getter_20_raw_u8'],
            'derived_current_20_raw_u8': value, 'ready': ready, 'current_flag20_inputs_ready': ready,
            'unavailable_reason': None if ready else row['unavailable_reason'],
        })
    return result
