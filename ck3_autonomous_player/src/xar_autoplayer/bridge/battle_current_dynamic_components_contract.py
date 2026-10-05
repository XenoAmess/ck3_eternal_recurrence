"""Current actual native component outputs; each source retains its own status."""

from __future__ import annotations


def _signed(value: object, field: str, bits: int) -> int:
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"{field} must be signed int{bits}")
    return value


def _component(value: object, *, field: str, name: str, bits: int) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {'status', 'unavailable_reason', name}:
        raise ValueError(f"{field} has invalid component fields")
    status, reason, raw = value['status'], value['unavailable_reason'], value[name]
    if status == 'available':
        raw = _signed(raw, f'{field}.{name}', bits)
        if reason is not None:
            raise ValueError(f"{field} available component requires null reason")
    elif status != 'unavailable' or raw is not None or not isinstance(reason, str) or not reason:
        raise ValueError(f"{field} unavailable component requires null value and reason")
    return {'status': status, name: raw, 'unavailable_reason': reason}


def normalize_current_dynamic_components_v1(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {'scale', 'sides'}:
        raise ValueError(f"{field} must contain current dynamic component fields")
    if type(value['scale']) is not int or value['scale'] != 100000:
        raise ValueError(f"{field}.scale must be 100000")
    sides = value['sides']
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{field}.sides requires both native side slots")
    rows = []
    for index, side in enumerate(sides):
        if not isinstance(side, dict) or set(side) != {
            'side_index', 'current_roll_points', 'selected_character_id_raw',
            'selection', 'relation', 'commander', 'side_aggregate',
        } or type(side['side_index']) is not int or side['side_index'] != index:
            raise ValueError(f"{field}.sides must retain native side order")
        selected = side['selection']
        if not isinstance(selected, dict) or set(selected) != {
            'status', 'resolved_character_id_raw', 'used_native_fallback', 'unavailable_reason',
        }:
            raise ValueError(f"{field}.selection has invalid source fields")
        selected_raw = selected['resolved_character_id_raw']
        fallback, reason = selected['used_native_fallback'], selected['unavailable_reason']
        if selected['status'] == 'available':
            selected_raw = _signed(selected_raw, f'{field}.selection.resolved_character_id_raw', 32)
            if type(fallback) is not bool or reason is not None:
                raise ValueError(f"{field}.selection available lineage is incomplete")
        elif (selected['status'] != 'unavailable' or selected_raw is not None or fallback is not None
              or not isinstance(reason, str) or not reason):
            raise ValueError(f"{field}.selection unavailable lineage requires nulls and reason")
        rows.append({
            'side_index': index,
            'current_roll_points': _signed(side['current_roll_points'], f'{field}.current_roll_points', 32),
            'selected_character_id_raw': _signed(side['selected_character_id_raw'], f'{field}.selected_character_id_raw', 32),
            'selection': {'status': selected['status'], 'resolved_character_id_raw': selected_raw,
                          'used_native_fallback': fallback, 'unavailable_reason': reason},
            'relation': _component(side['relation'], field=f'{field}.relation', name='kind_raw', bits=32),
            'commander': _component(side['commander'], field=f'{field}.commander', name='total_raw', bits=64),
            'side_aggregate': _component(side['side_aggregate'], field=f'{field}.side_aggregate', name='total_raw', bits=64),
        })
    return {'scale': 100000, 'sides': rows}
