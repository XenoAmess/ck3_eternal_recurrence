from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP,
    ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1,
    ZHONGGUO_MANAGER_GOVERNANCE_CASE_KIND_V1,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoManagerGovernanceQueryV1,
    normalize_native_zhongguo_manager_governance_snapshot_v1,
    normalize_zhongguo_manager_governance_snapshot_v1_response,
    parse_query_zhongguo_manager_governance_snapshot_v1_step,
    query_zhongguo_manager_governance_snapshot_v1_step,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_manager_governance_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


NATIVE_REVISION = 81
PUBLIC_REVISION = 7
CONNECTION_GENERATION = 4
DATE_RAW = 730_101
PLAYER = 100
SUBJECT = 200
OWNER = PLAYER
SNAPSHOT_ID = "native-headless:manager-governance:81"
NONCE = "manager:81"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "zhongguo-manager-governance-snapshot-v1.schema.json"
)


def _available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def _query() -> ZhongguoManagerGovernanceQueryV1:
    return ZhongguoManagerGovernanceQueryV1(SUBJECT, OWNER, NONCE)


def _receipt(choice: int = 1) -> dict[str, object]:
    return {
        "owner_character_id": _available(OWNER),
        "subject_character_id": _available(SUBJECT),
        "cycle_serial": _available(7),
        "case_serial": _available(903),
        "state": _available(1),
        "choice": _available(choice),
    }


def _provenance() -> dict[str, str]:
    return {
        "game_version": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
        "backend_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
    }


def _readiness(**overrides: bool) -> dict[str, bool]:
    result = {
        "subject_binding_ready": True,
        "bounded_ai_dependency_ready": True,
        "case_identity_ready": True,
        "team_snapshot_ready": True,
        "f035_receipt_ready": True,
        "distribution_snapshot_ready": True,
        "distribution_conservation_ready": True,
        "next_cycle_policy_ready": True,
        "effective_distribution_ready": True,
        "distribution_settlement_ready": True,
        "actual_bottom_slots_ready": True,
        "distribution_lifecycle_ready": True,
        "f032_receipt_ready": True,
        "manager_score_ready": True,
        "component8_token_ready": True,
        "component8_settlement_ready": True,
        "component8_lifecycle_ready": True,
        "same_frame_ready": True,
        "ready": True,
    }
    result.update(overrides)
    return result


def _frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_MANAGER_GOVERNANCE_CASE_KIND_V1,
        "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "subject_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "subject_binding": {
            "kind": "bounded_ai_direct_manager",
            "manager_character_id": _available(SUBJECT),
            "owner_character_id": _available(OWNER),
            "bounded_ai_manager_dependency": _available(
                ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1
            ),
        },
        "f_case": {
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(7),
            "case_serial": _available(903),
            "state": _available(2),
            "active": _available(True),
            "revision": _available(5),
        },
        "team_snapshot": {
            "status": _available(1),
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(7),
            "case_serial": _available(903),
            "revision": _available(12),
            "source_cycle": _available(6),
            "cohort_n": _available(17),
            "aggregates": {
                "targets": _available(25),
                "jingcha": _available(10),
                "calibration": _available(-5),
                "pip_success": _available(5),
                "appeal_overturn": _available(-5),
                "retention": _available(30),
                "hc_efficiency": _available(9),
            },
        },
        "f035": {
            "receipt": _receipt(),
            "snapshot": {
                "available": _available(True),
                "mode": _available(1),
                "rule_source": _available(2),
                "top_slots": _available(5),
                "middle_slots": _available(11),
                "bottom_slots": _available(1),
                "conserved_slots": _available(17),
            },
            "next_cycle_policy": {
                "status": _available(2),
                "owner_character_id": _available(SUBJECT),
                "subject_character_id": _available(SUBJECT),
                "source_reviewer_character_id": _available(OWNER),
                "source_cycle": _available(7),
                "source_case": _available(903),
                "source_revision": _available(3),
                "input_revision": _available(12),
                "mode": _available(1),
                "rule_source": _available(2),
                "due_cycle": _available(8),
            },
            "effective": {
                "mode": _available(1),
                "cycle": _available(8),
                "source_cycle": _available(7),
                "source_case": _available(903),
                "input_revision": _available(12),
                "settled_cycle": _available(8),
                "settlement_receipt": _available(903),
                "actual_cohort_n": _available(23),
                "actual_bottom_slots": _available(2),
            },
        },
        "f032": {
            "receipt": _receipt(),
            "manager_score": {"sum": _available(69), "mode": _available(1)},
            "component8": {
                "status": _available(2),
                "owner_character_id": _available(OWNER),
                "subject_character_id": _available(SUBJECT),
                "source_cycle": _available(7),
                "source_case": _available(903),
                "source_revision": _available(4),
                "input_revision": _available(12),
                "component": _available(8),
                "value": _available(69),
                "due_cycle": _available(8),
                "settled_by_owner_character_id": _available(OWNER),
                "settled_cycle": _available(8),
                "settled_value": _available(69),
                "settlement_receipt": _available(903),
            },
        },
        "readiness": _readiness(),
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _response(frame: dict[str, object] | None = None) -> dict[str, object]:
    result = copy.deepcopy(frame if frame is not None else _frame())
    result.update(
        {
            "build": {
                "version": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION,
                "exe_sha256": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256
                ),
            },
            "source": {
                "bridge_version": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "game_adapter_id": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_ADAPTER_ID
                ),
                "backend_id": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID
                ),
                "consumer_id": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID
                ),
                "connection_generation": CONNECTION_GENERATION,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
            },
            "binding": {
                "request_nonce": NONCE,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "connection_generation": CONNECTION_GENERATION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
                "subject_character_id": SUBJECT,
                "owner_character_id": OWNER,
                "subject_binding_kind": "bounded_ai_direct_manager",
                "bounded_ai_manager_dependency": (
                    ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1
                ),
                "expected_revision": PUBLIC_REVISION,
            },
        }
    )
    return result


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_native_zhongguo_manager_governance_snapshot_v1(
        frame,
        expected_query=_query(),
        expected_snapshot_revision=NATIVE_REVISION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER,
    )


