"""Automatically bridge exact successful read-only recovery to first progress.

Only retained original halt + exact control/audit + same-date fresh SEM can
mark a repair applied. That acknowledgement is never recovery. Search settled
TURNs forward from the audit boundary, so later normal gameplay is not edited
as waiting. All runtime execution remains Root-owned; no Game/MCP/OBS calls.
"""
from copy import deepcopy
from datetime import timedelta
import hashlib
import importlib.util
import json
from pathlib import Path

SOURCE = Path(__file__).with_name('runtime_repair_status_sdk_transfer_v2.py')
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != 'd3a6dbf4bff6c51258aa5ad8a7c53e5151652ecd50b63d063026e4242b0bfb11':
    raise ValueError('Frozen same-Game transfer v2 changed')
spec = importlib.util.spec_from_file_location('frozen_transfer_for_auto_applied', SOURCE)
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)
core = transfer.core


def applied_proof(state, halt, original, response, audit, semantic):
    if state.get('phase') not in ('repairing', 'repair_applied_waiting_for_progress'): return None
    request = response.get('request') or {}
    body, sem = core.decode(response), core.decode(semantic)
    binding = state.get('active_binding', state.get('binding')) or {}
    rejected = (((original.get('result') or {}).get('structured_content') or {}).get('diagnostics') or {}).get('native_command_rejection') or {}
    qualification, observed = audit.get('qualification') or {}, audit.get('observed') or {}
    baseline, frame = state.get('observed_frame') or {}, core.semantic(semantic, binding)
    sequence = request.get('sequence')
    previous = audit.get('completed_cycles_before_after')
    pending = audit.get('failed_pending_cycle') or {}
    if (not isinstance(body, dict) or not isinstance(sem, dict) or frame is None
            or audit.get('schema') != 'g2.queue.readonly-planning-precondition-recovery/v1'
            or original.get('request') != state.get('original_request')
            or halt.get('original_request') != state.get('original_request')
            or audit.get('original_request') != state.get('original_request')
            or halt.get('replay_allowed') is not False
            or qualification.get('read_only_precondition') is not True
            or qualification.get('business_submission') is not False
            or qualification.get('classification') != 'campaign_root_preflight_state_changed'
            or qualification.get('native_step') != 'query-campaign-root-context-v1'
            or rejected.get('native_step') != qualification.get('native_step')
            or rejected.get('native_request_id') != qualification.get('native_request_id')
            or rejected.get('native_error') != 'state_changed'
            or (original.get('result') or {}).get('is_error') is not True
            or type(sequence) is not int or sequence != halt.get('next_sequence')
            or sequence <= state['original_request'].get('sequence', sequence)
            or request.get('command') != 'recover_partial_life_advance'
            or request.get('arguments') != {'recovery_kind': 'ordinary_campaign_succession',
                                            'recovery_mode': 'readonly_planning_precondition'}
            or body.get('status') != 'readonly_planning_precondition_recovered'
            or body.get('actual_paused') is not True or body.get('new_auto_admitted') is not True
            or body.get('original_auto_replayed') is not False or audit.get('original_auto_replayed') is not False
            or body.get('gameplay_actions_submitted') != 0 or audit.get('gameplay_actions_submitted') != 0
            or body.get('fresh_readonly_calls') != 1 or audit.get('fresh_readonly_calls') != 1
            or body.get('failed_pending_business_credit') != 0 or audit.get('failed_pending_business_credit') != 0
            or body.get('succession_performed') is not False or audit.get('succession_performed') is not False
            or audit.get('same_actor_paused_recovery_verified') is not True
            or audit.get('same_game') != {'pid': binding.get('game_pid'), 'creation_filetime': binding.get('game_creation_filetime')}
            or type(previous) is not int or previous < 0 or body.get('completed_cycles') != previous
            or pending.get('global_turn') != previous + 1
            or pending.get('auto_sequence') != state['original_request'].get('sequence')
            or any(pending.get('before', {}).get(k) != baseline.get(k)
                   for k in ('date_raw', 'actor_character_id', 'episode_run_id'))
            or (state.get('phase') == 'repair_applied_waiting_for_progress'
                and state.get('repair_applied_sequence') != sequence)
            or semantic.get('request', {}).get('sequence') != sequence + 1
            or any(frame.get(k) != baseline.get(k) or observed.get(k) != baseline.get(k)
                   for k in ('date_raw', 'actor_character_id', 'episode_run_id'))
            or observed.get('actor_alive') is not True or observed.get('paused') is not True
            or observed.get('map_ready') is not True):
        return None
    return {'schema': 'xar.runtime-repair-known-readonly-auto-applied/v1',
        'repair_sequence': sequence, 'same_SDK_namespace': binding['sdk_prefix'],
        'actual_stop_frame': frame, 'first_candidate_settled_turn': previous + 1,
        'recovery_claimed': False, 'original_AUTO_replayed': False,
        'new_business_credit': 0, 'Game_MCP_OBS_Desktop_calls': 0}


