"""Production native_auto_run pairs fulfillment ACKs and later pending reads."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

import xar_autoplayer.native_auto_run as run_module
from xar_autoplayer.current_first_heir_betrothal_formal_consumer import SUBMIT_STEP
from xar_autoplayer.family_marriage_formal_consumer import RESULT_STEP, _write, read_family_marriage_ledger
from test_native_auto_run import _NativeAutoRunHarness, _FakeGameplayService, NativeAutoRunTests
import g2_preview_operator as operator


class FulfillmentHarness(_NativeAutoRunHarness):
    def make_service(self, driver):
        self.events.append('service_init')
        return FulfillmentService(self, driver)

    def save_checkpoint(self, *, expected_revision):
        result = super().save_checkpoint(expected_revision=expected_revision)
        if len(self.history) > 1 and self.history[-2]['command'] == RESULT_STEP:
            self.native_revision += 1
            self.public_revision += 1
        return result


class FulfillmentService(_FakeGameplayService):
    def auto_turn(self, *, before_submit=None):
        harness = self.harness
        harness.auto_turn_count += 1
        if not self.driver.allow_private_current_first_heir_betrothal_fulfillment:
            return harness.execute_auto_turn()
        state = self.driver.take_snapshot()
        pending = read_family_marriage_ledger(self.driver.state_dir)['pending']
        if pending is None:
            step = SUBMIT_STEP
            pending = {
                'schema': 'xar.ck3.observed-first-heir-marriage-private-action.v1',
                'status': 'receipt_pending', 'submission_state': 'receipt_pending',
                'accepted': True, 'material_result': False, 'fulfill_existing_betrothal': True,
                'matrilineal_option_selected': False,
                'played_character_id': harness.played_character_id,
                'heir_character_id': 808, 'candidate_character_id': 909,
                'recipient_character_id': 1001, 'episode_run_id': harness.episode_run_id,
                'source_date_raw': harness.date_raw,
                'source_bridge_pid': harness.bridge_pid, 'source_bridge_creation_date': 'fixture',
            }
            result = copy.deepcopy(pending)
            plan = {'selected_step': step, 'current_betrothal_fulfillment': True,
                    'current_betrothal_choice': {'candidate_character_id': 909}}
        else:
            step = RESULT_STEP
            pending = {**pending, 'last_checked_native_revision': state['native_revision'],
                       'last_checked_date_raw': state['date_raw'],
                       'last_checked_bridge_pid': harness.bridge_pid,
                       'last_checked_bridge_creation_date': 'fixture'}
            result = {'status': 'pending', 'material_result': False,
                      'fulfill_existing_betrothal': True,
                      'heir_character_id': 808, 'candidate_character_id': 909}
            plan = {'selected_step': step, 'current_betrothal_fulfillment': True,
                    'current_betrothal_pending': copy.deepcopy(pending)}
        _write(self.driver.state_dir, {
            'schema': 'xar.ck3.first-heir-marriage-formal.v1',
            'pending': pending, 'resolved': None,
        })
        harness._append_history(step, result)
        return {'status': 'executed', 'selected_step': step, 'plan': plan,
                'result': result, 'revision': state['revision'], 'snapshot_id': state['snapshot_id']}


class CurrentBetrothalFormalRunTests(unittest.TestCase):
    setUp = NativeAutoRunTests.setUp
    tearDown = NativeAutoRunTests.tearDown

    def run_fixture(self, *, enabled):
        harness = FulfillmentHarness(self.spec, ['advance'], initial_unready_snapshot=False)
        with (
            mock.patch.object(run_module, 'NativeHeadlessGameplayDriver', side_effect=harness.make_driver),
            mock.patch.object(run_module, 'GameplayBridgeService', side_effect=harness.make_service),
            mock.patch.object(run_module, 'native_session', side_effect=harness.run_session),
            mock.patch('xar_autoplayer.current_first_heir_betrothal_formal_consumer._identity',
                       return_value=(4242, 'fixture')),
        ):
            report = run_module.native_auto_run(
                self.spec, native_bridge=self.config, turn_count=2 if enabled else 1,
                timeout_seconds=2, readiness_timeout_seconds=0.25,
                readiness_stable_seconds=0, poll_interval_seconds=0.001,
                allow_private_family_marriage_formal_trial=enabled,
            )
        return report, harness

    def test_formal_option_pairs_ack_then_pending_read_without_material_claim(self):
        report, harness = self.run_fixture(enabled=True)
        self.assertTrue(report['ok'], report.get('first_blocker'))
        turns = report['auto_run']['turns']
        self.assertEqual([turn['selected_step'] for turn in turns], [SUBMIT_STEP, RESULT_STEP])
        self.assertIs(harness.driver.allow_private_current_first_heir_betrothal_fulfillment, True)
        phases = [item['phase'] for item in report['checkpoints']]
        self.assertIn('current_first_heir_betrothal_submitted_pending', phases)
        self.assertIn('current_betrothal_fulfillment_result_pending', phases)
        ledger = read_family_marriage_ledger(self.spec.state_dir)
        self.assertIsNone(ledger['resolved'])
        self.assertIs(ledger['pending']['material_result'], False)
        self.assertEqual(ledger['pending']['last_consumed_checkpoint_native_revision'], harness.native_revision)
        self.assertGreater(ledger['pending']['last_consumed_checkpoint_native_revision'],
                           ledger['pending']['last_checked_native_revision'])
        self.assertIn('current_betrothal_fulfillment_readback_checkpoint_saved', turns[-1]['evidence'])
        self.assertEqual(sum(item['command'] == SUBMIT_STEP for item in harness.history), 1)
        # The actual compact production report is also the official cold-pair input.
        manifest = {'episode_character_id': harness.episode_character_id,
                    'episode_run_id': harness.episode_run_id}
        checkpoint = report['checkpoints'][-1]
        self.assertEqual(operator.family_pending_sidecar_pair(
            ledger, {**manifest, 'last_checkpoint': checkpoint}, manifest,
            checkpoint['sha256'], report), 909)

    def test_existing_family_default_keeps_new_internal_gate_off(self):
        report, harness = self.run_fixture(enabled=False)
        self.assertTrue(report['ok'], report.get('first_blocker'))
        self.assertIs(harness.driver.allow_private_current_first_heir_betrothal_fulfillment, False)
        self.assertFalse((self.spec.state_dir / 'first-heir-marriage-formal-v1.json').exists())


if __name__ == '__main__':
    unittest.main()
