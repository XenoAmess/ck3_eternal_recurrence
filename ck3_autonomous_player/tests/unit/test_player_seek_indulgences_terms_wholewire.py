"""The sole FIRST consumer of four future compiled native wholewire outputs.

Execution is NOT RUN in the source delivery. ROOT supplies --wire-dir after
building the native fixture once. The fixture world, predicates and session
frames are synthetic. The collector and complete result serializer, Service,
NativeDriver and protocol ingest/wait are production code. Only request_id is
rebound for correlation; native command envelopes and DTO bodies are retained.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_seek_indulgences_terms_private_transport import (
    DOMAIN_KEY, SCHEMA, STEP,
)
from xar_autoplayer.bridge.version_identity import CK3_12003


TOOL = "ck3_query_player_seek_indulgences_terms_v1"
CASES = {
    "negative-final": (True, True, False),
    "positive": (True, True, True),
    "shown-false": (True, False, True),
    "sample-failure": (False, True, None),
}
QUALIFICATION = (
    "Four complete compiled native collector/production serializer command results; "
    "synthetic world, predicates, session hello/snapshot and in-memory endpoint; "
    "production MCP, GameplayBridgeService, NativeHeadlessGameplayDriver and "
    "NativeProtocolState ingest/wait; request_id rebound only; no CK3 process, "
    "named pipe, live capability, fee, acceptance or gameplay action."
)


class _WholewireEndpoint:
    """Supply native whole command packets to the real driver's protocol state."""

    def __init__(self, case: str, packet: dict[str, object]) -> None:
        self.pipe_name = rf"\\.\pipe\xar_seek_indulgences_first_{case}"
        self.packet = deepcopy(packet)
        self.on_frame = None
        self.sent: list[dict[str, object]] = []
        self.replies: list[dict[str, object]] = []

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("fixture endpoint has not been started")
        self.on_frame(deepcopy(frame))

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        if request.get("type") == "execute_step":
            if request.get("step") != self.packet["result"]["step"]:
                raise AssertionError("query differs from the compiled native wholewire")
            reply = deepcopy(self.packet)
            reply["request_id"] = request["request_id"]
            self.replies.append(deepcopy(reply))
            self.publish(reply)

    def transport_error(self) -> str | None:
        return None

    def close(self) -> None:
        return None


