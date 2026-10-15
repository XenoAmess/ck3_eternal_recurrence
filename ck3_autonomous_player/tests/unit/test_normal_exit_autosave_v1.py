"""Fixed autosave-disable action preserves exit claims and requires readback."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_normal_exit_integrated_v1 import FakeExitDriver, native_observation, driver_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    ExitWireBinding, encode_normal_exit_map_request, normalize_native_exit_observation,
    normalize_public_exit_result,
)


class AutosaveDriver(FakeExitDriver):
    def __init__(self, path, save=True):
        super().__init__(path)
        self.modal = True
        self.save = save
        self.fail = False
        self.visible = True

    def send(self, request):
        if request['action'] != 'disable_exit_autosave':
            return super().send(request)
        self.sent.append(copy.deepcopy(request))
        self.toggled = self.save
        self.save = False
        if self.fail:
            raise OSError('callback delivery unknown')

    def wait_for_command_result(self, request_id, timeout):
        request = self.sent[-1]
        value = native_observation(request, modal=True)
        value['exit_autosave'] = {
            'state_available': True, 'control_visible': self.visible,
            'control_enabled': self.visible, 'should_save': self.save,
            'disable_claimed': request['action'] != 'query_context' and self.toggled,
            'dispatch_invoked': request['action'] != 'query_context' and self.toggled,
            'postcondition_observed': request['action'] == 'disable_exit_autosave',
        }
        if request['action'] == 'disable_exit_autosave':
            value['status'] = 'autosave_disabled'
        return {'ok': True, 'request_id': request_id, 'result': value}


class AutosaveTests(unittest.TestCase):
    def sources(self):
        return patch.object(driver_module, 'verify_source_inventory_v1',
                            return_value={'source_inventory_sha256': 'b' * 64})

    def disable(self, driver):
        query = driver.query_normal_exit_context_v1(expected_revision=72)
        return driver.request_normal_exit_v1('disable_exit_autosave', expected_revision=72,
            expected_exit_context_signature=query['exit_context_signature'])

    def test_actual_driver_requires_false_native_readback_without_exit_claim(self):
        for original in [True, False]:
            with self.subTest(original=original), tempfile.TemporaryDirectory() as temporary, self.sources():
                driver = AutosaveDriver(Path(temporary), original)
                result = self.disable(driver)
                self.assertEqual(result['status'], 'autosave_disabled')
                self.assertTrue(result['exit_autosave_disabled_observed'])
                self.assertFalse(result['typed_normal_exit_observed'])
                self.assertFalse(result['process_exit_observed'])
                self.assertFalse(result['autosave_verified'])
                self.assertEqual(driver.toggled, original)
                self.assertFalse(any(d['dispatch_invoked'] for d in result['native_observation']['dispatches']))
                normalize_public_exit_result(result, action='disable_exit_autosave', expected_revision=72)

    def test_missing_or_hidden_stock_checkbox_rejects_before_claim_and_send(self):
        for old_native in [True, False]:
            with self.subTest(old_native=old_native), tempfile.TemporaryDirectory() as temporary, self.sources():
                driver = FakeExitDriver(Path(temporary)) if old_native else AutosaveDriver(Path(temporary))
                driver.modal = True
                driver.visible = False
                query = driver.query_normal_exit_context_v1(expected_revision=72)
                calls = len(driver.sent)
                with self.assertRaisesRegex(BridgeUnavailableError, 'stock save checkbox'):
                    driver.request_normal_exit_v1('disable_exit_autosave', expected_revision=72,
                        expected_exit_context_signature=query['exit_context_signature'])
                self.assertEqual(len(driver.sent), calls)
                self.assertFalse(list((Path(temporary) / 'normal-exit-map-requests').glob('*.claim.json')))

    def test_unknown_toggle_claim_is_preserved_and_not_replayed(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            driver = AutosaveDriver(Path(temporary))
            driver.fail = True
            result = self.disable(driver)
            self.assertEqual(result['status'], 'dispatch_unknown_claimed')
            self.assertFalse(result['exit_autosave_disabled_observed'])
            self.assertTrue(result['claim_consumed'])
            self.assertFalse(result['retry_authorized'])
            count = len(driver.sent)
            claim = Path(result['claim_path']).read_bytes()
            with self.assertRaisesRegex(BridgeUnavailableError, 'already claimed'):
                self.disable(driver)
            self.assertEqual(len(driver.sent), count + 1) # fresh query only
            self.assertEqual(Path(result['claim_path']).read_bytes(), claim)

    def test_observation_cannot_upgrade_true_unknown_or_exit_stage_to_disabled(self):
        with tempfile.TemporaryDirectory() as temporary, self.sources():
            result = self.disable(AutosaveDriver(Path(temporary)))
            raw = result['native_observation']
            binding = ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
            mutations = [lambda v: v['exit_autosave'].update(should_save=True),
                         lambda v: v['exit_autosave'].update(state_available=False),
                         lambda v: v['exit_autosave'].update(postcondition_observed=False),
                         lambda v: v['dispatches'][2].update(dispatch_invoked=True),
                         lambda v: v.update(exit_autosave=None)]
            for mutate in mutations:
                forged = copy.deepcopy(raw)
                mutate(forged)
                with self.assertRaises(ValueError):
                    normalize_native_exit_observation(forged, binding, 'disable_exit_autosave')

    def test_encoder_keeps_closed_semantic_action_and_no_caller_save_setting(self):
        binding = ExitWireBinding(72, 9301, 43, 8, 133000000000000043, 'b' * 64)
        request = json.loads(encode_normal_exit_map_request(request_id='exit-disable-1',
            action='disable_exit_autosave', binding=binding, request_nonce='nonce-1',
            expected_exit_context_signature='c' * 64))
        self.assertEqual(len(request), 13)
        self.assertNotIn('should_save', request)
        self.assertNotIn('widget_path', request)


if __name__ == '__main__':
    unittest.main()
