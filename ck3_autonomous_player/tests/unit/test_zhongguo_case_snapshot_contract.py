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

from xar_autoplayer.bridge import zhongguo_case_snapshot_contract as contract
from xar_autoplayer.bridge.zhongguo_case_snapshot_contract import (
    ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
    ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoCaseQueryV1,
    normalize_native_zhongguo_case_snapshot_v1,
    normalize_zhongguo_case_snapshot_v1_response,
    parse_query_zhongguo_case_snapshot_v1_step,
    query_zhongguo_case_snapshot_v1_step,
)


NATIVE_REVISION = 17
PUBLIC_REVISION = 4
CONNECTION_GENERATION = 3
DATE_RAW = 53_182_008
PLAYER_CHARACTER_ID = 12_345
SUBJECT_CHARACTER_ID = 23_456
OWNER_CHARACTER_ID = PLAYER_CHARACTER_ID
SNAPSHOT_ID = "native-headless:fixture:4"
REQUEST_NONCE = "zg361-b1.case:0001"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "zhongguo-case-snapshot-v1.schema.json"


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": reason,
    }


def _provenance() -> dict[str, str]:
    return {
        "game_version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
        "backend_id": ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
    }


def _query(owner_character_id: int | None = None) -> ZhongguoCaseQueryV1:
    return ZhongguoCaseQueryV1(
        case_kind=ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
        subject_character_id=SUBJECT_CHARACTER_ID,
        owner_character_id=owner_character_id,
        request_nonce=REQUEST_NONCE,
    )


def _frame(
    *, exact_open_date: bool = True, exact_due_date: bool = False
) -> dict[str, object]:
    due_date = (
        _available(DATE_RAW + 30)
        if exact_due_date
        else _unavailable("due_date_not_persisted_by_product")
    )
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
        "request_nonce": REQUEST_NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER_CHARACTER_ID,
        "subject_character_id": SUBJECT_CHARACTER_ID,
        "requested_owner_character_id": None,
        "case": {
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(SUBJECT_CHARACTER_ID),
            "cycle_serial": _available(3),
            "case_serial": _available(8),
            "state": _available(1),
            "active": _available(True),
            "revision": _available(2),
            "timeline_serial": _available(2),
            "feedback_revision": _available(2),
        },
        "policy": {
            "policy_id": _available("mechanism_039"),
            "choice": _available(1),
        },
        "operation": {
            "operation_id": _available(39),
            "operation_key": _available("roster_lock"),
            "hook": _available("roster_lock"),
            "pre_state": _available(1),
            "post_state": _available(1),
        },
        "receipt": {
            "status": "recorded",
            "key": _available("roster_lock"),
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "subject_character_id": _available(SUBJECT_CHARACTER_ID),
            "cycle_serial": _available(3),
            "case_serial": _available(8),
            "state": _available(1),
            "choice": _available(1),
        },
        "deadline": {
            "status": "pending",
            "target_character_id": _available(SUBJECT_CHARACTER_ID),
            "owner_character_id": _available(OWNER_CHARACTER_ID),
            "cycle_serial": _available(3),
            "case_serial": _available(8),
            "expected_state": _available(1),
            "days": _available(30),
            "pending": _available(True),
            "expired": _available(False),
            "open_date_raw": (
                _available(DATE_RAW)
                if exact_open_date
                else _unavailable("variable_absent")
            ),
            "due_date_raw": due_date,
            "on_due_operation": _available("resolve_pending_milestone"),
        },
        "readiness": {
            "player_binding_ready": True,
            "case_identity_ready": True,
            "policy_ready": True,
            "operation_ready": True,
            "receipt_ready": True,
            "deadline_identity_ready": True,
            "deadline_due_date_ready": exact_due_date,
            "same_frame_ready": True,
            "ready": exact_due_date,
        },
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _unavailable_frame(
    reason: str = "case_not_found",
) -> dict[str, object]:
    frame = _frame()
    frame["status"] = "unavailable"
    frame["requested_owner_character_id"] = OWNER_CHARACTER_ID
    frame["unavailable_reason"] = reason
    for group_name in ("case", "policy", "operation"):
        group = frame[group_name]
        assert isinstance(group, dict)
        for key in group:
            group[key] = _unavailable("case_unavailable")
    receipt = frame["receipt"]
    assert isinstance(receipt, dict)
    receipt["status"] = "unavailable"
    for key in set(receipt) - {"status"}:
        receipt[key] = _unavailable("case_unavailable")
    deadline = frame["deadline"]
    assert isinstance(deadline, dict)
    deadline["status"] = "unavailable"
    for key in set(deadline) - {"status"}:
        deadline[key] = _unavailable("case_unavailable")
    frame["readiness"] = {
        "player_binding_ready": True,
        "case_identity_ready": False,
        "policy_ready": False,
        "operation_ready": False,
        "receipt_ready": False,
        "deadline_identity_ready": False,
        "deadline_due_date_ready": False,
        "same_frame_ready": True,
        "ready": False,
    }
    return frame


