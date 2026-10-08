"""One new registered Army auto-turn packaging regression; no native wire fixture."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService


def _army_auto_packet() -> dict:
    rows = []
    for army_id, carmy_id, soldiers in ((218104048, 67109093, 1833), (134218098, 167772499, 348)):
        rows.append({
            "army_id": army_id, "native_carmy_id": carmy_id, "status": "available",
            "current_soldiers": soldiers, "maximum_soldiers": soldiers + 100,
            "regiment_count": 2, "ai_base_power_raw": 6224500000,
            "ai_base_power_scale": 100000, "current_supply_raw": 0,
            "current_supply_scale": 100000, "current_attrition_fraction_raw": -1,
            "current_attrition_fraction_scale": 100000, "unavailable_reason": None,
            "synthetic_ordered_inputs": [
                {"ordinal": ordinal, "full_id": 0xFFFFFFFF if ordinal % 3 else 0,
                 "native_false": False, "unread_value": None, "raw": -(1 << 63),
                 "label": "旅人 unchanged source operand"}
                for ordinal in range(2048)
            ],
            "current_movement_progress": {
                "first_route_edge_weight_cost_raw": -1,
                "edge_progress_raw": 0,
                "conditional_native_reader_ready": False,
            },
        })
    return {
        "status": "executed", "selected_step": "query-army-strengths-v1",
        "plan": {
            "selected_step": "query-army-strengths-v1", "phase": "wartime_army_strength_query",
            "reason": "synthetic fresh-frame Army decision input",
            "native_revision": 12, "date_raw": 53288472,
            "existing_input": {"known_false": False, "unread_value": None},
        },
        "result": {
            "step": "query-army-strengths-v1", "accepted": True, "status": "available",
            "query_sequence": 7, "queried_snapshot_id": "synthetic-native:12",
            "queried_revision": 13, "queried_native_revision": 12,
            "backend_id": "synthetic_transport_fixture", "army_strengths": rows,
            "current_unit_next_arrival_transition_v1": [{
                "army_id": rows[0]["army_id"],
                "source_provenance": {"snapshot_id": "synthetic-native:12", "revision": 13, "native_revision": 12},
                "projection": {"arrival_transition_input_ready": False,
                               "conditional_unit_168_raw_after_arrival_subtraction": None,
                               "actual_future_frame_observed": False},
            }],
        },
    }


class R76ArmyAutoResultFootprintTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_registered_auto_army_preserves_packet_and_reduces_duplicate_text(self) -> None:
        army = _army_auto_packet()
        original = copy.deepcopy(army)
        ordinary = {
            "status": "executed", "selected_step": "query-war-state-v1",
            "plan": {"selected_step": "query-war-state-v1", "phase": "war_query"},
            "result": {"step": "query-war-state-v1", "accepted": True, "unknown": None, "ended": False},
        }
        blocked = {
            "status": "blocked",
            "plan": {"selected_step": "query-army-strengths-v1", "phase": "blocked"},
        }
        baseline_calls = []
        with patch.object(GameplayBridgeService, "auto_turn", autospec=True,
                          side_effect=[army, ordinary, blocked]) as auto, patch.object(
            GameplayBridgeService, "auto_nonwar_turn", autospec=True, return_value=army
        ) as nonwar:
            server = create_server(object())

            @server.tool()
            def fixture_original_auto() -> dict[str, object]:
                baseline_calls.append(True)
                return army

            baseline = await server.call_tool("fixture_original_auto", {})
            compact = await server.call_tool("ck3_auto_turn", {})
            unchanged_ordinary = await server.call_tool("ck3_auto_turn", {})
            unchanged_blocked = await server.call_tool("ck3_auto_turn", {})
            tools = {tool.name: tool for tool in await server.list_tools()}
            legacy_route_server = create_server(SimpleNamespace(nonwar_only=True))
            unchanged_route = await legacy_route_server.call_tool("ck3_auto_turn", {})

        self.assertEqual(auto.call_count, 3)
        self.assertTrue(all(call.kwargs == {} and len(call.args) == 1 for call in auto.call_args_list))
        nonwar.assert_called_once()
        self.assertEqual(nonwar.call_args.kwargs, {})
        self.assertEqual(baseline_calls, [True])
        for field in ("input_schema", "output_schema"):
            production_schema = getattr(tools["ck3_auto_turn"], field)
            baseline_schema = getattr(tools["fixture_original_auto"], field)
            self.assertEqual(
                {key: value for key, value in production_schema.items() if key != "title"},
                {key: value for key, value in baseline_schema.items() if key != "title"},
            )
        self.assertEqual(army, original)
        for output in (baseline, compact, unchanged_route):
            self.assertFalse(output.is_error)
            self.assertEqual(output.structured_content, original)
        self.assertEqual(json.loads(baseline.content[0].text), original)
        summary = json.loads(compact.content[0].text)
        self.assertEqual(summary["selected_step"], army["selected_step"])
        self.assertEqual(summary["plan"]["phase"], army["plan"]["phase"])
        self.assertEqual(summary["result"]["source"], {"revision": 13, "native_revision": 12})
        self.assertEqual(summary["result"]["army_ids"], [218104048, 134218098])
        self.assertEqual(summary["result"]["armies"][0]["current_soldiers"], 1833)
        self.assertEqual(summary["result_location"], "structuredContent")
        self.assertNotIn("synthetic_ordered_inputs", compact.content[0].text)
        self.assertLess(len(compact.content[0].text.encode("utf-8")), 4096)
        self.assertEqual(unchanged_route.content, compact.content)
        for output, expected in ((unchanged_ordinary, ordinary), (unchanged_blocked, blocked)):
            self.assertFalse(output.is_error)
            self.assertEqual(output.structured_content, expected)
            self.assertEqual(json.loads(output.content[0].text), expected)
        # One serialization of each synthetic baseline/new envelope; not a live timing claim.
        old_wire = baseline.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8")
        new_wire = compact.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8")
        self.assertGreater(len(old_wire), 256 * 1024)
        self.assertLessEqual(len(new_wire), len(old_wire) * 0.60)
        decoded = json.loads(new_wire)["structuredContent"]
        self.assertEqual(decoded, original)
        self.assertEqual(decoded["result"]["army_strengths"][0]["synthetic_ordered_inputs"], original["result"]["army_strengths"][0]["synthetic_ordered_inputs"])
        self.assertIs(decoded["result"]["army_strengths"][0]["synthetic_ordered_inputs"][0]["native_false"], False)
        self.assertIsNone(decoded["result"]["army_strengths"][0]["synthetic_ordered_inputs"][0]["unread_value"])
        self.assertEqual(decoded["result"]["army_strengths"][0]["synthetic_ordered_inputs"][0]["raw"], -(1 << 63))
        self.assertEqual(decoded["result"]["current_unit_next_arrival_transition_v1"], original["result"]["current_unit_next_arrival_transition_v1"])
        output_path = os.environ.get("XAR_R76_ARMY_AUTO_FOOTPRINT_CASE_OUTPUT")
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "synthetic_original_sdk_bytes": len(old_wire),
                "synthetic_compact_sdk_bytes": len(new_wire),
                "new_to_old_ratio": len(new_wire) / len(old_wire),
                "text_summary_bytes": len(compact.content[0].text.encode("utf-8")),
                "full_structured_packet_preserved": True,
                "ordinary_and_blocked_conversion_preserved": True,
                "auto_service_calls": auto.call_count,
                "legacy_nonwar_service_calls": nonwar.call_count,
                "actual_game_queries": 0, "native_producer_executions": 0,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
