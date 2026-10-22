"""Lossless public normal-exit JSON; the native and service V1 models stay integer.

Only the enumerated uint64 paths change representation. All remaining JSON
integers must be safe, exact integers; unknown fields cannot smuggle a large
number through a JavaScript Number. Validation reuses the original semantic
receipt validator after decoding, without observing or dispatching anything.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from .normal_exit_contract_v1 import (
    normalize_public_exit_observation_result, normalize_public_exit_result,
)

UINT64_MAX = 2**64 - 1
SAFE_INTEGER_MAX = 2**53 - 1
ExitAction = Literal['query_context', 'prepare_confirmation', 'continue_preparation',
                     'disable_exit_autosave', 'confirm_desktop']
_SCHEMAS = {
    'ck3-normal-exit-context-result-v1': 'ck3-normal-exit-context-result-v2',
    'ck3-normal-exit-request-result-v1': 'ck3-normal-exit-request-result-v2',
    'ck3-normal-exit-process-observation-result-v1':
        'ck3-normal-exit-process-observation-result-v2',
}
_TOP_FIELDS = frozenset({
    'schema', 'action', 'status', 'public_revision', 'native_observation',
    'exit_context_signature', 'source_inventory_sha256',
    'process_creation_filetime_100ns', 'claim_consumed', 'retry_authorized',
    'orderly_exit_verified', 'autosave_verified', 'process_observation',
    'process_preconfirm_pin', 'driver_dispatch_receipt_observed_monotonic_ns',
    'receipt_clock_meaning', 'snapshot_after_required', 'reason',
    'observer_retained', 'confirmation_observed', 'exit_autosave_disabled_observed',
    'process_exit_observed', 'typed_normal_exit_observed', 'exit_code',
    'request_id', 'claim_path', 'uses_desktop_input', 'uses_ocr',
    'native_submission_count', 'observer_close_receipt_path',
    'observer_close_receipt_error', 'receipt_path',
})
_PIN_FIELDS = frozenset({'pid', 'creation_filetime_100ns', 'retained_handle_token',
                         'wait_result', 'verified_monotonic_ns', 'observation_clock_domain'})
_PROCESS_FIELDS = frozenset({'pid', 'creation_filetime_100ns', 'retained_handle_token',
    'wait_result', 'wait_state', 'exit_code', 'process_identity_verified',
    'process_exit_observed', 'observed_monotonic_ns', 'timeout_ms',
    'observation_deadline_reached', 'observation_clock_domain', 'errors'})


def parse_normal_exit_public_revision_v2(value: object) -> int:
    """The public revision input is exclusively a canonical decimal string."""
    return _decimal(value, 'expected_revision', minimum=1)


def validate_normal_exit_public_revision_v2(value: object) -> str:
    """Pydantic's input validator preserves the public string representation."""
    return str(parse_normal_exit_public_revision_v2(value))


def normal_exit_public_revision_from_snapshot_v2(value: object) -> str:
    """Encode the host's exact integer snapshot revision at the public boundary."""
    return str(_integer(value, 'snapshot revision', minimum=1))


def is_normal_exit_terminal_plan_result_v2(tool: object, arguments: object,
                                         result: object) -> bool:
    """Recognize a validated terminal receipt without requiring a live snapshot.

    A pending retained-process observation also forbids a new game snapshot.
    The receipt's actual exit flags remain authoritative; this grants no exit
    success or permission to retry a consumed confirmation.
    """
    schemas = {
        'ck3_request_normal_exit_v1': 'ck3-normal-exit-request-result-v2',
        'ck3_observe_normal_exit_v1': 'ck3-normal-exit-process-observation-result-v2',
    }
    if (not isinstance(tool, str) or tool not in schemas
            or not isinstance(result, dict) or result.get('schema') != schemas[tool]):
        return False
    parsed = parse_normal_exit_public_result_v2(result)
    if parsed.action != 'confirm_desktop' or result.get('snapshot_after_required') is not False:
        return False
    if tool == 'ck3_request_normal_exit_v1':
        return isinstance(arguments, dict) and arguments.get('action') == 'confirm_desktop'
    return isinstance(arguments, dict) and not arguments


def _integer(value: object, name: str, *, minimum: int = 0,
             maximum: int = UINT64_MAX) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise ValueError(f'{name} requires an exact integer in {minimum}..{maximum}')
    return value


def _decimal(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, str) or re.fullmatch(r'0|[1-9][0-9]{0,19}', value) is None:
        raise ValueError(f'{name} requires a canonical uint64 decimal string')
    return _integer(int(value), name, minimum=minimum)


def _object(value: object, name: str) -> dict[str, object]:
    # This is the only dynamic object boundary; keys are checked before copying.
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f'{name} requires a JSON object with string keys')
    result: dict[str, object] = {}
    for key, item in value.items():
        result[key] = item
    return result


