"""Registered MCP roundtrips; complete synthetic AUTO DTOs, no game wire."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import combat_query_mcp_result as shaping
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService


def fixture(version=2):
    step = f"query-combat-simulation-inputs-v{version}-5-2-a-1-16777217-d-1-16777218"
    capture = {"rows": [{"index": index, "identity": 0xFFFFFFFF,
                         "negative": -1, "enabled": False, "operand": None,
                         "order": [7, 7, 0], "text": "骑士原始上下文"}
                        for index in range(16)]}
    inputs = {"scenario": {"attacker_army_ids": [16777217],
                            "defender_army_ids": [16777218]},
              "knight_stat_consumption_v1": {"events": [{"contexts": [
                  {"preparation_at_entry": deepcopy(capture),
                   "consumption_capture": deepcopy(capture)}]}]}}
    return {"status": "executed", "selected_step": step,
            "plan": {"selected_step": step, "phase": "native_war_general_battle_inputs_query",
                     "risk_guard": {"attack_allowed": False}},
            "planning_source_frame": {"snapshot_id": "native:10292", "revision": 83,
                                      "native_revision": 10292, "date_raw": 53363808},
            "result": {"step": step, "accepted": True, "status": "available",
                       "query_sequence": 7, "queried_snapshot_id": "native:10292",
                       "queried_revision": 83, "queried_native_revision": 10292,
                       "combat_simulation_inputs": inputs if version == 2 else {"base_inputs": inputs}}}


class CombatQueryMcpResultTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_registered_client_keeps_full_structured_and_avoids_two_full_conversions(self):
        from mcp import Client
        from mcp.server.mcpserver.utilities import func_metadata

        self.measurements = []
        for version in (2, 3):
            with self.subTest(version=version):
                payload = fixture(version)
                before = deepcopy(payload)
                with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True,
                                       return_value=payload) as auto:
                    server = create_server(object())

                    @server.tool()
                    def fixture_legacy_auto() -> dict[str, object]:
                        return payload

                    legacy = server._tool_manager.get_tool("fixture_legacy_auto").fn_metadata
                    actual = server._tool_manager.get_tool("ck3_auto_turn").fn_metadata
                    for schema_name in ("output_schema",):
                        left, right = getattr(legacy, schema_name), getattr(actual, schema_name)
                        self.assertEqual({k: v for k, v in left.items() if k != "title"},
                                         {k: v for k, v in right.items() if k != "title"})
                    original_content = func_metadata._convert_to_content
                    dump = legacy.output_model.model_dump
                    with (mock.patch.object(func_metadata, "_convert_to_content", wraps=original_content) as text,
                          mock.patch.object(legacy.output_model, "model_dump", autospec=True, side_effect=dump) as dumping,
                          mock.patch.object(legacy.output_model, "model_validate", wraps=legacy.output_model.model_validate) as validating):
                        async with Client(server) as client:
                            old = await client.call_tool("fixture_legacy_auto", {})
                        old_counts = (text.call_count, dumping.call_count, validating.call_count)
                    dump = actual.output_model.model_dump
                    with (mock.patch.object(func_metadata, "_convert_to_content", wraps=original_content) as text,
                          mock.patch.object(actual.output_model, "model_dump", autospec=True, side_effect=dump) as dumping,
                          mock.patch.object(actual.output_model, "model_validate", wraps=actual.output_model.model_validate) as validating):
                        async with Client(server) as client:
                            new = await client.call_tool("ck3_auto_turn", {})
                        new_counts = (text.call_count, dumping.call_count, validating.call_count)
                auto.assert_called_once_with(mock.ANY)
                self.assertEqual(old_counts, (1, 1, 1))
                self.assertEqual(new_counts, (0, 0, 1))
                self.assertFalse(new.is_error)
                self.assertEqual(new.structured_content, before)
                self.assertEqual(old.structured_content, before)
                self.assertEqual(payload, before)
                self.assertEqual(json.loads(old.content[0].text), before)
                summary = json.loads(new.content[0].text)
                self.assertEqual(summary["full_result_location"], "structuredContent")
                self.assertFalse(summary["text_contains_full_result"])
                self.assertLess(len(new.content[0].text.encode()), 1024)
                self.measurements.append({
                    "version": version,
                    "legacy_complete_result_bytes": len(old.model_dump_json(by_alias=True).encode()),
                    "new_complete_result_bytes": len(new.model_dump_json(by_alias=True).encode()),
                    "legacy_full_pretty_text_bytes": len(old.content[0].text.encode()),
                    "new_summary_text_bytes": len(new.content[0].text.encode()),
                    "legacy_full_unstructured_conversions": old_counts[0],
                    "new_full_unstructured_conversions": new_counts[0],
                    "legacy_output_model_json_dumps": old_counts[1],
                    "new_output_model_json_dumps": new_counts[1],
                    "legacy_and_new_output_model_validations": new_counts[2],
                    "full_structured_equal": True, "elapsed_speedup_claimed": False,
                })

    async def test_explicit_result_still_passes_the_real_registered_output_validator(self):
        from mcp.types import CallToolResult
        from mcp.server.mcpserver.exceptions import ToolError
        payload = fixture()
        with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True, return_value=payload):
            server = create_server(object())
            metadata = server._tool_manager.get_tool("ck3_auto_turn").fn_metadata
            # This deliberately malformed return tests the SDK output boundary,
            # not Native business validation (the Service is synthetic here).
            bad = CallToolResult(content=[], structured_content=["not an object"])
            with mock.patch.object(shaping, "build_combat_query_auto_turn_mcp_result", return_value=bad), \
                    mock.patch.object(metadata.output_model, "model_validate", wraps=metadata.output_model.model_validate) as validate:
                with self.assertRaisesRegex(ToolError, "valid dictionary"):
                    await server.call_tool("ck3_auto_turn", {})
            self.assertEqual(validate.call_count, 1)

    async def test_unrelated_blocked_or_mismatched_turns_keep_original_conversion(self):
        for change in ("blocked", "other", "mismatch"):
            payload = fixture()
            if change == "blocked":
                payload["status"] = "blocked"
            elif change == "other":
                payload["selected_step"] = payload["plan"]["selected_step"] = payload["result"]["step"] = "query-war-state-v1"
            else:
                payload["plan"]["selected_step"] = "query-war-state-v1"
            self.assertIs(shaping.build_combat_query_auto_turn_mcp_result(payload), payload)
            with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True, return_value=payload):
                result = await create_server(object()).call_tool("ck3_auto_turn", {})
            self.assertEqual(result.structured_content, payload)
            self.assertEqual(json.loads(result.content[0].text), payload)


if __name__ == "__main__":
    unittest.main()
