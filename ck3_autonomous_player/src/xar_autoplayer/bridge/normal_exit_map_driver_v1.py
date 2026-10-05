"""Dedicated map normal-exit driver path; terminal readback never needs a snapshot.

All Win32/pipe operations occur only inside explicitly requested driver methods.
One persistent client claim and one native backend claim prevent replay after
uncertain delivery. Importing or offline SDK schema inspection does no business
callback, process, pipe, desktop or game work.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_decisions_open_contract import opening_binding
from .normal_exit_contract_v1 import (
    ExitWireBinding, NORMAL_EXIT_MAP_CAPABILITY, encode_normal_exit_map_request,
    normalize_query_arguments, normalize_request_arguments, normalize_native_exit_observation,
    classify_terminal_exit_receipt,
)
from .normal_exit_process_observer_v1 import (
    Win32ProcessApi, RetainedProcessObserver, SYNCHRONIZE,
    PROCESS_QUERY_LIMITED_INFORMATION, exact_integer,
)
from .normal_exit_source_inventory_v1 import verify_source_inventory_v1
from .normal_exit_pending_observer_v1 import (
    retain_normal_exit_observer_v1, complete_normal_exit_observer_after_receipt_v1,
)


def _prepare(driver, expected_revision: int) -> tuple[dict, dict, dict]:
    capabilities = driver.capabilities()
    if NORMAL_EXIT_MAP_CAPABILITY not in capabilities.get('bridge_capabilities', []):
        raise UnsupportedStepError('native normal-exit-map-v1 capability is unavailable (default OFF)')
    profile = getattr(driver, 'normal_exit_managed_profile', None)
    reference = profile.get('normal_exit_source_inventory') if type(profile) is dict else None
    if type(reference) is not dict:
        raise UnsupportedStepError('normal exit requires the fixed actual managed-source inventory')
    try:
        sources = verify_source_inventory_v1(reference, profile)
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise UnsupportedStepError(f'normal-exit source inventory unsupported: {error}') from error
    snapshot = driver.take_snapshot()
    if snapshot.get('revision') != expected_revision:
        raise PreSubmissionRevisionMismatchError('normal-exit public revision changed before submission')
    try:
        binding = opening_binding(snapshot)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return snapshot, binding, sources


def _api(driver):
    factory = getattr(driver, 'normal_exit_process_api_factory', Win32ProcessApi)
    return factory()


def _exact_creation(api, pid: int) -> int:
    handle = api.open_process(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, pid)
    try:
        if exact_integer(api.process_id(handle), 1, 0xFFFFFFFF, 'actual_pid') != pid:
            raise ValueError('original process PID differs from current native frame')
        return exact_integer(api.creation_filetime(handle), 1, 0xFFFFFFFFFFFFFFFF, 'actual_creation_filetime')
    finally:
        api.close(handle)


def _wire_binding(binding: dict, creation: int, sources: dict) -> ExitWireBinding:
    return ExitWireBinding(binding['native_revision'], binding['played_character_id'],
                           binding['game_pid'], binding['connection_generation'], creation,
                           sources['source_inventory_sha256'])


def _preserve(path: Path, value: dict) -> None:
    actual=Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path
    with actual.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def _exchange(driver, action: str, wire: ExitWireBinding, request_id: str,
              directory: Path, signature: str | None, on_submission=None) -> tuple[dict, int]:
    arguments = {'request_id': request_id, 'action': action, 'binding': wire,
                 'request_nonce': request_id, 'expected_exit_context_signature': signature}
    payload = encode_normal_exit_map_request(**arguments)
    request = json.loads(payload)
    # The production endpoint sends the existing length-prefixed compact JSON.
    # Offline tests capture its actual packet and prove exact equality to payload.
    with (directory / (request_id + '.payload.bin')).open('xb') as stream: stream.write(payload)
    _preserve(directory / (request_id + '.request.json'), request)
    if on_submission is not None: on_submission()
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)
    receipt_ns = time.monotonic_ns()
    if frame is None:
        raise BridgeUnavailableError('normal-exit native response missing; submission remains consumed')
    _preserve(directory / (request_id + '.native-frame.json'), frame)
    if frame.get('ok') is not True:
        raise BridgeUnavailableError('normal-exit native response rejected: ' + str(frame.get('error')))
    native = normalize_native_exit_observation(frame.get('result'), wire, action)
    return native, receipt_ns


def query_normal_exit_context_v1(driver, *, expected_revision: int) -> dict:
    expected_revision = normalize_query_arguments({'expected_revision': expected_revision})['expected_revision']
    before, binding, sources = _prepare(driver, expected_revision)
    creation = _exact_creation(_api(driver), binding['game_pid'])
    wire = _wire_binding(binding, creation, sources)
    directory = driver._native_driver_state_path().parent / 'normal-exit-map-requests'
    directory.mkdir(parents=True, exist_ok=True)
    request_id = 'normal-exit-query-' + uuid.uuid4().hex
    native, receipt_ns = _exchange(driver, 'query_context', wire, request_id, directory, None)
    after = driver.take_snapshot()
    if opening_binding(after) != binding or after.get('revision') != expected_revision:
        raise BridgeUnavailableError('normal-exit context query crossed its actual paused-map frame')
    result = {'schema': 'ck3-normal-exit-context-result-v1', 'status': native['status'],
              'public_revision': expected_revision, 'native_observation': native,
              'exit_context_signature': native['exit_context_signature'],
              'source_inventory_sha256': wire.source_inventory_sha256,
              'process_creation_filetime_100ns': creation,
              'claim_consumed': False, 'retry_authorized': False,
              'orderly_exit_verified': False, 'autosave_verified': False}
    if native['status'] == 'context_observed':
        cache = getattr(driver, '_normal_exit_map_contexts', None)
        if cache is None:
            cache = {}; driver._normal_exit_map_contexts = cache
        cache[native['exit_context_signature']] = {
            'wire': wire, 'binding': binding, 'public_revision': expected_revision,
            'native': native, 'request_id': request_id, 'receipt_observed_monotonic_ns': receipt_ns}
    _preserve(directory / (request_id + '.result.json'), result)
    return result


def request_normal_exit_v1(driver, action: str, *, expected_revision: int,
                           expected_exit_context_signature: str) -> dict:
    arguments = normalize_request_arguments({'action': action, 'expected_revision': expected_revision,
                                             'expected_exit_context_signature': expected_exit_context_signature})
    if getattr(driver, '_normal_exit_owned_observer_v1', None) is not None:
        raise BridgeUnavailableError('terminal phase is consumed; use the read-only original-process observer')
    before, binding, sources = _prepare(driver, arguments['expected_revision'])
    cache = getattr(driver, '_normal_exit_map_contexts', {})
    context = cache.get(expected_exit_context_signature)
    if (type(context) is not dict or context.get('binding') != binding
            or context.get('public_revision') != expected_revision
            or context['wire'].source_inventory_sha256 != sources['source_inventory_sha256']):
        raise BridgeUnavailableError('normal-exit signature is not a fresh backend-observed context')
    wire = context['wire']
    if action == 'confirm_desktop' and not context['native']['confirmation_visible']:
        raise BridgeUnavailableError('desktop confirmation requires a fresh actual official modal query')
    directory = driver._native_driver_state_path().parent / 'normal-exit-map-requests'
    directory.mkdir(parents=True, exist_ok=True)
    identity = {'game_pid': wire.expected_game_pid,
                'creation_filetime_100ns': wire.expected_process_creation_filetime_100ns, 'action': action}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    claim = directory / (key + '.claim.json')
    if claim.exists():
        raise BridgeUnavailableError('normal-exit phase already claimed for the original process; no retry')
    observer = None
    if action == 'confirm_desktop':
        observer = RetainedProcessObserver(_api(driver), wire.expected_game_pid,
                                           wire.expected_process_creation_filetime_100ns)
    request_id = 'normal-exit-' + action + '-' + uuid.uuid4().hex
    native = None; process = None; receipt_ns = None; error_text = None
    submission_attempted = [False]
    try:
        pin = observer.verify_before_dispatch() if observer is not None else None
        _preserve(claim, {'schema': 'ck3-normal-exit-once-claim-v1', 'identity': identity,
                          'request_id': request_id, 'status': 'claimed_result_unknown_no_retry',
                          'exit_context_signature': expected_exit_context_signature,
                          'source_inventory_sha256': wire.source_inventory_sha256,
                          'process_preconfirm_pin': pin})
        # Exactly one submission. A native rejection or missing ACK never clears it.
        native, native_receipt_ns = _exchange(driver, action, wire, request_id, directory,
            expected_exit_context_signature,
            on_submission=lambda: submission_attempted.__setitem__(0, True))
        if action == 'confirm_desktop' and native['dispatches'][2]['dispatch_invoked']:
            receipt_ns = native_receipt_ns
    except FileExistsError as error:
        raise BridgeUnavailableError('normal-exit phase race lost; no retry') from error
    except Exception as error:
        if not claim.exists():
            raise
        error_text = f'{type(error).__name__}: {error}'
    finally:
        if observer is not None:
            if claim.exists():
                process = observer.observe(5000)
            else:
                observer.close()
    if action == 'confirm_desktop':
        facts = classify_terminal_exit_receipt(native, process,
            driver_dispatch_receipt_observed_monotonic_ns=receipt_ns,
            expected_process_identity=observer.identity)
        result = {'schema': 'ck3-normal-exit-request-result-v1', 'action': action, **facts,
                  'native_observation': native, 'process_observation': process,
                  'process_preconfirm_pin': pin,
                  'driver_dispatch_receipt_observed_monotonic_ns': receipt_ns,
                  'receipt_clock_meaning': 'driver observed a validated dispatch_invoked native response; not native callback time',
                  'snapshot_after_required': False, 'reason': error_text}
        retained_state = retain_normal_exit_observer_v1(driver, observer, native, receipt_ns,
            {'action': action, 'public_revision': expected_revision, 'request_id': request_id,
             'claim_path': str(claim), 'source_inventory_sha256': wire.source_inventory_sha256,
             'process_creation_filetime_100ns': wire.expected_process_creation_filetime_100ns,
             'process_preconfirm_pin': pin}, directory)
        result['observer_retained'] = True
    else:
        result = {'schema': 'ck3-normal-exit-request-result-v1', 'action': action,
                  'status': native['status'] if native else 'dispatch_unknown_claimed',
                  'native_observation': native, 'claim_consumed': True, 'retry_authorized': False,
                  'confirmation_observed': native is not None and native['status'] == 'confirmation_observed',
                  'process_exit_observed': False, 'typed_normal_exit_observed': False,
                  'orderly_exit_verified': False, 'autosave_verified': False, 'reason': error_text}
    result.update({'public_revision': expected_revision, 'request_id': request_id,
                   'claim_path': str(claim), 'source_inventory_sha256': wire.source_inventory_sha256,
                   'process_creation_filetime_100ns': wire.expected_process_creation_filetime_100ns,
                   'uses_desktop_input': False, 'uses_ocr': False,
                   'native_submission_count': int(submission_attempted[0])})
    receipt_path = directory / (request_id + '.result.json')
    _preserve(receipt_path, result)
    if action == 'confirm_desktop':
        complete_normal_exit_observer_after_receipt_v1(driver, retained_state, result, receipt_path)
    return result
