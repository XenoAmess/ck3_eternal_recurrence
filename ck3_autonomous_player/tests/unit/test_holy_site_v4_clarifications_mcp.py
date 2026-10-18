"""Seven-action source corrections through the existing real MCP tool.

The static tool must never ask a gameplay driver for state or submit a command.
This is knowledge/transport verification, not native or live qualification.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server

TOOL = "ck3_query_holy_site_planning_knowledge_v1"
ACTIONS = ("adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic")


class NoGameDriver:
    def __init__(self):
        self.calls = []

    def refuse(self, name):
        self.calls.append(name)
        raise RuntimeError("static planning knowledge attempted gameplay operation: " + name)

    def capabilities(self): return self.refuse("capabilities")
    def take_snapshot(self): return self.refuse("take_snapshot")
    def take_snapshot_without_native_command_history(self): return self.refuse("take_snapshot_without_native_command_history")
    def execute_step(self, *args, **kwargs): return self.refuse("execute_step")
    def wait_for_change(self, *args, **kwargs): return self.refuse("wait_for_change")
    def _execute_primitive_step(self, *args, **kwargs): return self.refuse("_execute_primitive_step")


class V4ClarificationsMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []
    actual_game_driver_calls = []

    async def test_seven_action_corrections_static_scope_and_portable_deepcopy(self):
        driver = NoGameDriver()
        type(self).actual_game_driver_calls = driver.calls
        outputs = {}
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            tool = next(item for item in (await client.session.list_tools()).tools if item.name == TOOL)
            self.assertEqual(set(tool.input_schema["properties"]), {"action", "ck3_build"})
            for action in ACTIONS:
                arguments = {"action": action}
                reply = await client.session.call_tool(TOOL, arguments)
                self.actual_mcp_results.append({"arguments": arguments, "response": deepcopy(reply.structured_content), "is_error": reply.is_error})
                self.assertFalse(reply.is_error)
                output = reply.structured_content
                outputs[action] = output
                self.assertFalse(output["state_observed"])
                self.assertIsNone(output["native_legality"])
                self.assertFalse(output["action_ready"])
                details = output["knowledge"]["v4_clarifications"]
                self.assertFalse(details["current_state_observed"])
                self.assertIsNone(details["native_legality"])
                self.assertFalse(details["action_ready"])
                self.assertEqual(details["official_terms"]["T-COUNTY"]["wording"], "伯爵领")
                self.assertIn("圣职区", details["official_terms"]["T-CLERICAL-REGION"]["wording"])
                self.assertEqual(details["official_terms"]["T-WISDOM"]["wording"], "智慧之地")
                self.assertIn("总宝物稀有度等级", details["official_terms"]["T-RARITY"]["wording"])
                self.assertIn("有效稀有度", details["official_terms"]["T-RARITY"]["avoid_or_context_limited"])
                self.assertIn("HOLY_SITE_TOTAL_RARITY_LEVELS", [row["key"] for row in details["official_terms"]["T-RARITY"]["official_entries"]])
                self.assertTrue(details["grade_and_benefit_layers"]["major_is_not_a_universal_gate"])
                self.assertIn("No major gate", details["grade_and_benefit_layers"]["local_county_scaled"])
                self.assertIn("does not call the current rarity producer", details["current_cached_and_projection"]["cached_scaling"])
                self.assertIn("same_native_evaluation_as_total=false", details["current_cached_and_projection"]["matrix_projection"])
                self.assertFalse(details["modifier_receipt_observed"])
                self.assertEqual((details["capacity"]["total_max"], details["capacity"]["major_max"]), (9, 3))
                self.assertTrue(details["capacity"]["total_includes_major"])
                self.assertTrue(details["capacity"]["over_cap_is_not_raised_max"])
                self.assertEqual(details["capacity"]["max_runtime_mutation"], "no_supported_original_progression_found_in_reviewed_scope")
                self.assertEqual(details["capacity"]["absolute_native_write_impossibility"], "unknown")
                self.assertFalse(details["capacity"]["current_limit_values_observed"])
                self.assertFalse(details["relic_management"]["ai_natural_execution_observed"])
                self.assertIn("cleanup decision", details["relic_management"]["ai_risk"])
                self.assertIn("executing actor", details["opinion_and_resource_roles"]["direction"])
                self.assertEqual(details["opinion_and_resource_roles"]["positive"]["opinion"], 15)
                self.assertEqual(details["opinion_and_resource_roles"]["negative"]["opinion"], -20)
                example = details["opinion_and_resource_roles"]["conditional_lower_replacement_example"]
                self.assertEqual((example["base_piety_delta"], example["base_devotion_delta"]), (-750, -500))
                self.assertFalse(example["actual_net_observed"])
                self.assertIn("presence tokens", details["parameter_predicates"]["storage"])
                self.assertEqual(len(details["parameter_predicates"]["known_parameter_sites"]), 6)
                # Portable values are shipped in code; paths only identify source resources.
                portable = json.dumps(details, ensure_ascii=False)
                self.assertIsNone(re.search(r"[A-Za-z]:[\\/]", portable))
                self.assertNotIn("/workspace/", portable)
                self.assertIn("historical observations", details["history_boundary"])
            expected = deepcopy(outputs["adopt"]["knowledge"]["v4_clarifications"])
            outputs["adopt"]["knowledge"]["v4_clarifications"]["official_terms"].clear()
            reply = await client.session.call_tool(TOOL, {"action": "adopt"})
            self.actual_mcp_results.append({"arguments": {"action": "adopt"}, "response": deepcopy(reply.structured_content), "is_error": reply.is_error})
            self.assertEqual(reply.structured_content["knowledge"]["v4_clarifications"], expected)
            reply = await client.session.call_tool(TOOL, {"action": "promote", "ck3_build": "1.20.1"})
            self.actual_mcp_results.append({"arguments": {"action": "promote", "ck3_build": "1.20.1"}, "response": deepcopy(reply.structured_content), "is_error": reply.is_error})
            self.assertFalse(reply.is_error)
            self.assertIsNone(reply.structured_content["knowledge"])
            self.assertFalse(reply.structured_content["action_ready"])
        self.assertEqual(driver.calls, [])


if __name__ == "__main__":
    unittest.main()
