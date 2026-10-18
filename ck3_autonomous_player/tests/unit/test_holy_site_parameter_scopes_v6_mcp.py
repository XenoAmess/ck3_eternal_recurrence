"""Actual existing MCP knowledge boundary: distinct static parameter scopes."""
from pathlib import Path
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from mcp import Client
from xar_autoplayer.bridge.mcp_server import create_server

class NoGame:
    def __init__(self): self.calls = []
    def refuse(self, name):
        self.calls.append(name)
        raise AssertionError('Static planning called game: '+name)
    def capabilities(self): return self.refuse('capabilities')
    def take_snapshot(self): return self.refuse('take_snapshot')
    def take_snapshot_without_native_command_history(self): return self.refuse('take_snapshot_without_native_command_history')
    def execute_step(self, *args, **kwargs): return self.refuse('execute_step')
    def wait_for_change(self, *args, **kwargs): return self.refuse('wait_for_change')
    def _execute_primitive_step(self, *args, **kwargs): return self.refuse('_execute_primitive_step')

class FaithRiteParameterScopeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_tool_calls = 0
    async def test_adoption_keeps_main_current_and_personal_distinct(self):
        driver = NoGame()
        async with Client(create_server(driver)) as client:
            tool = next(t for t in (await client.session.list_tools()).tools
                        if t.name == 'ck3_query_holy_site_planning_knowledge_v1')
            self.assertEqual(set(tool.input_schema['properties']), {'action', 'ck3_build'})
            type(self).actual_mcp_tool_calls += 1
            response = await client.session.call_tool(tool.name, {'action': 'adopt'})
            self.assertFalse(response.is_error)
            output = response.structured_content
            scope = output['knowledge']['v5_clarifications']['cross_religion_adoption']['parameter_scopes_v6']
            self.assertEqual(scope['faith_query']['lookup'], 'queried_faith.main_rite.boolean_parameters')
            self.assertEqual(scope['current_rite_query']['lookup'], 'supplied_rite.boolean_parameters')
            self.assertEqual(scope['personal_query']['lookup'], 'queried_character.owned_personal_tenet_definitions.personal_parameters')
            self.assertEqual(scope['consumers']['directional_adoption'], 'actor.faith.main_rite')
            self.assertEqual(scope['consumers']['allow_any_adoption'], 'actor.current_rite')
            self.assertEqual(scope['consumers']['building_current_rite_branches'], 'barony_holder.current_rite')
            self.assertFalse(scope['personal_syncretism_has_directional_actor_parameter'])
            self.assertEqual(scope['selection_ui']['rite_core_column']['displayed_heading_zh'], '信条')
            self.assertEqual(scope['selection_ui']['personal_column']['displayed_heading_zh'], '你的个人信条')
            self.assertFalse(scope['current_state_observed'])
            self.assertFalse(scope['new_live_query_or_business_result'])
            self.assertFalse(output['state_observed'])
            self.assertIsNone(output['native_legality'])
            self.assertFalse(output['action_ready'])
            unresolved = output['knowledge']['v5_clarifications']['cross_religion_adoption']['unresolved_native_observations']
            self.assertEqual(unresolved, [])
            adopt = output['knowledge']['v5_clarifications']['cross_religion_adoption']
            reform = output['knowledge']['v5_clarifications']['reform_mcp_scope']
            self.assertTrue(reform['both_directions_new_live_examples'])
            self.assertFalse(reform['historical_source_baseline']['both_directions_new_live_examples_at_that_time'])
            self.assertNotIn('current_published_write_gap', reform)
            self.assertIn('ck3_execute_player_rite_creation_action_v1', reform['published_tools'])
            self.assertTrue(reform['retained_build_configuration']['historical_only'])
            self.assertEqual([m['id'] for m in reform['completed_milestones']], ['R0019','R0022'])
            self.assertEqual([m['reform_outcome'] for m in reform['completed_milestones']], ['create_faith','edit_rite'])
            for milestone in reform['completed_milestones']:
                self.assertEqual(milestone['machine_id'], '4-8e1c2f1861')
                self.assertTrue(all(s['sha256'] for s in milestone['sources']))
            self.assertEqual(reform['completed_milestones'], adopt['completed_cross_religion_milestones'])
            self.assertFalse(reform['current_state_observed'])
            self.assertIsNone(reform['native_legality'])
            self.assertFalse(reform['action_ready'])
            for source in scope['sources']:
                self.assertTrue(source['repository_path'].startswith('docs/ck3-native-ai/'))
                self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')
            self.assertIsNone(re.search(r'[A-Za-z]:[\\/]', json.dumps(scope)))
        self.assertEqual(driver.calls, [])

if __name__ == '__main__':
    unittest.main()