class ZhongguoManagerGovernanceSnapshotContractTests(unittest.TestCase):
    def test_step_round_trip_has_no_kind_or_variable_name(self) -> None:
        step = query_zhongguo_manager_governance_snapshot_v1_step(
            SUBJECT, OWNER, NONCE
        )
        self.assertEqual(
            parse_query_zhongguo_manager_governance_snapshot_v1_step(step),
            _query(),
        )
        self.assertNotIn("zhongguo.manager", step)
        self.assertNotIn("zg361_", step)
        for malformed in (
            "query-zhongguo-manager-governance-snapshot-v1-0-100-00",
            "query-zhongguo-manager-governance-snapshot-v1-0200-100-00",
            "query-zhongguo-manager-governance-snapshot-v1-200-0-00",
            "query-zhongguo-manager-governance-snapshot-v1-200-100-0",
        ):
            self.assertIsNone(
                parse_query_zhongguo_manager_governance_snapshot_v1_step(
                    malformed
                )
            )

    def test_settled_ai_manager_projection_is_ready(self) -> None:
        normalized = _normalize(_frame())
        self.assertTrue(normalized["readiness"]["ready"])
        self.assertEqual(
            normalized["f035"]["effective"]["actual_bottom_slots"]["value"],
            2,
        )
        self.assertEqual(
            normalized["f032"]["component8"]["component"]["value"], 8
        )

    def test_bounded_ai_dependency_cannot_be_asserted_by_caller_data(self) -> None:
        frame = _frame()
        frame["subject_binding"]["bounded_ai_manager_dependency"] = _unavailable(
            "not_applicable"
        )
        frame["readiness"]["bounded_ai_dependency_ready"] = False
        frame["readiness"]["subject_binding_ready"] = False
        frame["readiness"]["ready"] = False
        with self.assertRaises(ValueError):
            _normalize(frame)

    def test_distribution_conservation_and_actual_bottom_are_enforced(self) -> None:
        for path, value in (
            (("snapshot", "middle_slots"), 12),
            (("effective", "actual_bottom_slots"), 1),
        ):
            with self.subTest(path=path):
                frame = _frame()
                frame["f035"][path[0]][path[1]] = _available(value)
                with self.assertRaises(ValueError):
                    _normalize(frame)

    def test_component8_is_the_official_next_cycle_token(self) -> None:
        frame = _frame()
        frame["f032"]["component8"]["component"] = _available(9)
        with self.assertRaises(ValueError):
            _normalize(frame)
        frame = _frame()
        frame["f032"]["component8"]["value"] = _available(68)
        with self.assertRaises(ValueError):
            _normalize(frame)

    def test_route_c_wipes_stale_f035_and_f032_business_fields(self) -> None:
        frame = _frame()
        frame["f035"]["receipt"] = _receipt(3)
        for group in ("snapshot", "next_cycle_policy", "effective"):
            for key in frame["f035"][group]:
                frame["f035"][group][key] = _unavailable("not_applicable")
        frame["f032"]["receipt"] = _receipt(3)
        for group in ("manager_score", "component8"):
            for key in frame["f032"][group]:
                frame["f032"][group][key] = _unavailable("not_applicable")
        frame["readiness"] = _readiness(
            distribution_snapshot_ready=False,
            distribution_conservation_ready=False,
            next_cycle_policy_ready=False,
            effective_distribution_ready=False,
            distribution_settlement_ready=False,
            actual_bottom_slots_ready=False,
            manager_score_ready=False,
            component8_token_ready=False,
            component8_settlement_ready=False,
        )
        self.assertTrue(_normalize(frame)["readiness"]["ready"])
        leaked = copy.deepcopy(frame)
        leaked["f032"]["manager_score"]["sum"] = _available(69)
        with self.assertRaises(ValueError):
            _normalize(leaked)

    def test_public_response_and_schema_bind_the_ai_selection(self) -> None:
        response = _response()
        normalized = normalize_zhongguo_manager_governance_snapshot_v1_response(
            response,
            expected_query=_query(),
            expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION,
            expected_native_revision=NATIVE_REVISION,
            expected_connection_generation=CONNECTION_GENERATION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertEqual(
            normalized["binding"]["bounded_ai_manager_dependency"],
            ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1,
        )
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.validate(response)
        extra = copy.deepcopy(response)
        extra["variable_name"] = "zg361_mg_manager_score"
        with self.assertRaises(ValidationError):
            validator.validate(extra)

    def test_production_transport_is_wired_but_not_claimed_live(self) -> None:
        native_root = PROJECT_ROOT / "native_bridge"
        sources = {
            "cmake": (native_root / "CMakeLists.txt").read_text(
                encoding="utf-8"
            ),
            "bridge": (native_root / "src" / "bridge.cpp").read_text(
                encoding="utf-8"
            ),
            "game_adapter": (
                native_root / "src" / "game_adapter.cpp"
            ).read_text(encoding="utf-8"),
            "adapter": (
                native_root / "src" / "ck3_11906_adapter.cpp"
            ).read_text(encoding="utf-8"),
            "driver": (
                PROJECT_ROOT / "src/xar_autoplayer/bridge/native_driver.py"
            ).read_text(encoding="utf-8"),
            "service": (
                PROJECT_ROOT / "src/xar_autoplayer/bridge/service.py"
            ).read_text(encoding="utf-8"),
            "mcp": (
                PROJECT_ROOT / "src/xar_autoplayer/bridge/mcp_server.py"
            ).read_text(encoding="utf-8"),
        }
        tokens = {
            "cmake": (
                "src/zhongguo_manager_governance_snapshot_v1.cpp",
                "src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp",
                "src/zhongguo_manager_governance_snapshot_v1_serializer.cpp",
            ),
            "bridge": (
                "ExecuteZhongguoManagerGovernanceSnapshotMailboxQueryV1",
                "ZhongguoManagerGovernanceSnapshotResultFrame",
                "permitted_executor_quinquevigintary",
            ),
            "game_adapter": (
                "ParseZhongguoManagerGovernanceSnapshotV1Step",
            ),
            "adapter": (
                "kZhongguoManagerGovernanceSnapshotV1Capability",
            ),
            "driver": (
                "_execute_zhongguo_manager_governance_snapshot_v1_query",
            ),
            "service": (
                "query_zhongguo_manager_governance_snapshot_v1",
            ),
            "mcp": (
                "ck3_query_zhongguo_manager_governance_snapshot_v1",
            ),
        }
        for source, expected in tokens.items():
            for token in expected:
                with self.subTest(source=source, token=token):
                    self.assertIn(token, sources[source])
        abi = json.loads(
            (
                native_root
                / "research/zhongguo_manager_governance_snapshot_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            abi["status"],
            "production_transport_integrated_static_ready_not_live",
        )
        self.assertIsNone(
            abi["integration_state"]["production_live_artifact"]
        )
        self.assertEqual(
            abi["integration_state"]["bounded_ai_manager_native_selector"],
            "exact_build_native_bound_static_not_live",
        )


class ManagerGovernanceServiceDriver:
    def __init__(self, *, advertise: bool = True) -> None:
        self.advertise = advertise
        self.last_query: ZhongguoManagerGovernanceQueryV1 | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY]
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
            "map_ready": True,
            "episode_run_id": "manager-governance-fixture",
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {
                "connection_generation": CONNECTION_GENERATION,
                "bridge_version": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "game_version": (
                        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_version": (
                        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        parsed = parse_query_zhongguo_manager_governance_snapshot_v1_step(step)
        if parsed is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the manager binding")
        self.last_query = parsed
        return {
            "step": QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP,
            "accepted": True,
            "status": "available",
            "query_sequence": 1,
            "snapshot_revision": NATIVE_REVISION,
            "zhongguo_manager_governance_snapshot": _frame(),
            "backend_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }


class ZhongguoManagerGovernanceServiceTests(unittest.TestCase):
    def test_service_and_mcp_helper_expose_only_fixed_selectors(self) -> None:
        self.assertEqual(
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_manager_governance_snapshot_v1
                ).parameters
            ),
            {
                "self",
                "request_nonce",
                "expected_revision",
                "subject_character_id",
                "owner_character_id",
            },
        )
        self.assertEqual(
            set(
                inspect.signature(
                    _ck3_query_zhongguo_manager_governance_snapshot_v1
                ).parameters
            ),
            {
                "service",
                "request_nonce",
                "expected_revision",
                "subject_character_id",
                "owner_character_id",
            },
        )

    def test_service_returns_the_typed_bounded_ai_binding(self) -> None:
        driver = ManagerGovernanceServiceDriver()
        result = _ck3_query_zhongguo_manager_governance_snapshot_v1(
            GameplayBridgeService(driver),
            NONCE,
            PUBLIC_REVISION,
            SUBJECT,
            OWNER,
        )
        self.assertTrue(result["readiness"]["ready"])
        self.assertEqual(
            result["binding"]["subject_binding_kind"],
            "bounded_ai_direct_manager",
        )
        self.assertEqual(driver.last_query, _query())

    def test_native_driver_sends_only_fixed_request_fields(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        snapshot = ManagerGovernanceServiceDriver().take_snapshot()
        driver.take_snapshot = lambda: copy.deepcopy(snapshot)
        calls: list[dict[str, object]] = []

        def execute(
            step: str,
            *,
            expected_revision: int,
            required_capability: str,
            request_fields: dict[str, object],
        ) -> dict[str, object]:
            calls.append(
                {
                    "step": step,
                    "expected_revision": expected_revision,
                    "required_capability": required_capability,
                    "request_fields": dict(request_fields),
                }
            )
            return {
                "step": QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP,
                "accepted": True,
                "status": "available",
                "query_sequence": 1,
                "snapshot_revision": NATIVE_REVISION,
                "zhongguo_manager_governance_snapshot": _frame(),
                "backend_id": (
                    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID
                ),
            }

        driver._execute_primitive_step = execute
        result = driver._execute_zhongguo_manager_governance_snapshot_v1_query(
            _query(), expected_revision=PUBLIC_REVISION
        )
        self.assertEqual(result["status"], "available")
        self.assertEqual(
            calls,
            [
                {
                    "step": (
                        QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP
                    ),
                    "expected_revision": PUBLIC_REVISION,
                    "required_capability": (
                        QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
                    ),
                    "request_fields": {
                        "subject_character_id": SUBJECT,
                        "owner_character_id": OWNER,
                        "request_nonce": NONCE,
                    },
                }
            ],
        )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoManagerGovernanceMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_schema_is_fixed_and_rejects_variable_names(self) -> None:
        from mcp import Client

        async with Client(create_server(ManagerGovernanceServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools[
                "ck3_query_zhongguo_manager_governance_snapshot_v1"
            ]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {
                    "request_nonce",
                    "expected_revision",
                    "subject_character_id",
                    "owner_character_id",
                },
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_manager_governance_snapshot_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "subject_character_id": SUBJECT,
                    "owner_character_id": OWNER,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_zhongguo_manager_governance_snapshot_v1",
                {
                    "request_nonce": NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "subject_character_id": SUBJECT,
                    "owner_character_id": OWNER,
                    "variable_name": "zg361_mg_manager_score",
                },
            )
        self.assertFalse(accepted.is_error)
        self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
