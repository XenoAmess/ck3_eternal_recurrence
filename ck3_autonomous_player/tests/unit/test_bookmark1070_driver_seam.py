"""One new production-seam compound; authoring does not execute this file.

Run only this test module once with -B -X utf8. The real event-window query
normalizer/pin, event-selection method, wait predicate, and material helper run.
Only existing snapshot/primitive transport and the Army provider are mocked.
"""

from copy import deepcopy
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'tests/unit'))

from test_event_window_context_v1_bridge import _frame
from test_bookmark1070_material import army_strength, decision, snapshot
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    _EVENT_PROVENANCE_BY_BACKEND,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.army_strengths_profile_contract import ORDINARY_CORE_PROFILE
from xar_autoplayer.vanilla_events.bookmark1070_material import (
    evaluate_bookmark1070_army_material_postcondition_v1,
    plan_bookmark1070_army_material_postcondition_v1,
)


def current_frame(before, event_key):
    frame = _frame()
    frame.update(
        snapshot_revision=before['native_revision'], date_raw=before['date_raw'],
        current_event_instance_id=before['active_event']['instance_id'],
        event_definition_key=event_key, saved_scopes=[],
        provenance=deepcopy(_EVENT_PROVENANCE_BY_BACKEND[
            'ck3-1.20.0.4-native-event-window-v1']),
    )
    frame['root_scope']['typed_identity']['character_id'] = 29829
    option = frame['options'][0]
    option.update(shown=True, enabled=True, fallback=False, cancel=False,
                  unavailable_reason='')
    option['effect_indicators'].update(
        coverage='played-character-event-icon-indicators-1.20.0.4-v1', rows=[])
    frame['options'] = [{**deepcopy(option), 'rendered_index': index,
                         'native_option_index': index,
                         'resolved_name': f'Option {index + 1}'}
                        for index in range(3)]
    return frame


def harness(*, event_key='bookmark.1070', new_shape='one', read_error=False,
            missing_before=False):
    before, after = snapshot(), snapshot(8, new_army=new_shape != 'none')
    before['active_event']['option_count'] = 3
    before['active_wars'] = after['active_wars'] = []
    if missing_before:
        before.pop('player_armies')
    if new_shape == 'multiple':
        after['player_armies'].append({
            'army_id': 268435482, 'owner_character_id': 29829,
            'current_province_id': 478})
    state = {'current': before}
    driver = object.__new__(NativeHeadlessGameplayDriver)
    driver._driver_state_lock = threading.RLock()
    driver.command_timeout_seconds = 0.05
    driver.take_snapshot = Mock(side_effect=lambda *args, **kwargs:
                                deepcopy(state['current']))
    driver.take_snapshot_without_native_command_history = Mock(
        side_effect=lambda: deepcopy(state['current']))
    frame = current_frame(before, event_key)

    def primitive(step, **kwargs):
        if step == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP:
            return {'step': step, 'accepted': True, 'status': 'available',
                'query_sequence': 1, 'snapshot_revision': before['native_revision'],
                'current_event_window_context': deepcopy(frame),
                'backend_id': 'ck3-1.20.0.4-native-event-window-v1'}
        if step.startswith('select-event-option-'):
            state['current'] = after
            return {'step': step, 'accepted': True}
        raise ValueError(f'Unexpected existing transport step: {step}')

    driver._execute_primitive_step = Mock(side_effect=primitive)
    driver._execute_army_strength_query = Mock(
        side_effect=BridgeUnavailableError('focused provider unavailable')
        if read_error else None,
        return_value={'army_strengths': [army_strength()]},
    )
    # Real query invokes real exact-build normalization and sets the private pin.
    queried = driver.query_current_event_window_context_v1(
        19, expected_revision=before['revision'])
    assert driver.take_snapshot_without_native_command_history.call_count == 2
    return driver, before, after, queried


