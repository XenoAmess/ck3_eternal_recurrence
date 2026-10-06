"""Strict observed-current inputs for the exact .3 callback numeric prefix."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import (
    _ordered, _references, _resolution, _typed as _native_typed,
)


_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'ArRg': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'arrg_resolution': 'OperandResolution', 'magic_14_raw_u32': 'u32?',
        'identity_valid': 'bool?', 'current_38_raw_i32': 'i32?',
        'value_40_raw_i64': 'i64?', 'numeric_24_inputs_ready': 'bool',
        'numeric_28_inputs_ready': 'bool',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution',
        'original_arrg_references': 'RawReferences', 'arrg_occurrences': 'ArRg[]',
        'actual_army_24_raw_i32': 'i32?', 'actual_army_28_raw_i64': 'i64?',
        'actual_army_20_raw_u8': 'u8?', 'actual_army_21_raw_u8': 'u8?',
        'actual_army_30_raw_u8': 'u8?', 'actual_army_31_raw_u8': 'u8?',
        'arrg_rows_ready': 'bool', 'numeric_24_inputs_ready': 'bool',
        'numeric_28_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1',
        'source': 'string=native_current_post_admission_refresh_inputs',
        'stage': 'string=observed_current_post_admission_refresh_inputs',
        'projection_stage': 'string=post24df4c3_pre24df4c7',
        'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool',
        'original_army_selections_ready': 'bool',
        'numeric_24_inputs_ready': 'bool', 'numeric_28_inputs_ready': 'bool',
        'source_operands_ready': 'bool',
        'actual_refresh_execution_ready': 'bool=false',
        'actual_next_occurrence_ready': 'bool=false', 'full_callback_ready': 'bool=false',
        'full_daily_assault_ready': 'bool=false', 'full_monthly_ready': 'bool=false',
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
        _native_typed(value, kind, name)
        return
    fields = _SHAPES[kind]
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f'{name} schema is malformed')
    for field, field_type in fields.items():
        _typed(value[field], field_type, name + '.' + field)
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError(f'{name}.status is malformed')
    if value['ready'] != (value['status'] == 'available'):
        raise ValueError(f'{name} availability disagrees with readiness')
    if value['ready'] == bool(value['unavailable_reason']):
        raise ValueError(f'{name} reason disagrees with readiness')


def _same_raw_occurrences(references: dict, rows: list, name: str) -> None:
    if [(row['native_index'], row['raw_full_id_u32']) for row in rows] != [
            (row['native_index'], row['raw_full_id_u32'])
            for row in references['occurrences']]:
        raise ValueError(f'{name} filtered or relabeled the original raw references')


def normalize_current_post_admission_refresh_inputs_v1(
        value: object, field: str = 'current_post_admission_refresh_inputs_v1') -> dict | None:
    """Keep raw fields; validate branch demand and both numeric gates independently."""
    if value is None:
        return None
    _typed(value, 'Inputs', field)
    _references(value['original_roster'], field + '.original_roster')
    _same_raw_occurrences(value['original_roster'], value['occurrences'], field)
    for row in value['occurrences']:
        name = field + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'],
                    name + '.original_army_resolution')
        references = row['original_arrg_references']
        _references(references, name + '.original_arrg_references')
        _ordered(row['arrg_occurrences'], name + '.arrg_occurrences', references['count_raw_i32'])
        _same_raw_occurrences(references, row['arrg_occurrences'], name)
        for arrg in row['arrg_occurrences']:
            _resolution(arrg['arrg_resolution'], arrg['raw_full_id_u32'],
                        name + f'.arrg_occurrences[{arrg["native_index"]}].arrg_resolution')
    from ..simulation.army_current_post_admission_refresh_12003 import (
        validate_current_post_admission_refresh_declared_12003,
    )
    validate_current_post_admission_refresh_declared_12003(value)
    return deepcopy(value)
