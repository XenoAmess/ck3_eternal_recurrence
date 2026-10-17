"""Same-Game incident continuity across a normally closed SDK generation.

Root executes transfer only after stopping the previous single status watcher.
Original cause/request/binding/stop time remain immutable. New SDK readiness is
an applied repair, never recovery; only its settled AUTO+MET date advance may
resolve. No Game/MCP/OBS/Desktop or process mutation API is used here.
"""
import argparse
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys

from . import runtime_repair_status_v5 as v5
core = v5.core

_base_progress = v5.settled_progress_proof


def transferred_progress_proof(state, turn, auto, metrics, loop, pair, published, observed):
    if state.get('active_binding'):
        source = (core.decode(auto) or {}).get('planning_source_frame') or {}
        if (state.get('repair_applied_namespace') != state['active_binding'].get('sdk_prefix')
                or pair.get('processes') != state.get('active_sdk_pair')
                or source.get('connection_generation') != state.get('active_connection_generation')):
            return None
    return _base_progress(state, turn, auto, metrics, loop, pair, published, observed)


# Call the bound proof explicitly; importing this module does not mutate v5.


def same_game(left, right):
    return all(left.get(k) == right.get(k) for k in
               ('session', 'game_pid', 'game_creation_filetime', 'game_creation_date'))


def exact_rows(rows):
    if (not isinstance(rows, list) or len(rows) != 2
            or {r.get('role') for r in rows} != {'sdk_queue', 'sdk_application'}):
        raise ValueError('Exactly two actual SDK roles required')
    for row in rows:
        if (type(row.get('pid')) is not int or row['pid'] <= 0
                or type(row.get('creation_filetime')) is not int or row['creation_filetime'] <= 0
                or not isinstance(row.get('executable'), str) or not row['executable']):
            raise ValueError('Exact PID, full birth and executable required')
    return rows


def qualify_transfer(state, active, old_pair, old_exit, new_pair, published, semantic, caps, freeze):
    old = state.get('active_binding', state.get('binding')) or {}
    if (state.get('schema') != core.SCHEMA or state.get('phase') not in
            ('repairing', 'repair_applied_waiting_for_progress')
            or old.get('sdk_prefix') == active.get('sdk_prefix') or not same_game(old, active)):
        raise ValueError('Only an unresolved incident on the exact same Game can transfer')
    old_rows = exact_rows(old_pair.get('processes'))
    exits = old_exit.get('processes') or []
    if old_exit.get('normal') is not True or len(exits) != 2:
        raise ValueError('Actual old normal dual kernel exit required')
    for row in old_rows:
        match = [r for r in exits if r.get('role') == row['role']]
        if (len(match) != 1 or any(match[0].get(k) != row[k] for k in
                                  ('pid', 'creation_filetime', 'executable'))
                or match[0].get('kernel_exit_observed') is not True or match[0].get('exit_code') != 0):
            raise ValueError('Old exact SDK exits do not match retained pair')
    rows = exact_rows(new_pair.get('processes'))
    if new_pair.get('status') != 'SDK_PAIR_HANDLES_RETAINED' or rows != published.get('processes'):
        raise ValueError('New actual retained/published SDK pair differs')
    if any((r['pid'], r['creation_filetime']) in {(x['pid'], x['creation_filetime']) for x in old_rows} for r in rows):
        raise ValueError('New pair cannot reuse old process generation')
    frame = core.semantic(semantic, active)
    sem_body, cap_body = core.decode(semantic), core.decode(caps)
    control = (cap_body or {}).get('native_session_control') or {}
    diag, cap_diag = (sem_body or {}).get('diagnostics') or {}, (cap_body or {}).get('diagnostics') or {}
    baseline = state.get('observed_frame') or {}
    if (frame is None or any(frame.get(k) != baseline.get(k) for k in
                            ('date_raw', 'actor_character_id', 'episode_run_id'))
            or diag.get('bridge_pid') != active['game_pid']
            or type(diag.get('connection_generation')) is not int or diag['connection_generation'] <= 0
            or cap_diag.get('bridge_pid') != active['game_pid']
            or cap_diag.get('connection_generation') != diag['connection_generation']
            or control.get('configured') is not True or control.get('driver_state_restored') is not True
            or control.get('driver_state_error') is not None
            or control.get('driver_state_restore_kind') != 'same_pid_hot'
            or control.get('episode_binding_state') != 'active_resumed'
            or caps.get('request', {}).get('tool') != 'ck3_get_capabilities'
            or type(caps.get('request', {}).get('sequence')) is not int
            or caps['request']['sequence'] <= semantic.get('request', {}).get('sequence', -1)
            or freeze.get('status') != 'FINAL_SOURCE_FROZEN'
            or freeze.get('sdk_generation') != active['sdk_prefix'].upper()
            or freeze.get('same_Game_hot_rotation') is not True):
        raise ValueError('Actual same-date, same-Game hot SEM/CAP and frozen SDK required')
    result = deepcopy(state)
    result.setdefault('source_binding', deepcopy(state['binding']))
    result.setdefault('source_observed_frame', deepcopy(state['observed_frame']))
    if 'repair_applied_sequence' in state:
        result.setdefault('source_repair_applied_sequence', state['repair_applied_sequence'])
    result.update(active_binding=deepcopy(active), active_sdk_pair=deepcopy(rows),
        active_connection_generation=diag['connection_generation'],
        active_bootstrap_frame=frame,
        repair_applied_sequence=caps['request']['sequence'],
        repair_applied_namespace=active['sdk_prefix'],
        repair_applied_at_utc=caps.get('ended_at_utc'),
        phase='repair_applied_waiting_for_progress', resume_baseline_confirmed=True,
        expires_at_utc=None, repair_status_transfer_version=1,
        resolving_requires='new active SDK immutable settled AUTO+paired MET actual calendar advance',
        new_business_credit=0, new_cycle_credit=0, new_Game_calls=0,
        old_request_sequence_comparison_across_SDK_generations=False)
    return result


