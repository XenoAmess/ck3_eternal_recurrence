from __future__ import annotations

import copy
import importlib.util
import inspect
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_result_case_snapshot_contract import (
    CONNECTION_GENERATION,
    DATE_RAW,
    NATIVE_REVISION,
    OWNER_CHARACTER_ID,
    PLAYER_CHARACTER_ID,
    PUBLIC_REVISION,
    REQUEST_NONCE,
    SNAPSHOT_ID,
    _frame,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_result_case_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_result_case_snapshot_contract import (
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
    parse_query_zhongguo_result_case_snapshot_v1_step,
    query_zhongguo_result_case_snapshot_v1_step,
)


def _native_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 11,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_result_case_snapshot": copy.deepcopy(frame),
    }


def _semantic_snapshot(
    revision: int = NATIVE_REVISION,
    *,
    paused: bool = True,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.16",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": paused,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_received_result_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver() -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
            "pid": 6868,
            "session_generation": 0,
            "game_version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
            "expected_ck3_version": (
                ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION
            ),
            "executable_sha256": (
                ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "expected_ck3_sha256": (
                ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": (
                ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
            ),
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class ZhongguoResultCaseNativeDriverTests(unittest.TestCase):
    def test_request_has_only_fixed_owner_and_nonce_payload(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities[
                "zhongguo_result_case_snapshot_v1_query_supported"
            ]
        )
        self.assertNotIn(
            QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
            capabilities["action_steps"],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY],
                paused=True,
            ),
            [],
        )

        def answer(request: dict[str, object]) -> None:
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": _native_result(_frame()),
                }
            )

        endpoint.send_hook = answer
        dynamic_step = query_zhongguo_result_case_snapshot_v1_step(
            OWNER_CHARACTER_ID,
            REQUEST_NONCE,
        )
        result = driver.execute_step(
            dynamic_step,
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(result["status"], "available")
        sent = endpoint.frames[-1]
        self.assertEqual(
            set(sent),
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "owner_character_id",
                "request_nonce",
            },
        )
        self.assertEqual(
            sent["step"], QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP
        )
        self.assertEqual(sent["owner_character_id"], OWNER_CHARACTER_ID)
        self.assertEqual(sent["request_nonce"], REQUEST_NONCE)
        for forbidden in (
            "subject_character_id",
            "case_kind",
            "variable_name",
        ):
            self.assertNotIn(forbidden, sent)

    def test_malformed_dynamic_step_and_same_frame_drift_are_rejected(self) -> None:
        driver, _endpoint = _native_driver()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-result-case-snapshot-v1-200-zz",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def drift(request: dict[str, object]) -> None:
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": _native_result(_frame()),
                }
            )

        endpoint.send_hook = drift
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(
                query_zhongguo_result_case_snapshot_v1_step(
                    OWNER_CHARACTER_ID, REQUEST_NONCE
                ),
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        paused: bool = True,
        connection_drift: bool = False,
    ) -> None:
        self.advertise = advertise
        self.paused = paused
        self.connection_drift = connection_drift
        self.snapshot_calls = 0
        self.last_query = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        generation = (
            CONNECTION_GENERATION + 1
            if self.connection_drift and self.snapshot_calls > 1
            else CONNECTION_GENERATION
        )
        return {
            "format_version": 1,
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": self.paused,
            "episode_run_id": "received-result-fixture",
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": generation,
                "bridge_version": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "game_version": (
                        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_version": (
                        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_result_case_snapshot_v1_step(step)
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the result-case binding")
        self.last_query = query
        return {
            **_native_result(_frame()),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only result observation must not advance")


class ZhongguoResultCaseServiceTests(unittest.TestCase):
    def test_service_and_helper_signatures_expose_no_subject_or_variable(self) -> None:
        service_parameters = set(
            inspect.signature(
                GameplayBridgeService.query_zhongguo_result_case_snapshot_v1
            ).parameters
        )
        helper_parameters = set(
            inspect.signature(
                _ck3_query_zhongguo_result_case_snapshot_v1
            ).parameters
        )
        self.assertEqual(
            service_parameters,
            {
                "self",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
        )
        self.assertEqual(
            helper_parameters,
            {
                "service",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
        )

    def test_service_returns_received_self_binding(self) -> None:
        driver = _ServiceDriver()
        result = _ck3_query_zhongguo_result_case_snapshot_v1(
            GameplayBridgeService(driver),
            REQUEST_NONCE,
            PUBLIC_REVISION,
            OWNER_CHARACTER_ID,
        )
        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["binding"]["subject_character_id"], PLAYER_CHARACTER_ID
        )
        self.assertEqual(
            result["binding"]["owner_character_id"], OWNER_CHARACTER_ID
        )
        self.assertEqual(driver.last_query.owner_character_id, OWNER_CHARACTER_ID)

    def test_service_rejects_pause_revision_capability_and_connection_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_zhongguo_result_case_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER_CHARACTER_ID,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                _ServiceDriver(paused=False)
            ).query_zhongguo_result_case_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER_CHARACTER_ID,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_result_case_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION - 1,
                owner_character_id=OWNER_CHARACTER_ID,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(connection_drift=True)
            ).query_zhongguo_result_case_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER_CHARACTER_ID,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoResultCaseMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_surface_is_exact_and_rejects_subject_alias(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_query_zhongguo_result_case_snapshot_v1"]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {
                    "request_nonce",
                    "expected_revision",
                    "owner_character_id",
                },
            )
            result = await client.call_tool(
                "ck3_query_zhongguo_result_case_snapshot_v1",
                {
                    "request_nonce": REQUEST_NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER_CHARACTER_ID,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_zhongguo_result_case_snapshot_v1",
                {
                    "request_nonce": REQUEST_NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER_CHARACTER_ID,
                    "subject_character_id": PLAYER_CHARACTER_ID,
                },
            )

        self.assertFalse(result.is_error)
        self.assertTrue(rejected.is_error)
        self.assertEqual(
            result.structured_content["binding"]["subject_character_id"],
            PLAYER_CHARACTER_ID,
        )


if __name__ == "__main__":
    unittest.main()
