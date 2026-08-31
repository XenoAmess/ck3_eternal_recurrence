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

from xar_autoplayer.bridge.zhongguo_workforce_normal_exit_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_ALLOWLIST_ID_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_BACKEND_ID_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_CASE_KIND_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_SOURCE_BACKEND_ID_V1,
    ZhongguoWorkforceNormalExitQueryV1,
    normalize_native_zhongguo_workforce_normal_exit_snapshot_v1,
    normalize_zhongguo_workforce_normal_exit_snapshot_v1_response,
    parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step,
    query_zhongguo_workforce_normal_exit_snapshot_v1_step,
    query_zhongguo_workforce_normal_exit_snapshot_v1_step_payload,
)


PLAYER = 100
OWNER = 200
CYCLE = 17
CASE = 17_075
FORMAL_CASE = 27_601
RECEIPT_ID = 1_707_515
RECEIPT_HASH = 9_361_075
NATIVE_REVISION = 94
PUBLIC_REVISION = 12
CONNECTION_GENERATION = 5
DATE_RAW = 777_777
NONCE = "wf-normal-exit:94"
SNAPSHOT_ID = "native-headless:workforce-normal-exit:94"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "zhongguo-workforce-normal-exit-snapshot-v1.schema.json"
)

PARTITION_KEYS = (
    "authorized",
    "available",
    "reserved",
    "occupied",
    "frozen",
    "reclaimed",
)
SOURCE_KEYS = (
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "route",
    "offer_gold",
    "receipt_serial",
    "object_owner_character_id",
    "object_subject_character_id",
    "object_cycle_serial",
    "object_receipt_case_serial",
    "object_route",
    "object_active",
    "object_consumed",
    "consumer_receipt_case_serial",
)
WORKFLOW_SCALAR_KEYS = (
    "pending",
    "pending_owner_character_id",
    "pending_subject_character_id",
    "pending_cycle_serial",
    "pending_case_serial",
    "state",
    "pending_hc_migration_authorized",
    "pending_slot_case_serial",
)
RECEIPT_SCALAR_KEYS = (
    "active",
    "sealed",
    "published",
    "consumed",
    "consumed_operation",
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "receipt_id",
    "receipt_hash",
    "hc_ledger_settled",
    "hc_destination_frozen",
    "hc_conservation_verified",
    "formal_hc_active_before",
    "formal_hc_active_after",
    "formal_hc_case_serial",
)
REHIRE_SCALAR_KEYS = (
    "state",
    "subject_character_id",
    "exit_owner_character_id",
    "exit_cycle_serial",
    "exit_case_serial",
    "exit_state",
    "exit_receipt_id",
    "exit_receipt_hash",
    "normal_exit_verified",
    "exit_hc_destination_frozen",
    "exit_hc_conservation_verified",
    "exit_formal_hc_active_before",
    "exit_formal_hc_active_after",
    "exit_formal_hc_case_serial",
)
READINESS_KEYS = (
    "player_subject_binding_ready",
    "owner_binding_ready",
    "source_object_ready",
    "pending_snapshot_ready",
    "current_hc_partition_ready",
    "migration_delta_ready",
    "sealed_receipt_ready",
    "rehire_capture_ready",
    "current_hc_matches_stage_ready",
    "lifecycle_ready",
    "same_frame_ready",
    "ready",
)

BEFORE = {
    "authorized": 10,
    "available": 2,
    "reserved": 1,
    "occupied": 5,
    "frozen": 1,
    "reclaimed": 1,
}
AFTER = {
    "authorized": 10,
    "available": 2,
    "reserved": 1,
    "occupied": 4,
    "frozen": 2,
    "reclaimed": 1,
}
LATER_VALID_HC = {
    "authorized": 10,
    "available": 3,
    "reserved": 1,
    "occupied": 3,
    "frozen": 2,
    "reclaimed": 1,
}


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str = "stage_not_reached") -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def partition(values: dict[str, int]) -> dict[str, object]:
    return {key: available(values[key]) for key in PARTITION_KEYS}


def unavailable_partition(reason: str = "stage_not_reached") -> dict[str, object]:
    return {key: unavailable(reason) for key in PARTITION_KEYS}


