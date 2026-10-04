"""Explicit typed movement uses native validation outside strategy target ads."""
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
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12003
from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot, _war

ARMY = 83_886_341
TARGET = 1513
STEP = f'move-army-{ARMY}-to-{TARGET}'


def fixture(*, omit_capability=None, paused=True, map_ready=True,
            owner=33388, controllable=True, army_state='regular',
            retreating=False, in_combat=False):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1,
    )
    caps = ['game.state.snapshot', 'game.state.war-objectives',
            'game.state.army-routes', 'game.command.move-army-N-to-N']
    if omit_capability in caps:
        caps.remove(omit_capability)
    hello = _hello(*caps)
    hello.update(expected_ck3_version=CK3_12003.game_version,
                 expected_ck3_sha256=CK3_12003.executable_sha256)
    endpoint.publish(hello)
    army = _army(ARMY, province_id=1506, owner_character_id=owner,
                 controllable=controllable, army_state=army_state,
                 route_province_ids=[], combat_id=None, retreating=retreating,
                 in_combat=in_combat)
    before = _snapshot(
        40, date_raw=53_147_160, paused=paused, map_ready=map_ready,
        played_character={'character_id': 33388, 'alive': True},
        player_armies=[army], active_wars=[_war(
            allied_armies=[army], war_objective_province_ids=[1527],
        )],
    )
    endpoint.publish(before)
    after = copy.deepcopy(before)
    after['snapshot_id'] = 'native:41'
    after['revision'] = 41
    for row in [after['state']['player_armies'][0],
                after['state']['active_wars'][0]['allied_armies'][0]]:
        row.update(move_target_province_id=TARGET, route_province_ids=[TARGET],
                   army_state='moving')

    def answer(frame):
        if frame.get('type') == 'execute_step':
            endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                              'request_id': frame['request_id'], 'ok': True,
                              'result': {'step': frame['step'], 'accepted': True,
                                         'status': 'submitted'}})
            endpoint.publish(after)
    endpoint.send_hook = answer
    return driver, endpoint, before, after, hello


