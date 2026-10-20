"""Real combined adapter entry with synthetic native IO; no game/runtime launch."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

import test_faith_e02_r19_hof_case as old
from ck3_mod_acceptance_cases import faith_e02_r19_ghw_adapter as A
from ck3_mod_acceptance_cases.faith_e02_ghw_observation_contract import ghw_scene_binding, ghw_decisions_visible
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


def decisions_tree(visible=True):
    return {'schema': 'ck3-native-gui-window-tree-inspection-v1',
        'read_only': True, 'window_kind': 'decisions', 'scope_root_name': 'decisions_view',
        'root_available': True, 'truncated': False,
        'widgets': [{'runtime_name': 'decisions_view', 'child_path': '',
            'effective_visible': visible}]}


class Client(old.Client):
    def __init__(self, *args, launch_rows=0, ghw_available=True, wrong_faith=False,
                 decisions_visible=True, census=None, open_error=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.launch_rows, self.ghw_available, self.wrong_faith = launch_rows, ghw_available, wrong_faith
        self.names, self.launch_selections = [], 0
        self.decisions_visible, self.census, self.open_error = decisions_visible, census, open_error

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        self.names.append(name)
        step = steps[0]
        tool, args = step['tool'], step.get('args', {})
        value = None
        if tool == 'ck3_inspect_gui_window_tree_v1' and args == {'window_kind': 'decisions'}:
            value = deepcopy(self.census) if self.census is not None else decisions_tree(self.decisions_visible)
        elif tool == 'ck3_open_ingame_decisions_v1':
            if self.open_error:
                self.calls.append(tool)
                row = {'id': name, 'ok': False, 'error': self.open_error}
                write_once(Path(self.c['output']) / (name + '.actual-results.json'), {'rows': [row]})
                return [row]
            self.decisions_visible = True
            value = {'accepted': True, 'postcondition_verified': True, 'status': 'verified_visible'}
        elif tool == 'ck3_query_player_religion_context_v1':
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
        elif tool == Q.EVENT_CONTEXT:
            value = {'accepted': True, 'current_event_window_context_ready': True,
                'current_event_window_context': {'schema': 'current-event-window-context-v1',
                    'status': 'available', 'current_event_instance_id': 777, 'date_raw': 53144328,
                    'snapshot_revision': 4, 'event_definition_key': 'synthetic.1',
                    'readiness': {'option_presentation_ready': True}, 'options': [
                        {'rendered_index': 0, 'native_option_index': 2, 'shown': True, 'enabled': True},
                        {'rendered_index': 1, 'native_option_index': 0, 'shown': True, 'enabled': True}]}}
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
        if tool == Q.EVENT_CONTEXT:
            row['after_snapshot'] = self.snapshot(require_event_free=False)
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


class DecisionsReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def observe(self, client):
        reader, _ = A.shared_opening_binding(client.c)
        return A.observe_ghw(client.c, client, reader(client.snapshot()), reader)

    def test_full_combined_entry_reuses_first_h2_open(self):
        c = context(self.root)
        client = Client(c)
        result = A.run_case(c, client)
        self.assertEqual(client.calls.count('ck3_open_ingame_decisions_v1'), 1)
        self.assertEqual(result['ghw_observation']['decisions_window_route'], 'reused_current_visible_readonly')
        self.assertNotIn('ghw-r19-open-decisions', client.names)
        self.assertTrue(result['ghw_observation']['current_group_qualified'])
        self.assertEqual(client.calls.count(Q.GHW_QUERY), 2)

    def test_hidden_census_uses_original_opener_once_then_independent_census(self):
        client = Client(context(self.root), decisions_visible=False)
        result = self.observe(client)
        self.assertEqual(result['decisions_window_route'], 'observed_hidden_original_once_opener')
        self.assertEqual(client.calls.count('ck3_open_ingame_decisions_v1'), 1)
        self.assertLess(client.names.index('ghw-r19-decisions-tree'), client.names.index('ghw-r19-open-decisions'))
        self.assertLess(client.names.index('ghw-r19-open-decisions'), client.names.index('ghw-r19-decisions-tree-after-open'))
        self.assertTrue(result['current_group_qualified'])

    def test_incomplete_or_unknown_census_never_means_hidden(self):
        mutations = [lambda t: t.update(truncated=True), lambda t: t.update(root_available=False),
            lambda t: t.update(window_kind='decision_detail'), lambda t: t.update(read_only=False),
            lambda t: t['widgets'][0].update(effective_visible=None),
            lambda t: t['widgets'][0].update(effective_visible=0),
            lambda t: t['widgets'][0].update(effective_visible=1),
            lambda t: t['widgets'].append(deepcopy(t['widgets'][0]))]
        for number, mutate in enumerate(mutations):
            with self.subTest(number=number):
                root = self.root / str(number)
                root.mkdir()
                tree = decisions_tree()
                mutate(tree)
                client = Client(context(root), census=tree)
                result = self.observe(client)
                self.assertNotIn('ck3_open_ingame_decisions_v1', client.calls)
                self.assertFalse(result['current_group_qualified'])
                self.assertIn('ghw-r19-decisions-visibility', result['errors'])
                self.assertEqual(client.calls.count(Q.GHW_QUERY), 2)

    def test_hidden_open_unknown_is_preserved_without_retry(self):
        message = 'BridgeUnavailableError: decision action already claimed with an unresolved result; no retry at any revision'
        client = Client(context(self.root), decisions_visible=False, open_error=message)
        result = self.observe(client)
        self.assertEqual(client.calls.count('ck3_open_ingame_decisions_v1'), 1)
        self.assertIn(message, result['errors']['ghw-r19-open-decisions'])
        self.assertFalse(result['current_group_qualified'])
        self.assertEqual(client.calls.count(Q.GHW_QUERY), 2)
        self.assertFalse(result['target_legality_observed'])

    def test_census_after_crosses_scene_no_open(self):
        class CrossScene(Client):
            drifted = False
            def execute_plan(self, steps, name, **kwargs):
                result = super().execute_plan(steps, name, **kwargs)
                if name == 'ghw-r19-decisions-tree':
                    self.drifted = True
                return result
            def snapshot(self, **kwargs):
                value = super().snapshot(**kwargs)
                if self.drifted:
                    value['date_raw'] += 1
                return value
        client = CrossScene(context(self.root))
        result = self.observe(client)
        self.assertNotIn('ck3_open_ingame_decisions_v1', client.calls)
        self.assertFalse(result['current_group_qualified'])
        self.assertIn('scene changed date_raw', result['errors']['ghw-r19-decisions-tree'])

    def test_scene_integer_lookalikes_reject_before_any_tool(self):
        client = Client(context(self.root))
        reader, _ = A.shared_opening_binding(client.c)
        binding = reader(client.snapshot())
        for key in ('native_revision', 'connection_generation', 'game_pid', 'played_character_id', 'date_raw'):
            for value in (True, float(binding[key]), str(binding[key])):
                with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                    bad = dict(binding)
                    bad[key] = value
                    A.observe_ghw(client.c, client, bad, reader)
        self.assertEqual(client.calls, [])

    def test_typed_scene_and_census_json_round_trip(self):
        client = Client(context(self.root))
        reader, _ = A.shared_opening_binding(client.c)
        binding = ghw_scene_binding(reader(client.snapshot()))
        self.assertEqual(ghw_scene_binding(json.loads(json.dumps(binding))), binding)
        for visible in (True, False):
            tree = decisions_tree(visible)
            self.assertIs(ghw_decisions_visible(json.loads(json.dumps(tree))), visible)
        for key in binding:
            incomplete = dict(binding)
            del incomplete[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                ghw_scene_binding(incomplete)


if __name__ == '__main__':
    unittest.main(verbosity=2)
