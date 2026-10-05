"""Closed map-only normal-exit SDK inputs and production wire encoding.

No caller may supply widget paths, native addresses, skip-save policy, claims,
process identity or connection binding. Driver injection owns all wire bindings.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import struct
try:
    from .normal_exit_process_observer_v1 import RetainedProcessIdentity
except ImportError:
    from normal_exit_process_observer_v1 import RetainedProcessIdentity

NORMAL_EXIT_MAP_CAPABILITY = 'normal-exit-map-v1'
NORMAL_EXIT_MAP_STEP = 'normal-exit-map-v1'
MAP_EXIT_ACTIONS = ('prepare_confirmation', 'continue_preparation', 'confirm_desktop')
SIGNATURE_PATTERN = r'^[0-9a-f]{64}$'
QUERY_INPUT_SCHEMA = {
    'type': 'object', 'properties': {'expected_revision': {'type': 'integer', 'minimum': 1}},
    'required': ['expected_revision'], 'additionalProperties': False,
}
REQUEST_INPUT_SCHEMA = {
    'type': 'object',
    'properties': {
        'action': {'type': 'string', 'enum': list(MAP_EXIT_ACTIONS)},
        'expected_revision': {'type': 'integer', 'minimum': 1},
        'expected_exit_context_signature': {'type': 'string', 'pattern': SIGNATURE_PATTERN},
    },
    'required': ['action', 'expected_revision', 'expected_exit_context_signature'],
    'additionalProperties': False,
}


def positive_integer(value: object, name: str, maximum: int = 0xFFFFFFFFFFFFFFFF) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f'{name} requires a positive exact integer')
    return value


def ascii_identity(value: object, name: str) -> str:
    if type(value) is not str or not 1 <= len(value) <= 128 or not value.isascii():
        raise ValueError(f'{name} requires 1..128 ASCII characters')
    if re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', value) is None:
        raise ValueError(f'{name} requires ASCII [A-Za-z0-9_.:-]')
    return value


def exit_signature(value: object) -> str:
    if type(value) is not str or re.fullmatch(SIGNATURE_PATTERN, value) is None:
        raise ValueError('expected_exit_context_signature requires 64 lowercase hexadecimal characters')
    return value


def normalize_query_arguments(arguments: dict) -> dict:
    if type(arguments) is not dict or set(arguments) != {'expected_revision'}:
        raise ValueError('closed query input requires exactly expected_revision')
    return {'expected_revision': positive_integer(arguments['expected_revision'], 'expected_revision')}


def normalize_request_arguments(arguments: dict) -> dict:
    if type(arguments) is not dict or set(arguments) != {
            'action', 'expected_revision', 'expected_exit_context_signature'}:
        raise ValueError('closed request input requires action, expected_revision and expected_exit_context_signature')
    action = arguments['action']
    if type(action) is not str or action not in MAP_EXIT_ACTIONS:
        raise ValueError('only map prepare_confirmation, continue_preparation and confirm_desktop are supported')
    return {'action': action,
            'expected_revision': positive_integer(arguments['expected_revision'], 'expected_revision'),
            'expected_exit_context_signature': exit_signature(arguments['expected_exit_context_signature'])}


@dataclass(frozen=True)
class ExitWireBinding:
    expected_revision: int
    expected_player_character_id: int
    expected_game_pid: int
    expected_connection_generation: int
    expected_process_creation_filetime_100ns: int
    source_inventory_sha256: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if name == 'source_inventory_sha256':
                exit_signature(getattr(self, name))
                continue
            maximum = (0xFFFFFFFF if name == 'expected_game_pid' else
                       0x7FFFFFFF if name == 'expected_player_character_id' else 0xFFFFFFFFFFFFFFFF)
            positive_integer(getattr(self, name), name, maximum)


def build_normal_exit_map_request(*, request_id: str, action: str,
                                  binding: ExitWireBinding, request_nonce: str,
                                  expected_exit_context_signature: str | None = None) -> dict:
    if type(binding) is not ExitWireBinding:
        raise ValueError('trusted typed exit binding required')
    if type(action) is not str or action not in ('query_context', *MAP_EXIT_ACTIONS):
        raise ValueError('closed map exit wire action required')
    if action == 'query_context':
        if expected_exit_context_signature is not None:
            raise ValueError('query cannot carry an exit context signature')
    else:
        exit_signature(expected_exit_context_signature)
    request = {
        'type': 'execute_step', 'protocol_version': 1,
        'request_id': ascii_identity(request_id, 'request_id'), 'step': NORMAL_EXIT_MAP_STEP,
        'action': action, **{name: getattr(binding, name) for name in binding.__dataclass_fields__},
        'request_nonce': ascii_identity(request_nonce, 'request_nonce'),
    }
    if expected_exit_context_signature is not None:
        request['expected_exit_context_signature'] = expected_exit_context_signature
    return request


def encode_normal_exit_map_request(**arguments: object) -> bytes:
    """The exact encoder used by the driver and offline native-parser interop."""
    request = build_normal_exit_map_request(**arguments)
    return json.dumps(request, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def encode_normal_exit_map_packet(**arguments: object) -> bytes:
    payload = encode_normal_exit_map_request(**arguments)
    return struct.pack('<I', len(payload)) + payload


NATIVE_OBSERVATION_KEYS = {
    'schema', 'step', 'action', 'status', 'native_revision', 'connection_generation',
    'game_pid', 'played_character_id', 'process_creation_filetime_100ns', 'pump_epoch',
    'exact_build_verified', 'owner_verified', 'process_identity_verified',
    'source_abi_pins_verified', 'stock_files_verified', 'loaded_source_binding_verified',
    'frame_verified', 'context_signature_verified', 'confirmation_visible',
    'orderly_exit_verified', 'autosave_verified', 'exit_context_signature', 'reason',
    'targets', 'dispatches', 'stage_consumed',
}
NATIVE_PROOF_KEYS = (
    'exact_build_verified', 'owner_verified', 'process_identity_verified',
    'source_abi_pins_verified', 'stock_files_verified', 'loaded_source_binding_verified',
    'frame_verified',
)
TARGET_BOOLEAN_KEYS = {
    'read_complete', 'root_exists', 'root_visible', 'target_exists', 'target_visible',
    'target_enabled', 'unique_target', 'dispatch_admitted',
}
DISPATCH_BOOLEAN_KEYS = {
    'claim_latched', 'dispatch_invoked', 'native_handled', 'post_read_complete', 'postcondition_observed',
}


def continue_preparation_context_ready_v1(native: object) -> bool:
    """Only a fresh owner-observed remaining stage may authorize continuation.

    This reads actual backend progress and targets; the earlier preparation
    claim remains consumed even when its delivery result was unknown.
    """
    if (type(native) is not dict or native.get('action') != 'query_context'
            or native.get('status') != 'context_observed'
            or native.get('confirmation_visible') is not False
            or any(native.get(key) is not True for key in NATIVE_PROOF_KEYS)
            or type(native.get('pump_epoch')) is not int or native['pump_epoch'] <= 0):
        return False
    consumed = native.get('stage_consumed')
    if (type(consumed) is not list or len(consumed) != 3
            or any(type(value) is not bool for value in consumed)
            or consumed != [True, False, False]):
        return False
    targets = native.get('targets')
    if (type(targets) is not list or len(targets) != 3
            or any(type(target) is not dict or target.get('read_complete') is not True
                   for target in targets)
            or targets[2].get('root_visible') is not False):
        return False
    target = targets[1]
    return (all(target.get(key) is True for key in TARGET_BOOLEAN_KEYS)
            and type(target.get('target_vtable_rva')) is int
            and target['target_vtable_rva'] > 0)


def normalize_native_exit_observation(raw: object, binding: ExitWireBinding, action: str) -> dict:
    if type(raw) is not dict or set(raw) != NATIVE_OBSERVATION_KEYS:
        raise ValueError('normal-exit native observation has unrecognized or missing fields')
    if (raw['schema'] != 'ck3-normal-exit-map-v1' or raw['step'] != NORMAL_EXIT_MAP_STEP
            or raw['action'] != action or raw['status'] not in {
                'unavailable', 'context_observed', 'confirmation_observed',
                'dispatch_pending', 'dispatch_unknown_claimed'}):
        raise ValueError('normal-exit native observation identity/status mismatch')
    for key, expected in {
        'native_revision': binding.expected_revision,
        'connection_generation': binding.expected_connection_generation,
        'game_pid': binding.expected_game_pid,
        'played_character_id': binding.expected_player_character_id,
        'process_creation_filetime_100ns': binding.expected_process_creation_filetime_100ns,
    }.items():
        if type(raw[key]) is not int or raw[key] != expected:
            raise ValueError(f'normal-exit native actual {key} differs from submission binding')
    if type(raw['pump_epoch']) is not int or raw['pump_epoch'] < 0:
        raise ValueError('normal-exit actual owner pump epoch is missing')
    for key in (*NATIVE_PROOF_KEYS, 'context_signature_verified', 'confirmation_visible',
                'orderly_exit_verified', 'autosave_verified'):
        if type(raw[key]) is not bool:
            raise ValueError(f'normal-exit native {key} is not a boolean observation')
    if raw['orderly_exit_verified'] or raw['autosave_verified']:
        raise ValueError('native ACK cannot establish orderly process exit or save integrity')
    if type(raw['reason']) is not str:
        raise ValueError('normal-exit native reason is missing')
    if raw['status'] != 'unavailable':
        exit_signature(raw['exit_context_signature'])
        if not all(raw[key] for key in NATIVE_PROOF_KEYS) or raw['pump_epoch'] <= 0:
            raise ValueError('normal-exit available observation lacks actual owner/source/frame proof')
    elif raw['exit_context_signature'] != '':
        exit_signature(raw['exit_context_signature'])
    for group, flags, extras in [('targets', TARGET_BOOLEAN_KEYS, {'target_vtable_rva'}),
                                 ('dispatches', DISPATCH_BOOLEAN_KEYS, set())]:
        if type(raw[group]) is not list or len(raw[group]) != 3:
            raise ValueError(f'normal-exit {group} must contain the three fixed targets')
        for entry in raw[group]:
            if type(entry) is not dict or set(entry) != flags | extras:
                raise ValueError(f'normal-exit {group} closed entry mismatch')
            if any(type(entry[key]) is not bool for key in flags):
                raise ValueError(f'normal-exit {group} requires actual boolean observations')
            if extras and (type(entry['target_vtable_rva']) is not int or entry['target_vtable_rva'] < 0):
                raise ValueError('normal-exit target vtable identity is invalid')
    if (type(raw['stage_consumed']) is not list or len(raw['stage_consumed']) != 3
            or any(type(value) is not bool for value in raw['stage_consumed'])):
        raise ValueError('normal-exit stage_consumed requires three actual boolean observations')
    if action == 'continue_preparation':
        if any(raw['dispatches'][index]['claim_latched'] or raw['dispatches'][index]['dispatch_invoked']
               for index in (0, 2)):
            raise ValueError('normal-exit continuation must never claim or dispatch stage 0 or stage 2')
        if (raw['status'] != 'unavailable' and (raw['stage_consumed'][0] is not True
                or raw['stage_consumed'][2] is not False
                or (raw['dispatches'][1]['claim_latched'] and raw['stage_consumed'][1] is not True))):
            raise ValueError('normal-exit continuation lacks its actual remaining-stage progress')
    if action == 'query_context' and any(entry['claim_latched'] or entry['dispatch_invoked']
                                         for entry in raw['dispatches']):
        raise ValueError('read-only normal-exit query unexpectedly dispatched or claimed')
    if action != 'query_context' and raw['status'] != 'unavailable' and not raw['context_signature_verified']:
        raise ValueError('normal-exit mutation lacks backend context signature verification')
    if raw['status'] == 'confirmation_observed':
        target = raw['targets'][2]
        if action not in {'prepare_confirmation', 'continue_preparation'} or not raw['confirmation_visible'] or not all(
                target[key] for key in TARGET_BOOLEAN_KEYS):
            raise ValueError('normal-exit preparation lacks actual admitted official confirmation readback')
    return dict(raw)


def classify_terminal_exit_receipt(native: dict | None, process: dict, *,
                                    driver_dispatch_receipt_observed_monotonic_ns: int | None,
                                    expected_process_identity: RetainedProcessIdentity) -> dict:
    """Independent process facts; driver receipt time is never native callback time."""
    facts = {'claim_consumed': True, 'retry_authorized': False,
             'process_exit_observed': False,
             'exit_code': None, 'typed_normal_exit_observed': False,
             'autosave_verified': False, 'status': 'dispatch_unknown_claimed'}
    if type(expected_process_identity) is not RetainedProcessIdentity or type(process) is not dict:
        raise ValueError('trusted original retained identity and observed facts required')
    if (type(process.get('pid')) is not int or type(process.get('creation_filetime_100ns')) is not int
            or process.get('pid') != expected_process_identity.pid
            or process.get('creation_filetime_100ns') != expected_process_identity.creation_filetime_100ns
            or type(process.get('retained_handle_token')) is not str
            or process.get('retained_handle_token') != expected_process_identity.retained_handle_token
            or process.get('process_identity_verified') is not True):
        facts['status'] = 'original_retained_handle_identity_mismatch'
        return facts
    receipt = driver_dispatch_receipt_observed_monotonic_ns
    after = process.get('observed_monotonic_ns')
    qualified = (type(native) is dict and native.get('action') == 'confirm_desktop'
                 and native.get('status') == 'dispatch_pending'
                 and all(native.get(key) is True for key in NATIVE_PROOF_KEYS)
                 and native.get('context_signature_verified') is True
                 and native['dispatches'][2]['claim_latched'] is True
                 and native['dispatches'][2]['dispatch_invoked'] is True
                 and native['dispatches'][2]['native_handled'] is True
                 and type(receipt) is int and type(after) is int and after >= receipt
                 and process.get('observation_clock_domain') == 'driver_monotonic_v1'
                 and process.get('pid') == native.get('game_pid')
                 and process.get('creation_filetime_100ns') == native.get('process_creation_filetime_100ns'))
    code = process.get('exit_code')
    if (process.get('wait_state') == 'signaled' and type(process.get('wait_result')) is int
            and process['wait_result'] == 0 and type(code) is int and 0 <= code <= 0xFFFFFFFF):
        facts['process_exit_observed'] = True
        facts['exit_code'] = code
        facts['status'] = 'process_exit_observed_zero' if process['exit_code'] == 0 else 'process_exit_observed_nonzero'
        facts['typed_normal_exit_observed'] = qualified and process['exit_code'] == 0
    elif qualified:
        facts['status'] = 'dispatch_pending' if process.get('wait_state') == 'timeout' else 'observation_failed_unknown'
    return facts


def normalize_public_exit_result(result: object, *, action: str,
                                 expected_revision: int) -> dict:
    """Validate the selected backend's typed result without live post-exit reads."""
    if type(result) is not dict or result.get('public_revision') != expected_revision:
        raise ValueError('normal-exit backend result lacks its public revision binding')
    if type(result.get('public_revision')) is not int:
        raise ValueError('normal-exit backend revision is not an exact integer')
    if result.get('retry_authorized') is not False or result.get('autosave_verified') is not False:
        raise ValueError('normal-exit backend cannot grant retries or save integrity from dispatch')
    if type(result.get('claim_consumed')) is not bool:
        raise ValueError('normal-exit backend lacks a typed claim observation')
    exit_signature(result.get('source_inventory_sha256'))
    positive_integer(result.get('process_creation_filetime_100ns'), 'actual process creation FILETIME')
    native = result.get('native_observation')
    if action == 'query_context':
        if (result.get('schema') != 'ck3-normal-exit-context-result-v1'
                or result.get('claim_consumed') is not False
                or result.get('orderly_exit_verified') is not False or type(native) is not dict):
            raise ValueError('normal-exit backend query is not a read-only context observation')
    else:
        if (result.get('schema') != 'ck3-normal-exit-request-result-v1'
                or result.get('action') != action or result.get('claim_consumed') is not True
                or type(result.get('typed_normal_exit_observed')) is not bool
                or type(result.get('process_exit_observed')) is not bool):
            raise ValueError('normal-exit backend request is not a typed consumed-phase result')
        if action in {'prepare_confirmation', 'continue_preparation'} and (result['typed_normal_exit_observed'] or result['process_exit_observed']):
            raise ValueError('normal-exit preparation cannot establish a process exit')
        if action == 'confirm_desktop' and result.get('snapshot_after_required') is not False:
            raise ValueError('terminal normal-exit backend must preserve handle facts without a final live snapshot')
        if native is None and result['typed_normal_exit_observed']:
            raise ValueError('unknown normal-exit dispatch cannot establish semantic route success')
    identity = None
    if action == 'confirm_desktop':
        pin = result.get('process_preconfirm_pin')
        if type(pin) is not dict:
            raise ValueError('original retained preconfirm pin is missing')
        identity = RetainedProcessIdentity(pin.get('pid'), pin.get('creation_filetime_100ns'),
                                           pin.get('retained_handle_token'))
        if identity.creation_filetime_100ns != result['process_creation_filetime_100ns']:
            raise ValueError('terminal result differs from its original process creation pin')
    if native is not None:
        if type(native) is not dict:
            raise ValueError('normal-exit backend native observation is not typed')
        binding = ExitWireBinding(native.get('native_revision'), native.get('played_character_id'),
                                  identity.pid if identity is not None else native.get('game_pid'),
                                  native.get('connection_generation'),
                                  result['process_creation_filetime_100ns'], result['source_inventory_sha256'])
        normalize_native_exit_observation(native, binding, action)
        if action == 'query_context' and result.get('exit_context_signature') != native['exit_context_signature']:
            raise ValueError('normal-exit backend replaced its actual native context signature')
    if identity is not None:
        facts = classify_terminal_exit_receipt(native, result.get('process_observation'),
            driver_dispatch_receipt_observed_monotonic_ns=result.get('driver_dispatch_receipt_observed_monotonic_ns'),
            expected_process_identity=identity)
        if any(result.get(key) != value or type(result.get(key)) is not type(value)
               for key, value in facts.items()):
            raise ValueError('terminal exit result differs from its actual same-handle facts')
    return result


