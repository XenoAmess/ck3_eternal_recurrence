"""The private family option reaches the fixed pair through the real turn entry."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.current_first_heir_betrothal_formal_consumer import SUBMIT_STEP
from xar_autoplayer.family_marriage_formal_consumer import RESULT_STEP
from xar_autoplayer.native_auto_run import _turn_record, _verify_pending_family_marriage_checkpoint


def frame() -> dict[str, object]:
    return {
        'snapshot_id': 'family-entry-fixture', 'revision': 7, 'native_revision': 7,
        'date_raw': 53220000, 'paused': True, 'map_ready': True,
        'active_event': None, 'pending_character_interaction': None,
        'active_wars': [], 'episode_run_id': 'family-entry-101',
        'episode_character_id': 101, 'played_character': {'character_id': 101},
        'history': [],
    }


def enabled_driver(state: dict[str, object]) -> CallbackGameplayDriver:
    driver = CallbackGameplayDriver(
        backend_id='native-headless', snapshot=lambda: copy.deepcopy(state),
        execute=lambda _step, _revision: {}, action_steps=('life-advance',),
    )
    driver.allow_private_family_marriage_formal_trial = True
    driver.allow_private_current_first_heir_betrothal_fulfillment = True
    return driver


def handled(step: str, **values: object):
    def plan(_driver, planned, _snapshot, **_kwargs):
        return {**planned, 'plan': {**planned['plan'],
            'selected_step': step, 'current_betrothal_fulfillment': True, **values}}
    return plan


class CurrentBetrothalEntryTests(unittest.TestCase):
    def test_formal_turn_executes_selected_fixed_pair_before_ordinary_pool(self):
        driver = enabled_driver(frame())
        receipt = {'status': 'receipt_pending', 'material_result': False,
                   'fulfill_existing_betrothal': True}
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
                       side_effect=handled(SUBMIT_STEP, current_betrothal_choice={
                           'candidate_character_id': 303})) as current,
            mock.patch('xar_autoplayer.bridge.service.plan_family_marriage_private') as ordinary,
            mock.patch('xar_autoplayer.bridge.service.submit_current_first_heir_betrothal_fulfillment_private',
                       return_value=receipt) as submit,
        ):
            outcome = GameplayBridgeService(driver).auto_turn()
        self.assertEqual(outcome['selected_step'], SUBMIT_STEP)
        self.assertIs(outcome['result']['material_result'], False)
        current.assert_called_once()
        submit.assert_called_once()
        ordinary.assert_not_called()

    def test_nonapplicable_fixed_pair_falls_back_to_ordinary_consumer(self):
        driver = enabled_driver(frame())
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
                       side_effect=lambda _driver, planned, _snapshot, **_kw: planned),
            mock.patch('xar_autoplayer.bridge.service.plan_family_marriage_private',
                       side_effect=lambda _driver, planned, _snapshot, **_kw: planned) as ordinary,
        ):
            result = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(result['plan']['selected_step'], 'life-advance')
        ordinary.assert_called_once()

    def test_default_off_does_not_read_fixed_pair(self):
        driver = enabled_driver(frame())
        driver.allow_private_family_marriage_formal_trial = False
        driver.allow_private_current_first_heir_betrothal_fulfillment = False
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private') as current,
        ):
            outcome = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(outcome['plan']['selected_step'], 'life-advance')
        current.assert_not_called()

    def test_shared_result_step_dispatches_the_fulfillment_mode(self):
        driver = enabled_driver(frame())
        pending = {'fulfill_existing_betrothal': True, 'heir_character_id': 202,
                   'candidate_character_id': 303}
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
                       side_effect=handled(RESULT_STEP, current_betrothal_pending=pending,
                                           current_betrothal_cold_recovery=True)),
            mock.patch('xar_autoplayer.bridge.service.query_current_first_heir_betrothal_fulfillment_result_private',
                       return_value={'status': 'pending', 'material_result': False}) as current,
            mock.patch('xar_autoplayer.bridge.service.query_family_marriage_result_private') as ordinary,
        ):
            outcome = GameplayBridgeService(driver).auto_turn()
        current.assert_called_once_with(driver, pending=pending, cold=True)
        ordinary.assert_not_called()
        self.assertEqual(outcome['result']['status'], 'pending')

    def test_joint_fallback_reaches_same_fixed_pair_consumer(self):
        driver = enabled_driver(frame())
        driver.allow_private_m5_joint_collector = True
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_m5_formal_query_only',
                       side_effect=lambda _driver, planned, **_kw: planned),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
                       side_effect=handled(SUBMIT_STEP)) as current,
            mock.patch('xar_autoplayer.bridge.service.plan_family_marriage_private') as ordinary,
        ):
            chosen = GameplayBridgeService(driver).plan_turn()['plan']
        self.assertEqual(chosen['selected_step'], SUBMIT_STEP)
        current.assert_called_once()
        ordinary.assert_not_called()

    def test_wartime_pending_is_not_cached_as_an_empty_opportunity(self):
        state = frame()
        state['active_wars'] = [{'war_id': 123}]
        driver = enabled_driver(state)
        service = GameplayBridgeService(driver)
        with mock.patch(
            'xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
            side_effect=handled('query-army-strengths-v1',
                                current_betrothal_pending={'fulfill_existing_betrothal': True}),
        ) as current:
            baseline = {'plan': {'selected_step': 'query-army-strengths-v1'}}
            service._plan_private_family_wartime_v1(baseline, state)
            service._plan_private_family_wartime_v1(baseline, state)
        self.assertEqual(current.call_count, 2)
        self.assertIs(current.call_args.kwargs['wartime_arbitration'], True)

    def test_joint_missing_fields_preserves_qualified_independent_fixed_pair(self):
        driver = enabled_driver(frame())
        driver.allow_private_m5_joint_collector = True
        def joint(_driver, planned, **_kwargs):
            return {**planned, 'plan': {**planned['plan'], 'selected_step': None,
                'phase': 'm5_joint_query_only_red', 'reason': 'joint income field unavailable',
                'formal_action_ready': False}}
        with (
            mock.patch('xar_autoplayer.bridge.service.choose_one_life_turn',
                       return_value={'selected_step': 'life-advance'}),
            mock.patch('xar_autoplayer.bridge.service.plan_m5_formal_query_only', side_effect=joint),
            mock.patch('xar_autoplayer.bridge.service.plan_current_first_heir_betrothal_fulfillment_private',
                       side_effect=handled(SUBMIT_STEP)),
        ):
            chosen = GameplayBridgeService(driver).plan_turn()['plan']
        self.assertEqual(chosen['selected_step'], SUBMIT_STEP)
        self.assertEqual(chosen['m5_joint_red_reason'], 'joint income field unavailable')
        self.assertIs(chosen['formal_action_ready'], False)

    def test_pending_checkpoint_preserves_mode_and_report_projection(self):
        state = frame()
        pending = {
            'status': 'receipt_pending', 'submission_state': 'receipt_pending',
            'material_result': False, 'fulfill_existing_betrothal': True,
            'episode_run_id': state['episode_run_id'], 'source_date_raw': state['date_raw'],
            'played_character_id': 101, 'heir_character_id': 202,
            'candidate_character_id': 303, 'recipient_character_id': 404,
        }
        checkpoint = {'episode_run_id': state['episode_run_id'], 'date_raw': state['date_raw']}
        proof = _verify_pending_family_marriage_checkpoint(
            checkpoint, snapshot=state, submitted_result=pending,
            ledger={'pending': pending}, expected_step=SUBMIT_STEP,
        )
        self.assertIs(proof['fulfill_existing_betrothal'], True)
        turn = _turn_record(1, 'fixture', turn_class='gameplay', before=state, after=state,
                            outcome={'plan': {'current_betrothal_fulfillment': True,
                                              'current_betrothal_choice': {'candidate_character_id': 303}}},
                            evidence=[])
        self.assertIs(turn['plan']['current_betrothal_fulfillment'], True)
        self.assertEqual(turn['plan']['current_betrothal_choice']['candidate_character_id'], 303)


if __name__ == '__main__':
    unittest.main()
