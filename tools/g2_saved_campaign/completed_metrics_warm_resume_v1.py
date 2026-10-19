"""Finite same-Game resume of an already completed, unpublished MET response.

The original queue's full_loop, recording guard, camera gate, and ordinary
settlement algorithm remain inherited. Only bootstrap and one generated MET
are supplied here. A runtime owner must separately retain the old kernel exits,
same Game, actual recording, source closure, and repaired publication ACK.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

SCHEMA = 'xar.same-game-completed-metrics-resume/v1'
LIMIT = 262144


def checked(reference, limit=LIMIT):
    path = Path(reference['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if (len(raw) > limit or len(raw) != reference['bytes']
            or hashlib.sha256(raw).hexdigest() != reference['sha256']):
        raise ValueError('Exact completed-metrics resume input differs: ' + str(path))
    return json.loads(raw)


def same_generation(left, right):
    return (all(type(left.get(key)) is int and left[key] > 0
                and left[key] == right.get(key) for key in ('pid', 'creation_filetime'))
            and isinstance(left.get('executable'), str) and bool(left['executable'])
            and left['executable'] == right.get('executable'))


def bind_verified_absence_lifecycle_v1(manifest, proof, launch, binder, *, machine_id):
    """Reuse actual vanilla proof; never rewrite the frozen manifest."""
    if (proof.get('game_pid') != launch.get('pid')
            or proof.get('game_creation_filetime') != launch.get('creation_filetime')
            or proof.get('machine_id') != machine_id):
        raise ValueError('Actual mod-absence evidence belongs to another Game generation')
    return binder({**manifest, 'verified_mod_absence': proof},
                  lifecycle='ordinary_campaign_succession', ordinary_campaign_no_pact=True)


def validate_inputs(admission):
    if admission.get('schema') != SCHEMA or not admission.get('machine_id'):
        raise ValueError('Explicit finite metadata resume admission required')
    request = checked(admission['rotation_request'])
    if (request.get('schema') != 'root.same-Game-SDK-only-metadata-rotation-request/v1'
            or request.get('machine_id') != admission['machine_id']
            or request.get('pending_cycle_to_reconsume_once') != 48
            or request.get('next_sequence') != 111
            or request.get('AUTO_or_MET_replayed') is not False
            or request.get('Game_OBS_publisher_stop_calls') != 0):
        raise ValueError('Only the exact MET110 metadata interruption is supported')
    state_pin = admission['retained_state']
    if any(state_pin.get(key) != request['settled_state_before_close'].get(key)
           for key in ('bytes', 'sha256')):
        raise ValueError('Archived state bytes differ from original interruption')
    state, governance = checked(state_pin), checked(admission['governance'])
    pending = state.get('pending_cycle') or {}
    if (state.get('completed_cycles') != 47 or pending.get('global_turn') != 48
            or pending.get('stage') != 'auto_verified' or pending.get('auto_sequence') != 109
            or pending.get('auto_response') != request['original_completed_AUTO']['path']
            or pending.get('before') != state.get('before')
            or pending.get('before_metrics_response') != state.get('before_metrics_response')
            or state.get('pending_checkpoint') is not None or state.get('terminal') is not None
            or governance.get('completed_cycles') != 47
            or governance.get('pending_cycle') != pending
            or governance.get('new_business_credit') != 0):
        raise ValueError('Original 47-cycle / pending48 state or sidecar differs')
    halt = checked(request['halt'])
    met = checked(request['original_completed_MET'])
    auto = checked(request['original_completed_AUTO'])
    if (halt.get('error_type') != 'PermissionError'
            or 'CURRENT-INPUT.json' not in halt.get('message', '')
            or ('WinError 5' not in halt.get('message', '') and 'WinError 32' not in halt.get('message', ''))
            or halt.get('original_request') != met.get('request')
            or halt.get('original_response') != request['original_completed_MET']['path']
            or halt.get('replay_allowed') is not False or halt.get('next_sequence') != 111
            or met.get('client_error') is not None or auto.get('client_error') is not None
            or met.get('request', {}).get('sequence') != 110
            or met.get('request', {}).get('tool') != 'root_current_runtime_metrics'
            or met.get('request', {}).get('arguments') != {}
            or auto.get('request', {}).get('sequence') != 109
            or auto.get('request', {}).get('tool') != 'ck3_auto_turn'
            or auto.get('request', {}).get('arguments') != {}):
        raise ValueError('Only completed AUTO109 / MET110 and their exact publication halt may resume')
    for row in (met, auto):
        result = row.get('result') or {}
        if result.get('is_error') is not False or not isinstance(result.get('structured_content'), dict):
            raise ValueError('Original completed native result required')
    body = met['result']['structured_content']
    if (body.get('paused') is not True or body.get('map_ready') is not True
            or any(body.get(key) != state['before'].get(key)
                   for key in ('actor_character_id', 'episode_run_id', 'date_raw'))
            or type(body.get('native_revision')) is not int):
        raise ValueError('Original MET110 frame differs from retained pending48')
    closed, pair = checked(admission['old_closed']), checked(request['original_pair'])
    rows = closed.get('processes') or []
    expected = pair.get('processes') or []
    if (closed.get('status') != 'ACTUAL_BOTH_SDK_EXITS_OBSERVED'
            or closed.get('normal') is not False or closed.get('launcher_exit_code') != 1
            or closed.get('machine_id') != admission['machine_id']
            or closed.get('Game_stopped') is not False or closed.get('recording_stopped') is not False
            or len(rows) != 2 or len(expected) != 2):
        raise ValueError('Honest original Queue1 / App0 kernel closure required')
    for role, code in (('sdk_queue', 1), ('sdk_application', 0)):
        actual = [row for row in rows if row.get('role') == role]
        original = [row for row in expected if row.get('role') == role]
        if (len(actual) != 1 or len(original) != 1 or not same_generation(actual[0], original[0])
                or actual[0].get('kernel_exit_observed') is not True
                or actual[0].get('wait_result') != 0 or actual[0].get('exit_code') != code
                or actual[0].get('observation_error') is not None):
            raise ValueError('Original process generation or actual exit differs: ' + role)
    ack = checked(admission['completed_MET_publication_ACK'])
    if (ack.get('schema') != 'xar.ck3.decision-text-published/v1'
            or ack.get('status') != 'TEXT_PUBLISHED' or ack.get('OBS_draw_ack') is not False
            or ack.get('business_submission_or_outcome_inferred') is not False
            or ack.get('machine_id') != admission['machine_id']):
        raise ValueError('Actual repaired same-source text publication ACK required')
    observation = checked(ack['source_observation'])
    if (observation.get('source_ref') != request['original_completed_MET']['path']
            or observation.get('request') != met.get('request')):
        raise ValueError('Text ACK belongs to another observation')
    return request, state, governance, body, ack


def make_met_resume_queue_v1(base, env, *, admission_path):
    """Compose with the exact original queue; no copy of full_loop is made."""
    class CompletedMetricsWarmQueue(base):
        def preflight(self):
            from root_continuous_segment_auto import verify_segment
            from root_decision_text_api import load_api, started_reference
            from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
            admission = env['read'](Path(admission_path), 65536)
            request, state, governance, body, ack = validate_inputs(admission)
            if env['Q'].exists() and any(env['Q'].iterdir()):
                raise ValueError('Original queue evidence must be retained separately; new queue must be empty')
            if (env['N'] / 'ROOT-COMPLETED-MET-110-CONSUME-INTENT.json').exists():
                raise ValueError('Original MET110 consumption was already attempted; preserve unknown outcome')
            if (self.zero_day_preparation or self.launch.get('pid') != admission['Game_pid']
                    or self.launch.get('creation_filetime') != admission['Game_creation_filetime']
                    or any(type(admission.get(key)) is not int or admission[key] <= 0
                           for key in ('Game_pid', 'Game_creation_filetime'))):
                raise ValueError('Exact retained Game generation and actual recording required')
            source = admission['original_source']
            with Path(source['path']).open('rb') as stream:
                raw = stream.read(1024**2 + 1)
            if (len(raw) != source['bytes'] or len(raw) > 1024**2
                    or hashlib.sha256(raw).hexdigest() != source['sha256']
                    or source['sha256'] != '3773af1c2beb0d66d800371012826e42d973d16cac855c4786212d45b28b9f20'):
                raise ValueError('Exact original complete queue source required')
            self.job, self.record_started, self.first = verify_segment(
                env['N'], env['R'], self.launch, self.record_job,
                self.args.first_frame_admission, env['read'], env['aware'], env['now'])
            api = load_api(env['N'])
            if (started_reference(env['N'], api) != ack.get('publisher_started')
                    or api.process_identity(self.launch['pid'])['creation_filetime'] != self.launch['creation_filetime']):
                raise ValueError('Actual retained Game or publisher generation changed')
            original_map = checked(admission['original_map_admission'])
            if (original_map.get('status') != 'GREEN' or original_map.get('reviewer') != '/root'
                    or original_map.get('game_pid') != self.launch['pid']
                    or original_map.get('game_creation_filetime') != self.launch['creation_filetime']
                    or original_map.get('Game_map_visible') is not True
                    or original_map.get('decision_text_visible') is not True
                    or original_map.get('recording_session_id') != self.job['session_id']):
                raise ValueError('Original actual retained recording map admission required')
            self.initial_frame = copy.deepcopy(original_map['actual_initial_frame'])
            self.expected_lifecycle_binding = bind_verified_absence_lifecycle_v1(
                env['read'](self.args.environment_manifest),
                env['read'](env['N'] / 'ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL.json'),
                self.launch, bind_succession_lifecycle_from_environment_v1,
                machine_id=admission['machine_id'])
            self.frozen_head = env['read'](env['N'] / 'ROOT-FINAL-SDK-FREEZE-P37.json', 2*1024**2)['git_head']
            self.checkpoint_mode = True
            self.frontend_done = len(env['FRONTEND'])
            self.next_sequence = 111
            self._completed_met_resume = {'admission': admission, 'request': request, 'state': state,
                'governance': governance, 'body': body, 'ack': ack, 'phase': 'semantic_required'}
            self.guard(reserve=False)

        def check_before(self, tool, arguments):
            resume = self._completed_met_resume
            if resume['phase'] != 'ready':
                expected = env['SEMANTIC'] if resume['phase'] == 'semantic_required' else env['CAPABILITIES']
                if tool != expected or arguments != {}:
                    raise ValueError('Fresh same-Game SEM then CAP required before retained MET settlement')
                return
            return super().check_before(tool, arguments)

        def check_after(self, tool, arguments, body):
            resume = self._completed_met_resume
            if resume['phase'] == 'semantic_required' and tool == env['SEMANTIC']:
                actual = env['frame'](body, semantic=True, expected_lifecycle=self.expected_lifecycle_binding)
                original = resume['body']
                diagnostics = body.get('diagnostics') or {}
                if (any(actual.get(key) != original.get(key)
                        for key in ('actor_character_id', 'episode_run_id', 'date_raw'))
                        or type(actual.get('native_revision')) is not int
                        or actual['native_revision'] < original['native_revision']
                        or body.get('paused') is not True or body.get('map_ready') is not True
                        or diagnostics.get('bridge_pid') != self.launch['pid']
                        or (diagnostics.get('hello') or {}).get('pid') != self.launch['pid']
                        or body.get('campaign_goal') != resume['state'].get('campaign_goal_anchor')):
                    raise ValueError('Fresh same-Game semantic differs from completed MET110')
                self.semantic = body
                self._met_resume_warm_frame = actual
                resume['phase'] = 'capabilities_required'
                return
            if resume['phase'] == 'capabilities_required' and tool == env['CAPABILITIES']:
                control = body.get('native_session_control') or {}
                if (body.get('episode_run_id') != resume['body']['episode_run_id']
                        or control.get('driver_state_restored') is not True
                        or control.get('driver_state_restore_kind') != 'same_pid_hot'
                        or control.get('episode_binding_state') != 'active_resumed'
                        or control.get('driver_state_error') is not None
                        or control.get('cold_candidate_rejection') is not None):
                    raise ValueError('Actual same-PID hot Driver restore required')
                self.full_loop_state = copy.deepcopy(resume['state'])
                self.governance_result_state = copy.deepcopy(resume['governance']['state'])
                self.lifestyle_pending_focus = copy.deepcopy(resume['governance'].get('pending_focus'))
                self.initial_save = copy.deepcopy(self.full_loop_state['actual_saved_checkpoint'])
                self.result_classifier = env['load_cold_result_classifier']()
                self.result_classifier_pin = copy.deepcopy(resume['governance']['classifier'])
                self.capabilities_verified = self.cold_readiness_verified = self.checkpoint_bootstrap_verified = True
                resume['phase'] = 'ready'
                self.persist_loop_state()
                env['atomic'](env['Q'] / 'ROOT-COMPLETED-MET-WARM-BOUND.json', {
                    'schema': SCHEMA, 'machine_id': resume['admission']['machine_id'],
                    'historical_completed_cycles': 47, 'pending_cycle_retained': 48,
                    'fresh_frame': self._met_resume_warm_frame,
                    'original_MET': resume['request']['original_completed_MET'],
                    'new_business_credit': 0, 'AUTO_or_MET_replayed': False}, limit=16384)
                return
            return super().check_after(tool, arguments, body)

        async def generated(self, session, tool, arguments=None):
            resume = self._completed_met_resume
            if resume['phase'] == 'ready' and not resume.get('consumed'):
                if tool != env['METRICS'] or arguments not in (None, {}):
                    raise ValueError('Pending48 must consume its original completed MET110 first')
                if (self.full_loop_state != resume['state']
                        or self.full_loop_state['pending_cycle']['stage'] != 'auto_verified'):
                    raise ValueError('Pending48 changed before one-time completed MET consumption')
                self.guard()
                source = resume['request']['original_completed_MET']
                original = checked(source)['result']['structured_content']
                if original != resume['body']:
                    raise ValueError('Original completed MET110 body changed')
                # This marker remains outside a rotated queue directory. A later
                # archive cannot accidentally reset the one-time consumption.
                intent = env['N'] / 'ROOT-COMPLETED-MET-110-CONSUME-INTENT.json'
                env['atomic'](intent, {'schema': SCHEMA, 'source': source,
                    'global_turn': 48, 'MCP_calls': 0, 'sequence_reissued': False}, limit=16384)
                # The original MET's check_after was skipped by the publication
                # error. Run that same inherited postcheck before returning it.
                super().check_after(env['METRICS'], {}, original)
                resume['consumed'] = True
                return original, Path(source['path'])
            return await super().generated(session, tool, arguments)

    return CompletedMetricsWarmQueue
