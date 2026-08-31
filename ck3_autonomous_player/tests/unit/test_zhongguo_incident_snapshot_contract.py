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

from xar_autoplayer.bridge.zhongguo_incident_snapshot_contract import (
    ZHONGGUO_INCIDENT_KIND_V1,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoIncidentQueryV1,
    normalize_native_zhongguo_incident_snapshot_v1,
    normalize_zhongguo_incident_snapshot_v1_response,
    parse_query_zhongguo_incident_snapshot_v1_step,
    query_zhongguo_incident_snapshot_v1_step,
)


OWNER = 200
PLAYER = 300
REVISION = 41
DATE_RAW = 53223936
NONCE = "incident.batch-01"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "zhongguo-incident-snapshot-v1.schema.json"
SNAPSHOT_ID = "native:41"
PUBLIC_REVISION = 19
CONNECTION_GENERATION = 3

PROBE_KEYS = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "probe_serial",
    "result",
    "source_kind",
    "consequence_kind",
}
RESOURCE_KEYS = {
    "subject_personal_gold_q100000",
    "manager_treasury_q100000",
    "capital_control_q100000",
}
NA_KEYS = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "reason",
    "probe_serial",
    "receipt_serial",
    "applicable",
    "kpi_staged",
}
INCIDENT_KEYS = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "revision",
    "incident_serial",
    "source_kind",
    "consequence_kind",
    "final_score",
    "applicable",
    "kpi_staged",
}
KPI_KEYS = {
    "pending",
    "consumed",
    "owner_character_id",
    "subject_character_id",
    "origin_cycle",
    "due_cycle",
    "due_offset",
    "case_serial",
    "state",
    "score",
    "incident_serial",
    "source_kind",
    "consequence_kind",
    "receipt_serial",
    "consumed_owner_character_id",
    "consumed_subject_character_id",
    "consumed_origin_cycle",
    "consumed_due_cycle",
    "consumed_cycle",
    "consumed_case_serial",
    "consumed_score",
    "consumed_incident_serial",
}


def available(value: int) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def query(profile: str) -> ZhongguoIncidentQueryV1:
    return ZhongguoIncidentQueryV1(OWNER, profile, NONCE)


def provenance() -> dict[str, object]:
    return {
        "game_version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
        "backend_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "variable_identifier_table_rva": "0x3B971A0",
        "variable_identifier_lookup_rva": "0x3B97020",
        "variable_identifier_name_rva": "0x3B97090",
        "character_storage_slot_rva": "0x570C130",
        "manager_treasury_source": "not_recorded_by_mod",
    }


def readiness(*, kpi: bool = True) -> dict[str, bool]:
    # resource_snapshot_ready stays false until the mod freezes manager treasury.
    return {
        "player_subject_binding_ready": True,
        "owner_binding_ready": True,
        "profile_binding_ready": True,
        "probe_ready": True,
        "terminal_ready": True,
        "resource_snapshot_ready": False,
        "kpi_state_ready": kpi,
        "same_frame_ready": True,
        "ready": False,
    }


def base(profile: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_INCIDENT_KIND_V1,
        "profile": profile,
        "request_nonce": NONCE,
        "snapshot_revision": REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "subject_character_id": PLAYER,
        "requested_owner_character_id": OWNER,
        "probe": {},
        "resources": {
            "subject_personal_gold_q100000": available(-125_000),
            "manager_treasury_q100000": unavailable("not_recorded_by_mod"),
            "capital_control_q100000": available(4_500_000),
        },
        "terminal": {},
        "kpi": {},
        "readiness": readiness(),
        "unavailable_reason": None,
        "provenance": provenance(),
    }


def kpi_not_staged() -> dict[str, object]:
    return {
        "disposition": "not_staged",
        **{key: unavailable("not_applicable") for key in KPI_KEYS},
    }


