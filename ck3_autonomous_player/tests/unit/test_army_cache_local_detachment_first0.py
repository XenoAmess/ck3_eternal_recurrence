"""One Root-only compound using actual R80 whole Army and snapshot receipts.

No native producer, synthetic large payload, game, or SDK reader is started.
The actual accepted semantic frame and cache rows feed the real NativeDriver,
Service ordinary planner, and registered normal MCP plan route.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint, _hello
from xar_autoplayer.bridge import mcp_server, native_driver
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def _sdk_body(path: Path) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    response = receipt["result"]
    if response.get("is_error", response.get("isError", False)):
        raise AssertionError("input must be an existing successful actual SDK receipt")
    body = response.get("structured_content", response.get("structuredContent"))
    if not isinstance(body, dict):
        raise AssertionError("input lacks complete structured content")
    return body


class ArmyCacheLocalDetachmentFirst0Tests(unittest.TestCase):
    def test_registered_ordinary_plan_transfers_owned_actual_cache_rows_once(self):
        army_path = Path(os.environ["XAR_ARMY_CACHE_ACTUAL_PACKET"])
        frame_path = Path(os.environ["XAR_ARMY_CACHE_ACTUAL_SNAPSHOT"])
        army_body = _sdk_body(army_path)
        packet = army_body["result"]
        frame = _sdk_body(frame_path)
        rows = packet["army_strengths"]
        self.assertEqual(packet["step"], "query-army-strengths-v1")
        self.assertTrue(packet["accepted"])
        self.assertEqual(packet["queried_snapshot_id"], frame["snapshot_id"])
        self.assertEqual(packet["queried_revision"], frame["revision"])
        self.assertEqual(packet["queried_native_revision"], frame["native_revision"])
        self.assertTrue(frame["paused"])
        self.assertTrue(frame["map_ready"])
        self.assertEqual(frame["played_character"]["character_id"], 29829)
        self.assertEqual(frame["succession_lifecycle"]["lifecycle"], "ordinary_campaign_succession")
        # native_campaign returns before Army cache projection. The actual
        # ordinary accepted frame carries the normal one_life episode fields.
        self.assertNotEqual(frame.get("episode_projection"), "native_campaign")
        self.assertIsInstance(frame["episode_run_id"], str)
        self.assertEqual([row["army_id"] for row in rows], [218104048, 134218098])
        original_war_ids = tuple(rows[0]["war_ids"])
        real_deepcopy = copy.deepcopy
        production_project = NativeHeadlessGameplayDriver._with_one_life_episode

        def exercise(*, legacy_second_copy: bool):
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint,
                command_timeout_seconds=.1,
            )
            # No unrelated private native query is opted in. Keep the real
            # ordinary Service planner and registered plan route intact.
            endpoint.publish(_hello("game.state.snapshot", "game.command.query-army-strengths-v1"))
            with driver.state._condition:
                # SDK revision is public; NativeProtocolState stores the
                # producer's native revision here and exposes public revision
                # separately. Retain the whole actual frame and adapt only
                # that existing generated revision projection.
                native_frame = real_deepcopy(frame)
                native_frame["revision"] = frame["native_revision"]
                driver.state._semantic_snapshot = native_frame
                driver.state._public_revision = frame["revision"]
                driver.state._connection_generation = frame["diagnostics"]["connection_generation"]
            projected_frame = driver.state.semantic_snapshot()
            self.assertEqual(projected_frame["revision"], frame["revision"])
            self.assertEqual(projected_frame["native_revision"], frame["native_revision"])
            self.assertEqual(projected_frame["snapshot_id"], frame["snapshot_id"])
            driver._episode_character_id = frame["played_character"]["character_id"]
            driver._episode_run_id = frame["episode_run_id"]
            driver._episode_binding_state = "active_new"
            driver._succession_lifecycle = real_deepcopy(frame["succession_lifecycle"])
            driver._campaign_goal = real_deepcopy(frame["campaign_goal"])
            driver._army_strength_query = {
                "status": packet["status"],
                "army_strengths": real_deepcopy(rows),
                "query_sequence": packet["query_sequence"],
                "cache_binding": {
                    "native_revision": frame["native_revision"],
                    "snapshot_id": frame["snapshot_id"],
                    "connection_generation": frame["diagnostics"]["connection_generation"],
                    "episode_run_id": frame["episode_run_id"],
                },
            }
            stats = {"projections": 0, "second_full_row_copies": 0}
            active = {"inside": False, "rows": None}
            production_cache = driver._army_strength_cache_for_snapshot

            def observe_cache(snapshot, *, episode_run_id):
                result = production_cache(snapshot, episode_run_id=episode_run_id)
                if isinstance(result, dict):
                    stats["projections"] += 1
                    active["rows"] = result["army_strengths"]
                    self.assertEqual(active["rows"], rows)
                    self.assertIsNot(active["rows"], driver._army_strength_query["army_strengths"])
                return result

            def tracked_deepcopy(value, memo=None):
                if active["inside"] and value is active["rows"]:
                    stats["second_full_row_copies"] += 1
                return real_deepcopy(value, memo)

            def project(owner, snapshot):
                active["inside"] = True
                try:
                    result = production_project(owner, snapshot)
                    if legacy_second_copy and result.get("army_strengths"):
                        # Restore only the old redundant local-list detach.
                        # Its position after dictionary assembly has the same
                        # rows and ownership as the former field expression.
                        result["army_strengths"] = tracked_deepcopy(result["army_strengths"])
                    return result
                finally:
                    active["inside"] = False

            try:
                with mock.patch.object(driver, "_army_strength_cache_for_snapshot", side_effect=observe_cache), \
                     mock.patch.object(NativeHeadlessGameplayDriver, "_with_one_life_episode", project), \
                     mock.patch.object(native_driver, "copy", SimpleNamespace(deepcopy=tracked_deepcopy)):
                    server = mcp_server.create_server(driver)
                    response = asyncio.run(server.call_tool("ck3_plan_turn", {}))
                    self.assertFalse(response.is_error)
                    outcome = response.structured_content
                    self.assertIsInstance(outcome["plan"], dict)
                    plan_stats = dict(stats)
                    self.assertGreater(plan_stats["projections"], 0)
                    # Full public export still owns all actual normalized
                    # fields and nested leaves; no size-limited row projection.
                    public = driver.take_snapshot()
                    self.assertEqual(public["army_strengths"], rows)
                    self.assertEqual(public["army_strengths_query_sequence"], packet["query_sequence"])
                    public["army_strengths"][0]["war_ids"].append(0)
                    self.assertEqual(driver._army_strength_query["army_strengths"], rows)
                    self.assertEqual(tuple(packet["army_strengths"][0]["war_ids"]), original_war_ids)
                self.assertEqual([request for request in endpoint.frames
                                  if request.get("type") == "execute_step"], [])
                return outcome, plan_stats
            finally:
                driver.close()

        baseline, baseline_stats = exercise(legacy_second_copy=True)
        optimized, optimized_stats = exercise(legacy_second_copy=False)
        self.assertEqual(optimized, baseline)
        self.assertEqual(optimized_stats["projections"], baseline_stats["projections"])
        self.assertEqual(baseline_stats["second_full_row_copies"], baseline_stats["projections"])
        self.assertEqual(optimized_stats["second_full_row_copies"], 0)
        output = os.environ.get("XAR_ARMY_CACHE_COPY_OUTPUT")
        if output:
            with Path(output).open("x", encoding="utf-8") as handle:
                json.dump({
                    "status": "GREEN",
                    "whole_actual_army_receipt": str(army_path),
                    "whole_actual_semantic_receipt": str(frame_path),
                    "actual_response_keys_retained_as_input": list(packet),
                    "actual_army_ids": [row["army_id"] for row in rows],
                    "baseline": baseline_stats,
                    "optimized": optimized_stats,
                    "ordinary_registered_route": "ck3_plan_turn",
                    "production_service_planner_used": True,
                    "complete_cache_row_fields_retained": True,
                    "public_nested_mutation_does_not_change_cache": True,
                    "normal_plan_equal": True,
                    "added_native_calls": 0,
                    "native_producer_reruns": 0,
                    "synthetic_large_payloads": 0,
                    "live_latency_improvement_claimed": False,
                }, handle, ensure_ascii=False, indent=2)
                handle.write("\n")


if __name__ == "__main__":
    unittest.main()
