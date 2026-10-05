"""Physical current qualifier prefix contract; no synthetic baseline or state."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _properties, _string,
)
from ..simulation.battle_person_qualifier_28bc0d0_12003 import (
    compute_qualifier_28bc0d0_from_native_inputs_12003,
    emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003,
    emit_qualifier_28bc0d0_definition_requests_from_current_source_inputs_12003,
)


def _word(value: object, field: str) -> int | None:
    if isinstance(value, str):
        digits = value[2:] if value[:2].lower() == '0x' else ''
        if not digits or len(digits) > 16 or any(c not in '0123456789abcdefABCDEF' for c in digits):
            raise ValueError(field + ' must be native unsigned64 or hexadecimal pointer')
        value = int(digits, 16)
    return _number(value, field, 64, unsigned=True)


def _rows(value: object, field: str, converter) -> list | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(field + ' must be a physical prefix list or null')
    rows = []
    for index, item in enumerate(value):
        row = converter(item, field + '[' + str(index) + ']')
        if row['native_index'] != index:
            raise ValueError(field + ' must preserve original physical row order')
        rows.append(row)
    return rows


def _index(value: object, field: str) -> int:
    return _integer(value, field + '.native_index', 32, unsigned=True)


def _relation(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'marker_u8', 'definition_object'})
    return {'native_index': _index(raw['native_index'], field),
            'marker_u8': _number(raw['marker_u8'], field + '.marker_u8', 8, unsigned=True),
            'definition_object': _word(raw['definition_object'], field + '.definition_object')}


def _candidate(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'definition_object', 'relationship_count_raw_i32',
                             'relationship_array_present', 'relationships'})
    out = {'native_index': _index(raw['native_index'], field),
           'definition_object': _word(raw['definition_object'], field + '.definition_object'),
           'relationship_count_raw_i32': _number(raw['relationship_count_raw_i32'], field + '.relationship_count_raw_i32', 32),
           'relationship_array_present': _boolean(raw['relationship_array_present'], field + '.relationship_array_present', optional=True),
           'relationships': _rows(raw['relationships'], field + '.relationships', _relation)}
    _prefix_extent(out['relationship_count_raw_i32'], out['relationships'], field + '.relationships')
    return out


def _evaluation(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'object', 'candidate_count_raw_i32',
                             'candidate_array_present', 'candidates', 'id_u32'})
    out = {'native_index': _index(raw['native_index'], field),
           'object': _word(raw['object'], field + '.object'),
           'candidate_count_raw_i32': _number(raw['candidate_count_raw_i32'], field + '.candidate_count_raw_i32', 32),
           'candidate_array_present': _boolean(raw['candidate_array_present'], field + '.candidate_array_present', optional=True),
           'candidates': _rows(raw['candidates'], field + '.candidates', _candidate),
           'id_u32': _number(raw['id_u32'], field + '.id_u32', 32, unsigned=True)}
    _prefix_extent(out['candidate_count_raw_i32'], out['candidates'], field + '.candidates')
    return out


def _definition(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'definition_object', 'ready', 'scratch_evaluations',
                             'accepted_ids_u32', 'repeat_count', 'properties', 'reason'})
    return {'native_index': _index(raw['native_index'], field),
            'definition_object': _word(raw['definition_object'], field + '.definition_object'),
            'ready': _boolean(raw['ready'], field + '.ready'),
            'scratch_evaluations': _rows(raw['scratch_evaluations'], field + '.scratch_evaluations', _evaluation),
            'accepted_ids_u32': _numbers(raw['accepted_ids_u32'], field + '.accepted_ids_u32', 32, unsigned=True),
            'repeat_count': _number(raw['repeat_count'], field + '.repeat_count', 32),
            'properties': _properties(raw['properties'], field + '.properties'),
            'reason': _string(raw['reason'], field + '.reason', optional=True)}


def _prefix_extent(count: int | None, rows: list | None, field: str) -> None:
    if count is not None and rows is not None and len(rows) > max(count, 0):
        raise ValueError(field + ' exceeds actual physical count')


def normalize_qualifier_28bc0d0(value: object, field: str = 'qualifier_28bc0d0') -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {'status', 'ready', 'character_id', 'manager_object',
                             'definition_count_raw_i32', 'definition_array_present',
                             'scratch_present', 'scratch_count_raw_i32',
                             'fallback_definition_object', 'definitions', 'reason'})
    out = {'status': _string(raw['status'], field + '.status'),
           'ready': _boolean(raw['ready'], field + '.ready'),
           'character_id': _integer(raw['character_id'], field + '.character_id', 32),
           'manager_object': _word(raw['manager_object'], field + '.manager_object'),
           'definition_count_raw_i32': _number(raw['definition_count_raw_i32'], field + '.definition_count_raw_i32', 32),
           'definition_array_present': _boolean(raw['definition_array_present'], field + '.definition_array_present', optional=True),
           'scratch_present': _boolean(raw['scratch_present'], field + '.scratch_present', optional=True),
           'scratch_count_raw_i32': _number(raw['scratch_count_raw_i32'], field + '.scratch_count_raw_i32', 32),
           'fallback_definition_object': _word(raw['fallback_definition_object'], field + '.fallback_definition_object'),
           'definitions': _rows(raw['definitions'], field + '.definitions', _definition),
           'reason': _string(raw['reason'], field + '.reason', optional=True)}
    _prefix_extent(out['definition_count_raw_i32'], out['definitions'], field + '.definitions')
    result = compute_qualifier_28bc0d0_from_native_inputs_12003(out)
    for result_row in result.definitions:
        rows = out['definitions']
        if rows is None or result_row.native_index >= len(rows):
            continue
        row = rows[result_row.native_index]
        name = field + '.definitions[' + str(result_row.native_index) + ']'
        _prefix_extent(out['scratch_count_raw_i32'], row['scratch_evaluations'], name + '.scratch_evaluations')
        ids = None if result_row.accepted_ids_u32 is None else list(result_row.accepted_ids_u32)
        if row['accepted_ids_u32'] != ids or row['repeat_count'] != result_row.repeat_count:
            raise ValueError(name + ' published dedup count differs from actual predicate operands')
        if row['ready'] != result_row.ready or (row['ready'] and row['reason'] is not None):
            raise ValueError(name + ' has inconsistent independent readiness')
        if not row['ready'] and row['reason'] is None:
            raise ValueError(name + ' partial observation lacks its actual missing operand')
    if out['ready'] != result.ready:
        raise ValueError(field + ' has inconsistent whole-stage readiness')
    if out['status'] == 'available':
        if out['ready'] is not True or out['reason'] is not None:
            raise ValueError(field + ' available observation is inconsistent')
    elif out['status'] == 'partial':
        if out['ready'] is not False or out['reason'] is None:
            raise ValueError(field + ' partial observation is inconsistent')
    else:
        raise ValueError(field + '.status is unsupported')
    return out
