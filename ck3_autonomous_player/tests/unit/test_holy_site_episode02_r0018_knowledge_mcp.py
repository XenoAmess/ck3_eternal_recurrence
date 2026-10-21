"""One registered MCP lookup of the new R0018 analyzed-source index."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from typing import Never, get_args
import unittest

REPO = Path(os.environ.get("XAR_E02_REPO", str(Path(__file__).resolve().parents[3]))).resolve()
CANDIDATE = Path(os.environ.get("XAR_E02_R18_CANDIDATE_ROOT", str(REPO))).resolve()
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
if CANDIDATE != REPO:
    module_name = "xar_autoplayer.holy_site_episode02_research"
    spec = importlib.util.spec_from_file_location(module_name, CANDIDATE / "ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py")
    if spec is None or spec.loader is None:
        raise ValueError("External research candidate cannot load")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import HolySitePlanningAction

PREFIX = "promo/ck3_faith_and_power/episode02/docs/knowledge/"
FROZEN_DOCUMENTS = {
    PREFIX + "pilgrimage-2070-source-analysis.json": "eb9b9db42710964daa90ef16c37820d3b356e39b1fbb8af6dc26f75e3e5f6a85",
    PREFIX + "pilgrimage-intent-1100-source-analysis.json": "4a4a32e38c359402143973c13b485f6a70e304420a1fe93b271aab3117d83d58",
    PREFIX + "r0018-events-001-003-occurrence.json": "1e6bf0cb1c07167d9b20a3b0e47ca1c53b758cd071e562917e78e8935110e85b",
    PREFIX + "pilgrimage-intent-1040-source-analysis.json": "bbc377c91cb934371298ae13b9dd26f22c588af0dd93296fb433af830a942716",
    PREFIX + "r0018-event004-and-scene-cutoff.json": "3adbe260b1f8da5089bd7da3828ee3f14f239bdc805cc31167c6e1db27fea0f9",
}
DEFINITIONS = {"pilgrimage.2070", "pilgrimage_intent.1100", "pilgrimage_intent.1040"}


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Expected string JSON object keys")
        result[key] = item
    return result


def array_value(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected a JSON array")
    return list(value)


def string_value(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected a JSON string")
    return value


def integer_value(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected an integer, not bool/float")
    return value


def repository_document(relative: str) -> Path:
    staged = CANDIDATE / relative
    return staged if staged.is_file() else REPO / relative


def json_document(relative: str) -> dict[str, object]:
    path = repository_document(relative)
    value: object = json.loads(path.read_text(encoding="utf-8"))
    return object_value(value)


class NoGameDriver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def refuse(self, name: str) -> Never:
        self.calls.append(name)
        raise AssertionError("Source knowledge attempted game access: " + name)

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


class R0018AnalyzedKnowledgeMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_three_definitions_are_source_analyzed_not_permission(self) -> None:
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            reply = await client.session.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "demote"})
        self.assertFalse(reply.is_error)
        output = object_value(reply.structured_content)
        research = object_value(object_value(output["knowledge"])["episode02_research"])
        topics = object_value(research["topics"])
        self.assertEqual(set(topics), {"artifacts", "site_effects_and_cache", "mecca", "head_of_faith", "pilgrimage", "great_holy_war"})
        self.assertEqual(set(get_args(HolySitePlanningAction)), {"adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic"})
        pilgrimage = object_value(topics["pilgrimage"])
        self.assertEqual(len(array_value(pilgrimage["source_only_events"])), 4)
        rows = object_value(pilgrimage["source_analyzed_events"])
        self.assertEqual(set(rows), DEFINITIONS)
        for definition, untyped_row in rows.items():
            row = object_value(untyped_row)
            self.assertEqual(row["static_definition_id"], definition)
            self.assertEqual(row["historical_native_definition_id"], definition)
            self.assertEqual(row["analysis_status"], "source_closed_actual_native_definition_and_choice_observed")
            self.assertIs(row["source_analysis_completed"], True)
            self.assertEqual(row["historical_run_id"], "4-8e1c2f1861--faith-engine--R0018")
            self.assertEqual(row["historical_machine_id"], "4-8e1c2f1861")
            for key in ("historical_evidence_is_current_state", "full_occurrence_contract_registered", "selection_policy_changed", "ordinary_auto_consumes", "state_observed", "action_ready"):
                self.assertIs(row[key], False)
            self.assertIs(row["native_legality"], None)
            self.assertTrue(array_value(row["unobserved"]))
            source = json_document(string_value(row["source_document"]))
            self.assertEqual(source["event_definition_key"], definition)
            self.assertEqual(source["analysis_status"], row["analysis_status"])
            expected_path = "events/activities/pilgrimage_activity/" + ("pilgrimage_events.txt" if definition == "pilgrimage.2070" else "pilgrimage_intent_events.txt")
            definitions = [object_value(value) for value in array_value(source["source_pins"]) if object_value(value)["game_relative_path"] == expected_path]
            self.assertEqual(len(definitions), 1)
            self.assertEqual(row["definition_source_sha256"], definitions[0]["sha256"])
            occurrence = json_document(string_value(row["occurrence_document"]))
            records = array_value(occurrence["events"]) if "events" in occurrence else [occurrence["event4"]]
            actual = [object_value(value) for value in records if object_value(value)["event_definition_key"] == definition]
            self.assertEqual(len(actual), 1)
            self.assertIs(actual[0]["ack_accepted"], True)
            self.assertIs(actual[0]["old_instance_gone_in_independent_snapshot"], True)
            self.assertEqual(integer_value(actual[0]["selected_option_number"]), 1)
        documents = {string_value(value) for value in array_value(pilgrimage["documents"])}
        for relative, digest in FROZEN_DOCUMENTS.items():
            self.assertIn(relative, documents)
            self.assertEqual(hashlib.sha256(repository_document(relative).read_bytes()).hexdigest(), digest)
        final = json_document(PREFIX + "r0018-event004-and-scene-cutoff.json")
        event4 = object_value(final["event4"])
        self.assertEqual(len(array_value(event4["actual_shown_options"])), 2)
        piety = object_value(object_value(event4["wallet_piety_prestige_readback"])["played_character_piety"])
        self.assertEqual(integer_value(piety["delta_raw"]), 5000000)
        self.assertIs(event4["trait_xp"], None)
        self.assertIs(event4["actual_eta"], None)
        cutoff = object_value(final["scene_cutoff"])
        self.assertEqual(integer_value(cutoff["actual_event_count"]), 4)
        self.assertEqual(integer_value(cutoff["day_requests"]), 57)
        for key in ("arrival_observed", "terminal_observed", "return_observed", "coordinate_home_observed", "normal_close_contract_pass", "actual_retained_os0"):
            self.assertIs(cutoff[key], False)
        for key in ("ordinary_auto_consumes", "state_observed", "action_ready", "historical_evidence_is_current_state"):
            self.assertIs(research[key], False)
        self.assertIs(output["native_legality"], None)
        self.assertIs(output["action_ready"], False)
        reference_relative = string_value(research["shared_reference"])
        text = repository_document(reference_relative).read_text(encoding="utf-8-sig")
        checked_links = 0
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in link or link.startswith("#"):
                continue
            absolute = ((REPO / reference_relative).parent / link.split("#", 1)[0]).resolve()
            relative = absolute.relative_to(REPO).as_posix()
            self.assertTrue(repository_document(relative).is_file(), link)
            checked_links += 1
        self.assertEqual(driver.calls, [])
        payload = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        print("R0018_SOURCE_KNOWLEDGE_MCP_ACTUAL=" + json.dumps({
            "registered_mcp_calls": 1, "source_analyzed_definition_ids": sorted(rows),
            "frozen_document_copies_checked": 5, "reference_links_checked": checked_links,
            "response_bytes": len(payload), "response_sha256": hashlib.sha256(payload).hexdigest(),
            "game_driver_calls": driver.calls, "ordinary_auto_consumption_proven": False,
            "new_native_registry_or_execution_policy_proven": False,
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
