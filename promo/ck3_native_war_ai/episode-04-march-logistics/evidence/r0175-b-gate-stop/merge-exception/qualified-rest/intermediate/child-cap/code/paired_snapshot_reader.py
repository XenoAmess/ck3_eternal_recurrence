"""Single explicit completed-B-observation read; no polling, SDK or game calls."""
import argparse
import hashlib
import json
from pathlib import Path

EPISODE = 'native-33388-23726fbd8a80'
START, END = 53148432, 53150592
SUBJECTS = {0: 0, 204: 199}
COMMANDERS = {0: 27357, 204: 33388}
SITES = {0: 2174, 204: 2327}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def changes(left, right, prefix=''):
    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        return [path for key in sorted(set(left) | set(right))
                for path in ([prefix + '/' + str(key)] if key not in left or key not in right
                             else changes(left[key], right[key], prefix + '/' + str(key)))]
    if isinstance(left, list):
        if len(left) != len(right):
            return [prefix]
        return [path for index, (old, new) in enumerate(zip(left, right))
                for path in changes(old, new, prefix + '/' + str(index))]
    return [] if left == right else [prefix]


def read(path, pins):
    need(path.suffix == '.json' and path.stat().st_size < 2097152, 'bounded completed JSON only')
    raw = path.read_bytes()
    pins.append({'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)


def project(packet, commander_queries):
    before, health, after = packet['before'], packet['health'], packet['after']
    need(before['episode_run_id'] == after['episode_run_id'] == EPISODE, 'same actual B episode')
    need(before['date_raw'] == after['date_raw'] and START <= before['date_raw'] <= END, 'same paused bounded frame')
    need(before['paused'] is after['paused'] is True and before['map_ready'] is after['map_ready'] is True, 'fresh paused map')
    for frame in (before, after):
        need(frame['played_character']['character_id'] == 33388 and frame['played_character']['alive'] is True,
             'living actual actor33388')
        need(frame['active_event'] is None and frame['pending_character_interaction'] is None, 'no unresolved actor event')
    need(before['player_armies'] == after['player_armies'], 'own before/after actual roster stable')
    need(before['played_character_gold'] == after['played_character_gold'], 'paused gold source stable')
    need(health['accepted'] is True and health['status'] == 'available', 'available actual health query')
    for query_key, frame_key in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
                                 ('queried_native_revision', 'native_revision')):
        need(health[query_key] == before[frame_key], 'health own before frame')
    for key in ('date_raw', 'paused', 'snapshot_id', 'revision', 'native_revision'):
        need(health['source'][key] == before[key], 'health own source ' + key)
    roster = {row['army_id']: row for row in before['player_armies']}
    health_rows = {row['army_id']: row for row in health['army_strengths']}
    regiments, records, arms, regiment_arm, record_arm = {}, {}, {}, {}, {}
    for public_id, native_id in SUBJECTS.items():
        need(public_id in roster and public_id in health_rows, 'both required halves actually present')
        context, army = roster[public_id], health_rows[public_id]
        need(context['owner_character_id'] == 33388 and context['controllable'] is True
             and context['in_combat'] is False and context['retreating'] is False, 'required owner/control/no combat/retreat')
        need(army['status'] == 'available' and army['native_carmy_id'] == native_id, 'actual current public/native binding')
        resolution = army['native_army_resolution_v1']
        need(resolution['status'] == 'available' and resolution['ready'] is True
             and resolution['entry_full_id'] == native_id, 'actual resolved native FullID')
        ids = set()
        for row in army['regiment_strengths']:
            key = str(row['army_regiment_id'])
            need(key not in regiments, 'disjoint actual regiment FullIDs')
            ids.add(key)
            regiments[key], regiment_arm[key] = row, public_id
        need(len(ids) == army['regiment_count'], 'complete actual local regiment count')
        need(sum(row['current_soldiers'] for row in army['regiment_strengths']) == army['current_soldiers']
             and sum(row['maximum_soldiers'] for row in army['regiment_strengths']) == army['maximum_soldiers'], 'actual perregiment current/max sums')
        groups = set()
        for group in army['regiment_replenishment_records_v1']:
            key = str(group['army_regiment_id'])
            need(key in ids and key not in groups, 'unique complete all-DATA group')
            groups.add(key)
            need(group['source'] == 'native_all_data_records' and group['status'] == 'available'
                 and group['ready'] is True and group['native_data_record_count'] == len(group['records']), 'complete all-DATA, including zero-record groups')
            for row in group['records']:
                record_key = json.dumps([group['army_regiment_id'], row['record_index'],
                                         row['persistent_regiment_id'], row['chunk_index']], separators=(',', ':'))
                need(record_key not in records and row['status'] == 'available', 'disjoint actual DATA identity')
                records[record_key], record_arm[record_key] = row, public_id
        need(groups == ids, 'DATA covers every actual regiment')
        query = commander_queries[public_id]
        body = query['army_commander_candidates']
        need(query['accepted'] is True and body['status'] == 'available', 'actual raw commander query required')
        need(query['date_raw'] == body['date_raw'] == before['date_raw']
             and query['snapshot_revision'] == body['snapshot_revision'] == before['native_revision'], 'commander own native frame')
        if 'queried_revision' in query:
            need(query['queried_revision'] == before['revision'] and query['queried_native_revision'] == before['native_revision'], 'commander own explicit public/native wrapper')
        speed = body['current_movement_speed']
        need(body['army_id'] == public_id and body['native_carmy_id'] == native_id
             and body['owner_character_id'] == 33388, 'actual commander owner/public/native')
        need(body['current_commander']['status'] == 'available'
             and body['current_commander']['character_id'] == COMMANDERS[public_id], 'required actual current commander')
        need(speed['context_observable'] is True and speed['snapshot_revision'] == before['native_revision']
             and speed['date_raw'] == before['date_raw'] and speed['public_cunit_id'] == public_id
             and speed['native_carmy_id'] == native_id and speed['owner_character_id'] == 33388
             and speed['current_commander_character_id'] == COMMANDERS[public_id], 'commander actual movement source')
        for key in ('current_province_id', 'route_source_count', 'army_state', 'in_combat', 'retreating'):
            need(speed[key] == context[key], 'commander actual context/' + key)
        clock = army['army_update_clock_v1']
        need(clock['status'] == 'available' and clock['ready'] is True
             and clock['current_date_raw'] == before['date_raw'], 'available own supply clock context')
        arms[str(public_id)] = {
            'public_id': public_id, 'native_carmy_id': native_id, 'owner': 33388,
            'commander': COMMANDERS[public_id], 'province': context['current_province_id'],
            'state': context['army_state'], 'route': context['route_province_ids'],
            'route_status': context['route_read_status'], 'route_count': context['route_source_count'],
            'current_soldiers': army['current_soldiers'], 'maximum_soldiers': army['maximum_soldiers'],
            'regiments': army['regiment_count'], 'DATA': sum(len(group['records']) for group in army['regiment_replenishment_records_v1']),
            'stock': army['current_supply_raw'], 'capacity': army['current_supply_capacity_raw'],
            'monthly': army['current_supply_change_monthly_raw'],
            'scales': {key: army[key] for key in ('current_supply_scale', 'current_supply_capacity_scale', 'current_supply_change_monthly_scale')},
            'last_supply_update_storage': clock['last_supply_update_date_storage_raw64'],
            'last_supply_update_raw': clock['last_supply_update_date_raw'],
            'grace_storage': clock['grace_anchor_date_storage_raw64'], 'grace_raw': clock['grace_anchor_date_raw'],
            'clock_status': clock['status'],
            'stationary_at_required_site': context['current_province_id'] == SITES[public_id]
                and context['army_state'] == 'regular' and context['route_province_ids'] == []
                and context['route_read_status'] == 'complete_empty' and context['route_source_count'] == 0}
    need(len(regiments) == 27 and len(records) == 37
         and sum(row['maximum_soldiers'] for row in regiments.values()) == 6747, 'complete required27/37/max6747')
    unassessed = []
    for public_id, context in roster.items():
        if public_id not in SUBJECTS:
            row = health_rows.get(public_id)
            unassessed.append({'public_cunit_id': public_id, 'roster': context,
                               'health': row if row is not None else None,
                               'classification': None, 'soldiers_if_unqueried': None})
    return {'date_raw': before['date_raw'], 'episode': EPISODE, 'gold': before['played_character_gold'],
            'arms': arms, 'regiments': regiments, 'records': records,
            'regiment_arm': regiment_arm, 'record_arm': record_arm,
            'active_wars': before['active_wars'], 'unassessed_ancillary': unassessed,
            'raw_scope_status': health.get('scope_status'),
            'query_source_version_and_executable': {key: health['source'].get(key) for key in ('game_version', 'executable_sha256')}}


def load(path, pins):
    packet = read(path, pins)
    commanders = {}
    for public_id in SUBJECTS:
        body = packet.get('commanders', {}).get(str(public_id))
        if isinstance(body, dict) and 'army_commander_candidates' in body:
            commanders[public_id] = body
        else:
            commanders[public_id] = read(path.parent / ('commander-' + str(public_id) + '.json'), pins)
    value = project(packet, commanders)
    frozen = read(Path(__file__).resolve().parent / 'frozen-cohort.json', pins)
    need(frozen['episode'] == EPISODE, 'this B actual cohort source')
    need({key: row['maximum_soldiers'] for key, row in value['regiments'].items()}
         == frozen['regiment_maximum_by_FullID'], 'actual complete original27 identities/max')
    need({key: row['maximum_soldiers'] for key, row in value['records'].items()}
         == frozen['DATA_maximum_by_identity'], 'actual complete original37 DATA identities/max')
    return value


def summary(value):
    eligible = all(row['stationary_at_required_site'] and row['monthly'] > 0 for row in value['arms'].values())
    main, child = value['arms']['0'], value['arms']['204']
    return {'actual_raw': value['date_raw'], 'used_days': (value['date_raw'] - START) / 24,
            'remaining_days': (END - value['date_raw']) / 24, 'gold': value['gold'], 'arms': value['arms'],
            'full27_regiment_rows_sha256': sha(value['regiments']), 'full37_DATA_rows_sha256': sha(value['records']),
            'both_stationary_positive_observed': eligible,
            'stock_branch_preconditions_observed': {'main_below_cap': main['stock'] < main['capacity'],
                                                     'child_at_or_above_cap': child['stock'] >= child['capacity']},
            'eligible_to_offer_new_Root_frozen_window_entry': eligible and main['stock'] < main['capacity'] and child['stock'] >= child['capacity'],
            'actual_window_frozen_or_recovery_completed_credit': None,
            'unassessed_ancillary': value['unassessed_ancillary'], 'scope_status_retained': value['raw_scope_status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, help='explicitly completed observation.json; no directory scan or wait')
    parser.add_argument('--previous', type=Path, help='optional completed earlier observation in same B')
    args = parser.parse_args()
    if args.current is None:
        print(json.dumps({'status': 'PLAN_ONLY_NO_SOURCE_READS', 'episode': EPISODE, 'start_raw': START,
                          'absolute_end_raw': END, 'actual_phase0_binding': SUBJECTS,
                          'entry': '--current COMPLETED/observation.json [--previous COMPLETED/observation.json]',
                          'polling_or_game_SDK_UI_bus_Git_or_media_actions': False}, indent=2))
        return 0
    pins = []
    try:
        current = load(args.current, pins)
        report = {'status': 'PASS_REQUIRED_B_PAIR_SNAPSHOT_ONLY', 'source_pins': pins,
                  'latest': summary(current), 'material_changes': None,
                  'B_terminal_arrival_final_deltas_closed_raw_result': None,
                  'ABC_or_ledger_cause_or_media_credit': 0}
        if args.previous is not None:
            previous = load(args.previous, pins)
            need(previous['date_raw'] <= current['date_raw'], 'ordered explicit completed frames')
            for collection in ('regiments', 'records'):
                need(set(previous[collection]) == set(current[collection]), 'original full identity preserved across pair')
                need(all(row['maximum_soldiers'] == previous[collection][key]['maximum_soldiers'] for key, row in current[collection].items()), 'individual maximum changed')
            material = changes({key: previous[key] for key in ('arms', 'gold', 'regiments', 'records', 'regiment_arm', 'record_arm')},
                               {key: current[key] for key in ('arms', 'gold', 'regiments', 'records', 'regiment_arm', 'record_arm')})
            world = changes(previous['active_wars'], current['active_wars'], '/active_wars')
            writes = {}
            for public_id in ('0', '204'):
                old, new = previous['arms'][public_id], current['arms'][public_id]
                stable = all(old[key] == new[key] for key in ('native_carmy_id', 'owner', 'commander', 'province', 'capacity', 'scales'))
                positive = old['monthly'] > 0 and new['monthly'] > 0
                anchor_changed = old['last_supply_update_storage'] != new['last_supply_update_storage'] and old['last_supply_update_raw'] != new['last_supply_update_raw']
                writes[public_id] = {'same_required_stationary_site_context': stable and old['stationary_at_required_site'] and new['stationary_at_required_site'],
                                     'both_monthly_positive': positive, '+188_changed': anchor_changed,
                                     'stock_net_raw': new['stock'] - old['stock'],
                                     'main_numeric_write_pair': public_id == '0' and stable and positive and anchor_changed
                                         and old['stationary_at_required_site'] and new['stationary_at_required_site']
                                         and old['stock'] < old['capacity'] and new['stock'] > old['stock'],
                                     'child_full_branch_numeric_pair': public_id == '204' and stable and positive and anchor_changed
                                         and old['stationary_at_required_site'] and new['stationary_at_required_site']
                                         and old['stock'] >= old['capacity'] and new['stock'] == new['capacity'],
                                     'frozen_window_policy_or_application_cause_credit': None}
            report['material_changes'] = {'count': len(material), 'paths_first24': material[:24],
                                           'paths_truncated': len(material) > 24,
                                           'active_war_changed_path_count': len(world), 'active_war_paths_first12': world[:12],
                                           'world_equality_or_accepted_confounder': None,
                                           'numeric_supply_pairs_only': writes}
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'STOP_REQUIRED_SOURCE_GATE', 'error': str(exc), 'source_pins': pins,
                          'current_or_missing_health_not_coerced_to_zero': True,
                          'B_terminal_arrival_final_deltas_raw_result': None}, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
