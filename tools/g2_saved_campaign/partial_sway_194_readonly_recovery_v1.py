"""Finite AUTO194 readonly recap from its own frozen source proof; no new RPC."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

KIND = 'partial_sway_readonly_194_zero_rpc'
META_SHA = '6cf39a4277e95cf660840e2728c201fc779497cc0b16c237c03a99f06cc0d1aa'
FREEZE_SHA = '172fdb55db129166f44d1b95caaf6cedade57deb23bf0eb1d83541d8033c048f'
MET_SHA = 'd40c98fd93f29609f80e4f8ae8990da8e54253dbcfc863a5709cd27c7485a383'


def require(ok, reason):
    if not ok:
        raise ValueError('partial readonly194 denied: ' + reason)


def pinned(ref, limit=1024**2):
    path = Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == ref['bytes']
        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'exact source changed: ' + str(path))
    return json.loads(raw)


def validate(admission):
    require(admission.get('schema') == 'xar.partial-sway194-readonly-admission/v1'
        and admission.get('machine_id') == 'xenoamess-full-tower-eb9d2c1186', 'reviewed admission machine/schema')
    require(admission['source_review']['sha256'] == META_SHA
        and admission['state_freeze']['sha256'] == FREEZE_SHA
        and admission['before_metrics']['sha256'] == MET_SHA, '194 own sealed proof required')
    meta = pinned(admission['source_review'])
    freeze = pinned(admission['state_freeze'])
    require(meta.get('schema') == 'xar.p51-auto194-partial-readonly-freeze/v1'
        and meta.get('machine_id') == freeze.get('machine_id') == admission['machine_id']
        and freeze.get('next_sequence') == 195 and freeze.get('completed_cycles') == 74,
        'sealed194/74/next195 proof differs')
    files = {}
    for ref in meta['files']:
        frozen = {'path': ref['frozen_path'], 'bytes': ref['bytes'], 'sha256': ref['sha256']}
        files[Path(ref['original_path']).name] = pinned(frozen)
        pinned({'path': ref['original_path'], 'bytes': ref['bytes'], 'sha256': ref['sha256']})
    for ref in meta['immutable_source_pins']:
        path = Path(ref['path']); raw = path.read_bytes()
        require(len(raw) <= 1024**2 and len(raw) == ref['bytes']
            and hashlib.sha256(raw).hexdigest() == ref['sha256'], '194 actual producer/control-flow source changed')
    retained = {}
    for ref in freeze['source_entries']:
        value = pinned({'path': ref['frozen_path'], 'bytes': ref['bytes'], 'sha256': ref['sha256']}, 16384)
        require(pinned({'path': ref['source_path'], 'bytes': ref['bytes'], 'sha256': ref['sha256']}, 16384) == value,
            'current retained state differs from sealed input')
        retained[Path(ref['source_path']).name] = value
    state = retained['ROOT-CUMULATIVE-LOOP-STATE.json']
    pending = state.get('pending_cycle') or {}
    before = state.get('before') or {}
    require(state.get('completed_cycles') == 74 and pending.get('global_turn') == 75
        and pending.get('auto_sequence') == 194 and pending.get('stage') == 'auto_unsettled'
        and pending.get('before') == before and pending.get('before_metrics_response') == state.get('before_metrics_response')
        and all(state.get(k) is None for k in ('pending_checkpoint', 'terminal',
            'pending_natural_succession', 'pending_unsafe_route_halt'))
        and before == {'snapshot_id': 'native:98', 'revision': 62, 'native_revision': 98,
            'date_raw': 53145792, 'actor_character_id': 31254, 'episode_run_id': 'native-31254-6271ac8cd441'},
        'actual74/pending75/before98-date61 differs')
    row = files['0194-1-result.json']; result = row.get('result') or {}
    content = result.get('content') or []
    require(row == meta['original_error'] and row.get('client_error') is None
        and row.get('request', {}).get('sequence') == 194 and row['request'].get('tool') == 'ck3_auto_turn'
        and row['request'].get('arguments') == {} and result.get('is_error') is True
        and result.get('result_type') == 'complete' and result.get('structured_content') is None
        and len(content) == 1 and content[0].get('type') == 'text'
        and content[0].get('text') == 'Error executing tool ck3_auto_turn: this decision was already published; no action replay',
        '194 must remain its completed original MCP error')
    flow = meta['control_flow']
    require(flow.get('first_before_submit_published') is True
        and flow.get('optional_branch') == 'observe_applied existing-instance read-only lifecycle'
        and flow.get('following_ordinary_driver_dispatch_occurred') is False
        and flow.get('new_Sway_submit_from194') is False
        and flow.get('readonly_native_observations_did_occur') is True
        and flow.get('following_selected_step_persisted') is False
        and flow.get('optional_summary_return_value_retained') is False, 'only source-proved readonly partial qualifies')
    plan = meta['original_plan']
    require(plan.get('snapshot_id') == before['snapshot_id'] and plan.get('revision') == before['revision']
        and plan.get('selected_step') == plan.get('plan', {}).get('selected_step') == 'ordinary-sway-opportunity-v1'
        and plan['plan'].get('phase') == 'native_war_entry_forecast_required'
        and plan['plan'].get('decision', {}).get('outcome') == 'NO_DECLARE', '194 first plan frame/context differs')
    ledger, schedule = files['active-scheme-sway-formal-private-v1.json'], files['ordinary-sway-schedule-v1.json']
    resolved = ledger.get('resolved') or {}; observation = resolved.get('latest_instance_observation') or {}
    material = resolved.get('material_intervention') or {}
    identity = {'action_id': 'sway-88765ff2258b45f88acb5eeabc1f63c2', 'actor_character_id': 31254,
        'target_character_id': 33946, 'scheme_instance_id': 2, 'scheme_instance_generation': 0,
        'source_native_revision': 98, 'source_date_raw': 53145792}
    require(ledger.get('pending') is None and all(all(value.get(k) == v for k, v in identity.items())
        for value in (observation, material)) and material.get('dedicated_benefit_observed') is False
        and schedule == meta['schedule'] and schedule.get('last_job_kind') == 'observe_applied'
        and schedule.get('last_check_date_raw') == before['date_raw']
        and schedule.get('next_check_date_raw') == 53146512
        and schedule.get('last_observation_attempt_action_id') == identity['action_id']
        and schedule.get('last_terminal_action_id') is None, '194 exact existing-instance/cooldown evidence differs')
    metrics = pinned(admission['before_metrics'], 32768)
    require(metrics.get('request', {}).get('sequence') == 193
        and metrics['request'].get('tool') == 'root_current_runtime_metrics'
        and metrics['request'].get('arguments') == {} and metrics.get('client_error') is None
        and metrics.get('result', {}).get('is_error') is False
        and metrics['result'].get('result_type') == 'complete', 'actual preceding successful readonlyMET193 required')
    return meta, retained, row, metrics


async def recover(queue, session, request, path, env, *, admission, birth_reader):
    meta, retained, original_row, metrics = validate(admission)
    state = retained['ROOT-CUMULATIVE-LOOP-STATE.json']; before = state['before']; root = env['N'].resolve()
    require(request == {'sequence': 195, 'command': 'recover_known_owner_1024',
        'arguments': {'recovery_kind': KIND}} and queue.next_sequence == 195
        and path == env['INBOX'] / '0195-1-result.json', 'one exact local195 control')
    require(queue.full_loop_state == state and isinstance(queue.halted, dict)
        and queue.halted.get('request') == original_row['request'] and queue.halted.get('row') == original_row
        and queue.halted.get('response') == str(env['OUTBOX'] / '0194-1-result.json'), 'live retained194/state differs')
    gov = retained['ROOT-GOVERNANCE-RESULT-STATE.json']
    require(queue.governance_result_state == gov['state'] and queue.lifestyle_pending_focus == gov['pending_focus']
        and queue.result_classifier_pin == gov['classifier'], 'live governance/classifier differs')
    binding = meta['source_binding']
    require(Path(binding['runtime']).resolve() == root and binding['game_pid'] == queue.launch.get('pid') == 214568
        and binding['game_creation_filetime'] == queue.launch.get('creation_filetime') == 134368503807325674
        and queue.job.get('game_creation_filetime') == 134368503807325674
        and queue.checkpoint_bootstrap_verified is True, 'same C3 actual Game/bootstrap required')
    require(birth_reader(214568) == 134368503807325674, 'current kernel Game birth differs')
    body = env['decoded'](metrics)
    require(env['frame'](body) == before and body.get('paused') is True and body.get('map_ready') is True
        and body.get('actor_alive') is True and body.get('connection_generation') == 4
        and state['before_metrics_response'] == admission['before_metrics']['path'], '193 actual paused same frame differs')
    audit_path = env['Q'] / 'PARTIAL-SWAY194-READONLY-RECAP.json'
    require(not audit_path.exists(), '194 local partial already processed')
    changed = copy.deepcopy(state)
    changed['pending_cycle'] = None
    changed['partial_readonly_recovery_last'] = {'original_auto_sequence': 194, 'audit': str(audit_path),
        'ordinary_cycle_credit': 0, 'game_day_credit': 0, 'new_Sway_Start_credit': 0,
        'named_benefit_inferred': False, 'completed_existing_instance_read_observed': True,
        'original_auto_replayed': False, 'new_RPC_calls': 0}
    require(changed['completed_cycles'] == 74 and changed['counts'] == state['counts']
        and changed['before'] == before and changed['actual_saved_checkpoint'] == state['actual_saved_checkpoint'],
        'settled credit/date/actual checkpoint changed')
    audit = {'schema': 'xar.partial-sway194-readonly-recap/v1', 'machine_id': admission['machine_id'],
        'observed_at_utc': env['now']().isoformat(), 'source_review': admission['source_review'],
        'state_freeze': admission['state_freeze'], 'before_metrics': admission['before_metrics'],
        'original_AUTO194_still_failed': True, 'completed_cycles_before_after': 74,
        'partial_observation': meta['actual_readonly_instance'], 'ordinary_cycle_credit': 0,
        'game_day_credit': 0, 'new_RPC_calls': 0, 'new_action_calls': 0,
        'new_Sway_Start_credit': 0, 'named_benefit_inferred': False, 'full_AUTO_summary_inferred': False,
        'original_auto_replayed': False, 'ledger_or_publication_history_reset': False,
        'fresh_SEM_SAVE_still_required_for_new_day61_checkpoint': True}
    queue.consume_sequence(request)
    env['atomic'](audit_path, audit, limit=16384)
    previous = queue.full_loop_state; queue.full_loop_state = changed
    try:
        queue.persist_loop_state()
    except Exception:
        queue.full_loop_state = previous
        raise
    receipt = {**audit, 'status': 'source_bound_partial_readonly194_recapped', 'audit': str(audit_path),
        'next_sequence': queue.next_sequence, 'new_auto_admitted': False, 'ready_for_fresh_SEM_SAVE': True}
    env['atomic'](env['OUTBOX'] / path.name, {'request': request,
        'result': {'is_error': False, 'structured_content': receipt}}, limit=16384)
    queue.halted = queue.current_attempt = queue.held_control = None
    queue.halt_cause = None
    return receipt