def source(*, post: bool) -> dict[str, object]:
    values: dict[str, object] = {
        "owner_character_id": OWNER,
        "subject_character_id": PLAYER,
        "cycle_serial": CYCLE,
        "case_serial": CASE,
        "state": 3 if post else 1,
        "route": 1,
        "offer_gold": 50,
        "receipt_serial": CASE,
        "object_owner_character_id": OWNER,
        "object_subject_character_id": PLAYER,
        "object_cycle_serial": CYCLE,
        "object_receipt_case_serial": CASE,
        "object_route": 1,
        "object_active": not post,
        "object_consumed": post,
    }
    result = {key: available(values[key]) for key in values}
    result["consumer_receipt_case_serial"] = (
        available(CASE) if post else unavailable("variable_absent")
    )
    return result


def unavailable_source(reason: str = "case_unavailable") -> dict[str, object]:
    return {key: unavailable(reason) for key in SOURCE_KEYS}


def workflow_offered() -> dict[str, object]:
    result = {key: unavailable() for key in WORKFLOW_SCALAR_KEYS}
    result["pending_hc_before"] = unavailable_partition()
    return result


def workflow_pending(*, state: int | None, migrating: bool = False) -> dict[str, object]:
    result = {
        "pending": available(True),
        "pending_owner_character_id": available(OWNER),
        "pending_subject_character_id": available(PLAYER),
        "pending_cycle_serial": available(CYCLE),
        "pending_case_serial": available(CASE),
        "state": unavailable("variable_absent") if state is None else available(state),
        "pending_hc_migration_authorized": (
            available(True) if migrating else unavailable("variable_absent")
        ),
        "pending_slot_case_serial": available(FORMAL_CASE),
        "pending_hc_before": partition(BEFORE),
    }
    return result


def workflow_sealed() -> dict[str, object]:
    result = {key: unavailable() for key in WORKFLOW_SCALAR_KEYS}
    result["state"] = available(4)
    result["pending_hc_before"] = unavailable_partition()
    return result


def current_hc(values: dict[str, int], *, formal_active: bool) -> dict[str, object]:
    return {
        "formal_active": available(formal_active),
        "formal_case_serial": available(FORMAL_CASE),
        "partition": partition(values),
    }


def unavailable_current_hc(reason: str = "case_unavailable") -> dict[str, object]:
    return {
        "formal_active": unavailable(reason),
        "formal_case_serial": unavailable(reason),
        "partition": unavailable_partition(reason),
    }


def sealed_receipt() -> dict[str, object]:
    values: dict[str, object] = {
        "active": True,
        "sealed": True,
        "published": True,
        "consumed": True,
        "consumed_operation": 75,
        "owner_character_id": OWNER,
        "subject_character_id": PLAYER,
        "cycle_serial": CYCLE,
        "case_serial": CASE,
        "state": 6,
        "receipt_id": RECEIPT_ID,
        "receipt_hash": RECEIPT_HASH,
        "hc_ledger_settled": True,
        "hc_destination_frozen": True,
        "hc_conservation_verified": True,
        "formal_hc_active_before": True,
        "formal_hc_active_after": False,
        "formal_hc_case_serial": FORMAL_CASE,
    }
    return {
        **{key: available(values[key]) for key in RECEIPT_SCALAR_KEYS},
        "hc_before": partition(BEFORE),
        "hc_after": partition(AFTER),
    }


def unavailable_receipt(reason: str = "stage_not_reached") -> dict[str, object]:
    return {
        **{key: unavailable(reason) for key in RECEIPT_SCALAR_KEYS},
        "hc_before": unavailable_partition(reason),
        "hc_after": unavailable_partition(reason),
    }


def captured_rehire() -> dict[str, object]:
    values: dict[str, object] = {
        "state": 1,
        "subject_character_id": PLAYER,
        "exit_owner_character_id": OWNER,
        "exit_cycle_serial": CYCLE,
        "exit_case_serial": CASE,
        "exit_state": 6,
        "exit_receipt_id": RECEIPT_ID,
        "exit_receipt_hash": RECEIPT_HASH,
        "normal_exit_verified": True,
        "exit_hc_destination_frozen": True,
        "exit_hc_conservation_verified": True,
        "exit_formal_hc_active_before": True,
        "exit_formal_hc_active_after": False,
        "exit_formal_hc_case_serial": FORMAL_CASE,
    }
    return {
        **{key: available(values[key]) for key in REHIRE_SCALAR_KEYS},
        "exit_hc_before": partition(BEFORE),
        "exit_hc_after": partition(AFTER),
    }


