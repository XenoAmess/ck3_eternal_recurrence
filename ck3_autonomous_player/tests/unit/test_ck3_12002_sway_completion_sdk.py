"""Actual completion packets through real protocol state and official MCP SDK."""

from __future__ import annotations

from copy import deepcopy
import unittest

from test_ck3_12002_sway_completion_wire import load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


class ProtocolCompletionSdkDriver:
    """Synthetic paused fixture context; actual C++ command_result unchanged."""

    allow_private_active_scheme_sway_completion_query = False
    command_timeout_seconds = 30.0
    query_active_scheme_sway_completion_private_v1 = NativeHeadlessGameplayDriver.query_active_scheme_sway_completion_private_v1

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-sway-completion-fixture-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        native = packet["result"]["sway_completion"]
        # Only the paused context is fixture scaffolding. The complete native
        # response is copied from the actual production C++ reader/formatter.
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": native["build_version"],
            "expected_ck3_sha256": native["executable_sha256"],
        })
        self.initial_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "date_raw": native["date_raw"], "speed": 1,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": native["actor_character_id"], "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [], "player_armies": [],
                "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


class SwayCompletion12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_current_and_retained_terminal_packets_reach_the_sdk_through_protocol_ingest_wait(self) -> None:
        from mcp import Client

        name = "ck3_query_active_scheme_sway_completion_private_v1"
        self.assertFalse(parser().parse_args([]).private_active_scheme_sway_completion_query)
        self.assertTrue(parser().parse_args(["--private-active-scheme-sway-completion-query"]).private_active_scheme_sway_completion_query)
        driver = ProtocolCompletionSdkDriver(load_fixture("current-wire.json"))
        self.assertEqual(driver.initial_ingest, "state_snapshot")
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_active_scheme_sway_completion_query = True
        before = driver.take_snapshot()
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[name].annotations.read_only_hint)
            outputs = []
            for packet_name in ("current-wire.json", "terminated-owner-cleared-wire.json"):
                driver.packet = load_fixture(packet_name)
                native = driver.packet["result"]["sway_completion"]
                received = await client.call_tool(name, {
                    "expected_revision": before["revision"],
                    "target_character_id": native["target_character_id"],
                    "scheme_instance_id": native["scheme_instance_id"],
                })
                self.assertFalse(received.is_error, received.content)
                actual = received.structured_content
                self.assertEqual(driver.last_ingest, "command_result")
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["queried_revision"], before["revision"])
                self.assertEqual(actual["queried_native_revision"], before["native_revision"])
                self.assertFalse(actual["terminal_cause_observed"])
                self.assertEqual(actual["terminal_cause"], "unknown")
                self.assertNotIn("terminal", actual)
                outputs.append(actual)
        current, terminated = outputs
        self.assertFalse(current["native_terminal_state_observed"])
        self.assertEqual(current["native_success_chance_raw"], 6875000)
        self.assertTrue(terminated["native_terminal_state_observed"])
        self.assertEqual(terminated["native_status_key"], "invalidated")
        self.assertEqual(terminated["native_owner_raw"], 0xFFFFFFFF)
        self.assertIsNone(terminated["native_success_chance_raw"])
        self.assertEqual(len(driver.sent), 2)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-sway-completion-v1-private"})


if __name__ == "__main__":
    unittest.main()
