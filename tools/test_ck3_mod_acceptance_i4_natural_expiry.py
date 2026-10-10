"""New partial-observation guards; no CK3, SDK, process, screen or real save."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as adapter


def frame(date=53144712, pid=901, generation=1):
    return {'diagnostics': {'bridge_pid': pid, 'connection_generation': generation},
        'played_character': {'character_id': 31254}, 'date_raw': date,
        'native_revision': 11, 'paused': True, 'active_event': None}


def tree(enabled=False):
    # Topology comes from the stock named-anchor contract, not a guessed row index.
    widgets = []
    for path, name, count, visible, active in [
        ('', 'decisiondetail_view', 1, True, True), ('0', '', 7, True, True),
        ('0/0', 'cost', 0, True, True), ('0/2', '', 3, True, True),
        ('0/2/1', '', 0, True, enabled), ('0/2/2', 'cram_study_start_tutorial_highlight', 0, False, True),
        ('0/3', '', 2, False, True), ('0/3/0', 'back', 0, False, True), ('0/3/1', '', 0, False, True)]:
        widgets.append({'child_path': path, 'runtime_name': name, 'child_count': count,
            'effective_visible': visible, 'enabled': active})
    return {'schema': 'ck3-native-gui-window-tree-inspection-v1', 'window_kind': 'decision_detail',
        'scope_root_name': 'decisiondetail_view', 'read_only': True, 'accepted': True,
        'status': 'available', 'root_available': True, 'truncated': False,
        'widget_count': len(widgets), 'widgets': widgets}


def origin(data):
    flag = {'present': True, 'tick': '349', 'type': None, 'identity': None, 'entries': [],
        'row_entries': [{'key': 'flag', 'value': 'lyd_school_cooldown'},
            {'key': 'tick', 'value': '349'}, {'key': 'data', 'value': []}]}
    return {'schema': 'lyd.i3b0240.cached-baseline.v1', 'historical_save': data['saved_campaign'],
        'historical_frame': {'actor': 31254, 'date_raw': 53144712, 'paused': True,
            'active_event': None, 'pending_interaction': None}, 'roles': data['origin_roles'],
        'school_study_CD': {'lyd_school_cooldown': flag}}


def natural_row(before, hours=24):
    return {'id': 'natural-day-1', 'ok': True, 'result': {'before': before,
        'after': frame(before['date_raw'] + hours), 'requested_days': 1,
        'requested_interval_complete': True, 'event_boundary': None, 'elapsed_hours': hours}}


def saved_fixture(directory, present):
    flag = '{ flag=lyd_school_cooldown tick=349 data={} }' if present else ''
    raw = ('living={\n31254={\nrite=169 alive_data={ variables={ data={ '
        '{ flag=lyd_enabled data={} } ' + flag + ' } } } landed_data={}\n}\n}\n'
        'dead_unprunable={\n}\nfaiths={ database={ 107={ religious_head=4294967295 main_rite=169 } } }\n'
        'rites={ database={ 169={ faith=107 head_of_rite=31254 } } }\n').encode()
    path = directory / 'public-fixed-checkpoint.ck3'
    path.write_bytes(raw)
    return {'path': str(path), 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
        'status': 'saved', 'date_raw': 53144712, 'episode_projection': 'native_campaign'}


class NaturalExpiryGuards(unittest.TestCase):
    def setUp(self):
        self.data = adapter.contract()
        self.seed = {**self.data['saved_campaign'], 'save': 'original-not-opened.ck3'}

    def test_raw_tick_never_becomes_remaining_days_or_date(self):
        result = adapter.validate_origin(origin(self.data), self.seed, self.data)
        self.assertEqual(result['raw_tick_observed'], '349')
        self.assertIsNone(result['remaining_days'])
        self.assertIsNone(result['expiry_date'])
        self.assertEqual(result['tick_interpretation'], 'UNQUALIFIED')

    def test_absent_initial_flag_rejected(self):
        value = origin(self.data)
        value['school_study_CD']['lyd_school_cooldown'] = None
        with self.assertRaises(ValueError): adapter.validate_origin(value, self.seed, self.data)

    def test_typed_numeric_zero_is_not_a_flag(self):
        value = origin(self.data)
        value['school_study_CD']['lyd_school_cooldown']['type'] = 'value'
        with self.assertRaises(ValueError): adapter.validate_origin(value, self.seed, self.data)

    def test_enabled_and_disabled_are_actual_widget_booleans(self):
        self.assertIs(adapter.confirm_enabled(tree(False)), False)
        self.assertIs(adapter.confirm_enabled(tree(True)), True)

    def test_truncated_tree_cannot_mean_disabled(self):
        value = tree(); value['truncated'] = True
        with self.assertRaises(ValueError): adapter.confirm_enabled(value)

    def test_ambiguous_or_hidden_confirm_cannot_mean_disabled(self):
        for visible in (True, False):
            value = tree()
            for row in value['widgets']:
                if row['child_path'] == ('0/3/1' if visible else '0/2/1'):
                    row['effective_visible'] = visible
            with self.assertRaises(ValueError): adapter.confirm_enabled(value)

    def test_changed_footer_and_duplicate_anchor_rejected(self):
        for change in ('layout', 'anchor'):
            value = tree()
            if change == 'layout': value['widgets'][1]['child_count'] = 8
            else:
                value['widgets'][-1]['runtime_name'] = 'cost'
            with self.assertRaises(ValueError): adapter.confirm_enabled(value)

    def test_available_decision_alone_never_qualifies_eligibility(self):
        with self.assertRaises(ValueError):
            adapter.observe_model(frame(), {'available': True, 'can_execute': True}, self.data['decision_key'])

    def test_one_actual_natural_interval_and_duration(self):
        initial = frame()
        self.assertEqual(adapter.validate_day(natural_row(initial, 25), initial, initial, 0, 366), 25)

    def test_calendar_jump_or_incomplete_interval_rejected(self):
        for mutation in ('hours', 'date', 'incomplete'):
            initial = frame(); row = natural_row(initial)
            if mutation == 'hours': row['result']['elapsed_hours'] = 24 * 365
            elif mutation == 'date': row['result']['after']['date_raw'] += 24 * 365
            else: row['result']['requested_interval_complete'] = False
            with self.assertRaises(ValueError): adapter.validate_day(row, initial, initial, 0, 366)

    def test_event_and_connection_change_rejected(self):
        for mutation in ('event', 'connection', 'unpaused'):
            initial = frame(); row = natural_row(initial)
            if mutation == 'event': row['result']['event_boundary'] = {'instance_id': 9}
            elif mutation == 'connection': row['result']['after']['diagnostics']['connection_generation'] = 2
            else: row['result']['after']['paused'] = False
            with self.assertRaises(ValueError): adapter.validate_day(row, initial, initial, 0, 366)

    def test_actual_elapsed_cap_not_only_submitted_day_count(self):
        initial = frame(); before = frame(initial['date_raw'] + 366 * 24 - 24)
        with self.assertRaises(ValueError):
            adapter.validate_day(natural_row(before, 25), before, initial, 366 * 24 - 24, 366)

    def test_fresh_initial_body_requires_present_flag_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            cp = saved_fixture(directory, True)
            facts = adapter.read_saved({'output': str(directory), 'repo_root': str(TOOLS.parent)}, cp,
                53144712, self.data, True)
            self.assertTrue(facts['school_cooldown_present'])
            self.assertEqual(facts['raw_tick_observed'], '349')
            self.assertNotEqual(facts['preserved_checkpoint']['path'], cp['path'])
            self.assertEqual(Path(facts['preserved_checkpoint']['path']).read_bytes(), Path(cp['path']).read_bytes())
            self.assertEqual(facts['save_body_reads'], 1)

    def test_fresh_initial_absence_and_final_presence_rejected(self):
        for present in (False, True):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); cp = saved_fixture(directory, present)
                message = 'Final SAVE still contains' if present else 'Fresh initial SAVE must contain'
                with self.assertRaisesRegex(ValueError, message):
                    adapter.read_saved({'output': str(directory), 'repo_root': str(TOOLS.parent)}, cp,
                        53144712, self.data, not present)

    def test_final_body_no_flag_and_same_headless_membership(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary); cp = saved_fixture(directory, False)
            facts = adapter.read_saved({'output': str(directory), 'repo_root': str(TOOLS.parent)}, cp,
                53144712, self.data, False)
            self.assertFalse(facts['school_cooldown_present'])
            self.assertTrue(facts['headless'])
            self.assertEqual(facts['baseline_body_reads'], 0)

    def test_wrong_faith_head_or_rite_parent_cannot_qualify(self):
        reader = adapter.base._reader(TOOLS.parent)
        actor = {'character_id': 31254, 'rite_id': 169, 'landed_data': [],
            'variables': {'lyd_enabled': {'present': True}}}
        faith = {'id': 107, 'heads': {'religious_head': '4294967295', 'religious_head_title': None}, 'main_rite': '169'}
        rite = {'id': 169, 'faith': '107'}
        for mutation in ('head', 'parent', 'rite', 'membership'):
            a, f, r = copy.deepcopy(actor), copy.deepcopy(faith), copy.deepcopy(rite)
            if mutation == 'head': f['heads']['religious_head'] = '18373'
            elif mutation == 'parent': r['faith'] = '108'
            elif mutation == 'rite': a['rite_id'] = 170
            else: a['variables'] = {}
            with self.assertRaises(ValueError): adapter.evaluate_saved(reader, a, f, r, self.data, False)

    def test_verify_rejects_intermediate_gap_even_when_sum_and_final_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            start = self.data['saved_campaign']['date_raw']
            facts = {'run_id': 'test-only', 'product': 'li-yu-dao', 'case': self.data['case_id'],
                'scope': self.data['scope'], 'initial_flag': {'initial_flag_present': True},
                'initial_confirm_enabled': False, 'final_confirm_enabled': True, 'school_choice_actions': 0,
                'initial_saved': {'school_cooldown_present': True, 'headless': True, 'save_body_reads': 1,
                    'baseline_body_reads': 0, 'preserved_checkpoint': {'path': str(Path(temporary) / 'initial.ck3')}},
                'saved': {'school_cooldown_present': False, 'headless': True, 'save_body_reads': 1,
                    'baseline_body_reads': 0, 'checkpoint': {'path': str(Path(temporary) / 'final.ck3')}},
                'natural_intervals': [{'step_id': 'a', 'elapsed_hours': 24, 'date_raw': start + 25, 'confirm_enabled': False},
                    {'step_id': 'b', 'elapsed_hours': 24, 'date_raw': start + 48, 'confirm_enabled': True}],
                'elapsed_natural_hours': 48, 'elapsed_natural_days': 2,
                **{k: None for k in ('fresh_full_365_cycle', 'exact_expiry_date', 'cold_reload', 'formal_I3b', 'C3', 'I4_complete')}}
            path = Path(temporary) / 'i4-existing-school-cooldown-case-result.json'
            path.write_text(json.dumps(facts), encoding='utf-8')
            context = {'output': temporary, 'run_id': 'test-only', 'product': 'li-yu-dao',
                'case': self.data['case_id'], 'case_contract': self.data}
            with self.assertRaisesRegex(ValueError, 'Intermediate natural date gap'):
                adapter.verify_case(context)


class SelectedDetailCompletionGuards(unittest.TestCase):
    """Source09 can verify selection later while retaining a pending native ACK."""
    def setUp(self):
        self.frame = frame()
        self.key = adapter.contract()['decision_key']
        model = {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True, 'available': True,
            'decision_key': self.key, 'detail_decision_key': self.key, 'matching_row_count': 1,
            'native_revision': self.frame['native_revision'], 'connection_generation': 1, 'game_pid': 901,
            'played_character_id': 31254, 'date_raw': self.frame['date_raw'], 'detail_actor_reference_key': 31254,
            **{key: True for key in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified',
                'gui_owner_binding_verified', 'decisions_tree_complete', 'decisions_root_visible',
                'row_owner_verified', 'detail_tree_complete', 'detail_root_visible', 'detail_definition_available',
                'detail_definition_matches_target', 'detail_actor_binding_verified')}}
        self.selected = {'schema': 'ck3-ingame-decision-item-action-v1', 'step': 'select-ingame-decision-item-v1',
            'action': 'select', 'decision_key': self.key, 'postcondition_verified': True,
            'status': 'verified_selected_detail', 'verification_pending': False,
            'selected_after_verified': False, 'native_ack': {'selected_after_verified': False,
                'postcondition_verified': False, 'status': 'acknowledged_verification_pending', 'verification_pending': True},
            'later_actual_observation': copy.deepcopy(model)}
        self.observation = {'frame': copy.deepcopy(self.frame), 'model_after': copy.deepcopy(model)}

    def test_pending_native_ack_later_verified_actual_detail_accepted_unchanged(self):
        original = copy.deepcopy(self.selected)
        proof = adapter.validate_selected(self.selected, self.frame, self.observation, self.key)
        self.assertTrue(proof['postcondition_verified'])
        self.assertFalse(proof['original_ack_selected_after_verified'])
        self.assertEqual(self.selected, original)

    def test_unverified_or_missing_later_observation_rejected(self):
        for mutation in ('postcondition', 'pending', 'status', 'missing_later'):
            selected = copy.deepcopy(self.selected)
            if mutation == 'postcondition': selected['postcondition_verified'] = False
            elif mutation == 'pending': selected['verification_pending'] = True
            elif mutation == 'status': selected['status'] = 'acknowledged_verification_pending'
            else: selected.pop('later_actual_observation')
            with self.assertRaises(ValueError):
                adapter.validate_selected(selected, self.frame, self.observation, self.key)

    def test_wrong_later_key_actor_frame_or_independent_target_rejected(self):
        for mutation in ('key', 'actor', 'frame', 'current_target'):
            selected, current = copy.deepcopy(self.selected), copy.deepcopy(self.observation)
            if mutation == 'key': selected['later_actual_observation']['detail_decision_key'] = 'lyd_study_decision'
            elif mutation == 'actor': selected['later_actual_observation']['detail_actor_reference_key'] = 65865
            elif mutation == 'frame': selected['later_actual_observation']['date_raw'] += 24
            else: current['model_after']['decision_key'] = 'lyd_study_decision'
            with self.assertRaises(ValueError):
                adapter.validate_selected(selected, self.frame, current, self.key)


if __name__ == '__main__':
    unittest.main(verbosity=2)
