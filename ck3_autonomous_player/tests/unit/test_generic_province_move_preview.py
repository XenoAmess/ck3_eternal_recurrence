"""Generic read-only army previews keep native validation and paused identity."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.bridge.war_contract import PREVIEW_MOVE_ARMY_CAPABILITY
from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot, _war


ARMY_ID = 83_886_341
STEP = f'preview-move-army-{ARMY_ID}-to-1513'


def fixture(*, paused=True, controllable=True, advertised=True, wars=True):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.2,
    )
    caps = ['game.state.snapshot', 'game.state.war-objectives',
            'game.state.army-routes', 'game.command.move-army-N-to-N']
    if advertised:
        caps.append(PREVIEW_MOVE_ARMY_CAPABILITY)
    hello = _hello(*caps)
    hello.update(expected_ck3_version=CK3_12003.game_version,
                 expected_ck3_sha256=CK3_12003.executable_sha256)
    endpoint.publish(hello)
    player = _army(ARMY_ID, province_id=1506, controllable=controllable,
                   owner_character_id=33388, army_state='regular',
                   route_province_ids=[], combat_id=None, retreating=False)
    state = _snapshot(
        40, paused=paused, date_raw=53_147_160,
        played_character={'character_id': 33388, 'alive': True},
        player_armies=[player],
        active_wars=[_war(allied_armies=[player],
                         war_objective_province_ids=[1527])] if wars else [],
    )
    endpoint.publish(state)
    route = {'status': 'available', 'army_id': ARMY_ID,
             'origin_province_id': 1506, 'target_province_id': 1513,
             'route_province_ids': [1513]}

    def answer(frame):
        if frame.get('type') == 'execute_step':
            endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                              'request_id': frame['request_id'], 'ok': True,
                              'result': {'step': frame['step'], 'accepted': True,
                                         'status': 'available',
                                         'route_preview': copy.deepcopy(route)}})
    endpoint.send_hook = answer
    return driver, endpoint, state, route, hello


class GenericProvinceMovePreviewTests(unittest.TestCase):
    def setup_fixture(self, **kwargs):
        value = fixture(**kwargs)
        self.addCleanup(value[0].close)
        return value

    def test_nonadvertised_province_uses_native_preview_with_full_cunit(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        before = driver.take_snapshot()
        self.assertNotIn(STEP, driver.capabilities()['action_steps'])
        result = driver.execute_step(STEP, expected_revision=before['revision'])
        self.assertEqual(result['route_preview']['army_id'], ARMY_ID)
        self.assertEqual(result['route_preview']['target_province_id'], 1513)
        self.assertEqual(result['queried_snapshot_id'], before['snapshot_id'])
        self.assertEqual(result['queried_connection_generation'],
                         before['diagnostics']['connection_generation'])
        after = driver.take_snapshot()
        self.assertEqual(after['date_raw'], before['date_raw'])
        self.assertEqual(after['player_armies'], before['player_armies'])
        calls = [f for f in endpoint.frames if f.get('type') == 'execute_step']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['step'], STEP)
        self.assertEqual(calls[0]['expected_revision'], 40)

    def test_preview_does_not_require_an_active_war(self):
        driver, _, _, _, _ = self.setup_fixture(wars=False)
        self.assertNotIn(STEP, driver.capabilities()['action_steps'])
        self.assertTrue(driver.execute_step(STEP)['accepted'])

    def test_missing_native_capability_rejects_without_send(self):
        driver, endpoint, _, _, _ = self.setup_fixture(advertised=False)
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(STEP)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_unpaused_and_uncontrollable_reject_without_send(self):
        for options in ({'paused': False}, {'controllable': False}):
            with self.subTest(options=options):
                driver, endpoint, _, _, _ = self.setup_fixture(**options)
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(STEP)
                self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_stale_expected_revision_rejects_without_send(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        revision = driver.take_snapshot()['revision']
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            driver.execute_step(STEP, expected_revision=revision + 1)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_noncanonical_or_invalid_ids_reject_without_send(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        for step in (f'preview-move-army-0{ARMY_ID}-to-1513',
                     f'preview-move-army-{ARMY_ID}-to-01513',
                     f'preview-move-army-{ARMY_ID}-to-0',
                     f'preview-move-army-{ARMY_ID}-to-2147483648',
                     'preview-move-army-2147483648-to-1513'):
            with self.subTest(step=step), self.assertRaises(UnsupportedStepError):
                driver.execute_step(step)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_native_destination_rejection_is_retained(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        def reject(frame):
            if frame.get('type') == 'execute_step':
                endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                                  'request_id': frame['request_id'], 'ok': False,
                                  'error': 'CK3 destination province was not found'})
        endpoint.send_hook = reject
        with self.assertRaisesRegex(BridgeUnavailableError, 'province was not found'):
            driver.execute_step(STEP)

    def test_native_route_full_id_mismatch_is_rejected(self):
        driver, _, _, route, _ = self.setup_fixture()
        route['army_id'] = ARMY_ID & 0xFFFFFF
        with self.assertRaisesRegex(BridgeUnavailableError, 'malformed route_preview'):
            driver.execute_step(STEP)

    def test_changed_native_connection_generation_is_rejected(self):
        driver, endpoint, state, _, hello = self.setup_fixture()
        answer = endpoint.send_hook
        def reconnect(frame):
            answer(frame)
            if frame.get('type') == 'execute_step':
                endpoint.publish({**hello, 'session_generation': 1})
                endpoint.publish(state)
        endpoint.send_hook = reconnect
        # A new hello invalidates the old pending command result before the
        # route can be trusted, or the final paused-frame check rejects it.
        with self.assertRaisesRegex(
            BridgeUnavailableError, 'command_result timed out|snapshot revision'
        ):
            driver.execute_step(STEP)

    def test_actual_move_to_nonadvertised_province_remains_rejected(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        move = f'move-army-{ARMY_ID}-to-1513'
        self.assertNotIn(move, driver.capabilities()['action_steps'])
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(move)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))


class GenericProvinceMovePreviewRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_mcp_accepts_canonical_nonadvertised_preview(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        driver, endpoint, _, _, _ = fixture()
        self.addCleanup(driver.close)
        before = driver.take_snapshot()
        self.assertNotIn(STEP, driver.capabilities()['action_steps'])
        async with Client(create_server(driver)) as client:
            reply = await client.call_tool('ck3_execute_step', {
                'step': STEP, 'expected_revision': before['revision'],
            })
        self.assertFalse(reply.is_error)
        self.assertEqual(reply.structured_content['route_preview']['army_id'], ARMY_ID)
        self.assertEqual(reply.structured_content['route_preview']['target_province_id'], 1513)
        calls = [f for f in endpoint.frames if f.get('type') == 'execute_step']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['step'], STEP)


if __name__ == '__main__':
    unittest.main()
