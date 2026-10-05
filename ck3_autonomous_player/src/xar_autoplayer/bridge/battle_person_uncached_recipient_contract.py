"""Raw cache440-zero leaf contract; exact reduction lives in the pure module."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _numbers, _string,
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
        raise ValueError(field + ' must be a list or null')
    out = []
    for index, item in enumerate(value):
        row = converter(item, field + '[' + str(index) + ']')
        if row['native_index'] != index:
            raise ValueError(field + ' must preserve the raw physical index order')
        out.append(row)
    return out


def _record(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'marker_u8', 'key_object', 'key_id_i32', 'value_q64'})
    return {'native_index': _integer(raw['native_index'], field + '.native_index', 32, unsigned=True),
            'marker_u8': _number(raw['marker_u8'], field + '.marker_u8', 8, unsigned=True),
            'key_object': _word(raw['key_object'], field + '.key_object'),
            'key_id_i32': _number(raw['key_id_i32'], field + '.key_id_i32', 32),
            'value_q64': _number(raw['value_q64'], field + '.value_q64', 64)}


def _vector(value: object, field: str, name: str, converter) -> dict:
    raw = _dict(value, field, {'count', name})
    count = _number(raw['count'], field + '.count', 32)
    rows = _rows(raw[name], field + '.' + name, converter)
    if count is not None and rows is not None and len(rows) > max(count, 0):
        raise ValueError(field + '.' + name + ' exceeds the physical count')
    return {'count': count, name: rows}


def _family(value: object, field: str) -> dict:
    raw = _dict(value, field, {'ready', 'first', 'second'})
    out = {'ready': _boolean(raw['ready'], field + '.ready'),
           'first': _vector(raw['first'], field + '.first', 'records', _record),
           'second': _vector(raw['second'], field + '.second', 'records', _record)}
    if out['ready']:
        for name in ('first', 'second'):
            vector = out[name]
            rows = vector['records']
            if vector['count'] is None or vector['count'] < 0 or rows is None or len(rows) != vector['count']:
                raise ValueError(field + '.ready lacks its physical rows')
            for row in rows:
                if row['marker_u8'] is None or row['value_q64'] is None or (
                        row['marker_u8'] == 2 and (row['key_object'] is None or row['key_id_i32'] is None)):
                    raise ValueError(field + '.ready lacks a demanded intrinsic operand')
    return out


def _object(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'object', 'magic_u32', 'intrinsic_family'})
    return {'native_index': _integer(raw['native_index'], field + '.native_index', 32, unsigned=True),
            'object': _word(raw['object'], field + '.object'),
            'magic_u32': _number(raw['magic_u32'], field + '.magic_u32', 32, unsigned=True),
            'intrinsic_family': _family(raw['intrinsic_family'], field + '.intrinsic_family')}


def _context(value: object, field: str) -> dict:
    raw = _dict(value, field, {'native_index', 'object', 'flag_u8'})
    return {'native_index': _integer(raw['native_index'], field + '.native_index', 32, unsigned=True),
            'object': _word(raw['object'], field + '.object'),
            'flag_u8': _number(raw['flag_u8'], field + '.flag_u8', 8, unsigned=True)}


def _downstream(value: object, field: str) -> dict:
    raw = _dict(value, field, {
        'trait_ids', 'membership_ids', 'membership_header_guard_raw', 'aggregate_properties',
        'aggregate_context_selection', 'aggregate_context_guard_raw', 'member_multiplier_q64',
        'clamp_lower_q64', 'clamp_upper_q64',
    })
    out = {}
    for name, bits, values in (('trait_ids', 32, 'values_u32'), ('membership_ids', 64, 'values_u64')):
        row = _dict(raw[name], field + '.' + name, {'count', values})
        out[name] = {'count': _number(row['count'], field + '.' + name + '.count', 32),
                     values: _numbers(row[values], field + '.' + name + '.' + values, bits, unsigned=True)}
    aggregate = _dict(raw['aggregate_properties'], field + '.aggregate_properties',
                      {'count', 'keys_u16', 'values_q64'})
    out['aggregate_properties'] = {
        'count': _number(aggregate['count'], field + '.aggregate_properties.count', 32),
        'keys_u16': _numbers(aggregate['keys_u16'], field + '.aggregate_properties.keys_u16', 16, unsigned=True),
        'values_q64': _numbers(aggregate['values_q64'], field + '.aggregate_properties.values_q64', 64),
    }
    for name in ('membership_header_guard_raw', 'aggregate_context_guard_raw'):
        out[name] = _number(raw[name], field + '.' + name, 32)
    for name in ('member_multiplier_q64', 'clamp_lower_q64', 'clamp_upper_q64'):
        out[name] = _number(raw[name], field + '.' + name, 64)
    selection = _string(raw['aggregate_context_selection'], field + '.aggregate_context_selection', optional=True)
    if selection not in {None, 'owned_model_10', 'inline_context_5d67b90'}:
        raise ValueError(field + '.aggregate_context_selection is unsupported')
    out['aggregate_context_selection'] = selection
    return out


def normalize_uncached_recipient_inputs(value: object,
                                        field: str = 'uncached_recipient_inputs') -> dict | None:
    if value is None:
        return None
    fields = {
        'status', 'ready', 'character_id', 'carrier_present', 'associated_full_id',
        'associated_resolved_full_id', 'associated_used_fallback', 'associated_cache_440',
        'seed_receiver', 'seed_family', 'fallback_key_object', 'fallback_key_id_i32',
        'active_objects', 'active_context', 'removed_objects', 'cap_i32',
        'active_flag4_multiplier_q64', 'active_other_multiplier_q64', 'seed_boost_multiplier_q64',
        'positive_fallback_object', 'negative_fallback_object', 'positive_fallback_magic_u32',
        'negative_fallback_magic_u32', 'downstream_inputs', 'calculated_recipient_q64', 'reason',
    }
    raw = _dict(value, field, fields)
    out = {'status': _string(raw['status'], field + '.status'),
           'ready': _boolean(raw['ready'], field + '.ready'),
           'character_id': _integer(raw['character_id'], field + '.character_id', 32),
           'carrier_present': _boolean(raw['carrier_present'], field + '.carrier_present', optional=True),
           'associated_used_fallback': _boolean(raw['associated_used_fallback'], field + '.associated_used_fallback', optional=True),
           'seed_family': _family(raw['seed_family'], field + '.seed_family'),
           'active_objects': _vector(raw['active_objects'], field + '.active_objects', 'entries', _object),
           'removed_objects': _vector(raw['removed_objects'], field + '.removed_objects', 'entries', _object),
           'active_context': _vector(raw['active_context'], field + '.active_context', 'entries', _context),
           'downstream_inputs': _downstream(raw['downstream_inputs'], field + '.downstream_inputs'),
           'reason': _string(raw['reason'], field + '.reason', optional=True)}
    for name in ('associated_full_id', 'associated_resolved_full_id', 'associated_cache_440',
                 'positive_fallback_magic_u32', 'negative_fallback_magic_u32'):
        out[name] = _number(raw[name], field + '.' + name, 32, unsigned=True)
    for name in ('fallback_key_id_i32', 'cap_i32'):
        out[name] = _number(raw[name], field + '.' + name, 32)
    for name in ('fallback_key_object', 'positive_fallback_object', 'negative_fallback_object'):
        out[name] = _word(raw[name], field + '.' + name)
    for name in ('active_flag4_multiplier_q64', 'active_other_multiplier_q64',
                 'seed_boost_multiplier_q64', 'calculated_recipient_q64'):
        out[name] = _number(raw[name], field + '.' + name, 64)
    seed_fields = {'first_full_id', 'first_resolved_full_id', 'first_used_fallback',
                   'second_full_id', 'second_resolved_full_id', 'second_used_fallback', 'definition_object'}
    seed = _dict(raw['seed_receiver'], field + '.seed_receiver', seed_fields)
    out['seed_receiver'] = {}
    for name in seed_fields:
        path = field + '.seed_receiver.' + name
        out['seed_receiver'][name] = (_boolean(seed[name], path, optional=True) if name.endswith('fallback')
                                     else _word(seed[name], path) if name == 'definition_object'
                                     else _number(seed[name], path, 32, unsigned=True))
    from ..simulation.battle_person_uncached_recipient_12003 import (
        compute_uncached_recipient_from_native_inputs_12003,
    )
    result = compute_uncached_recipient_from_native_inputs_12003(out)
    if out['status'] == 'available':
        if (out['ready'] is not True or out['reason'] is not None or not result.calculation_ready
                or result.value_q64 != out['calculated_recipient_q64']):
            raise ValueError(field + ' available scalar differs from actual native inputs')
    elif out['status'] == 'not_applicable':
        if (out['ready'] is not True or result.applicable is not False
                or out['reason'] is not None or out['calculated_recipient_q64'] is not None):
            raise ValueError(field + ' has inconsistent present/cached skip')
    elif out['status'] == 'partial':
        if out['ready'] is not False or out['reason'] is None or out['calculated_recipient_q64'] is not None:
            raise ValueError(field + ' has inconsistent partial observation')
    else:
        raise ValueError(field + '.status is unsupported')
    return out
