from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_scoreboard_state_contract import (  # noqa: E402
    DATE_RAW,
    NONCE,
    PLAYER,
    REVISION as NATIVE_REVISION,
    native_frame,
)
from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_zhongguo_scoreboard_state_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.zhongguo_scoreboard_state_contract import (  # noqa: E402
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
    ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION,
    ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID,
    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
    parse_query_zhongguo_scoreboard_state_v1_step,
    query_zhongguo_scoreboard_state_v1_step,
)


PUBLIC_REVISION = 19
CONNECTION_GENERATION = 3
SNAPSHOT_ID = "native-headless:scoreboard:77"


def _native_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 9,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_scoreboard_state": copy.deepcopy(frame),
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
            "played_character": {"character_id": PLAYER, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_zhongguo_scoreboard_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("endpoint was not started")
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
            "bridge_version": ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION,
            "pid": 6767,
            "session_generation": 0,
            "game_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
            "expected_ck3_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
            "executable_sha256": ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
            "expected_ck3_sha256": (
                ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID,
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class ZhongguoScoreboardStateV1NativeDriverTests(unittest.TestCase):
    def test_query_sends_only_fixed_read_request_and_never_becomes_action(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["zhongguo_scoreboard_state_v1_query_supported"]
        )
        self.assertNotIn(
            QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
            capabilities["action_steps"],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY], paused=True
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
                    "result": _native_result(native_frame()),
                }
            )

        endpoint.send_hook = answer
        snapshot = driver.take_snapshot()
        result = driver.execute_step(
            query_zhongguo_scoreboard_state_v1_step(NONCE),
            expected_revision=int(snapshot["revision"]),
        )

        self.assertEqual(result["status"], "available")
        self.assertFalse(
            result["zhongguo_scoreboard_state"]["readiness"][
                "production_live_ready"
            ]
        )
        sent = endpoint.frames[-1]
        self.assertEqual(
            set(sent),
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "request_nonce",
            },
        )
        self.assertEqual(sent["request_nonce"], NONCE)
        self.assertNotIn("widget_name", sent)
        self.assertNotIn("action", sent)

    def test_malformed_query_and_same_frame_drift_fail_closed(self) -> None:
        driver, _endpoint = _native_driver()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                f"{QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP}-bad/nonce",
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
                    "result": _native_result(native_frame()),
                }
            )

        endpoint.send_hook = drift
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(
                query_zhongguo_scoreboard_state_v1_step(NONCE),
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

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY]
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
            "episode_run_id": "native-scoreboard-fixture",
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {
                "connection_generation": generation,
                "bridge_version": ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION,
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID
                    ),
                    "game_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_scoreboard_state_v1_step(step)
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the typed scoreboard binding")
        return {
            **_native_result(native_frame()),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only scoreboard observation must not advance")


class ZhongguoScoreboardStateV1ServiceTests(unittest.TestCase):
    def test_service_and_helper_return_exact_static_read_only_binding(self) -> None:
        result = _ck3_query_zhongguo_scoreboard_state_v1(
            GameplayBridgeService(_ServiceDriver()),
            NONCE,
            PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["binding"]["player_character_id"], PLAYER)
        self.assertEqual(
            result["source"]["connection_generation"], CONNECTION_GENERATION
        )
        self.assertFalse(result["readiness"]["full_widget_gate_ready"])
        self.assertFalse(result["readiness"]["production_live_ready"])
        self.assertEqual(len(result["widgets"]), 15)
        self.assertEqual(
            result["widgets"][5]["stable_identity"],
            "zg361_scoreboard_entry_received",
        )
        self.assertEqual(
            result["widgets"][5]["vtable_pointer"]["value"],
            "0x14506020",
        )
        self.assertEqual(
            result["actions"]["activate"]["unavailable_reason"],
            "read_only_provider_action_not_exposed",
        )

    def test_service_rejects_capability_pause_revision_and_connection_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_zhongguo_scoreboard_state_v1(
                NONCE, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                _ServiceDriver(paused=False)
            ).query_zhongguo_scoreboard_state_v1(
                NONCE, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_scoreboard_state_v1(
                NONCE, expected_revision=PUBLIC_REVISION - 1
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(connection_drift=True)
            ).query_zhongguo_scoreboard_state_v1(
                NONCE, expected_revision=PUBLIC_REVISION
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoScoreboardStateV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_calls_and_rejects_scope_expansion(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_query_zhongguo_scoreboard_state_v1",
                {tool.name for tool in listed.tools},
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_scoreboard_state_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                },
            )
            rejected = []
            for unexpected in (
                {"widget_name": "zg361_scoreboard_window"},
                {"action": "activate"},
                {"subject_character_id": PLAYER},
            ):
                rejected.append(
                    await client.call_tool(
                        "ck3_query_zhongguo_scoreboard_state_v1",
                        {
                            "request_nonce": NONCE,
                            "expected_revision": PUBLIC_REVISION,
                            **unexpected,
                        },
                    )
                )

        self.assertFalse(accepted.is_error)
        self.assertFalse(
            accepted.structured_content["readiness"]["production_live_ready"]
        )
        self.assertEqual(
            accepted.structured_content["widgets"][13]["runtime_name"],
            "zg361_scoreboard_modal_backdrop_close",
        )
        self.assertEqual(
            accepted.structured_content["widgets"][14]["vtable_pointer"][
                "value"
            ],
            "0x14506020",
        )
        self.assertTrue(all(result.is_error for result in rejected))


if __name__ == "__main__":
    unittest.main()
