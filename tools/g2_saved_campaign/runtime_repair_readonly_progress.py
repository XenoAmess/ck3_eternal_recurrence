"""Qualified readonly repair status and earliest real calendar progress.

No Game action or RPC is submitted here. Source diagnosis, applied repair and
actual settled progression are separate facts. Importing this module mutates
neither process state nor other package modules. It supports the same-Game
status contract; cross-Game cold lineage remains an explicit runtime adapter.
"""
from datetime import timedelta
from pathlib import Path

from . import runtime_repair_status as core
from . import runtime_repair_status_v4 as v4
from . import runtime_repair_status_v5 as v5
from . import runtime_repair_auto_applied as auto
from . import runtime_repair_current_fault_guard as guard
from .runtime_repair_prebaseline import PrebaselinePublisher

FRAME = v5.FRAME

MESSAGES = {'campaign_root_preflight_state_changed': '已刷新暂停状态的只读查询', 'construction_probe_paused_frame_rejected_before_read': '已恢复建设查询的暂停帧', 'first_heir_native_pre_read_guard_rejected': '已刷新继承人关系只读快照', 'faction_pending_planning_publication_wait_before_receipt': '已恢复派系行动所需的只读状态', 'faction_pending_newer_paused_frame_before_receipt': '已刷新派系行动的同日暂停快照'}

def _construction_or_heir_reason(row):
    wrapper = row.get('result')
    body = wrapper.get('structured_content', wrapper.get('structuredContent')) if isinstance(wrapper, dict) else None
    diagnostics = body.get('diagnostics') if isinstance(body, dict) else None
    value = diagnostics.get('construction_transport_v1') if isinstance(diagnostics, dict) else None
    if isinstance(value, dict):
        request_id = value.get('request_id')
        if wrapper.get('is_error', wrapper.get('isError')) is True and value.get('diagnostic_only') is True and (value.get('classification') == 'matched_native_rejected') and (value.get('step') == 'g2_player_construction_view_probe_v1') and (value.get('native_error') == 'private construction probe paused frame unavailable') and isinstance(request_id, str) and request_id.startswith('construction-read-') and (value.get('received_request_id') == request_id) and (value.get('received_type') == 'command_result') and (value.get('received_protocol_version') == 1) and (value.get('received_ok') is False) and (value.get('gate_request_id') is True) and (type(value.get('expected_native_revision')) is int) and (value['expected_native_revision'] > 0):
            key = 'structured_content' if isinstance(wrapper.get('structured_content'), dict) else 'structuredContent'
            return ('建设查询的暂停帧暂不可用', {'mapping': 'construction_query_paused_frame_unavailable', 'native_request_id': request_id, 'native_step': value['step'], 'native_error': value['native_error'], 'expected_native_revision': value['expected_native_revision'], 'classification': value['classification'], 'diagnostic_only': True, 'json_pointer': ['result', key, 'diagnostics', 'construction_transport_v1', 'native_error'], 'Native_business_result_or_failure_cause_beyond_text_inferred': False})
    legacy = v4.diagnostic_reason(row)
    if legacy is not None:
        return legacy
    if isinstance(wrapper, dict) and wrapper.get('is_error', wrapper.get('isError')) is True:
        for index, item in enumerate(wrapper.get('content') or []):
            text = item.get('text') if isinstance(item, dict) else None
            if isinstance(text, str) and text.startswith('Error executing tool ck3_auto_turn: current heir relationship query RED: current first-heir relationship frame changed;') and ('pre_read_guard=snapshot_not_equal;' in text) and ('differing_fields=played_character_prestige;' in text):
                return ('继承人关系查询的只读快照已变化', {'mapping': 'heir_relationship_snapshot_changed', 'json_pointer': ['result', 'content', index, 'text'], 'error_excerpt': text[:320], 'Native_business_result_or_failure_cause_beyond_text_inferred': False})
    return None


