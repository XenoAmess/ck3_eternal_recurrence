from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.zhongguo_result_case_snapshot_contract import (
    ZHONGGUO_RESULT_CASE_KIND_V1,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoResultCaseQueryV1,
    normalize_native_zhongguo_result_case_snapshot_v1,
    normalize_zhongguo_result_case_snapshot_v1_response,
    parse_query_zhongguo_result_case_snapshot_v1_step,
    query_zhongguo_result_case_snapshot_v1_step,
)


NATIVE_REVISION = 81
PUBLIC_REVISION = 7
CONNECTION_GENERATION = 4
DATE_RAW = 730_101
PLAYER_CHARACTER_ID = 100
OWNER_CHARACTER_ID = 200
SNAPSHOT_ID = "native-headless:received-result:81"
REQUEST_NONCE = "received-self:81"
SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "zhongguo-result-case-snapshot-v1.schema.json"
)


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _unavailable(reason: str = "case_unavailable") -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": reason,
    }


def _query(owner_character_id: int = OWNER_CHARACTER_ID) -> ZhongguoResultCaseQueryV1:
    return ZhongguoResultCaseQueryV1(
        owner_character_id=owner_character_id,
        request_nonce=REQUEST_NONCE,
    )


def _provenance() -> dict[str, str]:
    return {
        "game_version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": (
            ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
        "backend_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
    }


def _frame(matrix: str = "open") -> dict[str, object]:
    delivery = {
        "open": (1, 0, False, 0, False),
        "signed_a": (3, 1, False, 903, True),
        "signed_b": (3, 2, True, 903, True),
        "refused_c": (2, 3, False, 0, False),
    }[matrix]
    state, method, objection, settlement, appeal = delivery
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_RESULT_CASE_KIND_V1,
        "request_nonce": REQUEST_NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER_CHARACTER_ID,
        "subject_character_id": PLAYER_CHARACTER_ID,
        "requested_owner_character_id": OWNER_CHARACTER_ID,
        "case": {
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(PLAYER_CHARACTER_ID),
            "cycle_serial": _available(7),
            "case_serial": _available(903),
            "state": _available(state),
            "grade": _available(1),
        },
        "notice": {
            "absolute_grade": _available(2),
            "kpi_frozen_q100000": _available(7_654_321),
            "rank_frozen": _available(4),
            "cohort_n_frozen": _available(17),
        },
        "delivery": {
            "method": _available(method),
            "objection_recorded": _available(objection),
            "settlement_posted_serial": _available(settlement),
            "appeal_open": _available(appeal),
        },
        "readiness": {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "case_identity_ready": True,
            "notice_facts_ready": True,
            "delivery_state_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _unavailable_frame(reason: str) -> dict[str, object]:
    frame = _frame()
    frame["status"] = "unavailable"
    frame["unavailable_reason"] = reason
    for group_name in ("case", "notice", "delivery"):
        group = frame[group_name]
        assert isinstance(group, dict)
        for key in group:
            group[key] = _unavailable()
    frame["readiness"] = {
        "player_subject_binding_ready": False,
        "owner_binding_ready": False,
        "case_identity_ready": False,
        "notice_facts_ready": False,
        "delivery_state_ready": False,
        "same_frame_ready": True,
        "ready": False,
    }
    return frame


def _response(
    frame: dict[str, object] | None = None,
) -> dict[str, object]:
    result = copy.deepcopy(frame if frame is not None else _frame())
    actual_owner = (
        OWNER_CHARACTER_ID if result["status"] == "available" else None
    )
    result.update(
        {
            "build": {
                "version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
                "exe_sha256": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
                ),
            },
            "source": {
                "bridge_version": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "game_adapter_id": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
                ),
                "backend_id": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID
                ),
                "consumer_id": (
                    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID
                ),
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
                "owner_character_id": actual_owner,
                "expected_revision": PUBLIC_REVISION,
            },
        }
    )
    return result


