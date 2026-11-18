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
    classify_terminal_exit_receipt, continue_preparation_context_ready_v1,
    CORE_EXIT_ROUTE, CORE_EXIT_CAPABILITY, CORE_EXIT_STEP, CORE_EXIT_VERSION,
    CORE_EXIT_EXE_SHA256, CORE_EXIT_BACKEND, CORE_EXIT_OBSERVATION_SCHEMA,
    normalize_core_exit_ack_v1, normalize_core_exit_observation_v1, CoreExitObservationV1,
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
    core_route = CORE_EXIT_CAPABILITY in capabilities.get('bridge_capabilities', [])
    if not core_route and NORMAL_EXIT_MAP_CAPABILITY not in capabilities.get('bridge_capabilities', []):
        raise UnsupportedStepError('native normal-exit-map-v1 capability is unavailable (default OFF)')
    profile = getattr(driver, 'normal_exit_managed_profile', None)
    reference = profile.get('normal_exit_source_inventory') if type(profile) is dict else None
    if type(reference) is not dict:
        raise UnsupportedStepError('normal exit requires the fixed actual managed-source inventory')
    if core_route:
        guard = profile.get('guard')
        target = guard.get('target') if isinstance(guard, dict) else None
        digest = target.get('executable_sha256') if isinstance(target, dict) else None
        if (profile.get('game_version') != CORE_EXIT_VERSION or type(digest) is not str
                or digest.upper() != CORE_EXIT_EXE_SHA256):
            raise UnsupportedStepError('Core exit inventory must bind the actual exact Florin executable')
    try:
        evidence = profile.get('evidence_directory')
        allocated = (isinstance(evidence, str) and
                     any((Path(evidence) / name).exists() for name in ('frozen-argv.json', 'ready-context.json')))
        sources = verify_source_inventory_v1(reference, profile,
            input_phase='running' if allocated else 'launch')
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise UnsupportedStepError(f'normal-exit source inventory unsupported: {error}') from error
    snapshot = driver.take_snapshot()
    if snapshot.get('revision') != expected_revision:
        raise PreSubmissionRevisionMismatchError('normal-exit public revision changed before submission')
    try:
        binding = _core_binding(snapshot, expected_revision) if core_route else opening_binding(snapshot)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return snapshot, binding, sources


def _core_binding(snapshot: object, expected_revision: int) -> dict[str, object]:
    from .version_identity import florin_full_source
    if not isinstance(snapshot, dict):
        raise ValueError('Core exit requires the actual Full object')
    source = florin_full_source(snapshot, expected_revision)
    speed, player = snapshot.get('speed'), snapshot.get('local_player_id')
    if (type(speed) is not int or not 1 <= speed <= 5 or type(player) is not int
            or not -(2**31) <= player < 2**31 or player == -1):
        raise ValueError('Core exit requires the actual Full clock and local player')
    return {'route': CORE_EXIT_ROUTE, 'native_revision': source.native_revision,
            'played_character_id': source.played_character_id, 'game_pid': source.game_pid,
            'connection_generation': source.connection_generation, 'date_raw': source.date_raw,
            'speed': speed, 'local_player_id': player, 'scope_sha256': source.scope_sha256}


def _core_observation(binding: dict, creation: int, signature: str, *, confirm: bool,
                      ack: dict[str, object] | None = None) -> CoreExitObservationV1:
    return normalize_core_exit_observation_v1({
        'schema': CORE_EXIT_OBSERVATION_SCHEMA, 'step': CORE_EXIT_STEP,
        'action': 'confirm_desktop' if confirm else 'query_context',
        'status': ('dispatch_pending' if ack is not None and ack['dispatch_status'] == 'requested'
                   and ack['accepted'] is True and ack['effect_attempted'] is True else
                   'dispatch_unknown_claimed' if confirm else 'context_observed'),
        'native_revision': binding['native_revision'], 'connection_generation': binding['connection_generation'],
        'game_pid': binding['game_pid'], 'played_character_id': binding['played_character_id'],
        'process_creation_filetime_100ns': creation, 'exit_context_signature': signature,
        'core_prefix': {'date_raw': binding['date_raw'], 'speed': binding['speed'], 'paused': True,
            'local_player_id': binding['local_player_id'], 'map_ready': True, 'has_played_character': True,
            'played_character_id': binding['played_character_id'], 'played_character_alive': True}, 'core_ack': ack},
        'confirm_desktop' if confirm else 'query_context')


