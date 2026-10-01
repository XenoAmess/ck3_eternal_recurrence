"""Official SDK consumes all five native hostility packets through real ingest/wait."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_player_religion_hostility_wire import CASES, MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


TOOL = "ck3_query_player_religion_hostility_v1"


class PlayerReligionHostilityMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_off_and_explicit_readonly_sdk_preserve_all_actual_packets(self) -> None:
        from mcp import Client

        class NativeWrapperWireDriver(MailboxPacketDriver):
            command_timeout_seconds = 1
            query_player_religion_hostility_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_religion_hostility_private_v1
            )

        defaults = parser().parse_args([])
        self.assertIs(defaults.private_player_religion_hostility_query, False)
        explicit = parser().parse_args(["--private-player-religion-hostility-query"])
        self.assertIs(explicit.private_player_religion_hostility_query, True)

        driver = NativeWrapperWireDriver(actual_packet("asymmetric"))
        driver.allow_private_player_religion_hostility_query = defaults.private_player_religion_hostility_query
        async with Client(create_server(driver)) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            self.assertNotIn(TOOL, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_hostility_query = explicit.private_player_religion_hostility_query
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIn(TOOL, tools)
            self.assertIs(tools[TOOL].annotations.read_only_hint, True)
            self.assertEqual(set(tools[TOOL].input_schema["required"]),
                             {"expected_revision", "target_rite_id"})
            for case in CASES:
                with self.subTest(case=case):
                    packet = actual_packet(case)
                    driver.frame = deepcopy(packet)
                    native = packet["result"]["player_religion_hostility"]
                    target = 0 if case == "zero-target-id" else 2197815298
                    result = await client.call_tool(TOOL, {
                        "expected_revision": driver.snapshot["revision"], "target_rite_id": target,
                    })
                    self.assertFalse(result.is_error)
                    actual = result.structured_content
                    self.assertEqual({key: actual[key] for key in native}, native)
                    self.assertEqual(actual["status"], packet["result"]["status"])
                    self.assertEqual(actual["capture_epoch"], 3)
                    self.assertEqual(actual["snapshot_revision"], 701)
                    self.assertEqual(actual["queried_native_revision"], 701)
                    self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                    self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                    self.assertEqual(actual["backend_id"],
                                     "ck3-1.20.0.2-native-player-religion-hostility-v1")
                    self.assertEqual(actual["domain_key"], "player_religion_hostility_v1")
                    self.assertIs(actual["read_only"], True)
                    self.assertIs(actual["advertised"], False)
                    request = driver.sent[-1]
                    self.assertEqual(request["step"], "query-player-religion-hostility-v1")
                    self.assertEqual(request["target_rite_id"], target)
                    self.assertEqual(request["expected_revision"], 701)
                    self.assertEqual(request["expected_snapshot_revision"], 701)
                    self.assertNotIn("character_id", request)
                    self.assertNotIn("actor_rite_id", request)
                    self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                    outputs[case] = actual
        self.assertEqual(len(driver.sent), 5)
        self.assertEqual(driver.ingested_types, ["command_result"] * 5)
        self.assertEqual([outputs["asymmetric"][key] for key in (
            "actor_rite_towards_target", "target_rite_towards_actor",
            "actor_faith_towards_target", "target_faith_towards_actor",
        )], [2, 0, 3, 1])
        self.assertGreater(outputs["asymmetric"]["target_rite_id"], 0x7FFFFFFF)
        self.assertNotEqual(outputs["asymmetric"]["actor_rite_id"],
                            outputs["asymmetric"]["actor_main_rite_id"])
        self.assertTrue(outputs["same-faith"]["same_faith"])
        self.assertTrue(outputs["same-faith"]["same_religion"])
        self.assertEqual(outputs["zero-target-id"]["target_rite_id"], 0)
        for case, reason in (("target-unavailable", "target_rite_unavailable"),
                             ("native-sentinel", "native_level_unavailable")):
            self.assertFalse(outputs[case]["available"])
            self.assertEqual(outputs[case]["unavailable_reason"], reason)
            self.assertIsNone(outputs[case]["target_rite_towards_actor"])
            self.assertIsNone(outputs[case]["target_rite_towards_actor_key"])
            self.assertIsNone(outputs[case]["same_faith"])


if __name__ == "__main__":
    unittest.main()
