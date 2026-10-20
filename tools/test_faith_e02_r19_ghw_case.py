"""Real combined adapter entry with synthetic native IO; no game/runtime launch."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

import test_faith_e02_r19_hof_case as old
from ck3_mod_acceptance_cases import faith_e02_r19_ghw_adapter as A
import faith_e02_r19_ghw_queue as Q
from ck3_mod_acceptance_client import write_once


def context(root, *, confirm=False):
    c = old.context(root, confirm=confirm)
    c['case'] = A.CASE
    c['case_contract'].update(schema='faith-engine-e02-r19-hof-ghw-combined-case-v1', case=A.CASE,
        ghw_launch_confirmation_allowed=False, calendar_countdown_qualified=False,
        pilgrimage_completion_inferred=False, all_tools_declared_before_prepare=True)
    c['case_spec'].update(id=A.CASE,
        required_mcp_tools=sorted(A.SCENE_TOOLS | A.LIFECYCLE_TOOLS | ({Q.CONFIRM} if confirm else set())),
        opt_in_read_only_mcp_tools=sorted(A.READONLY_TOOLS))
    return c


class Client(old.Client):
    def __init__(self, *args, launch_rows=0, ghw_available=True, wrong_faith=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.launch_rows, self.ghw_available, self.wrong_faith = launch_rows, ghw_available, wrong_faith
        self.names, self.launch_selections = [], 0

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        self.names.append(name)
        step = steps[0]
        tool, args = step['tool'], step.get('args', {})
        value = None
        if tool == 'ck3_query_player_religion_context_v1':
            value = {'available': True, 'played_character_id': 31254,
                'faith_id': 103, 'rite_id': 150, 'faith_main_rite_id': 150, 'religion_id': 26}
        elif tool == Q.GHW_QUERY:
            value = {'schema': 'ck3_12004_player_ghw_permissions_v1',
                'available': self.ghw_available, 'frame_verified': self.ghw_available,
                'loaded_source_pins_verified': self.ghw_available, 'read_only': True,
                'launch_permission_inferred': False, 'date_raw': 53144328,
                'played_character_id': 31254, 'faith_id': 999 if self.wrong_faith else 103,
                'religion_id': 26, 'capture_epoch': 77 if name.endswith('-a') else 81,
                'snapshot_revision': 4,
                'variables': {'available_any': False, 'all_fields_observed': False,
                    'remaining_unit': 'signed32_native_scalar_counter_calendar_unqualified',
                    'fields': [{'key': key, 'scope': scope, 'read_available': False, 'present': None,
                        'expiry_date_raw': None, 'remaining_raw': None} for key, scope in (
                            ('variable_ghw_unlocked', 'religion'), ('variable_first_ghw_cooldown', 'religion'),
                            ('variable_ghw_cooldown', 'faith'), ('variable_ghw_global_unlocking_cooldown', 'global'))]},
                'object_links': {'available': False, 'ghw': 'unknown', 'war': 'unknown'}}
        elif tool == Q.PILGRIMAGE_QUERY:
            value = {'activity_count': 0, 'absence_is_completion': False}
        elif tool in {Q.QUERY, 'ck3_select_ingame_decision_item_v1'} and args.get('decision_key') == Q.LAUNCH_DECISION:
            if tool == Q.QUERY:
                value = {'available': self.launch_rows == 1, 'decision_key': Q.LAUNCH_DECISION,
                    'matching_row_count': self.launch_rows, 'played_character_id': 31254, 'date_raw': 53144328,
                    'detail_actor_reference_key': 31254,
                    **{k: True for k in ('detail_definition_matches_target', 'detail_tree_complete',
                        'detail_root_visible', 'detail_actor_binding_verified')},
                    'selected_terms': {'available': False,
                        'unavailable_reason': 'selected_terms_nonempty_parameters_not_yet_qualified',
                        'named_parameter_count': 2}}
            else:
                self.launch_selections += 1
                value = {'accepted': True}
        if value is None:
            return super().execute_plan(steps, name, timeout=timeout, reserve=reserve)
        self.calls.append(tool)
        row = {'id': name, 'ok': True, 'error': None, 'result': value}
        write_once(Path(self.c['output']) / (name + '.actual-results.json'), {'rows': [row]})
        return [row]


class CombinedEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_readonly_h2_then_two_current_ghw_reads_absent_launch(self):
        c = context(self.root)
        client = Client(c)
        value = A.run_case(c, client)
        self.assertTrue(value['readonly_eligibility_observed'])
        self.assertTrue(value['ghw_observation']['current_group_qualified'])
        self.assertEqual(value['ghw_observation']['launch_row_classification'], 'absent_in_actual_list')
        self.assertEqual(client.calls.count(Q.GHW_QUERY), 2)
        self.assertEqual(client.submitted, 0)
        self.assertEqual(client.launch_selections, 0)
        self.assertFalse(value['business_pass'])
        self.assertFalse(value['ghw_observation']['target_legality_observed'])
        self.assertNotEqual(value['ghw_observation']['first_ghw']['capture_epoch'],
            value['ghw_observation']['first_ghw']['snapshot_revision'])

    def test_unaﬀordable_h2_still_reads_independent_state_then_ghw_without_topup(self):
        c = context(self.root, confirm=True)
        client = Client(c, affordable=False)
        value = A.run_case(c, client)
        self.assertIn('ordinary legality rejected', value['rejection_reason'])
        self.assertEqual(client.submitted, 0)
        self.assertFalse((self.root / 'stable-ledger').exists())
        self.assertTrue(value['poststate_captured_before_event_policy'])
        self.assertTrue(value['ghw_observation']['current_group_qualified'])

    def test_confirm_timeout_keeps_one_submit_poststate_event_before_ghw(self):
        c = context(self.root, confirm=True)
        client = Client(c, unknown=True, post_event=True)
        value = A.run_case(c, client)
        self.assertEqual(client.submitted, 1)
        self.assertTrue(value['head_creation_observed'])
        self.assertTrue(value['h2_business_pass'])
        self.assertFalse(value['business_pass'])
        self.assertEqual(value['event_policy']['status'], 'DRAINED')
        self.assertLess(client.names.index('hof-r19-governance-after'),
            client.names.index('hof-r19-post-event-01-select-once'))
        self.assertLess(client.names.index('hof-r19-post-event-01-select-once'),
            client.names.index('ghw-r19-variables-and-objects-a'))
        self.assertEqual(len(list((self.root / 'stable-ledger').glob('*.submit-once.json'))), 1)

    def test_existing_head_is_observed_without_recreate_and_one_actual_launch_selection(self):
        c = context(self.root, confirm=True)
        client = Client(c, existing_head=True, launch_rows=1)
        value = A.run_case(c, client)
        self.assertEqual(client.submitted, 0)
        self.assertEqual(client.launch_selections, 1)
        observed = value['ghw_observation']
        self.assertEqual(observed['launch_row_classification'], 'one_actual_row')
        self.assertEqual(observed['actual_selected_launch_detail']['selected_terms']['named_parameter_count'], 2)
        self.assertFalse(observed['target_legality_observed'])
        self.assertFalse(observed['director_slot25_complete'])

    def test_ambiguous_launch_does_not_select(self):
        c = context(self.root)
        client = Client(c, launch_rows=2)
        value = A.run_case(c, client)
        self.assertEqual(client.launch_selections, 0)
        self.assertEqual(value['ghw_observation']['launch_row_classification'], 'ambiguous_actual_rows')

    def test_unavailable_unknowns_stay_unknown(self):
        c = context(self.root)
        value = A.run_case(c, Client(c, ghw_available=False))['ghw_observation']
        self.assertFalse(value['current_group_qualified'])
        self.assertIsNone(value['first_ghw']['variables']['fields'][0]['present'])
        self.assertEqual(value['first_ghw']['object_links']['war'], 'unknown')

    def test_ghw_other_faith_is_rejected_as_current_group(self):
        c = context(self.root)
        value = A.run_case(c, Client(c, wrong_faith=True))['ghw_observation']
        self.assertFalse(value['current_group_qualified'])
        self.assertIn('group_identity', value['errors'])

    def test_old_exact_set_or_unrelated_execution_permission_is_rejected(self):
        c = context(self.root)
        c['case_spec']['required_mcp_tools'].remove(Q.GHW_QUERY)
        with self.assertRaises(ValueError): A.validate_contract(c)
        c['case_spec']['required_mcp_tools'].append(Q.GHW_QUERY)
        c['case_spec']['opt_in_player_pilgrimage_execution'] = True
        with self.assertRaises(ValueError): A.validate_contract(c)

    def test_no_launch_confirm_world_or_raw_queue_path(self):
        for tool, args in ((Q.CONFIRM, {'decision_key': Q.LAUNCH_DECISION, 'expected_outcome': 'decision_closed'}),
                ('ck3_declare_war', {}), ('ck3_save_checkpoint', {}), ('ck3_set_speed', {}),
                (Q.GHW_QUERY, {'variable_key': 'arbitrary'}), (Q.GHW_QUERY, {'expected_revision': True})):
            with self.subTest(tool=tool), self.assertRaises(ValueError):
                Q.validate({'steps': [{'id': 'forbidden', 'tool': tool, 'args': args,
                    'fresh_revision': True, 'continue_on_error': True}]})


if __name__ == '__main__':
    unittest.main(verbosity=2)
