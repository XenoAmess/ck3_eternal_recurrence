"""Fixed stock switch flow, immutable claims and independently observed control.

This module has no arbitrary expression, process-writing or desktop fallback.
Unknown delivery remains consumed. A new flow cannot unlock an unfinished flow.
"""
from __future__ import annotations

from contextlib import nullcontext
import copy
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .normal_exit_map_driver_v1 import _exact_creation
from .normal_exit_process_observer_v1 import Win32ProcessApi
from .player_control_contract_v1 import (
    ACTIONS, CAPABILITY, PlayerControlWireBinding, actual_control_observed, encode_request,
    normalize_native_observation, normalize_public_result, normalize_query_arguments,
    normalize_request_arguments, snapshot_binding, stage_ready,
)
from .player_control_source_inventory_v1 import verify_source_inventory_v1


def _file(path: Path) -> Path:
    if os.name != 'nt':
        return path
    absolute = str(path.resolve())
    return Path(absolute if absolute.startswith('\\\\?\\') else '\\\\?\\' + absolute)


def _preserve(path: Path, value: dict) -> None:
    with _file(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _prepare(driver, expected_revision: int):
    if CAPABILITY not in driver.capabilities().get('bridge_capabilities', []):
        raise UnsupportedStepError('stock player-control-v1 source capability is unavailable (default OFF)')
    profile = getattr(driver, 'player_control_managed_profile', None)
    reference = profile.get('player_control_source_inventory') if type(profile) is dict else None
    if type(reference) is not dict:
        raise UnsupportedStepError('stock control requires its fixed actual managed-source inventory')
    try: sources = verify_source_inventory_v1(reference, profile)
    except (ValueError, OSError, TypeError, KeyError) as error:
        raise UnsupportedStepError(f'player-control source inventory unsupported: {error}') from error
    before = driver.take_snapshot()
    if before.get('revision') != expected_revision:
        raise PreSubmissionRevisionMismatchError('player-control public revision changed before submission')
    try: binding = snapshot_binding(before)
    except ValueError as error: raise BridgeUnavailableError(str(error)) from error
    api = getattr(driver, 'player_control_process_api_factory', Win32ProcessApi)()
    creation = _exact_creation(api, binding['game_pid'])
    wire = PlayerControlWireBinding(binding['native_revision'], binding['played_character_id'],
        binding['game_pid'], binding['connection_generation'], creation, sources['source_inventory_sha256'])
    return before, binding, wire, sources


def _directory(driver) -> Path:
    directory = _file(driver._native_driver_state_path().parent / 'player-control-requests-v1')
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def restore_pending_authorization_v1(driver, profile: dict) -> None:
    """Reconnect may restore an unfinished claim, but may never erase one."""
    if 'player_control_source_inventory' not in profile: return
    directory = _file(driver._native_driver_state_path().parent / 'player-control-requests-v1')
    if not directory.exists(): return
    pid = profile['guard']['target']['pid']
    api = getattr(driver, 'player_control_process_api_factory', Win32ProcessApi)()
    creation = _exact_creation(api, pid)
    digest = profile['player_control_source_inventory']['sha256']
    for record_path in directory.glob('process-*/*.flow.json'):
        record = json.loads(_file(record_path).read_bytes())
        process = record['process_identity']
        if (process['game_pid'] == pid and process['creation_filetime_100ns'] == creation
                and process['source_inventory_sha256'] == digest
                and not (record_path.parent / (record['flow_id'] + '.completed.json')).exists()
                and any((record_path.parent / (_digest({'process_identity': process,
                    'flow_id': record['flow_id'], 'stage': stage}) + '.claim.json')).exists()
                    for stage in ACTIONS)):
            driver._player_control_authorization_blocked_v1 = True
            return


def _exchange(driver, action, wire, directory, *, signature=None, candidate=None, on_submission=None):
    request_id = 'player-control-' + action + '-' + uuid.uuid4().hex
    payload = encode_request(request_id=request_id, action=action, binding=wire, request_nonce=request_id,
        expected_control_context_signature=signature, candidate_character_id=candidate)
    with _file(directory / (request_id + '.payload.bin')).open('xb') as stream: stream.write(payload)
    request = json.loads(payload)
    _preserve(directory / (request_id + '.request.json'), request)
    if on_submission is not None: on_submission(request_id)
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)
    receipt_ns = time.monotonic_ns()
    if frame is None: raise BridgeUnavailableError('native control response missing; submitted stage remains consumed')
    _preserve(directory / (request_id + '.native-frame.json'), frame)
    if frame.get('ok') is not True: raise BridgeUnavailableError('native stock control rejected: ' + str(frame.get('error')))
    native = normalize_native_observation(frame.get('result'), wire, action)
    return native, request_id, receipt_ns


