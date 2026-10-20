"""Only the new E02 resource: real registered MCP calls, plus one pure-function test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import query_holy_site_planning_knowledge_v1


TOOL = "ck3_query_holy_site_planning_knowledge_v1"
ACTIONS = ("adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic")
TOPICS = {"artifacts", "site_effects_and_cache", "mecca", "head_of_faith", "pilgrimage", "great_holy_war"}
ACTUAL_MCP_SUMMARIES = []


class NoGameDriver:
    def __init__(self): self.calls = []
    def refuse(self, name):
        self.calls.append(name)
        raise AssertionError("E02 static knowledge accessed gameplay: " + name)
    def capabilities(self): return self.refuse("capabilities")
    def take_snapshot(self): return self.refuse("take_snapshot")
    def take_snapshot_without_native_command_history(self): return self.refuse("take_snapshot_without_native_command_history")
    def execute_step(self, *args, **kwargs): return self.refuse("execute_step")
    def wait_for_change(self, *args, **kwargs): return self.refuse("wait_for_change")
    def _execute_primitive_step(self, *args, **kwargs): return self.refuse("_execute_primitive_step")


async def registered_query(client, arguments):
    reply = await client.session.call_tool(TOOL, arguments)
    if reply.is_error: raise AssertionError(reply.model_dump(mode="json"))
    output = reply.structured_content
    raw = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    research = (output.get("knowledge") or {}).get("episode02_research")
    ACTUAL_MCP_SUMMARIES.append({"arguments": arguments, "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(), "status": output["status"],
        "episode02_present": research is not None, "ordinary_auto_consumes": None if research is None else research["ordinary_auto_consumes"]})
    return output


class Episode02RegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_all_actions_return_six_source_topics_without_game(self):
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for action in ACTIONS:
                with self.subTest(action=action):
                    outer = await registered_query(client, {"action": action})
                    r = outer["knowledge"]["episode02_research"]
                    self.assertEqual(set(r["topics"]), TOPICS)
                    self.assertEqual(r["schema"], "xar.ck3.holy-site-episode02-research.v1")
                    self.assertEqual(r["ck3_build"], "1.20.0.4")
                    self.assertTrue(r["current_observations_must_be_fresh"])
                    self.assertTrue(r["read_only"])
                    for key in ("requires_ck3", "runtime_file_access_required", "state_observed", "action_ready",
                                "ordinary_auto_consumes", "historical_evidence_is_current_state"):
                        self.assertIs(r[key], False)
                    self.assertIsNone(r["native_legality"])
                    self.assertFalse(outer["action_ready"])
                    self.assertIsNone(outer["native_legality"])
                    self.assertEqual(r["shared_reference"], "docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md")
                    for topic in r["topics"].values():
                        self.assertIn(r["shared_reference"], topic["documents"])
                        self.assertTrue(topic["rules"])
                        self.assertTrue(topic["unknowns"])
                        for source in topic.get("sources", []):
                            self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
                            self.assertFalse(Path(source["game_relative_path"]).is_absolute())
                            self.assertTrue(all(0 < first <= last for first, last in source["line_ranges"]))
                    portable = json.dumps(r, ensure_ascii=False)
                    self.assertIsNone(re.search(r"[A-Za-z]:[\\/]", portable))
                    self.assertNotIn("/workspace/", portable)
                    mecca = r["topics"]["mecca"]
                    self.assertFalse(mecca["site_attribution_observed"])
                    self.assertIsNone(mecca["selected_site_contribution_raw"])
                    self.assertEqual(mecca["sources"][0]["line_ranges"], [[687, 710]])
        self.assertEqual(driver.calls, [])

    async def test_registered_foreign_build_publishes_no_episode02_or_permission(self):
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            out = await registered_query(client, {"action": "demote", "ck3_build": "1.20.1"})
        self.assertEqual(out["status"], "unavailable")
        self.assertEqual(out["qualification"], "unsupported_build")
        self.assertIsNone(out["knowledge"])
        self.assertIsNone(out["native_legality"])
        self.assertFalse(out["action_ready"])
        self.assertEqual(driver.calls, [])

    async def test_registered_history_and_cache_never_turn_into_current_state(self):
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            r = (await registered_query(client, {"action": "demote"}))["knowledge"]["episode02_research"]
        history = r["historical_observation_limits"]
        self.assertEqual(history["machine_id"], "4-8e1c2f1861")
        self.assertTrue(history["medina27"]["intent_consumed"])
        self.assertFalse(history["medina27"]["post_save_available"])
        self.assertFalse(history["medina27"]["replay_authorized"])
        self.assertFalse(r["historical_evidence_is_current_state"])
        self.assertFalse(r["topics"]["site_effects_and_cache"]["native_source_chain"]["refresh_schedule_verified"])
        self.assertIn("cache time unknown", history["medina27"]["not_proven"])
        self.assertEqual(driver.calls, [])

    async def test_registered_reply_isolation_and_existing_readonly_schema(self):
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            tool = next(t for t in (await client.session.list_tools()).tools if t.name == TOOL)
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertEqual(set(tool.input_schema["properties"]), {"action", "ck3_build"})
            self.assertEqual(set(tool.input_schema["properties"]["action"]["enum"]), set(ACTIONS))
            first = await registered_query(client, {"action": "enshrine_relic"})
            first["knowledge"]["episode02_research"]["topics"]["mecca"]["sources"].clear()
            first["knowledge"]["episode02_research"]["ordinary_auto_consumes"] = True
            second = await registered_query(client, {"action": "create"})
        r = second["knowledge"]["episode02_research"]
        self.assertFalse(r["ordinary_auto_consumes"])
        self.assertEqual(r["topics"]["mecca"]["sources"][0]["sha256"], "0824df55d4cd0a7c6d2c2d8b45bf577cca9ec0e5e1b4a6f699848b8661b17b40")
        self.assertEqual(driver.calls, [])


    async def test_registered_pilgrimage_cost_boundary_and_source_only_events(self):
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            out = await registered_query(client, {"action": "create"})
        r = out["knowledge"]["episode02_research"]
        pilgrimage = r["topics"]["pilgrimage"]
        self.assertTrue(any("final configured full10 activity quote (not proven whole-journey cost)" in rule for rule in pilgrimage["rules"]))
        self.assertTrue(any("whole-journey cost is not established" in item for item in pilgrimage["unknowns"]))
        events = pilgrimage["source_only_events"]
        self.assertEqual({e["static_definition_id"] for e in events}, {"pilgrimage.5001", "travel_start_event.1060"})
        repo = Path(__file__).resolve().parents[3]
        for event in events:
            self.assertFalse(Path(event["source_document"]).is_absolute())
            source = json.loads((repo / event["source_document"]).read_text(encoding="utf-8"))
            self.assertEqual(event["static_definition_id"], source.get("static_definition_id", source["event_definition_key"]))
            self.assertEqual(event["analysis_status"], source["analysis_status"])
            self.assertIsNone(event["live_native_definition_id"])
            self.assertIsNone(source.get("live_native_definition_id"))
            self.assertIs(event["full_occurrence_contract_registered"], False)
            self.assertIs(event["selection_policy_changed"], False)
            self.assertIs(source["full_occurrence_contract_registered"], False)
            self.assertIs(source["selection_policy_changed"], False)
        self.assertEqual(set(r["topics"]), TOPICS)
        self.assertFalse(r["ordinary_auto_consumes"])
        self.assertFalse(r["action_ready"])
        self.assertIsNone(r["native_legality"])
        self.assertEqual(driver.calls, [])
        print("E02_COST_EVENT_SINGLE_MCP_SUMMARY=" + json.dumps(ACTUAL_MCP_SUMMARIES[-1], sort_keys=True))
        print("E02_COST_EVENT_GAME_DRIVER_CALLS=" + json.dumps(driver.calls))


class Episode02FunctionTests(unittest.TestCase):
    def test_function_returns_reference_without_runtime_document_reads(self):
        # Imports are complete. Exercise only the new pure response construction.
        with patch("builtins.open", side_effect=AssertionError("runtime file read")), \
                patch.object(Path, "open", side_effect=AssertionError("runtime Path read")):
            out = query_holy_site_planning_knowledge_v1("promote")
        r = out["knowledge"]["episode02_research"]
        self.assertFalse(r["runtime_file_access_required"])
        self.assertFalse(r["ordinary_auto_consumes"])
        self.assertTrue(r["fresh_observations_required"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    print("E02_ACTUAL_REGISTERED_MCP_SUMMARIES=" + json.dumps(ACTUAL_MCP_SUMMARIES, sort_keys=True))
    print("E02_TEST_SCOPE=" + json.dumps({"registered_mcp_tests": 5, "function_tests": 1,
        "actual_call_tool_count": len(ACTUAL_MCP_SUMMARIES), "native_game_build_actions": 0,
        "ordinary_auto_consumption_proven": False, "old_full_suite_rerun": False}))
    raise SystemExit(not result.wasSuccessful())