def _response(
    *,
    frame: dict[str, object] | None = None,
    owner_character_id: int | None = OWNER_CHARACTER_ID,
) -> dict[str, object]:
    result = copy.deepcopy(frame if frame is not None else _frame())
    result.update(
        {
            "build": {
                "version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
                "exe_sha256": ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
            },
            "source": {
                "bridge_version": ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
                "game_adapter_id": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
                "backend_id": ZHONGGUO_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
                "consumer_id": ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
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
                "subject_character_id": SUBJECT_CHARACTER_ID,
                "owner_character_id": owner_character_id,
                "expected_revision": PUBLIC_REVISION,
            },
        }
    )
    return result


class ZhongguoCaseSnapshotV1ContractTests(unittest.TestCase):
    def test_step_round_trip_is_allowlisted_and_canonical(self) -> None:
        step = query_zhongguo_case_snapshot_v1_step(
            ZHONGGUO_B1_PERFORMANCE_CASE_KIND,
            SUBJECT_CHARACTER_ID,
            OWNER_CHARACTER_ID,
            REQUEST_NONCE,
        )
        self.assertEqual(
            parse_query_zhongguo_case_snapshot_v1_step(step),
            _query(OWNER_CHARACTER_ID),
        )

        step_prefix, nonce_hex = step.rsplit("-", 1)

        mutations = (
            step.replace(str(SUBJECT_CHARACTER_ID), f"0{SUBJECT_CHARACTER_ID}"),
            f"{step_prefix}-{nonce_hex.upper()}",
            step.replace("-b1-", "-b2-"),
            step + "00",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIsNone(
                    parse_query_zhongguo_case_snapshot_v1_step(mutation)
                )

    def test_native_frame_binds_exact_case_receipt_and_deadline(self) -> None:
        normalized = normalize_native_zhongguo_case_snapshot_v1(
            _frame(exact_due_date=True),
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(
            normalized["case"]["owner_character_id"]["value"],
            OWNER_CHARACTER_ID,
        )
        self.assertEqual(
            normalized["deadline"]["open_date_raw"]["value"], DATE_RAW
        )
        self.assertTrue(normalized["readiness"]["ready"])

    def test_absent_due_date_is_typed_and_keeps_gate_false(self) -> None:
        normalized = normalize_native_zhongguo_case_snapshot_v1(
            _frame(exact_due_date=False),
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        due = normalized["deadline"]["due_date_raw"]
        self.assertEqual(due["status"], "unavailable")
        self.assertEqual(
            due["unavailable_reason"], "due_date_not_persisted_by_product"
        )
        self.assertFalse(normalized["readiness"]["deadline_due_date_ready"])
        self.assertFalse(normalized["readiness"]["ready"])

        wrong_kind = _frame(exact_due_date=False)
        wrong_kind["deadline"]["open_date_raw"] = _unavailable(
            "value_type_mismatch"
        )
        normalized_wrong_kind = normalize_native_zhongguo_case_snapshot_v1(
            wrong_kind,
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )
        self.assertEqual(
            normalized_wrong_kind["deadline"]["open_date_raw"][
                "unavailable_reason"
            ],
            "value_type_mismatch",
        )

    def test_open_date_absence_is_typed_but_does_not_invent_due_date(self) -> None:
        normalized = normalize_native_zhongguo_case_snapshot_v1(
            _frame(exact_open_date=False, exact_due_date=True),
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertEqual(
            normalized["deadline"]["open_date_raw"]["unavailable_reason"],
            "variable_absent",
        )
        self.assertEqual(
            normalized["deadline"]["due_date_raw"]["value"], DATE_RAW + 30
        )
        self.assertTrue(normalized["readiness"]["deadline_due_date_ready"])

    def test_not_scheduled_is_a_complete_typed_negative_deadline(self) -> None:
        frame = _frame()
        deadline = frame["deadline"]
        assert isinstance(deadline, dict)
        deadline["status"] = "not_scheduled"
        for key in set(deadline) - {"status"}:
            deadline[key] = _unavailable(
                "not_applicable"
                if key in {"open_date_raw", "due_date_raw"}
                else "deadline_not_scheduled"
            )
        frame["readiness"]["deadline_due_date_ready"] = True
        frame["readiness"]["ready"] = True

        normalized = normalize_native_zhongguo_case_snapshot_v1(
            frame,
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertEqual(normalized["deadline"]["status"], "not_scheduled")
        self.assertTrue(normalized["readiness"]["deadline_identity_ready"])
        self.assertTrue(normalized["readiness"]["deadline_due_date_ready"])
        self.assertTrue(normalized["readiness"]["ready"])

    def test_receipt_inconsistency_keeps_exact_policy_but_not_operation(self) -> None:
        frame = _frame()
        operation = frame["operation"]
        receipt = frame["receipt"]
        assert isinstance(operation, dict)
        assert isinstance(receipt, dict)
        operation["pre_state"] = _unavailable("receipt_inconsistent")
        operation["post_state"] = _unavailable("receipt_inconsistent")
        receipt["status"] = "unavailable"
        for key in set(receipt) - {"status"}:
            receipt[key] = _unavailable("receipt_inconsistent")
        frame["readiness"]["operation_ready"] = False
        frame["readiness"]["receipt_ready"] = False
        frame["readiness"]["ready"] = False

        normalized = normalize_native_zhongguo_case_snapshot_v1(
            frame,
            expected_query=_query(),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertTrue(normalized["readiness"]["policy_ready"])
        self.assertFalse(normalized["readiness"]["operation_ready"])
        self.assertEqual(normalized["receipt"]["status"], "unavailable")

    def test_case_owner_subject_and_receipt_cross_bindings_are_strict(self) -> None:
        mutations = {
            "player_owner": lambda row: row["case"][
                "owner_character_id"
            ].__setitem__("value", OWNER_CHARACTER_ID + 1),
            "case_subject": lambda row: row["case"]["subject_character_id"].__setitem__(
                "value", SUBJECT_CHARACTER_ID + 1
            ),
            "owner_filter": lambda row: row.__setitem__(
                "requested_owner_character_id", OWNER_CHARACTER_ID + 1
            ),
            "receipt_case": lambda row: row["receipt"]["case_serial"].__setitem__(
                "value", 9
            ),
            "operation_key": lambda row: row["operation"]["operation_key"].__setitem__(
                "value", "arbitrary_read"
            ),
            "deadline_target": lambda row: row["deadline"][
                "target_character_id"
            ].__setitem__("value", SUBJECT_CHARACTER_ID + 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                expected_query = (
                    _query(OWNER_CHARACTER_ID + 1)
                    if label == "owner_filter"
                    else _query()
                )
                with self.assertRaises(ValueError):
                    normalize_native_zhongguo_case_snapshot_v1(
                        frame,
                        expected_query=expected_query,
                        expected_snapshot_revision=NATIVE_REVISION,
                        expected_date_raw=DATE_RAW,
                        expected_player_character_id=PLAYER_CHARACTER_ID,
                    )

    def test_unavailable_frame_never_publishes_an_actual_owner(self) -> None:
        frame = _unavailable_frame()
        response = _response(frame=frame, owner_character_id=None)
        normalized = normalize_zhongguo_case_snapshot_v1_response(
            response,
            expected_query=_query(OWNER_CHARACTER_ID),
            expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION,
            expected_native_revision=NATIVE_REVISION,
            expected_connection_generation=CONNECTION_GENERATION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertEqual(normalized["status"], "unavailable")
        self.assertEqual(normalized["unavailable_reason"], "case_not_found")
        self.assertIsNone(normalized["binding"]["owner_character_id"])

    def test_player_binding_mismatch_is_a_typed_top_level_result(self) -> None:
        frame = _unavailable_frame("player_binding_mismatch")
        frame["readiness"]["player_binding_ready"] = False
        normalized = normalize_native_zhongguo_case_snapshot_v1(
            frame,
            expected_query=_query(OWNER_CHARACTER_ID),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER_CHARACTER_ID,
        )

        self.assertEqual(
            normalized["unavailable_reason"], "player_binding_mismatch"
        )
        self.assertFalse(normalized["readiness"]["player_binding_ready"])

    def test_final_response_requires_every_exact_binding_mirror(self) -> None:
        response = _response()
        normalized = normalize_zhongguo_case_snapshot_v1_response(
            response,
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

        for path, value in (
            (("source", "connection_generation"), CONNECTION_GENERATION + 1),
            (("source", "game_adapter_id"), "wrong-adapter"),
            (("binding", "owner_character_id"), None),
            (("binding", "request_nonce"), "different"),
            (("build", "version"), "1.19.0.5"),
        ):
            with self.subTest(path=path):
                mutated = copy.deepcopy(response)
                mutated[path[0]][path[1]] = value
                with self.assertRaises(ValueError):
                    normalize_zhongguo_case_snapshot_v1_response(
                        mutated,
                        expected_query=_query(),
                        expected_snapshot_id=SNAPSHOT_ID,
                        expected_revision=PUBLIC_REVISION,
                        expected_native_revision=NATIVE_REVISION,
                        expected_connection_generation=CONNECTION_GENERATION,
                        expected_date_raw=DATE_RAW,
                        expected_player_character_id=PLAYER_CHARACTER_ID,
                    )


class ZhongguoCaseSnapshotV1SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_available_and_typed_due_date_unavailable_fixtures_validate(self) -> None:
        self.validator.validate(_response())
        self.validator.validate(_response(frame=_frame(exact_due_date=True)))
        self.validator.validate(
            _response(
                frame=_unavailable_frame("player_binding_mismatch"),
                owner_character_id=None,
            )
        )

    def test_schema_has_exact_contract_sets(self) -> None:
        deadline = self.schema["properties"]["deadline"]
        self.assertEqual(set(deadline["required"]), contract._DEADLINE_KEYS)
        self.assertEqual(set(deadline["properties"]), contract._DEADLINE_KEYS)
        self.assertIn("open_date_raw", deadline["required"])
        self.assertIn("due_date_raw", deadline["required"])
        self.assertEqual(
            set(
                self.schema["$defs"]["fieldUnavailableReason"]["enum"]
            ),
            contract._FIELD_UNAVAILABLE_REASONS,
        )
        self.assertEqual(
            set(
                self.schema["$defs"]["topLevelUnavailableReason"]["enum"]
            ),
            contract._TOP_LEVEL_UNAVAILABLE_REASONS,
        )
        provenance = self.schema["properties"]["provenance"]
        self.assertEqual(
            set(provenance["required"]), set(contract._PROVENANCE_VALUES)
        )
        self.assertEqual(
            set(provenance["properties"]), set(contract._PROVENANCE_VALUES)
        )

    def test_schema_requires_open_date_exact_provenance_and_typed_reasons(self) -> None:
        mutations = {
            "missing_open_date": lambda row: row["deadline"].pop(
                "open_date_raw"
            ),
            "unknown_field_reason": lambda row: row["deadline"][
                "due_date_raw"
            ].__setitem__("unavailable_reason", "anything"),
            "unknown_top_reason": lambda row: row.__setitem__(
                "unavailable_reason", "anything"
            ),
            "wrong_provenance": lambda row: row["provenance"].__setitem__(
                "variable_context_for_scope_rva", "0x0"
            ),
            "extra_provenance": lambda row: row["provenance"].__setitem__(
                "arbitrary_variable", "zg361_anything"
            ),
            "wrong_consumer": lambda row: row["source"].__setitem__(
                "consumer_id", "generic-variable-reader"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                row = _response(frame=_frame(exact_due_date=False))
                if label == "unknown_top_reason":
                    row = _response(
                        frame=_unavailable_frame(), owner_character_id=None
                    )
                mutate(row)
                with self.assertRaises(ValidationError):
                    self.validator.validate(row)


if __name__ == "__main__":
    unittest.main()
