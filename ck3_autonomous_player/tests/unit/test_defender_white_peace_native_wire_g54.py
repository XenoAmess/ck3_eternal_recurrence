from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


FIXTURES = PROJECT_ROOT / 'tests/fixtures/native_12003/defender_white_peace_g54'
NATIVE_REVISION = 100
DATE_RAW = 53_171_400
QUERY_CAPABILITY = 'game.command.query-war-termination-options-N'
OFFER_CAPABILITY = 'game.command.offer-white-peace-N'


def _packet(name: str) -> dict[str, object]:
    """Consume the genuine production reader/serializer/submit output unchanged."""
    path = FIXTURES / (name + '.json')
    if not path.is_file():
        raise AssertionError(f'production-native fixture is missing: {path}')
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise AssertionError(f'production-native fixture is not an object: {path}')
    return value


def _inner(packet: dict[str, object]) -> dict[str, object]:
    result = packet.get('result', packet)
    if not isinstance(result, dict):
        raise AssertionError('native fixture result must be an object')
    return result


class _NativeWireEndpoint:
    """Only the transport and independent paused snapshot are fixture seams."""

    def __init__(self, options_packet, action_packet, *, remove_war=False) -> None:
        self.pipe_name = r'\\.\pipe\xar_defender_white_peace_wire_fixture'
        self.options_packet = options_packet
        self.action_packet = action_packet
        self.remove_war = remove_war
        self.frames = []
        self.on_frame = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def snapshot(self, revision: int, *, active: bool = True) -> dict[str, object]:
        options = _inner(self.options_packet)['war_termination_options']
        war = {
            name: options[name]
            for name in ('war_id', 'player_side', 'player_is_primary_war_leader', 'player_relative_war_score')
        }
        war.update({
            'primary_opponent_character_id': 42,
            'enemy_primary_default_raise_province_id': None,
            'allied_armies': [], 'enemy_armies': [],
            'war_objective_province_ids': [], 'objective_province_states': [],
            'targeted_title_ids': [2128],
        })
        return {
            'type': 'state_snapshot', 'protocol_version': 1,
            'snapshot_id': f'native:{revision}', 'revision': revision,
            'state': {
                'phase': 'map_hud', 'date': '1066.9.15', 'date_raw': DATE_RAW,
                'speed': 1, 'paused': True, 'map_ready': True,
                'played_character': {'character_id': 29829, 'alive': True},
                'active_event': None, 'pending_character_interaction': None,
                'history': [], 'one_life_settlement': None,
                'active_wars': [war] if active else [], 'player_armies': [],
            },
        }

    def send(self, frame) -> None:
        self.frames.append(copy.deepcopy(frame))
        if frame.get('type') != 'execute_step':
            return
        war_id = _inner(self.options_packet)['war_termination_options']['war_id']
        if frame['step'] == f'query-war-termination-options-{war_id}':
            packet = self.options_packet
        elif frame['step'] == f'offer-white-peace-{war_id}':
            packet = self.action_packet
            if packet is None:
                raise AssertionError('an unavailable option reached the native sender')
            if self.remove_war:
                self.publish(self.snapshot(NATIVE_REVISION + 1, active=False))
        else:
            raise AssertionError(f'consumer requested an extra query/action: {frame["step"]}')
        # Rebind transport request_id only; never alter a native result or error.
        if 'ok' in packet:
            reply = copy.deepcopy(packet)
            reply.update({'type': 'command_result', 'protocol_version': 1, 'request_id': frame['request_id']})
        else:
            reply = {
                'type': 'command_result', 'protocol_version': 1,
                'request_id': frame['request_id'], 'ok': True,
                'result': copy.deepcopy(packet),
            }
        self.publish(reply)

    def close(self) -> None:
        pass

    def transport_error(self) -> str | None:
        return None


def _driver(options_name='options-legal', action_name='action-submitted', *, remove_war=False):
    endpoint = _NativeWireEndpoint(
        _packet(options_name), _packet(action_name) if action_name else None,
        remove_war=remove_war,
    )
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.2)
    endpoint.publish({
        'type': 'hello', 'protocol_version': 1, 'bridge_version': '0.1.0',
        'pid': 4545, 'session_generation': 0,
        'game_version': '1.20.0.3',
        'executable_sha256': '94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6',
        'capabilities': ['game.state.snapshot', QUERY_CAPABILITY, OFFER_CAPABILITY],
    })
    endpoint.publish(endpoint.snapshot(NATIVE_REVISION))
    return driver, endpoint


def _commands(endpoint):
    return [frame for frame in endpoint.frames if frame.get('type') == 'execute_step']


def _assert_proposal_input(test, result):
    options = result['war_termination_options']
    native_options = _inner(_packet('options-legal'))['war_termination_options']
    # The public normalizer adds source provenance; preserve every native field.
    test.assertEqual({key: options[key] for key in native_options}, native_options)
    test.assertEqual(options['player_side'], 'defender')
    test.assertEqual(options['player_relative_war_score'], 7)
    test.assertEqual(options['active_casus_belli_identity'], {
        'database_index': 17, 'canonical_key': 'individual_county_de_jure_cb',
    })
    wp = options['options']['white_peace']
    test.assertTrue(wp['available'])
    test.assertEqual(wp['ai_acceptance'], {'raw': 163736, 'scale': 100000})
    test.assertFalse(wp['terms_observable'])
    test.assertEqual(wp['recipient_response']['status'], 'unavailable')
    test.assertIsNone(wp['recipient_response']['decision_status_raw'])
    test.assertIsNone(wp['recipient_response']['would_accept_now'])