class TransferPublisher(v5.SettledPairPublisher):
    def state(self):
        if not self.current.exists():
            return None
        state = core.read(self.current)
        active = state.get('active_binding', state.get('binding'))
        if state.get('schema') != core.SCHEMA or active != self.binding:
            raise ValueError('Repair incident active session/Game/SDK binding differs')
        if not same_game(state['binding'], active):
            raise ValueError('Incident source and active Game generation differ')
        if state.get('active_pair_pin'):
            actual_pair = self.session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.prefix.upper() + '.json')
            if core.pin(actual_pair) != state['active_pair_pin']:
                raise ValueError('Active SDK retained pair changed after incident transfer')
        return state

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        if state.get('active_binding') is None:
            return super().resolve_if_proved(state, semantic_path, batch_path)
        if (state.get('repair_applied_namespace') != self.prefix
                or state.get('phase') != 'repair_applied_waiting_for_progress'):
            return False
        # No legacy FULL/SEM fallback for transferred incidents. Only immutable
        # active TURN + paired actual AUTO/MET can close this waiting interval.
        loop_path = self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json'
        signature = v5.v4.v3.v2.signature(loop_path)
        marker = (state['incident_id'], signature, state['repair_applied_sequence'])
        if marker == getattr(self, '_transfer_progress_marker', None):
            return False
        self._transfer_progress_marker = marker
        loop = core.read(loop_path)
        count = loop.get('completed_cycles')
        if type(count) is not int:
            return False
        same = getattr(self, '_transfer_incident', None) == state['incident_id']
        first = getattr(self, '_transfer_high', count - 64) + 1 if same else max(1, count - 63)
        self._transfer_incident, self._transfer_high = state['incident_id'], count
        self.observe_sdk_pair()
        observed = [{**handle.identity(role), **handle.observe()} for role, handle in self._sdk_handles or []]
        pair_path = self.session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.prefix.upper() + '.json')
        published_path = self.session / ('ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-' + self.prefix.upper() + '.json')
        pair, published = core.read(pair_path), core.read(published_path)
        hint = state.get('first_recovery_turn_hint') or {}
        first_hint = hint.get('global_turn')
        numbers = list(range(first, count + 1))
        if type(first_hint) is int and 0 < first_hint <= count:
            numbers = [first_hint, *[n for n in numbers if n != first_hint]]
        for number in numbers:
            path = self.queue / f'CUMULATIVE-TURN-{number:06d}.json'
            if not path.is_file():
                continue
            turn = core.read(path)
            if not isinstance(turn.get('auto_response'), str) or not isinstance(turn.get('after_metrics_response'), str):
                continue
            auto_path, met_path = Path(turn['auto_response']).resolve(), Path(turn['after_metrics_response']).resolve()
            if auto_path.parent != self.outbox.resolve() or met_path.parent != self.outbox.resolve():
                continue
            proof = transferred_progress_proof(state, turn, core.read(auto_path), core.read(met_path),
                                               loop, pair, published, observed)
            if proof is None:
                continue
            proof.update(settled_TURN=core.pin(path), AUTO=core.pin(auto_path), MET=core.pin(met_path),
                         queue_state=core.pin(loop_path), pair_pin=core.pin(pair_path),
                         active_sdk_prefix=self.prefix)
            state.update(phase='resolved', recovery_proof=proof, resolved_at_utc=core.utc().isoformat(),
                         expires_at_utc=(core.utc()+timedelta(seconds=30)).isoformat())
            core.atomic(self.store/(state['incident_id']+'-RESOLVED-SETTLED-PAIR.json'), state)
            self.emit(state)
            return True
        return False

    def refine_current(self):
        state = self.state()
        if not state or not state.get('active_binding'):
            return super().refine_current()
        # Original source diagnostics continue to belong to its old outbox.
        original = state['source_binding']['sdk_prefix'] + '-responses'
        saved = self.outbox
        try:
            self.outbox = self.session / original
            return super().refine_current()
        finally:
            self.outbox = saved

    def emit(self, state):
        # Existing overlay compatibility projection is retained. Binding in the
        # audit stays original; the explicit active binding is carried in state.
        return super().emit(state)