def diagnostic_reason(row):
    found = _construction_or_heir_reason(row)
    if found is not None:
        return found
    wrapper = row.get('result') or {}
    if (row.get('request', {}).get('tool') != 'ck3_auto_turn'
            or wrapper.get('is_error', wrapper.get('isError')) is not True):
        return None
    known = {
        'Error executing tool ck3_auto_turn: private faction pending same-date paused revision did not arrive':
            ('\u6d3e\u7cfb\u884c\u52a8\u6b63\u5728\u7b49\u5f85\u65b0\u5feb\u7167', 'faction_pending_paused_revision_not_published'),
        'Error executing tool ck3_auto_turn: private faction pending receipt has a newer same-date paused frame':
            ('\u6d3e\u7cfb\u884c\u52a8\u7684\u540c\u65e5\u6682\u505c\u5feb\u7167\u5df2\u66f4\u65b0', 'faction_pending_newer_same_date_paused_frame')}
    for index, item in enumerate(wrapper.get('content') or []):
        text = item.get('text') if isinstance(item, dict) else None
        if text in known:
            brief, mapping = known[text]
            return brief, {'mapping': mapping, 'json_pointer': ['result', 'content', index, 'text'],
                'original_error_text': text, 'prior_gift_result_or_business_success_inferred': False}
    return None


def qualify_readonly_recovery(state, halt, original, control, audit, semantic):
    body = core.decode(control)
    frame = core.semantic(semantic, state.get('active_binding', state.get('binding')) or {})
    request = control.get('request') or {}
    binding = state.get('active_binding', state.get('binding')) or {}
    baseline = state.get('observed_frame') or {}
    qualification = audit.get('qualification') or {}
    observed = audit.get('observed') or {}
    pending = audit.get('failed_pending_cycle') or {}
    count = audit.get('completed_cycles_before_after')
    sequence = request.get('sequence')
    original_request = state.get('original_request') or {}
    if state.get('phase') not in ('repairing', 'repair_applied_waiting_for_progress') or not isinstance(body, dict) or frame is None or any((row.get('original_request') != original_request for row in (halt, audit))) or (original.get('request') != original_request) or (original_request.get('tool') != 'ck3_auto_turn') or (original.get('result', {}).get('is_error') is not True) or (halt.get('replay_allowed') is not False) or (type(sequence) is not int) or (type(original_request.get('sequence')) is not int) or (sequence <= original_request['sequence']) or (type(halt.get('next_sequence')) is not int) or (sequence < halt['next_sequence']) or (request.get('command') != 'recover_partial_life_advance') or (request.get('arguments') != {'recovery_kind': 'ordinary_campaign_succession', 'recovery_mode': 'readonly_planning_precondition'}) or (control.get('result', {}).get('is_error') is not False) or (body.get('schema') != 'g2.queue.readonly-planning-precondition-recovery/v1') or (audit.get('schema') != body.get('schema')) or (body.get('status') != 'readonly_planning_precondition_recovered') or (body.get('actual_paused') is not True) or (body.get('new_auto_admitted') is not True) or (qualification.get('read_only_precondition') is not True) or (qualification.get('business_submission') is not False) or any((row.get('original_auto_replayed') is not False for row in (body, audit))) or any((row.get('succession_performed') is not False for row in (body, audit))) or any((row.get('gameplay_actions_submitted') != 0 for row in (body, audit))) or any((row.get('failed_pending_business_credit') != 0 for row in (body, audit))) or any((row.get('fresh_readonly_calls') != 1 for row in (body, audit))) or (audit.get('same_actor_paused_recovery_verified') is not True) or (audit.get('same_game') != {'pid': binding.get('game_pid'), 'creation_filetime': binding.get('game_creation_filetime')}) or (type(count) is not int) or (count < 0) or (body.get('completed_cycles') != count) or (pending.get('global_turn') != count + 1) or (pending.get('auto_sequence') != original_request['sequence']) or (semantic.get('request', {}).get('sequence') != sequence + 1) or any((any((row.get(key) != baseline.get(key) for key in ('date_raw', 'actor_character_id', 'episode_run_id'))) for row in (pending.get('before') or {}, observed, frame))) or (observed.get('actor_alive') is not True) or (observed.get('paused') is not True) or (observed.get('map_ready') is not True) or (body.get('observed_date_raw') != baseline.get('date_raw')) or (body.get('observed_actor_character_id') != baseline.get('actor_character_id')):
        raise ValueError('Actual readonly recovery does not qualify this exact unresolved incident')
    return {'repair_sequence': sequence, 'progress_search_start_turn': count + 1, 'actual_stop_frame': frame, 'recovery_claimed': False, 'business_credit': 0, 'original_auto_replayed': False}

