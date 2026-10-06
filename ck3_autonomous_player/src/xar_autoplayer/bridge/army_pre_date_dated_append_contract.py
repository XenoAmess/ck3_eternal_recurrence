"""Strict raw .3 dated append family; preserve partial and unused operands."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import _typed as _existing_typed, _resolution
from ..simulation.army_pre_date_dated_append_12003 import project_pre_date_dated_append_12003

_SHAPES = {
    'IdList': {'ready': 'bool', 'unavailable_reason': 'string', 'source': 'string',
               'count_raw_i32': 'i32?', 'ordered_ids_u32': 'u32?[]?'},
    'Date': {'native_index': 'i32', 'pointer_identity': 'string?', 'pointer_present': 'bool?',
             'date_low_raw_i32': 'i32?'},
    'Occurrence': {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string',
                   'native_index': 'i32', 'original_request_full_id_u32': 'u32?',
                   'army_resolution': 'OperandResolution', 'combat_request_full_id_u32': 'u32?',
                   'combat_resolution': 'OperandResolution', 'combat_magic_0c_raw_u32': 'u32?',
                   'army_date_count_5c_raw_i32': 'i32?', 'date_array_identity': 'string?',
                   'date_array_present': 'bool?', 'date_entries': 'Date[]', 'date_scan_ready': 'bool'},
    'Inputs': {'schema_version': 'i32', 'source': 'string', 'stage': 'string', 'status': 'string',
               'ready': 'bool', 'unavailable_reason': 'string', 'manager_loaded': 'bool',
               'manager_identity': 'string?', 'clock_source': 'string', 'clock_ready': 'bool',
               'current_date_raw_i32': 'i32?', 'tomorrow_date_low_i32': 'i32?',
               'source_c8': 'IdList', 'initial_158': 'IdList', 'occurrences': 'Occurrence[]'},
}


def _typed(value, kind, name):
    if kind.endswith('?'):
        if value is None:
            return
        kind = kind[:-1]
    if kind.endswith('[]'):
        if type(value) is not list:
            raise ValueError(f'{name} must retain its native array')
        for index, row in enumerate(value):
            _typed(row, kind[:-2], f'{name}[{index}]')
    elif kind in _SHAPES:
        if type(value) is not dict or set(value) != set(_SHAPES[kind]):
            raise ValueError(f'{name} schema is malformed')
        for key, field in _SHAPES[kind].items():
            _typed(value[key], field, name + '.' + key)
    else:
        _existing_typed(value, kind, name)


def _ready(value, ready, name, *, status=False):
    if value['ready'] != ready or bool(value['unavailable_reason']) == ready:
        raise ValueError(f'{name} readiness disagrees with observed operands')
    if status and (value['status'] not in {'available', 'partial', 'unavailable'} or
                   (value['status'] == 'available') != ready):
        raise ValueError(f'{name} status disagrees with readiness')


def _id_list(raw, name, *, source=False):
    count, ids = raw['count_raw_i32'], raw['ordered_ids_u32']
    if raw['source'] not in {'not_demanded', 'same_query_first_removal_id_list', 'native_manager_id_list'}:
        raise ValueError(f'{name} reuse source is malformed')
    # Partial reuse can retain a differently sized list. It is never upgraded
    # to complete by rescanning or by interpreting a declared ready flag.
    complete = (count is not None and ids is not None and (count >= 0 or source) and
                len(ids) == max(count, 0) and all(value is not None for value in ids))
    _ready(raw, complete, name)


def normalize_current_pre_date_dated_append_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_pre_date_dated_append_inputs_v1'
    _typed(value, 'Inputs', name)
    if (value['schema_version'] != 1 or value['source'] != 'native_current_pre_date_dated_append_inputs' or
            value['stage'] != 'observed_current_2a9a360_tomorrow_operands'):
        raise ValueError(f'{name} source stage is malformed')
    if value['manager_loaded'] and value['manager_identity'] is None:
        raise ValueError(f'{name} manager identity is unobserved')
    _id_list(value['source_c8'], name + '.source_c8', source=True)
    _id_list(value['initial_158'], name + '.initial_158')
    if value['clock_source'] not in {'unavailable', 'same_query_army_update_clock_v1', 'same_query_game_state_08'}:
        raise ValueError(f'{name} clock source is malformed')
    projected = project_pre_date_dated_append_12003(value)
    if (value['clock_ready'] != projected['clock_ready'] or
            value['tomorrow_date_low_i32'] != projected['tomorrow_date_low_i32'] or
            value['clock_ready'] != (value['clock_source'] != 'unavailable')):
        raise ValueError(f'{name} native tomorrow operand is malformed')
    count, ids = value['source_c8']['count_raw_i32'], value['source_c8']['ordered_ids_u32']
    expected = max(count, 0) if count is not None else 0
    if len(value['occurrences']) != expected:
        raise ValueError(f'{name} source occurrence count is malformed')
    for index, (raw, decision) in enumerate(zip(value['occurrences'], projected['occurrences'])):
        if raw['native_index'] != index or raw['original_request_full_id_u32'] != (
                ids[index] if ids is not None and index < len(ids) else None):
            raise ValueError(f'{name} lost original source order/full IDs')
        _resolution(raw['army_resolution'], raw['original_request_full_id_u32'], name + '.army_resolution')
        _resolution(raw['combat_resolution'], raw['combat_request_full_id_u32'], name + '.combat_resolution')
        _ready(raw, decision['ready'], name + '.occurrence', status=True)
        dates = raw['date_entries']
        if any(date['native_index'] != ordinal for ordinal, date in enumerate(dates)):
            raise ValueError(f'{name} date scan order is malformed')
        native_count = raw['army_date_count_5c_raw_i32']
        if dates and (native_count is None or len(dates) > max(native_count, 0)):
            raise ValueError(f'{name} date scan exceeds the observed count')
        demanded = decision['branch'] in {'first_due_date_append', 'all_dates_later_skip'}
        if raw['date_scan_ready'] != demanded:
            raise ValueError(f'{name} date scan completeness is malformed')
        if decision['branch'] == 'first_due_date_append' and len(dates) != decision['first_due_date_native_index'] + 1:
            raise ValueError(f'{name} collector did not stop at first due date')
        if decision['branch'] == 'all_dates_later_skip' and len(dates) != native_count:
            raise ValueError(f'{name} all-later scan is incomplete')
        if decision['branch'] in {'valid_combat_skip', 'nonpositive_date_count_skip'} and dates:
            raise ValueError(f'{name} collector demanded skipped date entries')
    _ready(value, projected['conditional_append_requests_ready'], name, status=True)
    return deepcopy(value)
