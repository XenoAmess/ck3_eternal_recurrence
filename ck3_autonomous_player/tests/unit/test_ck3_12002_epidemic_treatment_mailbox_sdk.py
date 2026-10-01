"""Actual CE1 treatment caller packets through protocol cache and MCP SDK."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


FIXTURES = Path(__file__).resolve().parents[2] / "native_bridge" / "research" / "fixtures" / "ck3_12002_epidemic_treatment_mailbox"


def load_fixture(name: str) -> dict[str, object]:
    data = (FIXTURES / name).read_bytes()
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    expected = next(item["sha256"] for item in provenance["wire"] if item["name"] == name)
    if hashlib.sha256(data).hexdigest() != expected:
        raise AssertionError(f"actual native packet bytes changed: {name}")
    return json.loads(data)


class ProtocolTreatmentSdkDriver:
    """Synthetic paused context, real protocol state, unchanged native response."""

    allow_private_epidemic_treatment_presence_query = False
    command_timeout_seconds = 30.0
    query_player_epidemic_treatment_presence_private_v1 = NativeHeadlessGameplayDriver.query_player_epidemic_treatment_presence_private_v1

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-ce1-treatment-mailbox-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        bindings = json.loads((FIXTURES / "provenance.json").read_bytes())["bindings"]
        native = packet["result"]["player_epidemic_treatment_presence"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": bindings["game_build"],
            "expected_ck3_sha256": bindings["exe_sha256"],
        })
        self.initial_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "date_raw": native["date_raw"], "speed": 1,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": native["played_character_id"], "alive": True},
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
        # The actual complete C++ packet is unmodified except request correlation.
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


class EpidemicTreatment12002MailboxSdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_present_absent_and_unavailable_packets_reach_sdk_through_ingest_wait(self) -> None:
        from mcp import Client

        name = "ck3_query_player_epidemic_treatment_presence_private_v1"
        self.assertFalse(parser().parse_args([]).private_player_epidemic_treatment_presence_query)
        self.assertTrue(parser().parse_args(["--private-player-epidemic-treatment-presence-query"]).private_player_epidemic_treatment_presence_query)
        driver = ProtocolTreatmentSdkDriver(load_fixture("present.json"))
        self.assertEqual(driver.initial_ingest, "state_snapshot")
        async with Client(create_server(driver)) as client:
            self.assertNotIn(name, {tool.name for tool in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_epidemic_treatment_presence_query = True
        before = driver.take_snapshot()
        self.assertEqual(before["native_revision"], 123)
        self.assertNotEqual(before["revision"], before["native_revision"])
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[name].annotations.read_only_hint)
            for packet_name, presence in (("present.json", True), ("absent.json", False), ("definition-unavailable.json", None)):
                with self.subTest(actual_native_packet=packet_name):
                    driver.packet = load_fixture(packet_name)
                    native_result = driver.packet["result"]
                    self.assertIn('"mailbox-fixture', driver.packet["request_id"])
                    response = await client.call_tool(name, {"expected_revision": before["revision"]})
                    self.assertFalse(response.is_error, response.content)
                    actual = response.structured_content
                    self.assertEqual(driver.last_ingest, "command_result")
                    self.assertEqual({key: actual[key] for key in native_result}, native_result)
                    self.assertEqual(actual["queried_revision"], before["revision"])
                    self.assertEqual(actual["queried_native_revision"], 123)
                    self.assertEqual(actual["query_sequence"], 1)
                    self.assertEqual(actual["observation_revision"], 3)
                    context = actual["player_epidemic_treatment_presence"]
                    self.assertIs(context["present"], presence)
                    self.assertEqual(context["played_character_id"], 50331652)
                    self.assertEqual(context["date_raw"], 53350560)
                    self.assertEqual(context["remaining_days"], {
                        "status": "unavailable", "value": None,
                        "unavailable_reason": "duration_abi_not_verified",
                    })
        self.assertEqual(len(driver.sent), 3)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-epidemic-treatment-presence-v1"})
        self.assertEqual({request["expected_revision"] for request in driver.sent}, {123})


if __name__ == "__main__":
    unittest.main()
