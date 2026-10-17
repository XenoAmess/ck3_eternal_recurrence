from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.holy_site_planning_knowledge import (  # noqa: E402
    query_holy_site_planning_knowledge_v1,
)


ACTIONS = ("adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic")
TOOL = "ck3_query_holy_site_planning_knowledge_v1"


class _NoGameDriver:
    """The production server must serve this resource without consulting CK3."""

    def capabilities(self):
        raise AssertionError("static knowledge consulted gameplay capabilities")

    def take_snapshot(self):
        raise AssertionError("static knowledge took a game snapshot")

    def execute_step(self, *args, **kwargs):
        raise AssertionError("static knowledge executed a game step")

    def wait_for_change(self, *args, **kwargs):
        raise AssertionError("static knowledge waited on the game")


class HolySitePlanningKnowledgeTests(unittest.TestCase):
    def test_planning_answers_preserve_unknown_runtime_state(self):
        for action in ACTIONS:
            with self.subTest(action=action):
                answer = query_holy_site_planning_knowledge_v1(action)
                self.assertEqual(answer["qualification"], "source_reviewed_static")
                self.assertFalse(answer["state_observed"])
                self.assertFalse(answer["action_ready"])
                self.assertFalse(answer["requires_ck3"])
                self.assertFalse(answer["executes_action"])
                self.assertIsNone(answer["native_legality"])
                self.assertIsNone(answer["knowledge"]["cost_and_cooldown"]["actual_native_quote"])
                self.assertTrue(answer["knowledge"]["required_observations"])
                self.assertTrue(all(row["status"] == "unknown" for row in answer["knowledge"]["required_observations"]))
                self.assertTrue(any("ACK" in item for item in answer["knowledge"]["postconditions"]))

    def test_new_build_does_not_inherit_old_rules_or_native_permission(self):
        for build in ("1.20.1", "1.20.1.1", "1.20", "1.19.0.6"):
            answer = query_holy_site_planning_knowledge_v1("adopt", ck3_build=build)
            self.assertEqual(answer["status"], "unavailable")
            self.assertEqual(answer["qualification"], "unsupported_build")
            self.assertIsNone(answer["knowledge"])
            self.assertIsNone(answer["native_legality"])
        with self.assertRaises(ValueError):
            query_holy_site_planning_knowledge_v1("sanctify_relic")

    def test_candidate_source_and_subrule_distinctions_survive_for_consumers(self):
        adopt = query_holy_site_planning_knowledge_v1("adopt")["knowledge"]
        pipeline = adopt["candidate_pipeline"]
        self.assertEqual(pipeline[0]["enumeration"], ["actor.every_realm_county", "county.every_county_holy_site"])
        self.assertFalse(pipeline[1]["is_final_permission"])
        self.assertFalse(pipeline[2]["is_complete_native_validator"])
        self.assertIn("all associated Faiths", adopt["compatibility"]["quantifier"])
        self.assertFalse(adopt["compatibility"]["missing_parameter_observation_is_false"])
        self.assertIn("personal", adopt["compatibility"]["parameter_scope"])
        remove = query_holy_site_planning_knowledge_v1("remove_relic")["knowledge"]
        self.assertFalse(remove["script_requirements"]["actor_faith_site_membership_required_by_this_subrule"])
        self.assertFalse(remove["script_requirements"]["is_complete_native_validator"])
        self.assertEqual(remove["candidate_pipeline"][0]["status"], "unknown")

    def test_creation_hint_is_not_the_complete_picker_or_permission(self):
        create = query_holy_site_planning_knowledge_v1("create")["knowledge"]
        hint, models = create["candidate_pipeline"]
        self.assertFalse(hint["is_complete_candidate_directory"])
        self.assertFalse(hint["payment_checked_by_this_hint"])
        self.assertEqual(models["native_producer_status"], "unknown")
        self.assertEqual(set(models["models"]), {
            "GetAvailableHolySiteTypes", "GetPotentialBaronyTitles", "GetEnshrinableArtifacts",
        })
        self.assertTrue(create["script_requirements"]["free_action_does_not_bypass_existing_creation_lock"])
        self.assertFalse(create["script_requirements"]["is_complete_native_validator"])
        self.assertEqual(create["cost_and_cooldown"]["script_base_piety"], 2000)
        self.assertIsNone(create["declared_effect"]["actual_created_site_id_and_level"])
        self.assertNotIn("holy_site_full_instance_id_type_id_county_id_and_barony_id", {
            item["field"] for item in create["required_observations"]
        })
        self.assertIn("newly created", create["postconditions"][0])

    def test_grade_capacity_inventory_return_and_schism_boundaries(self):
        promote, demote, abandon = (
            query_holy_site_planning_knowledge_v1(action)["knowledge"]
            for action in ("promote", "demote", "abandon")
        )
        for action in (promote, demote, abandon):
            self.assertTrue(action["entrypoint"]["is_invisible"])
            self.assertFalse(action["entrypoint"]["keyed_decision_list_reachability_verified"])
        self.assertEqual(promote["declared_count_delta"]["total"], 0)
        self.assertEqual(demote["declared_count_delta"]["total"], 0)
        self.assertEqual(abandon["declared_count_delta"]["total"], -1)
        self.assertEqual(demote["default_limits"]["eminent_min"], 1)
        self.assertFalse(demote["frees_total_capacity_or_kingdom_record"])
        self.assertEqual(demote["schism_side_effect"]["declared_effect_input"], 1)
        self.assertIsNone(demote["schism_side_effect"]["actual_progress_delta"])
        self.assertIn("county holder", abandon["declared_effect"]["inventory_recipient"])
        self.assertFalse(abandon["declared_effect"]["other_faith_follower_count_checked_by_return_branch"])
        self.assertFalse(abandon["declared_effect"]["uses_explicit_remove_relic_effect"])
        self.assertFalse(abandon["recovery_boundary"]["re_adoption_is_general_undo"])
        self.assertIn("no holy site remaining", abandon["kingdom_release"]["expression"])

    def test_shared_new_action_metadata_cannot_be_mutated_through_a_reply(self):
        create = query_holy_site_planning_knowledge_v1("create")["knowledge"]
        create["default_limits"]["eminent_min"] = 0
        create["postconditions"].clear()
        demote = query_holy_site_planning_knowledge_v1("demote")["knowledge"]
        self.assertEqual(demote["default_limits"]["eminent_min"], 1)
        self.assertTrue(query_holy_site_planning_knowledge_v1("create")["knowledge"]["postconditions"])

    def test_every_citation_matches_the_reviewed_source_manifest(self):
        manifest = json.loads((PROJECT_ROOT.parent / "docs/ck3-native-ai/evidence/faith-and-power-holy-sites-12004/source-manifest.json").read_text(encoding="utf-8-sig"))
        sources = {row["path"]: row["sha256"] for row in manifest["sources"]}
        additions = json.loads((PROJECT_ROOT.parent / "docs/ck3-native-ai/evidence/faith-and-power-episode01-planning/knowledge-source-comparison.json").read_text(encoding="utf-8"))
        self.assertTrue(additions["all_identical"])
        self.assertEqual(additions["mirror_commit"], manifest["mirror_commit"])
        for row in additions["comparisons"]:
            self.assertTrue(row["byte_identical"])
            self.assertEqual(row["local_sha256"], row["mirror_sha256"])
            sources[row["path"]] = row["local_sha256"]

        def citations(value):
            if isinstance(value, dict):
                if {"path", "sha256", "line_start", "line_end", "commit"}.issubset(value):
                    yield value
                for item in value.values():
                    yield from citations(item)
            elif isinstance(value, list):
                for item in value:
                    yield from citations(item)

        refs = [ref for action in ACTIONS for ref in citations(query_holy_site_planning_knowledge_v1(action))]
        self.assertGreater(len(refs), 10)
        for ref in refs:
            self.assertEqual(ref["sha256"], sources[ref["path"]])
            self.assertEqual(ref["commit"], manifest["mirror_commit"])
            self.assertGreater(ref["line_start"], 0)
            self.assertGreaterEqual(ref["line_end"], ref["line_start"])

    def test_a_consumers_annotation_cannot_mutate_another_query(self):
        answer = query_holy_site_planning_knowledge_v1("adopt")
        answer["knowledge"]["required_observations"][0]["status"] = "observed"
        answer["knowledge"]["compatibility"]["missing_parameter_observation_is_false"] = True
        fresh = query_holy_site_planning_knowledge_v1("adopt")
        self.assertEqual(fresh["knowledge"]["required_observations"][0]["status"], "unknown")
        self.assertFalse(fresh["knowledge"]["compatibility"]["missing_parameter_observation_is_false"])


class HolySitePlanningKnowledgeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results: list[dict[str, object]] = []

    async def test_adoption_invisible_entrypoint_is_not_a_keyed_row_guarantee(self):
        from mcp import Client

        async with Client(create_server(_NoGameDriver())) as client:
            reply = await client.call_tool(TOOL, {"action": "adopt"})
            self.actual_mcp_results.append({"operation": "call_tool", "arguments": {"action": "adopt"}, "response": reply.model_dump(mode="json")})
        self.assertFalse(reply.is_error)
        entrypoint = reply.structured_content["knowledge"]["entrypoint"]
        self.assertTrue(entrypoint["is_invisible"])
        self.assertFalse(entrypoint["keyed_decision_list_reachability_verified"])
        self.assertEqual(entrypoint["sources"][0]["path"], "common/decisions/50_holy_site_decisions.txt")
        self.assertEqual((entrypoint["sources"][0]["line_start"], entrypoint["sources"][0]["line_end"]), (482, 482))
        self.assertIn("actual list row", entrypoint["meaning"])
        self.assertFalse(reply.structured_content["action_ready"])
        self.assertIsNone(reply.structured_content["native_legality"])

    async def test_production_server_lists_and_calls_without_a_game(self):
        from mcp import Client

        async with Client(create_server(_NoGameDriver())) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.actual_mcp_results.append({"operation": "list_tools", "tool": tools[TOOL].model_dump(mode="json")})
            self.assertTrue(tools[TOOL].annotations.read_only_hint)
            self.assertEqual(set(tools[TOOL].input_schema["properties"]), {"action", "ck3_build"})
            self.assertEqual(set(tools[TOOL].input_schema["properties"]["action"]["enum"]), set(ACTIONS))
            for action in ACTIONS:
                reply = await client.call_tool(TOOL, {"action": action})
                self.actual_mcp_results.append({"operation": "call_tool", "arguments": {"action": action}, "response": reply.model_dump(mode="json")})
                self.assertFalse(reply.is_error)
                self.assertEqual(reply.structured_content, query_holy_site_planning_knowledge_v1(action))
            wrong_build = await client.call_tool(TOOL, {"action": "adopt", "ck3_build": "1.20.1.1"})
            self.actual_mcp_results.append({"operation": "call_tool", "arguments": {"action": "adopt", "ck3_build": "1.20.1.1"}, "response": wrong_build.model_dump(mode="json")})
            self.assertFalse(wrong_build.is_error)
            self.assertEqual(wrong_build.structured_content["status"], "unavailable")
            for arguments in ({"action": "sanctify_relic"}, {"action": "adopt", "actor_id": 29829}, {"action": "adopt", "native_legality": True}):
                reply = await client.call_tool(TOOL, arguments)
                self.actual_mcp_results.append({"operation": "call_tool", "arguments": arguments, "response": reply.model_dump(mode="json")})
                self.assertTrue(reply.is_error)


if __name__ == "__main__":
    unittest.main()
