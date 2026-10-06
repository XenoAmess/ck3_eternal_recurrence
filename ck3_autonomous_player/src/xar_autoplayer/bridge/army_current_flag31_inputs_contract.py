"""Strict exact .3 current Army31 source inputs and actual native slot24 verdict."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import (
    _typed as _native_typed, _references, _resolution,
)

_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'Selection': {
        **_STATE, 'registry_loaded': 'bool?', 'used_fallback': 'bool?',
        'requested_full_id_u32': 'u32?', 'registry_capacity_u32': 'u32?',
        'registry_index_u32': 'u32?', 'indexed_full_id_u32': 'u32?',
        'indexed_identity': 'identity?', 'selection': 'string?',
        'object_identity': 'identity?', 'selected_object_ready': 'bool',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution',
        'same_query_army_selection_matched': 'bool',
        'actual_army_31_raw_u8': 'u8?', 'army_1d4_raw_u8': 'u8?',
        'army_128_raw_u32': 'u32?', 'combat_resolution': 'Selection',
        'selected_combat_magic_0c_raw_u32': 'u32?',
        'selected_combat_full_id_08_raw_u32': 'u32?',
        'source_active_combat': 'bool?', 'active_combat_inputs_ready': 'bool',
        'army_124_raw_u32': 'u32?', 'unit_owner_174_raw_u32': 'u32?',
        'unit_resolution': 'Selection', 'character_resolution': 'Selection',
        'selected_character_18_raw_u32': 'u32?',
        'rule_selector_i32': 'i32=24', 'rule_inline_offset_u32': 'u32=4992',
        'rule_provider_identity': 'identity?', 'rule_array_identity': 'identity?',
        'inline_rule_identity': 'identity?', 'root_kind': 'i32?',
        'root_subtype': 'i32?', 'root_payload_u64': 'u64?',
        'root_construction': 'string', 'native_rule_evaluation_returned': 'bool',
        'native_current_rule24_passed': 'bool?', 'derived_current_31_raw_u8': 'u8?',
        'current_flag31_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1',
        'source': 'string=native_current_army_flag31_inputs',
        'stage': 'string=observed_current_army_flag31_inputs',
        'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool', 'original_army_selections_ready': 'bool',
        'current_flag31_inputs_ready': 'bool',
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


def _selection(value: dict, requested: int | None, name: str) -> None:
    if value['requested_full_id_u32'] != requested:
        raise ValueError(f'{name} requested wholeDWORD disagrees')
    if value['selection'] not in {None, 'registry_full_id', 'native_fallback'}:
        raise ValueError(f'{name} selected source is malformed')
    if value['selection'] is not None and value['used_fallback'] != (value['selection'] == 'native_fallback'):
        raise ValueError(f'{name} fallback classification disagrees')
    if value['registry_index_u32'] is not None and (
            requested is None or value['registry_index_u32'] != (requested & 0xFFFFFF)):
        raise ValueError(f'{name} low24 index disagrees with wholeDWORD')
    if value['registry_loaded'] is False and (requested is not None or value['registry_index_u32'] is not None):
        raise ValueError(f'{name} nullstore branch relabeled undemanded reference')
    if value['selection'] == 'registry_full_id' and value['selected_object_ready'] and (
            requested is None or value['indexed_full_id_u32'] != requested
            or value['object_identity'] != value['indexed_identity']):
        raise ValueError(f'{name} full generation/physical object disagrees')
    if value['selected_object_ready'] and (value['object_identity'] is None or value['selection'] is None):
        raise ValueError(f'{name} selected object has no source association')
    if value['ready'] != value['selected_object_ready']:
        raise ValueError(f'{name} independent selection readiness disagrees')


def normalize_current_army_flag31_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_army_flag31_inputs_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(row['native_index'], row['raw_full_id_u32']) for row in value['occurrences']] != [
            (row['native_index'], row['raw_full_id_u32']) for row in value['original_roster']['occurrences']]:
        raise ValueError('flag31 filtered or relabeled original roster occurrences')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        _selection(row['combat_resolution'], row['army_128_raw_u32'], prefix + '.combat_resolution')
        _selection(row['unit_resolution'], row['army_124_raw_u32'], prefix + '.unit_resolution')
        _selection(row['character_resolution'], row['unit_owner_174_raw_u32'], prefix + '.character_resolution')
        if row['root_construction'] not in {'not_demanded', '9F9E20_normal_return'}:
            raise ValueError(f'{prefix} actual root construction is malformed')
        if row['root_construction'] == '9F9E20_normal_return' and (
                row['root_kind'] != 4 or row['root_subtype'] != 0
                or row['selected_character_18_raw_u32'] is None
                or row['root_payload_u64'] != row['selected_character_18_raw_u32']):
            raise ValueError(f'{prefix} ordinary kind4 root lost actual selected Character18 DWORD')
    from ..simulation.army_current_flag31_inputs_12003 import validate_current_army_flag31_declared_12003
    validate_current_army_flag31_declared_12003(value)
    return deepcopy(value)
