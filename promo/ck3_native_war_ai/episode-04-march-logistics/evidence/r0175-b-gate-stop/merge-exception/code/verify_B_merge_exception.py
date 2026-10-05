"""Record a completed merge exception, never grant frozen-cohort PASS. JSON only."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
EPISODE = 'native-33388-23726fbd8a80'


def need(value, reason):
    if not value:
        raise ValueError(reason)


def read(relative, expected=None):
    path = (HERE / relative).resolve(strict=True)
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py', '.txt'}, 'relative bounded evidence leaf')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'small JSON/code source only')
    if expected:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'original source bytes/SHA mismatch')
    return json.loads(raw) if path.suffix == '.json' else raw


def module(relative, name):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def context(frame):
    need(frame['episode_run_id'] == EPISODE and frame['date_raw'] == 53149344
         and frame['paused'] is True and frame['map_ready'] is True, 'actual paused B+38 frame')
    need(frame['played_character']['character_id'] == 33388 and frame['played_character']['alive'] is True
         and frame['active_event'] is None and frame['pending_character_interaction'] is None, 'actual actor/events')
    need(frame['diagnostics']['bridge_pid'] == 19560
         and frame['diagnostics']['pipe_name'] == r'\\.\pipe\ck3-e04-r0175-20261006-a02', 'same actual B game/pipe')


def health(query, frame):
    need(query['accepted'] is True and query['status'] == 'available', 'available actual source health')
    for field in ('snapshot_id', 'revision', 'native_revision'):
        need(query['queried_' + field] == frame[field], 'health own query bracket/' + field)
    for field in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'paused'):
        need(query['source'][field] == frame[field], 'health own source bracket/' + field)
    roster = {row['army_id']: row for row in frame['player_armies']}
    rows = {row['army_id']: row for row in query['army_strengths']}
    need(set(rows) == set(roster), 'fresh actual roster/health join')
    regs, records, groups = {}, {}, {}
    for aid, row in rows.items():
        army = roster[aid]
        need(row['status'] == 'available' and army['owner_character_id'] == 33388
             and army['controllable'] is True and army['in_combat'] is False and army['retreating'] is False
             and army['current_province_id'] == 2174 and army['army_state'] == 'regular'
             and army['route_province_ids'] == [] and army['route_read_status'] == 'complete_empty', 'actual stationary owner/control context')
        resolution = row['native_army_resolution_v1']
        need(resolution['status'] == 'available' and resolution['ready'] is True
             and resolution['entry_full_id'] == row['native_carmy_id'], 'actual resolved CArmy FullID')
        ids = set()
        for regiment in row['regiment_strengths']:
            key = str(regiment['army_regiment_id'])
            need(key not in regs, 'disjoint complete Regiment IDs')
            regs[key] = regiment
            ids.add(key)
        need(len(ids) == row['regiment_count'], 'actual full local Regiment count')
        need(sum(item['current_soldiers'] for item in row['regiment_strengths']) == row['current_soldiers']
             and sum(item['maximum_soldiers'] for item in row['regiment_strengths']) == row['maximum_soldiers'], 'regiment total current/max')
        group_ids = set()
        for group in row['regiment_replenishment_records_v1']:
            key = str(group['army_regiment_id'])
            need(key in ids and key not in groups and group['status'] == 'available' and group['ready'] is True
                 and group['source'] == 'native_all_data_records' and group['native_data_record_count'] == len(group['records']), 'complete DATA container including zero-record')
            groups[key] = group
            group_ids.add(key)
            for record in group['records']:
                identity = json.dumps([group['army_regiment_id'], record['record_index'], record['persistent_regiment_id'], record['chunk_index']], separators=(',', ':'))
                need(identity not in records and record['status'] == 'available', 'complete disjoint DATA identities')
                records[identity] = record
        need(group_ids == ids, 'all native regiments have readable DATA containers')
    return rows, regs, records, groups


def commander(query, frame, expected):
    body = query['army_commander_candidates']
    need(query['accepted'] is True and body['status'] == 'available', 'actual commander query available')
    for item in (query, body):
        need(item['date_raw'] == frame['date_raw'] and item['snapshot_revision'] == frame['native_revision'], 'commander own native bracket')
    if 'queried_revision' in query:
        for field in ('snapshot_id', 'revision', 'native_revision'):
            need(query['queried_' + field] == frame[field], 'commander own public bracket')
    need(body['army_id'] == body['native_carmy_id'] == 0 and body['owner_character_id'] == 33388
         and body['current_commander']['status'] == 'available' and body['current_commander']['character_id'] == expected, 'actual current Main commander')
    speed = body['current_movement_speed']
    need(speed['context_observable'] is True and speed['date_raw'] == frame['date_raw']
         and speed['snapshot_revision'] == frame['native_revision'] and speed['public_cunit_id'] == speed['native_carmy_id'] == 0
         and speed['current_commander_character_id'] == expected and speed['current_province_id'] == 2174,
         'actual commander native context')
    return body['current_commander']


def verify():
    for pin in read('manifest.json')['files']:
        read(pin['path'], pin)
    previous = read('qualified-rest/B-qualified-rest-values.json')
    need(previous['status'] == 'PASS_B_TWO_REST_NUMERIC_BRANCHES_OBSERVED_NO_TERMINAL', 'preserved independent rest evidence')
    reader = module('qualified-rest/intermediate/child-cap/code/paired_snapshot_reader.py', 'B_merge_pre_reader')
    pre = read('inputs/pre/observation.json')
    pre_commanders = {aid: read('inputs/pre/commander-' + str(aid) + '.json') for aid in (0, 204)}
    pre_view = reader.project(pre, pre_commanders)
    for frame in (pre['before'], pre['after']):
        context(frame)
    pre_rows, pre_regs, pre_records, _ = health(pre['health'], pre['before'])
    need(set(pre_rows) == {0, 204} and pre_rows[0]['current_soldiers'] == 3344 and pre_rows[204]['current_soldiers'] == 3345, 'actual pre pair current3344/3345')
    need(len(pre_regs) == 27 and len(pre_records) == 37 and sum(row['maximum_soldiers'] for row in pre_regs.values()) == 6747, 'actual pre27/37/max6747')
    raw_command = read('inputs/merge-response.json')
    action = raw_command['body']['war_action']
    need(raw_command['is_error'] is False and raw_command['request']['tool'] == 'ck3_execute_step'
         and raw_command['request']['arguments']['step'] == 'merge-armies-0-with-204'
         and raw_command['body']['accepted'] is True and action['status'] == 'merge_applied', 'actual legal typed merge applied')
    need(action['destination_army_id'] == 0 and action['source_army_id'] == 204
         and action['submitted_date_raw'] == action['observed_date_raw'] == 53149344
         and action['submitted_episode_run_id'] == action['observed_episode_run_id'] == EPISODE
         and action['player_army_ids_before'] == [0, 204] and action['player_army_ids_after'] == [0]
         and action['postcondition_verified'] is True and action['source_army_id_absent'] is True,
         'actual merge command context; source absence is not death')
    post = read('inputs/post/observation.json')
    for frame in (post['before'], post['after']):
        context(frame)
    need(post['before']['player_armies'] == post['after']['player_armies'], 'post paused roster stable')
    post_rows, post_regs, post_records, post_groups = health(post['health'], post['before'])
    need(set(post_rows) == {0} and post_rows[0]['native_carmy_id'] == 0, 'current surviving Main0/native0 only')
    now = post_rows[0]
    need(len(post_regs) == now['regiment_count'] == 28 and now['current_soldiers'] == 6690 and now['maximum_soldiers'] == 6748,
         'actual post28/current6690/max6748')
    need(set(pre_regs).issubset(post_regs) and all(post_regs[key] == row for key, row in pre_regs.items()), 'original27 entire rows retained')
    new_reg_ids = sorted(set(post_regs) - set(pre_regs))
    need(new_reg_ids == ['16778273'], 'actual added regiment identity')
    new_reg = post_regs[new_reg_ids[0]]
    need(new_reg['current_soldiers'] == new_reg['maximum_soldiers'] == 1
         and new_reg['maa_type_status'] == 'absent' and new_reg['maa_type_key'] is None, 'observed new row fields only')
    need(set(pre_records).issubset(post_records) and all(pre_records[key]['maximum_soldiers'] == post_records[key]['maximum_soldiers'] for key in pre_records), 'original37 DATA identities/max retained')
    DATA_diffs = [{'identity': json.loads(key), 'before': old, 'after': post_records[key]} for key, old in pre_records.items() if old != post_records[key]]
    pre_commander = pre_view['arms']['0']['commander']
    now_commander = commander(read('inputs/post/commander-0.json'), post['before'], 33388)
    need(pre_commander == 27357 and now_commander['character_id'] != pre_commander, 'actual Main commander changed')
    need(now['current_supply_raw'] == now['current_supply_capacity_raw'] == 10000000
         and now['current_supply_change_monthly_raw'] == -423728, 'actual post stock/cap/monthly getter')
    immediate_before = read('inputs/immediate-post-before.json')
    context(immediate_before)
    _, immediate_regs, immediate_records, _ = health(read('inputs/immediate-post-health.json'), immediate_before)
    need(immediate_regs == post_regs and immediate_records == post_records, 'independent immediate/post-read cohort arrays agree')
    return {'schema': 'ck3.e04.B.merge-exception-portable.v1', 'status': 'PASS_RECORDED_ACTUAL_MERGE_EXCEPTION_NOT_FROZEN_COHORT_PASS',
            'run': 'R0175-a02', 'episode_run_id': EPISODE, 'actual_raw': 53149344, 'used_days': 38, 'global_END': 53150592,
            'remaining_days': 52, 'budget_reset': False, 'rest_qualification_preserved': 'qualified-rest/B-qualified-rest-values.json',
            'legal_merge_applied_only': True, 'frozen_whole_cohort_gate': 'FAILED_OBSERVED_NEW28TH_REGIMENT',
            'commander_preserved': False, 'current_commander': now_commander,
            'pre_subjects': pre_view['arms'],
            'post_metrics': {key: now[key] for key in ('army_id', 'native_carmy_id', 'regiment_count', 'current_soldiers', 'maximum_soldiers',
                'current_supply_raw', 'current_supply_scale', 'current_supply_capacity_raw', 'current_supply_capacity_scale',
                'current_supply_change_monthly_raw', 'current_supply_change_monthly_scale')},
            'post_supply_clock': now['army_update_clock_v1'],
            'original27_entire_rows_unchanged': True, 'original37_DATA_identity_and_maximum_retained': True,
            'original37_DATA_entire_row_diffs': DATA_diffs, 'post_actual_DATA_count': len(post_records),
            'new_regiment_entire_row': new_reg, 'new_regiment_complete_DATA_container': post_groups[new_reg_ids[0]],
            'new_DATA_identities': [json.loads(key) for key in sorted(set(post_records) - set(pre_records))],
            'new_unit_type_knight_or_cause': None,
            'stock_weighting_clamp_commander_change_producer_cause': None,
            'London_or_B_Root_final_disposition_or_closure_or_final_raw_result': None,
            'winner_ABC_completion_clean_human_or_refill_death_payment_applied_ledger_credit': 0}


def main():
    try:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({'status': 'STOP_MERGE_EXCEPTION_EVIDENCE_SOURCE_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
