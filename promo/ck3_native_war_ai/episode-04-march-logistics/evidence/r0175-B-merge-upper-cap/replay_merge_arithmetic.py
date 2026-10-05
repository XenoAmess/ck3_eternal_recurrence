"""Offline replay of one pinned merge window; no native, SDK or media imports."""
from pathlib import Path
import argparse
import ast
import hashlib
import json

HELPER_SHA = '529bf4f1f6f97a52b0ba51f67a47aa79f97c2a10570946f3ac1be2ff139e07ca'
FUNCTION_SHA = '12ed9c53ad2f92a6ea8974a2af47da618112c049816eb9f0ab57ae9d02bf42bf'

def need(condition, message):
    if not condition:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def source_function(helper_bytes):
    need(digest(helper_bytes) == HELPER_SHA, 'frozen original helper hash mismatch')
    text = helper_bytes.decode('utf-8-sig')
    module = ast.parse(text)
    matches = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'weighted_supply']
    need(len(matches) == 1, 'weighted_supply function ambiguous')
    function = matches[0]
    segment = ast.get_source_segment(text, function)
    need(digest(segment.encode('utf-8')) == FUNCTION_SHA, 'exact weighted_supply function hash mismatch')
    # Only this pinned pure function is compiled. No module imports/top-level runner execute.
    scope = {'need': need}
    isolated = ast.Module(body=[function], type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), '<pinned-weighted_supply-only>', 'exec'), scope)
    return scope['weighted_supply'], segment

def load_sources(package):
    index = json.loads((package / 'source-index.json').read_bytes())
    sources = {}
    for row in index['files']:
        relative = Path(row['path'])
        need(not relative.is_absolute() and '..' not in relative.parts, 'source must be package-relative')
        raw = (package / relative).read_bytes()
        need(len(raw) == row['bytes'] and digest(raw) == row['sha256'], 'source bytes/hash mismatch: ' + row['id'])
        need(row['id'] not in sources, 'duplicate source id')
        sources[row['id']] = raw if row['id'] == 'original-helper' else json.loads(raw)
    return index, sources

def full_cohort(rows):
    regiments, records = {}, {}
    for army in rows:
        for row in army['regiment_strengths']:
            key = row['army_regiment_id']
            need(key not in regiments, 'duplicate regiment identity')
            regiments[key] = row
        for group in army['regiment_replenishment_records_v1']:
            for row in group['records']:
                key = (group['army_regiment_id'], row['record_index'], row['persistent_regiment_id'], row['chunk_index'])
                need(key not in records, 'duplicate DATA identity')
                records[key] = row
    return regiments, records

def current_commander(packet):
    value = packet['army_commander_candidates']['current_commander']
    need(value['status'] == 'available', 'commander unavailable')
    return value['character_id']

