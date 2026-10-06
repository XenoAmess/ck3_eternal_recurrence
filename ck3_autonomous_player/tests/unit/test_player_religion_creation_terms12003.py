"""FIRST six complete new native packets through the registered MCP query.

Root supplies compiled composed-serializer output in the required wire-dir.
Only request nonce correlation changes in the offline mailbox; no native
result, component, row, or final gate is constructed or transplanted here.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, NativeProtocolState,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.player_religion_creation_terms12003 import (
    COMPONENT_KEY, READINESS_KEY,
)
from xar_autoplayer.bridge.player_religion_reform_context_private_transport import (
    DOMAIN_KEY, STEP,
)
from xar_autoplayer.bridge.version_identity import CK3_12003


CASES = (
    "visible-zero-below-threshold", "visible-exact-threshold", "visible-above-threshold",
    "unreformed-native-branch", "different-source-and-actor-faith", "hidden-existing-window",
)


class NativePacketDriver:
    """Replay complete native command_result through the real protocol mailbox.

    Snapshot and transport are synthetic offline fixtures. The driver's query
    method is the production NativeHeadlessGameplayDriver method.
    """

    allow_private_player_religion_reform_context_query = True
    command_timeout_seconds = 1.0
    query_player_religion_reform_context_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_reform_context_private_v1
    )

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        result = packet["result"]
        body = result["player_religion_reform_context"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": body["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": result["game_version"],
                "expected_ck3_sha256": result["executable_sha256"],
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:creation-terms12003-first")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionCreationTerms12003Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_six_whole_native_creation_terms_packets_through_registered_query(self) -> None:
        # This is the sole new compound test. No legacy fixture fallback, build,
        # test-time compilation, Service subclass, mock, or normalized-row stub.
        wire_dir = Path(os.environ["XAR_CREATION_TERMS_NATIVE_WIRE_DIR"])
        for case in CASES:
            with self.subTest(case=case):
                packet = json.loads((wire_dir / f"{case}.json").read_text(encoding="utf-8"))
                self.assertEqual(packet["type"], "command_result")
                self.assertIs(packet["ok"], True)
                native_result = packet["result"]
                native = deepcopy(native_result["player_religion_reform_context"])
                driver = NativePacketDriver(packet)
                server = create_server(driver)
                tool = "ck3_query_player_religion_reform_context_v1"
                tools = {row.name: row for row in await server.list_tools()}
                self.assertTrue(tools[tool].annotations.read_only_hint)
                response = await server.call_tool(tool, {
                    "expected_revision": driver.snapshot["revision"],
                })
                self.assertFalse(response.is_error)
                actual = response.structured_content
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(driver.packet["result"], native_result)
                self.assertEqual(packet["result"], native_result)
                self.assertEqual(actual["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(actual["domain_key"], DOMAIN_KEY)
                self.assertEqual(actual["snapshot_revision"], native_result["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], native_result["snapshot_revision"])
                self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], native_result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                self.assertNotIn("target_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                terms = actual[COMPONENT_KEY]
                self.assertEqual(terms, native[COMPONENT_KEY])
                self.assertEqual(actual["readiness"][READINESS_KEY], terms["available"])
                self.assertEqual(terms["capture_epoch"], actual["capture_epoch"])
                self.assertEqual(terms["date_raw"], actual["date_raw"])
                self.assertEqual(terms["played_character_id"], actual["played_character_id"])
                if case == "hidden-existing-window":
                    self.assertIs(terms["available"], False)
                    self.assertIs(actual["available"], True)
                    self.assertIs(actual["current_context"]["available"], True)
                    self.assertIs(actual["current_creation_window"]["present"], True)
                    self.assertIs(actual["current_creation_window"]["visible"], False)
                    self.assertIs(actual["current_creation_window"]["draft_observed"], False)
                    self.assertTrue(terms["unavailable_reason"])
                    for key in ("draft_divergence_raw", "faith_creation_threshold_raw",
                                "divergence_results_in_faith_creation", "native_create_faith_or_reform"):
                        self.assertIsNone(terms[key])
                else:
                    self.assertIs(terms["available"], True)
                    self.assertIsNone(terms["unavailable_reason"])
                    self.assertIs(actual["current_creation_window"]["draft_observed"], True)
                    self.assertEqual(terms["source_rite_id"],
                                     actual["current_creation_window"]["source_rite_id"])
                    self.assertEqual(terms["raw_scale"], 100000)
                    self.assertIs(terms["divergence_results_in_faith_creation"],
                                  terms["draft_divergence_raw"] >= terms["faith_creation_threshold_raw"])
                    if case == "visible-zero-below-threshold":
                        self.assertEqual(terms["draft_divergence_raw"], 0)
                        self.assertGreater(terms["faith_creation_threshold_raw"], 0)
                        self.assertNotEqual(terms["faith_creation_threshold_raw"], 10000000)
                        self.assertIs(terms["divergence_results_in_faith_creation"], False)
                        self.assertIs(terms["native_create_faith_or_reform"], False)
                    elif case == "visible-exact-threshold":
                        self.assertEqual(terms["draft_divergence_raw"], terms["faith_creation_threshold_raw"])
                        self.assertIs(terms["divergence_results_in_faith_creation"], True)
                        self.assertIs(terms["native_create_faith_or_reform"], True)
                    elif case == "visible-above-threshold":
                        self.assertGreater(terms["draft_divergence_raw"], terms["faith_creation_threshold_raw"])
                        self.assertIs(terms["native_create_faith_or_reform"], True)
                        self.assertIs(actual["current_draft_eligibility"]["can_create_rite"], False)
                    elif case == "unreformed-native-branch":
                        self.assertIs(terms["divergence_results_in_faith_creation"], False)
                        self.assertIs(terms["native_create_faith_or_reform"], True)
                        self.assertIs(actual["main_rite_unreformed"]["is_unreformed"], True)
                    elif case == "different-source-and-actor-faith":
                        self.assertNotEqual(terms["source_faith_id"], terms["actor_faith_id"])
                        self.assertNotEqual(terms["divergence_results_in_faith_creation"],
                                            terms["native_create_faith_or_reform"])


if __name__ == "__main__":
    unittest.main()
