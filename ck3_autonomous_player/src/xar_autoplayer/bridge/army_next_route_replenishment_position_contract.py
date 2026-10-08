"""Same-query actual first-route Province position verdict for exact1.20.0.4."""
from __future__ import annotations

_SOURCE = 'native_current_next_route_replenishment_position_12004'
_INTS = ('route_source_count', 'current_province_id', 'first_target_province_id',
         'owner_requested_full_id', 'owner_resolved_full_id',
         'holder_requested_full_id', 'holder_resolved_full_id')
_BOOLS = ('owner_used_fallback', 'holder_used_fallback', 'native_owner_holder_eligible',
          'native_first_target_position_eligible')
_KEYS = {'source', 'status', 'unavailable_reason', 'unit_full_id', 'route_read_status',
         'route_province_ids', 'first_target_province_magic_raw', *_INTS, *_BOOLS}


def _integer(value: object, *, nullable: bool = True, unsigned: bool = False) -> None:
    if value is None and nullable:
        return
    low, high = (0, 1 << 32) if unsigned else (-(1 << 31), 1 << 31)
    if type(value) is not int or not low <= value < high:
        raise ValueError('next-route replenishment integer is malformed')


def normalize_next_route_replenishment_position_inputs_v1(
    value: object, *, expected_unit_full_id: int,
) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS or value['source'] != _SOURCE:
        raise ValueError('next-route replenishment position schema is malformed')
    if value['status'] not in {'available', 'not_applicable', 'unavailable'}:
        raise ValueError('next-route replenishment status is malformed')
    reason = value['unavailable_reason']
    if reason is not None and (type(reason) is not str or not reason):
        raise ValueError('next-route replenishment reason is malformed')
    _integer(value['unit_full_id'], nullable=False)
    if value['unit_full_id'] != expected_unit_full_id:
        raise ValueError('next-route replenishment Unit is outside the same row')
    if value['route_read_status'] not in {'not_attempted', 'complete_empty',
            'complete_nonempty', 'target_only', 'invalid_header', 'unresolved_entry'}:
        raise ValueError('next-route replenishment route status is malformed')
    for key in _INTS:
        _integer(value[key])
    _integer(value['first_target_province_magic_raw'], unsigned=True)
    for key in _BOOLS:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError('next-route replenishment Boolean is malformed')
    route = value['route_province_ids']
    if not isinstance(route, list):
        raise ValueError('next-route replenishment route is malformed')
    for identity in route:
        _integer(identity, nullable=False)
    if value['route_read_status'] == 'complete_nonempty':
        if not route or value['route_source_count'] != len(route):
            raise ValueError('next-route replenishment complete route is malformed')
        if value['first_target_province_id'] != route[0]:
            raise ValueError('next-route replenishment target is not actual route[0]')
    if value['route_read_status'] == 'complete_empty' and (
            route or value['route_source_count'] != 0):
        raise ValueError('next-route replenishment empty route is malformed')
    if value['status'] == 'not_applicable' and value['route_read_status'] != 'complete_empty':
        raise ValueError('next-route replenishment absence is unproven')
    if value['status'] == 'available':
        if (value['route_read_status'] != 'complete_nonempty'
                or value['first_target_province_magic_raw'] is None
                or value['native_first_target_position_eligible'] is None):
            raise ValueError('next-route replenishment available verdict is incomplete')
        if value['first_target_province_magic_raw'] != 0x50726F76:
            if value['native_first_target_position_eligible'] is not False:
                raise ValueError('invalid target Province cannot admit replenishment')
        elif (any(value[key] is None for key in ('owner_resolved_full_id',
                'holder_resolved_full_id', 'owner_used_fallback', 'holder_used_fallback',
                'native_owner_holder_eligible'))
                or value['native_owner_holder_eligible'] != value['native_first_target_position_eligible']):
            raise ValueError('next-route replenishment actual political operands are incomplete')
    return {**value, 'route_province_ids': list(route)}