def progress_proof(state, turn, auto_row, metrics, before_metrics, loop, pair, published, observed_pair):
    if state.get('phase') != 'repair_applied_waiting_for_progress':
        return None
    binding = state.get('active_binding', state.get('binding')) or {}
    body, met, premet = (core.decode(auto_row), core.decode(metrics), core.decode(before_metrics))
    if not all((isinstance(row, dict) for row in (body, met, premet))):
        return None
    before, after = (turn.get('before') or {}, turn.get('after') or {})
    source = body.get('planning_source_frame') or {}
    if source.get('schema') != 'xar.ck3.planning-source-frame/v1' or source.get('status') != 'complete' or source.get('bridge_pid') != binding.get('game_pid') or any((source.get(k) != before.get(k) for k in ('date_raw', 'actor_character_id', 'episode_run_id'))) or any((premet.get(k) != before.get(k) for k in FRAME)) or (premet.get('paused') is not True) or (premet.get('map_ready') is not True) or (premet.get('actor_alive') is not True) or (type(source.get('connection_generation')) is not int) or (source['connection_generation'] <= 0) or (premet.get('connection_generation') != source['connection_generation']) or (met.get('connection_generation') != source['connection_generation']) or any((any((type(row.get(k)) is not int for row in (before, source, after))) or not before[k] <= source[k] <= after[k] for k in ('revision', 'native_revision'))) or any((row.get('snapshot_id') != 'native:' + str(row.get('native_revision')) for row in (before, source, after))):
        return None
    if state.get('active_binding') and (state.get('repair_applied_namespace') != binding.get('sdk_prefix') or pair.get('processes') != state.get('active_sdk_pair') or source.get('connection_generation') != state.get('active_connection_generation')):
        return None
    qualified_turn = dict(turn)
    qualified_turn['before'] = {key: source[key] for key in FRAME}
    proof = v5.settled_progress_proof(state, qualified_turn, auto_row, metrics, loop, pair, published, observed_pair)
    if proof is None:
        return None
    if not isinstance(auto_row.get('ended_at_utc'), str) or not isinstance(metrics.get('ended_at_utc'), str) or core.stamp(auto_row['ended_at_utc']) > core.stamp(metrics['ended_at_utc']):
        return None
    proof['planning_frame_qualification'] = {'kind': 'same_date_actor_episode_monotonic_planning_read_refresh', 'immutable_queue_before': before, 'actual_planning_source_frame': source, 'actual_paired_after': after, 'original_TURN_modified': False, 'before_MET_exact_queue_frame': True, 'actual_after_MET_exact_after_frame': True}
    return proof

