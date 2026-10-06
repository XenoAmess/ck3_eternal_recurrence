"""Pure current21 inline-prefix/native shared-tail projection, not a refresh replay."""
from __future__ import annotations
from copy import deepcopy

_LIMITS = ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
           'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready')
_HEADER_FIELDS = ('army_124_raw_u32', 'unit_owner_174_raw_u32', 'owner_character_carrier_1c0_present',
                  'owner_character_carrier_identity', 'header_selection', 'header_identity', 'header_0c_raw_i32')


def _header_ready(row: dict) -> bool:
    character = row['character_resolution']
    if not character['selected_object_ready'] or character['object_identity'] is None:
        return False
    if character['registry_loaded'] is True:
        if not row['unit_resolution']['selected_object_ready'] or row['unit_owner_174_raw_u32'] is None:
            return False
    elif character['registry_loaded'] is not False:
        return False
    carrier = row['owner_character_carrier_1c0_present']
    if carrier is None or row['header_identity'] is None or row['header_0c_raw_i32'] is None:
        return False
    expected = 'carrier_inline' if carrier else 'native_static'
    return row['header_selection'] == expected and (not carrier or row['owner_character_carrier_identity'] is not None)


def _derive(row: dict) -> tuple[bool, int | None]:
    if not row['same_query_army_selection_matched'] or row['army_1ec_raw_u8'] is None:
        return False, None
    if row['army_1ec_raw_u8'] == 0:
        return True, 0
    qword = row['army_1f0_raw_i64']
    if qword is None:
        return False, None
    if qword <= 0:
        if not _header_ready(row):
            return False, None
        if row['header_0c_raw_i32'] == 0:
            return True, 0
    ready = row['native_shared_tail_returned'] and row['native_shared_tail_21_raw_u8'] is not None
    return ready, row['native_shared_tail_21_raw_u8'] if ready else None


def validate_current_army_flag21_declared_12003(raw: dict) -> None:
    for row in raw['occurrences']:
        ready, value = _derive(row)
        if (row['ready'] != ready or row['current_flag21_inputs_ready'] != ready
                or row['derived_current_21_raw_u8'] != value):
            raise ValueError('flag21 declared currentvalue/readiness disagrees with demanded current inputs')
        if row['owner_header_inputs_ready'] != _header_ready(row):
            raise ValueError('flag21 header readiness disagrees with actual source inputs')
        if row['native_shared_tail_returned'] != (row['native_shared_tail_21_raw_u8'] is not None):
            raise ValueError('flag21 actual shared-tail return/value association disagrees')
        no_header = row['army_1ec_raw_u8'] == 0 or (row['army_1f0_raw_i64'] is not None and row['army_1f0_raw_i64'] > 0)
        if no_header and (any(row[f] is not None for f in _HEADER_FIELDS)
                          or row['unit_resolution']['selection'] is not None or row['character_resolution']['selection'] is not None):
            raise ValueError('flag21 sourcezero/positiveQWORD relabeled undemanded owner/header fields')
        source_zero = row['army_1ec_raw_u8'] == 0 or (_header_ready(row) and row['header_0c_raw_i32'] == 0)
        if source_zero and row['native_shared_tail_returned']:
            raise ValueError('flag21 sourcezero relabeled undemanded native call')
        if row['army_1ec_raw_u8'] == 0 and row['army_1f0_raw_i64'] is not None:
            raise ValueError('flag21 zero1EC relabeled undemanded signedQWORD')
    refs, rows = raw['original_roster'], raw['occurrences']
    count = refs['count_raw_i32']
    covered = refs['references_ready'] and count is not None and count >= 0 and len(rows) == count
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row)[0] for row in rows)
    if (raw['raw_roster_references_ready'] != refs['references_ready'] or raw['original_army_selections_ready'] != selected
            or raw['current_flag21_inputs_ready'] != ready or raw['ready'] != ready):
        raise ValueError('flag21 global readiness disagrees with original occurrences')
    if any(raw[field] for field in _LIMITS):
        raise ValueError('current21 cannot claim actual refresh or later callback readiness')


def project_current_army_flag21_inputs_12003(raw: dict | None, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_army_flag21_inputs',
        'stage': 'observed_current_army_flag21_inputs', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'current_army_flag21_inputs_unavailable',
        'current_flag21_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance), 'observed_current_army_flag21_inputs': deepcopy(raw),
        'native_calls_executed': 0, 'native_writes_executed': 0, 'actual_post_stage_observed': False,
        'future_tick_ready': False, **{field: False for field in _LIMITS},
    }
    if raw is None:
        return result
    validate_current_army_flag21_declared_12003(raw)
    result.update(status=raw['status'], ready=raw['ready'], unavailable_reason=None if raw['ready'] else raw['unavailable_reason'],
                  current_flag21_inputs_ready=raw['current_flag21_inputs_ready'])
    for row in raw['occurrences']:
        ready, value = _derive(row)
        result['occurrences'].append({
            **deepcopy(row), 'ready': ready, 'derived_current_21_raw_u8': value,
            'current_flag21_inputs_ready': ready, 'unavailable_reason': None if ready else row['unavailable_reason'],
        })
    return result
