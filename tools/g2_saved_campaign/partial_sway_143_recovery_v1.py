"""One source-bound partial read-only recap; never replay AUTO143 or grant a cycle."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import time

KIND = 'partial_sway_readonly_143'
META_SHA = 'aa3bc5375873b8dcd5bd7c45d43d1ff5a010857482e62f8ede8d3d9a9b85099d'
ERROR = 'Error executing tool ck3_auto_turn: this decision was already published; no action replay'


def require(ok, reason):
    if not ok:
        raise ValueError('partial Sway143 recap denied: ' + reason)


def read_pin(reference, limit=1024**2):
    path = Path(reference['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == reference['bytes']
            and hashlib.sha256(raw).hexdigest() == reference['sha256'], 'exact input pin differs')
    return json.loads(raw)


def validate_admission(admission):
    require(admission.get('schema') == 'xar.partial-sway143-recap-admission/v1'
            and admission.get('machine_id') == 'xenoamess-full-tower-eb9d2c1186', 'finite reviewed admission')
    require(admission['source_review']['sha256'] == META_SHA, 'exact prior partial source review')
    meta = read_pin(admission['source_review'])
    require(meta.get('machine_id') == admission['machine_id']
            and meta.get('schema') == 'xar.p51-auto143-partial-readonly-freeze/v1', 'review machine/schema')
    files = {}
    for item in meta['files']:
        value = read_pin({'path': item['frozen_path'], 'bytes': item['bytes'], 'sha256': item['sha256']})
        files[Path(item['original_path']).name] = value
    for item in meta['immutable_source_pins']:
        path = Path(item['path'])
        with path.open('rb') as stream:
            raw = stream.read(1024**2 + 1)
        require(len(raw) <= 1024**2 and len(raw) == item['bytes']
                and hashlib.sha256(raw).hexdigest() == item['sha256'], 'actual reviewed control-flow source changed')
    flow = meta['control_flow']
    require(flow.get('first_before_submit_published') is True
            and flow.get('optional_branch') == 'observe_applied existing-instance read-only lifecycle'
            and flow.get('following_ordinary_driver_dispatch_occurred') is False
            and flow.get('new_Sway_submit_from143') is False
            and flow.get('readonly_native_observations_did_occur') is True
            and flow.get('following_selected_step_persisted') is False
            and flow.get('optional_summary_return_value_retained') is False,
            'partial-only source control flow differs')
    state = read_pin(admission['retained_state'])
    pending = state.get('pending_cycle') or {}
    require(state.get('completed_cycles') == 57 and pending.get('global_turn') == 58
            and pending.get('auto_sequence') == 143 and pending.get('stage') == 'auto_unsettled'
            and pending.get('before') == state.get('before')
            and state.get('pending_checkpoint') is None and state.get('terminal') is None,
            'exact57 complete / pending58 branch required')
    row = files['0143-1-result.json']
    result = row.get('result') or {}
    content = result.get('content') or []
    require(row.get('client_error') is None and row.get('request', {}).get('sequence') == 143
            and row['request'].get('tool') == 'ck3_auto_turn' and row['request'].get('arguments') == {}
            and result.get('is_error') is True and result.get('result_type') == 'complete'
            and result.get('structured_content') is None and len(content) == 1
            and content[0].get('type') == 'text' and content[0].get('text') == ERROR,
            'original complete MCP error must remain failed')
    schedule = files['ordinary-sway-schedule-v1.json']
    ledger = files['active-scheme-sway-formal-private-v1.json']
    resolved = ledger.get('resolved') or {}
    observation = resolved.get('latest_instance_observation') or {}
    material = resolved.get('material_intervention') or {}
    require(ledger.get('pending') is None and resolved.get('action_id') == 'sway-88765ff2258b45f88acb5eeabc1f63c2'
            and schedule.get('last_observation_attempt_action_id') == resolved['action_id']
            and schedule.get('last_job_kind') == 'observe_applied'
            and schedule.get('last_check_date_raw') == 53145048
            and schedule.get('next_check_date_raw') == 53145768
            and schedule.get('last_terminal_action_id') is None, 'actual prior ledger/cooldown must remain intact')
    for value in (observation, material):
        require(value.get('action_id') == resolved['action_id'] and value.get('actor_character_id') == 31254
                and value.get('target_character_id') == 33946 and value.get('scheme_instance_id') == 2
                and value.get('scheme_instance_generation') == 0
                and value.get('source_native_revision') == 58 and value.get('source_date_raw') == 53145048,
                'full existing-instance read identity differs')
    require(material.get('dedicated_benefit_observed') is False, 'no named-benefit claim is supported')
    return meta, state, row


def project(state, frame, semantic_path, audit_path):
    require(frame['date_raw'] == state['before']['date_raw'], 'zero-day recap only')
    changed = copy.deepcopy(state)
    changed['before'] = {key: frame[key] for key in
        ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'actor_character_id', 'episode_run_id')}
    changed['before_metrics_response'] = str(semantic_path)
    changed['pending_cycle'] = None
    changed['partial_readonly_recovery_last'] = {'original_auto_sequence': 143,
        'audit': str(audit_path), 'ordinary_cycle_credit': 0, 'game_day_credit': 0,
        'new_Sway_Start_credit': 0, 'named_benefit_inferred': False,
        'completed_existing_instance_read_observed': True, 'original_auto_replayed': False}
    require(changed['completed_cycles'] == 57 and changed['counts'] == state['counts'], 'complete counters changed')
    return changed


async def recover(queue, session, request, path, env, *, admission_pin, birth_reader):
    admission = read_pin(admission_pin)
    meta, preserved, original_row = validate_admission(admission)
    root = env['Q'].parent
    require(request.get('command') == 'recover_partial_life_advance'
            and request.get('arguments') == {'recovery_kind': KIND} and 'tool' not in request,
            'explicit local partial recap control only')
    require(request.get('sequence') == queue.next_sequence == 144
            and path == env['INBOX'] / '0144-1-result.json', 'one exact unused control144')
    require(queue.full_loop_state == preserved
            and env['read'](env['Q'] / 'ROOT-CUMULATIVE-LOOP-STATE.json', 65536) == preserved,
            'retained complete state differs')
    original_path = env['OUTBOX'] / '0143-1-result.json'
    require(queue.halted.get('request') == original_row['request']
            and queue.halted.get('row') == original_row and queue.halted.get('response') == str(original_path)
            and env['read'](original_path, 16384) == original_row, 'original halted error changed')
    require(queue.launch.get('pid') == 214568 and queue.launch.get('creation_filetime') == 134368503807325674
            and queue.job.get('game_creation_filetime') == 134368503807325674,
            'exact retained Game generation')
    def ownership():
        queue.guard()
        require(birth_reader(214568) == 134368503807325674, 'Game generation changed')
    def unchanged_ledgers():
        for item in meta['files']:
            if Path(item['original_path']).name in ('active-scheme-sway-formal-private-v1.json', 'ordinary-sway-schedule-v1.json'):
                read_pin({'path': item['original_path'], 'bytes': item['bytes'], 'sha256': item['sha256']})
    ownership(); unchanged_ledgers()
    intent = env['Q'] / 'PARTIAL-SWAY143-RECAP-INTENT.json'
    env['atomic'](intent, {'source_review': admission['source_review'], 'control': request,
        'original_AUTO_replay_allowed': False}, limit=16384)
    queue.consume_sequence(request)
    queue.held_control = path.name
    child = {'sequence': queue.next_sequence, 'tool': env['SEMANTIC'], 'arguments': {},
        'source': 'Root approved partial143 recap; one fresh readonly SEM; original AUTO stays failed'}
    child_path = env['INBOX'] / f"{child['sequence']:04d}-1-result.json"
    env['atomic'](child_path, child, limit=16384)
    ownership()
    queue.consume_sequence(child)
    env['atomic'](env['Q'] / f"INFLIGHT-{child['sequence']:04d}.json", {'request': child, 'replay_allowed': False}, limit=16384)
    start, tick = env['now']().isoformat(), time.monotonic()
    try:
        actual = await session.call_tool(env['SEMANTIC'], {}, read_timeout_seconds=queue.call_budget(env['SEMANTIC']))
        row = {'started_at_utc': start, 'ended_at_utc': env['now']().isoformat(),
            'elapsed_seconds': time.monotonic() - tick, 'request': child, 'result': actual.model_dump(mode='json')}
    except Exception as error:
        row = {'started_at_utc': start, 'ended_at_utc': env['now']().isoformat(),
            'elapsed_seconds': time.monotonic() - tick, 'request': child, 'client_error': repr(error), 'replay_allowed': False}
    semantic_path = env['OUTBOX'] / child_path.name
    env['atomic'](semantic_path, row, limit=env['REPLY_RESERVE'])
    ownership(); unchanged_ledgers()
    semantic = env['decoded'](row)
    from root_p37_normal_map_known_pause_recovery import checked_semantic
    from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1
    frame = checked_semantic(semantic, before=preserved['before'], launch=queue.launch,
        lifecycle=queue.expected_lifecycle_binding, normalize_lifecycle=normalize_succession_lifecycle_binding_v1,
        expected_paused=True)
    require(frame['date_raw'] == 53145048 and frame['connection_generation'] == 4
            and frame['actor_character_id'] == 31254 and frame['native_revision'] >= 58
            and frame['episode_run_id'] == 'native-31254-6271ac8cd441'
            and frame['decision_identity'] == ('normal_map_no_modal',), 'fresh exact paused zero-day frame required')
    audit_path = env['Q'] / 'PARTIAL-SWAY143-RECAP-COMPLETED.json'
    audit = {'schema': 'xar.partial-sway143-recap/v1', 'machine_id': admission['machine_id'],
        'observed_at_utc': env['now']().isoformat(), 'source_review': admission['source_review'],
        'original_AUTO143_still_failed': True, 'completed_cycles_before_after': 57,
        'ordinary_cycle_credit': 0, 'game_day_credit': 0, 'new_Sway_Start_credit': 0,
        'completed_existing_instance_read_observed': True, 'overall_observer_summary_inferred': False,
        'named_benefit_inferred': False, 'fallback_submission_inferred': False,
        'source_partial_instance': meta['actual_readonly_instance'], 'fresh_frame': frame,
        'fresh_semantic_response': str(semantic_path), 'new_readonly_SEM_calls': 1,
        'new_AUTO_or_action_calls': 0, 'original_auto_replayed': False, 'ledger_or_publication_history_reset': False}
    env['atomic'](audit_path, audit, limit=32768)
    projected = project(preserved, frame, semantic_path, audit_path)
    original_state = queue.full_loop_state
    queue.full_loop_state = projected
    try:
        queue.persist_loop_state()
    except Exception:
        queue.full_loop_state = original_state
        raise
    queue.semantic = semantic
    result = {'status': 'source_bound_partial_readonly_recapped', 'audit': str(audit_path),
        'completed_cycles': 57, 'ordinary_cycle_credit': 0, 'game_day_credit': 0,
        'original_auto_replayed': False, 'new_AUTO_or_action_calls': 0,
        'new_readonly_SEM_calls': 1, 'next_sequence': queue.next_sequence, 'new_auto_admitted': True}
    env['atomic'](env['OUTBOX'] / path.name, {'request': request,
        'result': {'is_error': False, 'structured_content': result}}, limit=16384)
    queue.halted = queue.current_attempt = queue.held_control = None
    return result