def na_frame(profile: str = "x") -> dict[str, object]:
    frame = base(profile)
    frame["probe"] = {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(PLAYER),
        "cycle_serial": available(7),
        "probe_serial": available(12),
        "result": available(0),
        "source_kind": available(0),
        "consequence_kind": available(0),
    }
    frame["terminal"] = {
        "kind": "na",
        "na": {
            "owner_character_id": available(OWNER),
            "subject_character_id": available(PLAYER),
            "cycle_serial": available(7),
            "reason": available(1),
            "probe_serial": available(12),
            "receipt_serial": available(3),
            "applicable": available(0),
            "kpi_staged": available(0),
        },
        "incident": None,
    }
    frame["kpi"] = kpi_not_staged()
    return frame


def incident_frame(profile: str = "x", disposition: str = "pending") -> dict[str, object]:
    state = 8 if profile == "x" else 6
    frame = base(profile)
    frame["probe"] = {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(PLAYER),
        "cycle_serial": available(7),
        "probe_serial": available(12),
        "result": available(1),
        "source_kind": available(3),
        "consequence_kind": available(2),
    }
    frame["terminal"] = {
        "kind": "incident",
        "na": None,
        "incident": {
            "owner_character_id": available(OWNER),
            "subject_character_id": available(PLAYER),
            "cycle_serial": available(7),
            "case_serial": available(91),
            "state": available(state),
            "revision": available(15),
            "incident_serial": available(4),
            "source_kind": available(3),
            "consequence_kind": available(2),
            "final_score": available(2),
            "applicable": available(1),
            "kpi_staged": available(1),
        },
    }
    kpi = {
        "disposition": disposition,
        "pending": available(1 if disposition == "pending" else 0),
        "consumed": available(0 if disposition == "pending" else 1),
        "owner_character_id": available(OWNER),
        "subject_character_id": available(PLAYER),
        "origin_cycle": available(7),
        "due_cycle": available(8),
        "due_offset": available(1),
        "case_serial": available(91),
        "state": available(state),
        "score": available(2),
        "incident_serial": available(4),
        "source_kind": available(3),
        "consequence_kind": available(2),
    }
    receipt = {
        "receipt_serial": 5,
        "consumed_owner_character_id": OWNER,
        "consumed_subject_character_id": PLAYER,
        "consumed_origin_cycle": 7,
        "consumed_due_cycle": 8,
        "consumed_cycle": 8,
        "consumed_case_serial": 91,
        "consumed_score": 2,
        "consumed_incident_serial": 4,
    }
    for key, value in receipt.items():
        kpi[key] = (
            unavailable("not_yet_consumed")
            if disposition == "pending"
            else available(value)
        )
    frame["kpi"] = kpi
    return frame


def normalize(frame: dict[str, object], profile: str) -> dict[str, object]:
    return normalize_native_zhongguo_incident_snapshot_v1(
        frame,
        expected_query=query(profile),
        expected_snapshot_revision=REVISION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER,
    )


def response(frame: dict[str, object], profile: str) -> dict[str, object]:
    return {
        **copy.deepcopy(frame),
        "build": {
            "version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
            "exe_sha256": ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
        },
        "source": {
            "bridge_version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_BRIDGE_VERSION,
            "game_adapter_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_ADAPTER_ID,
            "backend_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_SOURCE_BACKEND_ID,
            "consumer_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
            "connection_generation": CONNECTION_GENERATION,
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": PLAYER,
        },
        "binding": {
            "request_nonce": NONCE,
            "profile": profile,
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": REVISION,
            "connection_generation": CONNECTION_GENERATION,
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": PLAYER,
            "subject_character_id": PLAYER,
            "owner_character_id": OWNER,
            "expected_revision": PUBLIC_REVISION,
        },
    }


