"""Finite, read-only ABC endpoint/table validation; stdlib only.

No SDK, game, UI, bus, Git, saved-game bytes, recordings or network access.
This checks values and provenance in supplied local JSON. Policy execution,
complete sampling, application causes and human/media review remain separate.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath


class ResultError(ValueError):
    pass


def need(value, message):
    if not value:
        raise ResultError(message)


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_table(path):
    table = json.loads(path.read_bytes())
    need(table['schema'] == 'xar.ck3.abc-results.v1', 'results schema')
    objects = {}
    for pin in table['artifact_pins']:
        relative = PurePosixPath(pin['path'])
        need(not relative.is_absolute() and '..' not in relative.parts and ':' not in pin['path'], 'unsafe relative source path')
        target = path.parent.joinpath(*relative.parts)
        need(target.resolve().is_relative_to(path.parent.resolve()), 'source escapes package')
        raw = target.read_bytes()
        need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'source bytes mismatch: ' + pin['id'])
        need(pin['id'] not in objects, 'duplicate source ID')
        objects[pin['id']] = json.loads(raw)
    return table, objects


def rows(health, subjects):
    by_id = {army['army_id']: army for army in health['army_strengths']}
    need(len(by_id) == len(health['army_strengths']), 'duplicate health public Army ID')
    regiments, records, mapping, stock, soldiers = {}, {}, {}, {}, 0
    for public_id in subjects:
        need(public_id in by_id, 'subject health missing')
        army = by_id[public_id]
        need(army['status'] == 'available', 'subject is not actual available CArmy; do not infer zero soldiers')
        native_id = army['native_carmy_id']
        resolution = army['native_army_resolution_v1']
        need(resolution['ready'] is True and resolution['entry_full_id'] == native_id, 'public/native FullID binding')
        mapping[str(public_id)] = native_id
        local_ids = set()
        need(len(army['regiment_strengths']) == army['regiment_count'], 'regiment count')
        for regiment in army['regiment_strengths']:
            key = str(regiment['army_regiment_id'])
            need(key not in regiments, 'overlapping subject regiment FullID')
            regiments[key] = regiment
            local_ids.add(regiment['army_regiment_id'])
        need(sum(row['current_soldiers'] for row in army['regiment_strengths']) == army['current_soldiers'], 'current actual whole-regiment sum')
        need(sum(row['maximum_soldiers'] for row in army['regiment_strengths']) == army['maximum_soldiers'], 'maximum actual whole-regiment sum')
        groups = army['regiment_replenishment_records_v1']
        need({group['army_regiment_id'] for group in groups} == local_ids, 'all-DATA covers every actual regiment, including record_count0')
        for group in groups:
            need(group['status'] == 'available' and group['ready'] is True and group['source'] == 'native_all_data_records', 'all-DATA read availability')
            need(group['native_data_record_count'] == len(group['records']), 'all-DATA record count')
            for row in group['records']:
                need(row['status'] == 'available', 'DATA row availability')
                key = json.dumps([group['army_regiment_id'], row['record_index'], row['persistent_regiment_id'], row['chunk_index']], separators=(',', ':'))
                need(key not in records, 'duplicate complete DATA identity')
                records[key] = row
        stock[str(public_id)] = {key: army[key] for key in ('current_supply_raw', 'current_supply_capacity_raw', 'current_supply_change_monthly_raw', 'current_supply_scale', 'current_supply_capacity_scale', 'current_supply_change_monthly_scale', 'current_attrition_fraction_raw', 'current_attrition_fraction_scale', 'army_update_clock_v1')}
        soldiers += army['current_soldiers']
    return {'regiments': regiments, 'records': records, 'mapping': mapping, 'stock': stock, 'soldiers': soldiers, 'maximum': sum(row['maximum_soldiers'] for row in regiments.values()), 'non_subject_health': [{'public_id': key, 'status': army['status'], 'native_carmy_id': army.get('native_carmy_id'), 'unavailable_reason': army.get('unavailable_reason')} for key, army in by_id.items() if key not in subjects]}


def observation(value, objects, common, initial=False):
    refs = value['source_refs']
    before, health, after = (objects[refs[key]] for key in ('before', 'health', 'after'))
    need(before['date_raw'] == after['date_raw'] and before['episode_run_id'] == after['episode_run_id'], 'observation date/episode boundary')
    need(before['paused'] is True and after['paused'] is True and before['map_ready'] is True and after['map_ready'] is True, 'paused map gate')
    need(before['source'] == after['source'] == 'injected-dll-named-pipe', 'native snapshot source')
    need(before['played_character']['character_id'] == after['played_character']['character_id'] == common['actor_character_id'], 'same actual actor for endpoint comparison')
    need(before['played_character']['alive'] is True and after['played_character']['alive'] is True, 'actor alive')
    need(before['active_event'] is None and after['active_event'] is None and before['pending_character_interaction'] is None and after['pending_character_interaction'] is None, 'blocking event/interaction endpoint')
    need(before['played_character_gold'] == after['played_character_gold'], 'gold changed within endpoint query; fresh stable read required')
    need(before['player_armies'] == after['player_armies'], 'player Army context changed within endpoint query')
    need(health['accepted'] is True and health['status'] == 'available', 'actual health query availability')
    for key in ('revision', 'native_revision', 'snapshot_id'):
        need(health['queried_' + key] == before[key], 'health must bind actual before frame: ' + key)
    for key in ('date_raw', 'revision', 'native_revision', 'snapshot_id', 'paused'):
        need(health['source'][key] == before[key], 'health source frame ' + key)
    need(value.get('episode_run_id', before['episode_run_id']) == before['episode_run_id'], 'declared episode mismatch')
    need(value.get('date_raw', before['date_raw']) == before['date_raw'], 'declared date mismatch')
    roster = {army['army_id']: army for army in before['player_armies']}
    subjects = value.get('subject_public_ids', [0])
    need(len(set(subjects)) == len(subjects) and len(subjects) > 0, 'unique actual subjects')
    for public_id in subjects:
        need(public_id in roster, 'subject absent from full player roster')
        army = roster[public_id]
        need(army['owner_character_id'] == common['actor_character_id'] and army['controllable'] is True, 'subject owner/control')
        need(army['in_combat'] is False and army['retreating'] is False, 'subject combat/retreat')
    cohort = rows(health, subjects)
    need(len(cohort['regiments']) == 27 and len(cohort['records']) == 37, 'complete original subject cohort 27/37')
    need(cohort['maximum'] == common['whole_maximum_soldiers'], 'cohort maximum')
    if initial:
        need(before['date_raw'] == common['start_raw'], 'actual cold start date')
        need(before['played_character_gold'] == common['initial_gold'], 'same actual cold initial treasury')
        need(semantic_sha(cohort['regiments']) == common['cold_baseline_regiment_rows_sha256'], 'cold regiment rows differ from shared actual baseline')
        need(semantic_sha(cohort['records']) == common['cold_baseline_complete_DATA_rows_sha256'], 'fresh cold complete DATA rows differ; historical hot rows are not the baseline')
    commanders = None
    if 'commander' in refs:
        query = objects[refs['commander']]
        body = query['army_commander_candidates']
        need(query['accepted'] is True and body['status'] == 'available', 'commander query availability')
        need(query['date_raw'] == body['date_raw'] == before['date_raw'], 'commander native date')
        need(query['snapshot_revision'] == body['snapshot_revision'] == before['native_revision'], 'commander native snapshot revision')
        if 'queried_revision' in query:
            need(query['queried_revision'] == before['revision'] and query['queried_native_revision'] == before['native_revision'], 'commander explicit public/native wrapper frame')
        # Some current capture packets intentionally retain only the native body.
        # Missing public/connection/episode stamps remain missing. Native context
        # is checked against the independent actual same-paused source packet.
        context = body['current_movement_speed']
        need(context['snapshot_revision'] == before['native_revision'] and context['date_raw'] == before['date_raw'], 'commander movement-context native frame')
        public_id = body['army_id']
        need(context['public_cunit_id'] == public_id and context['native_carmy_id'] == body['native_carmy_id'] and context['owner_character_id'] == common['actor_character_id'], 'commander movement-context identity')
        need(context['current_province_id'] == roster[public_id]['current_province_id'] and context['army_state'] == roster[public_id]['army_state'] and context['route_source_count'] == roster[public_id]['route_source_count'], 'commander context/current Army join')
        need(body['army_id'] in subjects and body['native_carmy_id'] == cohort['mapping'][str(body['army_id'])], 'commander public/native binding')
        current = body['current_commander']
        need(current['status'] == 'available', 'current commander actually observed')
        commanders = {str(body['army_id']): current['character_id']}
    return {'before': before, 'after': after, 'health': health, 'roster': roster, 'subjects': subjects, 'cohort': cohort, 'commanders': commanders, 'source_refs': refs}


def stationary_london(observed):
    return all(army['current_province_id'] == 1527 and army['route_province_ids'] == [] and army['route_read_status'] == 'complete_empty' and army['route_source_count'] == 0 and army['army_state'] in ('regular', 'sieging') and army['in_combat'] is False and army['retreating'] is False for key, army in observed['roster'].items() if key in observed['subjects'])


def diff_paths(left, right, path=''):
    if type(left) is not type(right):
        return [path or '/']
    if isinstance(left, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            child = path + '/' + str(key)
            result.extend([child] if key not in left or key not in right else diff_paths(left[key], right[key], child))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [path + '/length']
        return [item for index, (a,b) in enumerate(zip(left,right)) for item in diff_paths(a,b,path+'/'+str(index))]
    return [] if left == right else [path or '/']


def derive_terminal(arm_id, arm, objects, common, start):
    need(common['protocol_freeze_ref'] is not None, 'actual terminal requires Root frozen protocol pin; a candidate is not admission')
    freeze_ref = common['protocol_freeze_ref']
    need(isinstance(freeze_ref, dict) and freeze_ref['artifact_id'] in objects and freeze_ref['Root_receipt_artifact_id'] in objects, 'Root frozen protocol/receipt source absent')
    need(freeze_ref['frozen_before_first_arm_action'] is True, 'Root before-first-action freeze not explicitly evidenced')
    protocol, proof = objects[freeze_ref['artifact_id']], objects[freeze_ref['Root_receipt_artifact_id']]
    need(protocol['status'] == 'Root-frozen-prospective-ABC-intent-before-first-army-action' and proof['first_army_move_or_new_game_day_not_yet_issued'] is True, 'Root actual freeze scope')
    need(proof['frozen_protocol']['sha256'] == freeze_ref['protocol_sha256'], 'Root proof/protocol raw SHA join')
    need(protocol['start_raw'] == proof['common_start_raw'] == common['start_raw'], 'Root actual common T0')
    need(protocol['absolute_end_raw'] == proof['absolute_end_raw'] == common['planned_absolute_end_raw'], 'Root actual common END')
    need(protocol['actor_id'] == common['actor_character_id'], 'Root actual actor')
    need(protocol['common_input']['sha256'] == common['checkpoint_sha256'] and protocol['common_input']['split_c43_backup_permitted_as_input'] is False, 'Root actual whole common input')
    need(protocol['ABC']['arrival_allowed_states'] == ['regular', 'sieging'], 'actual frozen arrival states')
    terminal = observation(arm['terminal_observation'], objects, common)
    need(terminal['before']['episode_run_id'] == start['before']['episode_run_id'], 'do not join arm endpoints across episodes')
    for name in ('regiments', 'records'):
        need(set(terminal['cohort'][name]) == set(start['cohort'][name]), 'terminal original cohort identity')
        for key, row in terminal['cohort'][name].items():
            need(row['maximum_soldiers'] == start['cohort'][name][key]['maximum_soldiers'], 'terminal maximum differs; retain as stopped confounder')
    sequence = arm['ordered_observation_source_refs']
    need(isinstance(sequence, list) and len(sequence) >= 2, 'initial and complete supplied ordered endpoint sequence required')
    observations = [observation({'source_refs':item['source_refs'], 'subject_public_ids':item.get('subject_public_ids',[0])}, objects, common) for item in sequence]
    dates = [item['before']['date_raw'] for item in observations]
    need(dates == sorted(dates) and dates[0] == common['start_raw'], 'ordered source dates must begin at common T0')
    need(observations[-1]['source_refs'] == terminal['source_refs'], 'terminal must be last supplied observation')
    need(all(item['before']['episode_run_id'] == start['before']['episode_run_id'] for item in observations), 'ordered samples same arm episode')
    end_raw = terminal['before']['date_raw']
    stop = arm['stop']
    need(isinstance(stop,dict), 'actual endpoint needs explicit actual stop classification')
    kind = stop['kind']
    arrival = None
    if kind == 'ARRIVED_VALID_EVENT':
        need(stationary_london(terminal), 'terminal is not actually stationary London')
        need(len(terminal['cohort']['mapping']) == 1 and list(terminal['cohort']['mapping'].values()) == [0], 'arrival requires whole surviving Main nativeCArmy0, not unmerged halves')
        need(terminal['commanders'] == {key: 27357 for key in terminal['cohort']['mapping']}, 'arrival needs actual fresh Main commander27357 query')
        need(all(not stationary_london(item) for item in observations[:-1]), 'earlier supplied stationary London sample exists')
        need(common['start_raw'] < end_raw <= common['planned_absolute_end_raw'], 'arrival outside shared frozen budget')
        arrival = {'previous_observed_not_stationary_raw':dates[-2], 'first_supplied_stationary_raw':end_raw, 'exact_arrival_raw':None, 'interval':'(previous_observed_not_stationary_raw, first_supplied_stationary_raw] only; not GUI ETA or exact tick'}
    elif kind == 'CENSORED_DEADLINE':
        need(end_raw == common['planned_absolute_end_raw'], 'budget censor requires actual exact frozen endpoint; earlier stop is incomplete')
        need(not any(stationary_london(item) for item in observations), 'arrival already observed; not budget censored')
    elif kind == 'CENSORED_CONSERVATIVE_TIME_GUARD':
        guard = protocol['minimum_terminal_and_comparison_contract']['deadline']['pre_resume_guard_raw']
        need(end_raw == guard == common['conservative_pre_resume_guard_raw'], 'conservative censor needs actual frozen guard endpoint, not fictitious day90')
        need(not any(stationary_london(item) for item in observations), 'London already observed; not guard censored')
    elif kind == 'INVALID_BUDGET_BREACH':
        need(end_raw > common['planned_absolute_end_raw'], 'overshoot classification needs actual overrun')
    else:
        raise ResultError('only frozen arrival/deadline/guard/breach statuses yield this endpoint; gate-incomplete stops remain unranked with null derived_result')
    initial_gold = start['before']['played_character_gold']
    final_gold = terminal['before']['played_character_gold']
    need(initial_gold['scale'] == final_gold['scale'] == 100000, 'gold raw scale')
    elapsed = end_raw-common['start_raw']
    record_changes = {}
    for collection in ('regiments','records'):
        record_changes[collection] = [{'identity':key, 'changed_fields':diff_paths(start['cohort'][collection][key],row), 'before':start['cohort'][collection][key], 'after':row} for key,row in terminal['cohort'][collection].items() if row != start['cohort'][collection][key]]
    wars_changed = diff_paths(start['before']['active_wars'], terminal['before']['active_wars'], '/active_wars')
    return {'stop_kind':kind, 'terminal_raw':end_raw, 'elapsed_raw_hours':elapsed, 'elapsed_actual_days':elapsed/24, 'arrival':arrival, 'gold_start_raw':initial_gold['raw'], 'gold_end_raw':final_gold['raw'], 'gold_net_raw':final_gold['raw']-initial_gold['raw'], 'gold_scale':100000, 'gold_net_is':'observed treasury balance difference; no upkeep or cause attribution', 'soldiers_start':start['cohort']['soldiers'], 'soldiers_end':terminal['cohort']['soldiers'], 'soldier_net':terminal['cohort']['soldiers']-start['cohort']['soldiers'], 'maximum_soldiers':terminal['cohort']['maximum'], 'same_original_regiment_and_DATA_identity':True, 'full_regiment_and_complete_DATA_changes':record_changes, 'regiment_count':27, 'complete_DATA_record_count':37, 'initial_public_to_native':start['cohort']['mapping'], 'terminal_public_to_native':terminal['cohort']['mapping'], 'terminal_commander_readback':terminal['commanders'], 'initial_supply':start['cohort']['stock'], 'terminal_supply':terminal['cohort']['stock'], 'terminal_routes':{str(key):army['route_province_ids'] for key,army in terminal['roster'].items() if key in terminal['subjects']}, 'active_war_changed_paths':wars_changed, 'NPC_or_world_changes_are_not_arm_action_causality':True, 'unavailable_non_subjects_not_zero_soldiers':terminal['cohort']['non_subject_health'], 'policy_execution_review':arm.get('policy_execution_review'), 'troop_application_cause':None, 'army_cost_application_cause':None, 'media_human_credit':None}


def verify(path):
    table, objects = read_table(path)
    common = table['common']
    need(common['checkpoint_sha256'] == 'd052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a' and common['checkpoint_bytes'] == 73795635, 'same unsplit common checkpoint')
    need(common['start_raw'] == 53148432 and common['planned_absolute_end_raw'] == 53150592 and common['planned_actual_days'] == 90, 'same bounded planned clock')
    if common['protocol_freeze_ref'] is not None:
        ref = common['protocol_freeze_ref']
        pins = {item['id']: item for item in table['artifact_pins']}
        need(pins[ref['artifact_id']]['sha256'] == ref['protocol_sha256'], 'table raw protocol pin')
    need(set(table['arms']) == {'A','B','C'}, 'three distinct arm rows')
    verified, pending, stopped = {}, [], []
    for arm_id, arm in table['arms'].items():
        need(arm['applied_soldier_loss_or_refill_cause'] is None and arm['maintenance_cost_attribution'] is None and arm['media_or_human_credit'] is None, 'no application-cause or media signoff shortcuts in endpoint table')
        initial = arm['initial_observation']
        terminal = arm['terminal_observation']
        if initial is None:
            need(terminal is None and arm['derived_result'] is None and arm['stop'] is None, 'unobserved arm must keep endpoints/results NULL')
            pending.append(arm_id)
            continue
        start = observation(initial, objects, common, initial=True)
        if terminal is None:
            need(arm['derived_result'] is None and arm['stop'] is None, 'unobserved terminal must keep END/arrival/result NULL')
            pending.append(arm_id)
            continue
        if isinstance(arm['stop'],dict) and arm['stop'].get('kind') == 'STOPPED_GATE_INCOMPLETE':
            need(arm['derived_result'] is None and arm['stop'].get('reason') and arm['stop'].get('Root_review_artifact_id') in objects, 'condition stop needs exact Root review and null comparable result')
            stopped.append(arm_id)
            continue
        result = derive_terminal(arm_id, arm, objects, common, start)
        if arm['derived_result'] is not None:
            need(arm['derived_result'] == result, 'filled result differs from actual source-derived endpoint values')
        verified[arm_id] = result
    history = table.get('historical_attempts',{})
    if 'A1_R0174' in history:
        old = history['A1_R0174']
        need(old['primary_result_eligible'] is False and old['London_arrival'] is False and old['strategy_result'] is None and old['budget_or_bytes_reinterpreted'] is False, 'old capture-incomplete A1 must not become primary outcome')
        disposition = objects[old['terminal_disposition_artifact_id']]
        need(disposition['status'] == 'capture-incomplete-independent-attempt' and disposition['actual_days_used'] == 1 and disposition['actual_days_remaining'] == 89 and disposition['arrival_confirmed'] is False and disposition['comparison_after_outcome_selection'] is False, 'actual A1 disposition boundary')
    comparison = table['comparison']
    need(comparison['soldier_change_causal_ranking'] is None and comparison['victory_or_best_policy'] is None, 'endpoints do not establish causality or winner')
    if len(verified) != 3 or stopped:
        need(comparison['arrival_ranking'] is None and comparison['gold_net_ranking'] is None and comparison['all_arms_terminal_observed'] is False, 'incomplete three-arm experiment cannot claim ranking or all terminals')
    return {'schema':'xar.ck3.abc-results-validation.v1', 'status':'PASS_TEMPLATE_NO_ARM_RESULTS' if not verified and not stopped else 'PASS_SUPPLIED_ENDPOINT_VALUES_ONLY', 'verified_terminal_values':verified, 'pending_arm_ids':pending, 'condition_stopped_unranked_arm_ids':stopped, 'artifact_count':len(table['artifact_pins']), 'current_ABC_complete_comparison_credit':0, 'same_event_stop':'first supplied stationary1527 regular/sieging with complete emptyroute and no combat/retreat; exact tick remainsNULL', 'limits':['Root frozen protocol and execution reviews are distinct from file-only candidate', 'ordered sequence only establishes first in supplied samples, never unobserved exact arrival', 'actual gold delta is net treasury, not maintenance or action cost', 'NPC/source/world divergence and troop application causes are not simplified away', 'no saved-game bytes, active raw, game, SDK, UI, bus, Git or network read/write'], 'side_effects':{'files_written':0,'machine_actions':0}}


def main():
    try:
        need(len(sys.argv) == 2, 'usage: python validate_results.py results-template.json')
        print(json.dumps(verify(Path(sys.argv[1]).resolve()), ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ResultError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({'status':'FAIL','error':str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
