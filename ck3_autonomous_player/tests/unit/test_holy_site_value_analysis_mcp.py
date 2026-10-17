"""Only the new holy-site value payloads through a real MCP ClientSession."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server

TOOL = "ck3_query_holy_site_planning_knowledge_v1"
FIELD_ROOTS = {"promote": "grade_value_comparison", "demote": "grade_value_comparison",
    "adopt": "value_analysis", "create": "value_analysis", "enshrine_relic": "shared_relic_value",
    "remove_relic": "shared_relic_value", "abandon": "shared_relic_value"}
# Frozen from the three reviewed value packages; coefficients are not live gains.
VALUE_CASES = [{'case_id': 'wisdom_county_learning_is_not_promotion_delta', 'assertions': [{'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'county_holder_fixed_regular_and_eminent', 0, 'modifier_key'], 'equals': 'learning'}, {'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'county_holder_fixed_regular_and_eminent', 0, 'coefficient'], 'equals': 2}, {'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'source_calculated_examples', 0, 'eminent_only_increment'], 'key_absent': 'learning'}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'county_holder_fixed_regular_and_eminent', 0, 'modifier_key'], 'equals': 'learning'}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'county_holder_fixed_regular_and_eminent', 0, 'coefficient'], 'equals': 2}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'source_calculated_examples', 0, 'eminent_only_increment'], 'key_absent': 'learning'}, {'action': 'adopt', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'site_of_wisdom', 'county_holder_fixed', 'learning'], 'equals': 2}, {'action': 'create', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'site_of_wisdom', 'county_holder_fixed', 'learning'], 'equals': 2}]}, {'case_id': 'diplomacy_per_piety_does_not_stack', 'assertions': [{'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'faith_character_fixed_eminent_increment', 0, 'modifier_key'], 'equals': 'diplomacy_per_piety_level'}, {'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'faith_character_fixed_eminent_increment', 0, 'coefficient'], 'equals': 1}, {'action': 'promote', 'path': ['knowledge', 'grade_value_comparison', 'source_calculated_examples', 2, 'raw_modifier_coefficient_delta', 'diplomacy_per_piety_level'], 'equals': 0}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'faith_character_fixed_eminent_increment', 0, 'modifier_key'], 'equals': 'diplomacy_per_piety_level'}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'type_effects', 'site_of_wisdom', 'faith_character_fixed_eminent_increment', 0, 'coefficient'], 'equals': 1}, {'action': 'demote', 'path': ['knowledge', 'grade_value_comparison', 'source_calculated_examples', 2, 'raw_modifier_coefficient_delta', 'diplomacy_per_piety_level'], 'equals': 0}, {'action': 'adopt', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'nadjaf', 'faith_eminent_fixed', 'diplomacy_per_piety_level'], 'equals': 1}, {'action': 'adopt', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'site_of_wisdom', 'faith_eminent_fixed', 'diplomacy_per_piety_level'], 'equals': 1}, {'action': 'create', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'nadjaf', 'faith_eminent_fixed', 'diplomacy_per_piety_level'], 'equals': 1}, {'action': 'create', 'path': ['knowledge', 'value_analysis', 'shared', 'declared_type_coefficients', 'site_of_wisdom', 'faith_eminent_fixed', 'diplomacy_per_piety_level'], 'equals': 1}]}, {'case_id': 'shared_faith_benefit_scope', 'assertions': [{'action': 'adopt', 'path': ['knowledge', 'value_analysis', 'source_refs', 'NS01', 'sha256'], 'equals': '9a5eeb18664f134dfb52b9d94b94589340dd24518cf76a3b9895cd82dce83d79'}, {'action': 'create', 'path': ['knowledge', 'value_analysis', 'source_refs', 'NS01', 'sha256'], 'equals': '9a5eeb18664f134dfb52b9d94b94589340dd24518cf76a3b9895cd82dce83d79'}, {'action': 'enshrine_relic', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'cached_value_scope'], 'equals': 'one global site+18/+1C, not per-Faith Active'}, {'action': 'enshrine_relic', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'faithwide_actual_producer', 'gates'], 'contains': '2441F30 county holder current Faith fullID equals requested Faith fullID'}, {'action': 'remove_relic', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'cached_value_scope'], 'equals': 'one global site+18/+1C, not per-Faith Active'}, {'action': 'remove_relic', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'faithwide_actual_producer', 'gates'], 'contains': '2441F30 county holder current Faith fullID equals requested Faith fullID'}, {'action': 'abandon', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'cached_value_scope'], 'equals': 'one global site+18/+1C, not per-Faith Active'}, {'action': 'abandon', 'path': ['knowledge', 'shared_relic_value', 'state_model', 'faithwide_actual_producer', 'gates'], 'contains': '2441F30 county holder current Faith fullID equals requested Faith fullID'}]}, {'case_id': 'swap_returns_actor', 'assertions': [{'action': 'enshrine_relic', 'path': ['knowledge', 'shared_relic_value', 'action', 'nonempty_replacement', 'old_artifact_recipient'], 'contains': 'current command actor'}]}, {'case_id': 'remove_returns_actor', 'assertions': [{'action': 'remove_relic', 'path': ['knowledge', 'shared_relic_value', 'action', 'normal_recipient'], 'contains': 'current command actor'}]}, {'case_id': 'last_faith_abandon_returns_county_holder', 'assertions': [{'action': 'abandon', 'path': ['knowledge', 'shared_relic_value', 'action', 'return_branches', 0, 'recipient'], 'equals': None}, {'action': 'abandon', 'path': ['knowledge', 'shared_relic_value', 'action', 'return_branches', 1, 'recipient'], 'equals': 'county holder at execution, whether or not actor/same Faith/recognizer'}]}]


class _NoGameDriver:
    def __init__(self):
        self.calls = []

    def _refuse(self, operation):
        self.calls.append(operation)
        raise AssertionError("static value knowledge consulted CK3: " + operation)

    def capabilities(self): return self._refuse("capabilities")
    def take_snapshot(self): return self._refuse("take_snapshot")
    def take_snapshot_without_native_command_history(self): return self._refuse("take_snapshot_without_native_command_history")
    def execute_step(self, *args, **kwargs): return self._refuse("execute_step")
    def wait_for_change(self, *args, **kwargs): return self._refuse("wait_for_change")
    def _execute_primitive_step(self, *args, **kwargs): return self._refuse("_execute_primitive_step")


def _at(value, path):
    for key in path:
        value = value[key]
    return value


class HolySiteValueAnalysisMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []
    actual_game_driver_calls = []

    async def test_new_value_fields_player_distinctions_and_static_boundaries(self):
        driver = _NoGameDriver()
        self.actual_game_driver_calls[:] = driver.calls
        type(self).actual_game_driver_calls = driver.calls
        results = {}
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for action, field in FIELD_ROOTS.items():
                arguments = {"action": action, "ck3_build": "1.20.0.4"}
                reply = await client.session.call_tool(TOOL, arguments)
                self.actual_mcp_results.append({"role": "new_value_action", "arguments": arguments,
                    "response": deepcopy(reply.model_dump(mode="json"))})
                self.assertFalse(reply.is_error, action)
                value = reply.structured_content
                self.assertEqual(value["qualification"], "source_reviewed_static")
                self.assertIs(value["state_observed"], False)
                self.assertIsNone(value["native_legality"])
                self.assertIs(value["action_ready"], False)
                self.assertIn(field, value["knowledge"])
                results[action] = value
            for case in VALUE_CASES:
                with self.subTest(case=case["case_id"]):
                    for check in case["assertions"]:
                        action, path = check["action"], check["path"]
                        self.assertEqual(path[:2], ["knowledge", FIELD_ROOTS[action]])
                        actual = _at(results[action], path)
                        if "equals" in check:
                            self.assertIs(type(actual), type(check["equals"]), check)
                            self.assertEqual(actual, check["equals"], check)
                        elif "contains" in check:
                            self.assertIn(check["contains"], actual, check)
                        else:
                            self.assertIsInstance(actual, dict)
                            self.assertNotIn(check["key_absent"], actual, check)
            # A caller annotation to the new field cannot mutate a later reply.
            expected = deepcopy(results["promote"]["knowledge"]["grade_value_comparison"])
            results["promote"]["knowledge"]["grade_value_comparison"].clear()
            arguments = {"action": "promote", "ck3_build": "1.20.0.4"}
            fresh = await client.session.call_tool(TOOL, arguments)
            self.actual_mcp_results.append({"role": "new_value_deep_copy", "arguments": arguments,
                "response": deepcopy(fresh.model_dump(mode="json"))})
            self.assertFalse(fresh.is_error)
            self.assertEqual(fresh.structured_content["knowledge"]["grade_value_comparison"], expected)
            self.assertIs(fresh.structured_content["state_observed"], False)
            self.assertIsNone(fresh.structured_content["native_legality"])
            self.assertIs(fresh.structured_content["action_ready"], False)
            arguments = {"action": "promote", "ck3_build": "1.20.1"}
            foreign = await client.session.call_tool(TOOL, arguments)
            self.actual_mcp_results.append({"role": "unsupported_value_build", "arguments": arguments,
                "response": deepcopy(foreign.model_dump(mode="json"))})
            self.assertFalse(foreign.is_error)
            self.assertEqual(foreign.structured_content["qualification"], "unsupported_build")
            self.assertIsNone(foreign.structured_content["knowledge"])
            self.assertIs(foreign.structured_content["state_observed"], False)
            self.assertIsNone(foreign.structured_content["native_legality"])
            self.assertIs(foreign.structured_content["action_ready"], False)
        self.assertEqual(len(self.actual_mcp_results), 9)
        self.assertEqual(driver.calls, [])


if __name__ == "__main__":
    unittest.main()
