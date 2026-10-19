"""One local C3 metadata halt clear. The successful MET is never reissued."""
from __future__ import annotations
import copy
import hashlib
import json

PINS = {
    'p37-responses/0148-1-result.json': '80c9de3c0227bd03dedf14417684856b8d8365a0fa24efc2ef4437060b1b0833',
    'p37-responses/0153-1-result.json': 'b144a3ad7e27c4413e59f05601f9e2eb36be38dfe77bf11dff706c8f3aabda32',
    'p37-responses/0154-1-result.json': 'bb904b1550f94aa24210f4aac577f01b6dfa711556fd7881a560f3c2d42f6012',
    'p37-responses/0155-1-result.json': '21b77720a9a9708102c3fb5b2916886ac0418bccfa417b174d99279da412acaf',
    'p37-responses/0156-1-result.json': '0157df7b7e20a1478edfdae39b32b07c9ecd522692f25f1b9fe9e46efc6e0948',
    'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json': 'cf67a0c6f5d266e0bc49800a7242e59fd14ef0071eab89a8f788f1f9d17b5140',
    'ROOT-CURRENT-HALT-P37.json': '05b239d4e8306ea9b356650f7fdc7dc455af826c83dde786f86061d2a1466907',
}


async def recover_completed_metadata_v1(queue, session, request, path, env, *, birth=None):
    def require(ok, reason):
        if not ok:
            raise ValueError('C3 MET153 metadata clear denied: ' + reason)

    require(request == {'sequence': 157, 'command': 'clear_zero_rpc_preflight_rejection',
        'arguments': {'recovery_kind': 'completed_metrics153_metadata154'}}, 'one exact local157 control required')
    require(queue.next_sequence == 157, 'actual monotonic sequence changed')
    root = env['N'].resolve()
    values, sources = {}, []
    for relative, expected in PINS.items():
        source = root / relative
        require(source.stat().st_size <= 16384, 'small sealed evidence bound exceeded')
        raw = source.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'source changed: ' + relative)
        values[relative] = json.loads(raw)
        sources.append({'path': str(source), 'bytes': len(raw), 'sha256': expected})
    original = values['p37-responses/0153-1-result.json']
    original_path = root / 'p37-responses/0153-1-result.json'
    state = values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json']
    require(queue.full_loop_state == state and state.get('completed_cycles') == 58
        and all(state.get(k) is None for k in ('pending_cycle', 'pending_checkpoint', 'terminal',
            'pending_natural_succession', 'pending_unsafe_route_halt')), 'settled58 state or pending work differs')
    require(isinstance(queue.halted, dict) and queue.halted.get('request') == original['request']
        and queue.halted.get('row') == original
        and str(queue.halted.get('response')) == str(original_path),
        'retained completed MET153 differs')
    require(original['request'] == {'sequence': 153, 'tool': env['METRICS'], 'arguments': {}}
        and original.get('client_error') is None and original['result'].get('is_error') is False
        and original['result'].get('result_type') == 'complete', 'MET153 must be successful and readonly')
    require(getattr(queue, 'halt_cause', None) == {'error_type': 'ValueError',
        'message': 'classifier install is not a current clean settled boundary'}, 'original154 cause differs')
    installed = values['p37-responses/0148-1-result.json']['result']['structured_content']
    current_pin = {k: installed[k] for k in ('source', 'sha256')}
    require(queue.result_classifier_pin == current_pin
        and current_pin['sha256'] == '025c08f7e7f6453e38e244b5ecdbaa595edb6f74864efd97084fcc84e325e2b0',
        'actual live148 classifier differs')
    cause = values['p37-responses/0154-1-result.json']
    require(cause.get('request', {}).get('command') == 'install_result_classifier'
        and cause.get('client_error') == queue.halt_cause['message'], '154 was not the known local admission refusal')
    for sequence in (154, 155, 156):
        require(not (env['Q'] / f'INFLIGHT-{sequence:04d}.json').exists()
            and not (env['Q'] / f'{sequence:04d}-before-action.json').exists(), 'later dispatch evidence present')
    body = env['decoded'](original)
    observed = env['frame'](body)
    require(observed == state['before'] and body.get('paused') is True and body.get('map_ready') is True
        and body.get('actor_alive') is True and body.get('connection_generation') == 4
        and observed.get('date_raw') == 53145240 and observed.get('native_revision') == 68,
        'MET153 final paused same frame differs')
    require(queue.launch.get('pid') == 214568
        and queue.launch.get('creation_filetime') == 134368503807325674
        and queue.checkpoint_bootstrap_verified is True, 'same actual Game/bootstrap required')
    if birth is None:
        from root_p37_known_pause_recovery_control import process_birth_filetime
        birth = process_birth_filetime
    require(birth(214568) == 134368503807325674, 'retained Game kernel birth differs')
    receipt = {'schema': 'xar.c3-completed-metrics-metadata-clear/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': env['now']().isoformat(),
        'status': 'completed_readonly_metrics_metadata_halt_cleared', 'sources': sources,
        'completed_cycles': 58, 'current_classifier': current_pin, 'actual_frame': observed,
        'original_successful_MET_reissued': False, 'original_action_replayed': False,
        'new_MCP_or_native_calls': 0, 'new_business_credit': 0, 'new_game_day_credit': 0,
        'counts_unchanged': True, 'fresh_SEM_MET_still_required_for_clean_install': True}
    sequence = queue.consume_sequence(request)
    env['atomic'](env['Q'] / f'METADATA-HALT-CLEARED-{sequence:04d}.json', receipt, limit=16384)
    env['atomic'](root / env['CURRENT_HALT_NAME'], receipt, replace=True, limit=16384)
    env['atomic'](env['OUTBOX'] / path.name, {'request': request,
        'result': {'is_error': False, 'structured_content': receipt}}, limit=16384)
    require(queue.full_loop_state == state, 'settled state changed during local clear')
    queue.halted = queue.current_attempt = queue.held_control = None
    queue.halt_cause = None
    return receipt