def normalize_public_exit_observation_result(result: object) -> dict:
    if (type(result) is not dict or result.get('schema') != 'ck3-normal-exit-process-observation-result-v1'
            or result.get('action') != 'confirm_desktop' or result.get('claim_consumed') is not True
            or result.get('retry_authorized') is not False or result.get('autosave_verified') is not False
            or result.get('snapshot_after_required') is not False
            or result.get('native_submission_count') != 0
            or type(result.get('native_submission_count')) is not int
            or type(result.get('observer_retained')) is not bool
            or type(result.get('typed_normal_exit_observed')) is not bool
            or type(result.get('process_exit_observed')) is not bool):
        raise ValueError('backend result is not a typed read-only original-process observation')
    positive_integer(result.get('public_revision'),'original public revision')
    exit_signature(result.get('source_inventory_sha256'))
    pin=result.get('process_preconfirm_pin')
    if type(pin) is not dict:
        raise ValueError('original retained preconfirm pin is missing')
    identity=RetainedProcessIdentity(pin.get('pid'),pin.get('creation_filetime_100ns'),pin.get('retained_handle_token'))
    native=result.get('native_observation')
    if native is not None:
        binding=ExitWireBinding(native.get('native_revision'),native.get('played_character_id'),
            identity.pid,native.get('connection_generation'),identity.creation_filetime_100ns,
            result['source_inventory_sha256'])
        normalize_native_exit_observation(native,binding,'confirm_desktop')
    facts=classify_terminal_exit_receipt(native,result.get('process_observation'),
        driver_dispatch_receipt_observed_monotonic_ns=result.get('driver_dispatch_receipt_observed_monotonic_ns'),
        expected_process_identity=identity)
    if any(result.get(key)!=value or type(result.get(key)) is not type(value) for key,value in facts.items()):
        raise ValueError('read-only exit result differs from its actual same-handle facts')
    return result
