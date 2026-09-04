from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_manager_subordinate_selector_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_manager_subordinate_selector_contract import (
    QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY,
    QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP,
    ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_KIND_V1,
    ZhongguoManagerSubordinateSelectorQueryV1,
    normalize_native_zhongguo_manager_subordinate_selector_v1,
    parse_query_zhongguo_manager_subordinate_selector_v1_step,
    query_zhongguo_manager_subordinate_selector_v1_step,
)


NATIVE_REVISION = 81
PUBLIC_REVISION = 7
DATE_RAW = 730_101
PLAYER = 100
MANAGER = 201
SUBORDINATE = 301
SNAPSHOT_ID = "native-headless:b3-selector:81"
NONCE = "b3.selector.fixture"


def _query() -> ZhongguoManagerSubordinateSelectorQueryV1:
    return ZhongguoManagerSubordinateSelectorQueryV1(NONCE)


def _frame(*, status: str = "available") -> dict[str, object]:
    available = status == "available"
    return {
        "schema_version": 1,
        "status": status,
        "selector_kind": ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_KIND_V1,
        "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "provider_observed": available,
        "selection": (
            {
                "manager_character_id": MANAGER,
                "subordinate_character_id": SUBORDINATE,
                "manager_contract_id": 150_994_946,
                "subordinate_contract_id": 150_994_949,
                "manager_primary_title_id": 50_331_651,
                "manager_primary_title_tier_raw": 3,
                "manager_primary_title_tier_key": "duchy",
                "manager_government_key": "celestial_government",
            }
            if available
            else None
        ),
        "readiness": {
            "exact_build_ready": True,
            "player_binding_ready": True,
            "relationship_enumeration_ready": True,
            "manager_eligibility_ready": True,
            "direct_subordinate_ready": available,
            "same_frame_ready": True,
            "ready": available,
        },
        "unavailable_reason": (
            None if available else "no_bounded_ai_direct_manager"
        ),
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": (
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
            "subject_contract_storage_slot_rva": "0x570CCA0",
            "subject_contract_fallback_slot_rva": "0x570CC50",
            "immediate_liege_rva": "0x2613480",
            "primary_title_rva": "0x25F3350",
            "effective_government_rva": "0x26165B0",
            "is_human_player_rva": "0x28BCEB0",
        },
    }


class SelectorDriver:
    def __init__(self) -> None:
        self.last_step: str | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY
            ]
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": True,
            "map_ready": True,
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "episode_run_id": "b3-selector-fixture",
            "played_character": {"character_id": PLAYER},
            "diagnostics": {"connection_generation": 4},
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the public revision")
        self.last_step = step
        return {
            "step": QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP,
            "accepted": True,
            "status": "available",
            "query_sequence": 1,
            "snapshot_revision": NATIVE_REVISION,
            "zhongguo_manager_subordinate_selector": _frame(),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
        }


