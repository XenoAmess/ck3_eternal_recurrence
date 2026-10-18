"""Native query functions plus registered MCP with a small in-memory market."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "src"), str(HERE)]
from test_mercenary_history_projection_v1 import InMemoryMarketEndpoint
from xar_autoplayer.bridge import mercenary_query_mcp_result as shaping
from xar_autoplayer.bridge import native_driver, player_mercenary_context as contract
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer import war_mercenary_consumer_v1 as consumer


class MercenaryQueryMcpResultTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        endpoint = InMemoryMarketEndpoint()
        endpoint.sequence = 2**63 + 7

        def numbers(value):
            for row, company_id in zip(value["rows"], (0, 0x80000001, 0xFFFFFFFF)):
                row["company_id"] = row["composition_v1"]["company_id"] = company_id
            value["rows"][0]["final_terms"].update(
                resource_costs_raw=[33_000_001, -(2**63), 2**63 - 1] + [0] * 7,
                can_afford=False, can_hire=True, payment_status=1,
                can_afford_reason_literal="原生允许债务；不能折成禁止雇佣")
            value["rows"][1]["employer_id"] = 0

        endpoint.transform = numbers
        self.driver = native_driver.NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.5)
        endpoint.on_frame({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 4242, "session_generation": 0,
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", contract.CAPABILITY],
        })
        endpoint.publish()
        self.endpoint = endpoint
        app = GameplayBridgeService(self.driver)
        revision = self.driver.take_snapshot_without_native_command_history()["revision"]
        self.query = app.query_player_mercenary_context_v1(expected_revision=revision)
        self.snapshot = self.driver.take_snapshot_without_native_command_history()
        self.payload = {"status": "executed", "selected_step": contract.STEP,
                        "plan": {"selected_step": contract.STEP, "phase": "native_war_mercenary_query",
                                 "active_attack_allowed": False}, "result": self.query}

    def tearDown(self):
        self.driver.close()

    async def test_registered_AUTO_keeps_complete_numbers_frame_and_hire_terms_without_pretty_copy(self):
        from mcp import Client
        from mcp.server.mcpserver.utilities import func_metadata

        before = deepcopy(self.payload)
        with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True,
                               return_value=self.payload) as auto:
            server = create_server(self.driver)

            @server.tool()
            def fixture_legacy_market_auto() -> dict[str, object]:
                return self.payload

            original = server._tool_manager.get_tool("fixture_legacy_market_auto").fn_metadata
            current = server._tool_manager.get_tool("ck3_auto_turn").fn_metadata
            self.assertEqual({k: v for k, v in original.output_schema.items() if k != "title"},
                             {k: v for k, v in current.output_schema.items() if k != "title"})
            async with Client(server) as client:
                baseline = await client.call_tool("fixture_legacy_market_auto", {})
                with (mock.patch.object(func_metadata, "_convert_to_content",
                                        side_effect=AssertionError("full pretty encoding reached")),
                      mock.patch.object(current.output_model, "model_dump", autospec=True,
                                        side_effect=AssertionError("second full output dump reached")),
                      mock.patch.object(current.output_model, "model_validate",
                                        wraps=current.output_model.model_validate) as validation):
                    result = await client.call_tool("ck3_auto_turn", {})
                self.assertEqual(validation.call_count, 1)
        auto.assert_called_once_with(mock.ANY)
        self.assertEqual(result.structured_content, baseline.structured_content)
        self.assertEqual(result.structured_content, before)
        self.assertEqual(self.payload, before)
        self.assertFalse(result.is_error)
        summary = json.loads(result.content[0].text)
        self.assertEqual(summary["full_result_location"], "structuredContent")
        self.assertFalse(summary["text_contains_full_result"])
        self.assertLess(len(result.content[0].text.encode()), 1024)

        encoded = json.loads(result.model_dump_json(by_alias=True))
        decoded = encoded.get("structuredContent", encoded.get("structured_content"))
        self.assertEqual(decoded, before)
        full = decoded["result"]
        normalized = contract.normalize_player_mercenary_context_v1(
            full["player_mercenary_context"], snapshot=self.snapshot)
        self.assertEqual(normalized, self.query["player_mercenary_context"])
        self.assertEqual([row["company_id"] for row in normalized["rows"]],
                         [0, 0x80000001, 0xFFFFFFFF])
        terms = normalized["rows"][0]["final_terms"]
        self.assertEqual(terms["resource_costs_raw"], [33_000_001, -(2**63), 2**63 - 1] + [0] * 7)
        self.assertIs(terms["can_afford"], False)
        self.assertIs(terms["can_hire"], True)
        self.assertEqual(terms["payment_status"], 1)
        self.assertTrue(normalized["rows"][0]["readiness_v1"]["hire_ready"])
        self.assertEqual(normalized["rows"][1]["employer_id"], 0)
        self.assertEqual(full["query_sequence"], 2**63 + 8)
        self.assertEqual(normalized["capture_epoch"], 2**63 + 8)
        history = self.driver._history_snapshot()
        history[-1]["result"] = full
        context, reference = consumer._context_with_reference(history, self.snapshot)
        self.assertEqual(context, normalized)
        self.assertEqual(reference["query_sequence"], full["query_sequence"])
        self.assertEqual(reference["source_frame"], full["mercenary_query_source_frame_v1"])
        # Existing hire-context gates keep rejecting stale or misbound data.
        for field in ("actor_character_id", "company_composition"):
            stale = deepcopy(history)
            if field == "actor_character_id":
                stale[-1]["result"]["player_mercenary_context"][field] += 1
            else:
                stale[-1]["result"]["player_mercenary_context"]["rows"][0]["composition_v1"]["company_id"] = 3
            self.assertIsNone(consumer._context(stale, self.snapshot))
        self.measurements = {
            "baseline_result_bytes": len(baseline.model_dump_json(by_alias=True).encode()),
            "candidate_result_bytes": len(result.model_dump_json(by_alias=True).encode()),
            "baseline_text_bytes": len(baseline.content[0].text.encode()),
            "candidate_text_bytes": len(result.content[0].text.encode()),
            "candidate_full_pretty_encodes": 0, "candidate_output_model_json_dumps": 0,
            "candidate_original_output_model_validations": 1,
            "same_full_structured": True, "actual_hire_submissions": 0,
            "standard_JSON_bytes_decode_keeps_exact_numbers_and_binding": True,
        }

    async def test_direct_MCP_keeps_complete_text_and_original_decoder(self):
        from mcp import Client
        revision = self.snapshot["revision"]
        with mock.patch.object(GameplayBridgeService, "query_player_mercenary_context_v1",
                               autospec=True, return_value=self.query):
            async with Client(create_server(self.driver)) as client:
                result = await client.call_tool("ck3_query_player_mercenary_context_v1",
                                                {"expected_revision": revision})
        self.assertEqual(result.structured_content, self.query)
        self.assertEqual(json.loads(result.content[0].text), self.query)

    async def test_non_native_unavailable_hire_and_error_AUTO_are_unchanged(self):
        for case in ("nonnative", "unavailable", "hire", "failed", "blocked", "not_readonly"):
            payload = deepcopy(self.payload)
            if case == "nonnative":
                payload["result"]["backend_id"] = "synthetic-other-backend"
            elif case == "unavailable":
                payload["result"]["player_mercenary_context"].update(available=False,
                    unavailable_reason="fixture unavailable", rows=[])
            elif case == "hire":
                payload["selected_step"] = payload["plan"]["selected_step"] = payload["result"]["step"] = "hire-mercenary-v1"
            elif case == "failed":
                payload["result"]["accepted"] = False
            elif case == "blocked":
                payload["status"] = "blocked"
            else:
                payload["result"]["read_only"] = False
            self.assertIs(shaping.build_mercenary_query_auto_turn_mcp_result(payload), payload)
            with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True, return_value=payload):
                result = await create_server(self.driver).call_tool("ck3_auto_turn", {})
            self.assertEqual(result.structured_content, payload)
            self.assertEqual(json.loads(result.content[0].text), payload)

        from mcp.server.mcpserver.exceptions import ToolError
        with (mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True,
                                side_effect=BridgeUnavailableError("fixture native refusal")),
              mock.patch.object(shaping, "build_mercenary_query_auto_turn_mcp_result") as shape):
            with self.assertRaisesRegex(ToolError, "fixture native refusal"):
                await create_server(self.driver).call_tool("ck3_auto_turn", {})
            shape.assert_not_called()

    async def test_original_registered_output_schema_still_rejects_bad_result(self):
        from mcp.server.mcpserver.exceptions import ToolError
        from mcp.types import CallToolResult
        with mock.patch.object(GameplayBridgeService, "auto_turn", autospec=True, return_value=self.payload):
            server = create_server(self.driver)
            model = server._tool_manager.get_tool("ck3_auto_turn").fn_metadata.output_model
            with (mock.patch.object(shaping, "build_mercenary_query_auto_turn_mcp_result",
                                    return_value=CallToolResult(content=[], structured_content=["wrong root"])),
                  mock.patch.object(model, "model_validate", wraps=model.model_validate) as validation):
                with self.assertRaisesRegex(ToolError, "valid dictionary"):
                    await server.call_tool("ck3_auto_turn", {})
                self.assertEqual(validation.call_count, 1)


if __name__ == "__main__":
    unittest.main()
