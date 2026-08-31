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

from test_zhongguo_workforce_normal_exit_snapshot_contract import (  # noqa: E402
    CONNECTION_GENERATION,
    DATE_RAW,
    NATIVE_REVISION,
    NONCE,
    OWNER,
    PLAYER,
    PUBLIC_REVISION,
    SNAPSHOT_ID,
    frame,
    unavailable_frame,
)
from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_zhongguo_workforce_normal_exit_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.zhongguo_workforce_normal_exit_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
    parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step,
    query_zhongguo_workforce_normal_exit_snapshot_v1_step,
)


def native_result(native_frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": native_frame["status"],
        "query_sequence": 21,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_workforce_normal_exit_snapshot": copy.deepcopy(native_frame),
    }


def semantic_snapshot(
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
            "played_character": {"character_id": PLAYER, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_workforce_normal_exit_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, published: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("endpoint was not started")
        self.on_frame(published)

    def send(self, sent: dict[str, object]) -> None:
        self.frames.append(sent)
        if self.send_hook is not None:
            self.send_hook(sent)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def native_driver() -> tuple[NativeHeadlessGameplayDriver, FakeEndpoint]:
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
            "pid": 7075,
            "session_generation": 0,
            "game_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
            "expected_ck3_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
            "executable_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
            "expected_ck3_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
            "game_adapter_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(semantic_snapshot())
    return driver, endpoint


class WorkforceNormalExitNativeDriverTests(unittest.TestCase):
    def test_dynamic_query_is_not_an_action_and_request_is_exact(self) -> None:
        driver, endpoint = native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities[
                "zhongguo_workforce_normal_exit_snapshot_v1_query_supported"
            ]
        )
        self.assertNotIn(
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
            capabilities["action_steps"],
        )
        self.assertEqual(
            [],
            _action_steps(
                [QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY],
                paused=True,
            ),
        )

        def answer(request: dict[str, object]) -> None:
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": native_result(frame("sealed")),
                }
            )

        endpoint.send_hook = answer
        dynamic_step = query_zhongguo_workforce_normal_exit_snapshot_v1_step(
            OWNER, NONCE
        )
        result = driver.execute_step(
            dynamic_step,
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual("sealed", result["zhongguo_workforce_normal_exit_snapshot"]["lifecycle"])
        sent = endpoint.frames[-1]
        self.assertEqual(
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "owner_character_id",
                "request_nonce",
            },
            set(sent),
        )
        self.assertEqual(
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
            sent["step"],
        )
        self.assertEqual(OWNER, sent["owner_character_id"])
        self.assertEqual(NONCE, sent["request_nonce"])
        for forbidden in ("subject_character_id", "case_kind", "stage", "variable_name"):
            self.assertNotIn(forbidden, sent)

    def test_malformed_dynamic_step_and_same_frame_drift_fail_closed(self) -> None:
        driver, _endpoint = native_driver()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-workforce-normal-exit-snapshot-v1-200-zz",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = native_driver()

        def drift(request: dict[str, object]) -> None:
            endpoint.publish(semantic_snapshot(NATIVE_REVISION + 1))
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": native_result(frame("sealed")),
                }
            )

        endpoint.send_hook = drift
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.execute_step(
                query_zhongguo_workforce_normal_exit_snapshot_v1_step(
                    OWNER, NONCE
                ),
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        paused: bool = True,
        connection_drift: bool = False,
        native_frame: dict[str, object] | None = None,
    ) -> None:
        self.advertise = advertise
        self.paused = paused
        self.connection_drift = connection_drift
        self.native_frame = copy.deepcopy(
            native_frame if native_frame is not None else frame("sealed")
        )
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
                [QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY]
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
            "episode_run_id": "workforce-normal-exit-fixture",
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {
                "connection_generation": generation,
                "bridge_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
                "hello": {
                    "bridge_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
                    "game_adapter_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
                    "game_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
                    "expected_ck3_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
                    "expected_ck3_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        parsed = parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(step)
        if parsed is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the normal-exit query binding")
        self.last_query = parsed
        return {
            **native_result(self.native_frame),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("normal-exit observation must not advance time")


class WorkforceNormalExitServiceTests(unittest.TestCase):
    def test_service_and_helper_expose_only_owner_nonce_and_revision(self) -> None:
        self.assertEqual(
            {
                "self",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_workforce_normal_exit_snapshot_v1
                ).parameters
            ),
        )
        self.assertEqual(
            {"service", "request_nonce", "expected_revision", "owner_character_id"},
            set(
                inspect.signature(
                    _ck3_query_zhongguo_workforce_normal_exit_snapshot_v1
                ).parameters
            ),
        )

    def test_service_returns_exact_received_self_and_bridge_source_binding(self) -> None:
        driver = ServiceDriver()
        result = _ck3_query_zhongguo_workforce_normal_exit_snapshot_v1(
            GameplayBridgeService(driver),
            NONCE,
            PUBLIC_REVISION,
            OWNER,
        )
        self.assertEqual("sealed", result["lifecycle"])
        self.assertEqual(PLAYER, result["binding"]["subject_character_id"])
        self.assertEqual(OWNER, result["binding"]["owner_character_id"])
        self.assertEqual("native-headless", result["bridge_source"]["backend_id"])
        self.assertIsNot(result["source"], result["bridge_source"])
        self.assertEqual(OWNER, driver.last_query.owner_character_id)

        unavailable_driver = ServiceDriver(native_frame=unavailable_frame())
        unavailable_result = GameplayBridgeService(
            unavailable_driver
        ).query_zhongguo_workforce_normal_exit_snapshot_v1(
            NONCE,
            expected_revision=PUBLIC_REVISION,
            owner_character_id=OWNER,
        )
        self.assertEqual("unavailable", unavailable_result["status"])
        self.assertEqual(OWNER, unavailable_result["binding"]["owner_character_id"])

    def test_service_rejects_pause_revision_capability_and_connection_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                ServiceDriver(advertise=False)
            ).query_zhongguo_workforce_normal_exit_snapshot_v1(
                NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                ServiceDriver(paused=False)
            ).query_zhongguo_workforce_normal_exit_snapshot_v1(
                NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                ServiceDriver()
            ).query_zhongguo_workforce_normal_exit_snapshot_v1(
                NONCE,
                expected_revision=PUBLIC_REVISION - 1,
                owner_character_id=OWNER,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                ServiceDriver(connection_drift=True)
            ).query_zhongguo_workforce_normal_exit_snapshot_v1(
                NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class WorkforceNormalExitMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_surface_is_exact_and_rejects_subject_alias(self) -> None:
        from mcp import Client

        async with Client(create_server(ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools[
                "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1"
            ]
            self.assertEqual(
                {"request_nonce", "expected_revision", "owner_character_id"},
                set(tool.input_schema["properties"]),
            )
            result = await client.call_tool(
                "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER,
                    "subject_character_id": PLAYER,
                },
            )

        self.assertFalse(result.is_error)
        self.assertTrue(rejected.is_error)
        self.assertEqual(
            PLAYER,
            result.structured_content["binding"]["subject_character_id"],
        )


if __name__ == "__main__":
    unittest.main()
