"""Six new actual Driver/transport/sidecar branches; no Game, GUI or Native build.

Run only after the owner applies the continuity candidate. Existing v2 wire
fixtures are reused as inputs; the old matrix is not rerun.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path('Z:/ck3_mod_rewrite')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(REPO / 'ck3_autonomous_player/src'),
               str(REPO / 'ck3_autonomous_player/tests/unit')]

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.prewar_force_coalition_v2_transport import CAPABILITY, STEP
from xar_autoplayer.bridge.version_identity import CK3_12004
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot, _war
from test_ordinary_prewar_force_admission_v2 import _evidence
from test_prewar_force_transport_v2 import _response


class DriverSidecarContinuityCompound(unittest.TestCase):
    def setUp(self):
        temp_parent = HERE / 'test-temp'
        temp_parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='continuity-', dir=temp_parent)
        self.root = Path(self.temporary.name).resolve()
        self.assertEqual(self.root.parent, temp_parent.resolve())
        self.drivers = []

    def tearDown(self):
        for driver in reversed(self.drivers):
            driver.close()
        self.temporary.cleanup()

    def _harness(self, *, before_wars=None, state_root=None):
        template, declaration, _, _ = _evidence()
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            command_timeout_seconds=.02, state_dir=state_root or self.root)
        self.drivers.append(driver)
        hello = _hello('game.state.snapshot', 'game.state.declarable-wars',
                       'game.command.query-declarable-wars', 'game.command.declare-war-N', CAPABILITY)
        hello.update(bridge_version='0.1.0.4', expected_ck3_version=CK3_12004.game_version,
                     expected_ck3_sha256=CK3_12004.executable_sha256)
        endpoint.publish(hello)
        endpoint.publish(_snapshot(40, played_character=deepcopy(template['played_character']),
            date_raw=template['date_raw'], active_wars=before_wars or []))
        self._catalogue(driver, endpoint, declaration)
        before = driver.take_internal_semantic_snapshot()
        endpoint.send_hook = lambda request: endpoint.publish(_response(request, before, declaration))
        driver.query_prewar_force_coalition_coverage_v2(declaration['declaration_id'],
            expected_revision=before['revision'])
        endpoint.send_hook = None
        endpoint.frames.clear()
        return driver, endpoint, declaration, before

    def _catalogue(self, driver, endpoint, declaration):
        def answer(request):
            self.assertEqual(request['step'], 'query-declarable-wars')
            endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                'request_id': request['request_id'], 'ok': True, 'result': {
                    'step': request['step'], 'accepted': True, 'status': 'available',
                    'query_sequence': 3, 'declarable_wars': [deepcopy(declaration)]}})
        endpoint.send_hook = answer
        driver.execute_step('query-declarable-wars', expected_revision=driver.take_snapshot()['revision'])
        endpoint.send_hook = None

    def _war(self, declaration, war_id, *, opponent=None, titles=None):
        row = _war(war_id, targeted_title_ids=(deepcopy(declaration['target_title_ids'])
                    if titles is None else titles))
        row['primary_opponent_character_id'] = (declaration['target_character_id']
                    if opponent is None else opponent)
        return row

    def _publish(self, endpoint, before, revision, wars):
        endpoint.publish(_snapshot(revision, played_character=deepcopy(before['played_character']),
            date_raw=before['date_raw'], active_wars=wars))

    def _declare(self, driver, endpoint, declaration, before, wars, *, respond=True):
        def answer(request):
            self.assertEqual(request['step'], 'declare-war-' + declaration['declaration_id'])
            if respond:
                endpoint.publish({'type': 'command_result', 'protocol_version': 1,
                    'request_id': request['request_id'], 'ok': True, 'result': {
                        'step': request['step'], 'accepted': True, 'status': 'submitted'}})
            self._publish(endpoint, before, 41, wars)
        endpoint.send_hook = answer
        return driver.execute_step('declare-war-' + declaration['declaration_id'],
                                   expected_revision=driver.take_snapshot()['revision'])

    def _sidecar(self, driver):
        path = driver._native_driver_state_path().parent / 'war-declaration-continuity-v1.json'
        self.assertLessEqual(path.stat().st_size, 32768)
        return json.loads(path.read_text(encoding='utf-8'))

    def test_01_unrelated_new_war_retains_original_tuple_and_no_success(self):
        driver, endpoint, declaration, before = self._harness()
        result = self._declare(driver, endpoint, declaration, before,
            [self._war(declaration, 73, opponent=999)])
        self.assertEqual(result['war_action']['status'], 'declaration_submitted')
        self.assertFalse(result['war_action']['postcondition_verified'])
        record = self._sidecar(driver)
        self.assertEqual(record['request_id'], endpoint.frames[0]['request_id'])
        self.assertEqual(record['declaration'], declaration)
        self.assertEqual(record['before_war_ids'], [])
        self.assertEqual(record['final_cb_roles']['primary_defender_character_id'], declaration['target_character_id'])
        self.assertEqual(len(endpoint.frames), 1)

    def test_02_same_count_old_war_replaced_by_unique_actual_match(self):
        driver, endpoint, declaration, before = self._harness(before_wars=[_war(61)])
        result = self._declare(driver, endpoint, declaration, before, [self._war(declaration, 73)])
        action = result['war_action']
        self.assertEqual(action['status'], 'war_started')
        self.assertEqual(action['war_id'], 73)
        self.assertTrue(action['postcondition_verified'])
        self.assertFalse(action['casus_belli_identity_observed'])
        self.assertEqual(action['before_war_ids'], [61])
        self.assertEqual(len(endpoint.frames), 1)

    def test_03_missing_actual_target_titles_does_not_match(self):
        driver, endpoint, declaration, before = self._harness()
        result = self._declare(driver, endpoint, declaration, before,
            [self._war(declaration, 73, titles=[])])
        self.assertEqual(result['war_action']['status'], 'declaration_submitted')
        self.assertFalse(result['war_action']['postcondition_verified'])
        self.assertIsNone(result['war_action']['war_id'])
        self.assertEqual(len(endpoint.frames), 1)

    def test_04_two_matching_new_wars_remain_ambiguous(self):
        driver, endpoint, declaration, before = self._harness()
        result = self._declare(driver, endpoint, declaration, before,
            [self._war(declaration, 73), self._war(declaration, 74)])
        self.assertEqual(result['war_action']['status'], 'declaration_submitted')
        self.assertEqual(result['war_action']['reason'], 'ambiguous_new_wars')
        self.assertFalse(result['war_action']['postcondition_verified'])
        self.assertEqual(len(endpoint.frames), 1)

    def test_05_timeout_collects_only_original_response_without_sending(self):
        driver, endpoint, declaration, before = self._harness()
        wars = [self._war(declaration, 73)]
        with self.assertRaisesRegex(BridgeUnavailableError, 'timed out'):
            self._declare(driver, endpoint, declaration, before, wars, respond=False)
        original = deepcopy(endpoint.frames[0])
        self.assertEqual(self._sidecar(driver)['request_id'], original['request_id'])
        endpoint.send_hook = None
        endpoint.publish({'type': 'command_result', 'protocol_version': 1,
            'request_id': original['request_id'], 'ok': True, 'result': {
                'step': original['step'], 'accepted': True, 'status': 'submitted'}})
        self._publish(endpoint, before, 42, wars)
        continuity = driver.take_snapshot()['war_declaration_continuity_v1']
        self.assertEqual(continuity['status'], 'war_started')
        self.assertEqual(continuity['request_id'], original['request_id'])
        self.assertEqual(continuity['war_id'], 73)
        self.assertEqual(len(endpoint.frames), 1)

    def test_06_sdk_restart_preserves_original_sidecar_and_blocks_resend(self):
        driver, endpoint, declaration, before = self._harness()
        with self.assertRaisesRegex(BridgeUnavailableError, 'timed out'):
            self._declare(driver, endpoint, declaration, before, [], respond=False)
        original = deepcopy(endpoint.frames[0])
        driver.close()
        self.drivers.remove(driver)
        replacement_endpoint = FakeEndpoint(endpoint.pipe_name)
        replacement = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=replacement_endpoint,
            command_timeout_seconds=.02, state_dir=self.root)
        self.drivers.append(replacement)
        hello = _hello('game.state.snapshot', 'game.state.declarable-wars',
                       'game.command.query-declarable-wars', 'game.command.declare-war-N', CAPABILITY)
        hello.update(bridge_version='0.1.0.4', expected_ck3_version=CK3_12004.game_version,
                     expected_ck3_sha256=CK3_12004.executable_sha256)
        replacement_endpoint.publish(hello)
        self._publish(replacement_endpoint, before, 42, [])
        self._catalogue(replacement, replacement_endpoint, declaration)
        count_before = len(replacement_endpoint.frames)
        with self.assertRaisesRegex(BridgeUnavailableError, 'original declaration remains unresolved'):
            replacement.execute_step('declare-war-' + declaration['declaration_id'],
                                     expected_revision=replacement.take_snapshot()['revision'])
        self.assertEqual(len(replacement_endpoint.frames), count_before)
        self.assertEqual(self._sidecar(replacement)['request_id'], original['request_id'])
        self.assertFalse(self._sidecar(replacement)['request_retried'])
        self.assertNotEqual(replacement.take_snapshot()['war_declaration_continuity_v1']['status'], 'war_started')


if __name__ == '__main__':
    unittest.main(verbosity=2)
