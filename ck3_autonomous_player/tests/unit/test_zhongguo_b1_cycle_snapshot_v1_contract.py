from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import codex_mcp_setup as setup  # noqa: E402
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_zhongguo_b1_cycle_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.zhongguo_case_snapshot_contract import (  # noqa: E402
    ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
)
from xar_autoplayer.bridge.zhongguo_b1_cycle_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP,
    ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1,
    ZHONGGUO_B1_CYCLE_BACKEND_ID_V1,
    ZHONGGUO_B1_CYCLE_CASE_KIND_V1,
    ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1,
    ZHONGGUO_B1_CYCLE_EXE_SHA256_V1,
    ZHONGGUO_B1_CYCLE_GAME_VERSION_V1,
    normalize_native_zhongguo_b1_cycle_snapshot_v1,
    parse_query_zhongguo_b1_cycle_snapshot_v1_step,
    query_zhongguo_b1_cycle_snapshot_v1_step,
)


def typed(value):
    return {"status": "available", "value": value, "unavailable_reason": None}


def frame() -> dict[str, object]:
    cycle = {
        "cycle_serial": typed(7), "case_serial": typed(19), "state": typed(6),
        "open_year": typed(1088), "runtime_schema": typed(2), "active": typed(True),
    }
    roster = {
        "subject_count": typed(8), "before_prune_count": typed(8),
        "pruned_count": typed(0), "amendment_count": typed(0),
        "audit_version": typed(1), "reopen_required": typed(False),
    }
    processing = {
        "count": typed(8), "agenda_count": typed(8),
        "local_candidate_count": typed(8),
        "pre_calibration_valid_count": typed(8),
    }
    quota = {
        "rebuild_generation": typed(1), "built_case_serial": typed(19),
        "book_version": typed(1), "target_top": typed(2),
        "target_middle": typed(5), "target_bottom": typed(1),
        "recount_top": typed(2), "recount_middle": typed(5),
        "recount_bottom": typed(1), "pre_calibration_expected_count": typed(8),
        "pre_calibration_mismatch": typed(False), "pool_membership": typed(False),
    }
    closure = {
        "calibration_finalized": typed(False), "state": typed(0),
        "rewards_issued": typed(False), "publication_blocked": typed(False),
    }
    pending = {
        "open_count": typed(0), "slot_used": typed(0),
        "reward_expected_count": typed(0), "rewards_paid_count": typed(0),
        "rewards_committed": typed(False), "watchdog_cancelled_count": typed(0),
        "watchdog_orphan_count": typed(0),
    }
    return {
        "schema_version": 1, "status": "available",
        "case_kind": ZHONGGUO_B1_CYCLE_CASE_KIND_V1,
        "request_nonce": "portable-1", "snapshot_revision": 77,
        "date_raw": 123456, "paused": True, "player_character_id": 100,
        "manager_character_id": 100, "cycle": cycle, "roster": roster,
        "processing": processing, "quota": quota, "closure": closure,
        "pending": pending,
        "readiness": {
            "manager_binding_ready": True, "cycle_identity_ready": True,
            "roster_ready": True, "processing_ready": True, "quota_ready": True,
            "closure_ready": True, "pending_ready": True,
            "same_frame_ready": True, "ready": True,
        },
        "unavailable_reason": None,
        "provenance": {
            "game_version": ZHONGGUO_B1_CYCLE_GAME_VERSION_V1,
            "executable_sha256": ZHONGGUO_B1_CYCLE_EXE_SHA256_V1,
            "backend_id": ZHONGGUO_B1_CYCLE_BACKEND_ID_V1,
            "consumer_id": ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1,
            "allowlist_id": ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1,
            "variable_context_for_scope_rva": "0x3329A40",
            "variable_identifier_table_rva": "0x3B971A0",
            "variable_identifier_lookup_rva": "0x3B97020",
            "variable_identifier_name_rva": "0x3B97090",
            "character_storage_slot_rva": "0x570C130",
        },
    }


