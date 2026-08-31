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

from test_zhongguo_ai_owned_case_snapshot_contract import (  # noqa: E402
    CONNECTION_GENERATION,
    DATE_RAW,
    NATIVE_REVISION,
    NONCE,
    OWNER,
    PLAYER,
    PUBLIC_REVISION,
    SNAPSHOT_ID,
    SUBJECT,
    _frame,
    _unavailable_frame,
)
from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_zhongguo_ai_owned_case_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.zhongguo_ai_owned_case_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
    parse_query_zhongguo_ai_owned_case_snapshot_v1_step,
    query_zhongguo_ai_owned_case_snapshot_v1_step,
)


def _native_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 17,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_ai_owned_case_snapshot": copy.deepcopy(frame),
        "backend_id": "native-headless",
    }


def _semantic_snapshot(revision: int = NATIVE_REVISION) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.26",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": True,
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
        self.pipe_name = r"\\.\pipe\xar_zg361_ai_owned_case_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

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
            "bridge_version": (
                ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION
            ),
            "pid": 6969,
            "session_generation": 0,
            "game_version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
            "expected_ck3_version": (
                ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION
            ),
            "executable_sha256": (
                ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "expected_ck3_sha256": (
                ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": (
                ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
            ),
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class ZhongguoAiOwnedCaseNativeDriverTests(unittest.TestCase):
    def test_query_is_supported_pure_native_and_sends_only_selectors(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities[
                "zhongguo_ai_owned_case_snapshot_v1_query_supported"
            ]
        )
        self.assertEqual(
            _action_steps(
                [QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY],
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
        result = driver.execute_step(
            query_zhongguo_ai_owned_case_snapshot_v1_step(
                OWNER, SUBJECT, NONCE
            ),
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(result["status"], "available")
        request = endpoint.frames[-1]
        self.assertEqual(
            set(request),
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "owner_character_id",
                "subject_character_id",
                "request_nonce",
            },
        )
        self.assertNotIn("variable_name", request)
        self.assertNotIn("action", request)

    def test_malformed_query_fails_before_native_submission(self) -> None:
        driver, endpoint = _native_driver()
        before = len(endpoint.frames)
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-ai-owned-case-snapshot-v1-200-200-00",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(len(endpoint.frames), before)


class _ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        paused: bool = True,
        frame: dict[str, object] | None = None,
    ) -> None:
        self.advertise = advertise
        self.paused = paused
        self.frame = copy.deepcopy(frame if frame is not None else _frame())
        self.last_step: str | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": self.paused,
            "episode_run_id": "zg361-ai-owned-case-fixture",
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {
                "connection_generation": CONNECTION_GENERATION,
                "bridge_version": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "expected_ck3_version": (
                        ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_ai_owned_case_snapshot_v1_step(step)
        if (
            query is None
            or query.owner_character_id != OWNER
            or query.subject_character_id != SUBJECT
            or expected_revision != PUBLIC_REVISION
        ):
            raise AssertionError("service changed the AI-owned case binding")
        self.last_step = step
        return {
            **_native_result(self.frame),
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only AI-owned case query must not advance")


class ZhongguoAiOwnedCaseServiceTests(unittest.TestCase):
    def test_service_and_mcp_helper_expose_only_four_public_inputs(self) -> None:
        self.assertEqual(
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_ai_owned_case_snapshot_v1
                ).parameters
            ),
            {
                "self",
                "owner_character_id",
                "subject_character_id",
                "request_nonce",
                "expected_revision",
            },
        )
        self.assertEqual(
            set(
                inspect.signature(
                    _ck3_query_zhongguo_ai_owned_case_snapshot_v1
                ).parameters
            ),
            {
                "service",
                "owner_character_id",
                "subject_character_id",
                "request_nonce",
                "expected_revision",
            },
        )

    def test_optional_revision_and_unavailable_result_keep_request_binding(
        self,
    ) -> None:
        driver = _ServiceDriver(frame=_unavailable_frame())
        result = _ck3_query_zhongguo_ai_owned_case_snapshot_v1(
            GameplayBridgeService(driver),
            OWNER,
            SUBJECT,
            NONCE,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["binding"]["owner_character_id"], OWNER)
        self.assertEqual(result["binding"]["subject_character_id"], SUBJECT)
        self.assertEqual(result["binding"]["expected_revision"], PUBLIC_REVISION)
        self.assertIsNotNone(driver.last_step)

    def test_service_rejects_missing_capability_pause_and_revision_drift(
        self,
    ) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_zhongguo_ai_owned_case_snapshot_v1(
                OWNER, SUBJECT, NONCE, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                _ServiceDriver(paused=False)
            ).query_zhongguo_ai_owned_case_snapshot_v1(
                OWNER, SUBJECT, NONCE, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_ai_owned_case_snapshot_v1(
                OWNER, SUBJECT, NONCE, expected_revision=PUBLIC_REVISION + 1
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoAiOwnedCaseMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_signature_optional_revision_and_scope_rejection(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_query_zhongguo_ai_owned_case_snapshot_v1"]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {
                    "owner_character_id",
                    "subject_character_id",
                    "request_nonce",
                    "expected_revision",
                },
            )
            self.assertNotIn(
                "expected_revision", set(tool.input_schema.get("required", []))
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_ai_owned_case_snapshot_v1",
                {
                    "owner_character_id": OWNER,
                    "subject_character_id": SUBJECT,
                    "request_nonce": NONCE,
                },
            )
            rejected = []
            for unexpected in (
                {"variable_name": "zg361_b1_case_owner"},
                {"case_kind": "zhongguo.b1.performance"},
                {"action": "publish"},
            ):
                rejected.append(
                    await client.call_tool(
                        "ck3_query_zhongguo_ai_owned_case_snapshot_v1",
                        {
                            "owner_character_id": OWNER,
                            "subject_character_id": SUBJECT,
                            "request_nonce": NONCE,
                            **unexpected,
                        },
                    )
                )

        self.assertFalse(accepted.is_error)
        self.assertEqual(
            accepted.structured_content["binding"]["owner_character_id"],
            OWNER,
        )
        self.assertTrue(all(result.is_error for result in rejected))


if __name__ == "__main__":
    unittest.main()
