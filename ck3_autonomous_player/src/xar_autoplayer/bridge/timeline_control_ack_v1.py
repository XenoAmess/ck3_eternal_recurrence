"""Strictly retain a native pause/resume ACK's original protocol request ID.

The binding is diagnostic only. Existing accepted/status and state checks remain
owned by the driver; an ACK does not establish observed execution or completion.
"""
from __future__ import annotations

from typing import TypedDict
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import re
from .version_identity import CK3_1210, FlorinFullSource

FLORIN_CLOCK_CAPABILITY = 'game.command.full-snapshot-clock-control.v1'
FLORIN_CLOCK_STEPS = frozenset({'pause-map', 'resume-map', 'set-speed-1', 'set-speed-2',
    'set-speed-3', 'set-speed-4', 'set-speed-5', 'save-checkpoint'})
FLORIN_DATE_ARM_PREFIX = 'research-arm-tactical-daily-sentinel-v1-'


@dataclass(frozen=True)
class FlorinDateArmSpecV1:
    starting_date_raw: int
    target_date_raw: int
    speed: int


def florin_date_arm_spec_v1(step: str) -> FlorinDateArmSpecV1:
    match = re.fullmatch(FLORIN_DATE_ARM_PREFIX + r'([1-9][0-9]*)-to-([1-9][0-9]*)-speed-([1-5])-mode-terminal-a-0', step)
    if match is None:
        raise ValueError('Florin Date ARM requires the canonical terminal-a-0 step')
    start, target, speed = map(int, match.groups())
    if not (start < target < 2**31 and 24 <= target-start <= 31*24 and (target-start) % 24 == 0):
        raise ValueError('Florin Date ARM requires a bounded 1..31 whole-day window')
    return FlorinDateArmSpecV1(start, target, speed)


def florin_control_fields_v1(source: FlorinFullSource, *, deadline_unix_ms: int, date_arm: bool) -> dict[str, object]:
    if type(deadline_unix_ms) is not int or not 0 < deadline_unix_ms < 2**64:
        raise ValueError('Florin control requires its original positive deadline')
    schema = 'ck3_1210_date_sentinel_arm_v1' if date_arm else 'ck3_1210_full_clock_control_v1'
    return {'date_sentinel_arm' if date_arm else 'full_snapshot_clock_control': {
        'schema': schema, 'game_version': CK3_1210.game_version, 'executable_sha256': CK3_1210.executable_sha256,
        'adapter_id': 'ck3-1.21.0-msvc-x64', 'backend': 'ck3-1.21.0-native-headless-main-thread',
        'snapshot_id': source.snapshot_id, 'native_revision': source.native_revision,
        'deadline_unix_ms': deadline_unix_ms}}


def _control_directory(state_path: Path, source: FlorinFullSource) -> Path:
    return state_path.parent / 'world-control1210' / f'{source.game_pid}-{source.scope_sha256}'


