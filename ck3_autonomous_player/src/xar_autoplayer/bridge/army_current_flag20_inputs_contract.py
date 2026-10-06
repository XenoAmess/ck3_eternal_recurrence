"""Exact .3 actual current Army20 getter, independent of old numeric refresh."""
from __future__ import annotations
from copy import deepcopy
from .army_daily_assault_roster_admission_contract import (
    _typed as _native_typed, _references, _resolution,
)

_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution', 'same_query_army_selection_matched': 'bool',
        'actual_army_20_raw_u8': 'u8?', 'army_1d4_raw_u8': 'u8?',
        'native_getter_returned': 'bool', 'native_getter_20_raw_u8': 'u8?',
        'derived_current_20_raw_u8': 'u8?', 'current_flag20_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1', 'source': 'string=native_current_army_flag20_inputs',
        'stage': 'string=observed_current_army_flag20_inputs',
        'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool', 'original_army_selections_ready': 'bool',
        'current_flag20_inputs_ready': 'bool',
        'actual_refresh_execution_ready': 'bool=false', 'actual_next_occurrence_ready': 'bool=false',
        'full_callback_ready': 'bool=false', 'full_daily_assault_ready': 'bool=false',
        'full_monthly_ready': 'bool=false',
    },
}


def _typed(value: object, kind: str, name: str) -> None:
    if kind.endswith('?'):
        if value is None:
            return
        return _typed(value, kind[:-1], name)
    if kind.endswith('[]'):
        if type(value) is not list:
            raise ValueError(f'{name} must retain its native array')
        for index, item in enumerate(value):
            _typed(item, kind[:-2], f'{name}[{index}]')
        return
    if kind not in _SHAPES:
        return _native_typed(value, kind, name)
    fields = _SHAPES[kind]
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f'{name} schema is malformed')
    for field, field_type in fields.items():
        _typed(value[field], field_type, name + '.' + field)
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError(f'{name}.status is malformed')
    if value['ready'] != (value['status'] == 'available') or value['ready'] == bool(value['unavailable_reason']):
        raise ValueError(f'{name} status/readiness/reason disagree')


def normalize_current_army_flag20_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_army_flag20_inputs_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(r['native_index'], r['raw_full_id_u32']) for r in value['occurrences']] != [
            (r['native_index'], r['raw_full_id_u32']) for r in value['original_roster']['occurrences']]:
        raise ValueError('flag20 filtered or relabeled original roster occurrences')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        if row['native_getter_20_raw_u8'] not in (None, 0, 1):
            raise ValueError(f'{prefix} actual source getter value must be0or1')
    from ..simulation.army_current_flag20_inputs_12003 import validate_current_army_flag20_declared_12003
    validate_current_army_flag20_declared_12003(value)
    return deepcopy(value)
