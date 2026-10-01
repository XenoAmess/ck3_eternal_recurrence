"""Actual choices/inputs packets via the real protocol state and readonly SDK."""

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
from xar_autoplayer.bridge import player_religion_conversion_choices_private_transport as choices
from xar_autoplayer.bridge import player_religion_conversion_inputs_private_transport as inputs
from xar_autoplayer.bridge.version_identity import CK3_12002


def actual_packet(kind: str, case: str) -> dict[str, object]:
    path = ROOT / "tests/fixtures/native_12002" / ("religion_conversion_" + kind) / (case + ".json")
    return json.loads(path.read_text(encoding="utf-8"))


class PacketDriver:
    """Correlate only the protocol nonce, then ingest into real native state."""

    command_timeout_seconds = 30.0

    def __init__(self, kind: str, packet: dict[str, object]) -> None:
        self.kind = kind
        self.packet = deepcopy(packet)
        self.module = choices if kind == "choices" else inputs
        setattr(self, self.module.PERMISSION, True)
        result = packet["result"]
        native = result["player_religion_conversion_" + kind]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 4,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {"expected_ck3_version": CK3_12002.game_version,
                                      "expected_ck3_sha256": CK3_12002.executable_sha256}},
        }
        self.state = NativeProtocolState("offline-religion-conversion-" + kind)
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

    def query_player_religion_conversion_choices_private_v1(self, *, expected_revision: int) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_player_religion_conversion_choices_private_v1(
            self, expected_revision=expected_revision,
        )

    def query_player_religion_conversion_inputs_private_v1(self, *, expected_revision: int, target_rite_id: int) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_player_religion_conversion_inputs_private_v1(
            self, expected_revision=expected_revision, target_rite_id=target_rite_id,
        )


@pytest.mark.parametrize(("kind", "case"), [
    ("choices", "choices"), ("choices", "empty"), ("choices", "faith-unavailable"),
    ("choices", "rites-unavailable"), ("choices", "both-unavailable"),
    ("inputs", "current-zero"), ("inputs", "signed-prediction"), ("inputs", "target-zero"),
    ("inputs", "gates-unavailable"), ("inputs", "prediction-unavailable"), ("inputs", "stale-target-generation"),
])
def test_eleven_actual_extension_packets_preserve_native_sources(kind: str, case: str) -> None:
    packet = actual_packet(kind, case)
    native = packet["result"]["player_religion_conversion_" + kind]
    driver = PacketDriver(kind, packet)
    kwargs = {"expected_revision": driver.snapshot["revision"]}
    if kind == "inputs":
        kwargs["target_rite_id"] = native["target_rite_id"]
        actual = inputs.query_player_religion_conversion_inputs_private_v1(driver, **kwargs)
    else:
        actual = choices.query_player_religion_conversion_choices_private_v1(driver, **kwargs)
    assert {key: actual[key] for key in native} == native
    assert actual["status"] == packet["result"]["status"]
    assert actual["capture_epoch"] != actual["snapshot_revision"]
    assert actual["queried_revision"] == actual["queried_native_revision"] + 4
    assert actual["exe_sha256"] == CK3_12002.executable_sha256
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == driver.module.STEP
    assert driver.sent[0]["expected_revision"] == packet["result"]["snapshot_revision"]
    assert driver.sent[0]["expected_snapshot_revision"] == packet["result"]["snapshot_revision"]
    assert "character_id" not in driver.sent[0]
    if kind == "choices":
        assert "target_rite_id" not in driver.sent[0]
        assert actual["membership_is_legality"] is False
        if case == "choices":
            assert actual["current_faith_rites"]["rite_ids"] == [0, 2_952_790_019]
            assert actual["faith_choices"]["choices"][1]["faith_key"] == 'target"faith'
        elif case == "empty":
            assert actual["status"] == "observed"
            assert actual["faith_choices"]["choices"] == []
        elif case == "both-unavailable":
            assert actual["current_faith_rites"]["faith_id"] == 0xFFFFFFFF
    else:
        assert driver.sent[0]["target_rite_id"] == native["target_rite_id"]
        prediction = actual["predicted_base_fulfillment"]
        assert all(prediction[key] is False for key in (
            "is_current_fulfillment", "is_observed_conversion_gain", "is_final_ai_desire"))
        if case == "current-zero":
            assert prediction["current_rite_id"] == 0
            assert prediction["current_rite_base_raw"] == 0
        elif case == "signed-prediction":
            assert prediction["current_rite_base_raw"] == -2_500_000
            assert prediction["expected_base_change_raw"] == 3_750_000
        elif case == "target-zero":
            assert actual["target_rite_id"] == 0
        elif case in {"gates-unavailable", "stale-target-generation"}:
            assert actual["conversion_gates"]["knowledge_level_raw"] is None


@pytest.mark.parametrize(("kind", "case"), [("choices", "choices"), ("inputs", "signed-prediction")])
def test_actual_extension_packet_reaches_official_sdk_with_readonly_discovery(kind: str, case: str) -> None:
    from mcp import Client

    option = "--private-player-religion-conversion-" + kind + "-query"
    argument = "private_player_religion_conversion_" + kind + "_query"
    tool_name = "ck3_query_player_religion_conversion_" + kind + "_v1"
    assert getattr(parser().parse_args([]), argument) is False
    assert getattr(parser().parse_args([option]), argument) is True
    packet = actual_packet(kind, case)
    driver = PacketDriver(kind, packet)

    async def exercise():
        setattr(driver, driver.module.PERMISSION, False)
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert tool_name not in listed
        assert driver.sent == []
        setattr(driver, driver.module.PERMISSION, True)
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert listed[tool_name].annotations.read_only_hint is True
            native = packet["result"]["player_religion_conversion_" + kind]
            fields = {"expected_revision": driver.snapshot["revision"]}
            if kind == "inputs":
                fields["target_rite_id"] = native["target_rite_id"]
            called = await client.call_tool(tool_name, fields)
            assert called.is_error is False
            actual = called.structured_content
            assert {key: actual[key] for key in native} == native
            assert actual["read_only"] is True

    asyncio.run(exercise())
    assert len(driver.sent) == 1
    assert driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0) is None
