"""Optional actual vector headers needed by the .3 normal-return release seam."""
from __future__ import annotations

from copy import deepcopy

_FIELDS = {'status', 'ready', 'unavailable_reason', 'data_present', 'data_identity',
           'count_raw_i32', 'capacity_raw_i32'}


def normalize_daily_assault_release_header_v1(value: object) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError('daily_assault_release_header_v1 schema is malformed')
    if value['status'] not in ('available', 'partial', 'unavailable') or type(value['ready']) is not bool:
        raise ValueError('daily_assault_release_header_v1 status is malformed')
    if value['unavailable_reason'] is not None and not isinstance(value['unavailable_reason'], str):
        raise ValueError('daily_assault_release_header_v1 unavailable reason is malformed')
    present = value['data_present']
    if present is not None and type(present) is not bool:
        raise ValueError('daily_assault_release_header_v1 data presence is malformed')
    identity = value['data_identity']
    if identity is not None and not isinstance(identity, str):
        raise ValueError('daily_assault_release_header_v1 data identity is malformed')
    for name in ('count_raw_i32', 'capacity_raw_i32'):
        number = value[name]
        if number is not None and (type(number) is not int or not -(1 << 31) <= number < (1 << 31)):
            raise ValueError(f'daily_assault_release_header_v1 {name} is malformed')
    return deepcopy(value)
