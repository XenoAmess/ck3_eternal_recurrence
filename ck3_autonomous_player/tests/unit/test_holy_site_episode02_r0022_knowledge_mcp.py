"""One registered MCP retrieval for additive R22 source/history; never a game."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Never, get_args
import unittest

REPO = Path(os.environ.get("XAR_E02_REPO", str(Path(__file__).resolve().parents[3]))).resolve()
CANDIDATE = Path(os.environ.get("XAR_E02_R22_CANDIDATE_ROOT", str(REPO))).resolve()
COPY_MAP = os.environ.get("XAR_E02_R22_COPY_MAP")
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
if CANDIDATE != REPO:
    name = "xar_autoplayer.holy_site_episode02_research"
    spec = importlib.util.spec_from_file_location(name, CANDIDATE / "ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py")
    if spec is None or spec.loader is None:
        raise ValueError("R22 research candidate cannot load")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import HolySitePlanningAction


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Expected object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Expected string keys")
        result[key] = item
    return result


def array_value(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected array")
    return list(value)


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected integer, not bool")
    return value


def document_path(relative: str) -> Path:
    if COPY_MAP is not None:
        raw: object = json.loads(Path(COPY_MAP).read_text(encoding="utf-8-sig"))
        for entry in array_value(object_value(raw)["files"]):
            row = object_value(entry)
            if row["canonical_target"] == relative:
                return Path(str(row["path"]))
        # Prior sealed layers are projected, never copied or implicitly applied.
        base = Path(COPY_MAP).resolve().parents[2]
        for lane in ("r21-cap-knowledge-source-a01", "p3-r18-knowledge-integration-source-a01"):
            path = base / lane / "candidate" / relative
            if path.is_file():
                return path
    path = CANDIDATE / relative
    return path if path.is_file() else REPO / relative


class NoGameDriver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def refuse(self, name: str) -> Never:
        self.calls.append(name)
        raise AssertionError("Research lookup attempted game access: " + name)

    def capabilities(self) -> object:
        return self.refuse("capabilities")

    def take_snapshot(self) -> object:
        return self.refuse("take_snapshot")

    def take_snapshot_without_native_command_history(self) -> object:
        return self.refuse("take_snapshot_without_native_command_history")

    def execute_step(self, *args: object, **kwargs: object) -> object:
        return self.refuse("execute_step")

    def wait_for_change(self, *args: object, **kwargs: object) -> object:
        return self.refuse("wait_for_change")


class R0022ResearchKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_lookup_indexes_analyzed_r22_without_permission(self) -> None:
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            reply = await client.session.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "promote"})
        self.assertFalse(reply.is_error)
        output = object_value(reply.structured_content)
        research = object_value(object_value(output["knowledge"])["episode02_research"])
        topics = object_value(research["topics"])
        self.assertEqual(set(topics), {"artifacts", "site_effects_and_cache", "mecca", "head_of_faith", "pilgrimage", "great_holy_war"})
        self.assertEqual(len(get_args(HolySitePlanningAction)), 7)
        pilgrimage = object_value(topics["pilgrimage"])
        # Existing R18/legacy consumers retain their exact prior fields.
        self.assertEqual(len(array_value(pilgrimage["source_only_events"])), 4)
        self.assertEqual(set(object_value(pilgrimage["source_analyzed_events"])), {"pilgrimage.2070", "pilgrimage_intent.1100", "pilgrimage_intent.1040"})
        rows = object_value(pilgrimage["r0022_source_analyzed_events"])
        self.assertEqual(set(rows), {"pilgrimage.3004", "pilgrimage_intent.1030", "pilgrimage.6840", "stress_threshold.1701", "pilgrimage.6750", "councillor_spouse_learning.2601", "pilgrimage.6800", "pilgrimage.7000", "pilgrimage.9001"})
        for definition, raw_row in rows.items():
            row = object_value(raw_row)
            self.assertEqual(row["static_definition_id"], definition)
            self.assertIs(row["source_analysis_completed"], True)
            for field in ("ordinary_auto_consumes", "state_observed", "action_ready", "historical_evidence_is_current_state", "full_occurrence_contract_registered", "selection_policy_changed"):
                self.assertIs(row[field], False)
            self.assertIsNone(row["native_legality"])
            for field in ("source_document", "occurrence_document"):
                path = document_path(str(row[field]))
                self.assertTrue(path.is_file(), str(path))
                parsed: object = json.loads(path.read_text(encoding="utf-8-sig"))
                self.assertEqual(json.loads(json.dumps(parsed, ensure_ascii=False)), parsed)
        self.assertIn("dedicated route ran first", str(object_value(rows["stress_threshold.1701"])["decision_summary"]))
        self.assertIn("Five official source SHA", str(object_value(rows["stress_threshold.1701"])["decision_summary"]))
        self.assertIn("NPC", str(object_value(rows["pilgrimage.6800"])["decision_summary"]))
        self.assertIn("before the conclusion button", str(object_value(rows["pilgrimage.7000"])["decision_summary"]))
        batch_raw: object = json.loads(document_path(str(pilgrimage["r0022_complete_event_index_document"])).read_text(encoding="utf-8-sig"))
        batch = object_value(batch_raw)
        self.assertEqual(integer(batch["actual_event_count"]), 15)
        self.assertEqual(integer(batch["actual_interaction_count"]), 1)
        actual_events = array_value(batch["events"])
        self.assertEqual([integer(object_value(event)["event_instance_id"]) for event in actual_events], list(range(1, 16)))
        for raw_event in actual_events:
            event = object_value(raw_event)
            self.assertIs(event["analysis_completed"], True)
            self.assertIs(event["ack_accepted"], True)
            self.assertIs(event["old_instance_gone_in_independent_snapshot"], True)
            self.assertIsNone(event["current_native_legality"])
        self.assertEqual(object_value(actual_events[7])["actual_shown_native_indices"], [3, 6, 8])
        self.assertEqual(object_value(actual_events[9])["selected_native_option_index"], 2)
        ending_raw: object = json.loads(document_path(str(pilgrimage["r0022_ending_document"])).read_text(encoding="utf-8-sig"))
        ending = object_value(ending_raw)
        self.assertEqual(integer(ending["observed_game_days"]), 201)
        self.assertEqual(integer(ending["day_requests"]), 204)
        facts = object_value(ending["ending_four_facts"])
        identity = object_value(object_value(facts["native_activity_terminal"])["identity"])
        self.assertEqual(integer(identity["activity_id"]), 0)
        self.assertIs(identity["native_completed"], True)
        self.assertIs(identity["native_invalidated"], False)
        self.assertIsInstance(identity["native_completion_stamp_raw_decimal"], str)
        current = object_value(ending["current_postreturn_religion_only"])
        self.assertEqual(integer(current["spiritual_fulfillment_raw"]), 3500000)
        self.assertIsNone(current["historical_metric_delta"])
        self.assertIsNone(current["trait_XP"])
        self.assertIs(ending["complete_travel_total_known"], False)
        for field in ("ordinary_auto_consumes", "state_observed", "action_ready", "historical_evidence_is_current_state"):
            self.assertIs(research[field], False)
        self.assertIsNone(research["native_legality"])
        self.assertIsNone(output["native_legality"])
        self.assertIs(output["action_ready"], False)
        guide = document_path("docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md").read_text(encoding="utf-8-sig")
        links_checked = 0
        for link in re.findall(r"\]\(([^)]+)\)", guide):
            target = link.split("#", 1)[0].strip("<>")
            if not target or "://" in target or target.startswith("#"):
                continue
            relative = str(PurePosixPath("docs/ck3-native-ai") / target)
            normalized = os.path.relpath(REPO / relative, REPO).replace("\\", "/")
            self.assertTrue(document_path(normalized).is_file(), normalized)
            links_checked += 1
        self.assertGreater(links_checked, 10)
        self.assertEqual(driver.calls, [])
        print("R0022_KNOWLEDGE_MCP_ACTUAL=" + json.dumps({"registered_mcp_calls": 1, "game_driver_calls": driver.calls, "new_analyzed_rows": len(rows), "actual_events": 15, "interaction_count": 1, "links_checked": links_checked, "six_topics_seven_actions": True, "ordinary_auto_consumption_proven": False}, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
