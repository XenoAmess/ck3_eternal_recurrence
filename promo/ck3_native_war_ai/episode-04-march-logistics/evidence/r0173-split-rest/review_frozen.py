"""Read-only, stdlib-only verification of the locally pinned R0173 evidence.

No CK3, SDK, source checkout, host paths, recordings or network is accessed.
The original JSON bytes remain unchanged. Output is a derived endpoint review,
not an execution ledger, ABC comparison, media audit or human signoff.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PurePosixPath


class EvidenceError(ValueError):
    pass


def require(value, message):
    if not value:
        raise EvidenceError(message)


def load_package(root):
    index = json.loads((root / 'index.json').read_bytes())
    require(index['schema'] == 'xar.ck3.r0173.portable-endpoints.v1', 'index schema')
    objects = {}
    for item in index['artifacts']:
        relative = PurePosixPath(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts and ':' not in item['path'], 'unsafe local path')
        path = root.joinpath(*relative.parts)
        require(path.resolve().is_relative_to(root.resolve()), 'path escapes package')
        raw = path.read_bytes()
        require(len(raw) == item['bytes'], 'size mismatch: ' + item['path'])
        require(hashlib.sha256(raw).hexdigest() == item['sha256'], 'hash mismatch: ' + item['path'])
        require(item['id'] not in objects, 'duplicate artifact ID')
        if path.suffix == '.json':
            objects[item['id']] = json.loads(raw)
    return index, objects


FRAME_KEYS = ('date_raw', 'revision', 'native_revision', 'snapshot_id', 'episode_run_id', 'paused')


def validate_frame(before, after, query, label, expected_armies):
    for key in FRAME_KEYS:
        require(before[key] == after[key], label + ': changed frame ' + key)
    require(after['paused'] is True and after['map_ready'] is True, label + ': paused map gate')
    require(after['played_character']['character_id'] == 33388 and after['played_character']['alive'] is True, label + ': actor gate')
    require(after['active_event'] is None and after['pending_character_interaction'] is None, label + ': event gate')
    require(after['source'] == 'injected-dll-named-pipe', label + ': source')
    require(after['episode_run_id'] == 'native-33388-930004d2d2a0', label + ': episode')
    require(query['accepted'] is True and query['status'] == 'available', label + ': health availability')
    require(query['queried_revision'] == after['revision'], label + ': public revision')
    require(query['queried_native_revision'] == after['native_revision'], label + ': native revision')
    require(query['queried_snapshot_id'] == after['snapshot_id'], label + ': snapshot')
    source = query['source']
    for key in ('date_raw', 'revision', 'native_revision', 'snapshot_id', 'paused'):
        require(source[key] == after[key], label + ': health source ' + key)
    roster = {a['army_id']: a for a in after['player_armies']}
    require(set(roster) == set(expected_armies), label + ': full player roster')
    for army in roster.values():
        require(army['owner_character_id'] == 33388 and army['controllable'] is True, label + ': owner/control')
        require(army['in_combat'] is False and army['retreating'] is False, label + ': combat/retreat')
    health = {a['army_id']: a for a in query['army_strengths']}
    require(set(health) == set(expected_armies), label + ': full health roster')
    for public_id, native_id in expected_armies.items():
        army = health[public_id]
        require(army['status'] == 'available' and army['native_carmy_id'] == native_id, label + ': public/native binding')
        resolution = army['native_army_resolution_v1']
        require(resolution['ready'] is True and resolution['entry_full_id'] == native_id, label + ': native FullID')
        require(army['army_update_clock_v1']['current_date_raw'] == after['date_raw'], label + ': clock frame')
    return roster, health


def cohort(health):
    regs, records, army_rows = {}, {}, {}
    for public_id, army in health.items():
        rows = army['regiment_strengths']
        require(len(rows) == army['regiment_count'], 'regiment count')
        require(sum(row['current_soldiers'] for row in rows) == army['current_soldiers'], 'whole soldier sum')
        require(sum(row['maximum_soldiers'] for row in rows) == army['maximum_soldiers'], 'whole maximum sum')
        local_ids = set()
        for row in rows:
            key = row['army_regiment_id']
            require(key not in regs, 'overlapping army regiment FullID')
            regs[key] = row
            local_ids.add(key)
        groups = army['regiment_replenishment_records_v1']
        require({group['army_regiment_id'] for group in groups} == local_ids, 'complete all-record groups')
        for group in groups:
            require(group['source'] == 'native_all_data_records' and group['ready'] is True and group['status'] == 'available', 'all-record availability')
            require(len(group['records']) == group['native_data_record_count'], 'all-record count')
            for row in group['records']:
                require(row['status'] == 'available', 'DATA availability')
                key = (group['army_regiment_id'], row['record_index'], row['persistent_regiment_id'], row['chunk_index'])
                require(key not in records, 'duplicate DATA identity')
                records[key] = row
        army_rows[public_id] = local_ids
    require(len(regs) == 27 and len(records) == 37, 'cohort must be 27 regiments / 37 DATA')
    return regs, records, army_rows


def unchanged(left, right, message):
    require(left[0] == right[0] and left[1] == right[1], message)


def number_rows(health):
    names = ('current_soldiers', 'maximum_soldiers', 'current_supply_raw', 'current_supply_capacity_raw', 'current_supply_change_monthly_raw')
    return {str(key): {name: army[name] for name in names} for key, army in health.items()}


def verify(root):
    index, obj = load_package(root)
    protocol = obj['protocol']
    require(protocol['start_raw'] == 53147376 and protocol['absolute_end_raw'] == 53149536 and protocol['max_actual_game_days'] == 90, 'original finite budget')
    require(protocol['loaded_start_raw'] == 53148432 and protocol['actual_days_already_used'] == 44, 'cold load must not reset budget')
    require(protocol['ABC']['completed_arms'] == 0 and protocol['ABC']['this_run_is_ABC'] is False, 'protocol ABC credit')
    require(index['credits'] == {'ABC_completed_arms': 0, 'film': 0, 'clean_span': 0, 'human_signoff': 0}, 'credit boundary')
    save = obj['checkpoint_pin']
    require(save['bytes'] == 73795635 and save['sha256'] == 'd052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a', 'whole landing checkpoint identity')
    require(protocol['loaded_whole_checkpoint']['sha256'] == save['sha256'], 'protocol/checkpoint join')

    _, base_health = validate_frame(obj['baseline_before'], obj['baseline_after'], obj['baseline_strength'], 'baseline', {0: 0})
    base = cohort(base_health)
    action = obj['split_command']
    require(action['step'] == 'split-army-half-0' and action['accepted'] is True and action['status'] == 'split_submitted', 'legal split command')
    require(action['war_action']['submitted_date_raw'] == 53148432 and action['war_action']['source_army_id'] == 0, 'split action/date')
    require(obj['split_before']['date_raw'] == obj['split_after']['date_raw'] == 53148432, 'split same date')
    # A submitted split changes revision. Its post-query is bracketed against the
    # actual post snapshot, while pre-health remains the independently pinned baseline.
    _, split_health = validate_frame(obj['split_after'], obj['split_after'], obj['split_strength'], 'split post', {0: 0, 204: 199})
    split = cohort(split_health)
    unchanged(base, split, 'split must conserve every normalized regiment and complete DATA row')
    require([len(split[2][key]) for key in (0, 204)] == [15, 12], 'actual split 15+12')
    require([split_health[key]['current_soldiers'] for key in (0, 204)] == [3337, 3342], 'actual split 6679 soldiers')
    require([split_health[key]['maximum_soldiers'] for key in (0, 204)] == [3371, 3376], 'actual split 6747 maximum')
    for army in split_health.values():
        require(army['current_supply_raw'] == 11037716, 'absolute stock copied at split')
        require(army['army_update_clock_v1']['last_supply_update_date_raw'] == base_health[0]['army_update_clock_v1']['last_supply_update_date_raw'], 'split update anchor copy')
        require(army['army_update_clock_v1']['grace_anchor_date_raw'] == base_health[0]['army_update_clock_v1']['grace_anchor_date_raw'], 'split grace anchor copy')
    require(split_health[0]['current_supply_capacity_raw'] == 30000000 and split_health[204]['current_supply_capacity_raw'] == 10000000, 'actual split capacities')

    dates = {'01': 53148456, '02': 53148504, '03': 53148552, '04': 53148576, '10': 53148912, '11': 53148960, '13': 53149056, '14': 53149104, '15': 53149152, '16': 53149200}
    health, rosters, cohorts = {}, {}, {}
    for name, raw in dates.items():
        rosters[name], health[name] = validate_frame(obj['q'+name+'_before'], obj['q'+name+'_after'], obj['q'+name+'_strength'], 'q'+name, {0: 0, 204: 199})
        require(obj['q'+name+'_after']['date_raw'] == raw, 'q'+name+' date')
        cohorts[name] = cohort(health[name])
        require(set(cohorts[name][0]) == set(base[0]) and set(cohorts[name][1]) == set(base[1]), 'cross-window FullID/DATA identity')
        for key, row in cohorts[name][0].items():
            require(row['maximum_soldiers'] == base[0][key]['maximum_soldiers'], 'regiment max preservation')
        for key, row in cohorts[name][1].items():
            require(row['maximum_soldiers'] == base[1][key]['maximum_soldiers'], 'DATA max preservation')
        require(cohorts[name][2] == split[2], 'split lineage preservation')
    for before, after in (('01', '02'), ('03', '04'), ('10', '11'), ('15', '16')):
        unchanged(cohorts[before], cohorts[after], 'non-soldier window must preserve all regiment and DATA fields')
    # Fully pinned endpoint facts. A current positive monthly getter is not
    # treated as an applied update and an update anchor is not a PC trace.
    require(health['01'][0]['current_supply_raw'] == 11037716 and health['02'][0]['current_supply_raw'] == 10613988, 'negative Main stock endpoints')
    require(health['01'][0]['current_supply_change_monthly_raw'] == health['02'][0]['current_supply_change_monthly_raw'] == -423728, 'negative monthly endpoints')
    require(health['02'][0]['army_update_clock_v1']['last_supply_update_date_raw'] == 53148480, 'Main original day46 update mark')
    require(health['01'][204]['current_supply_raw'] == health['02'][204]['current_supply_raw'] == 11037716, 'child stock unchanged in negative window')
    for army_id, province in ((0, 2174), (204, 2327)):
        row = rosters['04'][army_id]
        require(row['current_province_id'] == province and row['army_state'] == 'regular' and row['route_province_ids'] == [], 'distinct stationary rest sites')
        require(health['03'][army_id]['current_supply_change_monthly_raw'] == -423728 and health['04'][army_id]['current_supply_change_monthly_raw'] == 2000000, 'arrival monthly endpoints')
        require(health['03'][army_id]['current_supply_raw'] == health['04'][army_id]['current_supply_raw'], 'arrival is not stock gain')
        require(health['10'][army_id]['current_supply_change_monthly_raw'] == health['11'][army_id]['current_supply_change_monthly_raw'] == 2000000, 'cap-window positive monthly')
    require(health['10'][204]['current_supply_raw'] == 11037716 and health['11'][204]['current_supply_raw'] == health['11'][204]['current_supply_capacity_raw'] == 10000000, 'child actual overcap-to-cap')
    require(health['11'][204]['army_update_clock_v1']['last_supply_update_date_raw'] == 53148936, 'child original day65 update mark')
    require(health['10'][0]['current_supply_raw'] == health['11'][0]['current_supply_raw'] == 10613988, 'Main still no growth at child cap update')

    grown = []
    for key, row in cohorts['14'][1].items():
        old = cohorts['13'][1][key]
        delta = row['current_soldiers'] - old['current_soldiers']
        require(delta >= 0, 'growth window unexpected DATA loss')
        require(row['effective_current_soldiers'] - old['effective_current_soldiers'] == delta, 'effective/current DATA gain')
        if delta:
            grown.append({'identity': list(key), 'delta': delta, 'after': row['current_soldiers'], 'max': row['maximum_soldiers']})
    require(sorted(row['delta'] for row in grown) == [1, 1, 1, 2, 2, 3], 'six actual DATA gains')
    require(len(grown) == 6, 'six positive DATA records')
    for army_id, before, after in ((0, 3337, 3344), (204, 3342, 3345)):
        require(health['13'][army_id]['current_soldiers'] == before and health['14'][army_id]['current_soldiers'] == after, 'actual army soldier gain')
        require(sum(item['delta'] for item in grown if item['identity'][0] in split[2][army_id]) == after-before, 'DATA/army gain join')
        for field in ('current_supply_raw', 'current_supply_capacity_raw', 'current_supply_change_monthly_raw'):
            require(health['13'][army_id][field] == health['14'][army_id][field], 'soldier gain distinct from supply change')
        for field in ('last_supply_update_date_raw', 'grace_anchor_date_raw'):
            require(health['13'][army_id]['army_update_clock_v1'][field] == health['14'][army_id]['army_update_clock_v1'][field], 'soldier window supply anchors unchanged')
    require(health['14'][0]['current_supply_raw'] == 10613988, 'Main positive-stock write remains absent at day72')

    require(health['15'][0]['current_supply_raw'] == 10613988 and health['16'][0]['current_supply_raw'] == 12613988, 'Main actual positive stock endpoints')
    require(health['15'][0]['current_supply_change_monthly_raw'] == health['16'][0]['current_supply_change_monthly_raw'] == 2000000, 'Main positive monthly endpoints')
    require(health['15'][0]['current_supply_capacity_raw'] == health['16'][0]['current_supply_capacity_raw'] == 30000000, 'Main remains below actual cap')
    require(health['15'][0]['army_update_clock_v1']['last_supply_update_date_raw'] == 53148480 and health['16'][0]['army_update_clock_v1']['last_supply_update_date_raw'] == 53149200, 'Main actual positive update mark')
    for army_id in (0, 204):
        require(health['15'][army_id]['army_update_clock_v1']['grace_anchor_date_raw'] == health['16'][army_id]['army_update_clock_v1']['grace_anchor_date_raw'], 'positive-window grace unchanged')
        require(rosters['15'][army_id]['current_province_id'] == rosters['16'][army_id]['current_province_id'] and rosters['16'][army_id]['route_province_ids'] == [] and rosters['16'][army_id]['army_state'] == 'regular', 'positive-window stationary lineage')
    require(health['15'][204]['current_supply_raw'] == health['16'][204]['current_supply_raw'] == 10000000, 'child at cap unchanged during Main growth')
    require(health['15'][204]['army_update_clock_v1']['last_supply_update_date_raw'] == health['16'][204]['army_update_clock_v1']['last_supply_update_date_raw'] == 53148936, 'child positive-window update mark unchanged')

    stationary_before, stationary_after = obj['stationary_before'], obj['stationary_after']
    for key in FRAME_KEYS:
        require(stationary_before[key] == stationary_after[key] == obj['q04_after'][key], 'stationary read-only frame')
    commanders, province_supply = {}, {}
    for army_id, native_id, province in ((0, 0, 2174), (204, 199, 2327)):
        commander = obj['commander_'+str(army_id)]
        preview = obj['preview_'+str(army_id)]
        for item in (commander, preview):
            require(item['queried_revision'] == stationary_after['revision'] and item['queried_native_revision'] == stationary_after['native_revision'], 'typed query fresh frame')
        body = commander['army_commander_candidates']
        require(body['army_id'] == army_id and body['native_carmy_id'] == native_id and body['date_raw'] == 53148576, 'commander actual identity/date')
        current = preview['route_preview']['province_supply']['current']
        require(current['status'] == 'available' and current['province_id'] == province, 'actual current-province supply')
        require(preview['route_preview']['previewed_date_raw'] == 53148576, 'province-supply query date')
        require(body['current_commander']['status'] == 'available', 'commander available')
        commanders[str(army_id)] = body['current_commander']['character_id']
        province_supply[str(army_id)] = current
    require(commanders == {'0': 27357, '204': 33388}, 'day50 commander endpoints')
    require(obj['root_world_review']['old_STOP_relabelled'] is False, 'external world STOP preserved')
    require(obj['root_cap_review']['belowcap_stock_growth'] is False, 'cap review is not recovery gain')

    closure = obj['root_closure']
    require(closure['final_qualification_raw'] == 53149200 and closure['original_budget_END'] == 53149536 and closure['used_actual_days'] == 76 and closure['remaining_actual_days'] == 14, 'actual Root closure budget')
    require(all(closure[key] is True for key in ('sdk_thread_exited', 'keeper_thread_exited', 'tree_gone', 'watchdog_absent', 'native_CK3_inventory_empty')), 'actual Root closure gates')
    require(closure['GameJob_active_processes'] == 0 and closure['owned_Game_termination_exit'] == 1 and closure['supervisor_exit0_observed_by_unified_exec_session'] == 8183, 'Game exit1 distinct from supervisor exit0 and GameJob0')
    require(closure['ABC_common_whole_save_SHA_unchanged'] == save['sha256'] and closure['ABC_completed_arms'] == 0, 'closure/common save boundary')
    split_save = obj['qualified_checkpoint_pin']
    require(split_save['bytes'] == 74386976 and split_save['sha256'] == 'c43f71c4973e035e04fb44609ba86f04407beb7af1a775191e09fddb9e943b66', 'actual qualified split save pin')
    require(closure['split_qualification_save']['sha256'] == split_save['sha256'], 'closure/split save join')
    coverage = obj['root_world_coverage']
    require(coverage['candidate_objective_rows'] == [] and coverage['full_rest_site_world_control_coverage'] is None and coverage['unread_fields_not_assumed_unchanged'] is True, 'limited world/site coverage')
    frame_review = obj['root_frame_review']
    require(frame_review['outside_finished900s_raw'] is True and frame_review['encoded_timecode_binding'] is None and frame_review['human_approval'] is False and frame_review['full_1x_review'] is False and frame_review['clean_spans_certified'] is False, 'Root image view distinct from encoded film/human credit')

    return {'status': 'PASS_FROZEN_SPLIT_REST_ENDPOINTS', 'schema': 'xar.ck3.r0173.portable-review.v1', 'verified_artifact_count': len(index['artifacts']), 'runtime': {'python_version': sys.version.split()[0], 'stdlib_only': True}, 'split': {'regiments': [15,12], 'soldiers': [3337,3342], 'maximum': [3371,3376], 'DATA_count': 37, 'absolute_stock_copied_raw': 11037716}, 'windows': {key: number_rows(value) for key,value in health.items()}, 'six_grown_DATA_records': grown, 'commander_readback_at_original_day50': commanders, 'actual_province_supply_at_original_day50': province_supply, 'latest_raw': 53149200, 'absolute_end_raw': 53149536, 'actual_original_days_used': 76, 'remaining_original_days': 14, 'Main_positive_stock_delta_raw': 2000000, 'pending': index['pending'], 'credits': index['credits'], 'side_effects': {'files_written': 0, 'game_or_SDK_or_network_or_media': 0}, 'limits': ['only saved endpoint values, identities and source-frame joins are verified', 'no producer PC/applied ledger, exact update tick or death attribution', 'day50 commander readback does not establish day76 commander stability', 'positive monthly values alone do not establish positive stock growth; q15/q16 additionally verifies actual stock endpoints', 'original save and recordings are deliberately not distributed or rehashed']}


def main():
    try:
        require(len(sys.argv) == 1, 'no arguments; index is local to this script')
        report = verify(Path(__file__).resolve().parent)
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (EvidenceError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
