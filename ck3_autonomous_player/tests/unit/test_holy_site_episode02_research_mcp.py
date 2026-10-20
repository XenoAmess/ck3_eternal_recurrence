"""Only the new E02 resource: real registered MCP calls, plus one pure-function test."""
from __future__ import annotations

import hashlib
import json
import os
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


    async def test_registered_pilgrimage_cost_boundary_and_source_only_events(self) -> None:
        """One forward data-revision call; the old five/eleven-call run is not rerun."""
        before_calls = len(ACTUAL_MCP_SUMMARIES)
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            out = await registered_query(client, {"action": "create"})
        r = out["knowledge"]["episode02_research"]
        pilgrimage = r["topics"]["pilgrimage"]
        self.assertTrue(any("final configured full10 activity quote (not proven whole-journey cost)" in rule for rule in pilgrimage["rules"]))
        self.assertTrue(any("whole-journey cost is not established" in item for item in pilgrimage["unknowns"]))
        events = pilgrimage["source_only_events"]
        self.assertEqual({e["static_definition_id"] for e in events}, {"pilgrimage.5001", "travel_start_event.1060", "travel_events_cities.1020", "pilgrimage.4100"})
        repo = Path(__file__).resolve().parents[3]
        fallback = Path(os.environ.get("XAR_E02_REFERENCE_ROOT", str(repo)))

        def document(relative: str) -> dict[str, object]:
            self.assertFalse(Path(relative).is_absolute())
            self.assertNotIn("..", Path(relative).parts)
            path = repo / relative
            if not path.is_file():
                path = fallback / relative
            self.assertTrue(path.is_file(), relative)
            value: object = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(value, dict)
            if not isinstance(value, dict):
                raise AssertionError("Source document must be a JSON object")
            return value

        by_id = {event["static_definition_id"]: event for event in events}
        for event in events:
            source = document(event["source_document"])
            self.assertEqual(event["static_definition_id"], source.get("static_definition_id", source.get("event_definition_key")))
            self.assertIs(event["full_occurrence_contract_registered"], False)
            self.assertIs(event["selection_policy_changed"], False)
            self.assertIs(event["historical_observation_is_current_state"], False)
            self.assertIs(source["full_occurrence_contract_registered"], False)
            self.assertIs(source["selection_policy_changed"], False)
        old = by_id["pilgrimage.5001"]
        self.assertEqual(old["analysis_status"], "native_definition_observed_existing_source_analysis_reused")
        self.assertEqual(old["live_native_definition_id"], "pilgrimage.5001")
        self.assertIn("occurrence_document", old)
        for key in ("pilgrimage.5001", "travel_start_event.1060", "travel_events_cities.1020", "pilgrimage.4100"):
            self.assertEqual(by_id[key]["live_native_definition_id"], key)
        occurrence = document(by_id["travel_start_event.1060"]["occurrence_document"])
        self.assertEqual(by_id["travel_start_event.1060"]["analysis_status"], "historical_live_native_definition_observed")
        self.assertEqual(occurrence["live_native_definition_id"], "travel_start_event.1060")
        self.assertEqual(occurrence["run_id"], "4-8e1c2f1861--faith-engine--R0012")
        self.assertIs(occurrence["independent_old_window_gone"], True)
        self.assertIs(occurrence["B17_historical_cutoff_unchanged"], True)
        city = by_id["travel_events_cities.1020"]
        self.assertEqual(city["analysis_status"], "completed_source_analysis_native_current_shown_variant")
        source = document(city["source_document"])
        self.assertIs(source["loaded_definition_bytes_verified"], False)
        post = document(city["post_observation_document"])
        interaction = document(city["related_interaction_document"])
        self.assertEqual(interaction["definition_key"], "arrange_marriage_interaction")
        self.assertEqual(post["event2"]["actual_gold_decrease"], 50)
        self.assertIs(post["event2"]["artifact_inventory_observed"], False)
        self.assertIs(post["event2"]["travel_delay_or_new_ETA_observed"], False)
        self.assertIs(post["whole_journey_cost_known"], False)
        self.assertIs(post["interaction35"]["old_pending35_absent"], True)
        self.assertEqual(set(r["topics"]), TOPICS)
        for key in ("state_observed", "ordinary_auto_consumes", "action_ready", "historical_evidence_is_current_state"):
            self.assertIs(r[key], False)
        self.assertIsNone(r["native_legality"])
        self.assertFalse(out["action_ready"])
        self.assertIsNone(out["native_legality"])
        self.assertEqual(driver.calls, [])
        self.assertEqual(len(ACTUAL_MCP_SUMMARIES), before_calls + 1)
        print("E02_OCCURRENCE_FORWARD_SINGLE_MCP_SUMMARY=" + json.dumps(ACTUAL_MCP_SUMMARIES[-1], sort_keys=True))
        print("E02_OCCURRENCE_FORWARD_GAME_DRIVER_CALLS=" + json.dumps(driver.calls))


    async def test_registered_arrival_badge_source_and_separate_actual_post(self) -> None:
        """One new arrival-forward MCP call; no earlier data consumer is rerun."""
        before_calls = len(ACTUAL_MCP_SUMMARIES)
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            out = await registered_query(client, {"action": "create"})
        r = out["knowledge"]["episode02_research"]
        pilgrimage = r["topics"]["pilgrimage"]
        events = {event["static_definition_id"]: event for event in pilgrimage["source_only_events"]}
        self.assertEqual(set(events), {"pilgrimage.5001", "travel_start_event.1060", "travel_events_cities.1020", "pilgrimage.4100"})
        repo = Path(__file__).resolve().parents[3]

        def document(relative: str) -> dict[str, object]:
            self.assertFalse(Path(relative).is_absolute())
            self.assertNotIn("..", Path(relative).parts)
            path = repo / relative
            self.assertTrue(path.is_file(), relative)
            value: object = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise AssertionError("Arrival evidence must be a JSON object")
            return value

        for definition, event in events.items():
            self.assertEqual(event["live_native_definition_id"], definition)
            for key in ("full_occurrence_contract_registered", "selection_policy_changed", "historical_observation_is_current_state"):
                self.assertIs(event[key], False)
        arrival = document(events["pilgrimage.5001"]["occurrence_document"])
        badge = document(events["pilgrimage.4100"]["source_document"])
        self.assertEqual(events["pilgrimage.5001"]["analysis_status"], arrival["analysis_status"])
        self.assertEqual(events["pilgrimage.4100"]["analysis_status"], badge["analysis_status"])
        self.assertEqual(arrival["live_native_definition_id"], "pilgrimage.5001")
        self.assertIs(arrival["as_of_query_selection_ack_observed"], False)
        self.assertIs(arrival["pilgrim_trait_or_xp_independently_observed"], False)
        self.assertEqual(badge["live_native_definition_id"], "pilgrimage.4100")
        option = badge["actual_native_context"]["options"][0]
        self.assertEqual(option["effect_indicators"]["rows"], [])
        self.assertIs(option["effect_indicators"]["complete_effect_set"], False)
        self.assertEqual(option["resource_deltas"]["status"], "unavailable")
        self.assertIs(badge["source_options"][0]["activity_log_score_is_piety"], False)
        self.assertEqual(events["pilgrimage.5001"]["post_observation_document"], events["pilgrimage.4100"]["post_observation_document"])
        post = document(events["pilgrimage.4100"]["post_observation_document"])
        self.assertEqual(post["run_id"], "4-8e1c2f1861--faith-engine--R0012")
        self.assertEqual(post["machine_id"], "4-8e1c2f1861")
        actual = {event["event_definition_key"]: event for event in post["events"]}
        for event in actual.values():
            self.assertIs(event["ack_accepted"], True)
            self.assertIs(event["independent_old_window_gone"], True)
            self.assertIs(event["piety_unchanged_across_this_choice"], True)
            self.assertEqual(event["piety_before"], event["piety_after"])
        self.assertEqual((actual["pilgrimage.5001"]["stress_before"], actual["pilgrimage.5001"]["stress_after"]), (15, 4))
        self.assertEqual(actual["pilgrimage.4100"]["gold_delta_raw"], -3125000)
        self.assertEqual(actual["pilgrimage.4100"]["gold_scale"], 100000)
        self.assertEqual(actual["pilgrimage.4100"]["gold_after_raw"] - actual["pilgrimage.4100"]["gold_before_raw"], -3125000)
        for key in ("full_journey_conclusion_or_return_observed", "whole_journey_cost_known", "pilgrim_trait_membership_or_xp_independently_read_back", "badge_artifact_owner_id_equipment_or_stats_independently_read_back"):
            self.assertIs(post[key], False)
        self.assertTrue(any("Empty event effect_indicators.rows" in rule for rule in pilgrimage["rules"]))
        self.assertTrue(any("score50 is a log score, not 50 piety" in rule for rule in pilgrimage["rules"]))
        for key in ("state_observed", "ordinary_auto_consumes", "action_ready", "historical_evidence_is_current_state"):
            self.assertIs(r[key], False)
        self.assertIsNone(r["native_legality"])
        self.assertFalse(out["action_ready"])
        self.assertIsNone(out["native_legality"])
        self.assertEqual(driver.calls, [])
        self.assertEqual(len(ACTUAL_MCP_SUMMARIES), before_calls + 1)
        print("E02_ARRIVAL_FORWARD_SINGLE_MCP_SUMMARY=" + json.dumps(ACTUAL_MCP_SUMMARIES[-1], sort_keys=True))
        print("E02_ARRIVAL_FORWARD_GAME_DRIVER_CALLS=" + json.dumps(driver.calls))



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
    print("E02_TEST_SCOPE=" + json.dumps({"registered_mcp_tests": 6, "function_tests": 1,
        "actual_call_tool_count": len(ACTUAL_MCP_SUMMARIES), "native_game_build_actions": 0,
        "ordinary_auto_consumption_proven": False, "old_full_suite_rerun": False}))
    raise SystemExit(not result.wasSuccessful())
