"""Physical same-Character ordered-list and exact early predicate contract."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _properties, _string,
)
from ..simulation.battle_person_list_predicate_2530dd0_12003 import (
    compute_list_predicate_2530dd0_from_native_inputs_12003,
    emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003,
    emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003,
)


def _word(value: object, field: str) -> int | None:
    if isinstance(value, str):
        digits = value[2:] if value[:2].lower() == '0x' else ''
        if not digits or len(digits) > 16 or any(c not in '0123456789abcdefABCDEF' for c in digits):
            raise ValueError(field + ' must be native unsigned64 or hexadecimal pointer')
        value = int(digits, 16)
    return _number(value, field, 64, unsigned=True)


def _scope(value: object, field: str) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {'root_scope_kind_u32', 'root_character_full_id_u32',
                             'named_scope_kind_u32', 'named_selected_full_id_u32',
                             'named_binding_key_i32', 'trigger_object', 'trigger_vtable',
                             'trigger_evaluator_function'})
    out = {}
    for name in ('root_scope_kind_u32', 'root_character_full_id_u32',
                 'named_scope_kind_u32', 'named_selected_full_id_u32'):
        out[name] = _number(raw[name], field + '.' + name, 32, unsigned=True)
    out['named_binding_key_i32'] = _number(raw['named_binding_key_i32'], field + '.named_binding_key_i32', 32)
    for name in ('trigger_object', 'trigger_vtable', 'trigger_evaluator_function'):
        out[name] = _word(raw[name], field + '.' + name)
    if out['root_scope_kind_u32'] not in (None, 4) or out['named_scope_kind_u32'] not in (None, 31):
        raise ValueError(field + ' has an unsupported exact-build scope kind')
    return out


def _row(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'key_u32', 'ready', 'resolution_selection',
                             'selected_object', 'selected_full_id_u32', 'used_fallback',
                             'predicate_receiver', 'magic_u32', 'condition_count_raw_i32',
                             'predicate_result', 'pc_selection', 'scope_inputs', 'properties', 'reason'})
    out = {'native_index': _integer(raw['native_index'], field + '.native_index', 32, unsigned=True),
           'ready': _boolean(raw['ready'], field + '.ready'),
           'condition_count_raw_i32': _number(raw['condition_count_raw_i32'], field + '.condition_count_raw_i32', 32),
           'used_fallback': _boolean(raw['used_fallback'], field + '.used_fallback', optional=True),
           'predicate_result': _boolean(raw['predicate_result'], field + '.predicate_result', optional=True),
           'scope_inputs': _scope(raw['scope_inputs'], field + '.scope_inputs'),
           'properties': _properties(raw['properties'], field + '.properties'),
           'reason': _string(raw['reason'], field + '.reason', optional=True)}
    for name in ('key_u32', 'selected_full_id_u32', 'magic_u32'):
        out[name] = _number(raw[name], field + '.' + name, 32, unsigned=True)
    for name in ('selected_object', 'predicate_receiver'):
        out[name] = _word(raw[name], field + '.' + name)
    for name in ('resolution_selection', 'pc_selection'):
        out[name] = _string(raw[name], field + '.' + name, optional=True)
    if out['resolution_selection'] not in (None, 'registry_full_id', 'native_fallback'):
        raise ValueError(field + '.resolution_selection is unsupported')
    if out['pc_selection'] not in (None, 'selected_d8'):
        raise ValueError(field + '.pc_selection lacks a source-closed predicate outcome')
    return out


def normalize_list_predicate_2530dd0(value: object, field: str = 'list_predicate_2530dd0') -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {'status', 'ready', 'character_id', 'scratch_present', 'header_selection',
                             'default_header_guard_raw', 'source_array_present', 'source_count_raw',
                             'rows', 'reason'})
    out = {'status': _string(raw['status'], field + '.status'),
           'ready': _boolean(raw['ready'], field + '.ready'),
           'character_id': _integer(raw['character_id'], field + '.character_id', 32),
           'scratch_present': _boolean(raw['scratch_present'], field + '.scratch_present', optional=True),
           'header_selection': _string(raw['header_selection'], field + '.header_selection', optional=True),
           'default_header_guard_raw': _number(raw['default_header_guard_raw'], field + '.default_header_guard_raw', 32),
           'source_array_present': _boolean(raw['source_array_present'], field + '.source_array_present', optional=True),
           'source_count_raw': _number(raw['source_count_raw'], field + '.source_count_raw', 32),
           'rows': None, 'reason': _string(raw['reason'], field + '.reason', optional=True)}
    if raw['rows'] is not None:
        if not isinstance(raw['rows'], list):
            raise ValueError(field + '.rows must be an original-order list or null')
        out['rows'] = []
        for index, value in enumerate(raw['rows']):
            row = _row(value, field + '.rows[' + str(index) + ']')
            if row['native_index'] != index:
                raise ValueError(field + '.rows must preserve native physical order')
            out['rows'].append(row)
        count = out['source_count_raw']
        if count is not None and len(out['rows']) > max(count, 0):
            raise ValueError(field + '.rows exceeds actual physical count')
    result = compute_list_predicate_2530dd0_from_native_inputs_12003(out)
    for result_row in result.rows:
        if out['rows'] is None or result_row.native_index >= len(out['rows']):
            continue
        row = out['rows'][result_row.native_index]
        name = field + '.rows[' + str(result_row.native_index) + ']'
        if row['ready'] != result_row.ready or row['predicate_result'] != result_row.predicate_result:
            raise ValueError(name + ' readiness/predicate differs from actual source operands')
        if row['pc_selection'] != result_row.pc_selection:
            raise ValueError(name + ' PC selection differs from actual source predicate')
        if (row['ready'] and row['reason'] is not None) or (not row['ready'] and row['reason'] is None):
            raise ValueError(name + ' lacks consistent read status/reason')
        if result_row.skipped and (row['properties'] is not None or row['scope_inputs'] is not None):
            raise ValueError(name + ' sentinel row includes undemanded properties/scope')
        if result_row.predicate_result is None and row['properties'] is not None:
            raise ValueError(name + ' unknown predicate cannot publish an actual selected PC')
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
