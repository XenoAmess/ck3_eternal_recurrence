from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_compensation_af5_snapshot_contract import (
    QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_CAPABILITY as CAPABILITY,
    QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_STEP as STEP,
    ZhongguoCompensationAf5SnapshotQueryV1,
    normalize_native_zhongguo_compensation_af5_snapshot_v1,
    parse_query_zhongguo_compensation_af5_snapshot_v1_step,
    query_zhongguo_compensation_af5_snapshot_v1_step,
)


def _fixtures() -> dict[str, object]:
    return json.loads((PROJECT_ROOT / "tests/fixtures/zhongguo_compensation_af5_snapshot_v1.json").read_text())


def _snapshot(revision: int = 51) -> dict[str, object]:
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": f"native:{revision}", "revision": revision,
        "state": {
            "phase": "map_hud", "date": "1066.10.26", "date_raw": 800,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": 147, "alive": True},
            "one_life_settlement": None, "active_wars": [], "player_armies": [],
        },
    }


class _Endpoint:
    pipe_name = r"\\.\pipe\xar_af5_snapshot_v1_fixture"

    def __init__(self) -> None:
        self.frames = []
        self.frame = _fixtures()["frames"]["pre_action"]
        self.drift = False

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame) -> None:
        self.on_frame(frame)

    def send(self, request) -> None:
        if request.get("type") != "execute_step":
            return
        self.frames.append(request)
        if self.drift:
            self.publish(_snapshot(52))
        self.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": {
                "step": STEP, "accepted": True, "status": self.frame["status"],
                "query_sequence": len(self.frames), "snapshot_revision": 51,
                "zhongguo_compensation_af5_snapshot": deepcopy(self.frame),
            },
        })

    def close(self) -> None:
        pass

    def transport_error(self):
        return None


def _driver(*, supported: bool = True):
    endpoint = _Endpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1
    )
    endpoint.publish({
        "type": "hello", "protocol_version": 1, "bridge_version": "af5-fixture-v1",
        "pid": 6868, "session_generation": 0,
        "capabilities": ["game.state.snapshot"] + ([CAPABILITY] if supported else []),
    })
    endpoint.publish(_snapshot())
    return driver, endpoint


class Af5SnapshotContractTests(unittest.TestCase):
    def test_step_round_trip(self) -> None:
        step = query_zhongguo_compensation_af5_snapshot_v1_step(147, "af5.14")
        self.assertEqual(
            parse_query_zhongguo_compensation_af5_snapshot_v1_step(step),
            ZhongguoCompensationAf5SnapshotQueryV1(147, "af5.14"),
        )

    def test_pre_action_and_both_terminal_frames_remain_observable(self) -> None:
        schema = json.loads((PROJECT_ROOT / "schemas/zhongguo-compensation-af5-snapshot-v1.schema.json").read_text())
        validator = Draft202012Validator(schema)
        for name, frame in _fixtures()["frames"].items():
            with self.subTest(frame=name):
                normalized = normalize_native_zhongguo_compensation_af5_snapshot_v1(
                    frame,
                    expected_query=ZhongguoCompensationAf5SnapshotQueryV1(147, "af5.14"),
                    expected_snapshot_revision=51, expected_date_raw=800,
                    expected_player_character_id=147,
                )
                validator.validate(normalized)
                self.assertTrue(normalized["readiness"]["ready"])
                self.assertEqual(normalized["terminal"], name != "pre_action")

    def test_service_reads_through_native_transport_without_an_active_event(self) -> None:
        driver, endpoint = _driver()
        self.addCleanup(driver.close)
        service = GameplayBridgeService(driver)
        self.assertTrue(driver.capabilities()["zhongguo_compensation_af5_snapshot_v1_query_supported"])
        self.assertEqual(_action_steps([CAPABILITY], paused=True), [])
        self.assertIsNone(service.snapshot()["active_event"])
        for name, frame in _fixtures()["frames"].items():
            with self.subTest(frame=name):
                endpoint.frame = frame
                revision = service.snapshot()["revision"]
                result = service.query_zhongguo_compensation_af5_snapshot_v1(
                    "af5.14", expected_revision=revision
                )
                schema = json.loads((PROJECT_ROOT / "schemas/zhongguo-compensation-af5-snapshot-v1.schema.json").read_text())
                Draft202012Validator(schema).validate(result)
                self.assertEqual(result["terminal"], name != "pre_action")
                self.assertTrue(result["readiness"]["ready"])
                self.assertEqual(result["binding"]["subject_character_id"], 361)
                self.assertEqual(result["binding"]["native_revision"], 51)
                request = endpoint.frames[-1]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], 51)
                self.assertEqual(request["owner_character_id"], 147)
                self.assertEqual(request["request_nonce"], "af5.14")
                self.assertEqual(set(request), {
                    "type", "protocol_version", "request_id", "step",
                    "expected_revision", "owner_character_id", "request_nonce",
                })

    def test_service_requires_supported_same_frame_query(self) -> None:
        driver, endpoint = _driver(supported=False)
        self.addCleanup(driver.close)
        service = GameplayBridgeService(driver)
        with self.assertRaises(UnsupportedStepError):
            service.query_zhongguo_compensation_af5_snapshot_v1(
                "af5.14", expected_revision=service.snapshot()["revision"]
            )
        self.assertEqual(endpoint.frames, [])
        driver, endpoint = _driver()
        self.addCleanup(driver.close)
        endpoint.drift = True
        service = GameplayBridgeService(driver)
        with self.assertRaises(BridgeUnavailableError):
            service.query_zhongguo_compensation_af5_snapshot_v1(
                "af5.14", expected_revision=service.snapshot()["revision"]
            )

    def test_hybrid_advertises_the_capability_only_from_native(self) -> None:
        class Capabilities:
            def __init__(self, supported):
                self.supported = supported

            def capabilities(self):
                return {"action_steps": [], "bridge_capabilities": [CAPABILITY] if self.supported else []}

        driver = object.__new__(ConfiguredHybridFallbackDriver)
        driver.native = Capabilities(False)
        driver._delegate = Capabilities(True)
        self.assertNotIn(CAPABILITY, driver.capabilities()["bridge_capabilities"])
        driver.native = Capabilities(True)
        self.assertIn(CAPABILITY, driver.capabilities()["bridge_capabilities"])


@unittest.skipUnless(importlib.util.find_spec("mcp") is not None, "optional MCP SDK not installed")
class Af5SnapshotMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_query_reaches_native_service(self) -> None:
        from mcp import Client

        driver, endpoint = _driver()
        self.addCleanup(driver.close)
        endpoint.frame = _fixtures()["frames"]["closed_portfolio_terminal"]
        async with Client(create_server(driver)) as client:
            listed = await client.list_tools()
            tool = next(t for t in listed.tools if t.name == "ck3_query_zhongguo_compensation_af5_snapshot_v1")
            self.assertEqual(set(tool.input_schema["properties"]), {"request_nonce", "expected_revision"})
            result = await client.call_tool(tool.name, {
                "request_nonce": "af5.14", "expected_revision": driver.take_snapshot()["revision"],
            })
        self.assertFalse(result.is_error)
        self.assertEqual(len(endpoint.frames), 1)
        self.assertTrue(result.structured_content["terminal"])


if __name__ == "__main__":
    unittest.main()
