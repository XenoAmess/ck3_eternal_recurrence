"""Optional exact current cached modifier19F, with independent aggregate scopes."""

from __future__ import annotations

from .battle_current_dynamic_components_contract import _component, _signed


def normalize_current_own_nested_modifier_v1(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {'scale', 'modifier_id', 'sides'}:
        raise ValueError(f'{field} has invalid current own modifier fields')
    if (type(value['scale']) is not int or value['scale'] != 100000
            or type(value['modifier_id']) is not int or value['modifier_id'] != 415):
        raise ValueError(f'{field} requires native Q100000 modifier19F')
    sides = value['sides']
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f'{field}.sides requires both native side slots')
    copied = []
    for index, side in enumerate(sides):
        if not isinstance(side, dict) or set(side) != {
            'side_index', 'selected_character_id_raw', 'selection',
            'combat_side_aggregate', 'selected_character_aggregate',
        } or type(side['side_index']) is not int or side['side_index'] != index:
            raise ValueError(f'{field}.sides must retain native side order')
        selected = side['selection']
        if not isinstance(selected, dict) or set(selected) != {
            'status', 'resolved_character_id_raw', 'used_native_fallback', 'unavailable_reason',
        }:
            raise ValueError(f'{field}.selection has invalid source fields')
        resolved, fallback, reason = (selected['resolved_character_id_raw'],
                                      selected['used_native_fallback'], selected['unavailable_reason'])
        if selected['status'] == 'available':
            resolved = _signed(resolved, f'{field}.resolved_character_id_raw', 32)
            if type(fallback) is not bool or reason is not None:
                raise ValueError(f'{field}.selection available lineage is incomplete')
        elif (selected['status'] != 'unavailable' or resolved is not None or fallback is not None
              or not isinstance(reason, str) or not reason):
            raise ValueError(f'{field}.selection unavailable lineage requires nulls and reason')
        copied.append({
            'side_index': index,
            'selected_character_id_raw': _signed(side['selected_character_id_raw'], field, 32),
            'selection': {'status': selected['status'], 'resolved_character_id_raw': resolved,
                          'used_native_fallback': fallback, 'unavailable_reason': reason},
            **{scope: _component(side[scope], field=f'{field}.{scope}', name='amount_raw', bits=64)
               for scope in ('combat_side_aggregate', 'selected_character_aggregate')},
        })
    return {'scale': 100000, 'modifier_id': 415, 'sides': copied}
