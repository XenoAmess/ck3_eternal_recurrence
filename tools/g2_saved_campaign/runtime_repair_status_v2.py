"""Incremental repair-status observer; frozen v1 UI publisher stays untouched.

Decode real text-JSON relays. Poll only bounded small cursor/state metadata and
new sequence paths; no repeated response/halt directory glob or full sort.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
import uuid

from . import runtime_repair_status as core


def decode(row):
    envelope = row.get('result')
    if not isinstance(envelope, dict) or envelope.get('is_error', envelope.get('isError')):
        return None
    body = envelope.get('structured_content', envelope.get('structuredContent'))
    if isinstance(body, dict):
        return body
    for block in envelope.get('content', []):
        if not isinstance(block, dict) or block.get('type') != 'text':
            continue
        text = block.get('text')
        if not isinstance(text, str) or len(text.encode('utf-8')) > 32768:
            continue
        try:
            body = json.loads(text)
        except (ValueError, TypeError):
            continue
        if isinstance(body, dict):
            return body
    return None


core.decode = decode
ACTIVE_PUBLISHERS = []


def signature(path):
    try:
        info = path.stat()
    except FileNotFoundError:
        return None
    return info.st_mtime_ns, info.st_size


class ReceiptIndex:
    """Bounded initial tail, then exact new sequence names and pending FULLs."""
    def __init__(self, session, prefix, window=512):
        self.session, self.prefix, self.window = Path(session), prefix, window
        self.cursor = self.session / ('NEXT-SEQUENCE-' + prefix.upper() + '.json')
        self.outbox = self.session / (prefix + '-responses')
        self.inbox = self.session / (prefix + '-requests')
        self.cursor_signature = None
        self.next_sequence = None
        self.rows, self.pending = {}, {}
        self.important_pending = set()
        self.full_sequences = []
        self.generation = 0
        self.latest_actual = (None, None)
        self.latest_actual_key = None
        self.reads = 0

    def candidates(self, number):
        stem = f'{number:04d}'
        return [self.outbox / (stem + '-1-result.json'),
                self.session / 'responses' / (self.prefix + '-responses-' + stem + '-0-plan.json'),
                self.session / 'responses' / (self.prefix + '-responses-' + stem + '-1-result.json'),
                self.session / 'responses' / (stem + '-0-plan.json'),
                self.session / 'responses' / (stem + '-1-result.json')]

    def add_sequence(self, number, recent=True):
        request_path = self.inbox / f'{number:04d}-1-result.json'
        if request_path.is_file() and request_path.stat().st_size <= 32768:
            request = core.read(request_path)
            self.reads += 1
            if request.get('command') == 'full_loop':
                self.important_pending.add(number)
                self.full_sequences = (self.full_sequences + [number])[-16:]
        for path in self.candidates(number):
            if path.is_file():
                self.load(path, number)
            elif recent or number in self.important_pending:
                self.pending[path] = number

    def load(self, path, number):
        info = path.stat()
        if info.st_size > 1024 * 1024:
            return
        row = core.read(path)
        self.reads += 1
        self.rows[path] = (number, row)
        self.generation += 1
        if path.parent == self.outbox and number in self.important_pending:
            self.important_pending.discard(number)
        if info.st_size > 32768 or row.get('client_error') or row.get('tool') == core.TOOL:
            return
        body = decode(row)
        if body is None:
            return
        plan = body.get('plan') if isinstance(body.get('plan'), dict) else {}
        step = body.get('selected_step') or body.get('step') or plan.get('selected_step')
        key = (number, 1 if path.name.endswith('-1-result.json') else 0)
        if isinstance(step, str) and step and (self.latest_actual_key is None or key > self.latest_actual_key):
            self.latest_actual = ({'source': core.pin(path), 'summary': step[:120]}, row)
            self.latest_actual_key = key

    def refresh(self):
        cursor_sig = signature(self.cursor)
        if cursor_sig is not None and cursor_sig != self.cursor_signature:
            cursor = core.read(self.cursor)
            self.reads += 1
            current = cursor.get('next_sequence')
            if type(current) is not int or current < 1:
                raise ValueError('Actual NEXT cursor is invalid')
            if self.next_sequence is not None and current < self.next_sequence:
                raise ValueError('Actual SDK cursor moved backwards')
            start = max(1, current - self.window) if self.next_sequence is None else self.next_sequence
            for number in range(start, current + 1):
                self.add_sequence(number, recent=number >= current - 8)
            self.next_sequence, self.cursor_signature = current, cursor_sig
            floor = current - self.window
            self.rows = {path: item for path, item in self.rows.items() if item[0] >= floor}
            self.pending = {path: number for path, number in self.pending.items()
                            if number >= current - 8 or number in self.important_pending}
        # Completed parent FULLs can arrive after dozens of their child AUTO
        # requests. Keep those exact pending parents, rather than a directory
        # search or an arbitrary assumption that they finish within eight IDs.
        for path, number in list(self.pending.items()):
            if path.is_file():
                self.load(path, number)
                self.pending.pop(path, None)

    def response_paths(self):
        self.refresh()
        return [path for path, _ in sorted(
            ((path, item[0]) for path, item in self.rows.items() if path.parent == self.outbox),
            key=lambda pair: pair[1], reverse=True)]


class IncrementalPublisher(core.Publisher):
    def __init__(self, session, prefix):
        super().__init__(session, prefix)
        self.index = ReceiptIndex(self.session, prefix)
        self._semantic_generation = -1
        self._semantic_item = None
        self._proof_generation = -1
        self._loop_signature = None
        self._loop = None
        self._feeder_signature = None
        self._deadline_incident = None
        self._deadline = None
        self._recording_signature = None
        self._sdk_handles = None
        self._sdk_capture_error = None
        self._sdk_failure_reported = False
        ACTIVE_PUBLISHERS.append(self)

    def close(self):
        for _, handle in self._sdk_handles or []:
            handle.close()
        self._sdk_handles = []

    def open_source_incident(self, source_path, reason, kind, details=None):
        current = self.state()
        if current and current['phase'] != 'expired':
            return
        semantic = self.latest_semantic()
        if semantic is None:
            return
        state = {'schema': core.SCHEMA, 'binding': self.binding, 'incident_id': uuid.uuid4().hex,
            'phase': 'repairing', 'pause_reason': reason[:100], 'halt_receipt': core.pin(source_path),
            'source_kind': kind, 'raw_pause_reason': reason[:2048], 'repair_message': None,
            'observed_frame': semantic[2], 'opened_at_utc': core.utc().isoformat(),
            'expires_at_utc': None, 'Game_action_submitted': False, 'business_credit': 0,
            'source_details': details or {}}
        core.atomic(self.store / (state['incident_id'] + '-OPENED.json'), state)
        self.emit(state)

    def observe_sdk_pair(self):
        """Root execution retains only the two exact published SDK handles.

        No machine/process enumeration, Game query, process mutation or MCP.
        Handles are captured once and kernel exit is observed without polling
        process names or reusing PIDs. Offline tests inject fake handles.
        """
        pair_path = self.session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.prefix.upper() + '.json')
        if self._sdk_handles is None:
            pair = core.read(pair_path)
            rows = pair.get('processes') or []
            if (pair.get('status') != 'SDK_PAIR_HANDLES_RETAINED' or len(rows) != 2
                    or {row.get('role') for row in rows} != {'sdk_queue', 'sdk_application'}):
                raise ValueError('Actual exact SDK pair metadata is required')
            from .sdk_process_custody import RetainedProcessGeneration
            self._sdk_handles = []
            try:
                for row in rows:
                    handle = RetainedProcessGeneration.capture(row['pid'],
                        expected_creation_filetime=row['creation_filetime'],
                        expected_executable=Path(row['executable']))
                    self._sdk_handles.append((row['role'], handle))
            except (OSError, ValueError, RuntimeError) as error:
                self._sdk_capture_error = {'error_type': type(error).__name__, 'message': str(error)[:1024],
                    'kernel_exit_inferred': False, 'published_pair': pair}
        exits = [{**handle.identity(role), **handle.observe()} for role, handle in self._sdk_handles]
        if not self._sdk_failure_reported and (self._sdk_capture_error
                or any(row['kernel_exit_observed'] for row in exits)):
            self._sdk_failure_reported = True
            proof = self.store / ('SDK-PAIR-OBSERVED-' + uuid.uuid4().hex + '.json')
            core.atomic(proof, {'schema': 'xar.runtime-repair-sdk-pair-observation/v1',
                'binding': self.binding, 'at_utc': core.utc().isoformat(), 'pair_pin': core.pin(pair_path),
                'observed_processes': exits, 'capture_error': self._sdk_capture_error,
                'process_mutation_calls': 0, 'Game_MCP_OBS_Desktop_calls': 0})
            reason = ('SDK进程身份暂不可核验，自动推进暂停' if self._sdk_capture_error
                      else 'SDK进程已退出，自动推进暂停')
            self.open_source_incident(proof, reason, 'exact_retained_SDK_pair_observation')

    def responses(self):
        return self.index.response_paths()

    def latest_decision(self):
        self.index.refresh()
        return self.index.latest_actual

    def latest_semantic(self):
        self.index.refresh()
        if self._semantic_generation == self.index.generation:
            return self._semantic_item
        for path in self.index.response_paths():
            row = self.index.rows[path][1]
            frame = core.semantic(row, self.binding)
            if frame is not None:
                self._semantic_item = (path, row, frame)
                break
        self._semantic_generation = self.index.generation
        return self._semantic_item

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        self.index.refresh()
        if semantic_path is None and batch_path is None:
            marker = (self.index.generation, state.get('repair_applied_sequence'),
                      state.get('repair_applied_at_utc'))
            if marker == self._proof_generation:
                return False
            self._proof_generation = marker
        return super().resolve_if_proved(state, semantic_path, batch_path)

    def expire(self, state):
        if state.get('phase') != 'resolved':
            return False
        if self._deadline_incident != state['incident_id']:
            self._deadline_incident = state['incident_id']
            remaining = max(0.0, (core.stamp(state['expires_at_utc']) - core.utc()).total_seconds())
            self._deadline = time.monotonic() + remaining
        if time.monotonic() < self._deadline:
            return False
        latest, actual = self.latest_decision()
        if actual is not None:
            projection = deepcopy(actual)
            projection.update(source='Root status TTL ended: redisplay exact prior actual receipt; no action replay',
                source_ref=latest['source']['path'], source_sha256=latest['source']['sha256'],
                root_repair_status_expired=state['incident_id'], new_action_submitted=False)
            core.atomic(self.session / 'responses' / ('zz-runtime-repair-' +
                core.utc().strftime('%Y%m%dT%H%M%S%fZ') + '-EXPIRED.json'), projection)
        state.update(phase='expired', expired_at_utc=core.utc().isoformat(),
                     status_visible=False, monotonic_ttl_elapsed=True)
        core.atomic(self.store / (state['incident_id'] + '-EXPIRED.json'), state)
        core.atomic(self.current, state, replace=True)
        return True

    def observe_halt(self):
        self.index.refresh()
        self.observe_sdk_pair()
        loop_path = self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json'
        current_signature = signature(loop_path)
        if current_signature != self._loop_signature and current_signature is not None:
            self._loop = core.read(loop_path)
            self._loop_signature = current_signature
        pending = (self._loop or {}).get('pending_cycle') or {}
        number = pending.get('auto_sequence')
        if type(number) is int:
            # Different harnesses name halt receipts after the failed AUTO or
            # its enclosing FULL. Both exact sequences are already indexed.
            candidates = [number, *reversed(self.index.full_sequences)]
            for candidate in dict.fromkeys(candidates):
                path = self.queue / f'ROOT-REQUEST-HALTED-{candidate:04d}.json'
                if not path.is_file():
                    continue
                halt = core.read(path)
                if halt.get('original_request', {}).get('sequence') != number:
                    continue
                state = self.state()
                if state is None or state.get('halt_receipt') != core.pin(path):
                    self.repairing(path, '自动推进受阻：' + str(halt.get('message', '未知错误'))[:80])
                return
        self.observe_feeder_error()
        self.observe_recording_pause()

    def observe_recording_pause(self):
        state = self.state()
        if state and state['phase'] != 'expired':
            return
        health = self.session / ('automatic-recording-recovery-' + self.prefix) / 'STATUS.json'
        current_signature = signature(health)
        if current_signature is None or current_signature == self._recording_signature:
            return
        self._recording_signature = current_signature
        row = core.read(health)
        status = row.get('status')
        recovery_states = {'waiting_feeder_exit', 'waiting_normal_cleanup', 'waiting_overlay',
            'waiting_segment', 'waiting_frame', 'waiting_attach', 'capture_restored_business_halt_preserved',
            'blocked'}
        if status not in recovery_states:
            return
        # A capture-only issue need not halt gameplay. Display a gameplay
        # repair only when an actual retained halt or feeder-stop receipt says
        # that advancement has been suspended; never equate OBS waiting with
        # a Game failure on its own.
        halt_path = self.session / ('ROOT-CURRENT-HALT-' + self.prefix.upper() + '.json')
        stop_path = self.session / ('ROOT-CONTINUOUS-FEEDER-STOP-' + self.prefix.upper())
        feeder_path = self.session / ('ROOT-CONTINUOUS-FEEDER-STATUS-' + self.prefix.upper() + '.json')
        stopped = False
        if feeder_path.is_file():
            stopped = core.read(feeder_path).get('status') == 'operator_stopped'
        if stop_path.is_file():
            try:
                stopped = stopped or core.read(stop_path).get('reason') == 'automatic_recording_recovery'
            except ValueError:
                pass
        if not halt_path.is_file() and not stopped:
            return
        details = {'recording_recovery_status': status,
                   'retained_halt': core.pin(halt_path) if halt_path.is_file() else None,
                   'feeder_stop': core.pin(stop_path) if stop_path.is_file() else None}
        self.open_source_incident(health, '录制恢复期间自动推进暂停',
                                  'actual_recording_recovery_and_feeder_pause', details)

    def observe_feeder_error(self):
        state = self.state()
        if state and state['phase'] != 'expired':
            return
        path = self.session / ('ROOT-CONTINUOUS-FEEDER-STATUS-' + self.prefix.upper() + '.json')
        current_signature = signature(path)
        if current_signature is None or current_signature == self._feeder_signature:
            return
        self._feeder_signature = current_signature
        feeder = core.read(path)
        sequence = feeder.get('control_sequence', feeder.get('failed_control_sequence'))
        kind = feeder.get('status')
        if (type(sequence) is not int or not isinstance(kind, str)
                or not kind.startswith(('halted', 'failed', 'error'))):
            return
        response = self.outbox / f'{sequence:04d}-1-result.json'
        if not response.is_file():
            self._feeder_signature = None
            return
        row = core.read(response)
        wrapper = row.get('result') or {}
        request = row.get('request', {})
        if (request.get('sequence') != sequence or request.get('command') != 'full_loop'
                or not (row.get('client_error') or wrapper.get('is_error', wrapper.get('isError')))):
            return
        if state and state.get('halt_receipt') == core.pin(response):
            return
        semantic = self.latest_semantic()
        if semantic is None:
            return
        reason = str(row.get('client_error') or '自动规划批次返回错误')[:2048]
        state = {'schema': core.SCHEMA, 'binding': self.binding, 'incident_id': uuid.uuid4().hex,
            'phase': 'repairing', 'pause_reason': '自动推进受阻：' + reason[:80],
            'halt_receipt': core.pin(response), 'feeder_error_receipt': core.pin(path),
            'source_kind': 'actual_failed_feeder_FULL_receipt', 'original_request': request,
            'raw_pause_reason': reason, 'repair_message': None, 'observed_frame': semantic[2],
            'opened_at_utc': core.utc().isoformat(), 'expires_at_utc': None,
            'Game_action_submitted': False, 'business_credit': 0}
        core.atomic(self.store / (state['incident_id'] + '-OPENED.json'), state)
        self.emit(state)


if __name__ == '__main__':
    core.Publisher = IncrementalPublisher
    try:
        core.main()
    finally:
        for publisher in ACTIVE_PUBLISHERS:
            publisher.close()