class ZhongguoIncidentSnapshotContractTests(unittest.TestCase):
    def test_query_round_trip_has_fixed_profile_not_variable_name(self) -> None:
        for profile in ("x", "y", "z"):
            with self.subTest(profile=profile):
                step = query_zhongguo_incident_snapshot_v1_step(
                    OWNER, profile, NONCE
                )
                self.assertEqual(
                    parse_query_zhongguo_incident_snapshot_v1_step(step),
                    query(profile),
                )
        for malformed in (
            f"query-zhongguo-incident-snapshot-v1-{OWNER}-q-00",
            f"query-zhongguo-incident-snapshot-v1-{OWNER}-x-zz",
            f"query-zhongguo-incident-snapshot-v1-0-x-00",
        ):
            self.assertIsNone(
                parse_query_zhongguo_incident_snapshot_v1_step(malformed)
            )

    def test_exact_na_union_for_all_profiles(self) -> None:
        for profile in ("x", "y", "z"):
            normalized = normalize(na_frame(profile), profile)
            self.assertEqual(normalized["terminal"]["kind"], "na")
            self.assertEqual(normalized["kpi"]["disposition"], "not_staged")
            self.assertFalse(normalized["readiness"]["ready"])

    def test_pending_and_consumed_incident_join_terminal(self) -> None:
        for profile in ("x", "y", "z"):
            for disposition in ("pending", "consumed"):
                with self.subTest(profile=profile, disposition=disposition):
                    normalized = normalize(
                        incident_frame(profile, disposition), profile
                    )
                    self.assertEqual(
                        normalized["terminal"]["kind"], "incident"
                    )
                    self.assertEqual(
                        normalized["kpi"]["disposition"], disposition
                    )

    def test_manager_treasury_gap_is_typed_never_zero_filled(self) -> None:
        frame = na_frame()
        normalized = normalize(frame, "x")
        self.assertEqual(
            normalized["resources"]["manager_treasury_q100000"],
            unavailable("not_recorded_by_mod"),
        )
        forged = copy.deepcopy(frame)
        forged["resources"]["manager_treasury_q100000"] = available(0)
        forged["readiness"]["resource_snapshot_ready"] = True
        forged["readiness"]["ready"] = True
        with self.assertRaises(ValueError):
            normalize(forged, "x")

    def test_na_and_incident_cross_arm_or_cross_profile_are_rejected(self) -> None:
        cross_arm = na_frame()
        cross_arm["terminal"]["incident"] = {
            key: available(1) for key in INCIDENT_KEYS
        }
        wrong_state = incident_frame("y")
        wrong_state["terminal"]["incident"]["state"] = available(8)
        stale_probe = incident_frame("x")
        stale_probe["terminal"]["incident"]["cycle_serial"] = available(6)
        for frame, profile in (
            (cross_arm, "x"),
            (wrong_state, "y"),
            (stale_probe, "x"),
        ):
            with self.subTest(profile=profile):
                with self.assertRaises(ValueError):
                    normalize(frame, profile)

    def test_na_requires_positive_receipt_and_zero_source_consequence(self) -> None:
        for mutate in (
            lambda frame: frame["terminal"]["na"].__setitem__(
                "receipt_serial", available(0)
            ),
            lambda frame: frame["probe"].__setitem__(
                "source_kind", available(3)
            ),
            lambda frame: frame["terminal"]["na"].__setitem__(
                "kpi_staged", available(1)
            ),
        ):
            frame = na_frame()
            mutate(frame)
            with self.assertRaises(ValueError):
                normalize(frame, "x")

    def test_kpi_cross_case_and_incomplete_consumed_receipt_are_rejected(self) -> None:
        cross_case = incident_frame("x", "pending")
        cross_case["kpi"]["case_serial"] = available(92)
        missing_receipt = incident_frame("x", "consumed")
        missing_receipt["kpi"]["receipt_serial"] = unavailable(
            "variable_absent"
        )
        for frame in (cross_case, missing_receipt):
            with self.assertRaises(ValueError):
                normalize(frame, "x")

    def test_final_response_binds_profile_source_and_actual_owner(self) -> None:
        normalized = normalize_zhongguo_incident_snapshot_v1_response(
            response(incident_frame("z", "pending"), "z"),
            expected_query=query("z"),
            expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION,
            expected_native_revision=REVISION,
            expected_connection_generation=CONNECTION_GENERATION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertEqual(normalized["binding"]["profile"], "z")
        self.assertEqual(normalized["binding"]["owner_character_id"], OWNER)

    def test_schema_accepts_exact_union_and_rejects_arbitrary_surface(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.validate(response(na_frame(), "x"))
        validator.validate(response(incident_frame("x", "consumed"), "x"))
        extra = response(na_frame(), "x")
        extra["variable_name"] = "gold"
        with self.assertRaises(ValidationError):
            validator.validate(extra)


if __name__ == "__main__":
    unittest.main()
