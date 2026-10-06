"""Strict source-bound current Character prefix observations, including partials."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import _typed as _existing_typed, _references, _resolution
from .army_pre_date_dated_append_contract import _id_list, _ready
from ..simulation.army_pre_date_character_prefix_12003 import _raw_projection

_SHAPES = {
    'Predicate': {'demanded': 'bool', 'observable': 'bool', 'verdict': 'bool?', 'unavailable_reason': 'string'},
    'IdList': {'ready': 'bool', 'unavailable_reason': 'string', 'source': 'string',
               'count_raw_i32': 'i32?', 'ordered_ids_u32': 'u32?[]?'},
    'Occurrence': {'status': 'string', 'ready': 'bool', 'unavailable_reason': 'string',
                   'native_index': 'i32', 'original_request_full_id_u32': 'u32?',
                   'army_resolution': 'OperandResolution', 'earlier_skip': 'bool?', 'earlier_skip_source': 'string',
                   'army_character_120_raw_u32': 'u32?', 'character_resolution': 'OperandResolution',
                   'army_unit_124_raw_u32': 'u32?', 'unit_resolution': 'OperandResolution',
                   'unit_owner_174_raw_u32': 'u32?', 'character_magic_1c_raw_u32': 'u32?',
                   'character_full_id_18_raw_u32': 'u32?', 'character_death_1d0_present': 'bool?',
                   'character_state_1c8_present': 'bool?', 'character_state_1c0_present': 'bool?',
                   'character_state_1b8_present': 'bool?', 'membership': 'Predicate', 'basic_rule': 'Predicate',
                   'availability': 'Predicate', 'failure_append_army_10_raw_u32': 'u32?'},
    'Inputs': {'schema_version': 'i32=1', 'source': 'string=native_current_pre_date_character_prefix_inputs',
               'stage': 'string=observed_current_conditional_2a99f72_character_prefix', 'status': 'string',
               'ready': 'bool', 'unavailable_reason': 'string', 'manager_loaded': 'bool',
               'manager_identity': 'identity?', 'original_roster': 'RawReferences',
               'initial_80': 'IdList', 'occurrences': 'Occurrence[]'},
}
_RAW_FIELDS = ('army_character_120_raw_u32', 'army_unit_124_raw_u32', 'unit_owner_174_raw_u32',
               'character_magic_1c_raw_u32', 'character_full_id_18_raw_u32', 'character_death_1d0_present',
               'character_state_1c8_present', 'character_state_1c0_present', 'character_state_1b8_present',
               'failure_append_army_10_raw_u32')


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


def normalize_current_pre_date_character_prefix_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_pre_date_character_prefix_inputs_v1'
    _typed(value, 'Inputs', name)
    if value['manager_loaded'] and value['manager_identity'] is None:
        raise ValueError(f'{name} manager identity is unobserved')
    _references(value['original_roster'], name + '.original_roster')
    _id_list(value['initial_80'], name + '.initial_80')
    references, rows = value['original_roster']['occurrences'], value['occurrences']
    if [(r['native_index'], r['original_request_full_id_u32']) for r in rows] != [
            (r['native_index'], r['raw_full_id_u32']) for r in references]:
        raise ValueError(f'{name} lost original roster order/full generations')
    decisions, complete = _raw_projection(value)
    for raw, decision in zip(rows, decisions):
        prefix = name + f'.occurrences[{raw["native_index"]}]'
        _resolution(raw['army_resolution'], raw['original_request_full_id_u32'], prefix + '.army_resolution')
        _resolution(raw['character_resolution'], raw['army_character_120_raw_u32'], prefix + '.character_resolution')
        _resolution(raw['unit_resolution'], raw['army_unit_124_raw_u32'], prefix + '.unit_resolution')
        if raw['earlier_skip_source'] not in {'unavailable', 'pending_dispatch_bypass', 'same_query_existing_pending_count'}:
            raise ValueError(f'{prefix} earlier source is malformed')
        if (raw['earlier_skip'] is None) != (raw['earlier_skip_source'] == 'unavailable'):
            raise ValueError(f'{prefix} earlier readiness disagrees with its source')
        if raw['earlier_skip_source'] == 'pending_dispatch_bypass' and raw['earlier_skip'] is not False:
            raise ValueError(f'{prefix} bypass cannot skip the Character prefix')
        for field in _RAW_FIELDS:
            if field not in decision['demanded_fields'] and raw[field] is not None:
                raise ValueError(f'{prefix}.{field} was captured after a source short circuit')
        for predicate in ('membership', 'basic_rule', 'availability'):
            observed = raw[predicate]
            demanded = predicate in decision['demanded_predicates']
            if observed['demanded'] != demanded or observed['observable'] != (observed['verdict'] is not None):
                raise ValueError(f'{prefix}.{predicate} demand/observation is malformed')
            if observed['observable'] and (not demanded or observed['unavailable_reason']):
                raise ValueError(f'{prefix}.{predicate} observable verdict is malformed')
            if not observed['observable'] and (not observed['unavailable_reason'] or
                                              (not demanded and observed['unavailable_reason'] != 'not_demanded')):
                raise ValueError(f'{prefix}.{predicate} missing verdict reason is malformed')
        _ready(raw, decision['ready'], prefix, status=True)
    _ready(value, complete, name, status=True)
    return deepcopy(value)
