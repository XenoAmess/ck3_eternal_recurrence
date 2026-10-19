"""Bounded actual-C7 AST/MRO regression; fake queue state, no Game or RPC."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,tempfile
from datetime import datetime,timezone
from pathlib import Path
from ordinary_metrics_afterhook_v1 import bind_clean_metrics_afterhook_v1
from source_only381_warm_queue_v1 import make_source_only_warm_queue_v1

QUEUE = 'fd579859a384ba94a059a38701719918ef763a15d7df21f86c5b347dc6ff0a30'
REINFORCEMENT = '3ae23f9188eef22b7dbc2124e6fc2db2506fb3eeb98d7c127f895845ed269fb1'
MET = '8ff7f47a5d01b488dd43795ed3abff244e96e3713c1690f15f949b9b2dc499f5'
AUTO = '896f6c4aa7658a7bfc9bf1f4c2380c445faf94cd8284ccb5081cde46ced4a484'


def checked(path, digest, limit):
    path = Path(path).resolve(strict=True)
    assert path.stat().st_size <= limit
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    return raw, {'path': str(path), 'bytes': len(raw), 'sha256': digest}


def namespace(queue_source, reinforcement, root, events):
    """Use each actual afterhook and the actual alias order, without constructors."""
    tree = ast.parse(queue_source)
    env = dict(Path=Path, json=json, copy=copy, hashlib=hashlib,
               N=root, Q=root/'queue', OUTBOX=root/'outbox',
               SEMANTIC='SEM', METRICS='root_current_runtime_metrics', AUTO='ck3_auto_turn',
               SAVE='SAVE', CAPABILITIES='CAP', INITIAL_CAMERA='CAMERA', FRONTEND=('F1','F2','F3'),
               now=lambda: datetime.now(timezone.utc),
               read=lambda *a, **k: {'episode_projection':'one_life', 'before_submit_observation':True})
    def atomic(path, value, **options):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not options.get('replace'):
            raise FileExistsError(path)
        path.write_text(json.dumps(value), encoding='utf-8')
        events.append('persist:' + path.name)
    env['atomic'] = atomic
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'frame','decoded'}]
    assert len(funcs) == 2
    exec(compile(ast.Module(body=funcs, type_ignores=[]), '<actual-frame-decoder>', 'exec'), env)
    real_frame = env['frame']
    def frame(*args, **kwargs):
        events.append('original-frame-validation')
        return real_frame(*args, **kwargs)
    env['frame'] = frame
    exec(compile(reinforcement, '<actual-reinforcement-factory>', 'exec'), env)
    names = ('FreshQueue','ColdReadyQueue','P37C7oldReadyQueue','P37SavedCampaignColdQueue',
             'SavedCampaignVisualQueue','SavedCampaignSemanticQueue','CleanRobertMainMenuQueue')
    for name in names:
        cls = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name))
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'check_after']
        if not cls.body:
            cls.body = [ast.Pass()]
        if name == 'SavedCampaignVisualQueue':
            env['FreshQueue'] = env['P37SavedCampaignColdQueue']
        module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
        exec(compile(module, '<actual-C7-afterhook-MRO>', 'exec'), env)
        if name == 'FreshQueue':
            env['ColdQueue'] = env['FreshQueue']
    Warm = make_source_only_warm_queue_v1(env['CleanRobertMainMenuQueue'], env, admission_path=Path('NOT-USED'))
    return env, Warm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--frozen-root', type=Path, required=True)
    parser.add_argument('--machine-id', required=True)
    args = parser.parse_args()
    qraw, qp = checked(args.runtime_root/'root_p37c7_sdk_queue.py', QUEUE, 400000)
    rraw, rp = checked(args.runtime_root/'root_p37_reinforcement_recovery.py', REINFORCEMENT, 16384)
    mraw, mp = checked(args.frozen_root/'p37-responses/4101-1-result.json', MET, 65536)
    araw, ap = checked(args.frozen_root/'p37-responses/4102-1-result.json', AUTO, 65536)
    original = qraw.decode('utf-8')
    fixed = bind_clean_metrics_afterhook_v1(original)
    compile(fixed, '<fixed-C7-source>', 'exec')
    insertion = '        if tool == METRICS:\n            return super().check_after(tool, arguments, body)\n'
    assert fixed.replace(insertion, '', 1) == original
    try:
        bind_clean_metrics_afterhook_v1(fixed)
    except ValueError:
        pass
    else:
        raise AssertionError('double source application accepted')
    cases = []
    for kind in ('baseline_stale_rejected','fresh_clear','wrong_date','wrong_actor','non_null_step',
                 'unknown_original','invalid_MET','non_MET_original_path'):
        with tempfile.TemporaryDirectory(prefix='ordinary-MET-source-regression-') as directory:
            events = []; root = Path(directory)
            env, Warm = namespace(original if kind == 'baseline_stale_rejected' else fixed,
                                  rraw.decode('utf-8'), root, events)
            met = env['decoded'](json.loads(mraw)); row = json.loads(araw)
            assert env['decoded'](row)['status'] == 'blocked'
            assert env['decoded'](row)['plan']['selected_step'] is None
            before = env['frame'](met)
            stale = dict(before, date_raw=before['date_raw']-24, native_revision=before['native_revision']-1)
            instance = Warm.__new__(Warm)
            instance.__dict__.update(_source_only381={'phase':'ready'}, next_sequence=4102,
                reinforcement_frame=stale.copy(), reinforcement_frame_response='explicit-software-stale-frame',
                initial_save={'status':'explicit-software-bootstrap'}, checkpoint_bootstrap_verified=True,
                halted={'request':copy.deepcopy(row['request']), 'row':row, 'response':ap['path']},
                full_loop_state={'before':before.copy(), 'pending_cycle':{'auto_sequence':4102},
                                 'pending_checkpoint':None, 'completed_cycles':7},
                current_attempt={'fixture':True}, held_control={'fixture':True})
            instance.persist_loop_state = lambda: events.append('persist-loop-state')
            def consume(request):
                assert request['sequence'] == instance.next_sequence
                instance.next_sequence += 1
                events.append('consume-local-control')
                return request['sequence']
            instance.consume_sequence = consume
            request = {'sequence':1000000, 'arguments':{}}
            if kind == 'wrong_date': met['date_raw'] += 24
            if kind == 'wrong_actor': met['actor_character_id'] += 1
            if kind == 'non_null_step': row['result']['structured_content']['plan']['selected_step'] = 'life-advance'
            if kind == 'unknown_original': row['client_error'] = 'explicit synthetic unknown outcome'
            if kind == 'invalid_MET': met['paused'] = False
            if kind == 'non_MET_original_path':
                instance.check_after('unknown-tool', {}, {})
                assert instance.reinforcement_frame == stale
                assert 'original-frame-validation' not in events[1:]
                cases.append(kind); continue
            try:
                instance.check_after(env['METRICS'], {}, met)
            except ValueError:
                assert kind == 'invalid_MET' and instance.reinforcement_frame == stale
                cases.append(kind); continue
            assert kind != 'invalid_MET'
            if kind == 'baseline_stale_rejected':
                assert instance.reinforcement_frame == stale
            else:
                assert instance.reinforcement_frame == env['frame'](met)
                assert instance.reinforcement_frame_response.endswith('4101-1-result.json')
            instance.next_sequence = request['sequence']
            try:
                asyncio.run(instance.clear_blocked_no_action(None, request, root/'outbox/1000000-1-result.json'))
            except ValueError:
                assert kind != 'fresh_clear'
                assert instance.full_loop_state['pending_cycle'] == {'auto_sequence':4102}
                assert instance.halted is not None and 'consume-local-control' not in events
            else:
                assert kind == 'fresh_clear'
                assert instance.full_loop_state['completed_cycles'] == 7
                assert instance.full_loop_state['pending_cycle'] is None and instance.halted is None
                assert instance.full_loop_state['before_metrics_response'].endswith('4101-1-result.json')
                receipt = json.loads((root/'queue/BLOCKED-NO-ACTION-RECOVERY-1000000.json').read_text())
                assert receipt['business_credit_added'] is False and receipt['original_action_replayed'] is False
                assert receipt['new_MCP_or_native_calls'] == 0
            cases.append(kind)
    print(json.dumps({'status':'PASS', 'machine_id':args.machine_id,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(), 'inputs':[qp,rp,mp,ap],
        'output_source_bytes':len(fixed.encode()), 'output_source_sha256':hashlib.sha256(fixed.encode()).hexdigest(),
        'cases':cases, 'actual_class_afterhooks_and_guard_used':True,
        'explicit_software_queue_state_and_7_cycles':True, 'constructors_preflight_qualified':False,
        'no_runtime_adoption_or_business_credit':True, 'Game_Native_RPC':0, 'runtime_writes':0}))


if __name__ == '__main__':
    main()
