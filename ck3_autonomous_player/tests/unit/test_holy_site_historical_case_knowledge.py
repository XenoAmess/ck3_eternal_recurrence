from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server


class _NoGameDriver:
    def capabilities(self):
        raise AssertionError("historical knowledge consulted gameplay capabilities")

    def take_snapshot(self):
        raise AssertionError("historical knowledge took a game snapshot")

    def execute_step(self, *args, **kwargs):
        raise AssertionError("historical knowledge executed a game step")

    def wait_for_change(self, *args, **kwargs):
        raise AssertionError("historical knowledge waited on the game")


class HolySiteHistoricalCaseKnowledgeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_calls = []

    async def test_case_history_is_provenance_bound_isolated_and_never_current_permission(self):
        from mcp import Client

        async with Client(create_server(_NoGameDriver())) as client:
            reply = await client.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "adopt"})
            self.assertFalse(reply.is_error)
            result = reply.structured_content
            self.actual_calls.append({"action": "adopt", "result": deepcopy(result)})
            self.assertEqual(result["qualification"], "source_reviewed_static")
            self.assertFalse(result["state_observed"])
            self.assertFalse(result["action_ready"])
            self.assertIsNone(result["native_legality"])
            case = result["knowledge"]["historical_case_evidence"][0]
            self.assertEqual(case["kind"], "historical_native_observation")
            self.assertEqual(case["machine_id"], "4-8e1c2f1861")
            self.assertEqual(case["scope"]["faith_main_rite_id"], 13)
            self.assertEqual(case["observed"]["new_faith50_level"], "regular")
            self.assertEqual(case["observed"]["actual_piety_paid"], 1000)
            self.assertFalse(case["observed"]["evaluated_active_after"])
            self.assertTrue(case["observed"]["post_adoption_checkpoint_saved"])
            repository = Path(__file__).resolve().parents[3]
            raw = (repository / case["record_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), case["record_sha256"])
            record = json.loads(raw)
            self.assertTrue(record["bounded_results"]["membership_added"])
            self.assertIsNone(record["bounded_results"]["cooldown_after"])
            self.assertFalse(record["bounded_results"]["faith51_level_unchanged_same_run_verified"])
            case["observed"]["membership_added"] = False
            case["unknown_or_not_verified"].clear()
            fresh = await client.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "adopt"})
            self.assertFalse(fresh.is_error)
            self.actual_calls.append({"action": "adopt_fresh", "result": fresh.structured_content})
            self.assertTrue(fresh.structured_content["knowledge"]["historical_case_evidence"][0]["observed"]["membership_added"])
            self.assertTrue(fresh.structured_content["knowledge"]["historical_case_evidence"][0]["unknown_or_not_verified"])
            other = await client.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "create"})
            self.assertNotIn("historical_case_evidence", other.structured_content["knowledge"])
            self.actual_calls.append({"action": "create_history_scope", "result": other.structured_content})
            foreign = await client.call_tool("ck3_query_holy_site_planning_knowledge_v1", {"action": "adopt", "ck3_build": "1.20.1"})
            self.assertIsNone(foreign.structured_content["knowledge"])
            self.actual_calls.append({"action": "foreign_build_history_scope", "result": foreign.structured_content})
