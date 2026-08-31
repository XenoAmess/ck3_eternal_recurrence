from __future__ import annotations

import copy
import importlib.util
import inspect
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_workforce_collective_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_workforce_collective_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP,
    ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION,
    _CASE_SPEC,
    _CHARTER_SPEC,
    _COHORT_SPEC,
    _COLLECTIVE_SPEC,
    _DEBT_SPEC,
    _HISTORY_SLOT_SPEC,
    _READINESS_KEYS,
    _RECEIPT_SPEC,
    parse_query_zhongguo_workforce_collective_snapshot_v1_step,
    query_zhongguo_workforce_collective_snapshot_v1_step,
)


NATIVE_REVISION = 91
PUBLIC_REVISION = 12
CONNECTION_GENERATION = 8
DATE_RAW = 730_121
PLAYER_CHARACTER_ID = 100
OWNER_CHARACTER_ID = 200
SNAPSHOT_ID = "native-headless:workforce-collective:91"
REQUEST_NONCE = "workforce:91"


def _unavailable() -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": "case_unavailable",
    }


def _group(spec: dict[str, str]) -> dict[str, object]:
    return {key: _unavailable() for key in spec}


def _frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "case_kind": ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1,
        "request_nonce": REQUEST_NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER_CHARACTER_ID,
        "subject_character_id": PLAYER_CHARACTER_ID,
        "requested_owner_character_id": OWNER_CHARACTER_ID,
        "al_case": _group(_CASE_SPEC),
        "m360_receipt": _group(_RECEIPT_SPEC),
        "collective": {
            "phase": "unavailable",
            **_group(_COLLECTIVE_SPEC),
        },
        "cohorts": [_group(_COHORT_SPEC) for _ in range(3)],
        "route_c_debt": _group(_DEBT_SPEC),
        "history": {
            "status": "unavailable",
            "count": _unavailable(),
            "effective_count": -1,
            "slots": [_group(_HISTORY_SLOT_SPEC) for _ in range(3)],
        },
        "charter_gate": {
            "status": "unavailable",
            **_group(_CHARTER_SPEC),
        },
        "readiness": {key: False for key in _READINESS_KEYS},
        "unavailable_reason": "case_not_found",
        "provenance": {
            "game_version": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION
            ),
            "executable_sha256": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "backend_id": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID
            ),
            "consumer_id": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID
            ),
            "allowlist_id": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID
            ),
            "variable_context_for_scope_rva": "0x3329A40",
            "variable_identifier_table_rva": "0x3B971A0",
            "variable_identifier_lookup_rva": "0x3B97020",
            "variable_identifier_name_rva": "0x3B97090",
            "character_storage_slot_rva": "0x570C130",
            "subject_allowlist_count": 144,
            "owner_allowlist_count": 31,
            "query_scope": (
                "paused_received_self_al_case_plus_owner_rolling_three_cycle"
            ),
        },
    }


def _native_result() -> dict[str, object]:
    frame = _frame()
    return {
        "step": QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 13,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_workforce_collective_snapshot": copy.deepcopy(frame),
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
        self.pipe_name = r"\\.\pipe\xar_workforce_collective_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

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
            "bridge_version": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION
            ),
            "pid": 6868,
            "session_generation": 0,
            "game_version": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION
            ),
            "expected_ck3_version": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION
            ),
            "executable_sha256": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "expected_ck3_sha256": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": (
                ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_ADAPTER_ID
            ),
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class WorkforceCollectiveNativeDriverTests(unittest.TestCase):
    def test_request_is_read_only_received_self_and_revision_bound(self) -> None:
        driver, endpoint = _native_driver()
        self.assertTrue(
            driver.capabilities()[
                "zhongguo_workforce_collective_snapshot_v1_query_supported"
            ]
        )
        self.assertEqual(
            _action_steps(
                [
                    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                ],
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
                    "result": _native_result(),
                }
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            query_zhongguo_workforce_collective_snapshot_v1_step(
                OWNER_CHARACTER_ID, REQUEST_NONCE
            ),
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(result["status"], "unavailable")
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
                "request_nonce",
            },
        )
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-workforce-collective-snapshot-v1-200-zz",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(self, *, advertise: bool = True) -> None:
        self.advertise = advertise
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
                [
                    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
                ]
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
            "paused": True,
            "episode_run_id": "workforce-collective-fixture",
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": CONNECTION_GENERATION,
                "bridge_version": (
                    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "expected_ck3_version": (
                        ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_workforce_collective_snapshot_v1_step(
            step
        )
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the Workforce binding")
        self.last_step = step
        return {
            **_native_result(),
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only Workforce observation must not advance")


class WorkforceCollectiveServiceTests(unittest.TestCase):
    def test_service_and_helper_expose_exact_three_public_inputs(self) -> None:
        self.assertEqual(
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_workforce_collective_snapshot_v1
                ).parameters
            ),
            {
                "self",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
        )
        self.assertEqual(
            set(
                inspect.signature(
                    _ck3_query_zhongguo_workforce_collective_snapshot_v1
                ).parameters
            ),
            {
                "service",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
        )

    def test_service_returns_unavailable_binding_without_fabricated_owner(
        self,
    ) -> None:
        driver = _ServiceDriver()
        result = _ck3_query_zhongguo_workforce_collective_snapshot_v1(
            GameplayBridgeService(driver),
            REQUEST_NONCE,
            PUBLIC_REVISION,
            OWNER_CHARACTER_ID,
        )
        self.assertEqual(
            result["binding"]["subject_character_id"], PLAYER_CHARACTER_ID
        )
        self.assertIsNone(result["binding"]["owner_character_id"])
        self.assertIsNotNone(driver.last_step)
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_zhongguo_workforce_collective_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION,
                owner_character_id=OWNER_CHARACTER_ID,
            )
        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_workforce_collective_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION + 1,
                owner_character_id=OWNER_CHARACTER_ID,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class WorkforceCollectiveMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_rejects_subject_variable_and_action_inputs(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools[
                "ck3_query_zhongguo_workforce_collective_snapshot_v1"
            ]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {
                    "request_nonce",
                    "expected_revision",
                    "owner_character_id",
                },
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_workforce_collective_snapshot_v1",
                {
                    "request_nonce": REQUEST_NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER_CHARACTER_ID,
                },
            )
            rejected = []
            for unexpected in (
                {"variable_name": "zg361_workforce_collective_route"},
                {"subject_character_id": PLAYER_CHARACTER_ID},
                {"action": "consume"},
            ):
                rejected.append(
                    await client.call_tool(
                        "ck3_query_zhongguo_workforce_collective_snapshot_v1",
                        {
                            "request_nonce": REQUEST_NONCE,
                            "expected_revision": PUBLIC_REVISION,
                            "owner_character_id": OWNER_CHARACTER_ID,
                            **unexpected,
                        },
                    )
                )
        self.assertFalse(accepted.is_error)
        self.assertTrue(all(result.is_error for result in rejected))


if __name__ == "__main__":
    unittest.main()
