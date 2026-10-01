"""Actual independent outcome facts through native state, query and SDK."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_religion_conversion_outcome_private_transport import (
    PERMISSION, STEP, query_player_religion_conversion_outcome_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((ROOT / "tests/fixtures/native_12002/religion_conversion_outcome" / (case + ".json")).read_text(encoding="utf-8"))


class OutcomePacketDriver:
    allow_private_player_religion_conversion_outcome_query = True
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_conversion_outcome"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 4,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {"expected_ck3_version": CK3_12002.game_version,
                                      "expected_ck3_sha256": CK3_12002.executable_sha256}},
        }
        self.state = NativeProtocolState("offline-religion-conversion-outcome")
        self.state.ingest({"type": "hello", "protocol_version": 1, "pid": 101,
                           "capabilities": [], "expected_ck3_version": CK3_12002.game_version,
                           "expected_ck3_sha256": CK3_12002.executable_sha256})
        self.endpoint = self
        self.sent = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.state.ingest(packet)

    def query_player_religion_conversion_outcome_private_v1(self, *, expected_revision: int, target_rite_id: int) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_player_religion_conversion_outcome_private_v1(
            self, expected_revision=expected_revision, target_rite_id=target_rite_id,
        )


@pytest.mark.parametrize("case", ["current", "zero-target", "target-current", "actor-unavailable", "state-unavailable", "both-unavailable"])
def test_six_actual_outcome_packets_preserve_independent_actor_and_state(case: str) -> None:
    packet = actual_packet(case)
    native = packet["result"]["player_religion_conversion_outcome"]
    driver = OutcomePacketDriver(packet)
    actual = query_player_religion_conversion_outcome_private_v1(
        driver, expected_revision=driver.snapshot["revision"], target_rite_id=native["target_rite_id"],
    )
    assert {key: actual[key] for key in native} == native
    assert actual["capture_epoch"] == 3
    assert actual["queried_native_revision"] == 901
    assert actual["queried_revision"] == 905
    assert actual["target_reached_is_identity_only"] is True
    assert actual["conversion_causality_inferred"] is False
    assert actual["state"]["flag_expiry_unit"] == "native_flag_updates"
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == STEP
    assert driver.sent[0]["target_rite_id"] == native["target_rite_id"]
    assert driver.sent[0]["expected_revision"] == 901
    assert driver.sent[0]["expected_snapshot_revision"] == 901
    assert "character_id" not in driver.sent[0]
    if case == "current":
        assert actual["actor"]["piety_raw"] == 0
        assert actual["actor"]["gold_raw"] == -123456
        assert actual["actor"]["prestige_raw"] == -7654321
        state = actual["state"]
        assert state["spiritual_fulfillment_raw"] == 345678
        assert state["baseline_spiritual_fulfillment_raw"] == 456789
        assert state["faith_conversion_recently_converted"]["remaining_updates"] == 50
        assert state["conversion_memory_recently_created"]["present"] is False
        assert state["conversion_memory_recently_created"]["expiry_counter_raw"] is None
        assert state["recent_convert"]["expiry_counter_raw"] == -1
        assert state["recent_convert"]["timed"] is False
    elif case == "zero-target":
        assert actual["target_rite_id"] == 0
    elif case == "target-current":
        assert actual["target_reached"] is True
    elif case == "state-unavailable":
        assert actual["available"] is False
        assert actual["actor"]["available"] is True
        assert type(actual["target_reached"]) is bool
    elif case == "both-unavailable":
        assert actual["target_reached"] is None
        assert actual["actor"]["piety_raw"] is None
        assert actual["state"]["recent_convert"]["present"] is None


def test_actual_outcome_packet_reaches_official_sdk_with_default_off_readonly_discovery() -> None:
    from mcp import Client

    tool_name = "ck3_query_player_religion_conversion_outcome_v1"
    assert parser().parse_args([]).private_player_religion_conversion_outcome_query is False
    assert parser().parse_args(["--private-player-religion-conversion-outcome-query"]).private_player_religion_conversion_outcome_query is True
    packet = actual_packet("current")
    driver = OutcomePacketDriver(packet)

    async def exercise():
        setattr(driver, PERMISSION, False)
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert tool_name not in listed
        assert driver.sent == []
        setattr(driver, PERMISSION, True)
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert listed[tool_name].annotations.read_only_hint is True
            native = packet["result"]["player_religion_conversion_outcome"]
            called = await client.call_tool(tool_name, {"expected_revision": 905, "target_rite_id": native["target_rite_id"]})
            assert called.is_error is False
            actual = called.structured_content
            assert {key: actual[key] for key in native} == native
            assert actual["read_only"] is True
            assert actual["state"]["flag_expiry_unit"] == "native_flag_updates"

    asyncio.run(exercise())
    assert len(driver.sent) == 1
    assert driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0) is None
