"""Strict source-selected administrative switch; never permission or actual ADD."""
from __future__ import annotations

_NUMBERS = ('persistent_full_id', 'character_ref_12c_raw', 'title_ref_130_raw',
            'resolved_title_full_id', 'selected_character_raw_full_id',
            'resolved_character_full_id', 'raw_byte_4a9')
_MAGIC = ('definition_magic_38_raw', 'character_magic_raw')
_BOOL = ('title_used_fallback', 'character_used_fallback',
         'military_component_present', 'enabled')
_KEYS = set(_NUMBERS + _MAGIC + _BOOL) | {
    'source', 'status', 'unavailable_reason', 'source_branch', 'identity_consistent'}
_SPECIAL = 0x4744624F

def normalize_refill_permission_switch_12004(value: object, *, owner_full_id: object = None) -> dict:
    if type(value) is not dict or set(value) != _KEYS:
        raise ValueError('refill source switch schema is malformed')
    if value['source'] != 'native_regiment_permission_262C6E0_switch_12004':
        raise ValueError('refill source switch source is malformed')
    if value['status'] not in {'available', 'not_applicable', 'unavailable'}:
        raise ValueError('refill source switch status is malformed')
    for name in _NUMBERS + _MAGIC:
        v = value[name]
        low, high = (0, 1 << 32) if name in _MAGIC else (-(1 << 31), 1 << 31)
        if v is not None and (type(v) is not int or not low <= v < high):
            raise ValueError('refill source switch integer is malformed')
    for name in _BOOL:
        if value[name] is not None and type(value[name]) is not bool:
            raise ValueError('refill source switch bool is malformed')
    if type(value['identity_consistent']) is not bool:
        raise ValueError('refill source switch consistency is malformed')
    reason = value['unavailable_reason']
    if reason is not None and (type(reason) is not str or not reason):
        raise ValueError('refill source switch reason is malformed')
    if type(value['source_branch']) is not str or value['source_branch'] not in {
            'unresolved', 'non_special_definition_bypass', 'direct_character', 'title_holder',
            'conflicting_references_fallback', 'missing_references_fallback'}:
        raise ValueError('refill source switch branch is malformed')
    if (owner_full_id is not None and value['persistent_full_id'] is not None
            and value['persistent_full_id'] != owner_full_id):
        raise ValueError('refill source switch belongs to another persistent receiver')
    raw = value['raw_byte_4a9']
    if raw is not None and not 0 <= raw <= 255:
        raise ValueError('refill source switch byte is malformed')
    if value['status'] == 'unavailable':
        if reason is None or value['enabled'] is not None or raw is not None or value['identity_consistent']:
            raise ValueError('unavailable refill switch cannot grant a value')
        return dict(value)
    if reason is not None or not value['identity_consistent'] or value['persistent_full_id'] in (None, -1):
        raise ValueError('qualified refill source switch lacks stable receiver')
    if value['status'] == 'not_applicable':
        omitted = _NUMBERS[1:] + ('character_magic_raw',) + _BOOL
        if (value['source_branch'] != 'non_special_definition_bypass'
                or value['definition_magic_38_raw'] in (None, _SPECIAL)
                or any(value[name] is not None for name in omitted)):
            raise ValueError('non-special bypass cannot invent a switch owner')
        return dict(value)
    if (value['definition_magic_38_raw'] != _SPECIAL or raw is None
            or value['enabled'] is not (raw != 0)
            or value['character_magic_raw'] != 0x43686172
            or value['military_component_present'] is not True
            or value['resolved_character_full_id'] in (None, -1)
            or type(value['character_used_fallback']) is not bool):
        raise ValueError('available refill switch lacks native source/byte witness')
    c, t, selected = (value[n] for n in ('character_ref_12c_raw', 'title_ref_130_raw',
                                       'selected_character_raw_full_id'))
    branch = value['source_branch']
    if c is None or t is None or selected is None:
        raise ValueError('available refill switch lacks source reference operands')
    expected = ('title_holder' if c == -1 else 'conflicting_references_fallback') if t != -1 else (
        'missing_references_fallback' if c == -1 else 'direct_character')
    if branch != expected:
        raise ValueError('refill switch source branch contradicts native reference precedence')
    if branch == 'title_holder':
        if value['resolved_title_full_id'] is None or type(value['title_used_fallback']) is not bool:
            raise ValueError('refill title-holder source lacks resolution witness')
        if not value['title_used_fallback'] and value['resolved_title_full_id'] != t:
            raise ValueError('refill title resolution loses full generation')
    elif value['resolved_title_full_id'] is not None or value['title_used_fallback'] is not None:
        raise ValueError('refill non-title branch cannot borrow title data')
    if branch == 'direct_character' and selected != c:
        raise ValueError('refill direct-character source changed identity')
    if branch in {'conflicting_references_fallback', 'missing_references_fallback'} and selected != -1:
        raise ValueError('refill native fallback must retain sentinel source')
    if not value['character_used_fallback'] and value['resolved_character_full_id'] != selected:
        raise ValueError('refill character resolution loses full generation')
    if selected == -1 and value['character_used_fallback'] is not True:
        raise ValueError('refill sentinel source must use native fallback')
    return dict(value)
