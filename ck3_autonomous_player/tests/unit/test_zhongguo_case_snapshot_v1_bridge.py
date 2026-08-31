from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_case_snapshot_contract import (
    CONNECTION_GENERATION,
    DATE_RAW,
    NATIVE_REVISION,
    OWNER_CHARACTER_ID,
    PLAYER_CHARACTER_ID,
    PUBLIC_REVISION,
    REQUEST_NONCE,
    SNAPSHOT_ID,
    SUBJECT_CHARACTER_ID,
    _frame,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_case_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_case_snapshot_contract import (
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
    ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
    parse_query_zhongguo_case_snapshot_v1_step,
    query_zhongguo_case_snapshot_v1_step,
)


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _frame_for(
    subject_character_id: int,
    *,
    owner_character_id: int = OWNER_CHARACTER_ID,
    requested_owner_character_id: int | None = None,
    exact_due_date: bool = True,
) -> dict[str, object]:
    frame = _frame(exact_due_date=exact_due_date)
    frame["subject_character_id"] = subject_character_id
    frame["requested_owner_character_id"] = requested_owner_character_id
    case = frame["case"]
    receipt = frame["receipt"]
    deadline = frame["deadline"]
    assert isinstance(case, dict)
    assert isinstance(receipt, dict)
    assert isinstance(deadline, dict)
    case["owner_character_id"] = _available(owner_character_id)
    case["subject_character_id"] = _available(subject_character_id)
    receipt["owner_character_id"] = _available(owner_character_id)
    receipt["subject_character_id"] = _available(subject_character_id)
    deadline["owner_character_id"] = _available(owner_character_id)
    deadline["target_character_id"] = _available(subject_character_id)
    return frame


def _native_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 9,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_case_snapshot": copy.deepcopy(frame),
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
        self.pipe_name = r"\\.\pipe\xar_zhongguo_case_v1_fixture"
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
            "bridge_version": ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
            "pid": 6767,
            "session_generation": 0,
            "game_version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
            "expected_ck3_version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
            "executable_sha256": (
                ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "expected_ck3_sha256": (
                ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class ZhongguoCaseSnapshotV1NativeDriverTests(unittest.TestCase):
    def test_query_is_typed_only_and_sends_fixed_allowlisted_fields(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["zhongguo_case_snapshot_v1_query_supported"]
        )
        self.assertNotIn(
            QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
            capabilities["action_steps"],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY],
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
                    "result": _native_result(
                        _frame_for(
                            SUBJECT_CHARACTER_ID,
                            exact_due_date=False,
                        )
                    ),
                }
            )

        endpoint.send_hook = answer
        dynamic_step = query_zhongguo_case_snapshot_v1_step(
            ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
            SUBJECT_CHARACTER_ID,
            None,
            REQUEST_NONCE,
        )
        snapshot = driver.take_snapshot()
        result = driver.execute_step(
            dynamic_step,
            expected_revision=int(snapshot["revision"]),
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["queried_connection_generation"], 1)
        sent = endpoint.frames[-1]
        self.assertEqual(sent["step"], QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP)
        self.assertEqual(sent["expected_revision"], NATIVE_REVISION)
        self.assertEqual(sent["case_kind"], ZHONGGUO_B1_PERFORMANCE_CASE_KIND)
        self.assertEqual(sent["subject_character_id"], SUBJECT_CHARACTER_ID)
        self.assertEqual(sent["owner_character_id"], 0)
        self.assertEqual(sent["request_nonce"], REQUEST_NONCE)
        self.assertNotIn("variable_name", sent)

    def test_driver_rejects_malformed_query_and_same_frame_drift(self) -> None:
        driver, _endpoint = _native_driver()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-case-snapshot-v1-b1-0-0-00",
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
                    "result": _native_result(
                        _frame_for(
                            SUBJECT_CHARACTER_ID,
                            exact_due_date=False,
                        )
                    ),
                }
            )

        endpoint.send_hook = drift
        step = query_zhongguo_case_snapshot_v1_step(
            ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
            SUBJECT_CHARACTER_ID,
            None,
            REQUEST_NONCE,
        )
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(
                step,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        paused: bool = True,
        connection_drift: bool = False,
        exact_due_date: bool = False,
        case_owner_character_id: int = OWNER_CHARACTER_ID,
    ) -> None:
        self.advertise = advertise
        self.paused = paused
        self.connection_drift = connection_drift
        self.exact_due_date = exact_due_date
        self.case_owner_character_id = case_owner_character_id
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
                [QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY]
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
            "episode_run_id": "native-12345-fixture",
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": generation,
                "bridge_version": ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "game_version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_case_snapshot_v1_step(step)
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the typed query binding")
        self.last_query = query
        frame = _frame_for(
            query.subject_character_id,
            owner_character_id=(
                query.owner_character_id or self.case_owner_character_id
            ),
            requested_owner_character_id=query.owner_character_id,
            exact_due_date=self.exact_due_date,
        )
        return {
            **_native_result(frame),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only case observation must not advance")


class ZhongguoCaseSnapshotV1ServiceTests(unittest.TestCase):
    def test_defaults_subject_and_returns_exact_source_binding(self) -> None:
        driver = _ServiceDriver()
        result = _ck3_query_zhongguo_case_snapshot_v1(
            GameplayBridgeService(driver),
            ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
            REQUEST_NONCE,
            PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["binding"]["subject_character_id"],
            PLAYER_CHARACTER_ID,
        )
        self.assertEqual(
            result["binding"]["owner_character_id"], OWNER_CHARACTER_ID
        )
        self.assertEqual(
            result["source"]["connection_generation"],
            CONNECTION_GENERATION,
        )
        self.assertEqual(result["source"]["backend_id"], "native-headless")
        self.assertEqual(result["build"]["version"], "1.19.0.6")
        self.assertEqual(driver.capabilities()["action_steps"], [])

    def test_explicit_subject_owner_and_semantic_red_are_preserved(self) -> None:
        driver = _ServiceDriver(exact_due_date=False)
        result = GameplayBridgeService(
            driver
        ).query_zhongguo_case_snapshot_v1(
            ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
            REQUEST_NONCE,
            expected_revision=PUBLIC_REVISION,
            subject_character_id=SUBJECT_CHARACTER_ID,
            owner_character_id=OWNER_CHARACTER_ID,
        )

        self.assertEqual(
            result["binding"]["subject_character_id"],
            SUBJECT_CHARACTER_ID,
        )
        self.assertEqual(
            result["requested_owner_character_id"], OWNER_CHARACTER_ID
        )
        self.assertEqual(
            result["deadline"]["due_date_raw"]["unavailable_reason"],
            "due_date_not_persisted_by_product",
        )
        self.assertFalse(result["readiness"]["deadline_due_date_ready"])
        self.assertFalse(result["readiness"]["ready"])

    def test_service_rejects_capability_pause_revision_and_connection_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_zhongguo_case_snapshot_v1(
                ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                _ServiceDriver(paused=False)
            ).query_zhongguo_case_snapshot_v1(
                ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_case_snapshot_v1(
                ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION - 1,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(connection_drift=True)
            ).query_zhongguo_case_snapshot_v1(
                ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
            )

    def test_service_rejects_an_available_ai_owned_case(self) -> None:
        with self.assertRaisesRegex(BridgeUnavailableError, "malformed"):
            GameplayBridgeService(
                _ServiceDriver(
                    case_owner_character_id=SUBJECT_CHARACTER_ID,
                )
            ).query_zhongguo_case_snapshot_v1(
                ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoCaseSnapshotV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_bounded_case_tool(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_query_zhongguo_case_snapshot_v1",
                {tool.name for tool in listed.tools},
            )
            result = await client.call_tool(
                "ck3_query_zhongguo_case_snapshot_v1",
                {
                    "case_kind": ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
                    "request_nonce": REQUEST_NONCE,
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(
            payload["binding"]["subject_character_id"],
            PLAYER_CHARACTER_ID,
        )
        self.assertEqual(
            payload["source"]["connection_generation"],
            CONNECTION_GENERATION,
        )


if __name__ == "__main__":
    unittest.main()
