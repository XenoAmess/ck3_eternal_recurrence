"""Actual physical current groups and independent held initial denominators."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


def _wrap32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def project_current_daily_assault_group_inputs_v1(army: Mapping) -> dict:
    """Expose complete global current groups without replaying any native write."""
    result = {
        'source_contract_game_version': '1.20.0.3',
        'queried_army_id': army.get('army_id'),
        'stage': 'observed_current_daily_assault_table',
        'manager_scope': 'shared_primary_manager_current_table',
        'input_basis': 'held_current_physical_groups; no_earlier_group_writes_replayed',
        'status': 'unavailable', 'current_group_inputs_ready': False,
        'raw_groups_ready': False, 'physical_group_order_ready': False,
        'current_empty': False, 'manager_identity': None, 'header': None,
        'groups': [], 'missing_inputs': [],
        'actual_daily_loss': False, 'native_writes_executed': 0,
        'pre_date_preparation_replayed': False, 'future_table_placement_ready': False,
        'full_daily_assault_ready': False,
    }
    leaf = army.get('current_daily_assault_table_v1')
    if not isinstance(leaf, Mapping):
        result['missing_inputs'] = ['current_daily_assault_table_v1']
        return result
    empty = leaf['header']['occupied_count_raw_i32'] == 0 and not leaf['groups']
    groups = []
    missing = []
    for observed in leaf['groups']:
        group = deepcopy(dict(observed))
        running = 0
        prefix_ready = True
        ledger = []
        for occurrence in observed['arrgs']['occurrences']:
            ready = occurrence['ready']
            contribution = (occurrence['current_raw_i32'] if occurrence['denominator_included'] else 0) if ready else None
            before = running
            before_ready = prefix_ready
            if contribution is not None:
                running = _wrap32(running + contribution)
            else:
                prefix_ready = False
            ledger.append({
                'native_index': occurrence['native_index'],
                'raw_full_id_u32': occurrence['raw_full_id_u32'],
                'object_identity': occurrence['resolution']['object_identity'],
                'ready': ready, 'included': occurrence['denominator_included'],
                'current_raw_i32': occurrence['current_raw_i32'],
                'contribution_i32': contribution, 'running_before_i32': before if before_ready else None,
                'running_after_i32': running if prefix_ready else None,
                'unavailable_reason': occurrence['unavailable_reason'],
            })
        group['initial_group_denominator_ready'] = observed['denominator_ready']
        group['observed_initial_eligible_current_soldiers_i32'] = running if observed['denominator_ready'] else None
        group['initial_denominator_occurrences'] = ledger
        if not observed['ready']:
            missing.append({'physical_slot_i64': observed['physical_slot_i64'],
                            'reason': observed['unavailable_reason']})
        groups.append(group)
    if not leaf['raw_groups_ready']:
        missing.append('complete_current_physical_groups_and_reference_lists')
    if not leaf['ready'] and leaf['unavailable_reason']:
        missing.append(leaf['unavailable_reason'])
    return {
        **result, 'status': leaf['status'], 'current_group_inputs_ready': leaf['ready'],
        'raw_groups_ready': leaf['raw_groups_ready'],
        'physical_group_order_ready': bool(leaf['physical_scan_ready'] or (empty and leaf['raw_groups_ready'])),
        'current_empty': empty, 'manager_identity': leaf['manager_identity'],
        'header': deepcopy(leaf['header']), 'groups': groups, 'missing_inputs': missing,
    }


def project_current_daily_assault_group_inputs_many_v1(armies: list[dict]) -> list[dict]:
    return [project_current_daily_assault_group_inputs_v1(army) for army in armies]