def unavailable_rehire(reason: str = "stage_not_reached") -> dict[str, object]:
    return {
        **{key: unavailable(reason) for key in REHIRE_SCALAR_KEYS},
        "exit_hc_before": unavailable_partition(reason),
        "exit_hc_after": unavailable_partition(reason),
    }


def readiness(stage: str, *, current_matches: bool = True) -> dict[str, bool]:
    values = {key: False for key in READINESS_KEYS}
    values.update(
        {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "source_object_ready": True,
            "pending_snapshot_ready": stage in {"pending", "accepted", "migrating"},
            "current_hc_partition_ready": True,
            "migration_delta_ready": stage in {"migrating", "sealed", "rehire"},
            "sealed_receipt_ready": stage in {"sealed", "rehire"},
            "rehire_capture_ready": stage == "rehire",
            "current_hc_matches_stage_ready": (
                False if stage == "offered" else current_matches
            ),
            "lifecycle_ready": True,
            "same_frame_ready": True,
            "ready": True,
        }
    )
    return values


def provenance() -> dict[str, object]:
    return {
        "game_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
        "executable_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
        "backend_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BACKEND_ID_V1,
        "consumer_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
        "allowlist_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_ALLOWLIST_ID_V1,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
        "subject_allowlist_count": 94,
        "owner_allowlist_count": 0,
        "query_scope": "paused_received_self_workforce_normal_exit_lifecycle",
    }


def frame(stage: str, *, later_hc_drift: bool = False) -> dict[str, object]:
    if stage not in {"offered", "pending", "accepted", "migrating", "sealed", "rehire"}:
        raise ValueError("unknown fixture stage")
    post = stage in {"accepted", "migrating", "sealed", "rehire"}
    if stage == "offered":
        flow = workflow_offered()
        live = current_hc(BEFORE, formal_active=True)
    elif stage == "pending":
        flow = workflow_pending(state=None)
        live = current_hc(BEFORE, formal_active=True)
    elif stage == "accepted":
        flow = workflow_pending(state=2)
        live = current_hc(BEFORE, formal_active=True)
    elif stage == "migrating":
        flow = workflow_pending(state=3, migrating=True)
        live = current_hc(AFTER, formal_active=False)
    else:
        flow = workflow_sealed()
        live = current_hc(
            LATER_VALID_HC if later_hc_drift else AFTER,
            formal_active=False,
        )
    lifecycle = {
        "offered": "pre",
        "pending": "pre",
        "accepted": "pre",
        "migrating": "migrating",
        "sealed": "sealed",
        "rehire": "rehire_captured",
    }[stage]
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CASE_KIND_V1,
        "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "subject_character_id": PLAYER,
        "requested_owner_character_id": OWNER,
        "lifecycle": lifecycle,
        "source": source(post=post),
        "workflow": flow,
        "current_hc": live,
        "receipt": (
            sealed_receipt() if stage in {"sealed", "rehire"} else unavailable_receipt()
        ),
        "rehire": captured_rehire() if stage == "rehire" else unavailable_rehire(),
        "readiness": readiness(
            stage,
            current_matches=not later_hc_drift,
        ),
        "unavailable_reason": None,
        "provenance": provenance(),
    }


def unavailable_frame(reason: str = "case_not_found") -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "case_kind": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CASE_KIND_V1,
        "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "subject_character_id": PLAYER,
        "requested_owner_character_id": OWNER,
        "lifecycle": "unavailable",
        "source": unavailable_source(),
        "workflow": {
            **{key: unavailable("case_unavailable") for key in WORKFLOW_SCALAR_KEYS},
            "pending_hc_before": unavailable_partition("case_unavailable"),
        },
        "current_hc": unavailable_current_hc(),
        "receipt": unavailable_receipt("case_unavailable"),
        "rehire": unavailable_rehire("case_unavailable"),
        "readiness": {key: False for key in READINESS_KEYS},
        "unavailable_reason": reason,
        "provenance": provenance(),
    }


