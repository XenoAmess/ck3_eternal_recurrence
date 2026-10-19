"""One source-bound observation of C16 AUTO8495; no pause or close submission."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import time

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
ROOT = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T = ROOT / 'robert30-v20261019-campaign01/runtime'
F91 = ROOT / 'p51-fresh1066-v20261019-prepare01/c16-war-results8495-failure91'
KIND = 'c16_war_results8495_observe_only'
SCHEMA = 'xar.c16.war-results8495-observation-reconcile/v1'
SEM = 'ck3_take_semantic_snapshot_private_v1'
QUERY = 'ck3_query_war_results_window_v1'
ENTRY_NAME = 'root_p37c16_war_results8495_reconcile.py'
DISPATCH_SHA = 'bfc3de2ca01045e8ce544f027b573dc4f5f0279709a073cb46306b1e4a556824'
QUEUE_SHA = '58f6ff2126793cb1c2f1d61f37ea8f9057c65fe1e53e84fdf921d33ab8ee9d83'
PINS = {
    'state.json': (8466, '3e3e13c6521e92a61c939e418bb0b642250ace7c4040add858bc4f3d3eb14dba'),
    'auto8495.json': (19980, '7cb2ed83a6342107ca399c97e81995b90fdbdde56b0b938c2e455bc85fa7e14b'),
    'plan8495.json': (775, 'e40735a056623d6d22baf85dee97c08cc03b2675c6319919b7f07d31c4cd39f1'),
    'governance-exact.json': (887, '848541b534654de29f91c004900b0128a92f2d48600e59be21a4c8e2bd8016d4'),
    'CONTROL-AND-METADATA-SUPPLEMENT.json': (2749, '17b877f70049be89e6de127ba2274f2f280454e04d57e51d2b3565c48d575300'),
}
OLD_ID = 'war-overview-close-81c0fd943b204e8aae7667a51d922916'
OLD_OWNER = {'request_id': OLD_ID, 'ticket_sequence': 2243,
    'executor_started_sequence': 2243, 'completed_sequence': 2243,
    'pump_epoch': 189498, 'thread_id': 227468, 'date_raw': 53217048,
    'connection_generation': 1}
FRAME_KEYS = ('snapshot_id', 'revision', 'native_revision', 'date_raw',
              'actor_character_id', 'episode_run_id')


def require(ok, why):
    if not ok:
        raise ValueError('C16 AUTO8495 observation denied: ' + why)


def pinned(name):
    path = F91 / name
    with path.open('rb') as stream:
        raw = stream.read(65537)
    size, digest = PINS[name]
    require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
            'closed original changed: ' + name)
    return json.loads(raw)


def qualify(queue, request, path, env, birth_reader):
    require(request == {'sequence': 8496, 'command': 'recover_partial_life_advance',
        'arguments': {'recovery_kind': KIND}}, 'one exact unused control8496 required')
    require(path == env['INBOX'] / '8496-1-result.json' and queue.next_sequence == 8496,
            'actual next sequence/path differs')
    require(env['Q'] == T / 'p37-queue' and env['OUTBOX'] == T / 'p37-responses',
            'actual C16 namespace differs')
    require(queue.launch.get('pid') == 30852
        and queue.launch.get('creation_filetime') == 134368995759027619
        and queue.job.get('game_creation_filetime') == 134368995759027619
        and birth_reader(30852) == 134368995759027619,
        'exact retained Game generation required')
    require(hashlib.sha256((T / 'root_p37c16_sdk_queue.py').read_bytes()).hexdigest() == QUEUE_SHA,
            'actual Queue source differs')
    original, state = queue.halted, queue.full_loop_state
    row, frozen_state = pinned('auto8495.json'), pinned('state.json')
    plan, gov = pinned('plan8495.json'), pinned('governance-exact.json')
    history = pinned('CONTROL-AND-METADATA-SUPPLEMENT.json')
    require(history['machine_id'] == MACHINE and history['non_FULL_local_controls'] == [],
            'unused lazy recovery entry proof differs')
    require(state == frozen_state and env['read'](env['Q'] / 'ROOT-CUMULATIVE-LOOP-STATE.json') == state
        and env['read'](env['Q'] / 'ROOT-GOVERNANCE-RESULT-STATE.json') == gov,
        'in-memory and closed current state/governance differ')
    require(isinstance(original, dict) and original.get('request') == row['request']
        and original.get('row') == row
        and Path(original.get('response', '')) == T / 'p37-responses/8495-1-result.json'
        and env['read'](Path(original['response']), 65536) == row,
        'original completed AUTO8495 halt differs')
    body = row['result']['structured_content']; close = body['result']
    require(row.get('client_error') is None and row['result']['is_error'] is False
        and row['result']['result_type'] == 'complete' and body['status'] == 'pending'
        and body['selected_step'] == body['plan']['selected_step'] == 'close-war-results-window-v1'
        and body['ui_action_credit'] is False
        and close['native_request_id'] == OLD_ID
        and close['native_command_result']['war_results_window_owner_receipt'] == OLD_OWNER
        and close['dispatch_invoked'] is close['native_handled'] is True
        and close['closure_verified'] is False
        and close['scope_transition_pause']['status'] == 'pause_unverified'
        and close['scope_transition_pause']['close_replayed'] is False,
        'original completed callback is not the exact unverified close')
    require(plan['game_pid'] == 30852 and plan['request']['parent_sequence'] == 8495
        and plan['result']['structured_content']['selected_step'] == body['selected_step']
        and env['read'](env['OUTBOX'] / '8495-0-plan.json', 65536) == plan,
        'actual before-submit source differs')
    pending = state['pending_cycle']
    require(state['completed_cycles'] == 3828 and pending['global_turn'] == 3829
        and pending['auto_sequence'] == 8495 and pending['stage'] == 'auto_unsettled'
        and pending['before'] == state['before'] and state['pending_checkpoint'] is None
        and state['terminal'] is None and queue.checkpoint_bootstrap_verified is True,
        'only original unsettled close branch is admitted')
    return copy.deepcopy(pending)


def checked_frame(body, queue, previous=None):
    diagnostics = body.get('diagnostics') or {}; hello = diagnostics.get('hello') or {}
    actor = body.get('played_character') or {}; before = queue.full_loop_state['before']
    require(body.get('map_ready') is True and body.get('paused') is True
        and body.get('one_life_terminal') is False and actor.get('alive') is True
        and actor.get('character_id') == before['actor_character_id'] == 40526
        and body.get('episode_run_id') == before['episode_run_id']
        and type(body.get('date_raw')) is int and body['date_raw'] >= 53217072
        and diagnostics.get('bridge_pid') == hello.get('pid') == 30852
        and diagnostics.get('connection_generation') == hello.get('connection_generation') == 1
        and body.get('succession_lifecycle') == queue.expected_lifecycle_binding,
        'fresh paused same-Game/actor/episode/lifecycle required; no new pause admitted')
    require(type(body.get('native_revision')) is int and body['native_revision'] >= 1126
        and type(body.get('revision')) is int and body['revision'] >= 1127
        and body.get('snapshot_id') == 'native:' + str(body['native_revision']),
        'fresh source revision regressed')
    frame = {k: body[k] for k in FRAME_KEYS if k != 'actor_character_id'}
    frame['actor_character_id'] = actor['character_id']
    frame['connection_generation'] = 1
    if previous is not None:
        require(frame == previous, 'window query crossed its exact paused semantic frame')
    return frame


def checked_query(dto, actual):
    require(isinstance(dto, dict) and dto.get('schema') == 'ck3-war-results-window-v1'
        and dto.get('operation') == 'query' and dto.get('step') == 'query-war-results-window-v1'
        and dto.get('window_name') == 'war_results'
        and dto.get('sdk_validation_schema') == 'war-results-window-source-v1', 'typed query source differs')
    for flag in ('available', 'accepted', 'root_observed', 'post_observed',
                 'scope_unchanged', 'application_owner_thread_verified', 'paused'):
        require(dto.get(flag) is True, 'query observation not verified: ' + flag)
    for flag in ('dispatch_attempted', 'dispatch_invoked', 'native_handled', 'closure_verified'):
        require(dto.get(flag) is False, 'query carried close dispatch/credit: ' + flag)
    for k, v in {'queried_snapshot_id': 'snapshot_id', 'queried_revision': 'revision',
        'queried_native_revision': 'native_revision', 'queried_date_raw': 'date_raw',
        'queried_actor_character_id': 'actor_character_id',
        'queried_episode_run_id': 'episode_run_id',
        'queried_connection_generation': 'connection_generation'}.items():
        require(type(dto.get(k)) is type(actual[v]) and dto[k] == actual[v], 'query lease differs: ' + k)
    top = dto.get('native_command_result') or {}; receipt = top.get('war_results_window_owner_receipt') or {}
    request_id = dto.get('native_request_id')
    require(isinstance(request_id, str) and request_id.startswith('war-overview-query-')
        and request_id != OLD_ID and dto.get('request_id') == request_id
        and top.get('type') == 'command_result' and top.get('protocol_version') == 1
        and top.get('request_id') == request_id and top.get('ok') is True
        and receipt.get('request_id') == request_id
        and type(receipt.get('ticket_sequence')) is int
        and receipt['ticket_sequence'] == receipt.get('executor_started_sequence')
        == receipt.get('completed_sequence') == dto.get('ticket_sequence')
        and receipt['ticket_sequence'] > OLD_OWNER['ticket_sequence']
        and type(receipt.get('pump_epoch')) is int and receipt['pump_epoch'] > OLD_OWNER['pump_epoch']
        and receipt.get('thread_id') == OLD_OWNER['thread_id']
        and receipt.get('connection_generation') == 1 and receipt.get('date_raw') == actual['date_raw'],
        'independent newer same-owner query receipt differs')
    prior = dto.get('prior_close_execution_observation') or {}
    require(prior.get('native_request_id') == OLD_ID
        and prior.get('status') == 'callback_completed_closure_unverified'
        and prior.get('original_owner_receipt') == OLD_OWNER
        and prior.get('followup_query_request_id') == request_id
        and prior.get('original_action_replayed') is False and prior.get('close_action_credit') is False,
        'query did not reconcile the exact original callback')
    present, visible = dto.get('post_window_present'), dto.get('post_effective_visible')
    require(type(present) is bool and type(visible) is bool and (present or not visible)
        and prior.get('fresh_window_visible') is visible, 'post window observation malformed')
    presence = 'visible' if visible else 'hidden' if present else 'absent'
    require(dto.get('status') == presence, 'window status differs from actual post visibility')
    return presence


def projected(state, frame, source, audit_path):
    result = copy.deepcopy(state)
    result.update(before={k: frame[k] for k in FRAME_KEYS}, before_metrics_response=str(source), pending_cycle=None)
    result['checkpoint_dirty_since_save'] = bool(state.get('checkpoint_dirty_since_save')
        or frame['date_raw'] > state['before']['date_raw'])
    result['war_results8495_observation_reconcile'] = {'audit': str(audit_path),
        'original_close_outcome': 'callback_completed_closure_unverified',
        'original_close_replayed': False, 'failed_pending_business_credit': 0,
        'ordinary_cycle_credit': 0, 'ui_closure_credit': 0}
    return result


async def recover(queue, session, request, path, env, *, birth_reader):
    from root_p37c16_overlay_relay import relay_compact, error_projection
    pending = qualify(queue, request, path, env, birth_reader)
    state = queue.full_loop_state
    audit_path = env['Q'] / 'WAR-RESULTS8495-OBSERVATION-8496.json'
    require(not audit_path.exists(), 'this exact recovery was already attempted')
    audit = {'schema': SCHEMA, 'machine_id': MACHINE, 'utc': env['now']().isoformat(),
        'original_auto': 8495, 'original_response_sha256': PINS['auto8495.json'][1],
        'original_plan_sha256': PINS['plan8495.json'][1], 'original_close': OLD_OWNER,
        'original_pending': pending, 'completed_cycles_before_after': 3828,
        'ordinary_cycle_credit': 0, 'ui_closure_credit': 0, 'new_pause_submissions': 0,
        'new_close_submissions': 0, 'original_action_replayed': False, 'calls': [], 'status': 'attempting'}

    def guard():
        queue.guard()
        require(birth_reader(30852) == 134368995759027619, 'actual Game birth changed')

    def save_audit():
        env['atomic'](audit_path, audit, replace=True, limit=32768)

    async def fresh(tool, arguments):
        guard()
        require(tool in (SEM, QUERY), 'only finite read-only observations are admitted')
        sequence = queue.next_sequence
        child = {'sequence': sequence, 'tool': tool, 'arguments': arguments, 'source': SCHEMA}
        inbox = env['INBOX'] / f'{sequence:04d}-1-result.json'
        response = env['OUTBOX'] / inbox.name
        require(not inbox.exists() and not response.exists(), 'unique new observation already attempted')
        env['atomic'](inbox, child, limit=16384)
        queue.consume_sequence(child)
        context = {**child, 'request_file': str(inbox), 'at_utc': env['now']().isoformat(), 'replay_allowed': False}
        env['atomic'](T / 'CURRENT-REQUEST-P37.json', context, replace=True, limit=16384)
        env['atomic'](env['Q'] / f'INFLIGHT-{sequence:04d}.json', context, limit=16384)
        env['atomic'](env['Q'] / f'{sequence:04d}-before-action.json', context, limit=16384)
        item = {'sequence': sequence, 'tool': tool, 'response': str(response), 'status': 'attempted'}
        audit['calls'].append(item); save_audit()
        started, mono = env['now']().isoformat(), time.monotonic()
        try:
            reply = await session.call_tool(tool, arguments, read_timeout_seconds=queue.call_budget(tool))
            row = {'request': child, 'started_at_utc': started, 'ended_at_utc': env['now']().isoformat(),
                'elapsed_seconds': time.monotonic() - mono, 'result': reply.model_dump(mode='json')}
        except Exception as error:
            row = {'request': child, 'started_at_utc': started, 'ended_at_utc': env['now']().isoformat(),
                'elapsed_seconds': time.monotonic() - mono, 'client_error': repr(error), 'replay_allowed': False}
        env['atomic'](response, row, limit=env['REPLY_RESERVE'])
        item.update(status='received', sha256=env['sha256'](response)); save_audit()
        try:
            body = env['decoded'](row)
        except Exception:
            relay_compact(response, error_projection(row))
            raise
        compact = {'request': child, 'ended_at_utc': row['ended_at_utc'],
            'source': 'actual finite AUTO8495 observation; no close or pause replay',
            'result': {'is_error': False, 'structured_content': {k: body[k] for k in
                ('status', 'snapshot_id', 'revision', 'native_revision', 'date_raw', 'paused',
                 'post_window_present', 'post_effective_visible', 'prior_close_execution_observation') if k in body}}}
        relay_compact(response, compact)
        env['atomic'](env['Q'] / f'{sequence:04d}-after-result.json',
            {'request': str(inbox), 'response': str(response), 'tool': tool, 'actual_status': body.get('status')}, limit=16384)
        guard()
        return body, response

    guard()
    queue.consume_sequence(request); queue.held_control = path.name
    env['atomic'](env['Q'] / 'INFLIGHT-8496.json', {'request': request,
        'control_only': True, 'replay_allowed': False}, limit=16384)
    save_audit()
    try:
        first_body, first_path = await fresh(SEM, {})
        first = checked_frame(first_body, queue)
        latch = first_body.get('war_results_window_v1_close_pending')
        require(isinstance(latch, dict) and latch.get('native_request_id') == OLD_ID
            and latch.get('step') == 'close-war-results-window-v1'
            and latch.get('status') == 'verification_pending', 'original pending close latch differs')
        query, query_path = await fresh(QUERY, {'expected_revision': first['revision']})
        presence = checked_query(query, first)
        final_body, final_path = await fresh(SEM, {})
        final = checked_frame(final_body, queue, first)
        require('war_results_window_v1_close_pending' in final_body
            and final_body['war_results_window_v1_close_pending'] is None,
            'follow-up query did not actually clear the original Driver execution latch')
        audit.update(status='observed_clear' if presence != 'visible' else 'visible_pending_retained',
            window_presence=presence, first_frame=first, final_frame=final,
            first_semantic=str(first_path), query_response=str(query_path), final_semantic=str(final_path),
            physical_date_drift_raw=final['date_raw'] - state['before']['date_raw'],
            physical_drift_credited=False, query_may_clear_driver_execution_latch=True,
            driver_latch_unchanged_claimed=False, query_original=query)
        save_audit()
        if presence != 'visible':
            changed = projected(state, final, final_path, audit_path)
            queue.full_loop_state = changed
            try:
                queue.persist_loop_state()
            except Exception:
                queue.full_loop_state = state
                raise
            queue.semantic = queue.reinforcement_semantic = final_body
            queue.reinforcement_frame = {k: final[k] for k in FRAME_KEYS}
            queue.reinforcement_frame_response = str(final_path)
        result = {k: audit[k] for k in ('schema', 'machine_id', 'status', 'window_presence',
            'completed_cycles_before_after', 'ordinary_cycle_credit', 'ui_closure_credit',
            'new_pause_submissions', 'new_close_submissions', 'original_action_replayed')}
        result.update(audit=str(audit_path), pending_retained=presence == 'visible',
            new_auto_admitted=presence != 'visible', final_semantic_response=str(final_path))
        env['atomic'](env['OUTBOX'] / path.name,
            {'request': request, 'result': {'is_error': False, 'structured_content': result}}, limit=16384)
        queue.held_control = None
        if presence != 'visible':
            queue.halted = queue.current_attempt = None
            env['atomic'](T / 'ROOT-CURRENT-HALT-P37.json', result, replace=True, limit=16384)
        return result
    except Exception as error:
        audit.update(status='failed_retained', error_type=type(error).__name__, error=str(error)[:2048])
        save_audit()
        raise


def build_sources(dispatch_source):
    """Pure finite lazy-dispatch addition; all prior code is byte-preserved."""
    require(hashlib.sha256(dispatch_source).hexdigest() == DISPATCH_SHA, 'original unused dispatcher changed')
    text = dispatch_source.decode('utf-8')
    anchor = 'async def recover(queue, session, request, path, env, *, birth_reader=process_birth_filetime):\n'
    require(text.count(anchor) == 1, 'unique original lazy dispatcher required')
    addition = ("    if request.get('arguments') == {'recovery_kind': '" + KIND + "'}:\n"
        "        from root_p37c16_war_results8495_reconcile import recover as recover8495\n"
        "        return await recover8495(queue, session, request, path, env, birth_reader=birth_reader)\n")
    changed = text.replace(anchor, anchor + addition, 1)
    require(changed.replace(anchor + addition, anchor, 1) == text, 'prior dispatcher changed')
    ast.parse(changed)
    return {ENTRY_NAME: Path(__file__).read_bytes(), 'root_p37_known_pause_recovery_control.py': changed.encode('utf-8')}
