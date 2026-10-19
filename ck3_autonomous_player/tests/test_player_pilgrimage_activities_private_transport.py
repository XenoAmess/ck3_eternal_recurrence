"""Real C++ reader/serializer packets through strict Python and registered MCP.

Set XAR_PILGRIMAGE_NATIVE_WIRE_DIR to a fresh compiled fixture output. The
transport and snapshots are owned offline fixtures; only nonce correlation
changes. Positive bodies are never reconstructed in Python. Ordinary discovery
without the native environment explicitly skips this opt-in qualification;
direct execution without it fails before unittest, so qualification cannot be
reported as passed from a missing-wire skip.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_pilgrimage_activities_private_transport import (
    STEP, TOOL, normalize_player_pilgrimage_activities_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004

CASES = ("mixed-stamp-availability", "non-pilgrimage-filtered", "empty-hosted", "full-generation")


class NativePacketDriver:
    allow_private_player_pilgrimage_activities_query = True
    command_timeout_seconds = 1.0
    query_player_pilgrimage_activities_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_pilgrimage_activities_private_v1
    )

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        body = packet["result"]["player_pilgrimage_activities"]
        self.snapshot = {
            "snapshot_id": "native:19", "revision": 23,
            "native_revision": body["snapshot_revision"], "date_raw": body["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": body["played_character_id"], "alive": True},
            "diagnostics": {"hello": {"expected_ck3_version": CK3_12004.game_version,
                                      "expected_ck3_sha256": CK3_12004.executable_sha256}},
        }
        self.after = deepcopy(self.snapshot)
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:pilgrimage-production-seam")
        self.sent = []
        self.ingested_types = []

    def take_snapshot(self):
        return deepcopy(self.after if self.sent else self.snapshot)

    def send(self, request):
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


@unittest.skipUnless(os.environ.get("XAR_PILGRIMAGE_NATIVE_WIRE_DIR"),
                     "explicit native production-wire qualification; supply XAR_PILGRIMAGE_NATIVE_WIRE_DIR")
class PilgrimageProductionSeamTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        directory = Path(os.environ["XAR_PILGRIMAGE_NATIVE_WIRE_DIR"])
        cls.provenance = json.loads((directory / "PROVENANCE.json").read_text(encoding="utf-8"))
        cls.packets = {name: json.loads((directory / (name + ".json")).read_text(encoding="utf-8"))
                       for name in CASES}

    async def test_four_native_packets_through_registered_readonly_mcp(self):
        self.assertEqual(self.provenance["production_serializer"],
                         "SerializePlayerPilgrimageActivitiesPrivate12004V1")
        self.assertEqual(self.provenance["production_reader"], "ReadActivityHostedIdentityV1")
        self.assertFalse(self.provenance["original_engine_executed"])
        for case, packet in self.packets.items():
            with self.subTest(case=case):
                native = deepcopy(packet["result"]["player_pilgrimage_activities"])
                driver = NativePacketDriver(packet)
                server = create_server(driver)
                tools = {row.name: row for row in await server.list_tools()}
                self.assertTrue(tools[TOOL].annotations.read_only_hint)
                response = await server.call_tool(TOOL, {"expected_revision": 23})
                self.assertFalse(response.is_error, response)
                actual = response.structured_content
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(packet["result"]["player_pilgrimage_activities"], native)
                self.assertEqual(driver.packet["result"]["player_pilgrimage_activities"], native)
                self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(actual["queried_revision"], 23)
                self.assertEqual(actual["queried_native_revision"], 19)
                self.assertIs(actual["absence_is_completion"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_activity_key"], "activity_pilgrimage")
                self.assertEqual(request["expected_actor_character_id"], 29829)
                self.assertEqual(request["expected_revision"], 19)
                self.assertEqual(request["expected_date_raw"], 53220000)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                rows = actual["activities"]
                if case in ("empty-hosted", "non-pilgrimage-filtered"):
                    self.assertEqual(rows, [])
                else:
                    self.assertEqual(len(rows), 2)
                    self.assertEqual(rows[0]["activity_id"],
                                     0xFE000005 if case == "full-generation" else 0x02000005)
                    self.assertEqual(rows[1]["activity_id"], 0x03000009)
                    self.assertTrue(rows[0]["native_completed"])
                    self.assertFalse(rows[0]["native_invalidated"])
                    self.assertIsNone(rows[0]["native_completion_stamp_raw"])
                    self.assertFalse(rows[0]["native_completion_stamp_observed"])
                    self.assertEqual(rows[1]["native_completion_stamp_raw"], 0)
                    self.assertTrue(rows[1]["native_completion_stamp_observed"])
                    self.assertFalse(rows[1]["native_completed"])
                    self.assertTrue(rows[1]["native_invalidated"])

    async def test_registered_mcp_rejects_unknown_arguments_before_transport(self):
        from mcp.server.mcpserver.exceptions import ToolError
        driver = NativePacketDriver(self.packets[CASES[0]])
        with self.assertRaisesRegex(ToolError, "Extra inputs are not permitted"):
            await create_server(driver).call_tool(TOOL, {
                "expected_revision": 23, "actor_character_id": 999,
            })
        self.assertEqual(driver.sent, [])

    async def test_registration_is_explicit_and_case_declared_readonly_is_supported(self):
        driver = NativePacketDriver(self.packets[CASES[0]])
        driver.allow_private_player_pilgrimage_activities_query = False
        tools = {row.name for row in await create_server(driver).list_tools()}
        self.assertNotIn(TOOL, tools)
        with self.assertRaises(UnsupportedStepError):
            driver.query_player_pilgrimage_activities_private_v1(expected_revision=23)
        self.assertEqual(driver.sent, [])
        driver.case_declared_read_only_mcp_tools = (TOOL,)
        result = await create_server(driver).call_tool(TOOL, {"expected_revision": 23})
        self.assertFalse(result.is_error)

    def test_wrong_build_and_stale_source_reject_before_send(self):
        for mode in ("build", "revision"):
            with self.subTest(mode=mode):
                driver = NativePacketDriver(self.packets[CASES[0]])
                if mode == "build":
                    driver.snapshot["diagnostics"]["hello"] = {
                        "expected_ck3_version": CK3_12003.game_version,
                        "expected_ck3_sha256": CK3_12003.executable_sha256,
                    }
                else:
                    driver.snapshot["revision"] += 1
                with self.assertRaises(BridgeUnavailableError):
                    driver.query_player_pilgrimage_activities_private_v1(expected_revision=23)
                self.assertEqual(driver.sent, [])

    def test_post_frame_change_and_native_envelope_red(self):
        driver = NativePacketDriver(self.packets[CASES[0]])
        driver.after["date_raw"] += 24
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed paused frame"):
            driver.query_player_pilgrimage_activities_private_v1(expected_revision=23)
        for mode in ("native-red", "unknown-envelope-key", "write-envelope"):
            with self.subTest(mode=mode):
                driver = NativePacketDriver(self.packets[CASES[0]])
                if mode == "native-red": driver.packet["ok"] = False
                elif mode == "write-envelope": driver.packet["result"]["read_only"] = False
                else: driver.packet["result"]["invented"] = 1
                with self.assertRaises(BridgeUnavailableError):
                    driver.query_player_pilgrimage_activities_private_v1(expected_revision=23)

    def test_strict_consumer_rejects_mutated_real_serializer_body(self):
        source = NativePacketDriver(self.packets[CASES[0]]).snapshot
        original = self.packets[CASES[0]]["result"]["player_pilgrimage_activities"]
        mutations = (
            lambda v: v.update(activity_count=1),
            lambda v: v.update(snapshot_revision=18),
            lambda v: v.update(date_raw=0),
            lambda v: v.update(played_character_id=999),
            lambda v: v.update(absence_is_completion=True),
            lambda v: v.update(raw_pointer_fields_persisted=True),
            lambda v: v["activities"][0].update(activity_id=True),
            lambda v: v["activities"][0].update(activity_id=2**32-1),
            lambda v: v["activities"][1].update(activity_id=v["activities"][0]["activity_id"]),
            lambda v: v["activities"][0].update(host_character_id=999),
            lambda v: v["activities"][0].update(type_key="activity_feast"),
            lambda v: v["activities"][0].update(native_completion_stamp_raw=0),
            lambda v: v["activities"][1].update(native_completion_stamp_raw=True),
            lambda v: v["activities"][1].update(native_completion_stamp_raw=2**64),
            lambda v: v["activities"][0].update(native_completed=None),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                value = deepcopy(original); mutate(value)
                with self.assertRaises(BridgeUnavailableError):
                    normalize_player_pilgrimage_activities_v1(value, source=source)
        # Consumer-only compatibility shape. Actual .4 reader missing terminal
        # bytes is RED and cannot produce this as a successful partial sample.
        value = deepcopy(original)
        value["activities"][0].update(terminal_flags_observed=False,
                                      native_completed=None, native_invalidated=None)
        parsed = normalize_player_pilgrimage_activities_v1(value, source=source)
        self.assertIsNone(parsed["activities"][0]["native_completed"])


if __name__ == "__main__":
    if not os.environ.get("XAR_PILGRIMAGE_NATIVE_WIRE_DIR"):
        print("native qualification requires XAR_PILGRIMAGE_NATIVE_WIRE_DIR", file=sys.stderr)
        raise SystemExit(2)
    unittest.main()
