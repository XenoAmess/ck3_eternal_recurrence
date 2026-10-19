"""Finite normal cold bootstrap at the real saved61 boundary; inherit full_loop."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
SEED_SHA = '13ace44626932920b7558ac7c74e5f648e697d291aa1d84a6671d166be4efdbc'
SAVE_RESPONSE_SHA = 'b59bbd30235fd0273cd11b0fbab05ceaa5d635f8e9cdfcfb3d66995b64778b71'


def require(ok, message):
    if not ok:
        raise ValueError('saved61 cold bootstrap denied: ' + message)


def checked(ref, limit=1024**2):
    path = Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == ref['bytes']
        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'exact source differs: ' + str(path))
    return json.loads(raw)


def checked_source(ref, root, name):
    path = Path(ref['path']).resolve(strict=True)
    require(path == (root / name).resolve() and path.stat().st_size <= 1024**2,
        'C4 source current view differs: ' + name)
    raw = path.read_bytes()
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
        'C4 source pin differs: ' + name)


def saved_inputs(admission):
    require(admission.get('schema') == 'xar.saved61-normal-cold-queue/v1'
        and admission.get('machine_id') == MACHINE, 'explicit C4 machine/schema')
    require(admission['seed']['sha256'] == SEED_SHA
        and admission['save_response']['sha256'] == SAVE_RESPONSE_SHA, 'actual197/seed51 sources required')
    seed = checked(admission['seed'], 65536)
    save_row = checked(admission['save_response'], 65536)
    checkpoint = (save_row.get('result') or {}).get('structured_content', {}).get('checkpoint')
    require(save_row.get('request', {}).get('sequence') == 197
        and save_row['request'].get('tool') == 'ck3_save_checkpoint'
        and save_row.get('client_error') is None and save_row['result'].get('is_error') is False
        and checkpoint == seed.get('actual_saved_checkpoint')
        and checkpoint.get('sha256') == 'cb385a8fd4be62b6e553a4d0a5575d50886e8d894dc8ed83173d9ae851d4075d'
        and checkpoint.get('size') == 70300340 and checkpoint.get('history_index') == 122
        and checkpoint.get('date_raw') == 53145792 and checkpoint.get('episode_character_id') == 31254,
        'saved61 checkpoint/history/actor differs')
    require(seed.get('completed_cycles') == 74 and seed.get('start_date_raw') == 53144328
        and all(seed.get(k) is None for k in ('pending_cycle', 'pending_checkpoint', 'terminal',
            'pending_natural_succession', 'pending_unsafe_route_halt'))
        and seed['counts']['checkpoint_saved'] == 5 and seed.get('checkpoint_dirty_since_save') is False
        and seed['checkpoint_calendar_v1']['last_saved_date_raw'] == checkpoint['date_raw']
        and seed['actual_saved_checkpoint_source']['save_response'] == admission['save_response']['path'],
        'settled74/T0/calendar61 state differs')
    prelaunch = checked(admission['cold_prelaunch'], 65536)
    require(prelaunch.get('machine_id') == MACHINE
        and prelaunch.get('validator_api') == 'xar_autoplayer.native_session.validate_cold_start_checkpoint_for_pipe',
        'actual canonical prelaunch validator provenance required')
    close_pin = prelaunch['final_driver_close']
    require(close_pin['sha256'] == '80f948193aac3cd62380d8603f04543705a158c662e6f70ae65b7e957e0b9bad',
        'actual final C3 close pin required')
    final_close = checked(close_pin, 16384)
    require(final_close.get('checkpoint') == checkpoint
        and final_close.get('original_command_history_preserved') is True
        and final_close.get('history_rows') == 122
        and all(prelaunch['driver_state'].get(k) == final_close['driver_state'].get(k) for k in ('bytes', 'sha256')),
        'canonical validator prelaunch Driver differs from final197 close source')
    expected_sidecars = {'active-scheme-sway-formal-private-v1.json': '54829a6fc69bfec57fed58754ea35e382806c6f9dcac4b62ec33edafd7a8458f',
        'ordinary-sway-schedule-v1.json': '8b6073f661ea19894d06222f29aa4d47111a4f8291a51b64c50d11932b904d1c'}
    require(len(prelaunch['sidecars']) == 2 and all(expected_sidecars.get(Path(ref['path']).name) == ref['sha256']
        for ref in prelaunch['sidecars']), 'final194 sidecar source pins differ')
    for ref in prelaunch['sidecars']:
        checked(ref, 16384)
    validation = prelaunch['validation']
    require(all(validation.get(k) == checkpoint.get(source) for k, source in (
        ('size', 'size'), ('sha256', 'sha256'), ('history_index', 'history_index'),
        ('saved_date_raw', 'date_raw'), ('succession_lifecycle', 'succession_lifecycle'))),
        'canonical cold validator did not accept actual197 anchor')
    require(Path(validation.get('path', '')).resolve() == Path(checkpoint['path']).resolve()
        and validation.get('name') == checkpoint['name'] and validation.get('load_save_name') == 'xar_checkpoint',
        'canonical cold validator used another save path/name')
    governance = checked(admission['governance'], 16384)
    require(governance.get('completed_cycles') == 74 and governance.get('pending_cycle') is None
        and governance.get('new_business_credit') == 0, 'settled governance input required')
    return seed, governance, checkpoint


def bind_opening(body, *, seed, launch, lifecycle, frame):
    actual = frame(body, semantic=True, expected_lifecycle=lifecycle)
    expected = seed['actual_saved_checkpoint']
    diagnostics = body.get('diagnostics') or {}; hello = diagnostics.get('hello') or {}
    require(actual['actor_character_id'] == expected['episode_character_id']
        and actual['episode_run_id'] == expected['episode_run_id'] and actual['date_raw'] == expected['date_raw']
        and actual['snapshot_id'] == 'native:' + str(actual['native_revision'])
        and type(actual['native_revision']) is int and actual['native_revision'] > 0
        and diagnostics.get('bridge_pid') == hello.get('pid') == launch['pid']
        and type(diagnostics.get('connection_generation')) is int
        and diagnostics['connection_generation'] > 0
        and diagnostics['connection_generation'] == hello.get('connection_generation')
        and diagnostics.get('pipe_name') == launch['pipe']
        and hello.get('ck3_build_match') is True
        and hello.get('game_adapter_id') == 'ck3-1.20.0.4-msvc-x64'
        and hello.get('game_adapter_status') == 'ready'
        and body.get('campaign_goal') == seed.get('campaign_goal_anchor')
        and body.get('active_event') is None and body.get('pending_character_interaction') is None,
        'actual new cold session actor/episode/date/Native/goal differs')
    return actual


def project_opening(seed, opening, source):
    changed = copy.deepcopy(seed)
    changed['before'] = copy.deepcopy(opening)
    changed['before_metrics_response'] = str(source)
    changed['before_source_kind'] = 'actual_cold_semantic_snapshot'
    changed['cold_session_opening'] = {'frame': copy.deepcopy(opening), 'semantic_response': str(source),
        'ordinary_cycle_credit': 0, 'game_day_credit': 0}
    return changed


def make_saved61_cold_queue_v1(base, env, *, admission_path):
    class Saved61ColdQueue(base):
        async def call(self, session, request, path):
            if (self._saved61_cold['phase'] == 'semantic'
                    and request.get('tool') == env['SEMANTIC']
                    and not getattr(self, 'cold_readiness_verified', False)
                    and self.initial_camera is None and not self.checkpoint_bootstrap_verified):
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c4_overlay_relay import relay_compact
                return await startup_readiness_call(self, session, request, path, env,
                    relay_compact=relay_compact)
            return await super().call(session, request, path)

        def preflight(self):
            from root_continuous_segment_auto_c4 import verify_segment
            from root_decision_text_api_c4 import load_api, started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission = env['read'](Path(admission_path), 65536)
            seed, governance, checkpoint = saved_inputs(admission)
            for key, name in (('queue_source', 'root_p37c4_sdk_queue.py'),
                    ('entry_source', 'root_p37c4_mcp_entry.py'),
                    ('native_binding_source', 'root_native_build_binding_p37c4.py')):
                checked_source(admission[key], env['N'], name)
            require(Path(env['__file__']).resolve() == Path(admission['queue_source']['path']).resolve(),
                'actual executing Queue differs from C4 source pin')
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir())),
                'normal cold bootstrap requires new empty queue and actual recording')
            require(admission['new_game'] == {key: self.launch[key] for key in ('pid', 'creation_filetime', 'creation_date')}
                and type(self.launch['pid']) is int and self.launch['pid'] > 0
                and type(self.launch['creation_filetime']) is int and self.launch['creation_filetime'] > 0
                and (self.launch['pid'], self.launch['creation_filetime']) != (214568, 134368503807325674)
                and self.launch.get('old_save_loaded') is True
                and self.launch.get('load_save_name') == 'xar_checkpoint', 'actual new Game loaded checkpoint required')
            old_closed = checked(admission['old_sdk_closed'], 65536)
            old_pair = checked(admission['old_sdk_pair'], 65536)
            require(env['sdk_pair_closed'](old_closed), 'actual old SDK kernel closure required')
            actual_rows = old_closed.get('sdk_processes', old_closed.get('processes', []))
            expected_rows = old_pair.get('processes', [])
            require(len(expected_rows) == 2 and all(any(old.get('role') == row.get('role')
                and old.get('pid') == row.get('pid') and old.get('creation_filetime') == row.get('creation_filetime')
                for old in expected_rows) for row in actual_rows), 'old closed SDK generation differs')
            self.job, self.record_started, self.first = verify_segment(env['N'], env['R'], self.launch,
                self.record_job, self.args.first_frame_admission, env['read'], env['aware'], env['now'])
            api = load_api(env['N'])
            checked(admission['publisher_started'], 16384)
            require(api.process_identity(self.launch['pid'])['creation_filetime'] == self.launch['creation_filetime']
                and started_reference(env['N'], api) == admission['publisher_started'],
                'actual new Game/publisher generation differs')
            absence = checked(admission['mod_absence'], 65536)
            require(absence.get('game_pid') == self.launch['pid']
                and absence.get('game_creation_filetime') == self.launch['creation_filetime']
                and absence.get('machine_id') == MACHINE, 'new Game actual mod-absence proof required')
            self.expected_lifecycle_binding = bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest), 'verified_mod_absence': absence},
                lifecycle='ordinary_campaign_succession', ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding == checkpoint['succession_lifecycle'],
                'new actual environment lifecycle differs from saved checkpoint')
            freeze = checked(admission['sdk_freeze'], 2*1024**2)
            self.frozen_head = freeze['git_head']
            require(Path(admission['sdk_freeze']['path']).name == 'ROOT-FINAL-SDK-FREEZE-P37C4.json'
                and Path(admission['current_map_admission']).resolve() == (env['N'] / 'ROOT-CAMPAIGN-MAP-ADMITTED-C4.json').resolve()
                and type(admission['next_sequence']) is int and admission['next_sequence'] >= 198,
                'C4 current source/map/sequence views required')
            self.frontend_done = len(env['FRONTEND']); self.checkpoint_mode = True
            self.next_sequence = admission['next_sequence']
            self.initial_frame = self.initial_save = None
            self._saved61_cold = {'phase': 'semantic', 'admission': admission, 'seed': seed,
                'governance': governance, 'checkpoint': checkpoint}
            self.guard(reserve=False)

        def check_before(self, tool, arguments):
            cold = self._saved61_cold
            if cold['phase'] != 'ready':
                expected = env['SEMANTIC'] if cold['phase'] == 'semantic' else env['CAPABILITIES']
                require(tool == expected and arguments == {}, 'fresh normal cold SEM then CAP required')
                return
            return super().check_before(tool, arguments)

        def check_after(self, tool, arguments, body):
            cold = self._saved61_cold
            if cold['phase'] == 'semantic' and tool == env['SEMANTIC']:
                attempt = self.current_attempt
                require(isinstance(attempt, dict) and isinstance(attempt.get('request'), dict)
                    and isinstance(attempt.get('row'), dict), 'actual cold SEM call context required')
                request = attempt['request']; row = attempt['row']; sequence = request.get('sequence')
                require(type(sequence) is int and sequence > 0
                    and self.next_sequence in (sequence, sequence + 1)
                    and request.get('tool') == env['SEMANTIC'] and request.get('arguments') == {}
                    and row.get('request') == request and row.get('client_error') is None
                    and (row.get('result') or {}).get('is_error') is False
                    and (row.get('result') or {}).get('result_type') == 'complete'
                    and env['decoded'](row) == body, 'actual completed SEM request/body differs')
                semantic_response = str(env['OUTBOX'] / f'{sequence:04d}-1-result.json')
                actual = bind_opening(body, seed=cold['seed'], launch=self.launch,
                    lifecycle=self.expected_lifecycle_binding, frame=env['frame'])
                self.initial_frame = copy.deepcopy(actual)
                self.semantic = body
                self.cold_semantic_response_path = semantic_response
                # Readiness persists its exact attempt before check_after, and
                # publishes the canonical outer response after this postcheck.
                observer_source = Path(attempt['response']).resolve(strict=True)
                require(observer_source.is_relative_to(env['N'].resolve())
                    and env['read'](observer_source, env['REPLY_RESERVE']) == row,
                    'actual persisted SEM observer row differs from completed call')
                from root_score_month_samples_c4 import observe_semantic
                observe_semantic(env['N'], body, self.launch, observer_source)
                cold['opening'] = actual
                cold['semantic_response'] = semantic_response
                cold['phase'] = 'capabilities'
                return
            if cold['phase'] == 'capabilities' and tool == env['CAPABILITIES']:
                control = body.get('native_session_control') or {}
                require(body.get('episode_run_id') == cold['checkpoint']['episode_run_id']
                    and body.get('episode_character_id') == cold['checkpoint']['episode_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True
                    and control.get('driver_state_restore_kind') == 'cold_checkpoint'
                    and control.get('episode_binding_state') == 'active_resumed'
                    and control.get('driver_state_error') is None and control.get('cold_candidate_rejection') is None,
                    'canonical cold checkpoint restore not materially verified')
                self.full_loop_state = project_opening(cold['seed'], cold['opening'], cold['semantic_response'])
                self.initial_save = copy.deepcopy(cold['checkpoint'])
                self.governance_result_state = copy.deepcopy(cold['governance']['state'])
                self.lifestyle_pending_focus = copy.deepcopy(cold['governance'].get('pending_focus'))
                reviewed = checked(cold['admission']['classifier_pin'], 16384)
                self.result_classifier = env['load_cold_result_classifier']()
                source = Path(self.result_classifier.__code__.co_filename).resolve(strict=True)
                require(source == Path(reviewed['source']).resolve(strict=True)
                    and source.stat().st_size <= 262144
                    and hashlib.sha256(source.read_bytes()).hexdigest() == reviewed['sha256'],
                    'actual loaded classifier differs from new reviewed pin')
                self.result_classifier_pin = {key: reviewed[key] for key in ('source', 'sha256')}
                self.capabilities_verified = self.cold_readiness_verified = self.checkpoint_bootstrap_verified = True
                cold['phase'] = 'ready'
                self.persist_loop_state()
                env['atomic'](env['Q'] / 'ROOT-SAVED61-COLD-BOUND.json', {'schema': 'xar.saved61-normal-cold-bound/v1',
                    'machine_id': MACHINE, 'opening_frame': cold['opening'], 'semantic_response': cold['semantic_response'],
                    'before_source_kind': 'actual_cold_semantic_snapshot', 'T0_date_raw': self.full_loop_state['start_date_raw'],
                    'completed_cycles': 74, 'new_ordinary_cycle_credit': 0, 'MET_or_AUTO_replayed': False,
                    'checkpoint': self.initial_save, 'classifier': self.result_classifier_pin}, limit=16384)
                return
            return super().check_after(tool, arguments, body)

    return Saved61ColdQueue