class ReadonlyProgressPublisher(PrebaselinePublisher):
    def diagnose(self, row):
        return diagnostic_reason(row)

    def remember_resolved_archive(self, state, archive):
        """Terminal dedup points to this old resolution, never newer CURRENT."""
        source = state.get('halt_receipt') or {}
        target = Path(source.get('path', ''))
        if not target.is_file() or core.pin(target) != source:
            return
        try:
            identity, _ = self.identity_for_halt(target, state.get('source_binding', state.get('binding')))
        except (ValueError, FileNotFoundError):
            return
        key = guard.fingerprint(identity)
        path = self.store/(key+'-CLOSED-FAULT.json')
        if not path.exists():
            core.atomic(path, {'schema': 'xar.runtime-repair-terminal-fault/v1',
                'fingerprint': key, 'identity': identity, 'incident_id': state['incident_id'],
                'terminal_phase': state['phase'], 'withdrawn': state.get('withdrawn', False),
                'terminal_state': core.pin(archive), 'business_credit': 0})
        self.terminal_faults()[key] = core.pin(path)

    def apply_readonly(self, control_path, expected_incident, original_sequence, message):
        state = self.state()
        if state is None or state.get('incident_id') != expected_incident or state.get('original_request', {}).get('sequence') != original_sequence:
            raise ValueError('CURRENT changed; do not apply a different incident repair')
        control_path = control_path.resolve(strict=True)
        if control_path.parent != self.outbox.resolve():
            raise ValueError('Actual recovery control must belong to this SDK outbox')
        control = core.read(control_path)
        body = core.decode(control) or {}
        audit_path = Path(body.get('audit', '')).resolve(strict=True)
        if audit_path.parent != self.queue.resolve():
            raise ValueError('Recovery audit escaped this SDK queue')
        audit = core.read(audit_path)
        halt_pin = state.get('halt_receipt') or {}
        halt_path = Path(halt_pin.get('path', '')).resolve(strict=True)
        if halt_path.parent != self.queue.resolve() or core.pin(halt_path) != halt_pin:
            raise ValueError('Original immutable HALT changed')
        halt = core.read(halt_path)
        original_path = Path(halt.get('original_response', '')).resolve(strict=True)
        semantic_path = Path(audit.get('fresh_semantic_response', '')).resolve(strict=True)
        handler_path = Path(audit.get('qualification', {}).get('handler_source', '')).resolve(strict=True)
        if original_path.parent != self.outbox.resolve() or semantic_path.parent != self.outbox.resolve() or handler_path.parent != self.session.resolve() or (audit.get('original_response') != str(original_path)) or (audit.get('original_response_sha256') != core.pin(original_path)['sha256']) or (audit.get('fresh_semantic_sha256') != core.pin(semantic_path)['sha256']) or (body.get('fresh_semantic_response') != str(semantic_path)) or (audit.get('qualification', {}).get('handler_sha256') != core.pin(handler_path)['sha256']):
            raise ValueError('Actual original/semantic/handler source pins do not agree')
        proof = qualify_readonly_recovery(state, halt, core.read(original_path), control, audit, core.read(semantic_path))
        if not message or len(message) > 160:
            raise ValueError('A short real repair explanation is required')
        proof.update(original_halt=halt_pin, original_AUTO=core.pin(original_path), recovery_marker=core.pin(audit_path), actual_control=core.pin(control_path), fresh_SEM=core.pin(semantic_path), handler_source=core.pin(handler_path))
        state.update(phase='repair_applied_waiting_for_progress', repair_message=message, repair_applied_sequence=proof['repair_sequence'], repair_applied_namespace=self.prefix, repair_applied_at_utc=core.read(semantic_path).get('ended_at_utc'), repair_evidence=core.pin(control_path), readonly_applied_proof=proof, observed_frame=proof['actual_stop_frame'], resume_baseline_confirmed=True, progress_search_start_turn=proof['progress_search_start_turn'])
        path = self.store / (state['incident_id'] + '-ROOT-READONLY-APPLIED-%04d.json' % proof['repair_sequence'])
        core.atomic(path, state)
        relay = self.emit(state)
        return {'status': 'SAME_INCIDENT_READONLY_REPAIR_APPLIED', 'audit': core.pin(path), 'relay': relay, 'recovery_claimed': False, 'business_credit': 0}

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        if state.get('phase') != 'repair_applied_waiting_for_progress':
            return False
        first = state.get('progress_search_start_turn')
        if type(first) is not int or first <= 0:
            raise ValueError('An actual recovery-bound first settled turn is required')
        loop_path = self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json'
        loop = core.read(loop_path)
        count = loop.get('completed_cycles')
        if type(count) is not int or count < first:
            return False
        self.observe_sdk_pair()
        observed = [{**h.identity(role), **h.observe()} for role, h in self._sdk_handles or []]
        pair_path = self.session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.prefix.upper() + '.json')
        published_path = self.session / ('ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-' + self.prefix.upper() + '.json')
        pair, published = (core.read(pair_path), core.read(published_path))
        same = getattr(self, '_refresh_progress_incident', None) == state['incident_id']
        cursor = getattr(self, '_refresh_progress_cursor', first) if same else first
        self._refresh_progress_incident = state['incident_id']
        for number in range(cursor, min(count + 1, cursor + 128)):
            path = self.queue / ('CUMULATIVE-TURN-%06d.json' % number)
            if not path.is_file():
                return False
            turn = core.read(path)
            if turn.get('stage') != 'auto_verified' or type(turn.get('date_delta_raw')) is not int:
                return False
            if turn['date_delta_raw'] <= 0:
                self._refresh_progress_cursor = number + 1
                continue
            self._refresh_progress_cursor = number
            paths = [Path(turn[key]).resolve(strict=True) for key in ('auto_response', 'after_metrics_response', 'before_metrics_response')]
            if any((p.parent != self.outbox.resolve() for p in paths)):
                return False
            proof = progress_proof(state, turn, auto.clock_receipt(paths[0]), core.read(paths[1]), core.read(paths[2]), loop, pair, published, observed)
            if proof is None:
                return False
            proof.update(settled_TURN=core.pin(path), AUTO=core.pin(paths[0]), MET=core.pin(paths[1]), before_MET=core.pin(paths[2]), queue_state=core.pin(loop_path), pair_pin=core.pin(pair_path), published_pair_pin=core.pin(published_path), first_progress_searched_from_settled_turn=first, earlier_settled_turns_verified_same_date=True, first_progress_search_complete=True)
            now = core.utc()
            state.update(phase='resolved', recovery_proof=proof, resolved_at_utc=now.isoformat(), actual_wait_ended_at_utc=proof['actual_progress_ended_at_utc'], expires_at_utc=(now + timedelta(seconds=30)).isoformat())
            current = self.state()
            same_current = bool(current and current.get('incident_id') == state['incident_id'])
            state['superseded_incident_archive_only'] = not same_current
            core.atomic(self.store / (state['incident_id'] + '-RESOLVED-PLANNING-REFRESH.json'), state)
            if same_current:
                self.emit(state)
            self.remember_resolved_archive(state, self.store / (state['incident_id'] + '-RESOLVED-PLANNING-REFRESH.json'))
            return True
        return False

    def observe_known_readonly_applied(self):
        if super().observe_known_readonly_applied():
            return True
        state = self.state()
        if not state or state.get('phase') != 'repairing':
            return False
        halt_pin = state.get('halt_receipt') or {}
        halt_path = Path(halt_pin.get('path', '')).resolve(strict=True)
        if halt_path.parent != self.queue.resolve() or core.pin(halt_path) != halt_pin:
            return False
        first = core.read(halt_path).get('next_sequence')
        if type(first) is not int or first <= 0:
            return False
        for number in range(first, first + 3):
            audit_path = self.queue / ('READONLY-PRECONDITION-RECOVERY-%04d.json' % number)
            response_path = self.outbox / ('%04d-1-result.json' % number)
            if not audit_path.is_file() or not response_path.is_file():
                continue
            audit = core.read(audit_path)
            classification = audit.get('qualification', {}).get('classification')
            if classification not in MESSAGES:
                continue
            if audit.get('original_request') != state.get('original_request'):
                continue
            self.apply_readonly(response_path, state['incident_id'], state['original_request']['sequence'], MESSAGES[classification])
            return True
        return False
