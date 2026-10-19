"""Exact local201 correction after actual198 relay halt and local200 rejection."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

PINS = {
    'p37-responses/0198-1-result.json': '900303320147c02c96f257de6caf75ae6f400523e5010b48b459babaa063a16f',
    'p37-responses/0199-1-result.json': 'a0e4603f08ceb65d4fcbf03da71f0429f91e2777d63d0a2fae001b876fe27cc1',
    'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json': 'c1b83e736d3774c4d4804c24cbea0a2dce54f8ab859afe6be6a72d3e9a3e797e',
    'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json': '34d671291162f5b4aba42708b8287e8a0f94048f25edf649580c06a5d4bfa7ba',
    'p37-queue/ROOT-SAVED61-COLD-BOUND.json': '53b4c0859ddb2eb76e065581bc172e9b30a87016449215059053a9b7adbd354b',
    'NEXT-SEQUENCE-P37.json': '8c7423110d8a00c2667316164e39408f7d1971b5a8f30e67dcc148653487d963',
    'p37-responses/0200-1-result.json': '7e7691b9158902dd1e68731d0a082bcef25ae5e7dd7861d4e61fb63c19b8c226',
    'p37-queue/ROOT-REQUEST-HALTED-0198.json': '41acd49770448614e4fb9e7ab49fdf21c128d0c468093776e97b8371e1a6bf75',
    'p37-queue/ROOT-REQUEST-HALTED-0200.json': '23e99a6c1be0dbb5701888fa23e3e0eb9d45f9ad9675704f5bfcac46bb34a766',
    'ROOT-CURRENT-HALT-P37.json': '23e99a6c1be0dbb5701888fa23e3e0eb9d45f9ad9675704f5bfcac46bb34a766',
    'ROOT-FIRST-QUEUE-EXCEPTION-P37C4.json': 'e55520c2c1e2c27ad967fdcf134418e456238e294439f4d6f9c753efc37bc2db',
}


async def recover(queue, session, request, path, env, *, retained, birth_reader):
    def require(ok, reason):
        if not ok:
            raise ValueError('C4 cold source201 repair denied: ' + reason)
    require(request == {'sequence': 201, 'command': 'recover_known_owner_1024',
        'arguments': {'recovery_kind': 'saved61_cold_semantic_pointer198_and_relay_halt'}},
        'one exact new local201 control')
    require(queue.next_sequence == 201 and queue.held_control is None,
        'current201 boundary without another held control required')
    root = env['N'].resolve(); values = {}; originals = []
    for relative, expected in PINS.items():
        source = root / relative
        require(source.stat().st_size <= 262144, 'bounded exact source exceeded')
        raw = source.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'current source changed: ' + relative)
        frozen = Path(retained[relative]['path'])
        require(frozen.read_bytes() == raw, 'original incorrect metadata was not retained exactly')
        values[relative] = json.loads(raw)
        originals.append({'path': str(frozen), 'bytes': len(raw), 'sha256': expected})
    state = values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json']
    gov = values['p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json']
    bound = values['p37-queue/ROOT-SAVED61-COLD-BOUND.json']
    sem = values['p37-responses/0198-1-result.json']; cap = values['p37-responses/0199-1-result.json']
    halt198 = values['p37-queue/ROOT-REQUEST-HALTED-0198.json']
    require(queue.halted == {'request': sem['request'], 'row': sem,
        'response': str(root / 'p37-responses/0198-1-result.json')}
        and queue.halt_cause == {'error_type': 'ValueError', 'message': 'Foreign cached decision provider'}
        and halt198['error_type'] == 'ValueError' and halt198['message'] == 'Foreign cached decision provider'
        and halt198['original_request'] == sem['request'] and halt198['next_sequence'] == 199,
        'only exact completed198 post-read relay halt is eligible')
    require(values['p37-responses/0200-1-result.json']['client_error']
        == 'C4 cold source200 repair denied: current clean200 boundary required'
        and values['NEXT-SEQUENCE-P37.json']['next_sequence'] == 201,
        'actual local200 rejection/sequence registration differs')
    require(queue.full_loop_state == state and state.get('completed_cycles') == 74
        and all(state.get(k) is None for k in ('pending_cycle', 'pending_checkpoint', 'terminal',
            'pending_natural_succession', 'pending_unsafe_route_halt')), '74 settled/no unknown pending required')
    require(queue.launch.get('pid') == 153556 and queue.launch.get('creation_filetime') == 134368602545256920
        and birth_reader(153556) == 134368602545256920, 'actual C4 Game kernel generation differs')
    require(sem.get('request') == {'sequence': 198, 'tool': env['SEMANTIC'], 'arguments': {}}
        and cap.get('request') == {'sequence': 199, 'tool': env['CAPABILITIES'], 'arguments': {}}
        and sem.get('startup_readiness_attempt') == 1, 'actual readiness198/CAP199 request differs')
    for row in (sem, cap):
        require(row.get('client_error') is None and row.get('result', {}).get('is_error') is False
            and row['result'].get('result_type') == 'complete', 'unknown or failed bootstrap response')
    body = env['decoded'](sem); capbody = env['decoded'](cap); control = capbody.get('native_session_control') or {}
    frame = env['frame'](body, semantic=True, expected_lifecycle=queue.expected_lifecycle_binding)
    require(frame == state['before'] == bound['opening_frame'] == queue.initial_frame
        and frame.get('native_revision') == 1 and frame.get('revision') == 2
        and frame.get('date_raw') == 53145792 and frame.get('actor_character_id') == 31254
        and frame.get('episode_run_id') == capbody.get('episode_run_id') == 'native-31254-6271ac8cd441'
        and queue.semantic == body and control.get('driver_state_restored') is True
        and control.get('driver_state_restore_kind') == 'cold_checkpoint'
        and control.get('episode_binding_state') == 'active_resumed'
        and control.get('driver_state_error') is None and control.get('cold_candidate_rejection') is None,
        'actual verified cold opening changed')
    wrong = str(root / 'p37-responses/0197-1-result.json'); correct = str(root / 'p37-responses/0198-1-result.json')
    cold = queue._saved61_cold
    require(cold.get('phase') == 'ready' and cold.get('semantic_response') == wrong
        and cold.get('opening') == frame and queue.cold_semantic_response_path == wrong
        and state.get('before_metrics_response') == state['cold_session_opening'].get('semantic_response') == wrong
        and bound.get('semantic_response') == wrong and gov.get('classifier') == queue.result_classifier_pin
        and gov.get('state') == queue.governance_result_state and gov.get('pending_focus') == queue.lifestyle_pending_focus
        and queue.capabilities_verified and queue.cold_readiness_verified and queue.checkpoint_bootstrap_verified,
        'only the observed metadata pointer defect is eligible')
    require(queue.current_attempt == {'request': cap['request'], 'row': cap,
        'response': str(root / 'p37-responses/0199-1-result.json')}, 'current actual completed CAP199 differs')
    audit_path = env['Q'] / 'COLD-SEMANTIC-SOURCE-CORRECTED-0201.json'
    require(not audit_path.exists(), 'source correction already attempted')
    audit = {'schema': 'xar.c4-cold-source-pointer-correction/v1', 'machine_id': 'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc': env['now']().isoformat(), 'status': 'cold_semantic_source_pointer_corrected',
        'original_incorrect_source': wrong, 'correct_actual_semantic_source': correct,
        'retained_originals': originals, 'actual_frame': frame, 'completed_cycles': 74,
        'new_RPC_calls': 0, 'new_action_calls': 0, 'ordinary_cycle_credit': 0, 'game_day_credit': 0,
        'SEM_CAP_replayed': False, 'initial_incorrect_bound_claimed_correct': False,
        'original198_post_read_relay_error': 'Foreign cached decision provider',
        'failed_local200_retained': True, 'original198_display_publication_claimed_success': False}
    changed = copy.deepcopy(state)
    changed['before_metrics_response'] = correct
    changed['cold_session_opening']['semantic_response'] = correct
    corrected_bound = {**bound, 'semantic_response': correct,
        'source_pointer_correction': str(audit_path), 'original_incorrect_metadata_retained': originals[4]}
    queue.consume_sequence(request)
    env['atomic'](audit_path, audit, limit=16384)
    queue.full_loop_state = changed
    cold['semantic_response'] = correct; queue.cold_semantic_response_path = correct
    queue.persist_loop_state()
    env['atomic'](env['Q'] / 'ROOT-SAVED61-COLD-BOUND.json', corrected_bound, replace=True, limit=16384)
    receipt = {**audit, 'next_sequence': queue.next_sequence}
    env['atomic'](env['OUTBOX'] / path.name, {'request': request,
        'result': {'is_error': False, 'structured_content': receipt}}, limit=16384)
    queue.current_attempt = None
    queue.halted = None
    env['atomic'](root / 'ROOT-CURRENT-HALT-P37.json', {'status': 'resolved_exact_cold_metadata_and_relay_halt',
        'correction': str(audit_path), 'original_halts_retained': True, 'new_RPC_calls': 0}, replace=True, limit=16384)
    return receipt
