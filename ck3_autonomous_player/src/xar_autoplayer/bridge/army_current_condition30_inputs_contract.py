"""Exact .3 current Army30 receiver/root observation, independent of numeric refresh."""
from __future__ import annotations
from copy import deepcopy
from .army_daily_assault_roster_admission_contract import (
    _typed as _native_typed, _references, _resolution,
)

_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'Unit': {
        **_STATE, 'requested_full_id_u32': 'u32?', 'registry_loaded': 'bool?',
        'registry_capacity_u32': 'u32?', 'registry_index_u32': 'u32?',
        'indexed_identity': 'identity?', 'indexed_full_id_u32': 'u32?',
        'selection': 'string?', 'used_fallback': 'bool?', 'object_identity': 'identity?',
        'selected_object_ready': 'bool',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution', 'same_query_army_selection_matched': 'bool',
        'actual_army_30_raw_u8': 'u8?', 'army_1d4_raw_u8': 'u8?',
        'army_124_raw_u32': 'u32?', 'unit_owner_174_raw_u32': 'u32?',
        'unit_resolution': 'Unit', 'condition_owner_identity': 'identity?',
        'inline_condition_identity': 'identity?', 'root_kind': 'u32?', 'root_subtype': 'u32?',
        'root_payload_u64': 'u64?', 'root_construction': 'string?',
        'native_current_condition_passed': 'bool?', 'derived_current_30_raw_u8': 'u8?',
        'current_condition_30_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1', 'source': 'string=native_current_army_condition30_inputs',
        'stage': 'string=observed_current_army_condition30_inputs',
        'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool', 'original_army_selections_ready': 'bool',
        'current_condition_30_inputs_ready': 'bool',
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
    if kind == 'u64':
        if type(value) is not int or not 0 <= value < 1 << 64:
            raise ValueError(f'{name} unsigned64 is malformed')
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


def _unit(row: dict, name: str) -> None:
    p = row['unit_resolution']
    raw = row['army_124_raw_u32']
    if p['requested_full_id_u32'] != raw:
        raise ValueError(f'{name} Unit request lost its complete DWORD')
    if p['selection'] not in {None, 'registry_full_id', 'native_fallback'}:
        raise ValueError(f'{name} Unit selection is malformed')
    if p['selection'] is not None and p['used_fallback'] != (p['selection'] == 'native_fallback'):
        raise ValueError(f'{name} Unit fallback classification disagrees')
    if p['registry_index_u32'] is not None and (
            raw is None or p['registry_index_u32'] != (raw & 0xFFFFFF)):
        raise ValueError(f'{name} Unit low24 index disagrees with full request')
    if p['registry_loaded'] is False and (raw is not None or p['registry_index_u32'] is not None):
        raise ValueError(f'{name} store-null branch demanded Army124')
    if p['selection'] == 'registry_full_id' and p['selected_object_ready'] and (
            raw is None or p['indexed_full_id_u32'] != raw or p['object_identity'] != p['indexed_identity']):
        raise ValueError(f'{name} Unit full generation disagrees')
    if p['selected_object_ready'] and (p['object_identity'] is None or p['selection'] is None):
        raise ValueError(f'{name} selected Unit has no association')
    if p['ready'] != p['selected_object_ready']:
        raise ValueError(f'{name} Unit readiness disagrees')


def normalize_current_army_condition30_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_army_condition30_inputs_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(r['native_index'], r['raw_full_id_u32']) for r in value['occurrences']] != [
            (r['native_index'], r['raw_full_id_u32']) for r in value['original_roster']['occurrences']]:
        raise ValueError('condition30 filtered or relabeled original roster occurrences')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        _unit(row, prefix)
        if row['root_construction'] is not None and (
                row['root_construction'] != '9F9E20_normal_return'
                or row['root_kind'] != 4 or row['root_subtype'] != 0
                or row['unit_owner_174_raw_u32'] is None
                or row['root_payload_u64'] != row['unit_owner_174_raw_u32']):
            raise ValueError(f'{prefix} ordinary kind4 root lost its full ownerDWORD')
    from ..simulation.army_current_condition30_inputs_12003 import validate_current_army_condition30_declared_12003
    validate_current_army_condition30_declared_12003(value)
    return deepcopy(value)