def _process_identity(binding, wire):
    # Deliberately exclude public/native revision, generation and reconnect session:
    # none of them unlocks a claimed stage of the original campaign/process.
    return {'game_pid': wire.expected_game_pid,
            'creation_filetime_100ns': wire.expected_process_creation_filetime_100ns,
            'source_inventory_sha256': wire.source_inventory_sha256}


def _observe_flow(driver, directory, binding, wire, native):
    if native['status'] == 'unavailable': return None
    process = _process_identity(binding, wire)
    chain = directory / ('process-' + _digest(process))
    chain.mkdir(exist_ok=True)
    flow_id = native['flow_id']
    record = chain / (flow_id + '.flow.json')
    if record.exists():
        stored = json.loads(_file(record).read_bytes())
        if (stored['process_identity'] != process or stored['flow_id'] != flow_id
                or stored['source_character_id'] != native['flow_source_character_id']
                or stored['local_player_id'] != native['flow_local_player_id']):
            raise BridgeUnavailableError('durable stock switch flow identity changed')
        return chain
    records = [json.loads(_file(path).read_bytes()) for path in chain.glob('*.flow.json')]
    records.sort(key=lambda row: row['sequence'])
    previous = records[-1] if records else None
    if previous:
        completed_path = chain / (previous['flow_id'] + '.completed.json')
        if not completed_path.exists():
            raise BridgeUnavailableError('new backend flow cannot unlock an unfinished or unknown switch')
        completed = json.loads(_file(completed_path).read_bytes())
        if (completed['process_identity'] != process or completed['flow_id'] != previous['flow_id']
                or completed['actual_control_verified'] is not True
                or native['flow_source_character_id'] != completed['controlled_character_id']
                or native['flow_local_player_id'] != completed['local_player_id']):
            raise BridgeUnavailableError('new switch lacks the prior independently observed control postcondition')
    if native['flow_source_character_id'] != binding['played_character_id'] or native['flow_local_player_id'] is None:
        # Re-observing a completed, already-known flow is handled above. An unknown
        # completed flow after reconnect cannot authorize another caller stage.
        raise BridgeUnavailableError('new stock flow lacks its actual starting actor/local player identity')
    _preserve(record, {'schema': 'ck3-player-control-durable-flow-v1', 'flow_id': flow_id,
        'process_identity': process, 'sequence': len(records) + 1,
        'source_character_id': native['flow_source_character_id'],
        'local_player_id': native['flow_local_player_id'],
        'previous_flow_id': previous['flow_id'] if previous else None,
        'introduced_native_revision': wire.expected_revision})
    return chain


_NONE_CACHES = (
    '_declaration_query_sequence', '_declaration_query_binding', '_pending_declaration_query',
    '_army_strength_query', '_combat_simulation_inputs_query', '_combat_simulation_inputs_v3_query',
    '_battle_control_snapshot_v1_query', '_active_combat_retreat_v1_token', '_war_entry_assessments_query',
    '_campaign_root_context_query', '_arrange_marriage_query_sequence', '_succession_expectation',
    '_succession_reconciliation',
)
_LIST_CACHES = ('_declarable_wars', '_war_entry_assessments_two_read_trace', '_arrange_marriage_choices')
_DICT_CACHES = ('_war_termination_options', '_war_termination_terms', '_war_termination_exit_terms',
                '_normal_exit_map_contexts', '_player_control_contexts')


