"""Bounded C11 source and actual Queue startup composition, with fake session."""
from __future__ import annotations
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace
sys.dont_write_bytecode = True
from prepare_native29_cold_controller_v1 import build_sources, pin
from normal_checkpoint_cold_queue_v1 import make_normal_checkpoint_cold_queue_v1, project_checkpoint_seed
from owner_response_json_once_v1 import prepare_success_response_row_v1
from prepare_c3_life_opening_classifier_v1 import load_functions

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P = T.parent.parent / 'p51-fresh1066-v20261019-prepare01/c10-save4226-failure82'


def qualify_prelaunch(root):
    """Real canonical file validator on invented isolated SAVE/Driver fixtures."""
    import native29_checkpoint_bootstrap_v1 as boot
    from xar_autoplayer import environment, native_session
    root.mkdir()
    profile = root/'state/profile'; profile.mkdir(parents=True)
    state_dir = root/'state'; (state_dir/native_session.NATIVE_SESSION_QUEUE_DIRNAME).mkdir()
    save_dir = profile/'save games'; save_dir.mkdir()
    save_path = save_dir/native_session.NATIVE_SESSION_CHECKPOINT_FILENAME
    save_path.write_bytes(b'explicit software SAVE fixture')
    checkpoint = {'status': 'saved', 'name': save_path.name, 'path': str(save_path.resolve()),
        'size': save_path.stat().st_size, 'sha256': hashlib.sha256(save_path.read_bytes()).hexdigest(),
        'date_raw': 53189040, 'history_index': 1, 'episode_character_id': 40526,
        'episode_run_id': 'native-40526-software-checkpoint', 'succession_lifecycle': {'lifecycle': 'ordinary_campaign_succession'}}
    pipe = r'\\.\pipe\explicit-canonical-software-original-pipe'
    payload = {'format_version': 2, 'pipe_name': pipe, 'last_checkpoint': checkpoint,
        'episode_character_id': 40526, 'episode_run_id': checkpoint['episode_run_id'],
        'succession_lifecycle': checkpoint['succession_lifecycle'],
        'command_history': [{'index': 1, 'command': 'save-checkpoint', 'ok': True, 'result': {'checkpoint': checkpoint}}]}
    driver = state_dir/native_session.NATIVE_SESSION_QUEUE_DIRNAME/native_session.NATIVE_DRIVER_STATE_FILENAME
    driver.write_text(json.dumps(payload), encoding='utf-8')
    def emit(name, value):
        path = root/name; path.write_text(json.dumps(value), encoding='utf-8'); return pin(path)
    sdk = emit('sdkclosed.json', {'normal': True, 'machine_id': boot.MACHINE, 'launcher_exit_code': 0,
        'processes': [{'exit_code': 0, 'kernel_exit_observed': True, 'observation_error': None}]*2})
    game = emit('gameexit.json', {'machine_id': boot.MACHINE, 'kernel_signaled': True, 'pid': 7001,
        'creation_filetime': 7002, 'exit_code': 0})
    recording = emit('recordingclosed.json', {'status': 'CLEANUP_OBSERVED', 'inputs_unbound': True,
        'decision_text_publisher': {'status': 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO'}})
    close = emit('driverclose.json', {'machine_id': boot.MACHINE, 'checkpoint': checkpoint,
        'original_command_history_preserved': True, 'history_rows': 1, 'sdk_closed': sdk,
        'Game_exit': game, 'old_Game': {'pid': 7001, 'creation_filetime': 7002},
        'recording_shutdown': recording, 'driver_state': pin(driver), 'sidecars': []})
    saved = emit('save-response.json', {'request': {'tool': 'ck3_save_checkpoint'}, 'result': {
        'result_type': 'complete', 'is_error': False, 'structured_content': {'checkpoint': checkpoint}}})
    (profile/'dlc_load.json').write_text('{"enabled_mods":[],"disabled_dlcs":[]}', encoding='utf-8')
    manifest = json.loads((T/'state/profile/xar-autoplayer-environment.json').read_bytes())
    manifest.update(state_dir=str(state_dir.resolve()), profile_dir=str(profile.resolve()))
    manifest['load_profile']['dlc_load_sha256'] = hashlib.sha256((profile/'dlc_load.json').read_bytes()).hexdigest()
    manifest['environment_sha256'] = environment._contract_digest(manifest)
    manifest_path = profile/'manifest.json'; manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    spec = SimpleNamespace(state_dir=state_dir, profile_dir=profile, manifest_path=manifest_path)
    calls = []
    def launch(*a, **kw):
        calls.append(kw); return 'software-launch-handle'
    runtime = SimpleNamespace(NativeBridgeLaunchConfig=lambda *a: a, launch=launch)
    old_root, old_api = boot.N, boot.api
    boot.N, boot.api = root, lambda: (environment, native_session, runtime)
    try:
        boot.prepare_prelaunch(spec, save_response=saved, final_driver_close=close, pipe_name=pipe, output_path=root/boot.PRELAUNCH)
        assert boot.launch_prepared(spec, 'explicit-software-native.dll', 'explicit-software-injector.exe') == 'software-launch-handle'
        assert len(calls) == 1 and calls[0]['native_bridge'][1] == pipe
        assert calls[0]['load_save_name'] == 'xar_checkpoint' and calls[0]['continue_last_save'] is False
        assert json.loads(driver.read_bytes()) == payload
        save_path.write_bytes(b'different fixture SAVE')
        try:
            boot.verify_cold_profile(spec)
        except Exception:
            pass
        else:
            raise AssertionError('canonical validator accepted wrong SAVE bytes')
        assert len(calls) == 1
    finally:
        boot.N, boot.api = old_root, old_api
    return {'real_canonical_validator_on_isolated_files': True, 'original_pipe_preserved': True,
        'SAVE_tamper_rejected_before_launch': True, 'real_Game_or_process_calls': 0,
        'API_loader_and_real_process_closure_fixture_only': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(T))
    spec = {'schema': 'xar.c11.native29-cold-source-spec/v1', 'machine_id': 'xenoamess-full-tower-eb9d2c1186',
        'generation': 'C11', 'base_generation': 'C10', 'templates': {k: pin(T/name) for k, name in {
            'supervisor': 'root_native26_c4_supervisor.py', 'record_shutdown': 'root_record_shutdown_c4.py',
            'score_observer': 'root_score_month_samples_c4.py', 'queue': 'root_p37c10_sdk_queue.py',
            'entry': 'root_p37c10_mcp_entry.py', 'native_binding': 'root_native_build_binding_p37c10.py',
            'sdk_owner': 'launch_sdk_p37c10_owner.py',
            'handoff': 'root_p37c10_automatic_natural_succession_handoff.py',
            'resident': 'p51_resident_successor_adoption_c10.py'}.items()}}
    files = build_sources(spec)
    timing_modules = []
    timing_prior = {}
    for name in ('root_c11_queue_control_timing', 'root_c11_control_timing_adapter'):
        module = ModuleType(name); timing_prior[name] = sys.modules.get(name); sys.modules[name] = module
        exec(compile(files[name+'.py'], name+'.py', 'exec'), module.__dict__)
        timing_modules.append(module)
    timing_adapter = timing_modules[-1]
    qt = ast.parse(files['root_p37c11_sdk_queue.py'])
    state = json.loads((P/'ROOT-CUMULATIVE-LOOP-STATE.json').read_bytes())
    state['pending_checkpoint'] = None  # Explicit software input after real source-bound4227; no live mutation.
    gov = json.loads((P/'ROOT-GOVERNANCE-RESULT-STATE.json').read_bytes())
    sem = json.loads((T/'p37-responses/4225-1-result.json').read_bytes())
    body = sem['result']['structured_content']; native_old = body['native_revision']
    checkpoint = copy.deepcopy(state['actual_saved_checkpoint'])
    checkpoint.update(date_raw=body['date_raw'], history_index=999)
    save = {'request': {'sequence': 5000, 'tool': 'ck3_save_checkpoint'},
        'result': {'result_type': 'complete', 'is_error': False, 'structured_content': {'checkpoint': checkpoint}}}
    seed = project_checkpoint_seed(state, save, save_response='software-new-save.json', semantic_response='software-old-sem.json')
    assert seed['completed_cycles'] == state['completed_cycles'] == 2010
    assert seed['counts']['checkpoint_saved'] == state['counts']['checkpoint_saved'] + 1
    assert seed['checkpoint_dirty_since_save'] is False and state['checkpoint_dirty_since_save'] is True
    assert state['actual_saved_checkpoint']['date_raw'] != checkpoint['date_raw']
    assert project_checkpoint_seed(seed, save, save_response='software-new-save.json', semantic_response='software-old-sem.json')['counts'] == seed['counts']
    # New Game/Native epoch is deliberately different, and revision1 <3261.
    sem = copy.deepcopy(sem); sem['request'] = {'sequence': 5001, 'tool': 'ck3_take_semantic_snapshot_private_v1', 'arguments': {}}
    body = sem['result']['structured_content']
    body.update(snapshot_id='native:1', native_revision=1, revision=2)
    body['diagnostics']['bridge_pid'] = body['diagnostics']['hello']['pid'] = 999991
    body['diagnostics']['connection_generation'] = body['diagnostics']['hello']['connection_generation'] = 1
    cap = json.loads((T/'p37-responses/4116-1-result.json').read_bytes())
    cap['request'] = {'sequence': 5002, 'tool': 'ck3_get_capabilities', 'arguments': {}}
    control = cap['result']['structured_content']['native_session_control']
    control.update(driver_state_restored=True, driver_state_restore_kind='cold_checkpoint', episode_binding_state='active_resumed')
    classifier = T/'root_p37c4_result_classifier.py'; classifierpin = pin(classifier)
    freeze = json.loads((T/'ROOT-FINAL-SDK-FREEZE-P37C10.json').read_bytes())
    sys.path.insert(0, freeze['source_root'])
    scope = {'Path': Path, 'copy': copy, 'json': json, 'ast': ast, 'hashlib': hashlib}
    load_functions(classifier.read_bytes(), scope, str(classifier))
    fixture = args.output/'fixture'; fixture.mkdir()
    qroot = fixture/'queue'; outbox = fixture/'outbox'; inbox = fixture/'inbox'
    for path in (qroot, outbox, inbox, fixture/'campaign-score/months'):
        path.mkdir(parents=True)
    (fixture/'campaign-score/months/month-000.json').write_bytes(b'{}')
    classifierpath = fixture/'classifier-pin.json'
    classifierpath.write_text(json.dumps({'source': classifierpin['path'], 'sha256': classifierpin['sha256']}), encoding='utf-8')
    events = []; calls = []; observed = []
    def read(path, *a):
        return json.loads(Path(path).read_bytes())
    def atomic(path, value, **kw):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not kw.get('replace'):
            raise FileExistsError(path)
        path.write_text(json.dumps(value), encoding='utf-8')
        events.append({'event': 'persist', 'file': path.name})
    selected = []
    for name in ('decoded', 'frame', 'consume_sequence', 'persist_loop_state', 'generated', 'full_loop', 'call'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name))
    fresh = next(n for n in qt.body if isinstance(n, ast.ClassDef) and n.name == 'FreshQueue')
    selected.append(next(n for n in fresh.body if isinstance(n, ast.FunctionDef) and n.name == 'check_after'))
    clean = next(n for n in qt.body if isinstance(n, ast.ClassDef) and n.name == 'CleanRobertMainMenuQueue')
    selected.append(next(n for n in clean.body if isinstance(n, ast.FunctionDef) and n.name == 'require_camera_pixel_admission'))
    env = {'N': fixture, 'R': fixture.parent, 'Q': qroot, 'OUTBOX': outbox, 'INBOX': inbox,
        'Path': Path, 'copy': copy, 'json': json, 'time': time, 'SEMANTIC': sem['request']['tool'],
        'CAPABILITIES': cap['request']['tool'], 'METRICS': 'root_current_runtime_metrics', 'AUTO': 'ck3_auto_turn',
        'SAVE': 'ck3_save_checkpoint', 'INITIAL_CAMERA': 'root_initialize_campaign_camera_v1',
        'REPLY_RESERVE': 512*1024**2+65536, 'FRONTEND': ('a', 'b', 'c'), 'now': lambda: datetime.now(timezone.utc),
        'read': read, 'atomic': atomic, 'atomic_payload_v1': lambda p, raw, **kw: atomic(p, json.loads(raw), **kw),
        '_owner_response_success_row_once_v1': prepare_success_response_row_v1,
        'preserve_first_exception': lambda *a, **kw: None, 'pending_request_paths': lambda *a, **kw: [],
        'display_projection': lambda row, value: {'request': row['request'], 'result': {'is_error': False, 'structured_content': {'status': 'fixture'}}},
        'load_cold_result_classifier': lambda: scope['classify_auto_result_credit_v1']}
    env.update({alias: getattr(timing_adapter, original) for alias, original in (
        ('_control_call_v1', 'control_call_v1'), ('_control_span_v1', 'control_span_v1'),
        ('_control_call_scope_v1', 'control_call_scope_v1'), ('_control_rpc_boundary_v1', 'control_rpc_boundary_v1'))})
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<actual-C11-queue-AST>', 'exec'), env)
    class Base(SimpleNamespace):
        call = env['call']; consume_sequence = env['consume_sequence']; persist_loop_state = env['persist_loop_state']
        generated = env['generated']; full_loop = env['full_loop']; check_after = env['check_after']
        require_camera_pixel_admission = env['require_camera_pixel_admission']
        def guard(self, **kw):
            pass
        def call_budget(self, *a):
            return 1
        def check_before(self, *a):
            pass
    old_ready = copy.deepcopy(next(n for n in qt.body if isinstance(n, ast.ClassDef) and n.name.startswith('P37') and n.name.endswith('oldReadyQueue')))
    old_ready.body = [n for n in old_ready.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'call']
    old_ready.bases = [ast.Name(id='Base', ctx=ast.Load())]; env['Base'] = Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old_ready], type_ignores=[])), '<actual-C11-oldReady-call>', 'exec'), env)
    Cold = make_normal_checkpoint_cold_queue_v1(env[old_ready.name], env, admission_path=Path('SOFTWARE_ONLY_NO_CONSTRUCTOR'))
    Cold = timing_adapter.bind_queue_control_timing_v1(Cold, env,
        admission_getter=lambda queue: queue._normal_cold['admission'].get('control_timing'))
    q = Cold.__new__(Cold)
    q.__dict__.update(launch={'pid': 999991, 'creation_filetime': 999992, 'pipe': body['diagnostics']['pipe_name']},
        next_sequence=5001, initial_frame=None, initial_save=None, initial_camera=None, semantic=None,
        zero_day_preparation=False, checkpoint_bootstrap_verified=False, cold_readiness_verified=False,
        expected_lifecycle_binding=checkpoint['succession_lifecycle'], halted=None, current_attempt=None,
        held_control=None, loop_count=0, job={'session_id': 'software-new-OBS'},
        _normal_cold={'phase': 'semantic', 'seed': seed, 'checkpoint': checkpoint, 'governance': gov,
            'admission': {'next_sequence': 5001, 'classifier_pin': pin(classifierpath)}})
    score = ModuleType('root_score_month_samples_c11'); score.END_RAW = 53407128; score.anchor_path = None
    def observe(_, value, game, path):
        row = read(path)
        assert path.name == 'READINESS-5001-000001-result.json' and not (outbox/'5001-1-result.json').exists()
        assert q.next_sequence == 5001 and row['request'] == sem['request'] and env['decoded'](row) == body
        observed.append({'source': str(path), 'sequence_at_postcheck': q.next_sequence, 'canonical_not_published': True})
    score.observe_semantic = observe
    relay = ModuleType('root_p37c11_overlay_relay')
    def publish(path, value):
        assert Path(path).exists() and q.next_sequence == read(path)['request']['sequence'] + 1
        events.append({'event': 'new_C11_relay', 'file': Path(path).name})
    relay.relay_compact = publish; relay.error_projection = lambda row: row
    mods = {m.__name__: m for m in (score, relay)}; prior = {k: sys.modules.get(k) for k in mods}; sys.modules.update(mods)
    class NewAutoReached(BaseException):
        pass
    class Session:
        async def call_tool(self, tool, arguments, **kw):
            if len(calls) >= 2:
                assert tool == env['AUTO']; calls.append({'tool': tool, 'new_sequence': 5004}); raise NewAutoReached()
            row = (sem, cap)[len(calls)]; assert tool == row['request']['tool'] and arguments == {}
            calls.append({'tool': tool, 'sequence': row['request']['sequence']})
            return SimpleNamespace(model_dump=lambda **kw: copy.deepcopy(row['result']))
    negatives = []
    try:
        for row in (sem, cap):
            asyncio.run(q.call(Session(), row['request'], inbox/f"{row['request']['sequence']:04d}-1-result.json"))
        assert q.full_loop_state['before']['native_revision'] == 1 < native_old
        assert q.full_loop_state['counts'] == seed['counts'] and q.initial_save == checkpoint and q.next_sequence == 5003
        assert q.full_loop_state['before_metrics_response'] == str(outbox/'5001-1-result.json')
        atomic(fixture/'ROOT-CAMPAIGN-MAP-ADMITTED-C11.json', {'status': 'GREEN', 'reviewer': '/root', 'game_pid': q.launch['pid'],
            'game_creation_filetime': q.launch['creation_filetime'], 'Game_map_visible': True, 'decision_text_visible': True,
            'recording_session_id': q.job['session_id'], 'actual_initial_frame': q.initial_frame})
        for label in ('wrong_actor', 'same_pid_hot_CAP'):
            instance = Cold.__new__(Cold); instance.__dict__.update(copy.deepcopy(q.__dict__))
            bad = copy.deepcopy(body); badcap = copy.deepcopy(cap['result']['structured_content'])
            if label == 'wrong_actor':
                instance.next_sequence = 5001; instance._normal_cold['phase'] = 'semantic'; bad['played_character']['character_id'] = 31254
                row = copy.deepcopy(sem); row['result']['structured_content'] = bad
                instance.current_attempt = {'request': sem['request'], 'row': row, 'response': str(qroot/'READINESS-5001-000001-result.json')}
            else:
                instance._normal_cold['phase'] = 'capabilities'; badcap['native_session_control']['driver_state_restore_kind'] = 'same_pid_hot'
            try:
                instance.check_after(env['SEMANTIC'] if label == 'wrong_actor' else env['CAPABILITIES'], {}, bad if label == 'wrong_actor' else badcap)
            except ValueError:
                negatives.append(label)
            else:
                raise AssertionError('invalid cold source accepted: ' + label)
        try:
            asyncio.run(q.full_loop(Session(), {'sequence': 5003, 'command': 'full_loop', 'arguments': {'max_turns': 1}}, inbox/'5003-1-result.json'))
        except NewAutoReached:
            pass
        else:
            raise AssertionError('ordinary original AUTO boundary not reached')
        assert q.full_loop_state['completed_cycles'] == 2010 and len(calls) == 3
    finally:
        for k, value in prior.items():
            if value is None: sys.modules.pop(k, None)
            else: sys.modules[k] = value
        for k, value in timing_prior.items():
            if value is None: sys.modules.pop(k, None)
            else: sys.modules[k] = value
    prelaunch = qualify_prelaunch(fixture/'prelaunch')
    receipt = {'schema': 'xar.c11.native29-cold-source-software-qualification/v1', 'machine_id': spec['machine_id'],
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE_AND_SOFTWARE_COMPOSITION_PASS',
        'templates': spec['templates'], 'outputs': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in files.items()},
        'actual_original_startup_call_postcheck_consume_publish_relay_CAP_full_loop': True,
        'new_epoch1_below_old_epoch_accepted': True, 'old_SAVE_cache_and_new_maintenance_SAVE_separately_accounted': True,
        'negative_cases': negatives, 'observed': observed, 'events': events, 'software_calls': calls,
        'prelaunch': prelaunch,
        'constructor_or_actual_new_SAVE_prelaunch_process_identity_qualified': False,
        'actual_future_C11_Game_Native29_qualification': False, 'actual_Game_SDK_Native_calls': 0, 'live_runtime_writes': 0}
    (args.output/'QUALIFICATION.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': receipt['status'], 'qualification': pin(args.output/'QUALIFICATION.json')}))


if __name__ == '__main__':
    main()
