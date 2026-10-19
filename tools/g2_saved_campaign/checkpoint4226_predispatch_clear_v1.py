"""Finite C10 SAVE4226 Queue bookkeeping, with zero SDK/Native calls."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
KIND = 'checkpoint4226_source_bound_before_native_save'
PACK = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c10-save4226-failure82')
ERROR = "Error executing tool ck3_save_checkpoint: cold checkpoint lineage requires the canonical App's internal native projection"
PINS = {
    'FROZEN.json': (13433, 'b4879f4e9c499efe48798013553eaf6a19a17cdd597cb5ec2b6896f7b1011c0f'),
    'ROOT-CUMULATIVE-LOOP-STATE.json': (5955, 'b4378a942f93e00f0ee621a3000488dd12bb36900f30135b642fc1400d283892'),
    'ROOT-GOVERNANCE-RESULT-STATE.json': (2353, '435b509829c3ffaa8caf9e4d2bd78540ee53de84a880d5920f317fe39de7c6bd'),
    'ROOT-CURRENT-HALT-P37.json': (740, '511c9d5baaf0e9c3f28c5f4bb4fbdfb9806802e563d8d20df9989b53ac8c43fa'),
}
SOURCE = {
    'xar_autoplayer/bridge/successor_ui_app_owner_v1.py': '61d34deec81004116e87470e111d0f33afee479e8a035ad3efa1d02ab7980f3f',
    'xar_autoplayer/successor_ui_checkpoint_lineage_v1.py': '44fa2870a33723559551960a09c3d07bb848da0337bb9f18b9c9bfed77cbaa51',
    'xar_autoplayer/successor_ui_pending_ledger_v1.py': 'c0efbfa6474aee2fde033953a7a0220aa5a74a4a9484b1daa4ed32d13fa8b0e4',
}


def require(ok, why):
    if not ok:
        raise ValueError('SAVE4226 predispatch clear denied: ' + why)


def exact(path, size, sha):
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(262145)
    require(len(raw) == size and len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == sha,
        'bounded original bytes changed: ' + str(path))
    return json.loads(raw)


async def recover(queue, session, request, path, env):
    require(request == {'sequence': 4227, 'command': 'clear_zero_rpc_preflight_rejection',
        'arguments': {'repair_kind': KIND}} and Path(path).resolve() == (env['INBOX'] / '4227-1-result.json').resolve(),
        'one exact new local control required')
    frozen = {name: exact(PACK / name, *pin) for name, pin in PINS.items()}
    require(frozen['FROZEN.json']['machine_id'] == MACHINE and queue.next_sequence == 4227
        and getattr(queue, 'held_control', None) is None, 'exact current C10 local boundary required')
    state = frozen['ROOT-CUMULATIVE-LOOP-STATE.json']; gov = frozen['ROOT-GOVERNANCE-RESULT-STATE.json']
    require(queue.full_loop_state == state and env['read'](env['Q'] / 'ROOT-CUMULATIVE-LOOP-STATE.json', 65536) == state
        and env['read'](env['Q'] / 'ROOT-GOVERNANCE-RESULT-STATE.json', 262144) == gov,
        'original live state/governance must equal the frozen boundary')
    require(state['completed_cycles'] == 2010 and state['before'] == {'snapshot_id': 'native:3261',
        'revision': 125, 'native_revision': 3261, 'date_raw': 53189040, 'actor_character_id': 40526,
        'episode_run_id': 'native-40526-1bec95182886'} and state.get('pending_cycle') is None
        and state.get('pending_checkpoint') == {'global_turn': 2010, 'save_sequence': 4226,
            'semantic_response': str(env['OUTBOX'] / '4225-1-result.json')}
        and all(state.get(k) is None for k in ('terminal', 'pending_natural_succession', 'pending_unsafe_route_halt')),
        'only the exact undispatched SAVE checkpoint intent may be removed')
    original_path = env['OUTBOX'] / '4226-1-result.json'
    row = exact(original_path, 614, '5e44d213a23fb0890be4974d79e2691a11a3bae75505d7643124cb92fa12b66e')
    req = row['request']; result = row['result']
    require(req['sequence'] == 4226 and req['tool'] == 'ck3_save_checkpoint'
        and req['arguments'] == {'expected_revision': 125} and result.get('is_error') is True
        and result.get('result_type') == 'complete' and result.get('structured_content') is None
        and len(result.get('content', [])) == 1 and result['content'][0].get('text') == ERROR,
        'only the completed source-proven pre-driver exception is qualified')
    attempt = queue.current_attempt; halted = queue.halted
    require(isinstance(attempt, dict) and isinstance(halted, dict)
        and all(x.get('request') == req and x.get('row') == row
            and Path(x.get('response', '')).resolve() == original_path.resolve() for x in (attempt, halted))
        and env['read'](env['N'] / 'ROOT-CURRENT-HALT-P37.json', 16384) == frozen['ROOT-CURRENT-HALT-P37.json'],
        'retained original halt/attempt must still be SAVE4226')
    require(queue.launch.get('pid') == 153556 and queue.launch.get('creation_filetime') == 134368602545256920,
        'original same Game tuple required')
    source_root = env['N'].parent.parent / 'sdk-v20261019-candidate' / 'src08'
    for relative, sha in SOURCE.items():
        require(hashlib.sha256((source_root / relative).read_bytes()).hexdigest() == sha,
            'audited before-driver source differs: ' + relative)
    require(getattr(queue, 'governance_result_state', None) == gov['state']
        and getattr(queue, 'lifestyle_pending_focus', None) == gov.get('pending_focus')
        and getattr(queue, 'result_classifier_pin', None) == gov['classifier'], 'retained governance differs')
    queue.guard(reserve=False)
    intent = env['Q'] / 'CHECKPOINT4226-PREDISPATCH-CLEAR-INTENT.json'
    require(not intent.exists(), 'this exact finite clear was already attempted')
    evidence = {'schema': 'xar.c10.checkpoint4226-predispatch-clear/v1', 'machine_id': MACHINE,
        'observed_at_utc': env['now']().isoformat(), 'original_response': str(original_path),
        'original_response_sha256': '5e44d213a23fb0890be4974d79e2691a11a3bae75505d7643124cb92fa12b66e',
        'frozen_packet': {'path': str(PACK / 'FROZEN.json'), 'bytes': PINS['FROZEN.json'][0],
            'sha256': PINS['FROZEN.json'][1]}, 'source_contract':
            'owner.driver_step271/279/280 -> ensure89 -> lineage281 raises before driver.execute_step289',
        'completed_cycles': 2010, 'date_raw': 53189040, 'new_ordinary_cycle_credit': 0,
        'Game_or_Native_or_SDK_RPC_calls': 0, 'original_SAVE_replayed': False,
        'new_SAVE_authorized_by_this_control': False, 'old_SAVE_cache_dirty_due_and_all_governance_preserved': True}
    env['atomic'](intent, evidence, limit=16384)
    queue.consume_sequence(request)
    changed = copy.deepcopy(state); changed['pending_checkpoint'] = None
    queue.full_loop_state = changed
    queue.persist_loop_state()
    require(env['read'](env['Q'] / 'ROOT-GOVERNANCE-RESULT-STATE.json', 262144) == gov,
        'governance must remain value-identical')
    queue.halted = queue.halt_cause = queue.current_attempt = queue.held_control = None
    outcome = {**evidence, 'status': 'source_bound_predispatch_checkpoint_cleared', 'next_sequence': queue.next_sequence}
    env['atomic'](env['Q'] / 'CHECKPOINT4226-PREDISPATCH-CLEARED.json', outcome, limit=16384)
    env['atomic'](env['N'] / 'ROOT-CURRENT-HALT-P37.json', outcome, replace=True, limit=16384)
    env['atomic'](env['OUTBOX'] / Path(path).name, {'request': request, **outcome}, limit=16384)
    return outcome