def query() -> ZhongguoWorkforceNormalExitQueryV1:
    return ZhongguoWorkforceNormalExitQueryV1(OWNER, NONCE)


def response(native: dict[str, object]) -> dict[str, object]:
    return {
        **copy.deepcopy(native),
        "build": {
            "version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
            "exe_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
        },
        "bridge_source": {
            "bridge_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
            "game_adapter_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
            "backend_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_SOURCE_BACKEND_ID_V1,
            "consumer_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
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
            "subject_character_id": PLAYER,
            "owner_character_id": OWNER,
            "expected_revision": PUBLIC_REVISION,
        },
    }


def normalize_native(native: dict[str, object]) -> dict[str, object]:
    return normalize_native_zhongguo_workforce_normal_exit_snapshot_v1(
        native,
        expected_query=query(),
        expected_snapshot_revision=NATIVE_REVISION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER,
    )


def normalize_response(final: dict[str, object]) -> dict[str, object]:
    return normalize_zhongguo_workforce_normal_exit_snapshot_v1_response(
        final,
        expected_query=query(),
        expected_snapshot_id=SNAPSHOT_ID,
        expected_revision=PUBLIC_REVISION,
        expected_native_revision=NATIVE_REVISION,
        expected_connection_generation=CONNECTION_GENERATION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER,
    )


class WorkforceNormalExitSnapshotContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def assert_schema_valid(self, value: dict[str, object]) -> None:
        errors = sorted(self.validator.iter_errors(value), key=lambda item: list(item.path))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def test_capability_and_step_acl_round_trip(self) -> None:
        self.assertEqual(
            "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1",
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
        )
        encoded = query_zhongguo_workforce_normal_exit_snapshot_v1_step(OWNER, NONCE)
        parsed = parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(encoded)
        self.assertEqual(query(), parsed)
        self.assertEqual(
            {
                "step": QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
                "owner_character_id": OWNER,
                "request_nonce": NONCE,
            },
            query_zhongguo_workforce_normal_exit_snapshot_v1_step_payload(OWNER, NONCE),
        )
        for bad_owner in (True, 0, -1, 2**31):
            with self.subTest(owner=bad_owner), self.assertRaises(ValueError):
                query_zhongguo_workforce_normal_exit_snapshot_v1_step(bad_owner, NONCE)
        for bad_nonce in ("", "with space", "雪", "a" * 65):
            with self.subTest(nonce=bad_nonce), self.assertRaises(ValueError):
                query_zhongguo_workforce_normal_exit_snapshot_v1_step(OWNER, bad_nonce)
        for invalid_step in (
            None,
            QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
            f"{QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP}-0200-61",
            f"{QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP}-200-ABC0",
            f"{QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP}-200-00",
        ):
            with self.subTest(step=invalid_step):
                self.assertIsNone(
                    parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(
                        invalid_step
                    )
                )
        with self.assertRaises(TypeError):
            query_zhongguo_workforce_normal_exit_snapshot_v1_step_payload(
                OWNER, NONCE, subject_character_id=PLAYER  # type: ignore[call-arg]
            )

    def test_schema_accepts_all_lifecycle_responses_and_is_strict(self) -> None:
        for stage in ("offered", "pending", "accepted", "migrating", "sealed", "rehire"):
            with self.subTest(stage=stage):
                final = response(frame(stage))
                self.assert_schema_valid(final)
                self.assertEqual(frame(stage)["lifecycle"], normalize_response(final)["lifecycle"])
        extra = response(frame("sealed"))
        extra["variable_name"] = "zg361_ch_hc_occupied"
        with self.assertRaises(ValidationError):
            self.validator.validate(extra)

    def test_unavailable_is_typed_and_leak_free(self) -> None:
        native = unavailable_frame()
        normalized = normalize_native(native)
        self.assertEqual("unavailable", normalized["lifecycle"])
        self.assertFalse(normalized["readiness"]["ready"])
        final = response(native)
        self.assert_schema_valid(final)
        self.assertEqual("unavailable", normalize_response(final)["status"])

        leaked = unavailable_frame()
        leaked["source"]["state"] = available(1)
        with self.assertRaisesRegex(ValueError, "leaks lifecycle facts"):
            normalize_native(leaked)
        falsely_ready = unavailable_frame()
        falsely_ready["readiness"]["ready"] = True
        with self.assertRaisesRegex(ValueError, "leaks lifecycle facts"):
            normalize_native(falsely_ready)

    def test_pre_offered_pending_and_accepted_are_distinct_valid_substages(self) -> None:
        for stage, pending_ready, current_matches in (
            ("offered", False, False),
            ("pending", True, True),
            ("accepted", True, True),
        ):
            with self.subTest(stage=stage):
                normalized = normalize_native(frame(stage))
                self.assertEqual("pre", normalized["lifecycle"])
                self.assertEqual(
                    pending_ready,
                    normalized["readiness"]["pending_snapshot_ready"],
                )
                self.assertEqual(
                    current_matches,
                    normalized["readiness"]["current_hc_matches_stage_ready"],
                )

    def test_migrating_proves_the_only_occupied_to_frozen_delta(self) -> None:
        normalized = normalize_native(frame("migrating"))
        self.assertEqual("migrating", normalized["lifecycle"])
        self.assertTrue(normalized["readiness"]["migration_delta_ready"])
        self.assertFalse(normalized["readiness"]["sealed_receipt_ready"])

    def test_sealed_receipt_remains_valid_after_later_live_hc_drift(self) -> None:
        exact = normalize_native(frame("sealed"))
        self.assertTrue(exact["readiness"]["current_hc_matches_stage_ready"])
        drifted = normalize_native(frame("sealed", later_hc_drift=True))
        self.assertEqual("sealed", drifted["lifecycle"])
        self.assertTrue(drifted["readiness"]["sealed_receipt_ready"])
        self.assertTrue(drifted["readiness"]["ready"])
        self.assertFalse(drifted["readiness"]["current_hc_matches_stage_ready"])
        self.assert_schema_valid(response(frame("sealed", later_hc_drift=True)))

    def test_rehire_capture_must_copy_the_sealed_hc_provenance(self) -> None:
        normalized = normalize_native(frame("rehire"))
        self.assertEqual("rehire_captured", normalized["lifecycle"])
        self.assertTrue(normalized["readiness"]["rehire_capture_ready"])
        self.assertTrue(normalized["readiness"]["sealed_receipt_ready"])

    def test_partial_higher_stages_do_not_fall_back(self) -> None:
        partial_receipt = frame("migrating")
        partial_receipt["receipt"]["active"] = available(True)
        with self.assertRaisesRegex(ValueError, "higher sealed stage is partial"):
            normalize_native(partial_receipt)

        partial_rehire = frame("sealed")
        partial_rehire["rehire"]["state"] = available(1)
        with self.assertRaisesRegex(ValueError, "higher rehire stage is partial"):
            normalize_native(partial_rehire)

    def test_cross_stage_receipt_collision_is_rejected(self) -> None:
        collision = frame("rehire")
        collision["rehire"]["exit_receipt_id"] = available(RECEIPT_ID + 1)
        with self.assertRaisesRegex(ValueError, "does not preserve sealed provenance"):
            normalize_native(collision)

        case_collision = frame("rehire")
        case_collision["rehire"]["exit_case_serial"] = available(CASE + 1)
        with self.assertRaisesRegex(ValueError, "does not preserve sealed provenance"):
            normalize_native(case_collision)

    def test_partition_conservation_and_delta_fail_closed(self) -> None:
        bad_pending = frame("pending")
        bad_pending["workflow"]["pending_hc_before"]["authorized"] = available(11)
        with self.assertRaisesRegex(ValueError, "pending snapshot"):
            normalize_native(bad_pending)

        bad_migration = frame("migrating")
        bad_migration["current_hc"]["partition"]["occupied"] = available(3)
        bad_migration["current_hc"]["partition"]["available"] = available(3)
        with self.assertRaisesRegex(ValueError, "occupied-to-frozen delta"):
            normalize_native(bad_migration)

        bad_receipt = frame("sealed")
        bad_receipt["receipt"]["hc_after"]["frozen"] = available(3)
        bad_receipt["receipt"]["hc_after"]["available"] = available(1)
        with self.assertRaisesRegex(ValueError, "receipt is inconsistent"):
            normalize_native(bad_receipt)

        negative = frame("offered")
        negative["current_hc"]["partition"]["reclaimed"] = available(-1)
        negative["current_hc"]["partition"]["available"] = available(4)
        with self.assertRaisesRegex(ValueError, "live HC partition"):
            normalize_native(negative)

    def test_owner_subject_and_cross_stage_identity_bindings(self) -> None:
        matrices = (
            ("source_owner", "offered", ("source", "owner_character_id"), OWNER + 1),
            ("source_subject", "offered", ("source", "subject_character_id"), PLAYER + 1),
            ("object_case", "offered", ("source", "object_receipt_case_serial"), CASE + 1),
            ("pending_case", "pending", ("workflow", "pending_case_serial"), CASE + 1),
            ("receipt_cycle", "sealed", ("receipt", "cycle_serial"), CYCLE + 1),
            ("rehire_owner", "rehire", ("rehire", "exit_owner_character_id"), OWNER + 1),
        )
        for label, stage, (group, key), value in matrices:
            with self.subTest(label=label):
                native = frame(stage)
                native[group][key] = available(value)
                with self.assertRaises(ValueError):
                    normalize_native(native)

        self_bound = frame("offered")
        self_bound["source"]["owner_character_id"] = available(PLAYER)
        self_bound["source"]["object_owner_character_id"] = available(PLAYER)
        with self.assertRaisesRegex(ValueError, "canonical route-A tuple"):
            normalize_native(self_bound)

    def test_readiness_is_recomputed_for_every_lifecycle(self) -> None:
        for stage in ("offered", "pending", "accepted", "migrating", "sealed", "rehire"):
            with self.subTest(stage=stage):
                native = frame(stage)
                native["readiness"]["ready"] = False
                with self.assertRaisesRegex(ValueError, "readiness"):
                    normalize_native(native)
        wrong_label = frame("rehire")
        wrong_label["lifecycle"] = "sealed"
        with self.assertRaisesRegex(ValueError, "highest complete stage"):
            normalize_native(wrong_label)

    def test_response_build_source_and_binding_are_exact(self) -> None:
        final = response(frame("sealed"))
        self.assertEqual("sealed", normalize_response(final)["lifecycle"])
        mutations = (
            ("build", "version", "1.19.0.5"),
            ("bridge_source", "consumer_id", "wrong-consumer"),
            ("bridge_source", "revision", PUBLIC_REVISION + 1),
            ("binding", "owner_character_id", OWNER + 1),
            ("binding", "subject_character_id", PLAYER + 1),
            ("binding", "expected_revision", PUBLIC_REVISION + 1),
            ("binding", "snapshot_id", "wrong-snapshot"),
        )
        for group, key, value in mutations:
            with self.subTest(group=group, key=key):
                changed = response(frame("sealed"))
                changed[group][key] = value
                with self.assertRaises(ValueError):
                    normalize_response(changed)

    def test_exact_shape_typed_fields_and_provenance_are_enforced(self) -> None:
        extra_source = frame("offered")
        extra_source["source"]["variable_name"] = unavailable()
        with self.assertRaisesRegex(ValueError, "exactly the v1 fields"):
            normalize_native(extra_source)

        bad_bool = frame("offered")
        bad_bool["source"]["object_active"] = available(1)
        with self.assertRaisesRegex(ValueError, "must be boolean"):
            normalize_native(bad_bool)

        bad_character = frame("offered")
        bad_character["source"]["owner_character_id"] = available(0)
        with self.assertRaisesRegex(ValueError, "positive character id"):
            normalize_native(bad_character)

        bad_reason = frame("offered")
        bad_reason["workflow"]["state"] = unavailable("invented")
        with self.assertRaisesRegex(ValueError, "typed unavailability"):
            normalize_native(bad_reason)

        bad_allowlist = frame("offered")
        bad_allowlist["provenance"]["subject_allowlist_count"] = 93
        with self.assertRaisesRegex(ValueError, "frozen exact build"):
            normalize_native(bad_allowlist)


if __name__ == "__main__":
    unittest.main()