class ZhongguoResultCaseSnapshotContractTests(unittest.TestCase):
    def test_step_round_trip_has_only_owner_and_nonce(self) -> None:
        step = query_zhongguo_result_case_snapshot_v1_step(
            OWNER_CHARACTER_ID, REQUEST_NONCE
        )
        self.assertEqual(
            parse_query_zhongguo_result_case_snapshot_v1_step(step),
            _query(),
        )
        self.assertNotIn("subject", step)
        self.assertNotIn("zg361_", step)
        for malformed in (
            "query-zhongguo-result-case-snapshot-v1-0-00",
            "query-zhongguo-result-case-snapshot-v1-0200-00",
            "query-zhongguo-result-case-snapshot-v1-200-0",
            "query-zhongguo-result-case-snapshot-v1-200-ff",
            "query-zhongguo-result-case-snapshot-v1-200-00-extra",
        ):
            self.assertIsNone(
                parse_query_zhongguo_result_case_snapshot_v1_step(malformed)
            )

    def test_four_product_delivery_matrices_and_q100000_are_preserved(self) -> None:
        for matrix in ("open", "signed_a", "signed_b", "refused_c"):
            with self.subTest(matrix=matrix):
                normalized = normalize_native_zhongguo_result_case_snapshot_v1(
                    _frame(matrix),
                    expected_query=_query(),
                    expected_snapshot_revision=NATIVE_REVISION,
                    expected_date_raw=DATE_RAW,
                    expected_player_character_id=PLAYER_CHARACTER_ID,
                )
                self.assertTrue(normalized["readiness"]["ready"])
                self.assertEqual(
                    normalized["notice"]["kpi_frozen_q100000"]["value"],
                    7_654_321,
                )

    def test_rank_over_cohort_is_an_available_but_not_ready_notice(self) -> None:
        frame = _frame()
        frame["notice"]["rank_frozen"] = _available(18)
        frame["readiness"]["notice_facts_ready"] = False
        frame["readiness"]["ready"] = False
        normalized = normalize_native_zhongguo_result_case_snapshot_v1(
            frame,
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )
        self.assertEqual(normalized["status"], "available")
        self.assertFalse(normalized["readiness"]["notice_facts_ready"])

    def test_owner_failures_are_typed_unavailable_and_semantically_wiped(self) -> None:
        for reason in ("owner_filter_mismatch", "not_received_self"):
            with self.subTest(reason=reason):
                frame = _unavailable_frame(reason)
                normalized = normalize_native_zhongguo_result_case_snapshot_v1(
                    frame,
                    expected_query=_query(),
                    expected_snapshot_revision=NATIVE_REVISION,
                    expected_date_raw=DATE_RAW,
                    expected_player_character_id=PLAYER_CHARACTER_ID,
                )
                self.assertEqual(normalized["unavailable_reason"], reason)
                for group_name in ("case", "notice", "delivery"):
                    self.assertTrue(
                        all(
                            field["status"] == "unavailable"
                            for field in normalized[group_name].values()
                        )
                    )

    def test_normalizer_rejects_leaks_and_unknown_fields(self) -> None:
        leaked = _unavailable_frame("owner_filter_mismatch")
        leaked["case"]["owner_character_id"] = _available(OWNER_CHARACTER_ID)
        unknown = _frame()
        unknown["subject_character_id_input"] = PLAYER_CHARACTER_ID
        for value in (leaked, unknown):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_native_zhongguo_result_case_snapshot_v1(
                        value,
                        expected_query=_query(),
                        expected_snapshot_revision=NATIVE_REVISION,
                        expected_date_raw=DATE_RAW,
                        expected_player_character_id=PLAYER_CHARACTER_ID,
                    )

    def test_inconsistent_delivery_is_visible_but_not_ready(self) -> None:
        frame = _frame("signed_a")
        frame["delivery"]["settlement_posted_serial"] = _available(902)
        frame["readiness"]["delivery_state_ready"] = False
        frame["readiness"]["ready"] = False
        normalized = normalize_native_zhongguo_result_case_snapshot_v1(
            frame,
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )
        self.assertFalse(normalized["readiness"]["delivery_state_ready"])

    def test_final_response_binds_source_subject_and_actual_owner(self) -> None:
        normalized = normalize_zhongguo_result_case_snapshot_v1_response(
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
            normalized["binding"]["subject_character_id"],
            PLAYER_CHARACTER_ID,
        )
        self.assertEqual(
            normalized["binding"]["owner_character_id"], OWNER_CHARACTER_ID
        )

    def test_schema_accepts_exact_response_and_rejects_extra_surface(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.validate(_response())
        extra = _response()
        extra["evaluator_character_id"] = 999
        with self.assertRaises(ValidationError):
            validator.validate(extra)


if __name__ == "__main__":
    unittest.main()