def transfer(args):
    session = args.session.resolve(strict=True)
    store = session / 'runtime-repair-status'
    if not (store / 'STOP').is_file():
        raise ValueError('Stop the previous single watcher first; keep STOP until transfer finishes')
    publisher = TransferPublisher(session, args.to_sdk_prefix)
    try:
        with core.writer_lock(store):
            path = store / 'CURRENT.json'
            state = core.read(path)
            old = state.get('active_binding', state.get('binding')) or {}
            if old.get('sdk_prefix') != args.from_sdk_prefix:
                raise ValueError('Current incident does not belong to the explicit prior SDK')
            outbox = session / (args.to_sdk_prefix + '-responses')
            for evidence in (args.semantic, args.capabilities):
                if evidence.resolve(strict=True).parent != outbox.resolve():
                    raise ValueError('Bootstrap evidence must be in the new SDK outbox')
            pair_path = session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + args.to_sdk_prefix.upper() + '.json')
            published_path = session / ('ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-' + args.to_sdk_prefix.upper() + '.json')
            old_pair_path = session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + args.from_sdk_prefix.upper() + '.json')
            freeze_path = session / ('ROOT-FINAL-SDK-FREEZE-' + args.to_sdk_prefix.upper() + '.json')
            candidate = qualify_transfer(state, publisher.binding, core.read(old_pair_path), core.read(args.old_exit),
                core.read(pair_path), core.read(published_path), core.read(args.semantic),
                core.read(args.capabilities), core.read(freeze_path))
            if args.first_recovery_hint:
                hint_path = args.first_recovery_hint.resolve(strict=True)
                if hint_path.parent != session:
                    raise ValueError('First recovery hint must be actual bounded metadata in this session')
                hint = core.read(hint_path)
                number = hint.get('completed_cycles')
                if type(number) is not int or number <= 0:
                    raise ValueError('First recovery hint lacks an actual settled TURN number')
                candidate['first_recovery_turn_hint'] = {
                    'global_turn': number, 'source': core.pin(hint_path),
                    'classification': 'lookup_hint_only_not_recovery_proof',
                    'must_verify_actual_TURN_AUTO_MET_and_active_pair': True}
            candidate['repair_message'] = args.message
            candidate['repair_evidence'] = core.pin(args.capabilities)
            candidate['active_pair_pin'] = core.pin(pair_path)
            candidate['incident_transfer'] = {'schema': 'xar.runtime-repair-sdk-transfer/v1',
                'original_current': core.pin(path), 'old_actual_exit': core.pin(args.old_exit),
                'new_pair': core.pin(pair_path), 'new_published_pair': core.pin(published_path),
                'new_semantic': core.pin(args.semantic), 'new_capabilities': core.pin(args.capabilities),
                'new_source_freeze': core.pin(freeze_path), 'new_incident_created': False,
                'Game_recording_overlay_restarted': False, 'recovery_claimed': False,
                'at_utc': core.utc().isoformat()}
            audit = store / (state['incident_id'] + '-SDK-TRANSFER-' + args.to_sdk_prefix.upper() + '.json')
            core.atomic(audit, candidate)
            publisher.emit(candidate)
            print(json.dumps({'status': 'SAME_INCIDENT_ACTIVE_SDK_TRANSFERRED_WAITING_FOR_ACTUAL_PROGRESS',
                'incident_id': state['incident_id'], 'audit': core.pin(audit),
                'source_binding': state['binding'], 'active_binding': publisher.binding,
                'recovery_claimed': False}, ensure_ascii=False))
    finally:
        publisher.close()


def main():
    if 'transfer-sdk' in sys.argv[1:]:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--session', type=Path, required=True)
        parser.add_argument('--from-sdk-prefix', required=True)
        parser.add_argument('--to-sdk-prefix', required=True)
        parser.add_argument('--old-exit', type=Path, required=True)
        parser.add_argument('--semantic', type=Path, required=True)
        parser.add_argument('--capabilities', type=Path, required=True)
        parser.add_argument('--message', required=True)
        parser.add_argument('--first-recovery-hint', type=Path)
        parser.add_argument('command', choices=['transfer-sdk'])
        args = parser.parse_args()
        if not args.message or len(args.message) > 160:
            raise ValueError('Short actual repair description required')
        transfer(args)
        return
    core.Publisher = TransferPublisher
    try:
        core.main()
    finally:
        for publisher in v5.v4.v3.v2.ACTIVE_PUBLISHERS:
            publisher.close()


if __name__ == '__main__':
    main()