def _safe_json(value: object) -> object:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return _integer(value, 'JSON integer', minimum=-SAFE_INTEGER_MAX,
                        maximum=SAFE_INTEGER_MAX)
    if isinstance(value, list):
        return [_safe_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _safe_json(item) for key, item in _object(value, 'JSON').items()}
    raise ValueError('normal-exit JSON rejects floats and non-JSON values')


def _field(row: dict[str, object], key: str, *, encode: bool,
           minimum: int = 0, nullable: bool = False) -> None:
    if key not in row:
        raise ValueError(f'missing normal-exit field: {key}')
    value = row[key]
    if value is None and nullable:
        return
    row[key] = (str(_integer(value, key, minimum=minimum)) if encode else
                _decimal(value, key, minimum=minimum))


def _transform(value: object, *, encode: bool) -> dict[str, object]:
    result = _object(value, 'normal-exit result')
    if set(result) - _TOP_FIELDS:
        raise ValueError('normal-exit result contains unknown public fields')
    required = {'schema', 'status', 'public_revision', 'native_observation',
                'process_creation_filetime_100ns', 'source_inventory_sha256',
                'claim_consumed', 'retry_authorized', 'autosave_verified'}
    if result.get('schema') == 'ck3-normal-exit-context-result-v1':
        required |= {'exit_context_signature', 'orderly_exit_verified'}
    else:
        required |= {'action', 'process_exit_observed', 'typed_normal_exit_observed',
                     'request_id', 'claim_path', 'uses_desktop_input', 'uses_ocr',
                     'native_submission_count'}
        if result.get('action') == 'confirm_desktop':
            required |= {'process_observation', 'process_preconfirm_pin',
                         'driver_dispatch_receipt_observed_monotonic_ns',
                         'snapshot_after_required'}
    if not required <= set(result):
        raise ValueError('normal-exit result is missing required fields')
    if 'native_submission_count' in result:
        _integer(result['native_submission_count'], 'native_submission_count', maximum=1)
    if 'exit_code' in result and result['exit_code'] is not None:
        _integer(result['exit_code'], 'exit_code', maximum=0xFFFFFFFF)
    _field(result, 'public_revision', encode=encode, minimum=1)
    _field(result, 'process_creation_filetime_100ns', encode=encode, minimum=1)
    native_raw = result.get('native_observation')
    if native_raw is not None:
        native = _object(native_raw, 'native_observation')
        expected_schema = 'ck3-normal-exit-map-v1' if encode else 'ck3-normal-exit-map-v2'
        if native.get('schema') != expected_schema:
            raise ValueError('native observation schema differs from its wire representation')
        native['schema'] = 'ck3-normal-exit-map-v2' if encode else 'ck3-normal-exit-map-v1'
        for key in ('native_revision', 'connection_generation', 'process_creation_filetime_100ns'):
            _field(native, key, encode=encode, minimum=1)
        _field(native, 'pump_epoch', encode=encode)
        targets = native.get('targets')
        if not isinstance(targets, list):
            raise ValueError('native targets must be a list')
        projected_targets: list[dict[str, object]] = []
        for target_raw in targets:
            target = _object(target_raw, 'target')
            _field(target, 'target_vtable_rva', encode=encode)
            projected_targets.append(target)
        native['targets'] = projected_targets
        result['native_observation'] = native
    if 'driver_dispatch_receipt_observed_monotonic_ns' in result:
        _field(result, 'driver_dispatch_receipt_observed_monotonic_ns', encode=encode, nullable=True)
    for name, clock in (('process_preconfirm_pin', 'verified_monotonic_ns'),
                        ('process_observation', 'observed_monotonic_ns')):
        if name in result:
            process = _object(result[name], name)
            if set(process) != (_PIN_FIELDS if name == 'process_preconfirm_pin' else _PROCESS_FIELDS):
                raise ValueError(f'{name} has missing or unknown fields')
            _integer(process['pid'], 'process pid', minimum=1, maximum=0xFFFFFFFF)
            _integer(process['wait_result'], 'wait_result', maximum=0xFFFFFFFF)
            if process['observation_clock_domain'] != 'driver_monotonic_v1':
                raise ValueError('process observation has a foreign clock domain')
            if name == 'process_observation':
                _integer(process['timeout_ms'], 'timeout_ms', maximum=5000)
                if process['exit_code'] is not None:
                    _integer(process['exit_code'], 'process exit_code', maximum=0xFFFFFFFF)
                if process['wait_state'] not in ('signaled', 'timeout', 'failed'):
                    raise ValueError('unknown original-process wait state')
                for flag in ('process_identity_verified', 'process_exit_observed',
                             'observation_deadline_reached'):
                    if not isinstance(process[flag], bool):
                        raise ValueError(f'{flag} requires an actual boolean')
                errors = process['errors']
                if not isinstance(errors, list) or any(not isinstance(error, str) for error in errors):
                    raise ValueError('process errors require a list of strings')
            _field(process, 'creation_filetime_100ns', encode=encode, minimum=1)
            _field(process, clock, encode=encode)
            result[name] = process
    # Encoding must prove every remaining number fits the JS exact integer domain.
    # Decoding intentionally keeps the listed uint64 integers for the V1 validator.
    if encode:
        return _object(_safe_json(result), 'encoded result')
    return result


