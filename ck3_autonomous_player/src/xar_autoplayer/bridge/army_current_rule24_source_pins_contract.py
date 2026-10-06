"""Strict optional inventory of the actual borrowed inline Rule24 source pins."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_roster_admission_contract import _typed as _native_typed

_FIELDS = {
    'status': 'string', 'unavailable_reason': 'string', 'schema_version': 'i32=1',
    'source': 'string=native_current_rule24_source_pins',
    'pins_captured_ready': 'bool', 'provider_array_borrowed': 'bool=true',
    'rule_receiver_identity': 'identity', 'rule_vtable_identity': 'identity?',
    'condition_mode_raw_u8': 'u8?',
    'expected_scope_function_identity': 'identity?', 'expected_scope_function_rva': 'u32?',
    'scope_mask_function_identity': 'identity?', 'scope_mask_function_rva': 'u32?',
    'rule_evaluator_function_identity': 'identity?', 'rule_evaluator_function_rva': 'u32?',
    'vtable_read_ready': 'bool', 'mode_read_ready': 'bool',
    'expected_scope_pin_read_ready': 'bool', 'scope_mask_pin_read_ready': 'bool',
    'rule_evaluator_pin_read_ready': 'bool',
    'pin_requested_bytes_u32': 'u32', 'pin_captured_bytes_u32': 'u32',
    'native_calls_executed': 'u32=0', 'native_writes_executed': 'u32=0',
}


def normalize_current_rule24_source_pins_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'rule24_source_pins_v1'
    if type(value) is not dict or set(value) != set(_FIELDS):
        raise ValueError(f'{name} schema is malformed')
    for field, kind in _FIELDS.items():
        _native_typed(value[field], kind, name + '.' + field)
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError(f'{name}.status is malformed')
    if (value['pins_captured_ready'] != (value['status'] == 'available')
            or value['pins_captured_ready'] == bool(value['unavailable_reason'])):
        raise ValueError(f'{name} status/readiness/reason disagree')
    from ..simulation.army_current_rule24_source_pins_12003 import validate_current_rule24_source_pins_declared_12003
    validate_current_rule24_source_pins_declared_12003(value)
    return deepcopy(value)
