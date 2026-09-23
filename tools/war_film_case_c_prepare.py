"""Freeze CASE-C first-contact intent from saved CASE-W rows; never connect to CK3."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('D:/workspace/ck3_war_film_research_20260923')
EXE_SHA = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'


def binding(path):
    data = path.read_bytes()
    return {'path': path.resolve().as_posix(), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def save(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def receipt(path):
    value = json.loads(path.read_bytes())
    if value.get('result') != 'CALL_COMPLETED':
        raise ValueError(f'Incomplete saved native receipt: {path}')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', type=Path, default=WORK)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    responses = args.workdir/'capture-live-live-r5/recovery-requests-responses'
    snapshot_path = responses/'w131-take_snapshot.json'
    route_path = responses/'w130-query_battle_reinforcement_assignment_v1.json'
    capabilities_path = responses/'w001-get_capabilities.json'
    identity_path = args.workdir/'capture-live-live-r5/live-run-identity.json'
    snap_receipt = receipt(snapshot_path)
    snap = snap_receipt['body']
    driver = snap_receipt['driver_state']
    route = receipt(route_path)['body']
    caps = receipt(capabilities_path)['body']
    identity = json.loads(identity_path.read_bytes())
    run_id = identity['identities'][0]['run_id']
    assert driver['bridge_pid'] == 32356 and driver['connection_generation'] == 1
    assert driver['hello']['expected_ck3_sha256'].lower() == EXE_SHA
    assert driver['hello']['ck3_build_match'] is True
    assert snap['paused'] is True and snap['map_ready'] is True
    assert snap['date_raw'] == 53144784 and snap['played_character']['character_id'] == 29829
    wars = [war for war in snap['active_wars'] if war['war_id'] == 4]
    assert len(wars) == 1 and wars[0]['primary_opponent_character_id'] == 31549
    war = wars[0]
    armies = war['allied_armies'] + war['enemy_armies']
    assert len(war['enemy_armies']) == 5 and all(row['in_combat'] is False for row in armies)
    player = next(row for row in armies if row['army_id'] == 18)
    assert player['owner_character_id'] == 29829 and player['current_province_id'] == 2624
    assert player['move_target_province_id'] == 2638
    assert route['queried_revision'] == snap['revision']
    assert route['queried_native_revision'] == snap['native_revision']
    assert route['selected_public_cunit_id'] == 22 and route['status'] == 'available'
    required_steps = ['pause-map', 'resume-map', 'set-speed-1', 'set-speed-2']
    assert all(step in caps['action_steps'] for step in required_steps)
    narrow = route['battle_reinforcement_assignment']
    assert narrow['observed_date_raw'] == snap['date_raw']
    baseline = {
        'schema': 'xar.war-film-case-c-baseline.v1', 'authority': 'saved CASE-W receipts; not a fresh game query',
        'case_w_state': 'parent reports completed and stopped at day19; CASE-C does not change W limits',
        'run_id': run_id, 'pid': 32356, 'connection_generation': 1, 'episode_run_id': snap['episode_run_id'],
        'frame': {key: snap[key] for key in ['snapshot_id', 'revision', 'native_revision', 'date_raw', 'paused']},
        'actor_character_id': 29829, 'war': war, 'route_u22': narrow,
        'route_estimate': {'endpoint_arrival_date_raw': narrow['route']['arrival_date_raws'][-1],
            'raw_hours_per_day': 24, 'estimated_days_from_baseline':
                (narrow['route']['arrival_date_raws'][-1]-snap['date_raw'])/24,
            'meaning': 'stored arrival timeline for U22; not combat ETA, probability or guaranteed continued route'},
        'sources': {key: binding(path) for key, path in [('snapshot', snapshot_path), ('route', route_path),
            ('capabilities', capabilities_path), ('run_identity', identity_path)]},
        'day19_checkpoint': None, 'checkpoint_state': 'root must save and bind actual day19 bytes before CASE-C resume',
    }
    checkpoint_path = args.workdir/'case-w-r1/end-checkpoint.json'
    checkpoint = json.loads(checkpoint_path.read_bytes())
    archive = binding(args.workdir/'case-w-r1/end-state.ck3')
    actual = checkpoint['response']['checkpoint']
    assert actual['status'] == 'saved' and actual['date_raw'] == snap['date_raw']
    assert archive['bytes'] == actual['size'] and archive['sha256'] == actual['sha256'].lower()
    assert checkpoint['after']['date_raw'] == snap['date_raw'] and checkpoint['after']['paused'] is True
    baseline['day19_checkpoint'] = {'receipt': binding(checkpoint_path), 'archive': archive,
        'after': {key: checkpoint['after'][key] for key in ['snapshot_id','revision','native_revision','date_raw','paused','episode_run_id']}}
    baseline['checkpoint_state'] = 'saved/materialized/archive hash verified offline; fresh live identity still required'
    server_path = ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
    tree = ast.parse(server_path.read_text(encoding='utf-8-sig'))
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    tool_names = ['ck3_get_capabilities', 'ck3_get_bridge_diagnostics', 'ck3_take_snapshot',
        'ck3_get_war_state', 'ck3_save_checkpoint', 'ck3_inspect_save_artifacts_v1', 'ck3_execute_step',
        'ck3_query_actual_contact_scope', 'ck3_query_battle_control_snapshot_v1', 'ck3_query_battle_transition_v1',
        'ck3_query_battle_terminal_transition_v1']
    contract = {'schema': 'xar.war-film-case-c-source-contract.v1',
        'tools': {name: {'line': functions[name].lineno,
            'parameters': [arg.arg for arg in functions[name].args.args]} for name in tool_names},
        'files': [binding(path) for path in [server_path,
            ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py',
            ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py',
            ROOT/'docs/ck3-native-ai/war-film-case-w-observation-2026-09-23.md']],
        'raw_date_rule': 'Existing war_contract.py horizon_end=date_raw+24 establishes one-day raw-hour convention; no new EXE/static extraction.',
        'actual_combat_binding': 'battle control attacker/defender ordered_armies have public_cunit_id, owner_character_id and combat_backlink_id; prove a current W4 opposite-side pair shares C.',
        'projection_boundary': 'in_combat triggers pause only; actual contact/control/transition must agree on full C. Present-time hypothetical contact or stored ETA is not actual contact.'}
    window = {
        'schema': 'xar.war-film-case-c-window.v1', 'status': 'prepared-not-executed',
        'owner': 'root is sole R0005 live owner; this preparer never connects',
        'output_root': (args.workdir/'case-c-r1').as_posix(),
        'recording_root': (args.workdir/'case-c-r1-recording').as_posix(),
        'baseline_date_raw': snap['date_raw'], 'maximum_game_days': 120, 'raw_hours_per_day': 24,
        'deadline_date_raw': snap['date_raw']+120*24, 'maximum_wall_seconds': 600,
        'wall_clock_start': 'monotonic mark immediately before the first CASE-C resume submission; all pause/query latency thereafter counts',
        'preconditions': ['actual root-saved day19 checkpoint bytes/hash/materialization and response bound',
            'fresh paused snapshot: same run/PID/generation/episode, actor29829, date53144784 and W4/opponent31549',
            'no active event or pending interaction; initial in_combat=false for the watched W4 rows',
            'fresh capability advertisement includes speed1/2, pause/resume and all three contact/control/transition queries'],
        'allowed_actions': ['pre-window save-checkpoint if root has not already completed it',
            'set-speed-1 or set-speed-2', 'resume-map', 'pause-map'],
        'forbidden_actions': ['declare-war', 'raise-troops', 'move-army', 'split/merge', 'event or interaction choices',
            'AI/planner turns', 'force combat', 'switch player', 'change war', 'retreat', 'peace'],
        'sampling': 'Serial fresh snapshot every <=2 wall seconds while running; <=0.5 seconds at speed1 near same/adjacent current locations or imminent stored arrivals. Inspect all currently published W4 allied/enemy CUnits, not only the original six. No narrow paused query while running.',
        'near_boundary': 'Switch to speed1 before the final five calendar days or final30 wall seconds; request pause by day119 or wall570s as a latency reserve. Max120/600 are ceilings, not targets.',
        'combat_trigger': 'First current W4 allied/enemy row with in_combat=true: immediately request pause using the latest public revision, then verify paused/map_ready and bind actual C through formal queries.',
        'success_stop': 'One actual C confirmed by contact/control/transition, with at least one current W4 allied and one enemy public CUnit on opposite actual combat sides; leave paused immediately.',
        'failure_stop': ['active_event or pending_character_interaction appears; pause and leave undecided',
            'PID/generation/episode/actor changes or connection/required binding unavailable',
            'W4 disappears, ends, or changes primary opponent',
            'first in_combat trigger cannot be bound to a current actual C/W4 after at most two paused fresh-read rounds',
            'any budget ceiling/reserve stop; no extra sailing/chasing extension'],
        'sampling_limit': 'Polling may miss a combat between snapshots. Preserve actual observed intervals and any budget overshoot; never claim no combat occurred or a guaranteed engine-synchronous stop.',
        'zero_result': 'No exact combat observed in this window; not proof that AI refuses combat or no combat happened between snapshots.',
        'runtime_bindings_required': ['day19 checkpoint binding', 'pre/post frame and run identity', 'first resume monotonic/UTC',
            'every request/response UTC/monotonic/date/public and native revision', 'trigger public CUnit and W4 membership',
            'paused contact/control/transition actual C and opposite sides', 'end reason and elapsed game/wall time',
            'raw recording bytes/SHA and actual PTS marks if root records; no exact frame-sync claim by timing proximity'],
    }
    window['success_stop'] = 'At first actual C binding, pause and preserve all contact/control/transition evidence. Either stop successfully or use the separately bounded optional same-battle natural-outcome subwindow below.'
    window['optional_same_battle_outcome'] = {
        'maximum_additional_game_days': 30, 'overall_limits_unchanged': True,
        'deadline': 'min(initial_date+120*24, contact_binding_date+30*24); same original600s wall clock; stop before service expiry',
        'procedure': 'After paused C evidence is durable, resume only existing combat at speed1/2; poll same C/subjects, pause on terminal/in_combat exit/C disappearance. No battle or retreat commands.',
        'closure': 'Formal terminal query with prior_combat_id=C and original subject_public_cunit_id=U, plus battle control/current W4 score snapshot. C disappearance alone is not a completed battle proof; terminal/control unavailable is incomplete.',
        'score_boundary': 'Before/after player_relative_war_score for exact W4 only. A total score delta is not attributed solely to this battle without component evidence.',
        'stop': 'One same-C terminal binding or first30-day/overall/event/identity/war-stop condition; never a second battle.'}
    window['service_expiry_parent_report'] = '2026-09-22T22:20:54Z; request final pause before22:20:24Z if still active, without extending service'
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in [('baseline.json', baseline), ('source-contract.json', contract), ('sampling-window.json', window)]:
        save(args.output_dir/name, value)
    evidence = []
    for ident, filename, layer, supports in [
        ('baseline', 'baseline.json', 'live-observation', 'Archived W day19 starting state only; CASE-C not executed.'),
        ('source', 'source-contract.json', 'source-contract', 'Existing public tool signatures and exact combat/day conventions; no repeated static research.'),
        ('window', 'sampling-window.json', 'source-contract', 'New independent bounded intent; neither W extension nor runtime proof.')]:
        item = {'id': ident, 'path': filename, 'layer': layer, 'sha256': binding(args.output_dir/filename)['sha256'],
                'exe_sha256': EXE_SHA, 'supports': supports}
        if layer == 'live-observation':
            item.update(session=f'{run_id}; PID32356; generation1',
                frame='native:44/public45/native44/date53144784', identity='actor29829; W4; player U18; enemy U16777221/U16777231/U22/U27/U28')
        evidence.append(item)
    plan = {
        'schema': 'xar.native-research-plan.v1', 'topic': 'war-film-case-c-first-actual-contact-20260923',
        'question': 'Within a new bounded observation window continuing existing W4 routes from day19, can formal queries bind one first observed actual CombatID to both sides of this same war?',
        'purpose': 'engine-transition', 'build': {'version': '1.19.0.6', 'exe_sha256': EXE_SHA},
        'observation': {'mode': 'passive-runtime', 'actor_kind': 'engine', 'owner_scope': 'Current W4 allied/enemy CUnits; existing player order continues, NPC orders remain native.',
            'identity_kind': 'generation-id', 'identity_lifetime': 'One R0005/PID32356/generation1/episode and exact W4. Refresh full public unit IDs; no inferred split/merge identity. Stop on session/war identity change.',
            'producer_trigger': 'daily-tick', 'producer': 'Normal unpaused movement/contact engine following existing routes; this observation does not add movement orders or force combat.',
            'caller': 'Sole root owner uses advertised speed1/2 and resume/pause; latest published in_combat is only a pause trigger.',
            'consumer': 'Paused public actual-contact, battle-control and battle-transition readbacks, retaining exact C, unit owners and side ordering.',
            'cache_lifetime': 'Fresh snapshots each sample and after every action. Use current public revision, never baseline45 or native44 as replay guards. Paused query identity/date/revision must be compatible.',
            'expected_signal': 'Current W4 unit in_combat followed by one agreed actual full C and opposite combat sides containing W4 allied/enemy units.',
            'zero_sample_meaning': window['zero_result'],
            'stop_condition': 'First exact contact binding or any failure stop; hard ceilings120 game days/600 wall seconds, proactive pause reserves in sampling-window.json; no change to completed CASE-W.',
            'runtime_window_ref': 'sampling-window.json; root-authorized independent case-c-r1 after actual day19 checkpoint binding'},
        'pre_observation': {'checkpoint': 'Pending root save at plan freeze; must bind actual bytes/hash/materialization before first resume.',
            'same_process': 'Continue existing paused session only after fresh identity checks. If it ends, stop this attempt; no automatic restore or relaunch.',
            'no_initial_combat': 'If C already exists before first resume, record pre-existing contact; do not claim this window captured its onset.'},
        'bindings_to_fill_from_live': {key: None for key in ['checkpoint', 'start_snapshot', 'start_monotonic', 'start_utc',
            'trigger_snapshot', 'subject_public_cunit_id', 'actual_contact', 'battle_control', 'combat_id',
            'battle_transition', 'same_war_opposite_sides', 'end_snapshot', 'end_reason', 'elapsed_game_days', 'elapsed_wall_seconds', 'recording']},
        'evidence': evidence,
        'nodes': [{'id': ident, 'label': label} for ident, label in [
            ('baseline', 'Completed W day19 routes'), ('ready', 'Fresh CASE-C checkpoint and identity'),
            ('running', 'Existing routes progress without new orders'), ('trigger', 'Published in_combat pause trigger'),
            ('bound', 'Actual same-war full CombatID and sides'), ('stop', 'Paused bounded result')]],
        'edges': [
            {'id': 'archived-start', 'from': 'baseline', 'to': 'ready', 'label': 'Archived W state is evidence; CASE-C checkpoint remains to bind', 'status': 'live-confirmed', 'evidence': ['baseline'], 'open_question': None},
            {'id': 'resume', 'from': 'ready', 'to': 'running', 'label': 'Explicit bounded time advance only', 'status': 'counter-policy', 'evidence': ['window'], 'open_question': None},
            {'id': 'contact-trigger', 'from': 'running', 'to': 'trigger', 'label': 'First observed current-W4 in_combat publication', 'status': 'unknown', 'evidence': [], 'open_question': 'Requires new CASE-C snapshot; polling can miss short contacts.'},
            {'id': 'actual-binding', 'from': 'trigger', 'to': 'bound', 'label': 'Paused contact/control/transition agree on actual C and opposite W4 sides', 'status': 'unknown', 'evidence': [], 'open_question': 'No CASE-C actual CombatID observed yet; ETA/hypothetical contact is insufficient.'},
            {'id': 'stop-rule', 'from': 'bound', 'to': 'stop', 'label': 'Stop at first binding; zero-result and exception paths also stop', 'status': 'counter-policy', 'evidence': ['window'], 'open_question': None}],
        'cases': [{'id': 'one-same-war-contact', 'question': 'One first observed actual C on existing W4 routes within independent CASE-C budgets.', 'status': 'pending', 'evidence': []}],
        'explicit_nonclaims': ['natural AI declaration', 'new NPC orders submitted by observer', 'complete target/combat scoring',
            'contact guaranteed by route ETA', 'frame-synchronous video/MCP mapping', 'no unobserved contact between polls',
            'retreat policy', 'battle winner or war result', 'extended CASE-W success window']}
    plan['pre_observation']['checkpoint'] = 'day19 end-state.ck3 archive hash verified and bound in baseline.json; native:45/public46/native45/date53144784. Fresh live snapshot still required; never reuse46 without refresh.'
    plan['question'] += ' After preserving that paused binding, optionally observe this same battle natural end within additional30 days and unchanged overall120 days/600 seconds.'
    plan['observation']['stop_condition'] = 'First exact C binding is paused and preserved; optional same-C natural outcome only within additional30 days and unchanged overall120 days/600 seconds/service expiry. All event/identity/war failures stop; completed CASE-W is not extended.'
    plan['nodes'].append({'id':'terminal','label':'Optional same-C natural terminal and W4 score readback'})
    plan['edges'].append({'id':'natural-terminal','from':'bound','to':'terminal','label':'Optional first battle natural end with formal terminal/control closure; no commands','status':'unknown','evidence':[],'open_question':'Requires same-C actual terminal journal/control and W4 score evidence; disappearance alone is incomplete.'})
    plan['cases'].append({'id':'optional-one-battle-outcome','question':'Only the bound first C, at most30 further days within original overall ceilings; no second battle.','status':'pending','evidence':[]})
    plan['bindings_to_fill_from_live'].update({key:None for key in ['contact_date_raw','terminal_receipt','terminal_control','war_score_before','war_score_after','optional_outcome_end_reason']})
    plan['explicit_nonclaims'].remove('battle winner or war result')
    plan['explicit_nonclaims'].append('sole attribution of total war-score delta to one battle without component evidence')
    save(args.output_dir/'plan.json', plan)
    print(json.dumps({'output': str(args.output_dir), 'state': 'prepared-not-executed',
        'deadline_date_raw': window['deadline_date_raw'], 'case_c_live_edges': 0,
        'day19_checkpoint_bound': True, 'plan_sha256': binding(args.output_dir/'plan.json')['sha256']}))


if __name__ == '__main__':
    main()
