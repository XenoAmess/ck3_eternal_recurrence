"""Expose independent actual current allocator inputs without predicting a tick."""
from __future__ import annotations

from copy import deepcopy


def project_current_daily_assault_placement_inputs_v1(table: dict | None) -> dict:
    result = {
        'schema_version': 1, 'source': 'observed_current_daily_assault_placement_inputs',
        'stage': 'observed_current_daily_assault_table', 'status': 'unavailable',
        'allocator_witnesses_ready': False, 'current_raw_table_ready': False,
        'groups': [], 'missing_inputs': [], 'actual_next_callback_ready': False,
        'full_future_table_placement_ready': False, 'full_daily_assault_ready': False,
        'admission_replayed': False, 'native_writes_executed': 0,
    }
    if table is None:
        result['missing_inputs'] = ['current_daily_assault_table_v1']
        return result
    result['current_raw_table_ready'] = table['raw_groups_ready']
    complete = True
    for group in table['groups']:
        row = {'native_index': group['native_index'], 'physical_slot_i64': group['physical_slot_i64'],
               'siege_full_id_u32': group['siege_full_id_u32'],
               'armies_allocator_witness': deepcopy(group['armies'].get('allocator_witness')),
               'arrgs_allocator_witness': deepcopy(group['arrgs'].get('allocator_witness'))}
        row['allocator_witnesses_ready'] = all(
            row[name] is not None and row[name]['ready']
            for name in ('armies_allocator_witness', 'arrgs_allocator_witness'))
        row['matched_transfer_inputs_ready'] = row['allocator_witnesses_ready'] and all(
            row[name]['matches_expected'] is True
            for name in ('armies_allocator_witness', 'arrgs_allocator_witness'))
        complete = complete and row['allocator_witnesses_ready']
        result['groups'].append(row)
        for name in ('armies_allocator_witness', 'arrgs_allocator_witness'):
            witness = row[name]
            if witness is None or not witness['ready']:
                result['missing_inputs'].append(
                    f"slot{group['physical_slot_i64']}.{name}:" +
                    ('not_observed' if witness is None else witness['unavailable_reason']))
    empty = table['header']['occupied_count_raw_i32'] == 0 and not table['groups']
    result['allocator_witnesses_ready'] = complete and (empty or table['physical_scan_ready'])
    result['status'] = 'available' if result['allocator_witnesses_ready'] else 'partial'
    return result
