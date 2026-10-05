"""Exact extracted pure functions from pinned Root paired driver; no driver imports."""

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def stationary(row, target):
    return (row.get('current_province_id') == target and row.get('route_read_status') == 'complete_empty'
            and row.get('route_province_ids') == [] and row.get('army_state') == 'regular'
            and row.get('in_combat') is False and row.get('retreating') is False)

def sites(pair):
    return stationary(pair['main_roster'], 2174) and stationary(pair['child_roster'], 2327)

def positive(pair):
    return sites(pair) and all(pair[role]['current_supply_change_monthly_raw'] > 0 for role in ['main', 'child'])

def window(left, right):
    need(set(left['regiments']) == set(right['regiments']) and set(left['DATA']) == set(right['DATA']), 'Window cohort FullID/DATA identities changed')
    for group in ['regiments', 'DATA']:
        for key in left[group]:
            need(left[group][key]['maximum_soldiers'] == right[group][key]['maximum_soldiers'], 'Window maximum changed')
    a, b = left['snapshot']['date_raw'], right['snapshot']['date_raw']
    eligible = positive(left) and positive(right) and b >= a
    result = {'pair_dates_raw': [a, b], 'both_stationary_positive_before_after': eligible,
              'main_window_success': False, 'child_window_success': False,
              'applied_refill_loss_payment_ledger': None, 'complete_source_window_credit_only': True}
    for role in ['main', 'child']:
        x, y = left[role], right[role]
        cx, cy = x['army_update_clock_v1'], y['army_update_clock_v1']
        need(x['army_id'] == y['army_id'] and x['native_carmy_id'] == y['native_carmy_id'], 'Window native/public identity changed')
        scale = x['current_supply_scale']
        need(scale == y['current_supply_scale'] == x['current_supply_capacity_scale'] == y['current_supply_capacity_scale'], 'Window stock/cap scale differs')
        cap_stable = x['current_supply_capacity_raw'] == y['current_supply_capacity_raw']
        stamp_changed = (cx['last_supply_update_date_storage_raw64'] != cy['last_supply_update_date_storage_raw64']
                         and cx['last_supply_update_date_raw'] < cy['last_supply_update_date_raw']
                         and a <= cy['last_supply_update_date_raw'] <= b)
        delta = y['current_supply_raw'] - x['current_supply_raw']
        result[role] = {'public': y['army_id'], 'native': y['native_carmy_id'],
                        'stock_before': x['current_supply_raw'], 'stock_after': y['current_supply_raw'], 'delta_raw': delta,
                        'cap_before': x['current_supply_capacity_raw'], 'cap_after': y['current_supply_capacity_raw'], 'scale': scale,
                        'monthly_before': x['current_supply_change_monthly_raw'], 'monthly_after': y['current_supply_change_monthly_raw'],
                        '+188_storage': [cx['last_supply_update_date_storage_raw64'], cy['last_supply_update_date_storage_raw64']],
                        '+188_date_raw': [cx['last_supply_update_date_raw'], cy['last_supply_update_date_raw']],
                        '+190_storage': [cx['grace_anchor_date_storage_raw64'], cy['grace_anchor_date_storage_raw64']],
                        'mark188_changed_inside_observed_window': stamp_changed}
        result[role + '_window_success'] = bool(eligible and cap_stable and stamp_changed and
            ((x['current_supply_raw'] < x['current_supply_capacity_raw'] and delta > 0) if role == 'main'
             else (x['current_supply_raw'] >= x['current_supply_capacity_raw'] and y['current_supply_raw'] == y['current_supply_capacity_raw'])))
    result['actual_current_sum_before'] = sum(left[r]['current_soldiers'] for r in ['main', 'child'])
    result['actual_current_sum_after'] = sum(right[r]['current_soldiers'] for r in ['main', 'child'])
    result['Regiment_entire_row_diffs'] = [{'FullID': key, 'before': left['regiments'][key], 'after': right['regiments'][key]} for key in left['regiments'] if left['regiments'][key] != right['regiments'][key]]
    result['DATA_entire_row_diffs'] = [{'identity': list(key), 'before': left['DATA'][key], 'after': right['DATA'][key]} for key in left['DATA'] if left['DATA'][key] != right['DATA'][key]]
    result['prepared_or_permission_change_is_integer_refill_credit'] = False
    return result
