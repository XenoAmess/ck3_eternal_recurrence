"""A real primitive rejection preserves actual packets and never permits replay."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import military_reinforcement_12004 as action
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from test_military_reinforcement_12004 import snapshot
from test_military_reinforcement_transport_12004 import Endpoint, State


class RejectingState(State):
    def wait_for_command_result(self, request_id, timeout):
        request = self.endpoint.sent[-1]
        if request['step'] == 'inspect-gui-window-tree-v1':
            return super().wait_for_command_result(request_id, timeout)
        self.actual_rejection = dict(type='command_result', request_id=request_id,
            ok=False, error='unsupported native gameplay step')
        return copy.deepcopy(self.actual_rejection)


class MilitaryReinforcementRejectionEvidenceTests(unittest.TestCase):
    def test_actual_rejected_packet_and_result_survive_without_retry_or_handler_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            endpoint = Endpoint()
            driver = NativeHeadlessGameplayDriver(endpoint=endpoint, state_dir=temporary)
            driver.state = RejectingState(endpoint)
            with patch.object(driver, 'take_snapshot', side_effect=snapshot):
                with self.assertRaisesRegex(BridgeUnavailableError, 'unsupported native gameplay step'):
                    action.set_fixed_military_reinforcement_12004(driver, desired_enabled=False, expected_revision=110)
                directory = driver._native_driver_state_path().parent / 'military-reinforcement-actions'
                claims = list(directory.glob('*.claim.json'))
                self.assertEqual(len(claims), 1)
                claim = claims[0]
                saved = json.loads(claim.with_suffix('.failure.json').read_text(encoding='utf-8'))
                self.assertEqual(len(endpoint.sent), 2)
                self.assertEqual(saved['native_request_frame'], endpoint.sent[-1])
                self.assertEqual(saved['native_request_frame']['step'], 'disable-military-reinforcement-v1')
                self.assertEqual(saved['native_request_frame']['expected_revision'], 109)
                self.assertEqual(saved['native_command_result_frame'], driver.state.actual_rejection)
                self.assertEqual(saved['native_request_id'], saved['request_id'])
                self.assertEqual(saved['native_handler_execution_status'], 'unknown')
                self.assertEqual(saved['result_state'], 'unknown_no_retry')
                self.assertEqual(json.loads(claim.read_text(encoding='utf-8'))['status'], 'claimed_result_unknown_no_retry')
                self.assertFalse(claim.with_suffix('.verified.json').exists())
                self.assertFalse(claim.with_suffix('.result.json').exists())
                with self.assertRaisesRegex(BridgeUnavailableError, 'unresolved result'):
                    action.set_fixed_military_reinforcement_12004(driver, desired_enabled=True, expected_revision=110)
                self.assertEqual(len(endpoint.sent), 2)
                self.actual_evidence = {'synthetic_fixture_public_revision': 110,
                    'actual_primitive_sent_expected_revision': 109, 'requests_sent': endpoint.sent,
                    'saved_failure': saved, 'opposite_direction_no_second_send': True,
                    'handler_execution_remains_unknown': True}


if __name__ == '__main__':
    unittest.main()
