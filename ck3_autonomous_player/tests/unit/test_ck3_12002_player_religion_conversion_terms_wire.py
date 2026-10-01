"""Actual conversion terms mailbox output through the Python query and SDK."""

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
from xar_autoplayer.bridge.player_religion_conversion_terms_private_transport import (
    STEP, query_player_religion_conversion_terms_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "tests/fixtures/native_12002/religion_conversion_terms"


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / (case + ".json")).read_text(encoding="utf-8"))


class ConversionPacketDriver:
    """Fake protocol endpoint; only request nonce changes in the native packet."""

    allow_private_player_religion_conversion_terms_query = True
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        result = packet["result"]
        terms = result["player_religion_conversion_terms"]
        revision = result["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": f"native:{revision}", "revision": revision + 4,
            "native_revision": revision, "date_raw": result["date_raw"],
            "played_character": {"character_id": terms["played_character_id"], "alive": True},
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


@pytest.mark.parametrize("case", [
    "permitted", "native-rule-rejected", "piety-short", "current-rite",
    "target-unavailable", "cost-unavailable",
])
def test_six_actual_terms_packets_preserve_native_verdict_and_quote(case: str) -> None:
    packet = actual_packet(case)
    native = packet["result"]["player_religion_conversion_terms"]
    driver = ConversionPacketDriver(packet)
    actual = query_player_religion_conversion_terms_private_v1(
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
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == STEP
    assert driver.sent[0]["expected_snapshot_revision"] == 701
    assert driver.sent[0]["expected_revision"] == 701
    assert driver.sent[0]["target_rite_id"] == native["target_rite_id"]
    assert "character_id" not in driver.sent[0]
    if case == "permitted":
        assert actual["target_rite_id"] > 0x7FFFFFFF
        assert actual["can_convert"] is True
        assert actual["cost"]["piety_points"] == 377
        assert actual["cost"]["piety_cost_raw"] == 37_700_000
        assert actual["cost"]["actor_piety_raw"] == 40_000_000
    elif case == "native-rule-rejected":
        assert actual["available"] is True
        assert actual["can_convert"] is False
        assert actual["cost"]["can_afford_piety"] is True
    elif case == "piety-short":
        assert actual["available"] is True
        assert actual["can_convert"] is False
        assert actual["cost"]["can_afford_piety"] is False
    elif case == "current-rite":
        assert actual["target_rite_id"] == 0
        assert actual["final_gate"]["validator_with_payment"] is True
        assert actual["can_convert"] is False
    else:
        assert actual["available"] is False
        assert actual["can_convert"] is None
        assert actual["cost"]["piety_cost_raw"] is None


class ConversionSdkDriver(ConversionPacketDriver):
    def __init__(self, packet: dict[str, object]) -> None:
        super().__init__(packet)
        self.state = NativeProtocolState("offline-religion-conversion-terms-fixture")
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 101,
            "capabilities": [],
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        })

    def send(self, request: dict[str, object]) -> None:
        super().send(request)
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.state.ingest(packet)

    def query_player_religion_conversion_terms_private_v1(
        self, *, expected_revision: int, target_rite_id: int,
    ) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_player_religion_conversion_terms_private_v1(
            self, expected_revision=expected_revision, target_rite_id=target_rite_id,
        )


def test_actual_terms_packet_reaches_official_sdk_with_default_off_readonly_discovery() -> None:
    from mcp import Client

    tool_name = "ck3_query_player_religion_conversion_terms_v1"
    assert parser().parse_args([]).private_player_religion_conversion_terms_query is False
    assert parser().parse_args(["--private-player-religion-conversion-terms-query"]).private_player_religion_conversion_terms_query is True
    packet = actual_packet("permitted")
    driver = ConversionSdkDriver(packet)

    async def exercise():
        driver.allow_private_player_religion_conversion_terms_query = False
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert tool_name not in listed
        assert driver.sent == []
        driver.allow_private_player_religion_conversion_terms_query = True
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert listed[tool_name].annotations.read_only_hint is True
            native = packet["result"]["player_religion_conversion_terms"]
            called = await client.call_tool(tool_name, {
                "expected_revision": driver.snapshot["revision"],
                "target_rite_id": native["target_rite_id"],
            })
            assert called.is_error is False
            actual = called.structured_content
            assert {key: actual[key] for key in native} == native
            assert actual["native_blocker_text_available"] is False
            assert actual["cost"]["final_conversion_legality_observed"] is False
            assert actual["queried_revision"] == 705
            assert actual["queried_native_revision"] == 701

    asyncio.run(exercise())
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == STEP
    assert driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0) is None
