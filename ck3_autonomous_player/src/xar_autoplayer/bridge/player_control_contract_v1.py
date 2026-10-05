"""Closed stock player-control requests; selection never proves human control.

Inputs contain no callback address, GUI expression, path, flow identifier,
controller record or admission flag. All of those come from the bound backend.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import struct

from .ingame_decisions_open_contract import EXE_SHA256

STEP = 'player-control-v1'
CAPABILITY = 'player-control-v1'
ACTIONS = ('open_pause_menu', 'open_switch', 'choose_character', 'confirm_control')
SIGNATURE_PATTERN = r'^[0-9a-f]{64}$'
U64_MAX = 2**64 - 1

QUERY_INPUT_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {'expected_revision': {'type': 'integer', 'minimum': 1, 'maximum': U64_MAX}},
    'required': ['expected_revision'],
}
REQUEST_INPUT_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'action': {'type': 'string', 'enum': list(ACTIONS)},
        'expected_revision': {'type': 'integer', 'minimum': 1, 'maximum': U64_MAX},
        'expected_control_context_signature': {'type': 'string', 'pattern': SIGNATURE_PATTERN,
                                               'minLength': 64, 'maxLength': 64},
        'candidate_character_id': {'anyOf': [
            {'type': 'integer', 'minimum': 1, 'maximum': U64_MAX - 1}, {'type': 'null'}]},
    },
    'required': ['action', 'expected_revision', 'expected_control_context_signature', 'candidate_character_id'],
}


def integer(value: object, name: str, *, minimum: int = 1, maximum: int = U64_MAX) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} requires a bounded exact integer')
    return value


def character_id(value: object, name: str = 'character_id') -> int:
    value = integer(value, name, maximum=U64_MAX - 1)
    if value == 0xFFFFFFFF:
        raise ValueError(f'{name} is an invalid native character ID')
    return value


def signature(value: object, name: str = 'control_context_signature') -> str:
    if type(value) is not str or re.fullmatch(SIGNATURE_PATTERN, value) is None:
        raise ValueError(f'{name} requires 64 lowercase hexadecimal characters')
    return value


def identity(value: object, name: str) -> str:
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', value) is None:
        raise ValueError(f'{name} requires a bounded ASCII identity')
    return value


def closed(value: object, fields: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f'closed {name} fields mismatch')
    return value


def normalize_query_arguments(arguments: object) -> dict:
    args = closed(arguments, {'expected_revision'}, 'player-control query')
    return {'expected_revision': integer(args['expected_revision'], 'expected_revision')}


def normalize_request_arguments(arguments: object) -> dict:
    args = closed(arguments, {'action', 'expected_revision', 'expected_control_context_signature',
                              'candidate_character_id'}, 'player-control request')
    if type(args['action']) is not str or args['action'] not in ACTIONS:
        raise ValueError('unsupported stock player-control action')
    candidate = args['candidate_character_id']
    if args['action'] in ACTIONS[:2]:
        if candidate is not None: raise ValueError('opening actions require candidate_character_id=null')
    else:
        character_id(candidate, 'candidate_character_id')
    return {'action': args['action'],
            'expected_revision': integer(args['expected_revision'], 'expected_revision'),
            'expected_control_context_signature': signature(args['expected_control_context_signature']),
            'candidate_character_id': candidate}


def snapshot_binding(snapshot: object) -> dict:
    if type(snapshot) is not dict:
        raise ValueError('actual native campaign snapshot required')
    played = snapshot.get('played_character')
    diag = snapshot.get('diagnostics'); hello = diag.get('hello') if type(diag) is dict else None
    if (snapshot.get('episode_projection') != 'native_campaign' or snapshot.get('paused') is not True
            or type(snapshot.get('map_ready')) is not bool or type(played) is not dict
            or played.get('alive') is not True or type(hello) is not dict
            or hello.get('ck3_build_match') is not True
            or hello.get('game_adapter_id') != 'ck3-1.20.0.3-msvc-x64'
            or hello.get('expected_ck3_version') != '1.20.0.3'
            or str(hello.get('expected_ck3_sha256', '')).lower() != EXE_SHA256):
        raise ValueError('stock control requires exact .3 paused native campaign identity')
    return {'native_revision': integer(snapshot.get('native_revision'), 'native_revision'),
            'connection_generation': integer(diag.get('connection_generation'), 'connection_generation'),
            'game_pid': integer(hello.get('pid'), 'game_pid', maximum=2**32-1),
            'played_character_id': character_id(played.get('character_id')),
            'date_raw': integer(snapshot.get('date_raw'), 'date_raw', minimum=0),
            'episode_run_id': identity(snapshot.get('episode_run_id'), 'episode_run_id')}


@dataclass(frozen=True)
class PlayerControlWireBinding:
    expected_revision: int
    expected_player_character_id: int
    expected_game_pid: int
    expected_connection_generation: int
    expected_process_creation_filetime_100ns: int
    source_inventory_sha256: str

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if name == 'source_inventory_sha256': signature(value, name)
            elif name == 'expected_player_character_id': character_id(value, name)
            else: integer(value, name, maximum=2**32-1 if name == 'expected_game_pid' else U64_MAX)


def build_request(*, request_id: str, action: str, binding: PlayerControlWireBinding,
                  request_nonce: str, expected_control_context_signature: str | None = None,
                  candidate_character_id: int | None = None) -> dict:
    if type(binding) is not PlayerControlWireBinding: raise ValueError('trusted typed control binding required')
    if action == 'query_context':
        if expected_control_context_signature is not None or candidate_character_id is not None:
            raise ValueError('read-only query cannot contain signature or candidate')
    else:
        normalize_request_arguments({'action': action, 'expected_revision': binding.expected_revision,
            'expected_control_context_signature': expected_control_context_signature,
            'candidate_character_id': candidate_character_id})
    result = {'type': 'execute_step', 'protocol_version': 1, 'request_id': identity(request_id, 'request_id'),
              'step': STEP, 'action': action,
              **{name: getattr(binding, name) for name in binding.__dataclass_fields__},
              'request_nonce': identity(request_nonce, 'request_nonce')}
    if action != 'query_context':
        result['expected_control_context_signature'] = expected_control_context_signature
        result['candidate_character_id'] = candidate_character_id
    return result


def encode_request(**arguments) -> bytes:
    return json.dumps(build_request(**arguments), ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def encode_packet(**arguments) -> bytes:
    payload = encode_request(**arguments)
    return struct.pack('<I', len(payload)) + payload


PROOF_KEYS = ('exact_build_verified', 'owner_verified', 'process_identity_verified',
              'source_abi_pins_verified', 'stock_files_verified', 'loaded_source_binding_verified',
              'frame_verified')
TARGET_FLAGS = {'read_complete', 'root_exists', 'root_visible', 'target_exists', 'target_visible',
                'target_enabled', 'unique_target', 'dispatch_admitted'}
DISPATCH_FLAGS = {'claim_latched', 'dispatch_invoked', 'native_handled', 'post_read_complete',
                  'postcondition_observed'}
NATIVE_KEYS = {'schema', 'step', 'action', 'status', 'native_revision', 'connection_generation',
               'game_pid', 'played_character_id', 'process_creation_filetime_100ns', 'pump_epoch',
               *PROOF_KEYS, 'context_signature_verified', 'control_context_signature', 'phase',
               'flow_id', 'flow_source_character_id', 'flow_target_character_id', 'flow_local_player_id',
               'flow_complete', 'local_player_id', 'controlled_character_id', 'selected_character_id',
               'controlled_character_is_ai', 'ironman', 'multiple_players', 'controller_records_complete',
               'controller_records', 'candidates_complete', 'candidates', 'targets', 'dispatches',
               'stage_consumed', 'control_postcondition_verified', 'reason'}
CONTROLLER_KEYS = {'player_id', 'character_id', 'is_current_controller', 'is_ai'}
CANDIDATE_KEYS = {'character_id', 'playable_id', 'is_ruler', 'can_control', 'selection_visible',
                  'selection_enabled', 'source_verified'}


def _nullable_bool(value: object, name: str):
    if value is not None and type(value) is not bool: raise ValueError(f'{name} must be actual bool or NULL')


def _nullable_id(value: object, name: str, *, player=False):
    if value is not None:
        if player: integer(value, name, minimum=0, maximum=2**32-1)
        else: character_id(value, name)


def actual_control_observed(raw: dict) -> bool:
    """Current manager membership and engine AI identity must independently agree."""
    if (not all(raw.get(key) is True for key in PROOF_KEYS)
            or type(raw.get('pump_epoch')) is not int or raw['pump_epoch'] <= 0
            or type(raw.get('flow_id')) is not str or re.fullmatch(SIGNATURE_PATTERN, raw['flow_id']) is None
            or type(raw.get('control_context_signature')) is not str
            or re.fullmatch(SIGNATURE_PATTERN, raw['control_context_signature']) is None
            or raw.get('controller_records_complete') is not True
            or raw.get('flow_complete') is not True or raw.get('phase') != 'control_confirmed'
            or raw.get('stage_consumed', [False]*4)[3] is not True
            or raw.get('controlled_character_is_ai') is not False
            or raw.get('flow_local_player_id') is None
            or raw.get('local_player_id') != raw.get('flow_local_player_id')
            or raw.get('controlled_character_id') != raw.get('flow_target_character_id')
            or raw.get('controlled_character_id') is None
            or raw.get('flow_source_character_id') == raw.get('flow_target_character_id')):
        return False
    if any(row['player_id'] is None or row['character_id'] is None
           or row['is_current_controller'] is None for row in raw['controller_records']):
        return False
    current = [row for row in raw['controller_records']
               if row['is_current_controller'] is True and row['player_id'] == raw['local_player_id']]
    return (len(current) == 1
            and current[0]['character_id'] == raw['controlled_character_id']
            and current[0]['is_ai'] is False
            and not any(row['is_current_controller'] is True
                        and row['character_id'] == raw['flow_source_character_id']
                        and row['player_id'] == raw['local_player_id'] for row in raw['controller_records']))


def normalize_native_observation(raw: object, binding: PlayerControlWireBinding, action: str) -> dict:
    raw = closed(raw, NATIVE_KEYS, 'native player-control observation')
    if (raw['schema'] != 'ck3-player-control-v1' or raw['step'] != STEP or raw['action'] != action
            or raw['status'] not in {'unavailable', 'context_observed', 'dispatch_pending',
                                     'dispatch_unknown_claimed', 'control_observed'}
            or raw['phase'] not in {'unavailable', 'map', 'pause_menu', 'switch_chooser', 'control_confirmed'}):
        raise ValueError('native player-control observation identity/status mismatch')
    for key, expected in {'native_revision': binding.expected_revision,
                          'connection_generation': binding.expected_connection_generation,
                          'game_pid': binding.expected_game_pid,
                          'played_character_id': binding.expected_player_character_id,
                          'process_creation_filetime_100ns': binding.expected_process_creation_filetime_100ns}.items():
        if type(raw[key]) is not int or raw[key] != expected: raise ValueError(f'native actual {key} binding changed')
    integer(raw['pump_epoch'], 'pump_epoch', minimum=0)
    for key in (*PROOF_KEYS, 'context_signature_verified', 'flow_complete', 'controller_records_complete',
                'candidates_complete', 'control_postcondition_verified'):
        if type(raw[key]) is not bool: raise ValueError(f'native {key} is not a boolean observation')
    for key in ('controlled_character_is_ai', 'ironman', 'multiple_players'):
        _nullable_bool(raw[key], key)
    for key in ('flow_source_character_id', 'flow_target_character_id', 'controlled_character_id', 'selected_character_id'):
        _nullable_id(raw[key], key)
    for key in ('local_player_id', 'flow_local_player_id'): _nullable_id(raw[key], key, player=True)
    if raw['flow_id'] is not None: signature(raw['flow_id'], 'backend flow_id')
    if type(raw['reason']) is not str: raise ValueError('native unavailability reason required')
    if raw['status'] != 'unavailable':
        signature(raw['control_context_signature'])
        if not all(raw[key] for key in PROOF_KEYS) or raw['pump_epoch'] <= 0 or raw['flow_id'] is None:
            raise ValueError('available context lacks actual source/owner/frame/flow proof')
    elif raw['control_context_signature'] != '': signature(raw['control_context_signature'])
    for group, fields in (('controller_records', CONTROLLER_KEYS), ('candidates', CANDIDATE_KEYS)):
        if type(raw[group]) is not list or len(raw[group]) > 16384: raise ValueError(f'bounded actual {group} required')
        seen = set()
        for row in raw[group]:
            row = closed(row, fields, group + ' row')
            _nullable_id(row['character_id'], 'character_id'); ident = row['character_id']
            if group == 'controller_records':
                _nullable_id(row['player_id'], 'player_id', player=True)
                ident = (row['player_id'], row['character_id'])
                for key in ('is_current_controller', 'is_ai'): _nullable_bool(row[key], key)
            else:
                if row['playable_id'] is not None: integer(row['playable_id'], 'playable_id')
                for key in ('is_ruler', 'can_control', 'selection_visible', 'selection_enabled', 'source_verified'):
                    _nullable_bool(row[key], key)
            if row['character_id'] is not None:
                if ident in seen: raise ValueError(f'duplicate actual {group} identity')
                seen.add(ident)
    for group, fields, extras in (('targets', TARGET_FLAGS, {'target_vtable_rva'}), ('dispatches', DISPATCH_FLAGS, set())):
        if type(raw[group]) is not list or len(raw[group]) != 4: raise ValueError(f'exact four {group} required')
        for row in raw[group]:
            row = closed(row, fields | extras, group + ' row')
            if any(type(row[key]) is not bool for key in fields): raise ValueError('actual target/dispatch bool required')
            if extras: integer(row['target_vtable_rva'], 'target_vtable_rva', minimum=0)
    if (type(raw['stage_consumed']) is not list or len(raw['stage_consumed']) != 4
            or any(type(value) is not bool for value in raw['stage_consumed'])):
        raise ValueError('actual four-stage consumption state required')
    if action == 'query_context':
        if any(row['claim_latched'] or row['dispatch_invoked'] for row in raw['dispatches']):
            raise ValueError('read-only query must not dispatch or consume a stage')
    else:
        index = ACTIONS.index(action)
        if any(row['claim_latched'] or row['dispatch_invoked'] for i,row in enumerate(raw['dispatches']) if i != index):
            raise ValueError('one typed request must never dispatch another stage')
        if raw['status'] != 'unavailable' and not raw['context_signature_verified']:
            raise ValueError('native mutation lacks backend signature verification')
        if raw['dispatches'][index]['claim_latched'] and not raw['stage_consumed'][index]:
            raise ValueError('claimed native stage cannot become unconsumed')
    if raw['control_postcondition_verified'] != actual_control_observed(raw):
        raise ValueError('control summary differs from actual controller/AI observations')
    if raw['status'] == 'control_observed' and not raw['control_postcondition_verified']:
        raise ValueError('selected character does not establish actual control')
    return dict(raw)


def stage_ready(native: dict, action: str, candidate: int | None) -> bool:
    index = ACTIONS.index(action)
    if (native.get('action') != 'query_context' or native.get('status') != 'context_observed'
            or any(native.get(key) is not True for key in PROOF_KEYS)
            or native.get('flow_complete') is not False or native.get('flow_id') is None
            or native['stage_consumed'][index] or native.get('ironman') is not False
            or native.get('multiple_players') is not False
            or native.get('controller_records_complete') is not True
            or native.get('controlled_character_is_ai') is not False
            or native.get('controlled_character_id') != native.get('flow_source_character_id')
            or native.get('local_player_id') != native.get('flow_local_player_id')
            or native.get('local_player_id') is None):
        return False
    if any(row['player_id'] is None or row['character_id'] is None
           or row['is_current_controller'] is None for row in native['controller_records']): return False
    current = [row for row in native['controller_records']
               if row['player_id'] == native['local_player_id'] and row['is_current_controller'] is True]
    if (len(current) != 1 or current[0]['character_id'] != native['controlled_character_id']
            or current[0]['is_ai'] is not False): return False
    if not all(native['targets'][index].get(key) is True for key in TARGET_FLAGS): return False
    if native['targets'][index]['target_vtable_rva'] <= 0: return False
    if action == 'open_pause_menu': return native['phase'] == 'map' and not any(native['stage_consumed'])
    if action == 'open_switch':
        return native['phase'] == 'pause_menu' and not any(native['stage_consumed'][1:])
    if (native['phase'] != 'switch_chooser' or native['stage_consumed'][1] is not True
            or native['candidates_complete'] is not True): return False
    choices = [row for row in native['candidates'] if row['character_id'] == candidate]
    if (len(choices) != 1 or choices[0]['can_control'] is not True or choices[0]['is_ruler'] is not True
            or choices[0]['source_verified'] is not True or choices[0]['playable_id'] is None
            or choices[0]['selection_visible'] is not True or choices[0]['selection_enabled'] is not True):
        return False
    if candidate == native['flow_source_character_id']: return False
    if action == 'choose_character':
        return (native['stage_consumed'][2:] == [False, False]
                and choices[0]['selection_visible'] is True and choices[0]['selection_enabled'] is True)
    return (native['stage_consumed'][2] is True and native['stage_consumed'][3] is False
            and native['selected_character_id'] == candidate and native['flow_target_character_id'] == candidate)


def normalize_public_result(raw: object, *, action: str, expected_revision: int) -> dict:
    if type(raw) is not dict or raw.get('schema') != 'ck3-player-control-result-v1':
        raise ValueError('typed public player-control result required')
    if (raw.get('action') != action or raw.get('public_revision') != expected_revision
            or raw.get('retry_authorized') is not False or raw.get('uses_ocr') is not False
            or raw.get('uses_desktop_input') is not False):
        raise ValueError('public control request identity/no-retry mismatch')
    for key in ('claim_consumed', 'actual_control_verified', 'actor_contexts_invalidated'):
        if type(raw.get(key)) is not bool: raise ValueError(f'public {key} boolean required')
    if action == 'query_context' and raw['claim_consumed']:
        raise ValueError('read-only query cannot claim a gameplay stage')
    if action != 'query_context' and not raw['claim_consumed']:
        raise ValueError('mutation must retain its durable no-retry claim')
    integer(raw.get('native_submission_count'), 'native_submission_count', minimum=0, maximum=1)
    signature(raw.get('source_inventory_sha256'), 'source_inventory_sha256')
    native = raw.get('native_observation')
    if native is None:
        if (raw.get('status') != 'dispatch_unknown_claimed' or not raw['claim_consumed']
                or raw['actual_control_verified']): raise ValueError('missing native result cannot establish control')
    else:
        wire = PlayerControlWireBinding(native['native_revision'], native['played_character_id'], native['game_pid'],
            native['connection_generation'], native['process_creation_filetime_100ns'], raw['source_inventory_sha256'])
        normalized = normalize_native_observation(native, wire, action)
        if raw.get('status') != normalized['status']:
            raise ValueError('public status differs from actual native status')
        if raw.get('process_creation_filetime_100ns') != normalized['process_creation_filetime_100ns']:
            raise ValueError('public original process FILETIME differs from native binding')
        verified = normalized['control_postcondition_verified']
        if verified:
            frame = raw.get('snapshot_after')
            binding = snapshot_binding(frame)
            if (binding['played_character_id'] != native['controlled_character_id']
                    or binding['game_pid'] != native['game_pid']
                    or binding['connection_generation'] != native['connection_generation']
                    or frame.get('map_ready') is not True
                    or type(frame.get('revision')) is not int or frame['revision'] < expected_revision
                    or binding['native_revision'] < native['native_revision']):
                raise ValueError('actual controller does not agree with independently refreshed snapshot')
        if raw['actual_control_verified'] != verified: raise ValueError('public control credit is inconsistent')
        if verified and not raw['actor_contexts_invalidated']: raise ValueError('changed control must invalidate actor caches')
    return dict(raw)
