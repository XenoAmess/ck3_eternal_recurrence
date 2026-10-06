"""Actual readonly allocator witnesses used by the source-bound placement model."""
from __future__ import annotations

from copy import deepcopy

FIELDS = {'status', 'ready', 'unavailable_reason', 'actual_read_ready',
          'actual_identity', 'expected_identity', 'expected_rva_u32', 'matches_expected'}
ARMY_ALLOCATOR_RVA = 0x54E0570
ARRG_ALLOCATOR_RVA = 0x54DEB68


def normalize_daily_assault_allocator_witness_v1(value: object, *, arrg: bool) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('daily assault allocator witness schema is malformed')
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError('daily assault allocator witness status is malformed')
    for name in ('ready', 'actual_read_ready'):
        if type(value[name]) is not bool:
            raise ValueError(f'daily assault allocator witness {name} must be bool')
    for name in ('actual_identity', 'expected_identity', 'unavailable_reason'):
        if value[name] is not None and (type(value[name]) is not str or not value[name]):
            raise ValueError(f'daily assault allocator witness {name} is malformed')
    expected = ARRG_ALLOCATOR_RVA if arrg else ARMY_ALLOCATOR_RVA
    if type(value['expected_rva_u32']) is not int or value['expected_rva_u32'] != expected:
        raise ValueError('daily assault allocator witness expected source RVA differs')
    if value['actual_read_ready'] != (value['actual_identity'] is not None):
        raise ValueError('daily assault allocator witness actual read differs from identity')
    ready = value['actual_read_ready'] and value['expected_identity'] is not None
    if value['ready'] != ready or (value['status'] == 'available') != ready:
        raise ValueError('daily assault allocator witness read readiness is malformed')
    match = value['matches_expected']
    if match is not None and type(match) is not bool:
        raise ValueError('daily assault allocator witness match must be bool or null')
    expected_match = value['actual_identity'] == value['expected_identity'] if ready else None
    if match != expected_match:
        raise ValueError('daily assault allocator witness match differs from actual identities')
    if (value['unavailable_reason'] is None) != ready:
        raise ValueError('daily assault allocator witness diagnostic differs from readiness')
    return deepcopy(value)
