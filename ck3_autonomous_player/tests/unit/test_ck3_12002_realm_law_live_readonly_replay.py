"""Replay actual paused LAW frames through real protocol state and MCP SDK."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_realm_law_live_readonly"


def frame(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ProtocolReplayLawDriver:
    """Use production protocol ingest/wait without creating a native pipe."""

    allow_private_realm_law_paused_query = True
    command_timeout_seconds = 30.0
    query_realm_law_final_terms_private_v1 = NativeHeadlessGameplayDriver.query_realm_law_final_terms_private_v1

    def __init__(self) -> None:
        self.state = NativeProtocolState("offline-law-captured-frame-replay")
        self.state.ingest(frame("hello.json"))
        self.initial_ingest = self.state.ingest(frame("initial-state.json"))
        self.endpoint = self
        self.sent: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        reply = frame("law-response.json")
        reply["request_id"] = request["request_id"]
        self.state.ingest(reply)
        self.final_ingest = self.state.ingest(frame("final-state.json"))


class RealmLaw12002ActualProtocolReplayTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_readonly_frame_roundtrips_costs_reasons_and_bound_outer_revision(self) -> None:
        from mcp import Client

        driver = ProtocolReplayLawDriver()
        self.assertEqual(driver.initial_ingest, "state_snapshot")
        before = driver.take_snapshot()
        native = frame("law-response.json")["result"]["realm_law_final_terms"]
        self.assertEqual(before["native_revision"], 2)
        self.assertEqual(before["played_character"]["character_id"], 29829)
        self.assertEqual(before["date_raw"], 53169072)
        async with Client(create_server(driver)) as client:
            name = "ck3_query_realm_law_final_terms_private_v1"
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[name].annotations.read_only_hint)
            received = await client.call_tool(name, {"expected_revision": before["revision"]})
            self.assertFalse(received.is_error, received.content)
            actual = received.structured_content
        self.assertEqual(driver.final_ingest, "state_snapshot")
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual["snapshot_revision"], frame("law-response.json")["result"]["snapshot_revision"])
        self.assertEqual(actual["queried_native_revision"], before["native_revision"])
        self.assertEqual(actual["exe_sha256"], frame("hello.json")["expected_ck3_sha256"])
        self.assertEqual(len(actual["groups"]), 2)
        self.assertEqual([len(group["candidates"]) for group in actual["groups"]], [4, 4])
        crown = actual["groups"][0]
        selected = next(row for row in crown["candidates"] if row["law_key"] == "crown_authority_1")
        self.assertTrue(selected["final_can_enact"])
        self.assertEqual(selected["cost_raw"][actual["cost_slots"].index("prestige")], 22300000)
        blocked = actual["groups"][1]["candidates"][1]
        self.assertIn("\x15", blocked["native_reason"])
        self.assertIn("\n", blocked["native_reason"])
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], "query-realm-law-final-terms-v1-private")
        self.assertEqual(driver.sent[0]["expected_revision"], 2)
        self.assertEqual(driver.state._command_results, {})


if __name__ == "__main__":
    unittest.main()
