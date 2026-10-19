"""C11 normal SAVE-bound cold queue; retain the original Queue algorithms."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
SCHEMA = 'xar.c11.normal-checkpoint-cold-queue/v1'
SIDECARS = ('faction-gift-pending-v1.json', 'active-scheme-sway-formal-private-v1.json',
    'ordinary-sway-schedule-v1.json')


def require(ok, why):
    if not ok:
        raise ValueError('C11 normal checkpoint cold denied: ' + why)


def checked(ref, limit=262144):
    path = Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == ref['bytes']
        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'exact source differs: ' + str(path))
    return json.loads(raw)


def clean(state):
    return all(state.get(k) is None for k in ('pending_cycle', 'pending_checkpoint', 'terminal',
        'pending_natural_succession', 'pending_unsafe_route_halt'))


def project_checkpoint_seed(state, save_row, *, save_response, semantic_response):
    """Explicitly account one real direct SAVE; never add an ordinary cycle."""
    result = save_row.get('result') or {}
    checkpoint = (result.get('structured_content') or {}).get('checkpoint')
    require(clean(state) and save_row.get('client_error') is None and result.get('is_error') is False
        and result.get('result_type') == 'complete' and save_row.get('request', {}).get('tool') == 'ck3_save_checkpoint'
        and isinstance(checkpoint, dict) and checkpoint.get('status') == 'saved', 'settled state and completed actual SAVE required')
    before = state['before']
    require(all(before[k] == checkpoint[other] for k, other in (
        ('date_raw', 'date_raw'), ('actor_character_id', 'episode_character_id'), ('episode_run_id', 'episode_run_id')))
        and type(checkpoint.get('history_index')) is int and checkpoint['history_index'] > 0
        and type(checkpoint.get('size')) is int and checkpoint['size'] > 0
        and len(checkpoint.get('sha256', '')) == 64, 'SAVE must belong to the real clean current player/date')
    changed = copy.deepcopy(state)
    accounted = (state.get('actual_saved_checkpoint') == checkpoint
        and state.get('checkpoint_dirty_since_save') is False
        and (state.get('checkpoint_calendar_v1') or {}).get('last_saved_date_raw') == checkpoint['date_raw'])
    if not accounted:
        changed['counts']['checkpoint_saved'] += 1
    from root_p37_checkpoint_cadence import checkpoint_saved
    require(hashlib.sha256(Path(checkpoint_saved.__code__.co_filename).read_bytes()).hexdigest()
        == 'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87', 'retained checkpoint cadence source differs')
    checkpoint_saved(changed, checkpoint)
    changed['actual_saved_checkpoint'] = copy.deepcopy(checkpoint)
    changed['actual_saved_checkpoint_source'] = {'global_turn': state['completed_cycles'],
        'semantic_response': str(semantic_response), 'save_response': str(save_response),
        'source_kind': 'typed_maintenance_save', 'ordinary_cycle_credit': 0}
    return changed


def cold_inputs(admission):
    require(admission.get('schema') == SCHEMA and admission.get('machine_id') == MACHINE,
        'explicit C11 machine/schema required')
    seed = checked(admission['seed'])
    original = checked(admission['original_state'])
    save = checked(admission['save_response'])
    saved_semantic = checked(admission['saved_semantic_response'])
    require(saved_semantic.get('request', {}).get('tool') == 'ck3_take_semantic_snapshot_private_v1'
        and saved_semantic.get('client_error') is None and saved_semantic['result'].get('is_error') is False
        and saved_semantic['result'].get('result_type') == 'complete', 'actual successful saved-map SEM source required')
    require(seed == project_checkpoint_seed(original, save, save_response=admission['save_response']['path'],
        semantic_response=admission['saved_semantic_response']['path']), 'cold seed is not the exact actual SAVE projection')
    gov = checked(admission['governance'])
    require(clean(seed) and gov.get('pending_cycle') is None and gov.get('completed_cycles') == seed['completed_cycles'],
        'normal settled governance required')
    pre = checked(admission['cold_prelaunch'])
    require(pre.get('machine_id') == MACHINE and pre.get('status') == 'EXACT_CLOSED_CHECKPOINT_COLD_INPUT_VALIDATED'
        and pre.get('validator_api') == 'xar_autoplayer.native_session.validate_cold_start_checkpoint_for_pipe'
        and pre.get('save_response') == admission['save_response']
        and pre.get('checkpoint') == seed['actual_saved_checkpoint'], 'canonical cold validator provenance required')
    close = checked(pre['final_driver_close'])
    require(close['driver_state'] == pre['driver_state'] and close['sidecars'] == pre['sidecars']
        and close['checkpoint'] == seed['actual_saved_checkpoint']
        and close['original_command_history_preserved'] is True
        and close['history_rows'] >= seed['actual_saved_checkpoint']['history_index'], 'post-close Driver provenance differs')
    require({Path(r['path']).name for r in pre['sidecars']} >= set(SIDECARS), 'gift/Sway sidecars must be retained')
    for ref in pre['sidecars']:
        checked(ref)
    validation = pre['validation']; checkpoint = seed['actual_saved_checkpoint']
    require(all(validation.get(k) == checkpoint.get(v) for k, v in (
        ('size', 'size'), ('sha256', 'sha256'), ('history_index', 'history_index'),
        ('saved_date_raw', 'date_raw'), ('succession_lifecycle', 'succession_lifecycle')))
        and Path(validation['path']).resolve() == Path(checkpoint['path']).resolve()
        and validation.get('load_save_name') == 'xar_checkpoint', 'actual SAVE validator anchor differs')
    return seed, gov, checkpoint, pre, close


def bind_opening(body, *, seed, launch, lifecycle, frame):
    """Same saved61 business guards, now the real current checkpoint owns identity."""
    actual = frame(body, semantic=True, expected_lifecycle=lifecycle)
    expected = seed['actual_saved_checkpoint']
    diagnostics = body.get('diagnostics') or {}; hello = diagnostics.get('hello') or {}
    require(actual['actor_character_id'] == expected['episode_character_id']
        and actual['episode_run_id'] == expected['episode_run_id'] and actual['date_raw'] == expected['date_raw']
        and actual['snapshot_id'] == 'native:' + str(actual['native_revision'])
        and type(actual['native_revision']) is int and actual['native_revision'] > 0
        and diagnostics.get('bridge_pid') == hello.get('pid') == launch['pid']
        and type(diagnostics.get('connection_generation')) is int and diagnostics['connection_generation'] > 0
        and diagnostics['connection_generation'] == hello.get('connection_generation')
        and diagnostics.get('pipe_name') == launch['pipe'] and hello.get('ck3_build_match') is True
        and hello.get('game_adapter_id') == 'ck3-1.20.0.4-msvc-x64' and hello.get('game_adapter_status') == 'ready'
        and body.get('campaign_goal') == seed.get('campaign_goal_anchor')
        and body.get('active_event') is None and body.get('pending_character_interaction') is None,
        'new cold actor/episode/date/Native/goal differs')
    return actual


def project_opening(seed, opening, source):
    changed = copy.deepcopy(seed)
    changed['before'] = copy.deepcopy(opening)
    changed['before_metrics_response'] = str(source)
    changed['before_source_kind'] = 'actual_cold_semantic_snapshot'
    changed['cold_session_opening'] = {'frame': copy.deepcopy(opening), 'semantic_response': str(source),
        'ordinary_cycle_credit': 0, 'game_day_credit': 0}
    return changed


def make_normal_checkpoint_cold_queue_v1(base, env, *, admission_path):
    class NormalCheckpointColdQueue(base):
        async def call(self, session, request, path):
            if self._normal_cold['phase'] == 'semantic' and request.get('tool') == env['SEMANTIC']:
                from startup_readiness_v1 import startup_readiness_call
                from root_p37c11_overlay_relay import relay_compact
                return await startup_readiness_call(self, session, request, path, env, relay_compact=relay_compact)
            return await super().call(session, request, path)

        def preflight(self):
            from root_continuous_segment_auto_c11 import verify_segment
            from root_decision_text_api_c11 import load_api, started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission = env['read'](Path(admission_path), 65536)
            seed, gov, checkpoint, pre, close = cold_inputs(admission)
            # Native29 includes the termination executor, but its .4 router has
            # no completion-execution executor. Absence keeps the existing
            # argparse store_true capability False; all other flags retain order.
            self.flags = [flag for flag in self.flags
                if flag != '--private-active-scheme-sway-completion-execution-query']
            require(not self.zero_day_preparation and (not env['Q'].exists() or not any(env['Q'].iterdir())),
                'new empty cold Queue and actual recording required')
            for key, name in (('queue_source', 'root_p37c11_sdk_queue.py'),
                    ('entry_source', 'root_p37c11_mcp_entry.py'), ('native_binding_source', 'root_native_build_binding_p37c11.py')):
                ref = admission[key]; path = Path(ref['path']).resolve(strict=True); raw = path.read_bytes()
                require(path == (env['N'] / name).resolve() and len(raw) == ref['bytes'] and len(raw) <= 1024**2
                    and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'actual C11 source differs: ' + name)
            require(Path(env['__file__']).resolve() == Path(admission['queue_source']['path']).resolve(), 'executing Queue differs')
            require(admission['new_Game'] == {k: self.launch[k] for k in ('pid', 'creation_filetime', 'creation_date')}
                and type(self.launch['pid']) is int and self.launch['pid'] > 0
                and type(self.launch['creation_filetime']) is int and self.launch['creation_filetime'] > 0
                and (self.launch['pid'], self.launch['creation_filetime']) != (close['old_Game']['pid'], close['old_Game']['creation_filetime'])
                and self.launch.get('old_save_loaded') is True and self.launch.get('load_save_name') == 'xar_checkpoint',
                'actual fresh Game loaded checkpoint required')
            old = checked(admission['old_sdk_closed']); pair = checked(admission['old_sdk_pair'])
            require(env['sdk_pair_closed'](old) and close['sdk_closed'] == admission['old_sdk_closed']
                and len(old.get('processes', [])) == len(pair.get('processes', [])) == 2
                and all(any(p['role'] == q['role'] and all(p[k] == q[k] for k in ('pid', 'creation_filetime', 'executable'))
                    for q in pair['processes']) for p in old['processes']), 'old actual SDK kernel generation differs')
            self.job, self.record_started, self.first = verify_segment(env['N'], env['R'], self.launch,
                self.record_job, self.args.first_frame_admission, env['read'], env['aware'], env['now'])
            api = load_api(env['N'])
            require(started_reference(env['N'], api) == admission['publisher_started']
                and api.process_identity(self.launch['pid'])['creation_filetime'] == self.launch['creation_filetime'],
                'fresh actual Game/publisher differs')
            absence = checked(admission['mod_absence'])
            require(absence.get('machine_id') == MACHINE and absence.get('game_pid') == self.launch['pid']
                and absence.get('game_creation_filetime') == self.launch['creation_filetime'], 'new Game mod absence differs')
            self.expected_lifecycle_binding = bind_succession_lifecycle_from_environment_v1(
                {**env['read'](self.args.environment_manifest), 'verified_mod_absence': absence},
                lifecycle='ordinary_campaign_succession', ordinary_campaign_no_pact=True)
            require(self.expected_lifecycle_binding == checkpoint['succession_lifecycle'], 'checkpoint lifecycle differs')
            freeze = checked(admission['sdk_freeze'], 2*1024**2)
            require(Path(admission['sdk_freeze']['path']).name == 'ROOT-FINAL-SDK-FREEZE-P37C11.json'
                and freeze['business_source_commit'] == admission['business_source_commit']
                and freeze['native_build_label'] == 'Native29 minimized camera and bounded native diagnostics'
                and Path(admission['current_map_admission']).resolve() == (env['N'] / 'ROOT-CAMPAIGN-MAP-ADMITTED-C11.json').resolve()
                and type(admission['next_sequence']) is int and admission['next_sequence'] > admission['save_sequence'],
                'C11 source/Native/current map/sequence required')
            self.frozen_head = freeze['git_head']; self.frontend_done = len(env['FRONTEND']); self.checkpoint_mode = True
            self.next_sequence = admission['next_sequence']; self.initial_frame = self.initial_save = None
            self._normal_cold = {'phase': 'semantic', 'admission': admission, 'seed': seed,
                'governance': gov, 'checkpoint': checkpoint, 'prelaunch': pre}
            self.guard(reserve=False)

        def check_before(self, tool, arguments):
            cold = self._normal_cold
            if cold['phase'] != 'ready':
                require(tool == (env['SEMANTIC'] if cold['phase'] == 'semantic' else env['CAPABILITIES'])
                    and arguments == {}, 'fresh cold SEM then CAP required')
                return
            return super().check_before(tool, arguments)

        def check_after(self, tool, arguments, body):
            cold = self._normal_cold
            if cold['phase'] == 'semantic' and tool == env['SEMANTIC']:
                attempt = self.current_attempt; request = attempt['request']; row = attempt['row']
                sequence = request.get('sequence')
                require(request == {'sequence': cold['admission']['next_sequence'], 'tool': env['SEMANTIC'], 'arguments': {}}
                    and row.get('request') == request and self.next_sequence == sequence and row.get('client_error') is None
                    and row['result'].get('is_error') is False and row['result'].get('result_type') == 'complete'
                    and env['decoded'](row) == body, 'actual completed first SEM call context required')
                actual = bind_opening(body, seed=cold['seed'], launch=self.launch,
                    lifecycle=self.expected_lifecycle_binding, frame=env['frame'])
                source = Path(attempt['response']).resolve(strict=True)
                require(source.is_relative_to(env['N'].resolve()) and env['read'](source, env['REPLY_RESERVE']) == row,
                    'actual persisted READINESS observer row required before canonical publication')
                from root_score_month_samples_c11 import observe_semantic
                observe_semantic(env['N'], body, self.launch, source)
                self.initial_frame = copy.deepcopy(actual); self.semantic = body
                self.cold_semantic_response_path = str(env['OUTBOX'] / f'{sequence:04d}-1-result.json')
                cold.update(opening=actual, semantic_response=self.cold_semantic_response_path, phase='capabilities')
                return
            if cold['phase'] == 'capabilities' and tool == env['CAPABILITIES']:
                control = body.get('native_session_control') or {}; checkpoint = cold['checkpoint']
                require(body.get('episode_run_id') == checkpoint['episode_run_id']
                    and body.get('episode_character_id') == checkpoint['episode_character_id']
                    and body.get('episode_identity_pending') is False and body.get('one_life_terminal') is False
                    and control.get('driver_state_restored') is True and control.get('driver_state_restore_kind') == 'cold_checkpoint'
                    and control.get('episode_binding_state') == 'active_resumed' and control.get('driver_state_error') is None
                    and control.get('cold_candidate_rejection') is None, 'actual canonical cold_checkpoint restore required')
                self.full_loop_state = project_opening(cold['seed'], cold['opening'], cold['semantic_response'])
                self.initial_save = copy.deepcopy(checkpoint)
                self.governance_result_state = copy.deepcopy(cold['governance']['state'])
                self.lifestyle_pending_focus = copy.deepcopy(cold['governance'].get('pending_focus'))
                reviewed = checked(cold['admission']['classifier_pin'], 16384)
                self.result_classifier = env['load_cold_result_classifier']()
                source = Path(self.result_classifier.__code__.co_filename).resolve(strict=True)
                require(source == Path(reviewed['source']).resolve(strict=True) and source.stat().st_size <= 262144
                    and hashlib.sha256(source.read_bytes()).hexdigest() == reviewed['sha256'], 'reviewed classifier differs')
                self.result_classifier_pin = {k: reviewed[k] for k in ('source', 'sha256')}
                self.capabilities_verified = self.cold_readiness_verified = self.checkpoint_bootstrap_verified = True
                cold['phase'] = 'ready'; self.persist_loop_state()
                env['atomic'](env['Q'] / 'ROOT-C11-NORMAL-COLD-BOUND.json', {
                    'schema': 'xar.c11.normal-checkpoint-cold-bound/v1', 'machine_id': MACHINE,
                    'observed_at_utc': env['now']().isoformat(), 'opening_frame': cold['opening'],
                    'semantic_response': cold['semantic_response'], 'before_source_kind': 'actual_cold_semantic_snapshot',
                    'completed_cycles': self.full_loop_state['completed_cycles'],
                    'T0_date_raw': self.full_loop_state['start_date_raw'], 'checkpoint': checkpoint,
                    'classifier': self.result_classifier_pin, 'new_ordinary_cycle_credit': 0, 'AUTO_or_MET_replayed': False}, limit=16384)
                return
            return super().check_after(tool, arguments, body)

    return NormalCheckpointColdQueue
