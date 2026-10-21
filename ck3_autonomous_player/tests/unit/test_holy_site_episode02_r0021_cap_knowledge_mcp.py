"""One source-knowledge MCP retrieval; no game or historical replay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Never, get_args
import unittest

REPO = Path(os.environ.get("XAR_E02_REPO", str(Path(__file__).resolve().parents[3]))).resolve()
CANDIDATE = Path(os.environ.get("XAR_E02_R21_CANDIDATE_ROOT", str(REPO))).resolve()
DOCUMENT = "promo/ck3_faith_and_power/episode02/docs/knowledge/r0021-promotion-cap-source-analysis.json"
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
if CANDIDATE != REPO:
    module_name = "xar_autoplayer.holy_site_episode02_research"
    spec = importlib.util.spec_from_file_location(
        module_name, CANDIDATE / "ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py"
    )
    if spec is None or spec.loader is None:
        raise ValueError("External R21 research candidate cannot load")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import HolySitePlanningAction


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Expected string object keys")
        result[key] = item
    return result


def array_value(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected JSON array")
    return list(value)


def document_path(relative: str) -> Path:
    path = CANDIDATE / relative
    return path if path.is_file() else REPO / relative


class NoGameDriver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def refuse(self, name: str) -> Never:
        self.calls.append(name)
        raise AssertionError("Static cap knowledge attempted game access: " + name)

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


class R0021PromotionCapKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_promote_lookup_keeps_cap_and_price_separate(self) -> None:
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            reply = await client.session.call_tool(
                "ck3_query_holy_site_planning_knowledge_v1", {"action": "promote"}
            )
        self.assertFalse(reply.is_error)
        output = object_value(reply.structured_content)
        research = object_value(object_value(output["knowledge"])["episode02_research"])
        topics = object_value(research["topics"])
        self.assertEqual(set(topics), {
            "artifacts", "site_effects_and_cache", "mecca", "head_of_faith", "pilgrimage", "great_holy_war"
        })
        self.assertEqual(set(get_args(HolySitePlanningAction)), {
            "adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic"
        })
        site_topic = object_value(topics["site_effects_and_cache"])
        self.assertIn(DOCUMENT, array_value(site_topic["documents"]))
        rules = array_value(site_topic["rules"])
        self.assertTrue(any(isinstance(rule, str) and "complete current Faith major membership/count" in rule for rule in rules))
        self.assertTrue(any(isinstance(rule, str) and "zero quote never waives" in rule for rule in rules))
        hof_rules = array_value(object_value(topics["head_of_faith"])["rules"])
        self.assertTrue(any(isinstance(rule, str) and "whole Faith" in rule and "selected-site" in rule for rule in hof_rules))
        pilgrimage = object_value(topics["pilgrimage"])
        self.assertEqual(len(array_value(pilgrimage["source_only_events"])), 4)
        self.assertEqual(set(object_value(pilgrimage["source_analyzed_events"])), {
            "pilgrimage.2070", "pilgrimage_intent.1100", "pilgrimage_intent.1040"
        })
        raw = document_path(DOCUMENT).read_bytes()
        decoded: object = json.loads(raw)
        source = object_value(decoded)
        self.assertEqual(source["schema"], "xar.ck3.holy-site-promotion-cap-knowledge.v1")
        self.assertEqual(source["machine_id"], "4-8e1c2f1861")
        historical = object_value(source["historical_r0021"])
        self.assertEqual(historical["faith_major_site_ids"], [0, 1, 3])
        self.assertIs(type(historical["faith_major_count"]), int)
        self.assertEqual(historical["faith_major_count"], 3)
        self.assertIs(historical["normal_requirements_can_confirm"], False)
        self.assertIs(historical["native_can_confirm"], False)
        self.assertIs(type(historical["bypass_requirements_raw"]), int)
        self.assertEqual(historical["bypass_requirements_raw"], 0)
        self.assertEqual(historical["resource_vector_raw"], [0] * 10)
        self.assertIs(historical["native_affordable"], True)
        self.assertEqual(historical["free_actions_remaining_native_text"], 2)
        self.assertIs(historical["typed_free_action_counter_observed"], False)
        self.assertEqual(historical["native_rendered_max"], 3)
        self.assertIs(historical["typed_religion_max_observed"], False)
        self.assertEqual(historical["confirm_submissions"], 0)
        self.assertIs(historical["promotion_success_observed"], False)
        source_rules = object_value(source["source_rules"])
        self.assertEqual(object_value(source_rules["default_limits"])["eminent_min"], 1)
        self.assertIs(source["current_religion_typed_max_reader_claimed"], False)
        plan = object_value(source["candidate_controlled_comparison"])
        self.assertEqual(plan["status"], "CANDIDATE_NOT_LIVE")
        for field in ("performed", "success_claimed"):
            self.assertIs(plan[field], False)
        for field in ("future_actual_mother_pin", "future_quote", "future_permission"):
            self.assertIsNone(plan[field])
        for value in (research, source):
            for field in ("state_observed", "action_ready", "ordinary_auto_consumes", "historical_evidence_is_current_state"):
                self.assertIs(value[field], False)
            self.assertIsNone(value["native_legality"])
        self.assertIsNone(output["native_legality"])
        self.assertIs(output["action_ready"], False)
        guide = document_path("docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md").read_text(encoding="utf-8-sig")
        self.assertIn("r0021-promotion-cap-source-analysis.json", guide)
        self.assertEqual(driver.calls, [])
        self.assertEqual(json.loads(json.dumps(source, ensure_ascii=False)), source)
        print("R0021_CAP_KNOWLEDGE_MCP_ACTUAL=" + json.dumps({
            "registered_mcp_calls": 1, "game_driver_calls": driver.calls,
            "source_document": DOCUMENT, "source_document_sha256": hashlib.sha256(raw).hexdigest(),
            "historical_rejection_not_current_permission": True,
            "six_topics_and_seven_actions_preserved": True,
            "ordinary_auto_consumption_proven": False,
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
