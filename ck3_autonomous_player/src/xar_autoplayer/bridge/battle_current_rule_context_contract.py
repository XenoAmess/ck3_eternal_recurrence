"""Current retained-rule scale/exclusion operands; no historical append claim."""
from __future__ import annotations


def _signed(value, field, bits):
    if value is not None and (type(value) is not int or not -(1 << (bits-1)) <= value < (1 << (bits-1))):
        raise ValueError(f'{field} must be signed int{bits} or null')
    return value


def _boolean(value, field):
    if value is not None and type(value) is not bool:
        raise ValueError(f'{field} must be bool or null')
    return value


def normalize_current_rule_context_v1(value, *, holding_defender, effects, field):
    if not isinstance(value, dict) or set(value) != {'holding_multiplier', 'commander_exclusion'}:
        raise ValueError(f'{field} must contain the current rule context fields')
    holding = value['holding_multiplier']
    commander = value['commander_exclusion']
    if not isinstance(holding, dict) or set(holding) != {
        'status', 'scale', 'province_multiplier_raw', 'province_has_holding',
        'holding_modifier_raw', 'unavailable_reason',
    }:
        raise ValueError(f'{field}.holding_multiplier has invalid fields')
    if type(holding['scale']) is not int or holding['scale'] != 100000:
        raise ValueError(f'{field}.holding_multiplier.scale must be 100000')
    province = _signed(holding['province_multiplier_raw'], field+'.province_multiplier_raw', 64)
    modifier = _signed(holding['holding_modifier_raw'], field+'.holding_modifier_raw', 64)
    has_holding = _boolean(holding['province_has_holding'], field+'.province_has_holding')
    if not isinstance(commander, dict) or set(commander) != {
        'status', 'selected_character_id_raw', 'used_native_fallback',
        'defender_adjacency_excluded', 'unavailable_reason',
    }:
        raise ValueError(f'{field}.commander_exclusion has invalid fields')
    selected = _signed(commander['selected_character_id_raw'], field+'.selected_character_id_raw', 32)
    fallback = _boolean(commander['used_native_fallback'], field+'.used_native_fallback')
    excluded = _boolean(commander['defender_adjacency_excluded'], field+'.defender_adjacency_excluded')
    if selected is None:
        raise ValueError(f'{field}.selected_character_id_raw must be observed')
    for name, row in (('holding_multiplier', holding), ('commander_exclusion', commander)):
        status, reason = row['status'], row['unavailable_reason']
        if status not in ('available', 'not_applicable', 'unavailable'):
            raise ValueError(f'{field}.{name}.status is invalid')
        if status == 'unavailable':
            if not isinstance(reason, str) or not reason:
                raise ValueError(f'{field}.{name} unavailable reason missing')
        elif reason is not None:
            raise ValueError(f'{field}.{name} available reason must be null')
    if holding['status'] == 'available':
        if holding_defender is not True or province is None or has_holding is None:
            raise ValueError(f'{field}.holding_multiplier available operands missing')
        if (has_holding and modifier is None) or (not has_holding and modifier is not None):
            raise ValueError(f'{field}.holding_multiplier modifier branch disagrees')
    elif holding['status'] == 'not_applicable':
        if holding_defender is not False or any(x is not None for x in (province, has_holding, modifier)):
            raise ValueError(f'{field}.holding_multiplier inactive branch disagrees')
    defender_status = effects['rows'][1]['status'] if effects and len(effects['rows']) == 3 else None
    if commander['status'] == 'available':
        if defender_status != 'available' or fallback is None or excluded is None:
            raise ValueError(f'{field}.commander_exclusion selected effect/flag missing')
    elif commander['status'] == 'not_applicable':
        if defender_status != 'not_selected' or fallback is not None or excluded is not None:
            raise ValueError(f'{field}.commander_exclusion inactive branch disagrees')
    return {'holding_multiplier': dict(holding), 'commander_exclusion': dict(commander)}
