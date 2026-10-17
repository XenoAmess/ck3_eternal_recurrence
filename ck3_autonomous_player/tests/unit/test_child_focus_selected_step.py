from copy import deepcopy
import unittest

from xar_autoplayer.bridge.service import GameplayBridgeService


class ChildFocusSelection(unittest.TestCase):
    def choose(self, *, legal=True, presence='absent', enabled=True):
        calls = []

        class Driver:
            allow_private_lifestyle_formal_trial = enabled

            def _with_internal_planning_view(self, snapshot, callback):
                return {'pending': None}

            def query_child_education_focus_private_v1(self, **arguments):
                calls.append(arguments)
                return {'status': 'available', 'native_legal': legal,
                        'current_focus': {'available': True, 'presence': presence},
                        'target_key': arguments['target_key']}

            def submit_child_education_focus_private_v1(self, **arguments):
                raise AssertionError('Planning must not submit a business command')

            def query_child_education_focus_receipt_private_v1(self, **arguments):
                raise AssertionError('No unresolved action exists')

        service = GameplayBridgeService.__new__(GameplayBridgeService)
        service.driver = Driver()
        planned = {'revision': 9, 'plan': {'selected_step': 'life-advance-one-day'}}
        needs = {'rows': [{'raw_character_id': 17, 'frame': {'native_revision': 40},
            'stock_skill_options': [{'focus_key': 'education_stewardship',
                'childhood_affinity': {'available': True, 'raw_value': True},
                'childhood_disaffinity': {'available': True, 'raw_value': False}}]}]}
        result = service._plan_private_family_child_focus_v1(
            deepcopy(planned), {'native_revision': 40}, needs)
        return result, calls

    def test_native_legal_absent_focus_selects_existing_canonical_submit_step(self):
        result, calls = self.choose()
        self.assertEqual(result['plan']['selected_step'], 'private-select-child-education-focus-v1')
        self.assertEqual(result['plan']['phase'], 'family_child_education_focus_submission')
        self.assertEqual(calls, [{'child_full_id': 17, 'target_key': 'education_stewardship',
                                 'expected_revision': 9}])

    def test_native_illegal_and_already_present_keep_original_plan(self):
        for arguments in ({'legal': False}, {'presence': 'present'}):
            with self.subTest(arguments=arguments):
                result, calls = self.choose(**arguments)
                self.assertEqual(result['plan']['selected_step'], 'life-advance-one-day')
                self.assertEqual(len(calls), 1)

    def test_disabled_trial_does_not_query_or_submit(self):
        result, calls = self.choose(enabled=False)
        self.assertEqual(result['plan']['selected_step'], 'life-advance-one-day')
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
