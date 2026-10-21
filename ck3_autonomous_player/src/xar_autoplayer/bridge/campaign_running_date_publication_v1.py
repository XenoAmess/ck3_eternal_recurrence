"""Classify one unqualified running clock-publication gap for bounded observation.

This does not admit a frame or repair it. The caller must subsequently pass its
unchanged complete-frame and successor guards before any pause or business use.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IdentityV1 = tuple[int, int, int, int, int, str, int, None]
DirectionV1 = Literal['mailbox-ahead', 'snapshot-ahead']
ERROR = 'campaign pause readback lost the complete same-owner frame'
SCHEMA = 'ck3-campaign-pause-same-owner-frame-diagnostic-v1'
DATE_CONDITION = 'mailbox["date_raw"] != snapshot["date_raw"]'


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError('Object required at running-publication boundary')
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError('Running-publication object keys must be strings')
        result[key] = item
    return result


def _integer(value: object, low: int = 0, high: int = 2**64 - 1) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Strict bounded integer required; bool/float rejected')
    return value


def _identity(value: object) -> IdentityV1:
    if not isinstance(value, (tuple, list)) or len(value) != 8:
        raise ValueError('Original complete owner binding required')
    if type(value[5]) is not str or not value[5] or '\0' in value[5] or value[7] is not None:
        raise ValueError('Original native pipe and interaction-free binding required')
    return (_integer(value[0], 1, 2**32 - 1), _integer(value[1], 1),
            _integer(value[2], 1, 2**31 - 1), _integer(value[3], 0, 2**31 - 1),
            _integer(value[4], 1, 5), value[5], _integer(value[6], 1, 2**32 - 1), None)


@dataclass(frozen=True)
class PendingRunningDateV1:
    identity: IdentityV1
    date_raw: int
    revision: int
    native_revision: int
    pump: int
    rejections: int
    mailbox_date_raw: int
    direction: DirectionV1

    def to_host_binding(self) -> dict[str, object]:
        """One explicit adapter to the existing in-memory host binding contract."""
        return {'identity': self.identity, 'date': self.date_raw, 'revision': self.revision,
                'native_revision': self.native_revision, 'pump': self.pump,
                'rejections': self.rejections, 'pause_transition': False,
                'pending_mailbox_date': self.mailbox_date_raw}


def pending_running_date_v1(source: object, snapshot: object, error: object) -> PendingRunningDateV1:
    """Recognize only a sole date mismatch of exactly 24h, preserving both clocks.

All failures re-raise the original guard exception. This authorizes readonly
observation under the caller's original deadline, never mutation or admission.
"""
    if type(error) is not RuntimeError:
        raise ValueError('Actual original RuntimeError required')
    try:
        if str(error) != ERROR:
            raise ValueError('Different original guard error')
        detail = _object(getattr(error, 'ck3_campaign_pause_frame_diagnostic', None))
        conditions = detail.get('conditions')
        if (detail.get('schema') != SCHEMA or type(detail.get('first_failed_condition')) is not int
                or detail['first_failed_condition'] != 31 or type(conditions) is not list or len(conditions) != 32):
            raise ValueError('Exact original 32-condition diagnostic required')
        failed: list[int] = []
        for index, value in enumerate(conditions):
            condition = _object(value)
            if (set(condition) != {'index', 'source', 'failed', 'unavailable_reason'}
                    or type(condition.get('index')) is not int or condition['index'] != index
                    or type(condition.get('source')) is not str or not condition['source']
                    or type(condition.get('failed')) is not bool or condition['unavailable_reason'] is not None):
                raise ValueError('Exact evaluated original predicate required')
            if condition['failed'] is True:
                failed.append(index)
        if failed != [31] or _object(conditions[31]).get('source') != DATE_CONDITION:
            raise ValueError('Only the original clock equality may be false')
        before, frame = _object(source), _object(snapshot)
        source_fields = {'identity', 'date', 'revision', 'native_revision', 'pump', 'rejections', 'pause_transition'}
        if set(before) not in (source_fields, source_fields | {'pending_mailbox_date'}) or before['pause_transition'] is not False:
            raise ValueError('Exact complete or pending original source binding required')
        diagnostics, played = _object(frame.get('diagnostics')), _object(frame.get('played_character'))
        mailbox = _object(_object(diagnostics.get('last_heartbeat')).get('main_thread_query_mailbox_v1'))
        hello = _object(diagnostics.get('hello'))
        snapshot_date = _integer(frame.get('date_raw'), 1, 2**31 - 1)
        mailbox_date = _integer(mailbox.get('date_raw'), 1, 2**31 - 1)
        if (frame.get('paused') is not False or frame.get('active_event') is not None
                or frame.get('pending_character_interaction') is not None
                or mailbox.get('ready') is not False or mailbox.get('paused') is not False
                or mailbox.get('application_main_observed') is not True
                or mailbox.get('paused_main_thread_observed') is not False
                or mailbox.get('stamp_read_success') is not True
                or abs(mailbox_date - snapshot_date) != 24):
            raise ValueError('Exact interaction-free running one-day publication gap required')
        identity = _identity((diagnostics.get('bridge_pid'), diagnostics.get('connection_generation'),
                              played.get('character_id'), frame.get('local_player_id'), frame.get('speed'),
                              diagnostics.get('pipe_name'), mailbox.get('owner_tid'), frame.get('pending_character_interaction')))
        if (identity != _identity(before.get('identity')) or identity[4] != 1
                or _integer(hello.get('pid'), 1, 2**32 - 1) != identity[0]
                or _integer(hello.get('connection_generation'), 1) != identity[1]
                or _integer(mailbox.get('current_tid'), 1, 2**32 - 1) != identity[6]):
            raise ValueError('Original actual owner changed')
        revision = _integer(frame.get('revision'), 1)
        native_revision = _integer(frame.get('native_revision'), 1)
        pump = _integer(mailbox.get('owner_verified_pump_epochs'), 1)
        rejections = _integer(diagnostics.get('rejected_state_snapshot_count'))
        for key, current in (('date', snapshot_date), ('revision', revision), ('native_revision', native_revision), ('pump', pump)):
            if current < _integer(before.get(key), 1):
                raise ValueError('Original running clock/revision/pump regressed')
        previous_mailbox = before.get('pending_mailbox_date', before.get('date'))
        if mailbox_date < _integer(previous_mailbox, 1, 2**31 - 1) or rejections != _integer(before.get('rejections')):
            raise ValueError('Observed mailbox clock regressed or rejection count changed')
        direction: DirectionV1 = 'mailbox-ahead' if mailbox_date > snapshot_date else 'snapshot-ahead'
        return PendingRunningDateV1(identity, snapshot_date, revision, native_revision, pump, rejections, mailbox_date, direction)
    except (KeyError, TypeError, ValueError):
        raise error