class ZhongguoManagerSubordinateSelectorTests(unittest.TestCase):
    def test_nonce_builder_is_typed_and_rejects_variable_payloads(self) -> None:
        step = query_zhongguo_manager_subordinate_selector_v1_step(NONCE)
        self.assertEqual(
            parse_query_zhongguo_manager_subordinate_selector_v1_step(step),
            _query(),
        )
        self.assertIsNone(
            parse_query_zhongguo_manager_subordinate_selector_v1_step(
                step + "-zg361_mg_manager_score"
            )
        )

    def test_available_and_typed_unavailable_frames_are_distinct(self) -> None:
        available = normalize_native_zhongguo_manager_subordinate_selector_v1(
            _frame(),
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        unavailable = normalize_native_zhongguo_manager_subordinate_selector_v1(
            _frame(status="unavailable"),
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertTrue(available["provider_observed"])
        self.assertEqual(
            available["selection"]["manager_character_id"], MANAGER
        )
        self.assertFalse(unavailable["provider_observed"])
        self.assertIsNone(unavailable["selection"])
        self.assertEqual(
            unavailable["unavailable_reason"], "no_bounded_ai_direct_manager"
        )

    def test_service_and_mcp_helper_expose_no_caller_character_ids(self) -> None:
        self.assertEqual(
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_manager_subordinate_selector_v1
                ).parameters
            ),
            {"self", "request_nonce", "expected_revision"},
        )
        self.assertEqual(
            set(
                inspect.signature(
                    _ck3_query_zhongguo_manager_subordinate_selector_v1
                ).parameters
            ),
            {"service", "request_nonce", "expected_revision"},
        )
        driver = SelectorDriver()
        result = _ck3_query_zhongguo_manager_subordinate_selector_v1(
            GameplayBridgeService(driver), NONCE, PUBLIC_REVISION
        )
        self.assertEqual(result["manager_character_id"], MANAGER)
        self.assertEqual(result["subordinate_character_id"], SUBORDINATE)
        self.assertTrue(result["provider_observed"])
        self.assertEqual(
            parse_query_zhongguo_manager_subordinate_selector_v1_step(
                driver.last_step
            ),
            _query(),
        )

    def test_native_driver_sends_only_the_nonce(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        snapshot = SelectorDriver().take_snapshot()
        driver.take_snapshot = lambda: copy.deepcopy(snapshot)
        calls: list[dict[str, object]] = []

        def execute(
            step: str,
            *,
            expected_revision: int,
            required_capability: str,
            request_fields: dict[str, object],
        ) -> dict[str, object]:
            calls.append(dict(request_fields))
            return {
                "step": QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP,
                "accepted": True,
                "status": "available",
                "query_sequence": 1,
                "snapshot_revision": NATIVE_REVISION,
                "zhongguo_manager_subordinate_selector": _frame(),
                "backend_id": "native-headless",
            }

        driver._execute_primitive_step = execute
        result = driver._execute_zhongguo_manager_subordinate_selector_v1_query(
            _query(), expected_revision=PUBLIC_REVISION
        )
        self.assertEqual(calls, [{"request_nonce": NONCE}])
        self.assertEqual(result["manager_character_id"], MANAGER)

    def test_exact_build_source_contract_and_transport_are_frozen(self) -> None:
        bridge_root = PROJECT_ROOT / "native_bridge"
        abi = json.loads(
            (bridge_root / "research/zhongguo_manager_subordinate_selector_v1_abi.json")
            .read_text(encoding="utf-8")
        )
        source_contract = json.loads(
            (
                bridge_root
                / "research/fixtures/zhongguo_manager_subordinate_selector_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        expected_status = (
            "production_transport_integrated_static_and_fixture_ready_not_live"
        )
        self.assertEqual(abi["status"], expected_status)
        self.assertEqual(source_contract["readiness"], expected_status)
        self.assertEqual(
            abi["public_request_fields"],
            ["request_nonce", "expected_revision"],
        )
        self.assertIsNone(abi["integration"]["live_artifact"])
        self.assertEqual(
            abi["integration"]["formal_phase2_runner_provider"],
            "wired_static_not_live",
        )
        bridge = (bridge_root / "src/bridge.cpp").read_text(encoding="utf-8")
        service = (
            PROJECT_ROOT / "src/xar_autoplayer/bridge/service.py"
        ).read_text(encoding="utf-8")
        runner = (
            PROJECT_ROOT.parent / "tools/run_zhongguo_acceptance.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "BindZhongguoManagerSubordinateSelectorNativeEnvironmentV1",
            bridge,
        )
        self.assertIn(
            "def query_zhongguo_manager_subordinate_selector_v1(", service
        )
        self.assertIn("query_phase2_b3_manager_subordinate_selector", runner)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoManagerSubordinateSelectorMcpTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_mcp_schema_has_no_caller_selected_character_ids(self) -> None:
        from mcp import Client

        async with Client(create_server(SelectorDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools[
                "ck3_query_zhongguo_manager_subordinate_selector_v1"
            ]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {"request_nonce", "expected_revision"},
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_manager_subordinate_selector_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_zhongguo_manager_subordinate_selector_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "manager_character_id": MANAGER,
                },
            )
        self.assertFalse(accepted.is_error)
        self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