def replay(package):
    index, source = load_sources(package)
    function, _ = source_function(source['original-helper'])
    initial = source['pre-observation']
    fresh = source['fresh-post-observation']
    pre = {row['army_id']: row for row in initial['health']['army_strengths']}
    post_rows = source['post-health']['army_strengths']
    fresh_rows = fresh['health']['army_strengths']
    need(set(pre) == {0, 204} and len(post_rows) == len(fresh_rows) == 1, 'actual source/destination scope differs')
    D, S, after = pre[0], pre[204], post_rows[0]
    need(after['army_id'] == fresh_rows[0]['army_id'] == 0, 'post destination differs')
    for key in ('current_soldiers', 'maximum_soldiers', 'current_supply_raw', 'current_supply_capacity_raw'):
        need(after[key] == fresh_rows[0][key], 'fresh readback differs: ' + key)
    dates = [obj[label]['date_raw'] for obj in (initial, fresh) for label in ('before', 'after')]
    need(dates == [53149344] * 4, 'actual dates differ')
    need(all(obj[label]['paused'] is True for obj in (initial, fresh) for label in ('before', 'after')), 'endpoint pause unknown')
    need(all(obj[label]['episode_run_id'] == 'native-33388-23726fbd8a80' for obj in (initial, fresh) for label in ('before', 'after')), 'episode differs')
    arithmetic = function(D, S, after['current_supply_capacity_raw'])
    need(arithmetic['expected_post_stock_raw'] == after['current_supply_raw'], 'arithmetic does not match actual stock')
    before_reg, before_data = full_cohort([D, S])
    after_reg, after_data = full_cohort([after])
    fresh_reg, fresh_data = full_cohort(fresh_rows)
    need(after_reg == fresh_reg and after_data == fresh_data, 'fresh full-cohort readback differs')
    missing = sorted(set(before_reg) - set(after_reg))
    added = sorted(set(after_reg) - set(before_reg))
    original_diff = [key for key in sorted(before_reg) if key in after_reg and before_reg[key] != after_reg[key]]
    old_commander = current_commander(source['pre-commander-0'])
    source_commander = current_commander(source['pre-commander-204'])
    new_commander = current_commander(source['fresh-post-commander-0'])
    action = source['merge-command']['war_action']
    need(action['destination_army_id'] == 0 and action['source_army_id'] == 204 and action['status'] == 'merge_applied', 'action roles differ')
    need(action['submitted_date_raw'] == action['observed_date_raw'] == dates[0], 'action/date binding differs')
    return {
        'schema': 'ck3.e04.B-merge-offline-replay.v1',
        'status': 'ACTUAL_UPPER_CAP_WINDOW_REPLAY_MATCHES_NOT_FROZEN_B_PASS',
        'source_files': index['files'],
        'date_raw': dates[0], 'days_from_common_T0': (dates[0] - 53148432) // 24,
        'common_T0_raw': 53148432, 'absolute_END_raw': 53150592, 'budget_reset': False,
        'endpoint_game_days_advanced': 0, 'endpoint_paused': True,
        'frame': {'before': initial['before']['snapshot_id'], 'after': fresh['after']['snapshot_id']},
        'roles': {'destination_public_id': 0, 'source_public_id': 204,
                  'D_current_soldiers': D['current_soldiers'], 'S_current_soldiers': S['current_soldiers'],
                  'D_actual_native_weight_raw': D['merge_supply_destination_weight_raw'],
                  'S_current_role_weight_raw': S['current_soldiers'] * 100000,
                  'S_destination_getter_not_used_raw': S['merge_supply_destination_weight_raw'],
                  'D_stock_raw': D['current_supply_raw'], 'S_stock_raw': S['current_supply_raw'],
                  'pre_capacities_raw': [D['current_supply_capacity_raw'], S['current_supply_capacity_raw']]},
        'arithmetic': arithmetic,
        'observed_post_stock_raw': after['current_supply_raw'],
        'observed_post_capacity_raw': after['current_supply_capacity_raw'],
        'upper_cap_observed_this_window': arithmetic['preclamp_raw'] > after['current_supply_capacity_raw'] and arithmetic['expected_post_stock_raw'] == after['current_supply_raw'],
        'cohort': {'pre_regiments': len(before_reg), 'post_regiments': len(after_reg),
                   'pre_DATA': len(before_data), 'post_DATA': len(after_data),
                   'missing_original_regiment_ids': missing, 'added_regiment_rows': [after_reg[key] for key in added],
                   'original_regiment_entire_row_diff_ids': original_diff,
                   'added_DATA_identities': [list(key) for key in sorted(set(after_data) - set(before_data))],
                   'missing_DATA_identities': [list(key) for key in sorted(set(before_data) - set(after_data))],
                   'DATA_entire_row_diff_identities': [list(key) for key in sorted(before_data) if key in after_data and before_data[key] != after_data[key]],
                   'pre_soldier_current_max': [D['current_soldiers'] + S['current_soldiers'], D['maximum_soldiers'] + S['maximum_soldiers']],
                   'post_soldier_current_max': [after['current_soldiers'], after['maximum_soldiers']],
                   'frozen_27_regiment_gate_pass': False},
        'commander': {'pre_destination': old_commander, 'pre_source': source_commander, 'post_destination': new_commander,
                      'frozen_destination_commander_gate_pass': new_commander == old_commander},
        'cause_of_new_regiment_or_commander_change': None,
        'new_regiment_is_knight': None, 'applied_update_payment_loss_refill_ledger': None,
        'Root_formal_B_terminal': None, 'B_London': None, 'C_terminal': None, 'winner': None,
        'human_signoff': False, 'TTS_media_SDK_GUI_Game_calls': 0,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', required=True, type=Path, help='New append-only JSON output file')
    args = parser.parse_args()
    result = replay(args.package)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with args.output.open('xb') as stream:
        stream.write(raw)
    print(json.dumps({'output': str(args.output), 'bytes': len(raw), 'sha256': digest(raw),
                      'status': result['status'], 'arithmetic': result['arithmetic']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
