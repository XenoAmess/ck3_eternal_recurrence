from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.title_holder_contract import (
    QUERY_TITLE_HOLDER_V1_CAPABILITY,
    normalize_title_holder_v1,
    query_title_holder_v1_step,
)


FIXTURES = PROJECT_ROOT / "tests/fixtures/native_12003/title_holder_v1"


def _native_results() -> list[tuple[str, dict[str, object]]]:
    """Read the production native reader/serializer fixture outputs verbatim."""
    paths = sorted(FIXTURES.glob("*.json"))
    if not paths:
        raise AssertionError("production-native title-holder wire fixtures are missing")
    rows = []
    for path in paths:
        wire = json.loads(path.read_text(encoding="utf-8-sig"))
        result = wire.get("result", wire)
        if isinstance(result, dict) and isinstance(result.get("title_holder"), dict):
            rows.append((path.stem, result))
    if not rows:
        raise AssertionError("native fixtures do not contain title-holder results")
    return rows


class _NativeFixtureEndpoint:
    def __init__(self, result: dict[str, object]) -> None:
        self.pipe_name = r"\\.\pipe\xar_title_holder_fixture"
        self.result = copy.deepcopy(result)
        self.frames: list[dict[str, object]] = []
        self.on_frame = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(copy.deepcopy(frame))
        if frame.get("type") == "execute_step":
            assert frame["step"] == self.result["step"]
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": copy.deepcopy(self.result),
            })

    def close(self) -> None:
        pass

    def transport_error(self) -> str | None:
        return None


def _driver(result: dict[str, object]) -> tuple[NativeHeadlessGameplayDriver, _NativeFixtureEndpoint]:
    value = result["title_holder"]
    endpoint = _NativeFixtureEndpoint(result)
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.2,
    )
    endpoint.publish({
        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
        "pid": 4545, "session_generation": 0,
        "game_version": value["game_version"],
        "executable_sha256": value["executable_sha256"],
        "capabilities": ["game.state.snapshot", QUERY_TITLE_HOLDER_V1_CAPABILITY],
    })
    native_revision = value["snapshot_revision"]
    endpoint.publish({
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": f"native:{native_revision}", "revision": native_revision,
        "state": {
            "date_raw": value["date_raw"], "speed": 1, "paused": True,
            "local_player_id": 0, "map_ready": True,
            "played_character": {"character_id": value["actor_character_id"], "alive": True},
            "active_event": None, "pending_character_interaction": None,
            "history": [], "one_life_settlement": None,
            # No war or held-title partition is needed to query an arbitrary title.
            "active_wars": [], "player_armies": [],
        },
    })
    return driver, endpoint


class TitleHolderNativeWireTests(unittest.TestCase):
    def test_production_native_wire_through_driver_and_service(self) -> None:
        observed = []
        for name, native_result in _native_results():
            with self.subTest(name=name):
                driver, endpoint = _driver(native_result)
                try:
                    snapshot = driver.take_snapshot()
                    value = native_result["title_holder"]
                    result = GameplayBridgeService(driver).query_title_holder_v1(
                        value["title_id"], expected_revision=snapshot["revision"],
                    )
                    self.assertEqual(result["title_holder"], value)
                    self.assertTrue(result["read_only"])
                    self.assertEqual(result["queried_native_revision"], value["snapshot_revision"])
                    commands = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0]["step"], query_title_holder_v1_step(value["title_id"]))
                    self.assertEqual(commands[0]["expected_revision"], value["snapshot_revision"])
                    observed.append(value)
                finally:
                    driver.close()
        # These are materially distinct native observations, not synthesized DTOs.
        self.assertTrue(any(row["available"] and row["holder_is_player"] for row in observed))
        self.assertTrue(any(row["available"] and row["holder_in_player_realm"] and not row["holder_is_player"] for row in observed))
        self.assertTrue(any(row["available"] and row["holder_character_id"] is not None and not row["holder_in_player_realm"] for row in observed))
        self.assertTrue(any(row["available"] and row["holder_character_id"] is None for row in observed))
        self.assertTrue(any(not row["available"] for row in observed))

    def test_wire_is_bound_to_requested_title_and_actor(self) -> None:
        native_result = next(result for _, result in _native_results() if result["title_holder"]["available"])
        value = native_result["title_holder"]
        common = {
            "expected_title_id": value["title_id"],
            "expected_actor_character_id": value["actor_character_id"],
            "expected_snapshot_revision": value["snapshot_revision"],
            "expected_date_raw": value["date_raw"],
        }
        with self.assertRaisesRegex(ValueError, "requested TitleID"):
            normalize_title_holder_v1(value, **{**common, "expected_title_id": value["title_id"] + 1})
        with self.assertRaisesRegex(ValueError, "played character"):
            normalize_title_holder_v1(value, **{**common, "expected_actor_character_id": value["actor_character_id"] + 1})


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class TitleHolderRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_mcp_consumes_the_production_native_wires(self) -> None:
        from mcp import Client

        for name, native_result in _native_results():
            with self.subTest(name=name):
                driver, endpoint = _driver(native_result)
                try:
                    revision = driver.take_snapshot()["revision"]
                    server = create_server(driver)
                    async with Client(server) as client:
                        listed = await client.list_tools()
                        tool = next(row for row in listed.tools if row.name == "ck3_query_title_holder_v1")
                        self.assertEqual(set(tool.input_schema["required"]), {"title_id", "expected_revision"})
                        result = await client.call_tool("ck3_query_title_holder_v1", {
                            "title_id": native_result["title_holder"]["title_id"],
                            "expected_revision": revision,
                        })
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content["title_holder"], native_result["title_holder"])
                    self.assertEqual(len([row for row in endpoint.frames if row.get("type") == "execute_step"]), 1)
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()
