"""Ransom MCP contract; collection's quote DTO is not native evaluator proof."""

from copy import deepcopy
import importlib.util
import unittest

from test_g2_prisoner_python_wire import PrisonerNativeWireDriver, wire
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_prisoner_ransom_private_action import STEP


class RansomMcpDriver(PrisonerNativeWireDriver):
    allow_private_prisoner_ransom_action = False
    submit_player_prisoner_ransom_private_v1 = (
        NativeHeadlessGameplayDriver.submit_player_prisoner_ransom_private_v1
    )

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        if request["step"] == STEP:
            # Existing native ACK contract, deliberately without release facts.
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True,
                    "result": {"step": STEP, "accepted": True,
                               "status": "submitted_verification_pending"}}
        return super().wait_for_command_result(request_id, timeout)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class PrisonerRansomMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_action_uses_quote_and_keeps_ack_pending(self):
        from mcp import Client

        driver = RansomMcpDriver(wire("two-prisoners"))
        name = "ck3_ransom_player_prisoner_private_v1"
        async with Client(create_server(driver)) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            self.assertNotIn(name, tools)
        self.assertEqual(driver.requests, [])
        driver.allow_private_prisoner_ransom_action = True
        async with Client(create_server(driver)) as client:
            collection = await client.call_tool(
                "ck3_query_player_prisoner_collection_private_v1",
                {"expected_revision": 12},
            )
            self.assertFalse(collection.is_error)
            row = driver.value["prisoners"][0]
            result = await client.call_tool(name, {
                "collection": deepcopy(collection.structured_content),
                "prisoner_character_id": row["prisoner_character_id"],
            })
            self.assertFalse(result.is_error)
            content = result.structured_content
            self.assertEqual(content["status"], "submitted_verification_pending")
            self.assertIs(content["material_result"], False)
            self.assertEqual(content["quoted_gold_raw"], 2_000_000)
            self.assertEqual(content["exact_ck3_build"], "1.20.0.2")
        sent = driver.requests[-1]
        self.assertEqual(sent["step"], STEP)
        self.assertEqual(sent["quote_query_sequence"], 4)
        self.assertEqual(sent["payer_character_id"], row["ransom_quote_preview"]["payer_character_id"])
        self.assertEqual(sent["prisoner_character_id"], row["prisoner_character_id"])


if __name__ == "__main__":
    unittest.main()
