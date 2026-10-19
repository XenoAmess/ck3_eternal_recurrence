"""Exact SAVE10456 metadata projection after C18 normal closure; no writer.

The unchanged original finish method runs on a copy. Every side effect is
captured in RAM; adopting returned metadata is a separate runtime operation.
"""
import ast
import copy
import hashlib
import json
from pathlib import PureWindowsPath
from types import SimpleNamespace

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
T = PureWindowsPath('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
Q = T/'p37-queue'
QUEUE_SHA = 'f4adb613364e56413b5244e13122f2530a897a5e42d76c1fa9897e2c7bfcd694'
CADENCE_SHA = 'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87'
NOTICE_SHA = '6d1d9bd4f938a0ba1cc12ac6c37fe2efdebebcacf44010175f17bb568e06e34a'
DATE, ACTOR, TURN = 53274576, 40526, 4748
EPISODE = 'native-40526-1bec95182886'
GAME, GAME_BIRTH = 30852, 134368995759027619
PAIR = {('sdk_queue',153792,134369092460097880), ('sdk_application',64328,134369092487102977)}
ALLOWED = frozenset(('actual_saved_checkpoint', 'actual_saved_checkpoint_source',
    'checkpoint_calendar_v1', 'checkpoint_dirty_since_save', 'checkpoint_due_after_readonly_chain',
    'pending_checkpoint', 'counts'))


def require(ok, reason):
    if not ok:
        raise ValueError('SAVE10456 offline reconciliation denied: '+reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_document_v1(raw, ref):
    require(type(raw) is bytes and isinstance(ref, dict)
        and type(ref.get('path')) is str and PureWindowsPath(ref['path']).is_absolute()
        and type(ref.get('bytes')) is int and len(raw) == ref['bytes'] <= 2*1024**2
        and sha(raw) == ref.get('sha256'), 'pinned closed document differs')
    value = json.loads(raw)
    require(isinstance(value, dict), 'closed document must be an object')
    return {'value':value, 'raw':raw, 'ref':{key:ref[key] for key in ('path','bytes','sha256')}}


def _uint(value):
    if type(value) is str and value.isdecimal() and len(value) <= 20:
        value = int(value)
    require(type(value) is int and 0 < value < 2**64, 'process birth/PID is not exact')
    return value


def _function(raw, name, scope):
    nodes = [node for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(nodes) == 1, 'one exact original function required: '+name)
    node = copy.deepcopy(nodes[0]); node.decorator_list = []
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), name, 'exec'), scope)
    return scope[name]


def _closed(owner, task):
    require(owner.get('machine_id') == task.get('machine_id') == MACHINE
        and owner.get('normal') is True and type(owner.get('launcher_exit_code')) is int
        and owner['launcher_exit_code'] == 0
        and owner.get('Game_stopped') is False and owner.get('recording_stopped') is False,
        'actual normal SDK-only closure required')
    rows = owner.get('processes')
    require(isinstance(rows, list) and len(rows) == 2
        and all(row.get('kernel_exit_observed') is True and type(row.get('exit_code')) is int
                and row['exit_code'] == 0 for row in rows), 'SDK kernel0/0 closure missing')
    require({(row.get('role'),_uint(row.get('pid')),_uint(row.get('creation_filetime'))) for row in rows} == PAIR,
        'closed C18 SDK pair differs')
    require(all(type(task.get(key)) is int and task[key] == 0 for key in
        ('child_exit_code','bootstrap_exit_code','job_active_after_stage'))
        and task.get('forced_remaining_cleanup') is False, 'durable SDK Task closure is not normal0/0/Job0')
    child = task.get('child') or {}
    require(_uint(child.get('pid')) == 53064 and _uint(child.get('creation_filetime')) == 134369092458681624,
        'durable C18 SDK owner generation differs')