class Bookmark1070DriverSeamTests(unittest.TestCase):
    def test_query_pin_selection_and_material_capture_compound(self):
        # Branch 1: exact current query -> one selection -> one core query ->
        # actual compact helper/comparator, never source-only material credit.
        with self.subTest(branch='current_unique_new_army'):
            driver, before, after, queried = harness()
            self.assertEqual(queried['event_definition_key'], 'bookmark.1070')
            self.assertEqual(driver._bookmark1070_material_frame['revision'], 7)
            result = driver._execute_event_option_step(
                'select-event-option-3', option_number=3, expected_revision=7)
            selection = result['event_selection']
            self.assertTrue(selection['postcondition_verified'])
            self.assertIsNone(driver._bookmark1070_material_frame)
            driver._execute_army_strength_query.assert_called_once_with(
                starting=after, selected_revision=8, profile=ORDINARY_CORE_PROFILE)
            self.assertIsNone(selection['starting_bookmark1070_armies']['army_strengths'])
            compact = selection['ending_bookmark1070_armies']['army_strengths']
            self.assertEqual([row['army_id'] for row in compact], [268435481])
            self.assertNotIn('actual_army_late_event_observations_v1', compact[0])
            expected = plan_bookmark1070_army_material_postcondition_v1(decision(), before)
            material = evaluate_bookmark1070_army_material_postcondition_v1(expected, selection)
            self.assertEqual(material['status'], 'verified_change')
            self.assertEqual(material['observed_current_soldiers'], 250)
            self.assertFalse(material['levy_type_identity_observed'])
            self.assertFalse(material['total_army_net_gain_used'])
            self.assertEqual([call.args[0] for call in
                driver._execute_primitive_step.call_args_list],
                [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, 'select-event-option-3'])

        # Branch 2: a different event or a different option does not enable Army
        # capture. The actual query and selection seams remain in both paths.
        for event_key, option in (('xar_test.0001', 3), ('bookmark.1070', 1)):
            with self.subTest(branch='unrelated_selection', event=event_key, option=option):
                driver, _, _, _ = harness(event_key=event_key)
                result = driver._execute_event_option_step(
                    f'select-event-option-{option}', option_number=option, expected_revision=7)
                driver._execute_army_strength_query.assert_not_called()
                self.assertNotIn('starting_bookmark1070_armies', result['event_selection'])
                self.assertTrue(result['event_selection']['postcondition_verified'])

        # Branch 3: provider failure follows an independently advanced event.
        # The material is unavailable and the event action is never replayed.
        with self.subTest(branch='post_provider_unavailable'):
            driver, _, _, _ = harness(read_error=True)
            result = driver._execute_event_option_step(
                'select-event-option-3', option_number=3, expected_revision=7)
            self.assertTrue(result['event_selection']['postcondition_verified'])
            self.assertEqual(result['event_selection']['ending_bookmark1070_armies']['status'],
                             'unavailable')
            self.assertEqual(driver._execute_army_strength_query.call_count, 1)
            self.assertEqual(sum(call.args[0] == 'select-event-option-3'
                for call in driver._execute_primitive_step.call_args_list), 1)

        # Branch 4: missing before roster or nonunique/no new owned IDs never
        # triggers a core read or receives new-army material credit.
        for shape, missing in (('none', False), ('multiple', False), ('one', True)):
            with self.subTest(branch='missing_or_nonunique_roster', shape=shape, missing=missing):
                driver, before, _, _ = harness(new_shape=shape, missing_before=missing)
                result = driver._execute_event_option_step(
                    'select-event-option-3', option_number=3, expected_revision=7)
                driver._execute_army_strength_query.assert_not_called()
                expected = plan_bookmark1070_army_material_postcondition_v1(decision(), before)
                material = evaluate_bookmark1070_army_material_postcondition_v1(
                    expected, result['event_selection'])
                self.assertNotEqual(material['status'], 'verified_change')
                self.assertTrue(result['event_selection']['postcondition_verified'])
                if missing:
                    self.assertEqual(result['event_selection']['starting_bookmark1070_armies']['status'],
                                     'unavailable')
                    self.assertIsNone(result['event_selection']['starting_bookmark1070_armies']['player_armies'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
