"""New V5 decisions through the existing MCP tool; never native/live credit."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server

TOOL = "ck3_query_holy_site_planning_knowledge_v1"


class NoGameDriver:
    def __init__(self):
        self.calls = []

    def refuse(self, name):
        self.calls.append(name)
        raise RuntimeError("static knowledge attempted gameplay operation: " + name)

    def capabilities(self): return self.refuse("capabilities")
    def take_snapshot(self): return self.refuse("take_snapshot")
    def take_snapshot_without_native_command_history(self): return self.refuse("take_snapshot_without_native_command_history")
    def execute_step(self, *args, **kwargs): return self.refuse("execute_step")
    def wait_for_change(self, *args, **kwargs): return self.refuse("wait_for_change")
    def _execute_primitive_step(self, *args, **kwargs): return self.refuse("_execute_primitive_step")


class V5ClarificationsMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_summaries = []
    actual_game_driver_calls = []

    async def test_v5_new_decision_boundaries_existing_tool(self):
        driver = NoGameDriver()
        type(self).actual_game_driver_calls = driver.calls
        outputs = {}

        async def query(client, arguments):
            reply = await client.session.call_tool(TOOL, arguments)
            self.assertFalse(reply.is_error)
            output = reply.structured_content
            payload = json.dumps(output, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            self.actual_mcp_summaries.append({"arguments": arguments, "response_sha256": hashlib.sha256(payload).hexdigest(),
                "response_bytes": len(payload), "is_error": reply.is_error,
                "state_observed": output["state_observed"], "native_legality": output["native_legality"],
                "action_ready": output["action_ready"]})
            self.assertFalse(output["state_observed"])
            self.assertIsNone(output["native_legality"])
            self.assertFalse(output["action_ready"])
            return output

        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            tool = next(item for item in (await client.session.list_tools()).tools if item.name == TOOL)
            self.assertEqual(set(tool.input_schema["properties"]), {"action", "ck3_build"})
            for action in ("adopt", "create", "enshrine_relic", "remove_relic", "abandon"):
                outputs[action] = await query(client, {"action": action})
                v5 = outputs[action]["knowledge"]["v5_clarifications"]
                self.assertFalse(v5["state_observed"])
                self.assertIsNone(v5["native_legality"])
                self.assertFalse(v5["action_ready"])
                self.assertFalse(v5["runtime_file_access_required"])
                portable = json.dumps(v5, ensure_ascii=False)
                self.assertIsNone(re.search(r"[A-Za-z]:[\\/]", portable))
                self.assertNotIn("/workspace/", portable)
                self.assertEqual(v5["source_payloads"]["adoption"]["sha256"],
                    "d0ba1e5b51c8587e461d33199c2d96bfd5ca5e7f79bee72edc398eda65f9a950")
                self.assertIn("v4_clarifications", outputs[action]["knowledge"])

            adopt = outputs["adopt"]["knowledge"]["v5_clarifications"]
            routes = adopt["cross_religion_adoption"]["directional_routes"]
            self.assertEqual(len(routes), 2)
            route_text = json.dumps(routes, ensure_ascii=False)
            self.assertIn("tenet_islamic_syncretism", route_text)
            self.assertIn("tenet_christian_syncretism", route_text)
            self.assertIn("astray", route_text)
            self.assertIn("F must satisfy relation and hostility together; G may differ from F",
                adopt["cross_religion_adoption"]["formula"]["witness_rule"])
            self.assertFalse(adopt["cross_religion_adoption"]["action_ready"])
            self.assertTrue(adopt["reform_mcp_scope"]["both_directions_new_live_examples"])
            self.assertIn("not current running", adopt["reform_mcp_scope"]["retained_build_configuration"]["observation_kind"])

            buildings = outputs["create"]["knowledge"]["v5_clarifications"]["special_buildings"]
            self.assertFalse(buildings["business_pass"])
            self.assertIsNone(buildings["native_legality"])
            building_text = json.dumps(buildings, ensure_ascii=False)
            self.assertIn("is_enabled", building_text)
            self.assertIn("can_construct", building_text)
            self.assertIn("barony", building_text)
            self.assertNotIn("can_use", building_text)

            for action in ("enshrine_relic", "remove_relic"):
                v5 = outputs[action]["knowledge"]["v5_clarifications"]
                ai = v5["relic_ai_and_cb"]
                self.assertFalse(ai["current_actor_admission_observed"])
                self.assertFalse(ai["natural_execution_observed"])
                self.assertFalse(ai["actor_admission"]["realm_at_war_excluded"])
                self.assertEqual(ai["actor_admission"]["human_protection_checks_exactly"],
                    ["top_liege", "actor currentFaith religious_head"])
                self.assertIn("AND NOT OwnSite", ai["per_item"]["effect_B"])
                self.assertEqual(ai["CB_AI_local_rules"]["AI_zeal_minimum"], 100)
                self.assertFalse(ai["CB_AI_local_rules"]["zealous_trait_bypass_for_AI_100_gate"])
                self.assertFalse(ai["CB_AI_local_rules"]["ordinary_item_hostility_2_gate_present"])
                opinion = v5["opinion_roles"]
                self.assertIn("subject's opinion of A", opinion["direction"])
                self.assertIn("old.rarity >= new.rarity", opinion["positive_15"]["nonempty_total_gate"])
                self.assertEqual(len(opinion["negative_20_when_L"]), 5)
                self.assertFalse(opinion["negative_20_when_not_L"]["separate_head_of_faith_loop"])
                self.assertFalse(opinion["duration"]["default_stacking"])

            returned = outputs["abandon"]["knowledge"]["v5_clarifications"]["last_faith_return"]
            self.assertEqual(returned["identities"]["H"], "S.holy_site_county.holder, saved once before return loop")
            cases = {row["case"]: row for row in returned["decision_table"]}
            self.assertIn("No return loop", cases["another associated Faith remains"]["transfer"])
            self.assertIn("no actor/donor/HoF fallback", cases["last associated Faith, H absent"]["transfer"])
            self.assertIn("set_owner target H", cases["last associated Faith, H exists, enshrined objects exist"]["transfer"])
            self.assertIn("not explicit removal callback", returned["different_path_comparison"]["Abandon_last_Faith"])

            expected = deepcopy(adopt)
            adopt["cross_religion_adoption"]["directional_routes"].clear()
            again = await query(client, {"action": "adopt"})
            self.assertEqual(again["knowledge"]["v5_clarifications"], expected)
            unsupported = await query(client, {"action": "adopt", "ck3_build": "1.20.1"})
            self.assertIsNone(unsupported["knowledge"])
        self.assertEqual(driver.calls, [])


if __name__ == "__main__":
    unittest.main()
