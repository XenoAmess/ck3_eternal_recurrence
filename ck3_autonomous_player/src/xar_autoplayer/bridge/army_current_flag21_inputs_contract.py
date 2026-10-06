"""Exact .3 inline current21 prefix and actual readonly shared-tail observation."""
from __future__ import annotations
from copy import deepcopy
from .army_daily_assault_roster_admission_contract import (
    _typed as _native_typed, _references, _resolution,
)

_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'Selection': {
        **_STATE, 'registry_loaded': 'bool?', 'requested_full_id_u32': 'u32?',
        'registry_capacity_u32': 'u32?', 'registry_index_u32': 'u32?',
        'indexed_identity': 'identity?', 'indexed_full_id_u32': 'u32?',
        'selection': 'string?', 'used_fallback': 'bool?', 'object_identity': 'identity?',
        'selected_object_ready': 'bool',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution', 'same_query_army_selection_matched': 'bool',
        'actual_army_21_raw_u8': 'u8?', 'army_1ec_raw_u8': 'u8?', 'army_1f0_raw_i64': 'i64?',
        'army_124_raw_u32': 'u32?', 'unit_resolution': 'Selection',
        'unit_owner_174_raw_u32': 'u32?', 'character_resolution': 'Selection',
        'owner_character_carrier_1c0_present': 'bool?', 'owner_character_carrier_identity': 'identity?',
        'header_selection': 'string?', 'header_identity': 'identity?', 'header_0c_raw_i32': 'i32?',
        'owner_header_inputs_ready': 'bool', 'native_shared_tail_returned': 'bool',
        'native_shared_tail_21_raw_u8': 'u8?', 'derived_current_21_raw_u8': 'u8?',
        'current_flag21_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1', 'source': 'string=native_current_army_flag21_inputs',
        'stage': 'string=observed_current_army_flag21_inputs', 'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]', 'raw_roster_references_ready': 'bool',
        'original_army_selections_ready': 'bool', 'current_flag21_inputs_ready': 'bool',
        'actual_refresh_execution_ready': 'bool=false', 'actual_next_occurrence_ready': 'bool=false',
        'full_callback_ready': 'bool=false', 'full_daily_assault_ready': 'bool=false', 'full_monthly_ready': 'bool=false',
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


def _selection(p: dict, requested: int | None, name: str) -> None:
    if p['requested_full_id_u32'] != requested:
        raise ValueError(f'{name} requested wholeDWORD disagrees')
    if p['selection'] not in {None, 'registry_full_id', 'native_fallback'}:
        raise ValueError(f'{name} selected source is malformed')
    if p['selection'] is not None and p['used_fallback'] != (p['selection'] == 'native_fallback'):
        raise ValueError(f'{name} fallback classification disagrees')
    if p['registry_index_u32'] is not None and (requested is None or p['registry_index_u32'] != requested & 0xFFFFFF):
        raise ValueError(f'{name} low24 index disagrees with wholeDWORD')
    if p['registry_loaded'] is False and (requested is not None or p['registry_index_u32'] is not None):
        raise ValueError(f'{name} nullstore branch relabeled undemanded reference')
    if p['selection'] == 'registry_full_id' and p['selected_object_ready'] and (
            requested is None or p['indexed_full_id_u32'] != requested or p['object_identity'] != p['indexed_identity']):
        raise ValueError(f'{name} full generation/physical object disagrees')
    if p['selected_object_ready'] and (p['object_identity'] is None or p['selection'] is None):
        raise ValueError(f'{name} selected object has no source association')
    if p['ready'] != p['selected_object_ready']:
        raise ValueError(f'{name} independent selection readiness disagrees')


def normalize_current_army_flag21_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_army_flag21_inputs_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(r['native_index'], r['raw_full_id_u32']) for r in value['occurrences']] != [
            (r['native_index'], r['raw_full_id_u32']) for r in value['original_roster']['occurrences']]:
        raise ValueError('flag21 filtered or relabeled original roster occurrences')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        _selection(row['unit_resolution'], row['army_124_raw_u32'], prefix + '.unit_resolution')
        _selection(row['character_resolution'], row['unit_owner_174_raw_u32'], prefix + '.character_resolution')
        if row['native_shared_tail_21_raw_u8'] not in (None, 0, 1):
            raise ValueError(f'{prefix} actual source shared-tail value must be0or1')
        if row['header_selection'] not in {None, 'carrier_inline', 'native_static'}:
            raise ValueError(f'{prefix} actual header source is malformed')
    from ..simulation.army_current_flag21_inputs_12003 import validate_current_army_flag21_declared_12003
    validate_current_army_flag21_declared_12003(value)
    return deepcopy(value)