def project_saved_checkpoint_v1(documents, *, queue_source, cadence_source, target_exists, source_fixture=False):
    """Return state/gov/CUMSAVE/audit only; unknown/duplicate inputs fail closed.

    documents values come from parse_document_v1. The sole caller must freshly
    stat the canonical CUM target after SDK closure, then recheck before adopting.
    """
    require(type(source_fixture) is bool and target_exists is False, 'existing/unknown CUM target; never overwrite or recount')
    require(type(queue_source) is bytes and len(queue_source) == 267957 and sha(queue_source) == QUEUE_SHA
        and type(cadence_source) is bytes and len(cadence_source) == 7065 and sha(cadence_source) == CADENCE_SHA,
        'original Queue/finish/cadence source changed')
    names = {'state','gov','semantic','save','owner_closed','task_closed','next','notice'}
    require(isinstance(documents, dict) and set(documents) == names, 'exact closed input set required')
    require(all(parse_document_v1(documents[name]['raw'], documents[name]['ref'])['value']
        == documents[name]['value'] for name in names), 'parsed input was changed after its pin check')
    refs = {name:documents[name]['ref'] for name in names}
    values = {name:copy.deepcopy(documents[name]['value']) for name in names}
    state, gov = values['state'], values['gov']
    _closed(values['owner_closed'], values['task_closed'])
    require(PureWindowsPath(refs['owner_closed']['path']).name == 'ROOT-P37C18-OWNER-CLOSED.json'
        and PureWindowsPath(refs['task_closed']['path']).name == 'CLOSED.json', 'closure source names differ')
    require(values['next'].get('next_sequence') == 10457, 'another request followed this maintenance SAVE')
    require(state.get('schema') == 'g2.queue.cumulative-loop/v1'
        and state.get('completed_cycles') == TURN and state.get('start_date_raw') == 53144328
        and all(state.get(key) is None for key in ('pending_cycle','pending_checkpoint','terminal',
            'pending_natural_succession','pending_unsafe_route_halt')),
        'exact clean4748 state required; failure/unknown history must remain separate')
    before = state.get('before') or {}
    require(before.get('date_raw') == DATE and before.get('actor_character_id') == ACTOR
        and before.get('episode_run_id') == EPISODE, 'current saved frontier differs')
    require(gov.get('completed_cycles') == TURN and gov.get('pending_cycle') is None
        and gov.get('new_business_credit') == 0, 'closed governance frontier differs')
    namespace = {'json':json}
    decoded = _function(queue_source, 'decoded', namespace)
    for name, seq, tool in (('semantic',10455,'ck3_take_semantic_snapshot_private_v1'),('save',10456,'ck3_save_checkpoint')):
        row = values[name]; request = row.get('request') or {}; result = row.get('result') or {}
        require(request.get('sequence') == seq and request.get('tool') == tool
            and row.get('client_error') is None and result.get('is_error') is False
            and result.get('result_type') == 'complete'
            and PureWindowsPath(refs[name]['path']) == T/'p37-responses'/f'{seq}-1-result.json',
            'actual successful maintenance SEM/SAVE identity differs')
    semantic, saved = decoded(values['semantic']), decoded(values['save'])
    diag = semantic.get('diagnostics') or {}; hello = diag.get('hello') or {}; actor = semantic.get('played_character') or {}
    require(semantic.get('paused') is True and semantic.get('map_ready') is True
        and semantic.get('one_life_terminal') is False and actor.get('alive') is True
        and actor.get('character_id') == ACTOR and semantic.get('episode_run_id') == EPISODE
        and type(semantic.get('date_raw')) is int and semantic['date_raw'] == DATE
        and type(semantic.get('native_revision')) is int and semantic['native_revision'] >= 4360
        and type(semantic.get('revision')) is int and semantic['revision'] >= 1693
        and semantic.get('snapshot_id') == f"native:{semantic['native_revision']}"
        and diag.get('bridge_pid') == hello.get('pid') == GAME
        and diag.get('connection_generation') == hello.get('connection_generation') == 3
        and diag.get('pipe_name') == r'\\.\pipe\xar-g2-robert30-v20261019-campaign01'
        and semantic.get('campaign_goal') == state.get('campaign_goal_anchor')
        and semantic.get('active_event') is None and semantic.get('pending_character_interaction') is None,
        'maintenance SEM is not the exact paused living same-Game frontier')
    require(values['semantic']['request'].get('arguments') == {}
        and values['save']['request'].get('arguments') == {'expected_revision':semantic['revision']},
        'maintenance request arguments differ')
    checkpoint = saved.get('checkpoint')
    require(isinstance(checkpoint, dict) and checkpoint.get('status') == 'saved'
        and checkpoint.get('date_raw') == DATE and checkpoint.get('episode_character_id') == ACTOR
        and checkpoint.get('episode_run_id') == EPISODE and checkpoint.get('history_index') == 5254
        and checkpoint.get('size') == 116194023
        and PureWindowsPath(checkpoint.get('path', '')) == T/'state/profile/save games/xar_checkpoint.ck3'
        and checkpoint.get('sha256') == '40483c63e79155a03bd3d495411d43a89ef11690b2b720e39113abe4579460fa'
        and checkpoint.get('succession_lifecycle') == semantic.get('succession_lifecycle')
        == (state.get('actual_saved_checkpoint') or {}).get('succession_lifecycle'), 'actual SAVE10456 anchor/lifecycle differs')
    notice = values['notice']
    require(refs['notice']['bytes'] == 3209 and refs['notice']['sha256'] == NOTICE_SHA
        and notice.get('machine_id') == MACHINE and notice.get('completed_cycles') == TURN
        and notice.get('checkpoint') == checkpoint and notice.get('driver_binding_verified') is True
        and notice.get('loop_bookkeeping_modified') is False
        and notice['sources']['SEM'] == refs['semantic'] and notice['sources']['SAVE'] == refs['save'],
        'actual closed SAVE notice/source pairing differs')
    games = [row for row in notice.get('owners', []) if row.get('role') == 'Game']
    require(len(games) == 1 and games[0].get('pid') == GAME
        and _uint(games[0].get('creation_filetime')) == GAME_BIRTH and games[0].get('wait0') == 258,
        'actual maintenance Game birth proof differs')
    counts = state.get('counts') or {}; count = counts.get('checkpoint_saved')
    require(type(count) is int and count == notice.get('loop_checkpoint_saved_count_observed') == 72
        and (state.get('actual_saved_checkpoint') or {}).get('date_raw') == notice.get('loop_checkpoint_raw_still_cached')
        and state.get('actual_saved_checkpoint') != checkpoint, 'SAVE already reconciled or cached source differs')
    work = copy.deepcopy(state)
    pending = {'global_turn':TURN, 'semantic_response':refs['semantic']['path'], 'save_sequence':10456,
        'source_kind':'explicit_maintenance_SAVE10456_bookkeeping_only'}
    work['pending_checkpoint'] = pending
    captured = []; persisted = []
    def atomic(path, value, **options):
        require(PureWindowsPath(path) == Q/f'CUMULATIVE-SAVE-{TURN:06d}.json'
            and options == {'limit':16384} and not captured, 'unexpected original finish side effect')
        captured.append(copy.deepcopy(value))
    scope = {'copy':copy, 'Q':Q, 'atomic':atomic, 'STATE_KEY':'checkpoint_calendar_v1'}
    _function(cadence_source, '_scope', scope)
    _function(cadence_source, 'checkpoint_saved', scope)
    finish = _function(queue_source, 'finish_cumulative_checkpoint', scope)
    holder = SimpleNamespace(full_loop_state=work,
        persist_loop_state=lambda: persisted.append(copy.deepcopy(work)))
    finish(holder, saved, refs['save']['path'])
    require(len(captured) == len(persisted) == 1 and persisted[0] == work, 'finish did not produce exactly one event/persist')
    missing = object()
    changed = {key for key in set(state)|set(work) if state.get(key, missing) != work.get(key, missing)}
    require(changed <= ALLOWED and work.get('pending_checkpoint') is None
        and work['counts'] == {**counts, 'checkpoint_saved':count+1}
        and work['actual_saved_checkpoint'] == checkpoint
        and work['actual_saved_checkpoint_source'] == {'global_turn':TURN,
            'semantic_response':refs['semantic']['path'], 'save_response':refs['save']['path']}
        and work['checkpoint_calendar_v1'] == {'last_saved_date_raw':DATE,
            'actor_character_id':ACTOR, 'episode_run_id':EPISODE,
            'war_ids':(state.get('checkpoint_calendar_v1') or {}).get('war_ids')}
        and work['checkpoint_dirty_since_save'] is False and work['checkpoint_due_after_readonly_chain'] is False,
        'original finish exceeded the checkpoint-only diff whitelist')
    require(state == documents['state']['value'] and gov == documents['gov']['value'], 'original inputs mutated')
    audit = {'schema':'xar.C18-SAVE10456-offline-reconciliation/v1', 'machine_id':MACHINE,
        'source_fixture':source_fixture, 'status':'RAM_PROJECTION_NOT_ADOPTED', 'sources':refs,
        'original_queue_sha256':QUEUE_SHA, 'original_cadence_sha256':CADENCE_SHA,
        'original_finish_calls':1, 'atomic_events_captured':1, 'persist_calls_captured':1,
        'changed_state_fields':sorted(changed), 'checkpoint_count_before':count, 'checkpoint_count_after':count+1,
        'maintenance_pending_derived_from_completed_SAVE_not_original_snapshot':pending,
        'Game':{'pid':GAME,'creation_filetime':GAME_BIRTH}, 'completed_cycles_before_after':TURN,
        'date_raw_before_after':DATE, 'business_or_cycle_credit':0, 'new_RPC_or_SAVE':0,
        'original_state_and_governance_unchanged':True,
        'requires_target_absence_recheck_and_separate_atomic_adoption':True}
    return {'state':work, 'governance':gov, 'cumulative_save':captured[0], 'audit':audit,
        'cumulative_save_path':str(Q/f'CUMULATIVE-SAVE-{TURN:06d}.json')}