def _query_core_context(driver, expected_revision: int, binding: dict, sources: dict) -> dict:
    creation = _exact_creation(_api(driver), binding['game_pid'])
    signature = hashlib.sha256(json.dumps({'binding': binding, 'birth': str(creation),
        'source_inventory_sha256': sources['source_inventory_sha256']}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    after = driver.take_snapshot()
    if _core_binding(after, expected_revision) != binding:
        raise BridgeUnavailableError('Core exit Full source changed during read-only context query')
    native = _core_observation(binding, creation, signature, confirm=False)
    result = {'schema': 'ck3-normal-exit-context-result-v1', 'route': CORE_EXIT_ROUTE,
        'status': 'context_observed', 'public_revision': expected_revision,
        'native_observation': native, 'exit_context_signature': signature,
        'source_inventory_sha256': sources['source_inventory_sha256'],
        'process_creation_filetime_100ns': creation, 'claim_consumed': False,
        'retry_authorized': False, 'orderly_exit_verified': False, 'autosave_verified': False}
    cache = getattr(driver, '_normal_exit_map_contexts', None)
    if cache is None:
        cache = {}; driver._normal_exit_map_contexts = cache
    cache[signature] = {'binding': binding, 'public_revision': expected_revision,
        'creation': creation, 'source_inventory_sha256': sources['source_inventory_sha256'], 'native': native}
    directory = driver._native_driver_state_path().parent / 'normal-exit-map-requests'
    directory.mkdir(parents=True, exist_ok=True)
    _preserve(directory / ('normal-exit-core-query-' + uuid.uuid4().hex + '.result.json'), result)
    return result


def _request_core_exit(driver, action: str, expected_revision: int, signature: str,
                       binding: dict, sources: dict) -> dict:
    if action != 'confirm_desktop':
        raise UnsupportedStepError('Core ApplicationExit uses one confirm_desktop request, without GUI preparation or autosave toggle')
    context = getattr(driver, '_normal_exit_map_contexts', {}).get(signature)
    if (type(context) is not dict or context.get('binding') != binding
            or context.get('public_revision') != expected_revision
            or context.get('source_inventory_sha256') != sources['source_inventory_sha256']):
        raise BridgeUnavailableError('Core exit signature is not this actual fresh Full context')
    creation = context['creation']
    directory = driver._native_driver_state_path().parent / 'normal-exit-map-requests'
    directory.mkdir(parents=True, exist_ok=True)
    identity = {'game_pid': binding['game_pid'], 'creation_filetime_100ns': creation, 'action': action}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    claim = directory / (key + '.claim.json')
    if claim.exists():
        raise BridgeUnavailableError('Core exit already claimed for the original process; no retry')
    observer = RetainedProcessObserver(_api(driver), binding['game_pid'], creation)
    request_id = 'normal-exit-core-' + uuid.uuid4().hex
    native = None; receipt_ns = None; error_text = None; attempted = False
    try:
        pin = observer.verify_before_dispatch()
        _preserve(claim, {'schema': 'ck3-normal-exit-once-claim-v1', 'identity': identity,
            'request_id': request_id, 'status': 'claimed_result_unknown_no_retry',
            'exit_context_signature': signature, 'source_inventory_sha256': sources['source_inventory_sha256'],
            'process_preconfirm_pin': pin})
    except FileExistsError as error:
        observer.close()
        raise BridgeUnavailableError('Core exit already claimed for the original process; no retry') from error
    except Exception:
        observer.close()
        raise
    try:
        # Core ApplicationExit's existing parser explicitly uses expected_revision
        # zero and the complete observed Core prefix. This is not the Full clock
        # route and cannot authorize resume or save.
        core = {'schema': 'ck3_1210_application_exit_v1', 'game_version': CORE_EXIT_VERSION,
            'executable_sha256': CORE_EXIT_EXE_SHA256, 'adapter_id': 'ck3-1.21.0-msvc-x64',
            'backend': CORE_EXIT_BACKEND, 'date_raw': binding['date_raw'], 'speed': binding['speed'],
            'paused': True, 'local_player_id': binding['local_player_id'], 'map_ready': True,
            'has_played_character': True, 'played_character_id': binding['played_character_id'],
            'played_character_alive': True}
        request = {'type': 'execute_step', 'protocol_version': 1, 'request_id': request_id,
            'step': CORE_EXIT_STEP, 'expected_revision': 0, 'arguments': {}, 'core_application_exit': core,
            'core_control_deadline_unix_ms': time.time_ns() // 1_000_000 + 8000}
        payload = json.dumps(request, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        with (directory / (request_id + '.payload.bin')).open('xb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        _preserve(directory / (request_id + '.request.json'), request)
        attempted = True
        driver.endpoint.send(request)
        frame = driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)
        observed_ns = time.monotonic_ns()
        if frame is None:
            raise BridgeUnavailableError('Core exit response missing; original submission remains UNKNOWN')
        _preserve(directory / (request_id + '.native-frame.json'), frame)
        if (type(frame) is not dict or frame.get('type') != 'command_result'
                or type(frame.get('protocol_version')) is not int or frame.get('protocol_version') != 1
                or frame.get('request_id') != request_id or type(frame.get('ok')) is not bool):
            raise BridgeUnavailableError('Core exit response identity is malformed')
        ack = normalize_core_exit_ack_v1(frame.get('result'))
        if frame['ok'] != ack['accepted']:
            raise BridgeUnavailableError('Core exit frame/ACK admission differs')
        native = _core_observation(binding, creation, signature, confirm=True, ack=ack)
        if native['status'] == 'dispatch_pending':
            receipt_ns = observed_ns
    except Exception as error:
        error_text = f'{type(error).__name__}: {error}'
    process = observer.observe(5000)
    facts = classify_terminal_exit_receipt(native, process,
        driver_dispatch_receipt_observed_monotonic_ns=receipt_ns, expected_process_identity=observer.identity)
    metadata = {'action': action, 'route': CORE_EXIT_ROUTE, 'public_revision': expected_revision,
        'request_id': request_id, 'claim_path': str(claim),
        'source_inventory_sha256': sources['source_inventory_sha256'],
        'process_creation_filetime_100ns': creation, 'process_preconfirm_pin': pin}
    retained = retain_normal_exit_observer_v1(driver, observer, native, receipt_ns, metadata, directory)
    result = {'schema': 'ck3-normal-exit-request-result-v1', **metadata, **facts,
        'native_observation': native, 'process_observation': process,
        'driver_dispatch_receipt_observed_monotonic_ns': receipt_ns,
        'receipt_clock_meaning': 'driver received an exact requested Core ApplicationExit ACK; not native callback time',
        'snapshot_after_required': False, 'reason': error_text, 'observer_retained': True,
        'uses_desktop_input': False, 'uses_ocr': False, 'native_submission_count': int(attempted)}
    receipt_path = directory / (request_id + '.result.json')
    _preserve(receipt_path, result)
    complete_normal_exit_observer_after_receipt_v1(driver, retained, result, receipt_path)
    return result


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
    if getattr(driver, '_normal_exit_owned_observer_v1', None) is not None:
        raise BridgeUnavailableError('terminal phase consumed; use the original-process read-only observer')
    before, binding, sources = _prepare(driver, expected_revision)
    if binding.get('route') == CORE_EXIT_ROUTE:
        return _query_core_context(driver, expected_revision, binding, sources)
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
    if binding.get('route') == CORE_EXIT_ROUTE:
        return _request_core_exit(driver, action, expected_revision, expected_exit_context_signature, binding, sources)
    cache = getattr(driver, '_normal_exit_map_contexts', {})
    context = cache.get(expected_exit_context_signature)
    if (type(context) is not dict or context.get('binding') != binding
            or context.get('public_revision') != expected_revision
            or context['wire'].source_inventory_sha256 != sources['source_inventory_sha256']):
        raise BridgeUnavailableError('normal-exit signature is not a fresh backend-observed context')
    wire = context['wire']
    if action == 'continue_preparation' and not continue_preparation_context_ready_v1(context['native']):
        raise BridgeUnavailableError('normal-exit continuation requires fresh stage 0 consumed, stage 1 available and no confirmation')
    if action == 'confirm_desktop' and not context['native']['confirmation_visible']:
        raise BridgeUnavailableError('desktop confirmation requires a fresh actual official modal query')
    if action == 'disable_exit_autosave':
        state = context['native'].get('exit_autosave', {})
        if (not context['native']['confirmation_visible'] or
                any(state.get(key) is not True for key in ('state_available', 'control_visible', 'control_enabled'))):
            raise BridgeUnavailableError('exit autosave disable requires the actual visible enabled stock save checkbox')
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
                  'exit_autosave_disabled_observed': native is not None and native['status'] == 'autosave_disabled',
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
