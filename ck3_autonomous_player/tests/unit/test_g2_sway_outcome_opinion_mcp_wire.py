"""Replay actual native Sway opinion packets through protocol state and MCP."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_outcome_opinion_private_transport import PERMISSION, STEP
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_sway_outcome_opinion"


def load_packet(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ProtocolSwayOutcomeOpinionDriver:
    """Paused fixture context with a real protocol cache and actual wire DTO."""

    allow_private_active_scheme_sway_outcome_opinion_query = False
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-sway-outcome-opinion-fixture-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        native = packet["result"]["sway_outcome_opinion"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
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
                "one_life_settlement": None, "active_wars": [], "player_armies": [], "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        # The protocol nonce is the only alteration to the actual C++ packet.
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


def test_actual_present_zero_and_absent_packets_reach_official_sdk_through_protocol_ingest_wait() -> None:
    from mcp import Client

    ProtocolSwayOutcomeOpinionDriver.query_active_scheme_sway_outcome_opinion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_outcome_opinion_private_v1
    )
    name = "ck3_query_active_scheme_sway_outcome_opinion_private_v1"
    assert parser().parse_args([]).private_active_scheme_sway_outcome_opinion_query is False
    assert parser().parse_args(["--private-active-scheme-sway-outcome-opinion-query"]).private_active_scheme_sway_outcome_opinion_query is True
    driver = ProtocolSwayOutcomeOpinionDriver(load_packet("wire-present-zero.json"))
    assert driver.initial_ingest == "state_snapshot"

    async def exercise() -> list[dict[str, object]]:
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert name not in listed
        assert driver.sent == []
        setattr(driver, PERMISSION, True)
        before = driver.take_snapshot()
        outputs = []
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert listed[name].annotations.read_only_hint is True
            for packet_name in ("wire-present-zero.json", "wire-absent.json"):
                driver.packet = load_packet(packet_name)
                original = deepcopy(driver.packet)
                native = original["result"]["sway_outcome_opinion"]
                received = await client.call_tool(name, {
                    "expected_revision": before["revision"],
                    "target_character_id": native["target_character_id"],
                })
                assert received.is_error is False, received.content
                actual = received.structured_content
                assert driver.last_ingest == "command_result"
                assert driver.packet == original
                assert {key: actual[key] for key in native} == native
                assert actual["queried_revision"] == before["revision"]
                assert actual["queried_native_revision"] == 17
                assert actual["exact_ck3_build"] == CK3_12002.game_version
                assert actual["exe_sha256"] == CK3_12002.executable_sha256
                assert actual["target_opinion_of_actor"] == 37
                assert actual["instance_terminal_outcome_observed"] is False
                assert actual["cancel_outcome_observed"] is False
                request = driver.sent[-1]
                assert request["step"] == STEP
                assert request["expected_revision"] == 17
                assert request["expected_snapshot_revision"] == 17
                assert request["actor_character_id"] == 42
                assert request["target_character_id"] == 43
                assert driver.state.wait_for_command_result(request["request_id"], 0) is None
                outputs.append(actual)
        return outputs

    present, absent = asyncio.run(exercise())
    assert present["scheme_sway_opinion"] == {"observed": True, "present": True, "value": 0}
    assert absent["scheme_sway_opinion"] == {"observed": True, "present": False, "value": None}
    assert present["sway_blocker_opinion"] == absent["sway_blocker_opinion"] == {
        "observed": True, "present": False, "value": None,
    }
    assert len(driver.sent) == 2