def _semantic(result: dict[str, object]) -> ExitAction:
    for flag in ('uses_desktop_input', 'uses_ocr', 'orderly_exit_verified'):
        if flag in result and result[flag] is not False:
            raise ValueError(f'public normal exit cannot assert {flag}')
    schema = result.get('schema')
    if schema == 'ck3-normal-exit-process-observation-result-v1':
        normalize_public_exit_observation_result(result)
        action: ExitAction = 'confirm_desktop'
    else:
        raw_action = 'query_context' if schema == 'ck3-normal-exit-context-result-v1' else result.get('action')
        if raw_action == 'query_context': action = 'query_context'
        elif raw_action == 'prepare_confirmation': action = 'prepare_confirmation'
        elif raw_action == 'continue_preparation': action = 'continue_preparation'
        elif raw_action == 'disable_exit_autosave': action = 'disable_exit_autosave'
        elif raw_action == 'confirm_desktop': action = 'confirm_desktop'
        else: raise ValueError('unknown normal-exit action')
        normalize_public_exit_result(result, action=action,
            expected_revision=_integer(result.get('public_revision'), 'public_revision', minimum=1))
        if action != 'confirm_desktop':
            native = result.get('native_observation')
            expected_status = (_object(native, 'native_observation').get('status')
                               if native is not None else 'dispatch_unknown_claimed')
            if result.get('status') != expected_status:
                raise ValueError('public status differs from its actual native observation')
    return action


@dataclass(frozen=True)
class NormalExitPublicResultV2:
    """Validated public receipt with exact Python identity and revision values."""
    action: ExitAction
    public_revision: int
    process_creation_filetime_100ns: int
    _memory: dict[str, object]

    def __post_init__(self) -> None:
        if (_semantic(self._memory) != self.action
                or _integer(self.public_revision, 'public_revision', minimum=1) != self._memory.get('public_revision')
                or _integer(self.process_creation_filetime_100ns, 'creation FILETIME', minimum=1)
                    != self._memory.get('process_creation_filetime_100ns')):
            raise ValueError('public result model differs from its validated memory receipt')

    def to_memory(self) -> dict[str, object]:
        """Return a fresh V1 memory object, never a public JSON serialization."""
        return _transform(_transform(self._memory, encode=True), encode=False)

    def to_wire(self) -> dict[str, object]:
        return normal_exit_public_result_v2(self._memory)


def normal_exit_public_result_v2(result: object) -> dict[str, object]:
    """Validate the actual Service result, then project the public V2 schema."""
    memory = _object(result, 'service result')
    _semantic(memory)
    wire = _transform(memory, encode=True)
    schema = memory.get('schema')
    if not isinstance(schema, str) or schema not in _SCHEMAS:
        raise ValueError('unknown service normal-exit schema')
    wire['schema'] = _SCHEMAS[schema]
    return wire


def parse_normal_exit_public_result_v2(value: object, *,
        expected_process_creation_filetime_100ns: int | None = None) -> NormalExitPublicResultV2:
    """Decode only V2 and revalidate the actual retained-process semantics."""
    wire = _object(_safe_json(value), 'public result')
    schema = wire.get('schema')
    reverse = {public: memory for memory, public in _SCHEMAS.items()}
    if not isinstance(schema, str) or schema not in reverse:
        raise ValueError('normal-exit public parser requires a V2 schema')
    wire['schema'] = reverse[schema]
    memory = _transform(wire, encode=False)
    action = _semantic(memory)
    revision = _integer(memory['public_revision'], 'public_revision', minimum=1)
    creation = _integer(memory['process_creation_filetime_100ns'], 'creation FILETIME', minimum=1)
    if expected_process_creation_filetime_100ns is not None:
        expected = _integer(expected_process_creation_filetime_100ns, 'expected creation FILETIME', minimum=1)
        if creation != expected:
            raise ValueError('public exit receipt belongs to a different process birth')
    # Re-encoding proves no unlisted or out-of-range numeric field was accepted.
    _transform(memory, encode=True)
    return NormalExitPublicResultV2(action, revision, creation, memory)