class TypedGenericProvinceMoveTests(unittest.TestCase):
    def setup_fixture(self, **kwargs):
        value = fixture(**kwargs)
        self.addCleanup(value[0].close)
        return value

    def test_service_explicit_typed_generic_move_observes_original_route(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        self.assertNotIn(STEP, driver.capabilities()['action_steps'])
        before = driver.take_snapshot()
        result = GameplayBridgeService(driver).move_army(
            ARMY, TARGET, expected_revision=before['revision'],
        )
        self.assertTrue(result['accepted'])
        self.assertEqual(result['war_action']['status'], 'moving')
        self.assertTrue(result['war_action']['postcondition_verified'])
        self.assertEqual(result['submitted_native_revision'], 40)
        self.assertEqual(result['submitted_snapshot_id'], 'native:40')
        self.assertEqual(result['player_armies'][0]['army_id'], ARMY)
        calls = [f for f in endpoint.frames if f.get('type') == 'execute_step']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['step'], STEP)
        self.assertEqual(calls[0]['expected_revision'], 40)
        self.assertEqual(driver.take_snapshot()['date_raw'], before['date_raw'])

    def test_optional_revision_keeps_existing_fresh_source_behavior(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        self.assertTrue(GameplayBridgeService(driver).move_army(ARMY, TARGET)['accepted'])
        self.assertEqual(len([f for f in endpoint.frames if f.get('type') == 'execute_step']), 1)

    def test_missing_family_or_route_capability_rejects_without_send(self):
        for cap in ('game.command.move-army-N-to-N', 'game.state.army-routes'):
            with self.subTest(cap=cap):
                driver, endpoint, _, _, _ = self.setup_fixture(omit_capability=cap)
                with self.assertRaises(UnsupportedStepError):
                    GameplayBridgeService(driver).move_army(ARMY, TARGET)
                self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_stale_expected_revision_rejects_without_send(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            GameplayBridgeService(driver).move_army(
                ARMY, TARGET, expected_revision=driver.take_snapshot()['revision'] + 1,
            )
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_nonowned_or_not_controllable_rejects_without_send(self):
        for options in ({'owner': 808}, {'controllable': False}):
            with self.subTest(options=options):
                driver, endpoint, _, _, _ = self.setup_fixture(**options)
                with self.assertRaises(BridgeUnavailableError):
                    GameplayBridgeService(driver).move_army(ARMY, TARGET)
                self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_unpaused_unready_combat_and_retreat_reject_without_send(self):
        for options in ({'paused': False}, {'map_ready': False},
                        {'army_state': 'combat'}, {'army_state': 'retreating'},
                        {'retreating': True}, {'in_combat': True}):
            with self.subTest(options=options):
                driver, endpoint, _, _, _ = self.setup_fixture(**options)
                with self.assertRaises(BridgeUnavailableError):
                    GameplayBridgeService(driver).move_army(ARMY, TARGET)
                self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_invalid_ids_reject_without_send(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        for army_id, province in ((True, TARGET), (-1, TARGET), (2**31, TARGET),
                                  (ARMY, 0), (ARMY, True), (ARMY, 2**31),
                                  (str(ARMY), TARGET), (ARMY, '01513')):
            with self.subTest(ids=(army_id, province)), self.assertRaises(ValueError):
                GameplayBridgeService(driver).move_army(army_id, province)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))

    def test_native_province_rejection_is_retained(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        def reject(frame):
            if frame.get('type') == 'execute_step':
                endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                                  'request_id': frame['request_id'], 'ok': False,
                                  'error': 'CK3 destination province was not found'})
        endpoint.send_hook = reject
        with self.assertRaisesRegex(BridgeUnavailableError, 'province was not found'):
            GameplayBridgeService(driver).move_army(ARMY, TARGET)

    def test_native_army_eligibility_rejection_keeps_deferred_result(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        def reject(frame):
            if frame.get('type') == 'execute_step':
                endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                                  'request_id': frame['request_id'], 'ok': False,
                                  'error': 'CK3 army state rejects movement'})
        endpoint.send_hook = reject
        result = GameplayBridgeService(driver).move_army(ARMY, TARGET)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['war_action']['status'], 'move_deferred')

    def test_ack_without_observed_route_does_not_verify_move(self):
        driver, _, _, after, _ = self.setup_fixture()
        after['state']['player_armies'][0]['route_province_ids'] = [1527]
        with self.assertRaisesRegex(BridgeUnavailableError, 'did not observe'):
            GameplayBridgeService(driver).move_army(ARMY, TARGET)

    def test_changed_owner_or_full_id_after_submit_is_rejected(self):
        for key, value in (('owner_character_id', 808), ('army_id', ARMY & 0xFFFFFF)):
            with self.subTest(key=key):
                driver, _, _, after, _ = self.setup_fixture()
                after['state']['player_armies'][0][key] = value
                with self.assertRaisesRegex(BridgeUnavailableError, 'paused session or army ownership'):
                    GameplayBridgeService(driver).move_army(ARMY, TARGET)

    def test_date_advance_or_reconnect_after_submit_is_rejected(self):
        driver, _, _, after, _ = self.setup_fixture()
        after['state']['date_raw'] += 24
        with self.assertRaisesRegex(BridgeUnavailableError, 'paused session or army ownership'):
            GameplayBridgeService(driver).move_army(ARMY, TARGET)
        driver2, endpoint, _, after2, hello = self.setup_fixture()
        def reconnect(frame):
            if frame.get('type') == 'execute_step':
                endpoint.publish({**hello, 'session_generation': 1})
                endpoint.publish(after2)
                endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                                  'request_id': frame['request_id'], 'ok': True,
                                  'result': {'step': frame['step'], 'accepted': True,
                                             'status': 'submitted'}})
        endpoint.send_hook = reconnect
        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService(driver2).move_army(ARMY, TARGET)

    def test_raw_nonadvertised_move_literal_remains_rejected(self):
        driver, endpoint, _, _, _ = self.setup_fixture()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(STEP)
        self.assertFalse(any(f.get('type') == 'execute_step' for f in endpoint.frames))


class TypedGenericProvinceMoveRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_mcp_typed_generic_move_sends_one_command(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        driver, endpoint, _, _, _ = fixture()
        self.addCleanup(driver.close)
        before = driver.take_snapshot()
        self.assertNotIn(STEP, driver.capabilities()['action_steps'])
        async with Client(create_server(driver)) as client:
            reply = await client.call_tool('ck3_move_army', {
                'army_id': ARMY, 'target_province_id': TARGET,
                'expected_revision': before['revision'],
            })
        self.assertFalse(reply.is_error)
        result = reply.structured_content
        self.assertEqual(result['war_action']['status'], 'moving')
        self.assertEqual(result['army_id'], ARMY)
        self.assertEqual(result['target_province_id'], TARGET)
        self.assertTrue(result['war_action']['postcondition_verified'])
        calls = [f for f in endpoint.frames if f.get('type') == 'execute_step']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['step'], STEP)
        self.assertEqual(calls[0]['expected_revision'], 40)


if __name__ == '__main__':
    unittest.main()
