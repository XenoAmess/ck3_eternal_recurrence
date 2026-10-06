"""New actual .4 whole native packets through the two registered MCP tools.

AUTHORED_NOTRUN. Root supplies the new native fixture output directory through
XAR_CK3_12004_EPIDEMIC_FIXTURE_DIR; this test never loads historic .2/.3 packets.
Only hello/snapshot scaffolding and request correlation are synthetic. The
native command_result envelope and payload are consumed without modification.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    NativeProtocolState,
)


BUILD = "1.20.0.4"
EXE_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
TREATMENT_TOOL = "ck3_query_player_epidemic_treatment_presence_private_v1"
RECOVERY_TOOL = "ck3_query_player_epidemic_recovery_private_v1"
DURATION = {"status": "unavailable", "value": None,
            "unavailable_reason": "duration_abi_not_verified"}


class WholeNativeEpidemicDriver:
    allow_private_epidemic_recovery_query = True
    allow_private_epidemic_treatment_presence_query = True
    command_timeout_seconds = 30.0
    query_player_epidemic_recovery_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_epidemic_recovery_private_v1
    )
    query_player_epidemic_treatment_presence_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_epidemic_treatment_presence_private_v1
    )

    def __init__(self) -> None:
        self.state = NativeProtocolState("synthetic-actual4-epidemic-whole-fixture")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": BUILD, "expected_ck3_sha256": EXE_SHA,
        })

    def select_packet(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        result = packet["result"]
        self.payload_key = ("player_epidemic_recovery" if
                            "player_epidemic_recovery" in result else
                            "player_epidemic_treatment_presence")
        native = result[self.payload_key]
        list_mode = self.payload_key == "player_epidemic_recovery" and native["requested_title_id"] == 0
        self.snapshot_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "date_raw": native["date_raw"], "speed": 1,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": native["played_character_id"], "alive": True},
                "active_event": {"instance_id": 73} if list_mode else None,
                "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [],
                "player_armies": [], "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.result_ingest = self.state.ingest(packet)


class Actual4EpidemicWholeQueryMcpTest(unittest.IsolatedAsyncioTestCase):
    async def test_new_whole_native_packets_reach_both_actual_registered_tools(self) -> None:
        from mcp import Client

        fixture_path = os.environ.get("XAR_CK3_12004_EPIDEMIC_FIXTURE_DIR")
        if not fixture_path:
            self.skipTest("AUTHORED_NOTRUN: new .4 native output directory was not supplied")
        fixtures = Path(fixture_path)
        provenance = json.loads((fixtures / "provenance.json").read_bytes())
        self.assertEqual(provenance["game_version"], BUILD)
        self.assertEqual(provenance["steam_build_id"], 25734779)
        self.assertEqual(provenance["executable_sha256"], EXE_SHA)
        self.assertIs(provenance["native_callbacks_synthetic"], True)
        self.assertIs(provenance["actual4_profile_bindings_verified"], True)
        self.assertIs(provenance["old_fixture_main_invoked"], False)
        self.assertIs(provenance["live"], False)
        cases = (
            ("recovery-two-counties.json", 2),
            ("recovery-empty-list.json", 0),
            ("recovery-list-unavailable.json", None),
            ("recovery-explicit-absent.json", 1),
            ("recovery-definition-unavailable.json", None),
            ("treatment-present.json", True),
            ("treatment-absent.json", False),
            ("treatment-empty-extension.json", False),
            ("treatment-empty-rows.json", False),
            ("treatment-rows-unavailable.json", None),
            ("treatment-definition-unavailable.json", None),
        )
        driver = WholeNativeEpidemicDriver()
        driver.select_packet(json.loads((fixtures / cases[0][0]).read_bytes()))
        async with Client(create_server(driver)) as client:
            registered = {tool.name: tool for tool in (await client.list_tools()).tools}
            for name in (TREATMENT_TOOL, RECOVERY_TOOL):
                self.assertIn(name, registered)
                self.assertTrue(registered[name].annotations.read_only_hint)
            for packet_name, expected in cases:
                with self.subTest(native_whole_packet=packet_name):
                    packet = json.loads((fixtures / packet_name).read_bytes())
                    driver.select_packet(packet)
                    self.assertEqual(driver.snapshot_ingest, "state_snapshot")
                    before = driver.take_snapshot()
                    self.assertEqual(before["native_revision"], 88)
                    native_result = packet["result"]
                    native = native_result[driver.payload_key]
                    arguments = {"expected_revision": before["revision"]}
                    if driver.payload_key == "player_epidemic_recovery":
                        title = native["requested_title_id"]
                        arguments.update({"requested_title_id": title,
                                          "expected_event_instance_id": None if title else 73})
                        tool = RECOVERY_TOOL
                    else:
                        tool = TREATMENT_TOOL
                    response = await client.call_tool(tool, arguments)
                    self.assertFalse(response.is_error, response.content)
                    actual = response.structured_content
                    self.assertEqual(driver.result_ingest, "command_result")
                    self.assertEqual({key: actual[key] for key in native_result}, native_result)
                    self.assertEqual(actual["queried_revision"], before["revision"])
                    self.assertEqual(actual["queried_native_revision"], 88)
                    material = actual[driver.payload_key]
                    self.assertEqual(material["remaining_days"], DURATION)
                    self.assertEqual(material["played_character_id"], provenance["played_character_id"])
                    self.assertEqual(material["date_raw"], provenance["date_raw"])
                    if driver.payload_key == "player_epidemic_recovery":
                        counties = material["counties"]
                        if expected is None:
                            self.assertIsNone(counties)
                        else:
                            self.assertEqual(len(counties), expected)
                            if packet_name == "recovery-explicit-absent.json":
                                self.assertIs(counties[0]["minor_present"], False)
                                self.assertIs(counties[0]["tiny_present"], False)
                    else:
                        self.assertIs(material["present"], expected)
                    self.assertEqual(material["status"], "unavailable" if expected is None else "available")
        self.assertEqual(len(driver.sent), len(cases))
        self.assertEqual({request["expected_revision"] for request in driver.sent}, {88})


if __name__ == "__main__":
    unittest.main()
