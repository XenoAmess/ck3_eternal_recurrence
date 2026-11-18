"""Exact cancelled-read proof and same-owner progress for the existing Fresh Full tool.

No executor, timeout, transport or world-action latch is owned by this module.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
from typing import Literal, Mapping


class FreshOwnerDriftV1(ValueError):
    """A cancelled read cannot authorize another owner or restored context."""


def _object(value: object, keys: set[str] | None = None) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError('Fresh read proof requires an object with named fields')
    if keys is not None and set(value) != keys:
        raise ValueError('Fresh read proof fields differ')
    return value


def _integer(value: object, maximum: int, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value < maximum:
        raise ValueError('Fresh read proof integer is malformed')
    return value


def _decimal(value: object, minimum: int = 0) -> int:
    if not isinstance(value, str) or re.fullmatch('0|[1-9][0-9]{0,19}', value) is None:
        raise ValueError('Fresh read proof decimal is malformed')
    return _integer(int(value), 2**64, minimum)


def _actor(value: object) -> int:
    actor = _integer(value, 2**31, -(2**31))
    if actor == -1:
        raise ValueError('Fresh read actor uses the invalid character sentinel')
    return actor


def _tls_flag(value: object) -> int:
    flag = _integer(value, 2**32, 1)
    if flag != 1:
        raise ValueError('Fresh read owner TLS flag must equal the Native qualified value 1')
    return flag


@dataclass(frozen=True)
class CancelledFreshReadV1:
    request_id: str
    owner_tid: int
    query_sequence: int
    elapsed_ms: int
    pump_start: int
    pump_end: int
    wake_attempts: int
    wake_succeeded: int
    wake_failed: int
    last_wake_error: int

    @classmethod
    def parse(cls, value: object) -> CancelledFreshReadV1:
        row = _object(value, {'schema', 'request_id', 'step', 'fresh_full_state_diagnostic'})
        request = row['request_id']
        if (row['schema'] != 'xar.native.fresh-full-state-read-rejection/v1'
                or row['step'] != 'query-fresh-full-state-v1' or not isinstance(request, str)
                or re.fullmatch('fresh-full-[1-9][0-9]*-[0-9a-f]{12}', request) is None):
            raise ValueError('Fresh read rejection identity differs')
        d = _object(row['fresh_full_state_diagnostic'], {'schema', 'stage', 'submit_result', 'wait_result',
            'reclaim_result', 'wait_running_timeouts', 'query_sequence', 'elapsed_ms', 'owner_thread_id',
            'pump_epoch_at_start', 'pump_epoch_at_end', 'wake_attempts', 'wake_succeeded', 'wake_failed',
            'last_wake_error', 'fresh_available', 'queued_wake_interval_ms'})
        if (d['schema'] != 'xar.native.fresh-full-state-diagnostic/v1' or d['stage'] != 'wait_terminal'
                or any(type(d[key]) is not int or d[key] != expected for key, expected in
                    (('submit_result', 0), ('wait_result', 4), ('reclaim_result', 0),
                     ('wait_running_timeouts', 0), ('queued_wake_interval_ms', 250)))
                or d['fresh_available'] is not False):
            raise ValueError('Fresh read is not the reclaimed unexecuted queued cancellation')
        result = cls(request, _integer(d['owner_thread_id'], 2**32, 1), _decimal(d['query_sequence'], 1),
            _decimal(d['elapsed_ms'], 8000), _decimal(d['pump_epoch_at_start'], 1),
            _decimal(d['pump_epoch_at_end'], 1), _integer(d['wake_attempts'], 2**32),
            _integer(d['wake_succeeded'], 2**32), _integer(d['wake_failed'], 2**32),
            _integer(d['last_wake_error'], 2**32))
        if result.pump_end < result.pump_start or result.wake_attempts != result.wake_succeeded + result.wake_failed:
            raise ValueError('Fresh read diagnostic counters differ')
        return result

    def to_json(self) -> dict[str, object]:
        return {'schema': 'xar.native.fresh-full-state-read-rejection/v1', 'request_id': self.request_id,
            'step': 'query-fresh-full-state-v1', 'fresh_full_state_diagnostic': {
                'schema': 'xar.native.fresh-full-state-diagnostic/v1', 'stage': 'wait_terminal',
                'submit_result': 0, 'wait_result': 4, 'reclaim_result': 0, 'wait_running_timeouts': 0,
                'query_sequence': str(self.query_sequence), 'elapsed_ms': str(self.elapsed_ms),
                'owner_thread_id': self.owner_tid, 'pump_epoch_at_start': str(self.pump_start),
                'pump_epoch_at_end': str(self.pump_end), 'wake_attempts': self.wake_attempts,
                'wake_succeeded': self.wake_succeeded, 'wake_failed': self.wake_failed,
                'last_wake_error': self.last_wake_error, 'fresh_available': False, 'queued_wake_interval_ms': 250}}


@dataclass(frozen=True)
class OwnerHookV1:
    completed: int
    completed_ms: int
    owner_tid: int

    @classmethod
    def parse(cls, value: object) -> OwnerHookV1:
        row = _object(value)
        return cls(_decimal(row.get('completed')), _decimal(row.get('last_completed_ms')),
                   _integer(row.get('last_thread_id'), 2**32))

    def to_json(self) -> dict[str, object]:
        return {'completed': str(self.completed), 'last_completed_ms': str(self.completed_ms), 'last_thread_id': self.owner_tid}


@dataclass(frozen=True)
class FreshOwnerV1:
    pid: int
    generation: int
    owner_tid: int
    date_raw: int
    jomini_state: int
    game_state: int
    tls_global: int
    tls_marker: int
    tls_context: int
    heartbeat_sequence: int
    pump: int
    peek: OwnerHookV1
    poll: OwnerHookV1

    def identity(self) -> tuple[int, ...]:
        return (self.pid, self.generation, self.owner_tid, self.date_raw, self.jomini_state, self.game_state,
                self.tls_global, self.tls_marker, self.tls_context)

    @staticmethod
    def context(diagnostics: object) -> tuple[int, ...]:
        d = _object(diagnostics)
        if d.get('connected') is not True:
            raise FreshOwnerDriftV1('Fresh cancelled read lost its original native connection')
        heartbeat = _object(d.get('last_heartbeat'))
        mailbox = _object(heartbeat.get('main_thread_query_mailbox_v1'))
        return (_integer(d.get('bridge_pid'), 2**32, 1), _integer(d.get('connection_generation'), 2**64, 1),
            _integer(mailbox.get('owner_tid'), 2**32, 1), _integer(mailbox.get('date_raw'), 2**63),
            _integer(mailbox.get('jomini_state'), 2**64, 1), _integer(mailbox.get('game_state'), 2**64, 1),
            _tls_flag(mailbox.get('tls_global')), _tls_flag(mailbox.get('tls_marker')),
            _integer(mailbox.get('tls_context'), 2**64, 1))

    @staticmethod
    def sequence(diagnostics: object) -> int:
        return _integer(_object(_object(diagnostics).get('last_heartbeat')).get('sequence'), 2**64, 1)

    @classmethod
    def observe(cls, diagnostics: object) -> FreshOwnerV1:
        d = _object(diagnostics)
        pid, generation = _integer(d.get('bridge_pid'), 2**32, 1), _integer(d.get('connection_generation'), 2**64, 1)
        heartbeat = _object(d.get('last_heartbeat'))
        mailbox = _object(heartbeat.get('main_thread_query_mailbox_v1'))
        observer = _object(heartbeat.get('snapshot_observer_12002'))
        owner = _integer(mailbox.get('owner_tid'), 2**32, 1)
        pump = _integer(mailbox.get('pump_epochs'), 2**64, 1)
        entries = _object(mailbox.get('owner_hook_entries_v1'))
        if (d.get('connected') is not True or d.get('transport_fatal_error') is not None
                or d.get('last_error') is not None or _integer(heartbeat.get('pid'), 2**32, 1) != pid
                or mailbox.get('ready') is not True or mailbox.get('stamp_read_success') is not True
                or mailbox.get('stop') is not False or type(mailbox.get('failure')) is not int or mailbox['failure'] != 0
                or mailbox.get('paused') is not True or mailbox.get('active_hook_calls') != 0
                or type(mailbox.get('active_hook_calls')) is not int
                or _integer(mailbox.get('owner_verified_pump_epochs'), 2**64, 2) > pump
                or _integer(mailbox.get('current_tid'), 2**32, 1) != owner
                or observer.get('read_in_progress') is not False
                or _integer(observer.get('completed_ms'), 2**64) < _integer(observer.get('started_ms'), 2**64)
                or entries.get('schema') != 'xar.native.owner-hook-entries/v1'):
            raise ValueError('Fresh retry lacks its qualified completed paused owner observation')
        return cls(pid, generation, owner, _integer(mailbox.get('date_raw'), 2**63),
            _integer(mailbox.get('jomini_state'), 2**64, 1), _integer(mailbox.get('game_state'), 2**64, 1),
            _tls_flag(mailbox.get('tls_global')), _tls_flag(mailbox.get('tls_marker')),
            _integer(mailbox.get('tls_context'), 2**64, 1),
            _integer(heartbeat.get('sequence'), 2**64, 1), pump,
            OwnerHookV1.parse(entries.get('peek')), OwnerHookV1.parse(entries.get('poll')))

    def to_json(self) -> dict[str, object]:
        return {'pid': self.pid, 'generation': str(self.generation), 'owner_tid': self.owner_tid,
            'date_raw': self.date_raw, 'jomini_state': str(self.jomini_state), 'game_state': str(self.game_state),
            'tls_global': self.tls_global, 'tls_marker': self.tls_marker, 'tls_context': str(self.tls_context),
            'heartbeat_sequence': str(self.heartbeat_sequence), 'pump': str(self.pump),
            'peek': self.peek.to_json(), 'poll': self.poll.to_json()}

    @classmethod
    def parse(cls, value: object) -> FreshOwnerV1:
        row = _object(value, {'pid', 'generation', 'owner_tid', 'date_raw', 'jomini_state', 'game_state', 'tls_global', 'tls_marker', 'tls_context',
                              'heartbeat_sequence', 'pump', 'peek', 'poll'})
        return cls(_integer(row['pid'], 2**32, 1), _decimal(row['generation'], 1),
            _integer(row['owner_tid'], 2**32, 1), _integer(row['date_raw'], 2**63),
            _decimal(row['jomini_state'], 1), _decimal(row['game_state'], 1),
            _tls_flag(row['tls_global']), _tls_flag(row['tls_marker']), _decimal(row['tls_context'], 1),
            _decimal(row['heartbeat_sequence'], 1), _decimal(row['pump'], 1),
            OwnerHookV1.parse(row['peek']), OwnerHookV1.parse(row['poll']))


@dataclass(frozen=True)
class FreshCancelledGateV1:
    receipt: CancelledFreshReadV1
    source: FreshOwnerV1
    actor_id: int
    failure_heartbeat_sequence: int
    anchor: FreshOwnerV1 | None = None

    def observation(self, diagnostics: object) -> FreshOwnerV1 | None:
        if FreshOwnerV1.context(diagnostics) != self.source.identity():
            raise FreshOwnerDriftV1('Fresh cancelled read changed its process/connection/owner/TLS/root/date')
        try:
            return FreshOwnerV1.observe(diagnostics)
        except ValueError:
            return None  # A busy or temporarily unqualified owner earns no new read.

    def sample(self, owner: FreshOwnerV1) -> FreshCancelledGateV1:
        if owner.identity() != self.source.identity() or owner.pump < self.receipt.pump_end:
            raise FreshOwnerDriftV1('Fresh cancelled read crossed its original process/connection/owner/paused context')
        if self.anchor is None and owner.heartbeat_sequence > self.failure_heartbeat_sequence:
            return replace(self, anchor=owner)
        return self

    def permits(self, owner: FreshOwnerV1) -> bool:
        self.sample(owner)  # A changed identity remains a hard failure.
        anchor = self.anchor
        if anchor is None or owner.heartbeat_sequence <= anchor.heartbeat_sequence or owner.pump <= max(anchor.pump, self.receipt.pump_end):
            return False
        return any(new.owner_tid == self.source.owner_tid and new.completed > old.completed
                   and new.completed_ms > old.completed_ms for old, new in ((anchor.peek, owner.peek), (anchor.poll, owner.poll)))

    def to_json(self) -> dict[str, object]:
        return {'schema': 'xar.native.fresh-full-cancelled-read-gate/v1', 'receipt': self.receipt.to_json(),
            'source': self.source.to_json(), 'actor_id': self.actor_id,
            'failure_heartbeat_sequence': str(self.failure_heartbeat_sequence),
            'anchor': self.anchor.to_json() if self.anchor is not None else None, 'business_submission': False}

    @classmethod
    def parse(cls, value: object) -> FreshCancelledGateV1:
        row = _object(value, {'schema', 'receipt', 'source', 'actor_id', 'failure_heartbeat_sequence', 'anchor', 'business_submission'})
        if row['schema'] != 'xar.native.fresh-full-cancelled-read-gate/v1' or row['business_submission'] is not False:
            raise ValueError('Fresh read gate schema differs')
        gate = cls(CancelledFreshReadV1.parse(row['receipt']), FreshOwnerV1.parse(row['source']),
            _actor(row['actor_id']), _decimal(row['failure_heartbeat_sequence'], 1),
            FreshOwnerV1.parse(row['anchor']) if row['anchor'] is not None else None)
        if gate.receipt.owner_tid != gate.source.owner_tid or gate.source.pump > gate.receipt.pump_end:
            raise ValueError('Fresh read gate source differs from its exact cancellation')
        if gate.anchor is not None and (gate.anchor.identity() != gate.source.identity()
                or gate.anchor.heartbeat_sequence <= gate.failure_heartbeat_sequence or gate.anchor.pump < gate.receipt.pump_end):
            raise ValueError('Fresh read gate post-failure anchor differs')
        return gate


def cancelled_receipt_from_mcp_error_v1(error: BaseException) -> CancelledFreshReadV1 | None:
    """Corroborate the exact original error; this alone never grants a retry."""
    prefix = ('MCP tool ck3_take_fresh_full_snapshot_v1 returned an error: '
              'Error executing tool ck3_take_fresh_full_snapshot_v1: native gameplay step failed: '
              'fresh_full_state_read_failed; original parsed return receipt=')
    if not isinstance(error, RuntimeError) or not str(error).startswith(prefix):
        return None
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate original receipt field')
            value[key] = item
        return value
    try:
        return CancelledFreshReadV1.parse(json.loads(str(error)[len(prefix):], object_pairs_hook=unique))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class FreshReadPreSubmissionWaitV1:
    call_sequence: int
    request_sequence_before: int
    gate: FreshCancelledGateV1
    reason: Literal['owner_temporarily_unqualified', 'awaiting_completed_owner']

    def to_json(self) -> dict[str, object]:
        return {'schema': 'xar.sdk.fresh-full-read-presubmission-wait/v1', 'call_sequence': str(self.call_sequence),
            'request_sequence_before': str(self.request_sequence_before), 'cancelled_read_gate': self.gate.to_json(),
            'reason': self.reason, 'native_request_created': False, 'native_request_sent': False,
            'step': 'query-fresh-full-state-v1'}

    @classmethod
    def parse(cls, value: object) -> FreshReadPreSubmissionWaitV1:
        row = _object(value, {'schema', 'call_sequence', 'request_sequence_before', 'cancelled_read_gate',
            'reason', 'native_request_created', 'native_request_sent', 'step'})
        reason = row['reason']
        if (row['schema'] != 'xar.sdk.fresh-full-read-presubmission-wait/v1' or row['step'] != 'query-fresh-full-state-v1'
                or row['native_request_created'] is not False or row['native_request_sent'] is not False
                or reason not in ('owner_temporarily_unqualified', 'awaiting_completed_owner')):
            raise ValueError('Fresh read pre-submission wait proof differs')
        if reason == 'owner_temporarily_unqualified':
            return cls(_decimal(row['call_sequence'], 1), _decimal(row['request_sequence_before']),
                       FreshCancelledGateV1.parse(row['cancelled_read_gate']), 'owner_temporarily_unqualified')
        return cls(_decimal(row['call_sequence'], 1), _decimal(row['request_sequence_before']),
                   FreshCancelledGateV1.parse(row['cancelled_read_gate']), 'awaiting_completed_owner')


def presubmission_wait_from_mcp_error_v1(error: BaseException) -> FreshReadPreSubmissionWaitV1 | None:
    prefix = ('MCP tool ck3_take_fresh_full_snapshot_v1 returned an error: Error executing tool '
              'ck3_take_fresh_full_snapshot_v1: fresh Full SDK pre-submission wait; original SDK parsed receipt=')
    if not isinstance(error, RuntimeError) or not str(error).startswith(prefix):
        return None
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value: raise ValueError('Duplicate SDK pre-submission proof field')
            value[key] = item
        return value
    try:
        return FreshReadPreSubmissionWaitV1.parse(json.loads(str(error)[len(prefix):], object_pairs_hook=unique))
    except (ValueError, TypeError):
        return None