def semantic_snapshot() -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": "native:77",
        "revision": 77,
        "state": {
            "phase": "map_hud",
            "date": "1088.1.1",
            "date_raw": 123456,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 100, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_b1_cycle_snapshot_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, value: dict[str, object]) -> None:
        self.on_frame(value)

    def send(self, value: dict[str, object]) -> None:
        self.frames.append(value)
        if self.send_hook is not None:
            self.send_hook(value)

    def close(self) -> None:
        pass

    def transport_error(self) -> None:
        return None


def native_driver() -> tuple[NativeHeadlessGameplayDriver, FakeEndpoint]:
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
            "pid": 6767,
            "session_generation": 0,
            "game_version": ZHONGGUO_B1_CYCLE_GAME_VERSION_V1,
            "expected_ck3_version": ZHONGGUO_B1_CYCLE_GAME_VERSION_V1,
            "executable_sha256": ZHONGGUO_B1_CYCLE_EXE_SHA256_V1,
            "expected_ck3_sha256": ZHONGGUO_B1_CYCLE_EXE_SHA256_V1,
            "game_adapter_id": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(semantic_snapshot())
    return driver, endpoint


class ServiceDriver:
    def __init__(self) -> None:
        self.last_query = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": [
                QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_CAPABILITY
            ],
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "snapshot_id": "native:77",
            "revision": 4,
            "native_revision": 77,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": 123456,
            "paused": True,
            "played_character": {"character_id": 100, "alive": True},
            "diagnostics": {"connection_generation": 1},
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(step)
        if query is None or expected_revision != 4:
            raise AssertionError("service changed the portable B1 binding")
        self.last_query = query
        return {
            "step": QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP,
            "accepted": True,
            "status": "available",
            "query_sequence": 9,
            "snapshot_revision": 77,
            "zhongguo_b1_cycle_snapshot": copy.deepcopy(frame()),
            "backend_id": "native-headless",
            "queried_snapshot_id": "native:77",
            "queried_revision": 4,
            "queried_native_revision": 77,
            "queried_connection_generation": 1,
        }

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float):
        raise AssertionError("read-only B1 observation must not advance")


