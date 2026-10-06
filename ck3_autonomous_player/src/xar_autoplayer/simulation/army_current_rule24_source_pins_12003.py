"""Pure presentation of current Rule24 pins; inventory does not invoke targets."""
from __future__ import annotations

from copy import deepcopy

_PIN_FIELDS = (
    ('expected_scope', 'expected_scope_pin_read_ready'),
    ('scope_mask', 'scope_mask_pin_read_ready'),
    ('rule_evaluator', 'rule_evaluator_pin_read_ready'),
)
_READ_FLAGS = ('vtable_read_ready', 'mode_read_ready',
               'expected_scope_pin_read_ready', 'scope_mask_pin_read_ready',
               'rule_evaluator_pin_read_ready')


def validate_current_rule24_source_pins_declared_12003(value: dict) -> bool:
    for flag, field in (('vtable_read_ready', 'rule_vtable_identity'),
                        ('mode_read_ready', 'condition_mode_raw_u8')):
        if value[flag] != (value[field] is not None):
            raise ValueError('Rule24 captured value/read status disagree')
    for prefix, flag in _PIN_FIELDS:
        identity, rva = value[prefix + '_function_identity'], value[prefix + '_function_rva']
        if value[flag] != (identity is not None) or (not value[flag] and rva is not None):
            raise ValueError('Rule24 function pin lost its actual read status/identity')
    vtable_nonnull = value['vtable_read_ready'] and value['rule_vtable_identity'] != 'native:0'
    if not vtable_nonnull and any(value[flag] for _, flag in _PIN_FIELDS):
        raise ValueError('Rule24 missing/null vtable relabeled undemanded virtual slots')
    expected_requested = 9 + (24 if vtable_nonnull else 0)
    expected_captured = (8 if value['vtable_read_ready'] else 0) + (1 if value['mode_read_ready'] else 0)
    expected_captured += sum(8 for _, flag in _PIN_FIELDS if value[flag])
    if (value['pin_requested_bytes_u32'] != expected_requested
            or value['pin_captured_bytes_u32'] != expected_captured
            or not 0 <= value['pin_captured_bytes_u32'] <= value['pin_requested_bytes_u32'] <= 33):
        raise ValueError('Rule24 pin byte accounting disagrees with demanded reads')
    ready = all(value[flag] for flag in _READ_FLAGS)
    if value['pins_captured_ready'] != ready:
        raise ValueError('Rule24 inventory readiness disagrees with captured pins')
    if value['native_calls_executed'] != 0 or value['native_writes_executed'] != 0:
        raise ValueError('Rule24 source pin capture cannot claim native target invocation or writes')
    return True


def project_current_rule24_source_pins_12003(value: dict | None, *, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_rule24_source_pins',
        'stage': 'observed_current_rule24_source_pins', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'rule24_source_pins_unavailable',
        'pins_captured_ready': False, 'source_provenance': deepcopy(source_provenance),
        'observed_current_rule24_source_pins': deepcopy(value),
        'native_calls_executed': 0, 'native_writes_executed': 0,
    }
    if value is None:
        return result
    validate_current_rule24_source_pins_declared_12003(value)
    result.update(status=value['status'], ready=value['pins_captured_ready'],
                  unavailable_reason=None if value['pins_captured_ready'] else value['unavailable_reason'],
                  pins_captured_ready=value['pins_captured_ready'])
    for field in ('provider_array_borrowed', 'rule_receiver_identity', 'rule_vtable_identity',
                  'condition_mode_raw_u8', 'vtable_read_ready', 'mode_read_ready',
                  'expected_scope_pin_read_ready', 'scope_mask_pin_read_ready', 'rule_evaluator_pin_read_ready',
                  'pin_requested_bytes_u32', 'pin_captured_bytes_u32'):
        result[field] = deepcopy(value[field])
    for prefix, _ in _PIN_FIELDS:
        result[prefix + '_function_identity'] = value[prefix + '_function_identity']
        result[prefix + '_function_rva'] = value[prefix + '_function_rva']
    return result