def _preserve(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, sort_keys=True, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def require_florin_control_ready_v1(state_path: Path, source: FlorinFullSource) -> None:
    directory = _control_directory(state_path, source)
    for claim in directory.glob('*.claim.json'):
        qualified = claim.with_name(claim.name.removesuffix('.claim.json') + '.qualified.json')
        if not qualified.exists():
            raise ValueError('Florin world control has an original pending or UNKNOWN action; replay is forbidden')
        original = json.loads(claim.read_text(encoding='utf-8'))
        receipt = json.loads(qualified.read_text(encoding='utf-8'))
        if (type(original) is not dict or type(receipt) is not dict
                or set(receipt) != {'schema','request_id','frame','physical_save_confirmed'}
                or receipt['schema'] != 'ck3-florin-world-control-ack-qualified-v1'
                or receipt['physical_save_confirmed'] is not False
                or type(original.get('request_id')) is not str or receipt['request_id'] != original['request_id']
                or _field(receipt['frame'], 'request_id') != original['request_id']):
            raise ValueError('Florin original control acknowledgement qualification differs')


def claim_florin_control_v1(state_path: Path, source: FlorinFullSource, *, request_id: str,
        step: str, request: dict[str, object]) -> Path:
    require_florin_control_ready_v1(state_path, source)
    identity = {'game_pid': source.game_pid, 'scope_sha256': source.scope_sha256,
        'native_revision': source.native_revision, 'step': step}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path = _control_directory(state_path, source) / (key + '.claim.json')
    _preserve(path, {'schema': 'ck3-florin-world-control-once-v1', 'identity': identity,
        'request_id': request_id, 'connection_generation': source.connection_generation,
        'request': request, 'status': 'claimed_result_unknown_no_retry'})
    return path


def qualify_florin_control_claim_v1(claim: Path, *, request_id: str, frame: dict[str, object]) -> None:
    _preserve(claim.with_name(claim.name.removesuffix('.claim.json') + '.qualified.json'), {
        'schema': 'ck3-florin-world-control-ack-qualified-v1', 'request_id': request_id,
        'frame': frame, 'physical_save_confirmed': False})


def preserve_florin_control_result_v1(claim: Path, frame: dict[str, object]) -> None:
    _preserve(claim.with_name(claim.name.removesuffix('.claim.json') + '.response.json'), frame)


def mark_florin_control_unknown_v1(state_path: Path, source: FlorinFullSource, *, request_id: str,
        step: str, reason: str) -> None:
    key = hashlib.sha256(request_id.encode()).hexdigest()
    path = _control_directory(state_path, source) / (key + '.claim.json')
    if not path.exists():
        _preserve(path, {'schema': 'ck3-florin-world-control-unknown-v1', 'request_id': request_id,
            'step': step, 'reason': reason, 'connection_generation': source.connection_generation})


def normalize_florin_clock_ack_v1(frame: object, *, expected_step: str,
        expected_request_id: str) -> dict[str, object]:
    """Exact current Native ACK DATA; submission never proves advancement or SAVE."""
    if expected_step not in FLORIN_CLOCK_STEPS and not expected_step.startswith(FLORIN_DATE_ARM_PREFIX):
        raise ValueError('fixed Florin clock operation required')
    if (_field(frame, 'type') != 'command_result' or type(_field(frame, 'protocol_version')) is not int
            or _field(frame, 'protocol_version') != 1 or _field(frame, 'request_id') != expected_request_id):
        raise ValueError('Florin clock ACK differs from its original envelope')
    raw = _field(frame, 'result')
    if type(raw) is not dict:
        raise ValueError('Florin clock ACK result must be an object')
    fields = {'schema','game_version','executable_sha256','adapter_id','backend','step','accepted',
        'queue_status','effect_attempted','full_snapshot_before_verified','complete_snapshot','physical_save_confirmed'}
    status = _field(raw, 'queue_status')
    if expected_step == 'save-checkpoint':
        fields.add('save_name')
        if status == 'submitted': fields.update({'status','submission'})
    if set(raw) != fields:
        raise ValueError('Florin clock ACK contains unknown or missing fields')
    if (raw['schema'] != 'ck3_1210_full_clock_control_result_v1' or raw['game_version'] != CK3_1210.game_version
            or not isinstance(raw['executable_sha256'], str) or raw['executable_sha256'].upper() != CK3_1210.executable_sha256
            or raw['adapter_id'] != 'ck3-1.21.0-msvc-x64' or raw['backend'] != 'ck3-1.21.0-native-headless-main-thread'
            or raw['step'] != expected_step):
        raise ValueError('Florin clock ACK exact source tuple differs')
    if any(type(raw[k]) is not bool for k in ('accepted','effect_attempted','full_snapshot_before_verified',
            'complete_snapshot','physical_save_confirmed')) or type(_field(frame, 'ok')) is not bool:
        raise ValueError('Florin clock ACK requires actual boolean flags')
    if raw['complete_snapshot'] is not False or raw['physical_save_confirmed'] is not False:
        raise ValueError('Florin clock ACK cannot claim a Full read or physical SAVE')
    if expected_step.startswith(FLORIN_DATE_ARM_PREFIX):
        florin_date_arm_spec_v1(expected_step)
        if raw['accepted'] is not False or _field(frame, 'ok') is not False:
            raise ValueError('Florin Date ARM full-clock schema is a negative ACK only')
    statuses = {'submitted','already_satisfied','unavailable','expired','stale_core_prefix','stale_full_snapshot',
        'requires_map','requires_paused','rejected','indeterminate'}
    if (not isinstance(status, str) or status not in statuses or raw['accepted'] != _field(frame, 'ok')
            or raw['accepted'] != (status in {'submitted','already_satisfied'})):
        raise ValueError('Florin clock ACK status/acceptance differs')
    zero = not raw['accepted'] and not raw['effect_attempted'] and status != 'indeterminate'
    envelope_fields = {'type','protocol_version','request_id','ok','result'} | ({'error'} if zero else set())
    if type(frame) is not dict or set(frame) != envelope_fields or (zero and _field(frame, 'error') != 'full_clock_'+status):
        raise ValueError('Florin clock ACK error/envelope differs')
    if status == 'submitted' and (raw['effect_attempted'] is not True or raw['full_snapshot_before_verified'] is not True):
        raise ValueError('Florin clock submission lacks Full verification or actual effect entry')
    if expected_step == 'save-checkpoint':
        if raw['save_name'] != 'xar_checkpoint': raise ValueError('fixed SAVE basename differs')
        if status == 'submitted':
            sub = raw['submission']
            if (raw['status'] != 'submitted' or type(sub) is not dict or set(sub) != {'sequence','requested_save_name','date_raw'}
                    or type(sub['sequence']) is not int or not 0 < sub['sequence'] < 2**64
                    or sub['requested_save_name'] != 'xar_checkpoint' or type(sub['date_raw']) is not int
                    or not -(2**31) <= sub['date_raw'] < 2**31):
                raise ValueError('Florin SAVE submission identity differs')
    return {key: raw[key] for key in fields}


class TimelineControlAckBindingV1(TypedDict):
    native_request_id: str


def _field(source: object, key: str) -> object:
    # JSON values leave this untrusted boundary as object, never unchecked Any.
    if type(source) is dict:
        value: object = source.get(key)
        return value
    return None


def normalize_timeline_control_ack_v1(
    frame: object, *, expected_step: str, expected_request_id: str,
) -> TimelineControlAckBindingV1:
    """Bind the success envelope without reinterpreting its action result."""
    if type(expected_request_id) is not str or not expected_request_id:
        raise ValueError("timeline control expected request_id must be a non-empty string")
    if type(expected_step) is not str or expected_step not in {"pause-map", "resume-map"}:
        raise ValueError("timeline control ACK requires pause-map or resume-map")
    protocol = _field(frame, "protocol_version")
    request_id = _field(frame, "request_id")
    frame_type = _field(frame, "type")
    if (type(frame) is not dict or type(frame_type) is not str or frame_type != "command_result"
            or type(protocol) is not int or protocol != 1
            or type(request_id) is not str or request_id != expected_request_id
            or _field(frame, "ok") is not True):
        raise ValueError("timeline control ACK envelope does not match its original request")
    result = _field(frame, "result")
    step = _field(result, "step")
    if (type(result) is not dict or type(step) is not str or step != expected_step
            or "request_id" in result or "native_request_id" in result):
        raise ValueError("timeline control ACK result has invalid step or identity aliases")
    return TimelineControlAckBindingV1(native_request_id=request_id)
