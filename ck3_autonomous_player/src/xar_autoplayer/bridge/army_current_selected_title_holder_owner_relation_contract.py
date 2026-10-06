"""Exact .3 current selected-title holder/full Unit-owner native relation inputs."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import (
    _typed as _native_typed, _references, _resolution,
)

_STATE = {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string'}
_SHAPES = {
    'OperandSelection': {
        **_STATE, 'registry_loaded': 'bool?', 'used_fallback': 'bool?',
        'requested_full_id_u32': 'u32?', 'registry_capacity_u32': 'u32?',
        'registry_index_u32': 'u32?', 'indexed_full_id_u32': 'u32?',
        'indexed_identity': 'identity?', 'object_identity': 'identity?',
        'selection': 'string', 'selected_object_ready': 'bool',
    },
    'UnitSelection': {
        'native_index': 'i32', 'purpose': 'string', 'army_124_raw_u32': 'u32?',
        'unit_resolution': 'OperandSelection', 'province_used_fallback': 'bool?',
        'province_identity': 'identity?', 'province_magic_85c_raw_u32': 'u32?',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution',
        'same_query_army_selection_matched': 'bool', 'unit_selections': 'UnitSelection[]',
        'province_title_738_raw_u32': 'u32?', 'title_holder_128_raw_u32': 'u32?',
        'title_resolution': 'OperandSelection', 'parent_title_resolution': 'OperandSelection',
        'title_definition_64_raw_u32': 'u32?', 'parent_title_e8_raw_u32': 'u32?',
        'parent_holder_128_raw_u32': 'u32?', 'holder_requested_full_id_u32': 'u32?',
        'holder_character_full_id_u32': 'u32?', 'holder_character_resolution': 'OperandSelection',
        'selected_unit_owner_174_raw_u32': 'u32?', 'holder_owner_equal': 'bool?',
        'native_relation_demanded': 'bool', 'native_relation_returned': 'bool',
        'native_holder_owner_relation': 'bool?', 'derived_current_shared_tail_raw_u8': 'u8?',
        'current_shared_tail_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1',
        'source': 'string=native_selected_title_holder_owner_relation_28b2820',
        'stage': 'string=observed_current_selected_title_holder_owner_relation_inputs',
        'context_basis': 'string=same_query_selected_title_holder_and_unit_owner',
        'manager_loaded': 'bool?', 'manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool', 'original_army_selections_ready': 'bool',
        'current_shared_tail_inputs_ready': 'bool',
        'actual_refresh_execution_ready': 'bool=false', 'actual_next_occurrence_ready': 'bool=false',
        'changed_selection_context_ready': 'bool=false', 'changed_relationship_context_ready': 'bool=false',
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
    if 'status' in fields:
        if value['status'] not in {'available', 'partial', 'unavailable'}:
            raise ValueError(f'{name}.status is malformed')
        if (value['ready'] != (value['status'] == 'available')
                or value['ready'] == bool(value['unavailable_reason'])):
            raise ValueError(f'{name} status/readiness/reason disagree')


def normalize_current_selected_title_holder_owner_relation_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_selected_title_holder_owner_relation_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(row['native_index'], row['raw_full_id_u32']) for row in value['occurrences']] != [
            (row['native_index'], row['raw_full_id_u32'])
            for row in value['original_roster']['occurrences']]:
        raise ValueError('selected-holder relation filtered or relabeled original roster occurrences')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'],
                    prefix + '.original_army_resolution')
    from ..simulation.army_current_selected_title_holder_owner_relation_12003 import (
        validate_current_selected_title_holder_owner_relation_declared_12003,
    )
    validate_current_selected_title_holder_owner_relation_declared_12003(value)
    return deepcopy(value)
