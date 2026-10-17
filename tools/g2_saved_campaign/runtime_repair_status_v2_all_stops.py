"""Incremental v2 plus settled-summary errors and typed-blocked feeder stops.

The exact frozen v1/v2 sources remain intact. Root is the sole runtime owner.
"""
from pathlib import Path
import uuid

from . import runtime_repair_status_v2 as v2
core = v2.core


def feeder_stopped(feeder, response):
    """A real feeder halt is meaningful even if FULL has a typed blocked DTO."""
    kind = feeder.get('status')
    request = response.get('request') or {}
    number = feeder.get('control_sequence', feeder.get('failed_control_sequence'))
    if (not isinstance(kind, str) or not kind.startswith(('halted', 'failed', 'error'))
            or type(number) is not int or request.get('sequence') != number
            or request.get('command') != 'full_loop'):
        return None
    # No business outcome or credit is inferred: this is the actual feeder's
    # own stopped state, bound to its exact original FULL receipt.
    reason = feeder.get('reason') or feeder.get('error') or response.get('client_error')
    if not isinstance(reason, str):
        reason = '自动推进校验受阻，等待修复'
    return request, reason[:2048]


class AllStopsPublisher(v2.IncrementalPublisher):
    def applied(self, evidence, message):
        state = self.state()
        receipt = core.read(Path(evidence).resolve(strict=True))
        repair_sequence = receipt.get('request', {}).get('sequence')
        failed_sequence = (state or {}).get('original_request', {}).get('sequence')
        if state and type(repair_sequence) is int and type(failed_sequence) is int:
            state['resume_baseline_confirmed'] = False
            # The failed action may already have changed the calendar. Use a
            # real paused SEM after that failure, before repair, as the stop
            # baseline. Do not count reconsume of its physical day as resume.
            for path in self.responses():
                row = self.index.rows[path][1]
                number = row.get('request', {}).get('sequence')
                frame = core.semantic(row, self.binding)
                if frame and type(number) is int and failed_sequence < number < repair_sequence:
                    state['observed_frame'] = frame
                    state['stop_semantic_receipt'] = core.pin(path)
                    state['resume_baseline_confirmed'] = True
                    break
            core.atomic(self.current, state, replace=True)
        return super().applied(evidence, message)

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        if state.get('resume_baseline_confirmed') is False:
            item = self.latest_semantic()
            sequence = (item[1].get('request', {}).get('sequence') if item else None)
            if (item and type(sequence) is int
                    and sequence > state.get('repair_applied_sequence', sequence)):
                state['observed_frame'] = item[2]
                state['stop_semantic_receipt'] = core.pin(item[0])
                state['resume_baseline_confirmed'] = True
                core.atomic(self.current, state, replace=True)
            # A fresh stop baseline is useful, but is not itself proof that
            # another calendar day progressed. Wait for a later real FULL.
            return False
        return super().resolve_if_proved(state, semantic_path, batch_path)

    def _open_exact(self, path, request, reason, kind, companion=None):
        state = self.state()
        if state and state['phase'] != 'expired':
            return
        if state and state.get('halt_receipt') == core.pin(path):
            return
        previous = (state or {}).get('original_request', {}).get('sequence', 0)
        if type(previous) is int and request.get('sequence', 0) <= previous:
            return
        semantic = self.latest_semantic()
        if semantic is None:
            return
        state = {'schema': core.SCHEMA, 'binding': self.binding, 'incident_id': uuid.uuid4().hex,
            'phase': 'repairing', 'pause_reason': ('自动推进受阻：' + reason)[:100],
            'halt_receipt': core.pin(path), 'source_kind': kind, 'original_request': request,
            'raw_pause_reason': reason, 'repair_message': None, 'observed_frame': semantic[2],
            'opened_at_utc': core.utc().isoformat(), 'expires_at_utc': None,
            'Game_action_submitted': False, 'business_credit': 0}
        if companion is not None:
            state['feeder_error_receipt'] = core.pin(companion)
        core.atomic(self.store / (state['incident_id'] + '-OPENED.json'), state)
        self.emit(state)

    def observe_halt(self):
        super().observe_halt()
        state = self.state()
        if state and state['phase'] != 'expired':
            return
        # A FULL can fail after the TURN was already settled. pending_cycle
        # is then None. Probe only the latest bounded, indexed FULL sequences;
        # preserve that settled credit and show the actual summary exception.
        for number in reversed(self.index.full_sequences):
            halt_path = self.queue / f'ROOT-REQUEST-HALTED-{number:04d}.json'
            result_path = self.outbox / f'{number:04d}-1-result.json'
            if not halt_path.is_file() or not result_path.is_file():
                continue
            halt, response = core.read(halt_path), core.read(result_path)
            request = halt.get('original_request')
            if (not isinstance(request, dict) or not halt.get('message')
                    or response.get('request', {}).get('command') != 'full_loop'
                    or response.get('request', {}).get('sequence') != number
                    or not (response.get('client_error') or (response.get('result') or {}).get('is_error'))):
                continue
            self._open_exact(halt_path, request, str(halt['message'])[:2048],
                             'actual_queue_exception_after_or_without_pending')
            break

    def observe_feeder_error(self):
        super().observe_feeder_error()
        state = self.state()
        if state and state['phase'] != 'expired':
            return
        path = self.session / ('ROOT-CONTINUOUS-FEEDER-STATUS-' + self.prefix.upper() + '.json')
        current_signature = v2.signature(path)
        if current_signature is None or current_signature == getattr(self, '_typed_feeder_signature', None):
            return
        self._typed_feeder_signature = current_signature
        feeder = core.read(path)
        number = feeder.get('control_sequence', feeder.get('failed_control_sequence'))
        if type(number) is not int:
            return
        result_path = self.outbox / f'{number:04d}-1-result.json'
        if not result_path.is_file():
            self._typed_feeder_signature = None
            return
        qualified = feeder_stopped(feeder, core.read(result_path))
        if qualified:
            request, reason = qualified
            self._open_exact(result_path, request, reason, 'actual_feeder_stop_including_typed_blocked', path)


if __name__ == '__main__':
    core.Publisher = AllStopsPublisher
    try:
        core.main()
    finally:
        for publisher in v2.ACTIVE_PUBLISHERS:
            publisher.close()