def _assert_submission(test, result, *, remove_war):
    test.assertTrue(result['accepted'])
    test.assertEqual(result['status'], 'submitted')
    termination = result['war_termination_result']
    test.assertEqual(termination['status'], 'applied' if remove_war else 'submitted_pending')
    test.assertEqual(termination['war_id_absent_after_ack'], remove_war)
    test.assertIsNone(termination['recipient_decision_status_raw'])
    test.assertIsNone(termination['recipient_would_accept_now'])
    test.assertEqual(termination['player_side'], 'defender')
    test.assertEqual(termination['recipient_ai_acceptance_raw'], 163736)


class DefenderWhitePeaceNativeWireTests(unittest.TestCase):
    def test_actual_driver_service_publishes_and_submits_without_terms_or_final_answer(self):
        for remove_war in (False, True):
            with self.subTest(remove_war=remove_war):
                driver, endpoint = _driver(remove_war=remove_war)
                try:
                    service = GameplayBridgeService(driver)
                    war_id = _inner(endpoint.options_packet)['war_termination_options']['war_id']
                    queried = service.query_war_termination_options(war_id, expected_revision=service.snapshot()['revision'])
                    _assert_proposal_input(self, queried)
                    self.assertIn(f'offer-white-peace-{war_id}', service.capabilities()['action_steps'])
                    submitted = service.offer_white_peace(war_id, expected_revision=service.snapshot()['revision'])
                    _assert_submission(self, submitted, remove_war=remove_war)
                    self.assertEqual([row['step'] for row in _commands(endpoint)], [
                        f'query-war-termination-options-{war_id}', f'offer-white-peace-{war_id}',
                    ])
                    self.assertEqual(_commands(endpoint)[0]['expected_revision'], NATIVE_REVISION)
                    self.assertEqual(_commands(endpoint)[1]['expected_revision'], NATIVE_REVISION)
                finally:
                    driver.close()

    def test_native_cansend_false_is_not_published_and_final_native_rejection_survives(self):
        driver, endpoint = _driver('options-cansend-false', None)
        try:
            service = GameplayBridgeService(driver)
            war_id = _inner(endpoint.options_packet)['war_termination_options']['war_id']
            queried = service.query_war_termination_options(war_id, expected_revision=service.snapshot()['revision'])
            self.assertFalse(queried['war_termination_options']['options']['white_peace']['available'])
            self.assertNotIn(f'offer-white-peace-{war_id}', service.capabilities()['action_steps'])
            with self.assertRaises(UnsupportedStepError):
                service.offer_white_peace(war_id, expected_revision=service.snapshot()['revision'])
            self.assertEqual(len(_commands(endpoint)), 1)
        finally:
            driver.close()
        driver, endpoint = _driver(action_name='action-final-rejected')
        try:
            service = GameplayBridgeService(driver)
            war_id = _inner(endpoint.options_packet)['war_termination_options']['war_id']
            service.query_war_termination_options(war_id, expected_revision=service.snapshot()['revision'])
            self.assertIn(f'offer-white-peace-{war_id}', service.capabilities()['action_steps'])
            with self.assertRaises(BridgeUnavailableError) as caught:
                service.offer_white_peace(war_id, expected_revision=service.snapshot()['revision'])
            self.assertEqual(caught.exception.native_error, endpoint.action_packet['error'])
            self.assertEqual(len(_commands(endpoint)), 2)
        finally:
            driver.close()


class DefenderWhitePeaceRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_mcp_consumes_genuine_wire_and_preserves_pending_applied_rejection(self):
        from mcp import Client

        for action_name, remove_war in (('action-submitted', False), ('action-submitted', True), ('action-final-rejected', False)):
            with self.subTest(action=action_name, remove_war=remove_war):
                driver, endpoint = _driver(action_name=action_name, remove_war=remove_war)
                try:
                    war_id = _inner(endpoint.options_packet)['war_termination_options']['war_id']
                    server = create_server(driver)
                    async with Client(server) as client:
                        listed = await client.list_tools()
                        for name in ('ck3_query_war_termination_options', 'ck3_offer_white_peace'):
                            self.assertTrue(any(tool.name == name for tool in listed.tools))
                        queried = await client.call_tool('ck3_query_war_termination_options', {
                            'war_id': war_id, 'expected_revision': driver.take_snapshot()['revision'],
                        })
                        self.assertFalse(queried.is_error)
                        _assert_proposal_input(self, queried.structured_content)
                        sent = await client.call_tool('ck3_offer_white_peace', {
                            'war_id': war_id, 'expected_revision': driver.take_snapshot()['revision'],
                        })
                    if action_name == 'action-final-rejected':
                        self.assertTrue(sent.is_error)
                    else:
                        self.assertFalse(sent.is_error)
                        _assert_submission(self, sent.structured_content, remove_war=remove_war)
                    self.assertEqual([row['step'] for row in _commands(endpoint)], [
                        f'query-war-termination-options-{war_id}', f'offer-white-peace-{war_id}',
                    ])
                finally:
                    driver.close()


if __name__ == '__main__':
    unittest.main()