def clock_receipt(path):
    """Dedicated positive-clock envelope bound; never changes core.read64KiB.
    Actual1911 is 2,781,241 bytes because its text and structured DTO repeat.
    The envelope is bounded at4MiB, the decoded body at2MiB. No Driver read.
    """
    path = Path(path)
    if path.stat().st_size > 4*1024**2:
        raise ValueError('Positive clock AUTO envelope exceeds4MiB dedicated bound')
    row = json.loads(path.read_bytes())
    body = core.decode(row)
    if not isinstance(body, dict) or len(json.dumps(body, ensure_ascii=False).encode('utf-8')) > 2*1024**2:
        raise ValueError('Positive clock decoded body exceeds2MiB dedicated bound')
    return row


class AutoAppliedPublisher(transfer.TransferPublisher):
    def observe_halt(self):
        super().observe_halt()
        self.observe_known_readonly_applied()

    def observe_known_readonly_applied(self):
        state = self.state()
        if (not state or state.get('phase') not in ('repairing', 'repair_applied_waiting_for_progress')
                or state.get('automatic_applied_proof')): return False
        halt_pin = state.get('halt_receipt') or {}
        halt_path = Path(halt_pin.get('path', '')).resolve()
        if halt_path.parent != self.queue.resolve() or core.pin(halt_path) != halt_pin: return False
        halt = core.read(halt_path)
        number = halt.get('next_sequence')
        if type(number) is not int: return False
        audit_path = self.queue / f'READONLY-PRECONDITION-RECOVERY-{number:04d}.json'
        response_path = self.outbox / f'{number:04d}-1-result.json'
        if not audit_path.is_file() or not response_path.is_file(): return False
        marker = (state['incident_id'], core.pin(audit_path), core.pin(response_path))
        if marker == getattr(self, '_readonly_applied_seen', None): return False
        audit, response = core.read(audit_path), core.read(response_path)
        handler = audit.get('qualification') or {}
        handler_path = Path(handler.get('handler_source', '')).resolve()
        if (handler_path.parent != self.session.resolve()
                or core.pin(handler_path)['sha256'] != handler.get('handler_sha256')):
            return False
        original_path = Path(halt.get('original_response', '')).resolve()
        semantic_path = Path(audit.get('fresh_semantic_response', '')).resolve()
        body = core.decode(response) or {}
        if (original_path.parent != self.outbox.resolve() or semantic_path.parent != self.outbox.resolve()
                or audit.get('original_response') != str(original_path)
                or audit.get('original_response_sha256') != core.pin(original_path)['sha256']
                or audit.get('fresh_semantic_sha256') != core.pin(semantic_path)['sha256']
                or body.get('audit') != str(audit_path)
                or body.get('fresh_semantic_response') != str(semantic_path)):
            return False
        proof = applied_proof(state, halt, core.read(original_path), response, audit, core.read(semantic_path))
        self._readonly_applied_seen = marker
        if proof is None: return False
        proof.update(original_halt=halt_pin, recovery_marker=core.pin(audit_path),
                     actual_control=core.pin(response_path), fresh_SEM=core.pin(semantic_path))
        state.update(phase='repair_applied_waiting_for_progress',
            repair_message='\u5df2\u5b8c\u6210\u53ea\u8bfb\u72b6\u6001\u6062\u590d',
            repair_applied_sequence=number, repair_applied_namespace=self.prefix,
            repair_applied_at_utc=core.read(semantic_path).get('ended_at_utc'),
            repair_evidence=core.pin(response_path), observed_frame=proof['actual_stop_frame'],
            resume_baseline_confirmed=True, automatic_applied_proof=proof,
            progress_search_start_turn=proof['first_candidate_settled_turn'])
        core.atomic(self.store/(state['incident_id']+f'-AUTO-APPLIED-{number:04d}.json'), state)
        self.emit(state)
        return True

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        first = state.get('progress_search_start_turn')
        if state.get('phase') != 'repair_applied_waiting_for_progress': return False
        loop_path = self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json'
        loop = core.read(loop_path)
        count = loop.get('completed_cycles')
        if type(first) is not int:
            first = (state.get('first_recovery_turn_hint') or {}).get('global_turn')
        known_search_boundary = type(first) is int
        if not known_search_boundary and type(count) is int:
            first = max(1, count-63)
        if type(count) is not int or count < first: return False
        same = getattr(self, '_ordered_progress_incident', None) == state['incident_id']
        cursor = getattr(self, '_ordered_progress_cursor', first) if same else first
        self._ordered_progress_incident = state['incident_id']
        self.observe_sdk_pair()
        observed = [{**h.identity(role), **h.observe()} for role, h in self._sdk_handles or []]
        pair_path = self.session/('ROOT-ACTUAL-SDK-PROCESSES-PINNED-'+self.prefix.upper()+'.json')
        published_path = self.session/('ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-'+self.prefix.upper()+'.json')
        pair, published = core.read(pair_path), core.read(published_path)
        # At most 128 named small TURN reads per poll, no directory scan or
        # last64 shortcut. Retain the earliest positive candidate until its
        # actual immutable pair qualifies; never skip it for later gameplay.
        for number in range(cursor, min(count + 1, cursor + 128)):
            path = self.queue/f'CUMULATIVE-TURN-{number:06d}.json'
            if not path.is_file(): return False
            turn = core.read(path)
            if type(turn.get('date_delta_raw')) is not int: return False
            if turn['date_delta_raw'] <= 0:
                self._ordered_progress_cursor = number + 1
                continue
            self._ordered_progress_cursor = number
            auto_path, met_path = Path(turn['auto_response']).resolve(), Path(turn['after_metrics_response']).resolve()
            if auto_path.parent != self.outbox.resolve() or met_path.parent != self.outbox.resolve(): return False
            proof = transfer.transferred_progress_proof(state, turn, clock_receipt(auto_path), core.read(met_path),
                                                        loop, pair, published, observed)
            if proof is None: return False
            proof.update(settled_TURN=core.pin(path), AUTO=core.pin(auto_path), MET=core.pin(met_path),
                queue_state=core.pin(loop_path), pair_pin=core.pin(pair_path),
                first_progress_searched_from_settled_turn=first,
                earlier_settled_turns_verified_same_date=known_search_boundary,
                first_progress_search_complete=known_search_boundary)
            state.update(phase='resolved', recovery_proof=proof, resolved_at_utc=core.utc().isoformat(),
                         expires_at_utc=(core.utc()+timedelta(seconds=30)).isoformat())
            core.atomic(self.store/(state['incident_id']+'-RESOLVED-SETTLED-PAIR.json'), state)
            self.emit(state)
            return True
        return False


if __name__ == '__main__':
    core.Publisher = AutoAppliedPublisher
    try: core.main()
    finally:
        for publisher in transfer.v5.v4.v3.v2.ACTIVE_PUBLISHERS: publisher.close()
