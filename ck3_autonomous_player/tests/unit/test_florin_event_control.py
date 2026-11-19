from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.event_contract import (
    FLORIN_EVENT_QUERY_STEP, FLORIN_EVENT_SELECT_CAPABILITY, florin_event_fields, florin_event_source, normalize_florin_event_result,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState, _semantic_snapshot_from_frame
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.timeline_control_ack_v1 import require_florin_control_ready_v1
from xar_autoplayer.bridge.version_identity import CK3_1210, florin_full_source
from xar_autoplayer.native_session import require_game_windows_background

FIXTURES = ROOT / 'java/ck3-control/native-transport/src/test/resources/newnative'


def cpp(name: str) -> dict[str, object]:
    directory = FIXTURES / 'event-options1210'
    manifest = json.loads((directory / 'producer.json').read_bytes())
    row = next(item for item in manifest['packets'] if item['file'] == name)
    raw = (directory / name).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    return json.loads(raw)['result']


def frame() -> dict[str, object]:
    raw = (FIXTURES / 'full1210/full-snapshot-producer-102.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5':
        raise AssertionError('Exact actual C++ Full fixture hash required')
    state = NativeProtocolState('software-florin-event-test')
    state.ingest({'type': 'hello', 'protocol_version': 1, 'pid': 42, 'connection_generation': 3,
                  'expected_ck3_version': CK3_1210.game_version, 'expected_ck3_sha256': CK3_1210.executable_sha256,
                  'game_adapter_id': 'ck3-1.21.0-msvc-x64', 'ck3_build_match': True,
                  'capabilities': ['game.state.snapshot', 'game.query.current-event-options.v1', 'game.command.select-event-option-N']})
    kind = state.ingest(json.loads(raw))
    if kind != 'state_snapshot':
        raise AssertionError('Actual C++ Full must be ingested by the shared SDK')
    return {**state.semantic_snapshot(), 'episode_run_id': 'software-episode'}


def event_capabilities(snapshot: dict[str, object]) -> dict[str, object]:
    # Same HELLO family spelling as retained R0014; no invented per-option capability.
    return {'bridge_capabilities': list(snapshot['diagnostics']['hello']['capabilities'])}


def production_primitive_driver(directory: Path):
    """Actual event writer AND primitive/capability/request path; only pipe and OS quiet check are inert."""
    driver = object.__new__(NativeHeadlessGameplayDriver)
    start = frame(); changed = copy.deepcopy(start); changed['active_event'] = None
    changed['native_revision'] = 12; changed['snapshot_id'] = 'native:12'
    driver.command_timeout_seconds = 2.0; driver._request_sequence = 0
    driver._record_command = Mock()
    driver.take_snapshot_without_native_command_history = Mock(side_effect=lambda: copy.deepcopy(start))
    driver.take_internal_semantic_snapshot = Mock(side_effect=lambda: copy.deepcopy(changed))
    driver._wait_for_life_advance_snapshot = Mock(side_effect=lambda snapshot, predicate, **kwargs: snapshot)
    driver._native_driver_state_path = Mock(return_value=directory / 'driver.json')
    caps = event_capabilities(start)
    driver.capabilities = Mock(return_value=caps)
    sent = []
    def send(request, **kwargs):
        sent.append(copy.deepcopy(request))
        packet = kwargs.get('packet_evidence_path')
        if packet is not None:
            with packet.open('x', encoding='utf-8') as stream:
                json.dump(request, stream)
    def result(request_id, timeout):
        step = sent[-1]['step']
        raw = cpp('available.json' if step == FLORIN_EVENT_QUERY_STEP else 'submitted.json')
        return {'type':'command_result', 'protocol_version':1, 'request_id':request_id, 'ok':True, 'result':raw}
    driver.endpoint = SimpleNamespace(send=send)
    driver.state = SimpleNamespace(wait_for_command_result=result)
    return driver, start, sent, caps


class FlorinEventControlTests(unittest.TestCase):

    def test_actual_capability_producer_reports_limited_florin_options_without_full_context(self) -> None:
        from xar_autoplayer.bridge.event_contract import florin_event_options_query_supported
        driver = NativeHeadlessGameplayDriver(endpoint=SimpleNamespace(start=lambda *_: None), episode_projection='native_campaign')
        actual = frame()
        hello = copy.deepcopy(actual['diagnostics']['hello'])
        driver.state.ingest(hello)
        packet = json.loads((FIXTURES / 'full1210/full-snapshot-producer-102.json').read_bytes())
        driver.state.ingest(packet)
        caps = driver.capabilities()
        self.assertIs(caps['current_event_options_v1210_query_supported'], True)
        self.assertIs(caps['current_event_window_context_v1_query_supported'], False)
        self.assertNotIn('game.command.query-current-event-window-context-v1', caps['bridge_capabilities'])
        self.assertTrue(florin_event_options_query_supported(actual, caps['bridge_capabilities']))
        for changed in ('capability', 'hello_capability', 'sha', 'schema', 'adapter', 'paused', 'full_sha'):
            candidate = copy.deepcopy(actual); announced = list(caps['bridge_capabilities'])
            if changed == 'capability': announced.remove('game.query.current-event-options.v1')
            elif changed == 'hello_capability': candidate['diagnostics']['hello']['capabilities'].remove('game.query.current-event-options.v1')
            elif changed == 'sha': candidate['diagnostics']['hello']['expected_ck3_sha256'] = '0' * 64
            elif changed == 'schema': candidate['schema'] = 'ck3_12004_full_state_v1'
            elif changed == 'adapter': candidate['adapter_id'] = 'ck3-1.20.0.4-msvc-x64'
            elif changed == 'paused': candidate['paused'] = False
            else: candidate['executable_sha256'] = '0' * 64
            with self.subTest(changed=changed):
                self.assertFalse(florin_event_options_query_supported(candidate, announced))
        driver.state.ingest({**hello, 'capabilities': ['game.state.snapshot']})
        driver.state.ingest(packet)
        self.assertIs(driver.capabilities()['current_event_options_v1210_query_supported'], False)


    def test_actual_primitive_accepts_hello_family_for_public_and_generic_florin_route(self) -> None:
        for generic in (False, True):
            with self.subTest(generic=generic), tempfile.TemporaryDirectory() as temporary:
                driver, start, sent, _ = production_primitive_driver(Path(temporary))
                self.assertEqual(FLORIN_EVENT_SELECT_CAPABILITY, 'game.command.select-event-option-N')
                self.assertNotIn('game.command.select-event-option-2', event_capabilities(start)['bridge_capabilities'])
                with patch('xar_autoplayer.native_session.require_game_windows_background'):
                    if generic:
                        result = driver._execute_event_option_step('select-event-option-2',
                            option_number=2, expected_revision=start['revision'])
                    else:
                        result = driver.select_event_option_v1210(2, event_instance_id=42,
                            expected_revision=start['revision'])
                self.assertTrue(result['event_selection']['postcondition_verified'])
                self.assertEqual([p['step'] for p in sent], [FLORIN_EVENT_QUERY_STEP, 'select-event-option-2'])
                self.assertEqual(sent[1]['expected_revision'], 11)
                self.assertEqual(sent[1]['arguments'], {'event_instance_id':42})
                self.assertEqual(sent[1]['event_option_control'], sent[0]['event_option_control'])
                self.assertEqual(driver._record_command.call_count, 0 if generic else 1)
                claims = list((Path(temporary)/'event-option-controls1210').glob('*.claim.json'))
                self.assertEqual(len(claims), 1)
                self.assertEqual(json.loads(claims[0].read_bytes())['native_option_index'], 1)

    def test_missing_or_per_option_only_family_refuses_before_query_claim_and_unknown(self) -> None:
        for announced in ([], ['game.command.select-event-option-2']):
            with self.subTest(announced=announced), tempfile.TemporaryDirectory() as temporary:
                driver, start, sent, caps = production_primitive_driver(Path(temporary))
                caps['bridge_capabilities'] = ['game.state.snapshot', 'game.query.current-event-options.v1', *announced]
                with patch('xar_autoplayer.native_session.require_game_windows_background'), \
                        self.assertRaisesRegex(UnsupportedStepError, 'game.command.select-event-option-N'):
                    driver.select_event_option_v1210(2, event_instance_id=42, expected_revision=start['revision'])
                self.assertEqual(sent, [])
                self.assertEqual(list(Path(temporary).rglob('*.claim.json')), [])
                self.assertFalse((Path(temporary)/'world-control1210').exists())
                self.assertFalse(driver._record_command.call_args.kwargs['ok'])

    def test_family_loss_after_query_preserves_original_attempt_and_unknown_without_send_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            driver, start, sent, caps = production_primitive_driver(Path(temporary))
            real_result = driver.state.wait_for_command_result
            def drop_after_query(request_id, timeout):
                result = real_result(request_id, timeout)
                if sent[-1]['step'] == FLORIN_EVENT_QUERY_STEP:
                    caps['bridge_capabilities'].remove(FLORIN_EVENT_SELECT_CAPABILITY)
                return result
            driver.state.wait_for_command_result = drop_after_query
            with patch('xar_autoplayer.native_session.require_game_windows_background'), \
                    self.assertRaisesRegex(UnsupportedStepError, 'game.command.select-event-option-N'):
                driver.select_event_option_v1210(2, event_instance_id=42, expected_revision=start['revision'])
            self.assertEqual([p['step'] for p in sent], [FLORIN_EVENT_QUERY_STEP])
            claim = next((Path(temporary)/'event-option-controls1210').glob('*.claim.json'))
            original = claim.read_bytes()
            with self.assertRaisesRegex(BridgeUnavailableError, 'never replay'):
                driver.select_event_option_v1210(2, event_instance_id=42, expected_revision=start['revision'])
            self.assertEqual(claim.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                require_florin_control_ready_v1(Path(temporary)/'driver.json', florin_full_source(start, None))
            self.assertEqual([p['step'] for p in sent], [FLORIN_EVENT_QUERY_STEP])

    def test_legacy_event_route_does_not_require_the_new_florin_family(self) -> None:
        start = frame(); start['diagnostics']['hello']['expected_ck3_version'] = '1.20.0.4'
        start['active_event']['option_count'] = 2
        changed = copy.deepcopy(start); changed['active_event'] = None
        primitive = Mock(return_value={'accepted':True, 'step':'select-event-option-2'})
        fake = SimpleNamespace(command_timeout_seconds=2.0, _driver_state_lock=threading.RLock(),
            take_snapshot_without_native_command_history=lambda: start,
            take_internal_semantic_snapshot=lambda: changed,
            _wait_for_life_advance_snapshot=lambda snapshot, predicate, **kwargs: snapshot,
            capabilities=Mock(side_effect=AssertionError('No new Florin capability check on legacy path')),
            _select_event_option_v1210_unrecorded=Mock(side_effect=AssertionError('No Florin route for legacy')),
            _execute_primitive_step=primitive)
        result = NativeHeadlessGameplayDriver._execute_event_option_step(fake, 'select-event-option-2',
            option_number=2, expected_revision=start['revision'])
        self.assertTrue(result['event_selection']['postcondition_verified'])
        primitive.assert_called_once_with('select-event-option-2',
            include_native_command_history=False, expected_revision=start['revision'])
        fake.capabilities.assert_not_called()
        fake._select_event_option_v1210_unrecorded.assert_not_called()


    def test_actual_cpp_full_reaches_existing_public_state_without_losing_signed_ids(self) -> None:
        actual = frame()
        self.assertEqual(actual['played_character']['character_id'], -2130706431)
        self.assertEqual(actual['played_character']['spouse_ids'], [0, -16777213])
        self.assertEqual(actual['pending_character_interaction']['instance_id'], -2097152000)
        binding = florin_full_source(actual, actual['revision'])
        self.assertEqual(binding.native_revision, 11)
        self.assertEqual(binding.played_character_id, -2130706431)

    def test_actual_cpp_query_submission_and_handled_rejection_round_trip(self) -> None:
        actual = frame(); source = florin_event_source(actual, 42, actual['revision'])
        query = normalize_florin_event_result(cpp('available.json'), source, FLORIN_EVENT_QUERY_STEP, None)
        self.assertEqual([row['native_option_index'] for row in query['options']], [0, 1])
        self.assertTrue(normalize_florin_event_result(cpp('submitted.json'), source, 'select-event-option-2', 1)['accepted'])
        self.assertFalse(normalize_florin_event_result(cpp('option-disabled.json'), source, 'select-event-option-2', 1)['accepted'])
        fields = florin_event_fields(source, 1795000000000)
        self.assertEqual(fields['arguments'], {'event_instance_id': 42})
        self.assertEqual(fields['event_option_control']['native_revision'], 11)

    def test_wrong_types_mixed_build_and_duplicate_authored_indices_refuse(self) -> None:
        source = florin_event_source(frame(), 42, None)
        for field, value in [('native_revision', True), ('event_instance_id', 42.0), ('accepted', 1),
                             ('executable_sha256', '0' * 64), ('native_option_index', 0), ('extra', None)]:
            raw = cpp('available.json'); raw[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_florin_event_result(raw, source, FLORIN_EVENT_QUERY_STEP, None)
        raw = cpp('available.json'); raw['options'].append(raw['options'][0].copy())
        with self.assertRaises(ValueError):
            normalize_florin_event_result(raw, source, FLORIN_EVENT_QUERY_STEP, None)
        for field, value in [('native_revision', True), ('snapshot_id', 'native:10'), ('map_ready', False)]:
            bad = frame(); bad[field] = value
            with self.assertRaises(ValueError):
                florin_full_source(bad, None)

    def test_signed_id_relaxation_cannot_escape_exact_florin_source(self) -> None:
        raw = json.loads((FIXTURES / 'full1210/full-snapshot-producer-102.json').read_bytes())
        raw['state']['schema'] = 'old-build'
        with self.assertRaises(ValueError):
            _semantic_snapshot_from_frame(raw)
        raw['state']['schema'] = 'ck3_1210_full_state_v1'; raw['state']['executable_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            _semantic_snapshot_from_frame(raw)

    def test_real_existing_driver_uses_actual_query_then_one_based_native_step_and_never_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            start = frame(); changed = copy.deepcopy(start); changed['active_event'] = None
            changed['native_revision'] = 12; changed['snapshot_id'] = 'native:12'
            calls = []
            def primitive(step, **kwargs):
                calls.append((step, kwargs))
                return {**cpp('available.json' if step == FLORIN_EVENT_QUERY_STEP else 'submitted.json'), 'backend_id': 'native-headless'}
            fake = SimpleNamespace(command_timeout_seconds=2.0,
                capabilities=lambda: event_capabilities(start), _record_command=Mock(),
                take_snapshot_without_native_command_history=lambda: start,
                take_internal_semantic_snapshot=lambda: changed,
                _wait_for_life_advance_snapshot=lambda snapshot, predicate, **kwargs: snapshot,
                _native_driver_state_path=lambda: Path(temporary) / 'driver.json', _execute_primitive_step=primitive)
            with patch('xar_autoplayer.native_session.require_game_windows_background') as quiet:
                result = NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 2, event_instance_id=42, expected_revision=start['revision'])
                self.assertTrue(result['event_selection']['postcondition_verified'])
                self.assertEqual([step for step, _ in calls], [FLORIN_EVENT_QUERY_STEP, 'select-event-option-2'])
                self.assertEqual(calls[0][1]['request_fields'], calls[1][1]['request_fields'])
                self.assertEqual(quiet.call_count, 2)
                with self.assertRaisesRegex(BridgeUnavailableError, 'never replay'):
                    NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 2, event_instance_id=42, expected_revision=start['revision'])
                with self.assertRaisesRegex(BridgeUnavailableError, 'never replay'):
                    NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 1, event_instance_id=42, expected_revision=start['revision'])
                self.assertEqual(len(calls), 2)

    def test_unknown_native_selection_keeps_original_claim_and_stops_second_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            start = frame(); calls = []
            def primitive(step, **kwargs):
                calls.append(step)
                if step == FLORIN_EVENT_QUERY_STEP: return cpp('available.json')
                raise BridgeUnavailableError('software lost ACK after send')
            fake = SimpleNamespace(command_timeout_seconds=2.0,
                capabilities=lambda: event_capabilities(start),
                _record_command=Mock(),
                take_snapshot_without_native_command_history=lambda: start,
                _native_driver_state_path=lambda: Path(temporary) / 'driver.json', _execute_primitive_step=primitive)
            with patch('xar_autoplayer.native_session.require_game_windows_background'):
                with self.assertRaisesRegex(BridgeUnavailableError, 'lost ACK'):
                    NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 2, event_instance_id=42, expected_revision=start['revision'])
                start['diagnostics']['connection_generation'] = 4
                start['diagnostics']['hello']['connection_generation'] = 4
                # Original attempt retains priority even if the new connection lacks the family.
                start['diagnostics']['hello']['capabilities'].remove(FLORIN_EVENT_SELECT_CAPABILITY)
                with self.assertRaisesRegex(BridgeUnavailableError, 'never replay'):
                    NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 2, event_instance_id=42, expected_revision=start['revision'])
            self.assertEqual(calls, [FLORIN_EVENT_QUERY_STEP, 'select-event-option-2'])
            self.assertEqual(len(list((Path(temporary) / 'event-option-controls1210').glob('*.claim.json'))), 1)
            unknown = list((Path(temporary) / 'world-control1210').rglob('*.claim.json'))
            self.assertEqual(len(unknown), 1)
            original = json.loads(unknown[0].read_bytes())
            self.assertEqual(original['step'], 'select-event-option-2')
            self.assertIn('lost ACK', original['reason'])
            with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                require_florin_control_ready_v1(Path(temporary) / 'driver.json', florin_full_source(start, None))

    def test_event_unknown_blocks_other_world_control_but_zero_effect_rejection_does_not(self) -> None:
        for outcome in ('malformed', 'indeterminate', 'no-postcondition', 'disabled'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temporary:
                start = frame(); path = Path(temporary) / 'driver.json'
                def primitive(step, **kwargs):
                    if step == FLORIN_EVENT_QUERY_STEP:
                        return cpp('available.json')
                    if outcome == 'disabled':
                        return cpp('option-disabled.json')
                    result = cpp('submitted.json')
                    if outcome == 'malformed':
                        result['native_revision'] = True
                    elif outcome == 'indeterminate':
                        result.update(status='indeterminate', accepted=False)
                    return result
                fake = SimpleNamespace(command_timeout_seconds=2.0, capabilities=lambda: event_capabilities(start), _record_command=Mock(),
                    take_snapshot_without_native_command_history=lambda: start,
                    take_internal_semantic_snapshot=lambda: start,
                    _wait_for_life_advance_snapshot=lambda snapshot, predicate, **kwargs: snapshot,
                    _native_driver_state_path=lambda: path, _execute_primitive_step=primitive)
                with patch('xar_autoplayer.native_session.require_game_windows_background'), self.assertRaises(BridgeUnavailableError):
                    NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 2, event_instance_id=42,
                        expected_revision=start['revision'])
                source = florin_full_source(start, None)
                if outcome == 'disabled':
                    require_florin_control_ready_v1(path, source)
                    self.assertEqual(list((Path(temporary) / 'world-control1210').rglob('*.claim.json')), [])
                else:
                    with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                        require_florin_control_ready_v1(path, source)
                    # A different event and a new connection cannot consume the original unknown.
                    start['active_event']['instance_id'] = 43
                    start['diagnostics']['connection_generation'] = 4
                    start['diagnostics']['hello']['connection_generation'] = 4
                    with self.assertRaisesRegex(BridgeUnavailableError, 'UNKNOWN'):
                        NativeHeadlessGameplayDriver.select_event_option_v1210(fake, 1,
                            event_instance_id=43, expected_revision=start['revision'])

    def test_existing_public_service_delegates_florin_before_old_fabricated_enabled_options(self) -> None:
        actual = frame(); actual['active_event']['options'] = []
        calls = []
        fake = SimpleNamespace(snapshot=lambda **kwargs: actual, driver=SimpleNamespace(
            select_event_option_v1210=lambda number, **kwargs: calls.append((number, kwargs)) or {'actual_native_query': True}))
        result = GameplayBridgeService.select_event_option(fake, 2, event_instance_id=42, expected_revision=actual['revision'])
        self.assertTrue(result['actual_native_query'])
        self.assertEqual(calls, [(2, {'event_instance_id': 42, 'expected_revision': actual['revision']})])

    def test_shared_quiet_guard_only_reads_and_refuses_focus_topmost_or_restored_windows(self) -> None:
        for minimized, topmost, foreground_pid, present, accepted in [
            (True, 0, 99, True, True), (False, 0, 99, True, False),
            (True, 8, 99, True, False), (True, 0, 42, True, False), (True, 0, 99, False, False),
        ]:
            gui = SimpleNamespace(IsIconic=lambda hwnd: minimized, IsWindowVisible=lambda hwnd: True,
                                  GetForegroundWindow=lambda: 9, GetWindowLong=lambda hwnd, flag: topmost)
            process = SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (1, foreground_pid if hwnd == 9 else 42))
            with patch.dict(sys.modules, {'win32gui': gui, 'win32process': process,
                                         'win32con': SimpleNamespace(GWL_EXSTYLE=-20, WS_EX_TOPMOST=8)}), \
                    patch('xar_autoplayer.native_session._visible_process_windows', return_value=[7] if present else []):
                if accepted: require_game_windows_background(42)
                else:
                    with self.assertRaises(RuntimeError): require_game_windows_background(42)
        with self.assertRaises(ValueError): require_game_windows_background(True)


class FlorinEventPublicQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_public_select_tool_uses_one_original_writer_and_independent_event_advance(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge import mcp_server
        with tempfile.TemporaryDirectory() as temporary:
            actual = frame(); changed = copy.deepcopy(actual); changed['active_event'] = None
            driver = object.__new__(NativeHeadlessGameplayDriver)
            driver.command_timeout_seconds = 2.0
            driver.capabilities = Mock(side_effect=lambda: event_capabilities(actual))
            driver.take_snapshot = Mock(side_effect=lambda **kwargs: copy.deepcopy(actual))
            driver.take_internal_semantic_snapshot = Mock(return_value=changed)
            driver._wait_for_life_advance_snapshot = Mock(return_value=changed)
            driver._native_driver_state_path = Mock(return_value=Path(temporary) / 'driver.json')
            driver._record_command = Mock()
            driver._execute_primitive_step = Mock(side_effect=lambda step, **kwargs: cpp(
                'available.json' if step == FLORIN_EVENT_QUERY_STEP else 'submitted.json'))
            with patch('xar_autoplayer.native_session.require_game_windows_background'):
                async with Client(mcp_server.create_server(driver)) as client:
                    selected = await client.session.call_tool('ck3_select_event_option', {
                        'option_number': 2, 'event_instance_id': 42, 'expected_revision': str(actual['revision'])})
            self.assertFalse(selected.is_error, str(selected))
            self.assertEqual(selected.structured_content['option_index'], 1)
            self.assertEqual(selected.structured_content['native_revision'], '11')
            self.assertTrue(selected.structured_content['event_selection']['postcondition_verified'])
            self.assertEqual(driver._record_command.call_count, 1)
            self.assertTrue(driver._record_command.call_args.kwargs['ok'])
            self.assertEqual([call.args[0] for call in driver._execute_primitive_step.call_args_list],
                             [FLORIN_EVENT_QUERY_STEP, 'select-event-option-2'])

    async def test_actual_cpp_query_reaches_existing_public_mcp_as_explicit_limited_variant(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge import mcp_server
        actual = frame()
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.command_timeout_seconds = 2.0
        driver._driver_state_lock = threading.RLock()
        driver.take_snapshot = Mock(side_effect=lambda **kwargs: copy.deepcopy(actual))
        driver._execute_primitive_step = Mock(return_value=cpp('available.json'))
        with patch('xar_autoplayer.native_session.require_game_windows_background'):
            async with Client(mcp_server.create_server(driver)) as client:
                result = await client.session.call_tool('ck3_query_current_event_window_context_v1', {
                    'event_instance_id': 42, 'expected_revision': str(actual['revision'])})
        self.assertFalse(result.is_error, str(result))
        public = result.structured_content
        self.assertEqual(public['schema'], 'ck3-florin-current-event-options-v1')
        self.assertEqual(public['native_revision'], '11')
        self.assertEqual([row['option_number'] for row in public['options']], [1, 2])
        self.assertFalse(public['saved_scopes_observed'])
        self.assertFalse(public['effect_indicators_observed'])
        self.assertFalse(public['business_acceptance_credit'])
        self.assertNotIn('current_event_window_context', public)
        self.assertEqual(json.loads(public['native_result_json']), cpp('available.json'))
        self.assertEqual(driver._execute_primitive_step.call_count, 1)

    def test_actual_public_query_refuses_source_change_and_malformed_backend_projection(self) -> None:
        actual = frame()
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.command_timeout_seconds = 2.0
        driver._execute_primitive_step = Mock(return_value=cpp('available.json'))
        altered = copy.deepcopy(actual); altered['date_raw'] += 24
        driver.take_snapshot = Mock(side_effect=[actual, altered])
        with patch('xar_autoplayer.native_session.require_game_windows_background'), self.assertRaisesRegex(BridgeUnavailableError, 'crossed'):
            driver.query_event_options_v1210(42, expected_revision=actual['revision'])
        fake = SimpleNamespace(snapshot=lambda **kwargs: actual, driver=SimpleNamespace(
            query_current_event_window_context_v1=lambda *args, **kwargs: {'schema': 'ck3-florin-current-event-options-v1', 'native_result_json': '{}'}))
        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService.query_current_event_window_context_v1(fake, 42, expected_revision=actual['revision'])


if __name__ == '__main__':
    unittest.main()
