"""Root-owned repair-status sidecar, using only local immutable receipts.

No Game/SDK/OBS/Desktop API, process restart, Driver, SAVE or video access.
The existing overlay receives explicitly identified Root status metadata. It
does not receive a fabricated MCP action or any business/cycle credit.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

SCHEMA = 'xar.runtime-repair-status/v1'
TOOL = 'root_runtime_repair_status_v1'
SEMANTIC_TOOL = 'ck3_take_semantic_snapshot_private_v1'


def utc():
    return datetime.now(timezone.utc)


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def read(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('Only bounded metadata is accepted: ' + str(path))
    return json.loads(path.read_bytes())


def pin(path):
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def atomic(path, row, replace=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(row, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(payload) > 32768:
        raise ValueError('Repair-status metadata exceeds 32KiB')
    pending = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    try:
        with pending.open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(pending, path)
        else:
            pending.rename(path)
    finally:
        pending.unlink(missing_ok=True)


@contextmanager
def writer_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'status.lock').open('a+b') as stream:
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def decode(row):
    envelope = row.get('result')
    if not isinstance(envelope, dict) or envelope.get('is_error', envelope.get('isError')):
        return None
    body = envelope.get('structured_content', envelope.get('structuredContent'))
    return body if isinstance(body, dict) else None


def semantic(row, binding):
    body = decode(row)
    if row.get('request', {}).get('tool') != SEMANTIC_TOOL or body is None:
        return None
    played, diagnostics = body.get('played_character', {}), body.get('diagnostics', {})
    if (diagnostics.get('bridge_pid') != binding['game_pid']
            or played.get('alive') is not True or body.get('map_ready') is not True
            or body.get('paused') is not True or type(body.get('date_raw')) is not int
            or type(played.get('character_id')) is not int
            or not isinstance(body.get('episode_run_id'), str)):
        return None
    return {'game_pid': binding['game_pid'], 'actor_character_id': played['character_id'],
            'episode_run_id': body['episode_run_id'], 'date_raw': body['date_raw'],
            'revision': body.get('revision'), 'native_revision': body.get('native_revision')}


def recovery_proof(state, semantic_row, batch_row):
    """A patch ACK, reconsume, same-day query or failed FULL cannot resolve."""
    if state.get('phase') != 'repair_applied_waiting_for_progress':
        return None
    frame = semantic(semantic_row, state['binding'])
    result = decode(batch_row)
    request = batch_row.get('request', {})
    baseline = state.get('observed_frame', {})
    applied_sequence = state.get('repair_applied_sequence')
    if type(applied_sequence) is int:
        # Local queue controls/FULL replies deliberately have no wall-clock
        # envelope. Their actual same-queue request sequence is the ordering
        # proof; do not invent an ended_at timestamp from file mtime.
        sem_seq = semantic_row.get('request', {}).get('sequence')
        batch_seq = request.get('sequence')
        ordered = (type(sem_seq) is int and type(batch_seq) is int
                   and sem_seq > applied_sequence and batch_seq > applied_sequence)
    else:
        try:
            applied = stamp(state['repair_applied_at_utc'])
            ordered = (stamp(semantic_row['ended_at_utc']) >= applied
                       and stamp(batch_row['ended_at_utc']) >= applied)
        except (KeyError, TypeError, ValueError):
            return None
    if (frame is None or result is None or not ordered
            or request.get('command') != 'full_loop'
            or result.get('status') != 'bounded_loop_finished'
            or type(result.get('actual_turns')) is not int or result['actual_turns'] < 1
            or type(result.get('actual_end_date_raw')) is not int
            or result['actual_end_date_raw'] <= baseline.get('date_raw', -1)
            or frame['date_raw'] < result['actual_end_date_raw']
            or frame['actor_character_id'] != baseline.get('actor_character_id')
            or frame['episode_run_id'] != baseline.get('episode_run_id')):
        return None
    end = result.get('actual_end_frame')
    if isinstance(end, dict) and any(end.get(key) != frame[key]
                                    for key in ('actor_character_id', 'episode_run_id')):
        return None
    return {'fresh_semantic_frame': frame, 'actual_end_date_raw': result['actual_end_date_raw'],
            'actual_turns': result['actual_turns'], 'cumulative_cycles': result.get('cumulative_cycles'),
            'new_Game_calls_by_status_sidecar': 0}


def status_relay(state, now=None):
    """Compatibility projection for the already-running immutable overlay."""
    now = now or utc()
    brief = state['pause_reason']
    latest = state.get('last_decision') or {}
    context = '\n最近决策：' + latest['summary'] if latest.get('summary') else ''
    metadata = {'schema': SCHEMA, 'binding': state['binding'], 'incident_id': state['incident_id'],
                'phase': state['phase'], 'repair_message': state.get('repair_message'),
                'pause_reason': brief, 'expires_at_utc': state.get('expires_at_utc'),
                'business_credit': 0, 'cycle_credit': 0, 'Game_action_submitted': False,
                'Root_status_only': True}
    row = {'tool': TOOL, 'request': {'tool': TOOL}, 'ended_at_utc': now.isoformat(),
           'source': 'Root runtime repair status; no MCP call or business action',
           'root_runtime_repair_status': metadata}
    if state['phase'] in ('repairing', 'repair_applied_waiting_for_progress'):
        row['client_error'] = brief + '。正在修复中' + context
    elif state['phase'] == 'resolved':
        row['result'] = {'is_error': False, 'structured_content': {
            'status': '已恢复推进', 'step': '修复状态',
            'plan': {'phase': TOOL, 'reason': state['repair_message'] + '。已恢复推进' + context},
            'root_runtime_repair_status': metadata,
            'business_action': False, 'new_business_credit': 0}}
    else:
        raise ValueError('Terminal repair status must return to actual decision evidence')
    return row


class Publisher:
    def __init__(self, session, prefix):
        self.session = Path(session).resolve(strict=True)
        if not prefix.startswith('p') or not prefix[1:].isdigit():
            raise ValueError('Explicit SDK prefix is required')
        self.prefix = prefix
        self.queue = self.session / (prefix + '-queue')
        self.outbox = self.session / (prefix + '-responses')
        self.store = self.session / 'runtime-repair-status'
        self.current = self.store / 'CURRENT.json'
        launch = read(self.session / 'ROOT-ACTUAL-GAME-LAUNCH.json')
        request = read(self.session / 'ROOT-CURRENT-OBS-RECORDING-REQUESTED.json')
        job_root = Path(request['receipt_root']).resolve()
        if job_root.parent != (self.session / 'recordings').resolve():
            raise ValueError('Actual recording metadata escaped this session')
        job = read(job_root / 'job.json')
        if job['pid'] != launch['pid'] or job['launch'] != launch:
            raise ValueError('Actual Game recording generation differs')
        self.binding = {'session': str(self.session), 'sdk_prefix': prefix,
            'game_pid': launch['pid'], 'game_creation_filetime': job['game_creation_filetime'],
            'game_creation_date': launch['creation_date']}

    def state(self):
        if not self.current.exists():
            return None
        state = read(self.current)
        if state.get('schema') != SCHEMA or state.get('binding') != self.binding:
            raise ValueError('Repair status belongs to another session/Game/SDK generation')
        return state

    def responses(self):
        return sorted(self.outbox.glob('*-1-result.json'), key=lambda path: path.name, reverse=True)

    def latest_semantic(self):
        for path in self.responses():
            if path.stat().st_size <= 1024 * 1024:
                row = read(path)
                frame = semantic(row, self.binding)
                if frame is not None:
                    return path, row, frame
        return None

    def latest_decision(self):
        paths = sorted((self.session / 'responses').glob('*.json'),
                       key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for path in paths:
            if path.name.startswith('zz-runtime-repair-') or path.stat().st_size > 32768:
                continue
            row = read(path)
            if row.get('tool') == TOOL or row.get('client_error'):
                continue
            body = decode(row)
            if body is None:
                continue
            plan = body.get('plan') if isinstance(body.get('plan'), dict) else {}
            selected = body.get('selected_step') or body.get('step') or plan.get('selected_step')
            if isinstance(selected, str) and selected:
                return {'source': pin(path), 'summary': selected[:120]}, row
        return None, None

    def emit(self, state):
        latest, _ = self.latest_decision()
        if latest:
            state['last_decision'] = latest
        state['updated_at_utc'] = utc().isoformat()
        row = status_relay(state)
        relay = self.session / 'responses' / ('zz-runtime-repair-' +
            utc().strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8] + '.json')
        atomic(relay, row)
        state['last_overlay_relay'] = pin(relay)
        atomic(self.current, state, replace=True)
        return pin(relay)

    def repairing(self, halt_path, reason):
        halt_path = Path(halt_path).resolve(strict=True)
        if halt_path.parent != self.queue.resolve() or not halt_path.name.startswith('ROOT-REQUEST-HALTED-'):
            raise ValueError('Actual immutable queue halt receipt is required')
        halt = read(halt_path)
        if not isinstance(halt.get('original_request'), dict) or not halt.get('message'):
            raise ValueError('Queue halt receipt lacks the original request/reason')
        old = self.state()
        if old and old['halt_receipt'] == pin(halt_path) and old['phase'] != 'expired':
            return self.emit(old)
        # An already-repaired incident may be published later for presentation.
        # Bind its first actual post-halt SEM, not today's later progressed SEM.
        semantic_item = None
        halt_at = stamp(halt['at_utc'])
        for path in reversed(self.responses()):
            if path.stat().st_size > 1024 * 1024:
                continue
            row = read(path)
            frame = semantic(row, self.binding)
            if frame is not None and stamp(row['ended_at_utc']) >= halt_at:
                semantic_item = (path, row, frame)
                break
        if semantic_item:
            observed_frame = semantic_item[2]
        else:
            loop = read(self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json')
            observed_frame = loop['before']
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 100:
            raise ValueError('A short real stop reason (1..100 characters) is required')
        state = {'schema': SCHEMA, 'binding': self.binding, 'incident_id': uuid.uuid4().hex,
            'phase': 'repairing', 'pause_reason': reason.strip(), 'halt_receipt': pin(halt_path),
            'original_request': halt['original_request'], 'raw_pause_reason': halt['message'][:2048],
            'repair_message': None, 'observed_frame': observed_frame,
            'opened_at_utc': utc().isoformat(), 'expires_at_utc': None,
            'resolving_requires': 'actual post-repair semantic receipt and successful progressing FULL',
            'Game_action_submitted': False, 'business_credit': 0}
        atomic(self.store / (state['incident_id'] + '-OPENED.json'), state)
        return self.emit(state)

    def applied(self, evidence, message):
        state = self.state()
        if state is None or state['phase'] not in ('repairing', 'repair_applied_waiting_for_progress'):
            raise ValueError('An existing unresolved repair incident is required')
        path = Path(evidence).resolve(strict=True)
        if not path.is_relative_to(self.session.parent) or path.stat().st_size > 1024 * 1024:
            raise ValueError('Only the bounded real repair receipt under admitted N may bind')
        if not message or len(message) > 160:
            raise ValueError('A short real repair explanation is required')
        receipt = read(path)
        actual_applied_at = receipt.get('ended_at_utc') or receipt.get('at_utc')
        applied_sequence = receipt.get('request', {}).get('sequence')
        if path.parent == self.outbox.resolve() and type(applied_sequence) is int and decode(receipt) is not None:
            state['repair_applied_sequence'] = applied_sequence
        elif not isinstance(actual_applied_at, str) or stamp(actual_applied_at) > utc():
            raise ValueError('Repair evidence needs actual queue ordering or its completed timestamp')
        state.update(phase='repair_applied_waiting_for_progress', repair_message=message,
                     repair_evidence=pin(path), repair_applied_at_utc=actual_applied_at)
        atomic(self.store / (state['incident_id'] + '-APPLIED.json'), state)
        return self.emit(state)

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        if state['phase'] != 'repair_applied_waiting_for_progress':
            return False
        if semantic_path is None:
            item = self.latest_semantic()
        else:
            semantic_path = Path(semantic_path).resolve(strict=True)
            if semantic_path.parent != self.outbox.resolve():
                raise ValueError('Actual semantic evidence must be in this SDK outbox')
            semantic_row = read(semantic_path)
            item = (semantic_path, semantic_row, semantic(semantic_row, self.binding))
        if item is None:
            return False
        sem_path, sem_row, _ = item
        candidates = self.responses() if batch_path is None else [Path(batch_path).resolve(strict=True)]
        for path in candidates:
            if path.parent != self.outbox.resolve():
                raise ValueError('Actual successful batch must be in this SDK outbox')
            if path.stat().st_size > 1024 * 1024:
                continue
            row = read(path)
            proof = recovery_proof(state, sem_row, row)
            if proof:
                proof.update(semantic_receipt=pin(sem_path), successful_batch_receipt=pin(path))
                state.update(phase='resolved', recovery_proof=proof,
                             resolved_at_utc=utc().isoformat(),
                             expires_at_utc=(utc() + timedelta(seconds=30)).isoformat())
                atomic(self.store / (state['incident_id'] + '-RESOLVED.json'), state)
                self.emit(state)
                return True
        return False

    def expire(self, state):
        if state['phase'] != 'resolved' or utc() < stamp(state['expires_at_utc']):
            return False
        latest, actual = self.latest_decision()
        if actual is not None:
            projection = deepcopy(actual)
            projection.update(source='Root repair-status expiry: redisplay exact prior actual receipt; no action replay',
                source_ref=latest['source']['path'], source_sha256=latest['source']['sha256'],
                root_repair_status_expired=state['incident_id'], new_action_submitted=False)
            atomic(self.session / 'responses' / ('zz-runtime-repair-' +
                utc().strftime('%Y%m%dT%H%M%S%fZ') + '-EXPIRED.json'), projection)
        state.update(phase='expired', expired_at_utc=utc().isoformat(), status_visible=False)
        atomic(self.store / (state['incident_id'] + '-EXPIRED.json'), state)
        atomic(self.current, state, replace=True)
        return True

    def observe_halt(self):
        state_path = self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json'
        if not state_path.exists():
            return
        loop = read(state_path)
        pending = loop.get('pending_cycle') or {}
        state = self.state()
        for path in sorted(self.queue.glob('ROOT-REQUEST-HALTED-*.json'), reverse=True):
            halt = read(path)
            sequence = halt.get('original_request', {}).get('sequence')
            if pending.get('auto_sequence') != sequence:
                continue
            if state is None or state.get('halt_receipt') != pin(path):
                self.repairing(path, '自动推进受阻：' + str(halt.get('message', '未知错误'))[:80])
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--sdk-prefix', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    repairing = sub.add_parser('repairing')
    repairing.add_argument('--halt', type=Path, required=True)
    repairing.add_argument('--reason', required=True)
    applied = sub.add_parser('applied')
    applied.add_argument('--evidence', type=Path, required=True)
    applied.add_argument('--message', required=True)
    resolved = sub.add_parser('resolved')
    resolved.add_argument('--semantic', type=Path, required=True)
    resolved.add_argument('--batch', type=Path, required=True)
    sub.add_parser('watch')
    sub.add_parser('once')
    args = parser.parse_args()
    publisher = Publisher(args.session, args.sdk_prefix)
    if args.command in ('repairing', 'applied'):
        with writer_lock(publisher.store):
            result = (publisher.repairing(args.halt, args.reason) if args.command == 'repairing'
                      else publisher.applied(args.evidence, args.message))
        print(json.dumps(result), flush=True)
        return
    if args.command == 'resolved':
        with writer_lock(publisher.store):
            state = publisher.state()
            if state is None or not publisher.resolve_if_proved(state, args.semantic, args.batch):
                raise ValueError('Actual progressing FULL + fresh matching SEM proof is not qualified')
            print(json.dumps({'status': 'ACTUAL_PROGRESS_RESOLVED_PUBLISHED',
                              'state': str(publisher.current), 'runtime_calls': 0}), flush=True)
        return
    last_decision = None
    while True:
        with writer_lock(publisher.store):
            publisher.observe_halt()
            state = publisher.state()
            if state and state['phase'] != 'expired':
                publisher.resolve_if_proved(state)
                state = publisher.state()
                if not publisher.expire(state):
                    latest, _ = publisher.latest_decision()
                    fingerprint = (latest or {}).get('source')
                    if fingerprint != last_decision:
                        publisher.emit(state)
                        last_decision = fingerprint
        if args.command == 'once' or (publisher.store / 'STOP').exists():
            return
        if (publisher.session / 'ROOT-ACTUAL-GAME-EXIT.json').exists():
            exit_row = read(publisher.session / 'ROOT-ACTUAL-GAME-EXIT.json')
            if exit_row.get('pid', exit_row.get('game_pid')) == publisher.binding['game_pid']:
                return
        time.sleep(.5)


if __name__ == '__main__':
    main()