class B1CycleContractTests(unittest.TestCase):
    def test_nonce_only_step_round_trip(self) -> None:
        step = query_zhongguo_b1_cycle_snapshot_v1_step("portable-1")
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(step)
        self.assertEqual("portable-1", query.request_nonce)
        self.assertNotIn("100", step)
        for bad in ("", "bad space", "é", "x" * 65):
            with self.assertRaises(ValueError):
                query_zhongguo_b1_cycle_snapshot_v1_step(bad)

    def test_normalizer_derives_invariants_and_anomalies(self) -> None:
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(
            query_zhongguo_b1_cycle_snapshot_v1_step("portable-1")
        )
        normalized = normalize_native_zhongguo_b1_cycle_snapshot_v1(
            frame(), expected_query=query, expected_snapshot_revision=77,
            expected_date_raw=123456, expected_player_character_id=100,
        )
        self.assertTrue(normalized["invariants"]["quota_target_conserved"])
        self.assertTrue(normalized["invariants"]["quota_recount_conserved"])
        self.assertTrue(normalized["invariants"]["quota_target_matches_recount"])
        self.assertEqual([], normalized["anomalies"])

    def test_normalizer_is_idempotent_and_rejects_derived_fact_drift(self) -> None:
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(
            query_zhongguo_b1_cycle_snapshot_v1_step("portable-1")
        )
        expected = {
            "expected_query": query,
            "expected_snapshot_revision": 77,
            "expected_date_raw": 123456,
            "expected_player_character_id": 100,
        }
        normalized = normalize_native_zhongguo_b1_cycle_snapshot_v1(
            frame(), **expected
        )
        self.assertEqual(
            normalized,
            normalize_native_zhongguo_b1_cycle_snapshot_v1(
                copy.deepcopy(normalized), **expected
            ),
        )

        bad_invariants = copy.deepcopy(normalized)
        bad_invariants["invariants"]["quota_target_conserved"] = False
        with self.assertRaisesRegex(ValueError, "derived invariants changed"):
            normalize_native_zhongguo_b1_cycle_snapshot_v1(
                bad_invariants, **expected
            )

        bad_anomalies = copy.deepcopy(normalized)
        bad_anomalies["anomalies"] = ["active_zero_roster"]
        with self.assertRaisesRegex(ValueError, "derived anomalies changed"):
            normalize_native_zhongguo_b1_cycle_snapshot_v1(
                bad_anomalies, **expected
            )

    def test_normalizer_flags_zero_roster_liveness(self) -> None:
        value = frame()
        value["roster"]["subject_count"] = typed(0)
        value["processing"]["count"] = typed(0)
        value["quota"]["target_top"] = typed(0)
        value["quota"]["target_middle"] = typed(0)
        value["quota"]["target_bottom"] = typed(0)
        value["quota"]["recount_top"] = typed(0)
        value["quota"]["recount_middle"] = typed(0)
        value["quota"]["recount_bottom"] = typed(0)
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(
            query_zhongguo_b1_cycle_snapshot_v1_step("portable-1")
        )
        normalized = normalize_native_zhongguo_b1_cycle_snapshot_v1(
            value, expected_query=query, expected_snapshot_revision=77,
            expected_date_raw=123456, expected_player_character_id=100,
        )
        self.assertIn("active_zero_roster", normalized["anomalies"])

    def test_partial_lifecycle_values_remain_typed_unavailable(self) -> None:
        value = frame()
        value["quota"]["recount_top"] = {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "variable_absent",
        }
        value["readiness"]["quota_ready"] = False
        query = parse_query_zhongguo_b1_cycle_snapshot_v1_step(
            query_zhongguo_b1_cycle_snapshot_v1_step("portable-1")
        )
        normalized = normalize_native_zhongguo_b1_cycle_snapshot_v1(
            value,
            expected_query=query,
            expected_snapshot_revision=77,
            expected_date_raw=123456,
            expected_player_character_id=100,
        )
        self.assertIsNone(
            normalized["invariants"]["quota_target_matches_recount"]
        )
        self.assertNotIn("quota_target_recount_mismatch", normalized["anomalies"])

    def test_schema_and_frozen_abi_are_machine_neutral(self) -> None:
        schema = json.loads((ROOT / "schemas" / "zhongguo-b1-cycle-snapshot-v1.schema.json").read_text(encoding="utf-8"))
        abi = json.loads((ROOT / "native_bridge" / "research" / "zhongguo_b1_cycle_snapshot_v1_abi.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(frame())
        self.assertEqual(QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_CAPABILITY, abi["capability"])
        self.assertEqual(False, abi["binding"]["caller_character_ids"])
        self.assertNotIn("xenoa", json.dumps([schema, abi]).lower())
        self.assertNotIn("Z:\\", json.dumps([schema, abi]))

    def test_native_request_forbids_identity_and_variable_inputs(self) -> None:
        source = (ROOT / "native_bridge" / "src" / "zhongguo_b1_cycle_snapshot_v1_mailbox.cpp").read_text(encoding="utf-8")
        for forbidden in ("manager_character_id", "owner_character_id", "subject_character_id", "variable_name"):
            self.assertIn(forbidden, source)
        header = (ROOT / "native_bridge" / "include" / "xar_bridge" / "zhongguo_b1_cycle_snapshot_v1.hpp").read_text(encoding="utf-8")
        self.assertIn("kZhongguoB1CycleSnapshotV1VariableAllowlist", header)
        self.assertIn("zg361_b1_quota_recount_top", header)
        self.assertNotIn("variable_name;", header)

    def test_generator_owns_monotonic_rebuild_generation(self) -> None:
        generator = (ROOT.parent / "mod_zhongguo_style" / "tools" / "gen_361_b1_runtime.py").read_text(encoding="utf-8-sig")
        self.assertIn("name = zg361_b1_quota_rebuild_generation value = 0", generator)
        self.assertIn("name = zg361_b1_quota_rebuild_generation add = 1", generator)

    def test_mcp_wrapper_and_portable_setup(self) -> None:
        class Service:
            def query_zhongguo_b1_cycle_snapshot_v1(self, nonce, *, expected_revision):
                return {"nonce": nonce, "revision": expected_revision}

        self.assertEqual(
            {"nonce": "portable-1", "revision": 5},
            _ck3_query_zhongguo_b1_cycle_snapshot_v1(Service(), "portable-1", 5),
        )
        with tempfile.TemporaryDirectory() as raw:
            layout = setup.build_layout(
                account="another-user", local_app_data=Path(raw),
                codex_command=Path(raw) / "codex.exe",
                bootstrap_python=Path(sys.executable),
            )
            plan = setup.render_plan(layout)
        portable = plan["portable_b1_cycle_snapshot"]
        self.assertEqual("ck3_query_zhongguo_b1_cycle_snapshot_v1", portable["tool"])
        self.assertFalse(portable["accepts_character_ids"])
        self.assertFalse(portable["accepts_variable_names"])

    def test_native_driver_sends_only_nonce_and_revision(self) -> None:
        driver, endpoint = native_driver()

        def answer(request: dict[str, object]) -> None:
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": {
                        "step": QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP,
                        "accepted": True,
                        "status": "available",
                        "query_sequence": 9,
                        "snapshot_revision": 77,
                        "zhongguo_b1_cycle_snapshot": copy.deepcopy(frame()),
                    },
                }
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            query_zhongguo_b1_cycle_snapshot_v1_step("portable-1"),
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual("available", result["status"])
        sent = endpoint.frames[-1]
        self.assertEqual(QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP, sent["step"])
        self.assertEqual("portable-1", sent["request_nonce"])
        for forbidden in (
            "manager_character_id",
            "owner_character_id",
            "subject_character_id",
            "variable_name",
        ):
            self.assertNotIn(forbidden, sent)

    def test_native_driver_output_composes_with_service_normalization(self) -> None:
        driver, endpoint = native_driver()

        def answer(request: dict[str, object]) -> None:
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": {
                        "step": QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP,
                        "accepted": True,
                        "status": "available",
                        "query_sequence": 9,
                        "snapshot_revision": 77,
                        "zhongguo_b1_cycle_snapshot": copy.deepcopy(frame()),
                    },
                }
            )

        endpoint.send_hook = answer
        snapshot = driver.take_snapshot()
        result = GameplayBridgeService(
            driver
        ).query_zhongguo_b1_cycle_snapshot_v1(
            "portable-1", expected_revision=int(snapshot["revision"])
        )
        self.assertEqual(100, result["binding"]["manager_character_id"])
        self.assertTrue(result["invariants"]["quota_target_matches_recount"])
        self.assertEqual([], result["anomalies"])

    def test_service_returns_played_manager_binding_and_derived_facts(self) -> None:
        result = GameplayBridgeService(
            ServiceDriver()
        ).query_zhongguo_b1_cycle_snapshot_v1(
            "portable-1", expected_revision=4
        )
        self.assertEqual(100, result["binding"]["manager_character_id"])
        self.assertTrue(result["invariants"]["quota_target_matches_recount"])
        self.assertEqual([], result["anomalies"])


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "MCP SDK not installed")
class B1CycleMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_portable_tool(self) -> None:
        from mcp import Client

        async with Client(create_server(ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            self.assertIn("ck3_query_zhongguo_b1_cycle_snapshot_v1", tools)
            schema = tools[
                "ck3_query_zhongguo_b1_cycle_snapshot_v1"
            ].input_schema
            self.assertEqual(
                {"request_nonce", "expected_revision"},
                set(schema["properties"]),
            )
            called = await client.call_tool(
                "ck3_query_zhongguo_b1_cycle_snapshot_v1",
                {"request_nonce": "portable-1", "expected_revision": 4},
            )
            forbidden = await client.call_tool(
                "ck3_query_zhongguo_b1_cycle_snapshot_v1",
                {
                    "request_nonce": "portable-1",
                    "expected_revision": 4,
                    "subject_character_id": 100,
                },
            )

        self.assertFalse(called.is_error)
        self.assertEqual(100, called.structured_content["manager_character_id"])
        self.assertTrue(forbidden.is_error)


if __name__ == "__main__":
    unittest.main()
