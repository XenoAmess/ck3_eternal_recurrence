"""Forced long-path and service-entry offline regressions; no runtime proof."""
from pathlib import Path
import copy
import hashlib
import json
import tempfile
import unittest

import test_player_control_v1 as flow_fixtures
import test_player_control_readonly_capability_v1 as readonly_fixtures
from xar_autoplayer.bridge import player_control_driver_v1 as driver_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.player_control_contract_v1 import ACTIONS
from xar_autoplayer.bridge.service import GameplayBridgeService


def fixture_directory():
    root = Path(tempfile.mkdtemp(prefix='lyd-pc-long-'))
    print('LYD_PLAYER_CONTROL_LONG_PATH_ARTIFACTS=' + str(root))
    directory = driver_module._file(root / ('forced-' + 'x' * 100) / ('fixture-' + 'y' * 50))
    directory.mkdir(parents=True)
    return directory


def durable(directory):
    directory = driver_module._file(directory)
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob('*')
            if path.is_file() and path.name.endswith(('.flow.json', '.claim.json', '.completed.json'))}


def all_files(directory):
    directory = driver_module._file(directory)
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob('*') if path.is_file()}


class LongPathAndServiceEntryTests(unittest.TestCase):
    def test_unknown_long_path_claim_survives_reconnect_revision_and_signature_retirement(self):
        directory = fixture_directory()
        self.assertEqual(driver_module._file(directory), directory)
        with readonly_fixtures.driver_sources():
            driver = readonly_fixtures.OfflinePartialDriver(directory)
            driver.partial_mode = False
            first = driver.query_player_control_context_v1(expected_revision=72)
            driver.missing_result_action = 'open_pause_menu'
            result = driver.request_player_control_v1('open_pause_menu', expected_revision=72,
                expected_control_context_signature=first['control_context_signature'], candidate_character_id=None)
            self.assertTrue(result['claim_consumed'])
            self.assertEqual(result['status'], 'dispatch_unknown_claimed')
            self.assertFalse(result['retry_authorized'])
            claim = Path(result['claim_path'])
            self.assertGreater(len(str(claim).removeprefix('\\\\?\\')), 260)
            self.assertTrue(claim.is_file())
            retained = durable(directory)
            self.assertEqual(sum(name.endswith('.claim.json') for name in retained), 1)
            self.assertEqual(sum(name.endswith('.flow.json') for name in retained), 1)

            reconnected = readonly_fixtures.OfflinePartialDriver(directory)
            reconnected.partial_mode = False
            reconnected.revision = reconnected.native_revision = 73
            profile = {'guard': {'target': {'pid': 43}},
                       'player_control_source_inventory': {'sha256': 'b' * 64}}
            driver_module.restore_pending_authorization_v1(reconnected, profile)
            self.assertTrue(reconnected._player_control_authorization_blocked_v1)
            fresh = reconnected.query_player_control_context_v1(expected_revision=73)
            self.assertEqual(durable(directory), retained)
            sent = len(reconnected.sent)
            with self.assertRaisesRegex(BridgeUnavailableError, 'stage already consumed'):
                reconnected.request_player_control_v1('open_pause_menu', expected_revision=73,
                    expected_control_context_signature=fresh['control_context_signature'], candidate_character_id=None)
            self.assertEqual(len(reconnected.sent), sent)
            self.assertEqual(durable(directory), retained)

            history = copy.deepcopy(reconnected._command_history)
            files = all_files(directory)
            with self.assertRaises(ValueError):
                reconnected.query_player_control_context_v1(expected_revision=True)
            self.assertEqual(reconnected._player_control_contexts, {})
            for action in ACTIONS:
                candidate = None if action in ACTIONS[:2] else flow_fixtures.DESTINATION
                with self.subTest(action=action), self.assertRaisesRegex(BridgeUnavailableError, 'latest eligible backend query'):
                    reconnected.request_player_control_v1(action, expected_revision=73,
                        expected_control_context_signature=fresh['control_context_signature'], candidate_character_id=candidate)
            self.assertTrue(reconnected._player_control_authorization_blocked_v1)
            self.assertEqual(reconnected._command_history, history)
            self.assertEqual(len(reconnected.sent), sent)
            self.assertEqual(all_files(directory), files)

    def test_service_bad_query_arguments_retire_signature_without_touching_once_or_files(self):
        directory = fixture_directory()
        with readonly_fixtures.driver_sources():
            driver = readonly_fixtures.OfflinePartialDriver(directory)
            driver.partial_mode = False
            first = driver.query_player_control_context_v1(expected_revision=72)
            claimed = driver.request_player_control_v1('open_pause_menu', expected_revision=72,
                expected_control_context_signature=first['control_context_signature'], candidate_character_id=None)
            self.assertTrue(claimed['claim_consumed'])
            fresh = driver.query_player_control_context_v1(expected_revision=72)
            signature = fresh['control_context_signature']
            self.assertIn(signature, driver._player_control_contexts)
            service = GameplayBridgeService(driver)
            files = all_files(directory)
            history = copy.deepcopy(driver._command_history)
            sent = len(driver.sent)
            with self.assertRaises(ValueError):
                service.query_player_control_context_v1(expected_revision=True)
            self.assertEqual(driver._player_control_contexts, {})
            for action in ACTIONS:
                candidate = None if action in ACTIONS[:2] else flow_fixtures.DESTINATION
                with self.subTest(action=action), self.assertRaisesRegex(BridgeUnavailableError, 'latest eligible backend query'):
                    service.request_player_control_v1(action, expected_revision=72,
                        expected_control_context_signature=signature, candidate_character_id=candidate)
            self.assertTrue(driver._player_control_authorization_blocked_v1)
            self.assertEqual(driver._command_history, history)
            self.assertEqual(len(driver.sent), sent)
            self.assertEqual(all_files(directory), files)


if __name__ == '__main__':
    unittest.main()
