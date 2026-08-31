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

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_zhongguo_b2_pip_snapshot_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.zhongguo_b2_pip_snapshot_contract import (
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP,
    ZHONGGUO_B2_PIP_CASE_KIND_V1,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoB2PipQueryV1,
    _GROUP_SPECS,
    normalize_native_zhongguo_b2_pip_snapshot_v1,
    normalize_zhongguo_b2_pip_snapshot_v1_response,
    parse_query_zhongguo_b2_pip_snapshot_v1_step,
    query_zhongguo_b2_pip_snapshot_v1_step,
)


NATIVE_REVISION = 91
PUBLIC_REVISION = 12
CONNECTION_GENERATION = 8
DATE_RAW = 730_121
PLAYER_CHARACTER_ID = 100
OWNER_CHARACTER_ID = 200
MENTOR_CHARACTER_ID = 300
CASE_SERIAL = 903
SNAPSHOT_ID = "native-headless:b2-pip:91"
REQUEST_NONCE = "b2-pip:91"
SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "zhongguo-b2-pip-snapshot-v1.schema.json"
)


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _unavailable(reason: str = "variable_absent") -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": reason,
    }


def _provenance() -> dict[str, str]:
    return {
        "game_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": (
            ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
        "backend_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
    }


def _query(owner: int = OWNER_CHARACTER_ID) -> ZhongguoB2PipQueryV1:
    return ZhongguoB2PipQueryV1(owner, REQUEST_NONCE)


def _empty_groups(
    reason: str = "variable_absent",
) -> dict[str, dict[str, dict[str, object]]]:
    return {
        group_name: {key: _unavailable(reason) for key in spec}
        for group_name, spec in _GROUP_SPECS.items()
    }


def _pending_frame() -> dict[str, object]:
    groups = _empty_groups()
    groups["gate"].update(
        {
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(PLAYER_CHARACTER_ID),
            "cycle_serial": _available(7),
            "case_serial": _available(CASE_SERIAL),
            "threshold": _available(3),
            "negative_component_count": _available(3),
            "evidence_complete": _available(True),
            "status": _available(1),
            "result_case_serial": _available(CASE_SERIAL),
            "result_grade": _available(1),
            "absolute_grade": _available(1),
            "kpi_frozen_q100000": _available(-100_000),
            "governance_q100000": _available(-100_000),
            "capability_q100000": _available(100_000),
            "growth_q100000": _available(100_000),
            "superior_q100000": _available(100_000),
            "values_q100000": _available(100_000),
            "collaboration_q100000": _available(100_000),
            "jingcha_q100000": _available(100_000),
            "organization_q100000": _available(100_000),
        }
    )
    groups["pip"].update(
        {
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(PLAYER_CHARACTER_ID),
            "cycle_serial": _available(7),
            "case_serial": _available(CASE_SERIAL),
            "state": _available(1),
            "task_kind": _available(2),
            "task_controllable": _available(True),
            "policy_route": _available(1),
        }
    )
    groups["response"].update(
        {
            "subject_response": _available(0),
            "response_case_serial": _available(0),
            "acknowledgement_receipt_serial": _available(CASE_SERIAL),
            "goal_revision_used": _available(False),
            "refusal_receipt_serial": _available(0),
        }
    )
    groups["support"].update(
        {
            "capacity_reserved": _available(False),
            "support_absent": _available(False),
            "treasury_budget_allocated": _available(0),
            "treasury_budget_spent": _available(0),
        }
    )
    groups["budget_ledger"].update(
        {
            "result_case_serial": _available(CASE_SERIAL),
            "treasury_penalty_paid": _available(50),
            "personal_gold_penalty_paid": _available(25),
            "support_treasury_allocated": _available(0),
            "support_treasury_spent": _available(0),
        }
    )
    for ticket_name in ("d180_ticket", "d365_ticket"):
        groups[ticket_name] = {
            key: _unavailable(
                "product_not_persisted"
                if key == "due_date_raw"
                else "native_observation_unavailable"
            )
            for key in _GROUP_SPECS[ticket_name]
        }
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_B2_PIP_CASE_KIND_V1,
        "request_nonce": REQUEST_NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER_CHARACTER_ID,
        "subject_character_id": PLAYER_CHARACTER_ID,
        "requested_owner_character_id": OWNER_CHARACTER_ID,
        **groups,
        "pip_modifier_present": _unavailable(
            "native_observation_unavailable"
        ),
        "readiness": {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "gate_ready": True,
            "gate_evidence_ready": True,
            "pip_identity_ready": True,
            "response_ready": True,
            "support_ready": False,
            "budget_ledger_ready": True,
            "midpoint_ready": False,
            "outcome_ready": False,
            "next_cycle_evidence_ready": False,
            "d180_ticket_observation_ready": False,
            "d365_ticket_observation_ready": False,
            "modifier_observation_ready": False,
            "same_frame_ready": True,
            "ready": True,
        },
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _accepted_support_frame() -> dict[str, object]:
    frame = _pending_frame()
    frame["pip"]["state"] = _available(2)
    frame["response"].update(
        {
            "subject_response": _available(1),
            "response_case_serial": _available(CASE_SERIAL),
            "response_author_character_id": _available(
                PLAYER_CHARACTER_ID
            ),
        }
    )
    frame["support"].update(
        {
            "capacity_reserved": _available(True),
            "owner_capacity_used": _available(1),
            "support_absent": _available(False),
            "hours": _available(12),
            "attention_units": _available(1),
            "mentor_character_id": _available(MENTOR_CHARACTER_ID),
            "budget_owner_character_id": _available(OWNER_CHARACTER_ID),
            "treasury_budget_allocated": _available(25),
            "treasury_budget_spent": _available(25),
            "support_receipt_serial": _available(CASE_SERIAL),
        }
    )
    frame["budget_ledger"].update(
        {
            "support_treasury_allocated": _available(25),
            "support_treasury_spent": _available(25),
        }
    )
    frame["readiness"]["support_ready"] = True
    return frame


def _graduated_frame() -> dict[str, object]:
    frame = _accepted_support_frame()
    frame["pip"]["state"] = _available(3)
    frame["support"]["capacity_reserved"] = _available(False)
    frame["support"]["owner_capacity_used"] = _available(0)
    frame["support"]["released"] = _available(True)
    frame["readiness"]["support_ready"] = False
    frame["midpoint"].update(
        {
            "receipt_serial": _available(CASE_SERIAL),
            "resource_delivery_valid": _available(True),
            "progress_status": _available(0),
            "progress_red_code": _available(1),
            "state": _available(2),
        }
    )
    frame["outcome"].update(
        {
            "code": _available(1),
            "settlement_receipt_serial": _available(CASE_SERIAL),
            "result_cycle_serial": _available(8),
            "result_case_serial": _available(904),
            "result_grade": _available(2),
            "stability_days_observed": _available(365),
            "independent_review_status": _available(0),
            "independent_review_red_code": _available(2),
            "graduation_receipt_serial": _available(CASE_SERIAL),
        }
    )
    frame["next_cycle_evidence"].update(
        {
            "status": _available(1),
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(PLAYER_CHARACTER_ID),
            "source_cycle_serial": _available(7),
            "source_case_serial": _available(CASE_SERIAL),
            "due_cycle_serial": _available(8),
            "delta": _available(10),
        }
    )
    frame["readiness"].update(
        {
            "midpoint_ready": True,
            "outcome_ready": True,
            "next_cycle_evidence_ready": True,
        }
    )
    return frame


def _failed_frame() -> dict[str, object]:
    frame = _graduated_frame()
    frame["pip"]["state"] = _available(4)
    frame["outcome"]["code"] = _available(2)
    frame["outcome"]["graduation_receipt_serial"] = _available(0)
    frame["outcome"]["failure_receipt_serial"] = _available(CASE_SERIAL)
    frame["next_cycle_evidence"]["delta"] = _available(-10)
    return frame


def _refused_frame() -> dict[str, object]:
    frame = _pending_frame()
    frame["pip"]["state"] = _available(5)
    frame["response"].update(
        {
            "subject_response": _available(3),
            "response_case_serial": _available(CASE_SERIAL),
            "response_author_character_id": _available(
                PLAYER_CHARACTER_ID
            ),
            "refusal_receipt_serial": _available(CASE_SERIAL),
        }
    )
    frame["next_cycle_evidence"].update(
        {
            "status": _available(1),
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(PLAYER_CHARACTER_ID),
            "source_cycle_serial": _available(7),
            "source_case_serial": _available(CASE_SERIAL),
            "due_cycle_serial": _available(8),
            "delta": _available(-15),
        }
    )
    frame["readiness"]["next_cycle_evidence_ready"] = True
    return frame


def _unavailable_frame(reason: str) -> dict[str, object]:
    frame = _pending_frame()
    frame["status"] = "unavailable"
    frame["unavailable_reason"] = reason
    for group_name in _GROUP_SPECS:
        frame[group_name] = {
            key: _unavailable("case_unavailable")
            for key in _GROUP_SPECS[group_name]
        }
    frame["pip_modifier_present"] = _unavailable("case_unavailable")
    frame["readiness"] = {
        key: key == "same_frame_ready"
        for key in frame["readiness"]
    }
    return frame


def _response(frame: dict[str, object] | None = None) -> dict[str, object]:
    result = copy.deepcopy(frame if frame is not None else _pending_frame())
    result.update(
        {
            "build": {
                "version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
                "exe_sha256": (
                    ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256
                ),
            },
            "source": {
                "bridge_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION,
                "game_adapter_id": (
                    ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID
                ),
                "backend_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_SOURCE_BACKEND_ID,
                "consumer_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
                "connection_generation": CONNECTION_GENERATION,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER_CHARACTER_ID,
            },
            "binding": {
                "request_nonce": REQUEST_NONCE,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "connection_generation": CONNECTION_GENERATION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER_CHARACTER_ID,
                "subject_character_id": PLAYER_CHARACTER_ID,
                "owner_character_id": (
                    OWNER_CHARACTER_ID
                    if result["status"] == "available"
                    else None
                ),
                "expected_revision": PUBLIC_REVISION,
            },
        }
    )
    return result


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_native_zhongguo_b2_pip_snapshot_v1(
        frame,
        expected_query=_query(),
        expected_snapshot_revision=NATIVE_REVISION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER_CHARACTER_ID,
    )


class ZhongguoB2PipContractTests(unittest.TestCase):
    def test_step_round_trip_exposes_only_owner_filter_and_nonce(self) -> None:
        step = query_zhongguo_b2_pip_snapshot_v1_step(
            OWNER_CHARACTER_ID, REQUEST_NONCE
        )
        self.assertEqual(
            parse_query_zhongguo_b2_pip_snapshot_v1_step(step), _query()
        )
        self.assertNotIn("subject", step)
        self.assertNotIn("zg361_", step)
        for malformed in (
            "query-zhongguo-b2-pip-snapshot-v1-0-00",
            "query-zhongguo-b2-pip-snapshot-v1-0200-00",
            "query-zhongguo-b2-pip-snapshot-v1-200-0",
            "query-zhongguo-b2-pip-snapshot-v1-200-zz",
            "query-zhongguo-b2-pip-snapshot-v1-200-00-extra",
        ):
            self.assertIsNone(
                parse_query_zhongguo_b2_pip_snapshot_v1_step(malformed)
            )

    def test_pending_accept_support_and_duplicate_read_are_truthful(self) -> None:
        pending = _normalize(_pending_frame())
        self.assertTrue(pending["readiness"]["response_ready"])
        self.assertFalse(pending["readiness"]["support_ready"])
        accepted = _normalize(_accepted_support_frame())
        duplicate = _normalize(copy.deepcopy(_accepted_support_frame()))
        self.assertEqual(accepted, duplicate)
        self.assertTrue(accepted["readiness"]["support_ready"])
        self.assertEqual(accepted["support"]["hours"]["value"], 12)
        self.assertEqual(
            accepted["support"]["treasury_budget_spent"]["value"], 25
        )

    def test_midpoint_outcome_and_pending_next_cycle_evidence(self) -> None:
        normalized = _normalize(_graduated_frame())
        self.assertTrue(normalized["readiness"]["midpoint_ready"])
        self.assertTrue(normalized["readiness"]["outcome_ready"])
        self.assertTrue(
            normalized["readiness"]["next_cycle_evidence_ready"]
        )

        failed = _normalize(_failed_frame())
        self.assertTrue(failed["readiness"]["outcome_ready"])
        self.assertEqual(
            failed["outcome"]["failure_receipt_serial"]["value"],
            CASE_SERIAL,
        )

        refused = _normalize(_refused_frame())
        self.assertTrue(refused["readiness"]["response_ready"])
        self.assertFalse(refused["readiness"]["outcome_ready"])
        self.assertEqual(
            refused["response"]["refusal_receipt_serial"]["value"],
            CASE_SERIAL,
        )

    def test_wrong_owner_and_case_absence_leak_no_semantics(self) -> None:
        for reason in ("owner_filter_mismatch", "case_not_found"):
            normalized = _normalize(_unavailable_frame(reason))
            self.assertEqual(normalized["unavailable_reason"], reason)
            self.assertTrue(
                all(
                    field["unavailable_reason"] == "case_unavailable"
                    for group_name in _GROUP_SPECS
                    for field in normalized[group_name].values()
                )
            )

        forged = _unavailable_frame("owner_filter_mismatch")
        forged["readiness"]["owner_binding_ready"] = True
        with self.assertRaises(ValueError):
            _normalize(forged)

    def test_tickets_due_dates_and_modifier_cannot_be_fabricated(self) -> None:
        for group_name, field_name, value in (
            ("d180_ticket", "owner_character_id", OWNER_CHARACTER_ID),
            ("d365_ticket", "due_date_raw", DATE_RAW + 365),
            (None, "pip_modifier_present", True),
        ):
            frame = _pending_frame()
            if group_name is None:
                frame[field_name] = _available(value)
            else:
                frame[group_name][field_name] = _available(value)
            with self.assertRaises(ValueError):
                _normalize(frame)

        invalid_mentor = _accepted_support_frame()
        invalid_mentor["support"]["mentor_character_id"] = _available(-1)
        invalid_mentor["readiness"]["support_ready"] = False
        with self.assertRaises(ValueError):
            _normalize(invalid_mentor)

    def test_each_component_readiness_is_recomputed(self) -> None:
        for key in (
            "gate_evidence_ready",
            "response_ready",
            "support_ready",
            "budget_ledger_ready",
            "midpoint_ready",
            "outcome_ready",
            "next_cycle_evidence_ready",
        ):
            frame = _graduated_frame()
            frame["readiness"][key] = not frame["readiness"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                _normalize(frame)

    def test_final_response_and_schema_are_exact(self) -> None:
        normalized = normalize_zhongguo_b2_pip_snapshot_v1_response(
            _response(),
            expected_query=_query(),
            expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION,
            expected_native_revision=NATIVE_REVISION,
            expected_connection_generation=CONNECTION_GENERATION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )
        self.assertEqual(
            normalized["binding"]["owner_character_id"], OWNER_CHARACTER_ID
        )
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.validate(_response())
        extra = _response()
        extra["variable_name"] = "zg361_b2_pip_state"
        with self.assertRaises(ValidationError):
            validator.validate(extra)


def _native_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 13,
        "snapshot_revision": NATIVE_REVISION,
        "zhongguo_b2_pip_snapshot": copy.deepcopy(frame),
        "backend_id": "native-headless",
    }


def _semantic_snapshot(
    revision: int = NATIVE_REVISION, *, paused: bool = True
) -> dict[str, object]:
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
        self.pipe_name = r"\\.\pipe\xar_b2_pip_v1_fixture"
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
            "bridge_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION,
            "pid": 6868,
            "session_generation": 0,
            "game_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
            "expected_ck3_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
            "executable_sha256": (
                ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "expected_ck3_sha256": (
                ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
            "game_adapter_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID,
            "capabilities": [
                "game.state.snapshot",
                QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


class ZhongguoB2PipNativeDriverTests(unittest.TestCase):
    def test_native_request_contains_no_subject_or_variable_surface(self) -> None:
        driver, endpoint = _native_driver()
        self.assertTrue(
            driver.capabilities()[
                "zhongguo_b2_pip_snapshot_v1_query_supported"
            ]
        )
        self.assertEqual(
            _action_steps(
                [QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY], paused=True
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
                    "result": _native_result(_pending_frame()),
                }
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            query_zhongguo_b2_pip_snapshot_v1_step(
                OWNER_CHARACTER_ID, REQUEST_NONCE
            ),
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(result["status"], "available")
        duplicate = driver.execute_step(
            query_zhongguo_b2_pip_snapshot_v1_step(
                OWNER_CHARACTER_ID, REQUEST_NONCE
            ),
            expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(duplicate, result)
        query_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("step") == QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP
        ]
        self.assertEqual(len(query_frames), 2)
        self.assertEqual(
            set(query_frames[-1]),
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

    def test_malformed_step_and_revision_drift_fail_closed(self) -> None:
        driver, _endpoint = _native_driver()
        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-zhongguo-b2-pip-snapshot-v1-200-zz",
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
                    "result": _native_result(_pending_frame()),
                }
            )

        endpoint.send_hook = drift
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(
                query_zhongguo_b2_pip_snapshot_v1_step(
                    OWNER_CHARACTER_ID, REQUEST_NONCE
                ),
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

    def test_hybrid_capability_is_authoritative_from_native_only(self) -> None:
        class _CapabilitiesOnly:
            def __init__(self, bridge_capabilities: list[str]) -> None:
                self.bridge_capabilities = bridge_capabilities

            def capabilities(self) -> dict[str, object]:
                return {
                    "action_steps": [],
                    "bridge_capabilities": self.bridge_capabilities,
                }

        hybrid = object.__new__(ConfiguredHybridFallbackDriver)
        hybrid.native = _CapabilitiesOnly([])
        hybrid._delegate = _CapabilitiesOnly(
            [QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY]
        )
        self.assertNotIn(
            QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
            hybrid.capabilities()["bridge_capabilities"],
        )
        hybrid.native = _CapabilitiesOnly(
            [QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY]
        )
        self.assertIn(
            QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
            hybrid.capabilities()["bridge_capabilities"],
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
        self.last_query: ZhongguoB2PipQueryV1 | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY]
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
            "episode_run_id": "b2-pip-fixture",
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": generation,
                "bridge_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION,
                "hello": {
                    "bridge_version": (
                        ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION
                    ),
                    "game_adapter_id": (
                        ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID
                    ),
                    "game_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_b2_pip_snapshot_v1_step(step)
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the B2 PIP binding")
        self.last_query = query
        return {
            **_native_result(_pending_frame()),
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("read-only B2 PIP observation must not advance")


class ZhongguoB2PipServiceTests(unittest.TestCase):
    def test_service_and_helper_expose_exact_three_inputs(self) -> None:
        self.assertEqual(
            set(
                inspect.signature(
                    GameplayBridgeService.query_zhongguo_b2_pip_snapshot_v1
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
                    _ck3_query_zhongguo_b2_pip_snapshot_v1
                ).parameters
            ),
            {
                "service",
                "request_nonce",
                "expected_revision",
                "owner_character_id",
            },
        )

    def test_service_returns_received_self_binding(self) -> None:
        driver = _ServiceDriver()
        result = _ck3_query_zhongguo_b2_pip_snapshot_v1(
            GameplayBridgeService(driver),
            REQUEST_NONCE,
            PUBLIC_REVISION,
            OWNER_CHARACTER_ID,
        )
        self.assertEqual(
            result["binding"]["subject_character_id"], PLAYER_CHARACTER_ID
        )
        self.assertEqual(
            result["binding"]["owner_character_id"], OWNER_CHARACTER_ID
        )
        self.assertEqual(driver.last_query, _query())

    def test_service_rejects_pause_capability_and_connection_drift(self) -> None:
        for driver, error in (
            (_ServiceDriver(advertise=False), UnsupportedStepError),
            (_ServiceDriver(paused=False), BridgeUnavailableError),
            (_ServiceDriver(connection_drift=True), BridgeUnavailableError),
        ):
            with self.subTest(driver=driver), self.assertRaises(error):
                GameplayBridgeService(
                    driver
                ).query_zhongguo_b2_pip_snapshot_v1(
                    REQUEST_NONCE,
                    expected_revision=PUBLIC_REVISION,
                    owner_character_id=OWNER_CHARACTER_ID,
                )

        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_zhongguo_b2_pip_snapshot_v1(
                REQUEST_NONCE,
                expected_revision=PUBLIC_REVISION + 1,
                owner_character_id=OWNER_CHARACTER_ID,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoB2PipMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_schema_rejects_subject_and_variable_inputs(self) -> None:
        from mcp import Client

        async with Client(create_server(_ServiceDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_query_zhongguo_b2_pip_snapshot_v1"]
            self.assertEqual(
                set(tool.input_schema["properties"]),
                {
                    "request_nonce",
                    "expected_revision",
                    "owner_character_id",
                },
            )
            accepted = await client.call_tool(
                "ck3_query_zhongguo_b2_pip_snapshot_v1",
                {
                    "request_nonce": REQUEST_NONCE,
                    "expected_revision": PUBLIC_REVISION,
                    "owner_character_id": OWNER_CHARACTER_ID,
                },
            )
            rejected = []
            for unexpected in (
                {"variable_name": "zg361_b2_pip_state"},
                {"subject_character_id": PLAYER_CHARACTER_ID},
            ):
                rejected.append(
                    await client.call_tool(
                        "ck3_query_zhongguo_b2_pip_snapshot_v1",
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