def _verify_and_refresh_control(driver, native, after, chain, binding, wire):
    if not actual_control_observed(native): return False
    current = snapshot_binding(after)
    if (current['played_character_id'] != native['controlled_character_id']
            or current['game_pid'] != binding['game_pid']
            or current['connection_generation'] != binding['connection_generation']
            or current['episode_run_id'] != binding['episode_run_id']
            or current['date_raw'] != binding['date_raw'] or after.get('map_ready') is not True
            or current['native_revision'] < binding['native_revision']):
        raise BridgeUnavailableError('stock Control ACK lacks independent actual player snapshot agreement')
    lock = getattr(driver, '_driver_state_lock', None) or nullcontext()
    with lock:
        for name in _NONE_CACHES:
            if hasattr(driver, name): setattr(driver, name, None)
        for name in _LIST_CACHES:
            if hasattr(driver, name): setattr(driver, name, [])
        for name in _DICT_CACHES:
            if hasattr(driver, name): setattr(driver, name, {})
        if hasattr(driver, '_episode_character_id'):
            driver._episode_character_id = current['played_character_id']
        driver._player_control_last_verified_actor_v1 = current['played_character_id']
        driver._player_control_last_verified_flow_v1 = native['flow_id']
    persist = getattr(driver, '_persist_driver_state', None)
    if callable(persist): persist()
    completed_path = chain / (native['flow_id'] + '.completed.json')
    if not completed_path.exists():
        _preserve(completed_path, {'schema': 'ck3-player-control-durable-completion-v1',
            'process_identity': _process_identity(binding, wire), 'flow_id': native['flow_id'],
            'actual_control_verified': True, 'local_player_id': native['local_player_id'],
            'controlled_character_id': current['played_character_id'],
            'native_observation': native, 'snapshot_after': after,
            'claim_files_retained': True, 'command_history_retained': True})
    driver._player_control_authorization_blocked_v1 = False
    return True


def _result(action, expected_revision, wire, native, *, request_id, claim_consumed,
            after=None, verified=False, reason=None, submissions=0, claim=None):
    return {'schema': 'ck3-player-control-result-v1', 'action': action,
            'status': native['status'] if native else 'dispatch_unknown_claimed',
            'public_revision': expected_revision, 'native_observation': native,
            'control_context_signature': native['control_context_signature'] if native else None,
            'source_inventory_sha256': wire.source_inventory_sha256,
            'process_creation_filetime_100ns': wire.expected_process_creation_filetime_100ns,
            'request_id': request_id, 'claim_path': str(claim) if claim else None,
            'claim_consumed': claim_consumed, 'retry_authorized': False,
            'actual_control_verified': verified, 'actor_contexts_invalidated': verified,
            'snapshot_after': after, 'reason': reason, 'native_submission_count': submissions,
            'uses_ocr': False, 'uses_desktop_input': False,
            'business_effects_verified': False, 'full_product_acceptance_credit': False}