class PlayerSeekIndulgencesTermsWholewireFirstTests(unittest.IsolatedAsyncioTestCase):
    async def test_four_native_wholewires_through_mcp_service_driver_ingest_wait(self) -> None:
        from mcp import Client

        directory = os.environ.get("XAR_SEEK_INDULGENCES_FIRST_WIRE_DIR")
        if not directory:
            self.fail("ROOT must supply --wire-dir or XAR_SEEK_INDULGENCES_FIRST_WIRE_DIR")
        wire_dir = Path(directory)
        hello = json.loads((wire_dir / "hello.json").read_text(encoding="utf-8-sig"))
        semantic = json.loads((wire_dir / "semantic-snapshot.json").read_text(encoding="utf-8-sig"))
        self.assertIs(hello["fixture_synthetic"], True)
        self.assertIs(semantic["fixture_synthetic"], True)
        self.assertEqual(hello["game_version"], CK3_12003.game_version)
        self.assertEqual(hello["executable_sha256"].upper(), CK3_12003.executable_sha256)
        self.assertEqual(semantic["state"]["played_character"]["character_id"], 29829)
        self.assertIs(semantic["state"]["paused"], True)
        self.assertIs(semantic["state"]["map_ready"], True)
        outputs = {}

        for case, (available, shown, can_send) in CASES.items():
            with self.subTest(case=case):
                packet = json.loads((wire_dir / f"{case}.json").read_text(encoding="utf-8-sig"))
                frozen_packet = deepcopy(packet)
                native = packet["result"]["player_seek_indulgences_terms"]
                requested = native["identity"]["requested_recipient_character_id"]
                self.assertEqual(packet["type"], "command_result")
                self.assertIs(packet["ok"], True)
                self.assertEqual(native["schema"], SCHEMA)
                self.assertEqual(native["definition_key"], "seek_indulgences_interaction")
                self.assertEqual(native["capture_epoch"], 41)
                self.assertGreater(requested, 0x7FFFFFFF)
                self.assertEqual(native["identity"]["secondary_actor_id"], -1)
                self.assertEqual(native["identity"]["intermediary_id"], -1)
                self.assertEqual(native["options"]["declared_count"], 1)
                self.assertEqual(native["options"]["selected_count"], 0)
                self.assertIs(native["options"]["all_unselected"], True)
                endpoint = _WholewireEndpoint(case, packet)
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1,
                    episode_projection="native_campaign",
                )
                try:
                    endpoint.publish(hello)
                    endpoint.publish(semantic)
                    before = driver.take_snapshot()
                    driver.allow_private_player_religion_context_query = True
                    async with Client(create_server(driver)) as client:
                        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                        self.assertIn(TOOL, tools)
                        self.assertIs(tools[TOOL].annotations.read_only_hint, True)
                        response = await client.call_tool(TOOL, {
                            "expected_revision": before["revision"],
                            "recipient_character_id": requested,
                        })
                    self.assertFalse(response.is_error)
                    actual = response.structured_content
                    self.assertEqual({key: actual[key] for key in native}, native)
                    self.assertIs(actual["available"], available)
                    self.assertIs(actual["shown"]["value"], shown)
                    self.assertIs(actual["can_send"]["value"], can_send)
                    self.assertEqual(actual["status"], "observed" if available else "unavailable")
                    self.assertEqual(actual["domain_key"], DOMAIN_KEY)
                    self.assertEqual(actual["exact_ck3_build"], CK3_12003.game_version)
                    self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                    self.assertEqual(actual["snapshot_revision"], semantic["revision"])
                    self.assertEqual(actual["queried_revision"], before["revision"])
                    self.assertEqual(actual["queried_native_revision"], semantic["revision"])
                    self.assertEqual(actual["date_raw"], semantic["state"]["date_raw"])
                    self.assertIs(actual["read_only"], True)
                    self.assertIs(actual["advertised"], False)
                    if case == "sample-failure":
                        self.assertIs(actual["can_send"]["available"], False)
                        self.assertEqual(actual["can_send"]["reason"], "native_evaluation_unavailable")
                        self.assertEqual(actual["unavailable_reason"], "one_or_more_samples_unavailable")
                    else:
                        self.assertIs(actual["can_send"]["available"], True)
                    commands = [frame for frame in endpoint.sent if frame.get("type") == "execute_step"]
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0]["step"], STEP)
                    self.assertEqual(commands[0]["recipient_character_id"], requested)
                    self.assertEqual(commands[0]["expected_revision"], semantic["revision"])
                    self.assertEqual(commands[0]["expected_snapshot_revision"], semantic["revision"])
                    self.assertNotIn("snapshot_alias", commands[0])
                    self.assertEqual(endpoint.replies[0]["result"], frozen_packet["result"])
                    self.assertIsNone(driver.state.wait_for_command_result(commands[0]["request_id"], 0))
                    self.assertEqual(packet, frozen_packet)
                    outputs[case] = actual
                    driver.allow_private_player_religion_context_query = False
                    async with Client(create_server(driver)) as disabled_client:
                        names = {tool.name for tool in (await disabled_client.list_tools()).tools}
                    self.assertNotIn(TOOL, names)
                finally:
                    driver.close()

        receipt = os.environ.get("XAR_SEEK_INDULGENCES_FIRST_RECEIPT")
        if receipt:
            destination = Path(receipt)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "status": "PASS", "qualification": QUALIFICATION,
                "wire_directory": str(wire_dir.resolve()), "cases": outputs,
                "live": False, "game_launched": False,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--wire-dir", type=Path, required=True)
    arguments.add_argument("--receipt", type=Path)
    options, unittest_arguments = arguments.parse_known_args()
    os.environ["XAR_SEEK_INDULGENCES_FIRST_WIRE_DIR"] = str(options.wire_dir)
    if options.receipt:
        os.environ["XAR_SEEK_INDULGENCES_FIRST_RECEIPT"] = str(options.receipt)
    unittest.main(argv=[sys.argv[0], *unittest_arguments])
