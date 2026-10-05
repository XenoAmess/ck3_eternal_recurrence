"""Offline replay of the R0171 current-input evidence, using only stdlib and package files."""
from pathlib import Path
import argparse
import hashlib
import json

def require(value, reason):
    if not value:
        raise ValueError(reason)

def verify(root):
    index = json.loads((root / 'index.json').read_bytes())
    require(index['run'] == 'R0171' and index['portable'] is True and index['media_files'] == 0, 'package scope')
    for row in index['files']:
        path = (root / row['path']).resolve()
        require(path.is_relative_to(root.resolve()), 'package path escapes')
        raw = path.read_bytes()
        require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'file bytes/SHA mismatch: ' + row['path'])
    def load(role):
        return json.loads((root / index['roles'][role]).read_bytes())
    before, after = load('baseline_strength'), load('move_strength')
    snapshots = [load('baseline_snapshot'), load('move_snapshot')]
    main = []
    main_snapshots = []
    for pos, body in enumerate((before, after)):
        require(body['step'] == 'query-army-strengths-v1' and body['accepted'] is True and body['status'] == 'available', 'strength query unavailable')
        require(body['army_ids'] == [0] and len(body['army_strengths']) == 1, 'query army scope')
        row = body['army_strengths'][0]
        main.append(row)
        require(row['army_id'] == 0 and row['native_carmy_id'] == 0 and row['status'] == 'available', 'native army identity')
        require(row['native_army_resolution_v1']['ready'] is True and row['native_army_resolution_v1']['entry_full_id'] == 0, 'native FullID readiness')
        source = body['source']
        require(source['paused'] is True and source['date_raw'] == 53147376, 'paused actual date')
        require(source['snapshot_id'] == body['queried_snapshot_id'] and source['revision'] == body['queried_revision'] and source['native_revision'] == body['queried_native_revision'], 'source/query frame identity')
        require(source['game_version'] is None and source['executable_sha256'] is None, 'version should not be fabricated in source packet')
        snapshot = snapshots[pos]
        require(snapshot['paused'] is True and snapshot['map_ready'] is True and snapshot['date_raw'] == source['date_raw'], 'snapshot paused/date')
        for key in ('snapshot_id', 'revision', 'native_revision'):
            require(snapshot[key] == source[key], 'snapshot/query frame join: ' + key)
        require(snapshot['played_character']['character_id'] == 33388 and snapshot['played_character']['alive'] is True, 'played actor identity')
        require(snapshot['episode_identity_pending'] is False, 'episode identity not ready')
        require(snapshot['active_event'] is None and snapshot['pending_character_interaction'] is None, 'endpoint event/context')
        army = next(x for x in snapshot['player_armies'] if x['army_id'] == 0)
        main_snapshots.append(army)
        require(army['owner_character_id'] == 33388 and army['controllable'] is True and army['current_province_id'] == 1506, 'current owner/province')
        require(army['in_combat'] is False and army['retreating'] is False, 'endpoint combat/retreat')
        strengths = row['regiment_strengths']
        require(row['regiment_count'] == len(strengths) == 27 and len({x['army_regiment_id'] for x in strengths}) == 27, 'complete actual regiments')
        require(sum(x['current_soldiers'] for x in strengths) == row['current_soldiers'] == 6746, 'actual current sum')
        require(sum(x['maximum_soldiers'] for x in strengths) == row['maximum_soldiers'] == 6747, 'actual maximum sum')
        require(all(x['scale'] == 1 for x in strengths), 'soldier scale')
        containers = row['regiment_replenishment_records_v1']
        require(len(containers) == 27 and {x['army_regiment_id'] for x in containers} == {x['army_regiment_id'] for x in strengths}, 'all-DATA container binding')
        require(all(x['status'] == 'available' and x['ready'] is True and x['native_data_record_count'] == len(x['records']) for x in containers), 'complete DATA records')
        require(sum(len(x['records']) for x in containers) == 37, '37 actual DATA records')
        empty_ids = sorted(x['army_regiment_id'] for x in containers if not x['records'])
        require(empty_ids == [56, 57, 58, 59, 60], 'zero-record identity')
        require(all(x['current_soldiers'] == x['maximum_soldiers'] == 1 for x in strengths if x['army_regiment_id'] in empty_ids), 'zero record is not zero soldiers')
        county = row['county_entry_inputs_v1']
        wanted = {'status': 'available', 'source': 'native_current_county_entry_inputs', 'unavailable_reason': None,
                  'whole_soldiers': 6746, 'current_loss_budget': 236, 'effective_fraction_raw': 3500,
                  'minimum_multiplier_raw': 70000, 'loaded_minimum_soldiers': 5, 'fraction_scale': 100000, 'soldier_scale': 1}
        require({k: county[k] for k in wanted} == wanted, 'current native county input values')
        response = load('baseline_response' if pos == 0 else 'move_response')
        request_role = 'baseline_request' if pos == 0 else 'move_request'
        request_raw = (root / index['roles'][request_role]).read_bytes()
        require(response['is_error'] is False and response['body'] == body, 'original SDK response/body exact semantic match')
        require(response['request'] == json.loads(request_raw), 'original exact request')
        require(response['request_identity']['sha256'] == hashlib.sha256(request_raw).hexdigest() and response['request_identity']['bytes'] == len(request_raw), 'original request byte identity')
        require(response['request']['tool'] == 'ck3_query_army_strengths' and response['request']['arguments'] == {'army_ids': [0], 'expected_revision': 3 + pos}, 'actual tool/arguments')
        snapshot_response = load('baseline_snapshot_response' if pos == 0 else 'move_snapshot_response')
        require(snapshot_response['is_error'] is False and snapshot_response['body'] == snapshot, 'original snapshot response join')
    require(before['queried_snapshot_id'] == 'native:2' and before['queried_revision'] == 3 and before['queried_native_revision'] == 2, 'baseline frame')
    require(after['queried_snapshot_id'] == 'native:3' and after['queried_revision'] == 4 and after['queried_native_revision'] == 3, 'moved frame')
    require(snapshots[0]['episode_run_id'] == snapshots[1]['episode_run_id'] == 'native-33388-88a82177b681', 'same episode')
    require(main_snapshots[0]['route_province_ids'] == [] and main_snapshots[0]['route_read_status'] == 'complete_empty', 'baseline actual route empty')
    condition = main[0]['county_entry_inputs_v1']['condition']
    require(condition['status'] == 'unavailable' and condition['unavailable_reason'] == 'no_stored_route', 'unknown no-route condition')
    require(all(condition[k] is None for k in ('actor_character_id', 'source_province_id', 'target_province_id', 'mode', 'passes')), 'unknown fields null')
    route = main_snapshots[1]['route_province_ids']
    require(route == [725, 1009, 2174] and main_snapshots[1]['route_read_status'] == 'complete_nonempty' and main_snapshots[1]['route_source_count'] == 3, 'complete actual stored route')
    require(main_snapshots[1]['move_target_province_id'] == route[-1], 'final target independent from first province')
    condition = main[1]['county_entry_inputs_v1']['condition']
    require(condition == {'status': 'available', 'source': 'current_stored_route_first_province', 'unavailable_reason': None,
                           'actor_character_id': 33388, 'source_province_id': 1506,
                           'target_province_id': route[0], 'mode': 1, 'passes': False}, 'current native route-first predicate')
    movement = main[1]['current_movement_progress']
    require(movement['status'] == 'available' and movement['normalized_edge_progress'] == {'raw': 0, 'scale': 100000} and movement['first_route_edge_remaining_duration'] == {'raw': 3000000, 'scale': 100000}, 'first edge current 30 days/progress zero')
    for key in ('regiment_strengths', 'regiment_replenishment_records_v1', 'army_update_clock_v1'):
        require(main[0][key] == main[1][key], 'paused endpoint block unchanged: ' + key)
    require(load('move_command_response')['body'] == load('move_command') and load('move_command_response')['is_error'] is False, 'original typed movement command preservation')
    build = load('build_delivery')
    require(build['status'] == 'offline-build-passed; not-deployed' and build['source_head'] == index['source_commit'] == '7f1db1a773e647b9f31378d4a9ccf57a60cf9e73', 'pinned exact a08 source')
    dll = next(x for x in build['artifacts'] if x['target'] == 'xar_ck3_bridge')
    injector = next(x for x in build['artifacts'] if x['target'] == 'xar_ck3_bridge_injector')
    require(dll['sha256'] == '8d4d80249ccdfed0954181df38d81daec9740f809fe59dc6c3e7b6708872cc28', 'a08 build DLL pin')
    ready = load('session_ready')
    require(ready['type'] == 'native_session_ready' and ready['pid'] == 19092, 'actual new session identity')
    final = ready['frontend_first_warmup']['final_bridge']
    require(final['dll_injection'] is True and final['dll_path'] == dll['path'] and final['injector_path'] == injector['path'], 'actual session a08 binary paths')
    sdk = load('sdk_ready')
    require(sdk['pipe_name'] == ready['pipe'], 'SDK/new session pipe join')
    origins = sdk['runtime_identity']['loaded_xar_autoplayer_modules']
    require(origins['xar_autoplayer.bridge.army_county_entry_inputs_contract'].replace('\\', '/') == 'C:/w/e4countybuilda01/ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_inputs_contract.py', 'actual matching county normalizer origin')
    require(load('capabilities')['army_strength_query_supported'] is True, 'actual Strength capability')
    summary = json.loads((root / 'summary.json').read_bytes())
    require(summary['endpoint_strength_delta'] == 0 and summary['game_date_delta_raw'] == 0, 'zero date/strength endpoint difference')
    require(all(summary['readiness'][k] is False for k in ('actual_applied_loss', 'refill_event_ledger', 'county_arrival', 'executor_special_R9_boolean', 'movement_loaded_lock_threshold', 'William_starvation_crossing', 'filming_completion')), 'no expanded runtime credit')
    return {'status': 'passed', 'run': 'R0171', 'files_verified': len(index['files']),
            'bytes_verified': sum(x['bytes'] for x in index['files']),
            'source_commit': index['source_commit'], 'baseline_frame': 'native:2/pub3', 'move_frame': 'native:3/pub4',
            'date_raw': 53147376, 'date_delta_raw': 0, 'actual_strength_delta': 0,
            'actual_regiments': 27, 'full_DATA_records': 37,
            'county_current_budget': 236, 'route_first_target': 725, 'current_predicate_passes': False,
            'credit': 'Current-input runtime readback only; no applied loss/refill/arrival/starvation/lock-threshold/film completion.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    receipt = verify(args.package)
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(receipt, f, indent=2)
            f.write('\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