def query_player_control_context_v1(driver, *, expected_revision: int) -> dict:
    # Every attempted fresh query retires the old ephemeral signature, including
    # argument/source/process/frame refusals. Durable claims and barriers survive.
    driver._player_control_contexts = {}
    expected_revision = normalize_query_arguments({'expected_revision': expected_revision})['expected_revision']
    before, binding, wire, sources = _prepare(driver, expected_revision)
    directory = _directory(driver)
    native, request_id, receipt_ns = _exchange(driver, 'query_context', wire, directory)
    after = driver.take_snapshot()
    actual_after = snapshot_binding(after)
    verified_native = actual_control_observed(native)
    if not verified_native and (actual_after != binding or after.get('revision') != expected_revision):
        raise BridgeUnavailableError('stock switch query crossed its actual paused identity/revision frame')
    chain = _observe_flow(driver, directory, binding, wire, native)
    verified = _verify_and_refresh_control(driver, native, after, chain, binding, wire) if verified_native else False
    result = _result('query_context', expected_revision, wire, native, request_id=request_id,
                     claim_consumed=False, after=after, verified=verified, submissions=1)
    if native['status'] == 'context_observed':
        # Retain just the latest read, not a reusable cache of historical signatures.
        driver._player_control_contexts = {native['control_context_signature']: {
            'wire': wire, 'binding': binding, 'public_revision': expected_revision,
            'native': copy.deepcopy(native), 'request_id': request_id,
            'receipt_observed_monotonic_ns': receipt_ns, 'chain': chain}}
        if any(native['stage_consumed']): driver._player_control_authorization_blocked_v1 = True
    normalize_public_result(result, action='query_context', expected_revision=expected_revision)
    _preserve(directory / (request_id + '.result.json'), result)
    return result


def request_player_control_v1(driver, action: str, *, expected_revision: int,
                              expected_control_context_signature: str,
                              candidate_character_id: int | None) -> dict:
    arguments = normalize_request_arguments({'action': action, 'expected_revision': expected_revision,
        'expected_control_context_signature': expected_control_context_signature,
        'candidate_character_id': candidate_character_id})
    before, binding, wire, sources = _prepare(driver, expected_revision)
    context = getattr(driver, '_player_control_contexts', {}).get(expected_control_context_signature)
    if (type(context) is not dict or context.get('binding') != binding
            or context.get('public_revision') != expected_revision or context.get('wire') != wire
            or not stage_ready(context['native'], action, candidate_character_id)):
        raise BridgeUnavailableError('stock player-control requires the exact latest eligible backend query/candidate')
    directory = _directory(driver)
    chain = _observe_flow(driver, directory, binding, wire, context['native'])
    identity = {'process_identity': _process_identity(binding, wire),
                'flow_id': context['native']['flow_id'], 'stage': action}
    claim = chain / (_digest(identity) + '.claim.json')
    if claim.exists():
        raise BridgeUnavailableError('stock switch stage already consumed; new query/revision/reconnect cannot retry it')
    native = None; request_id = None; after = None; verified = False; submissions = 0; reason = None
    _preserve(claim, {'schema': 'ck3-player-control-once-claim-v1', 'identity': identity,
        'candidate_character_id': candidate_character_id,
        'control_context_signature': expected_control_context_signature,
        'status': 'claimed_result_unknown_no_retry'})
    driver._player_control_authorization_blocked_v1 = True
    # Consume this query before submission. It never becomes reusable on failure.
    driver._player_control_contexts = {}
    def submitted(rid):
        nonlocal submissions, request_id
        request_id = rid; submissions = 1
    try:
        native, request_id, receipt_ns = _exchange(driver, action, wire, directory,
            signature=expected_control_context_signature, candidate=candidate_character_id,
            on_submission=submitted)
        if actual_control_observed(native):
            after = driver.take_snapshot()
            verified = _verify_and_refresh_control(driver, native, after, chain, binding, wire)
    except Exception as error:
        # Preserve the failed normalization and its original native frame rather
        # than presenting any unvalidated ACK as a successful native observation.
        reason = f'{type(error).__name__}: {error}'
        native = None; verified = False
    request_id = request_id or ('player-control-presubmission-' + uuid.uuid4().hex)
    result = _result(action, expected_revision, wire, native, request_id=request_id,
        claim_consumed=True, after=after, verified=verified, reason=reason, submissions=submissions, claim=claim)
    normalize_public_result(result, action=action, expected_revision=expected_revision)
    _preserve(directory / (request_id + '.result.json'), result)
    return result
