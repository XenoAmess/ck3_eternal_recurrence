"""Actual native reasons packets through the Python readonly query and SDK."""

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
from xar_autoplayer.bridge.player_religion_conversion_reasons_private_transport import (
    STEP, query_player_religion_conversion_reasons_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = ROOT / "tests/fixtures/native_12002/religion_conversion_reasons"
CASES = (
    "native-refusal-sso", "native-refusal-heap", "native-allowed-empty",
    "native-allowed-with-text", "native-refusal-empty", "target-zero",
    "target-unavailable", "native-text-unavailable",
)


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / (case + ".json")).read_text(encoding="utf-8"))


class ReasonsPacketDriver:
    """Protocol endpoint seam; only the native packet's request nonce changes."""

    allow_private_player_religion_conversion_reasons_query = True
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        result = packet["result"]
        reasons = result["player_religion_conversion_reasons"]
        revision = result["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": f"native:{revision}", "revision": revision + 4,
            "native_revision": revision, "date_raw": result["date_raw"],
            "played_character": {"character_id": reasons["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.sent = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet


@pytest.mark.parametrize("case", CASES)
def test_eight_actual_reasons_packets_preserve_native_text_and_verdict(case: str) -> None:
    packet = actual_packet(case)
    native = packet["result"]["player_religion_conversion_reasons"]
    driver = ReasonsPacketDriver(packet)
    actual = query_player_religion_conversion_reasons_private_v1(
        driver, expected_revision=driver.snapshot["revision"],
        target_rite_id=native["target_rite_id"],
    )
    assert {key: actual[key] for key in native} == native
    assert actual["capture_epoch"] != actual["snapshot_revision"]
    assert actual["queried_revision"] == 705
    assert actual["queried_native_revision"] == 701
    assert actual["exe_sha256"] == CK3_12002.executable_sha256
    assert actual["read_only"] is True
    assert actual["advertised"] is False
    assert actual["reason_codes_available"] is False
    assert "can_convert" not in actual
    assert len(driver.sent) == 1
    request = driver.sent[0]
    assert request["step"] == STEP
    assert request["expected_revision"] == request["expected_snapshot_revision"] == 701
    assert request["target_rite_id"] == native["target_rite_id"]
    assert "character_id" not in request
    if case.startswith("native-refusal"):
        assert actual["available"] is True
        assert actual["native_paid_validator_passes"] is False
        assert actual["native_blocker_text_available"] is True
    elif case.startswith("native-allowed"):
        assert actual["available"] is True
        assert actual["native_paid_validator_passes"] is True
        assert actual["native_blocker_text_available"] is True
    elif case == "target-zero":
        assert actual["target_rite_id"] == 0
    else:
        assert actual["available"] is False
        assert actual["native_paid_validator_passes"] is None
        assert actual["raw_native_text"] is None
        assert actual["ui_blocker_text"] is None
        assert actual["native_blocker_text_available"] is False
    if case in ("native-allowed-empty", "native-refusal-empty"):
        assert actual["raw_native_text"] == actual["ui_blocker_text"] == ""


class ReasonsSdkDriver(ReasonsPacketDriver):
    def __init__(self, packet: dict[str, object]) -> None:
        super().__init__(packet)
        self.state = NativeProtocolState("offline-religion-conversion-reasons-fixture")
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 101, "capabilities": [],
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        })

    def send(self, request: dict[str, object]) -> None:
        super().send(request)
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.state.ingest(packet)

    def query_player_religion_conversion_reasons_private_v1(
        self, *, expected_revision: int, target_rite_id: int,
    ) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_player_religion_conversion_reasons_private_v1(
            self, expected_revision=expected_revision, target_rite_id=target_rite_id,
        )


def test_actual_reasons_packet_reaches_official_sdk_with_default_off_readonly_discovery() -> None:
    from mcp import Client

    tool_name = "ck3_query_player_religion_conversion_reasons_v1"
    assert parser().parse_args([]).private_player_religion_conversion_reasons_query is False
    assert parser().parse_args(["--private-player-religion-conversion-reasons-query"]).private_player_religion_conversion_reasons_query is True
    packet = actual_packet("native-refusal-heap")
    driver = ReasonsSdkDriver(packet)

    async def exercise():
        driver.allow_private_player_religion_conversion_reasons_query = False
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert tool_name not in listed
        assert driver.sent == []
        driver.allow_private_player_religion_conversion_reasons_query = True
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert listed[tool_name].annotations.read_only_hint is True
            native = packet["result"]["player_religion_conversion_reasons"]
            called = await client.call_tool(tool_name, {
                "expected_revision": driver.snapshot["revision"],
                "target_rite_id": native["target_rite_id"],
            })
            assert called.is_error is False
            actual = called.structured_content
            assert {key: actual[key] for key in native} == native
            assert actual["reason_codes_available"] is False
            assert actual["native_paid_validator_passes"] is False
            assert "can_convert" not in actual
            assert actual["queried_revision"] == 705
            assert actual["queried_native_revision"] == 701

    asyncio.run(exercise())
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == STEP
    assert driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0) is None
