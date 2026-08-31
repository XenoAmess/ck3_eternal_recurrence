from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from xar_autoplayer.bridge.zhongguo_workforce_collective_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZhongguoWorkforceCollectiveQueryV1,
    normalize_native_zhongguo_workforce_collective_snapshot_v1,
    normalize_zhongguo_workforce_collective_snapshot_v1_response,
    parse_query_zhongguo_workforce_collective_snapshot_v1_step,
    query_zhongguo_workforce_collective_snapshot_v1_step,
)


OWNER = 200
PLAYER = 100
CYCLE = 40
CASE = 36040
NATIVE_REVISION = 71
PUBLIC_REVISION = 33
DATE_RAW = 9001
NONCE = "wf.case-1"
SNAPSHOT_ID = "paused-workforce-fixture"


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def unavailable_group(keys: tuple[str, ...], reason: str) -> dict[str, object]:
    return {key: unavailable(reason) for key in keys}


CASE_KEYS = ("owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "state", "active", "revision")
RECEIPT_KEYS = ("owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "state", "choice")
COLLECTIVE_KEYS = (
    "submission_active", "submission_sealed", "submission_consumed",
    "owner_character_id", "subject_character_id", "cycle_serial", "case_serial",
    "state", "collective_case_serial", "submitted_cycle_serial", "cohort_count",
    "settlement_id", "settlement_hash", "settled", "route", "total_members",
    "total_quota", "forced_count", "exception_count", "manager_cost_total",
)
COHORT_KEYS = (
    "cohort_id", "manager_character_id", "member_count", "member_hash",
    "quota", "forced_count", "exception_count", "manager_cost",
    "partition_verified", "approval_verified", "b1_cycle_serial",
    "b1_case_serial", "b1_source_id", "b1_source_hash", "mg_cycle_serial",
    "mg_case_serial", "mg_snapshot_source_serial", "mg_snapshot_revision",
)
DEBT_KEYS = ("owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "state", "open", "consumed", "due_cycle_serial")
HISTORY_KEYS = ("owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "m357_receipt_id", "m357_receipt_hash", "m358_receipt_id", "m358_receipt_hash", "m359_receipt_id", "m359_receipt_hash")
CHARTER_KEYS = (
    "evidence_count", "evidence_ready", "evidence_consumed", "owner_character_id",
    "subject_character_id", "cycle_serial", "case_serial", "state",
    "prepared_report_id", "prepared_charter_id", "previous_charter_id",
    "previous_version", "adopted_cycle_serial", "effective_cycle_serial",
    "portfolio_status", "portfolio_closed", "terminal_history_accruing",
    "portfolio_history_cycle_count", "terminal_success",
)
READINESS_KEYS = (
    "player_subject_binding_ready", "owner_binding_ready", "case_identity_ready",
    "m360_receipt_projection_ready", "collective_lifecycle_ready",
    "cohort_identity_ready", "cohort_conservation_ready",
    "route_conservation_ready", "history_ledger_ready", "history_order_ready",
    "three_cycle_ready", "charter_gate_lifecycle_ready", "same_frame_ready", "ready",
)


def query() -> ZhongguoWorkforceCollectiveQueryV1:
    return ZhongguoWorkforceCollectiveQueryV1(OWNER, NONCE)


def cohort(index: int, route: int) -> dict[str, object]:
    quota = (1, 2, 1)[index]
    values = {
        "cohort_id": index + 10, "manager_character_id": 300 + index,
        "member_count": (8, 9, 7)[index], "member_hash": 800 + index,
        "quota": quota,
        "forced_count": 0 if route == 1 else quota,
        "exception_count": quota if route == 1 else 0,
        "manager_cost": quota if route == 1 else 0,
        "partition_verified": True, "approval_verified": route == 1,
        "b1_cycle_serial": CYCLE - 1, "b1_case_serial": 700 + index,
        "b1_source_id": 800 + index, "b1_source_hash": 900 + index,
        "mg_cycle_serial": CYCLE - 1, "mg_case_serial": 1000 + index,
        "mg_snapshot_source_serial": 1100 + index,
        "mg_snapshot_revision": 1200 + index,
    }
    return {key: available(values[key]) for key in COHORT_KEYS}


def history_slot(index: int) -> dict[str, object]:
    base = 2000 + index * 20
    values = {
        "owner_character_id": OWNER, "subject_character_id": PLAYER,
        "cycle_serial": CYCLE - 2 + index, "case_serial": CASE - 2 + index,
        "m357_receipt_id": base + 1, "m357_receipt_hash": base + 2,
        "m358_receipt_id": base + 3, "m358_receipt_hash": base + 4,
        "m359_receipt_id": base + 5, "m359_receipt_hash": base + 6,
    }
    return {key: available(values[key]) for key in HISTORY_KEYS}


def charter(status: str) -> dict[str, object]:
    values = {
        "evidence_count": 3, "evidence_ready": status == "ready",
        "evidence_consumed": status == "consumed", "owner_character_id": OWNER,
        "subject_character_id": PLAYER, "cycle_serial": CYCLE,
        "case_serial": CASE, "state": 5, "prepared_report_id": 91,
        "prepared_charter_id": 92, "previous_charter_id": 0,
        "previous_version": 0, "adopted_cycle_serial": CYCLE,
        "effective_cycle_serial": CYCLE + 1, "portfolio_status": 2,
        "portfolio_closed": False, "terminal_history_accruing": True,
        "portfolio_history_cycle_count": 3, "terminal_success": False,
    }
    return {"status": status, **{key: available(values[key]) for key in CHARTER_KEYS}}


def frame(route: int = 1, history_count: int = 3, charter_status: str = "consumed") -> dict[str, object]:
    case_values = {
        "owner_character_id": OWNER, "subject_character_id": PLAYER,
        "cycle_serial": CYCLE, "case_serial": CASE, "state": 5,
        "active": True, "revision": 8,
    }
    receipt_values = {
        "owner_character_id": OWNER, "subject_character_id": PLAYER,
        "cycle_serial": CYCLE, "case_serial": CASE, "state": 4, "choice": route,
    }
    if route in (1, 2):
        cohorts = [cohort(index, route) for index in range(3)]
        totals = {key: sum(item[key]["value"] for item in cohorts) for key in ("member_count", "quota", "forced_count", "exception_count", "manager_cost")}
        collective_values = {
            "submission_active": False, "submission_sealed": True,
            "submission_consumed": True, "owner_character_id": OWNER,
            "subject_character_id": PLAYER, "cycle_serial": CYCLE,
            "case_serial": CASE, "state": 4, "collective_case_serial": CASE,
            "submitted_cycle_serial": CYCLE, "cohort_count": 3,
            "settlement_id": 501, "settlement_hash": 502, "settled": True,
            "route": route, "total_members": totals["member_count"],
            "total_quota": totals["quota"], "forced_count": totals["forced_count"],
            "exception_count": totals["exception_count"],
            "manager_cost_total": totals["manager_cost"],
        }
        collective = {"phase": "route_a_exception" if route == 1 else "route_b_forced", **{key: available(collective_values[key]) for key in COLLECTIVE_KEYS}}
        debt = unavailable_group(DEBT_KEYS, "not_applicable")
    else:
        cohorts = [unavailable_group(COHORT_KEYS, "not_applicable") for _ in range(3)]
        collective = {"phase": "route_c_debt", **unavailable_group(COLLECTIVE_KEYS, "not_applicable")}
        debt_values = {
            "owner_character_id": OWNER, "subject_character_id": PLAYER,
            "cycle_serial": CYCLE, "case_serial": CASE, "state": 4,
            "open": True, "consumed": False, "due_cycle_serial": CYCLE + 1,
        }
        debt = {key: available(debt_values[key]) for key in DEBT_KEYS}
    if history_count == 0:
        history = {
            "status": "empty", "count": unavailable("variable_absent"),
            "effective_count": 0,
            "slots": [unavailable_group(HISTORY_KEYS, "lifecycle_not_reached") for _ in range(3)],
        }
        gate = {"status": "not_eligible", **unavailable_group(CHARTER_KEYS, "lifecycle_not_reached")}
    else:
        slots = [history_slot(index) if index < history_count else unavailable_group(HISTORY_KEYS, "lifecycle_not_reached") for index in range(3)]
        history = {"status": "three_cycle" if history_count == 3 else "partial", "count": available(history_count), "effective_count": history_count, "slots": slots}
        gate = charter(charter_status) if history_count == 3 else {"status": "not_eligible", **unavailable_group(CHARTER_KEYS, "lifecycle_not_reached")}
    readiness = {key: True for key in READINESS_KEYS}
    readiness["three_cycle_ready"] = history_count == 3
    return {
        "schema_version": 1, "status": "available",
        "case_kind": "zhongguo.workforce-collective", "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
        "paused": True, "player_character_id": PLAYER,
        "subject_character_id": PLAYER, "requested_owner_character_id": OWNER,
        "al_case": {key: available(case_values[key]) for key in CASE_KEYS},
        "m360_receipt": {key: available(receipt_values[key]) for key in RECEIPT_KEYS},
        "collective": collective, "cohorts": cohorts, "route_c_debt": debt,
        "history": history, "charter_gate": gate, "readiness": readiness,
        "unavailable_reason": None,
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256,
            "backend_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID,
            "consumer_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
            "allowlist_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID,
            "variable_context_for_scope_rva": "0x3329A40",
            "variable_identifier_table_rva": "0x3B971A0",
            "variable_identifier_lookup_rva": "0x3B97020",
            "variable_identifier_name_rva": "0x3B97090",
            "character_storage_slot_rva": "0x570C130",
            "subject_allowlist_count": 144, "owner_allowlist_count": 31,
            "query_scope": "paused_received_self_al_case_plus_owner_rolling_three_cycle",
        },
    }


def response(native: dict[str, object]) -> dict[str, object]:
    return {
        **copy.deepcopy(native),
        "build": {"version": "1.19.0.6", "exe_sha256": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256},
        "source": {
            "bridge_version": "0.1.0", "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
            "backend_id": "native-headless", "consumer_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
            "connection_generation": 4, "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW, "paused": True, "player_character_id": PLAYER,
        },
        "binding": {
            "request_nonce": NONCE, "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
            "connection_generation": 4, "date_raw": DATE_RAW, "paused": True,
            "player_character_id": PLAYER, "subject_character_id": PLAYER,
            "owner_character_id": OWNER, "expected_revision": PUBLIC_REVISION,
        },
    }


def normalize(value: dict[str, object]) -> dict[str, object]:
    return normalize_native_zhongguo_workforce_collective_snapshot_v1(
        value, expected_query=query(), expected_snapshot_revision=NATIVE_REVISION,
        expected_date_raw=DATE_RAW, expected_player_character_id=PLAYER,
    )


class WorkforceCollectiveContractTests(unittest.TestCase):
    def test_step_surface_contains_only_owner_filter_and_nonce(self) -> None:
        step = query_zhongguo_workforce_collective_snapshot_v1_step(OWNER, NONCE)
        self.assertEqual(parse_query_zhongguo_workforce_collective_snapshot_v1_step(step), query())
        self.assertEqual(QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY, "game.command.query-zhongguo-workforce-collective-snapshot-v1")
        self.assertNotIn("subject", step)
        self.assertNotIn("zg361_", step)
        for malformed in (
            "query-zhongguo-workforce-collective-snapshot-v1-0-00",
            "query-zhongguo-workforce-collective-snapshot-v1-0200-00",
            "query-zhongguo-workforce-collective-snapshot-v1-200-0",
            "query-zhongguo-workforce-collective-snapshot-v1-200-zz",
        ):
            self.assertIsNone(parse_query_zhongguo_workforce_collective_snapshot_v1_step(malformed))

    def test_routes_a_b_and_c_conserve_their_distinct_costs(self) -> None:
        route_a = normalize(frame(1))
        route_b = normalize(frame(2))
        route_c = normalize(frame(3))
        self.assertEqual(route_a["collective"]["exception_count"]["value"], 4)
        self.assertEqual(route_a["collective"]["manager_cost_total"]["value"], 4)
        self.assertEqual(route_b["collective"]["forced_count"]["value"], 4)
        self.assertEqual(route_b["collective"]["manager_cost_total"]["value"], 0)
        self.assertEqual(route_c["route_c_debt"]["due_cycle_serial"]["value"], CYCLE + 1)

    def test_three_cycle_receipts_are_ordered_distinct_and_charter_consumed(self) -> None:
        value = normalize(frame(1, 3, "consumed"))
        self.assertTrue(value["readiness"]["three_cycle_ready"])
        self.assertFalse(value["charter_gate"]["evidence_ready"]["value"])
        self.assertTrue(value["charter_gate"]["evidence_consumed"]["value"])
        for mutation in ("order", "receipt", "tail"):
            broken = frame()
            if mutation == "order":
                broken["history"]["slots"][1]["cycle_serial"] = available(CYCLE - 3)
            elif mutation == "receipt":
                broken["history"]["slots"][0]["m358_receipt_id"] = copy.deepcopy(broken["history"]["slots"][0]["m357_receipt_id"])
            else:
                broken["history"]["slots"][2]["case_serial"] = available(CASE - 1)
            with self.assertRaisesRegex(ValueError, "history"):
                normalize(broken)

    def test_empty_history_keeps_typed_absence_and_effective_zero(self) -> None:
        value = normalize(frame(3, 0))
        self.assertEqual(value["history"]["count"]["unavailable_reason"], "variable_absent")
        self.assertEqual(value["history"]["effective_count"], 0)
        fabricated = frame(3, 0)
        fabricated["history"]["count"] = available(0)
        with self.assertRaisesRegex(ValueError, "history"):
            normalize(fabricated)

    def test_collective_cohort_and_charter_lifecycle_mutations_fail(self) -> None:
        mutations = []
        duplicate_manager = frame()
        duplicate_manager["cohorts"][1]["manager_character_id"] = copy.deepcopy(duplicate_manager["cohorts"][0]["manager_character_id"])
        mutations.append(duplicate_manager)
        broken_total = frame()
        broken_total["collective"]["total_quota"] = available(5)
        mutations.append(broken_total)
        consumed_still_ready = frame()
        consumed_still_ready["charter_gate"]["evidence_ready"] = available(True)
        mutations.append(consumed_still_ready)
        for broken in mutations:
            with self.assertRaises(ValueError):
                normalize(broken)

    def test_deferred_three_cycle_gate_and_final_response_schema(self) -> None:
        deferred = frame(1, 3, "consumed")
        deferred["charter_gate"] = charter("consumed")
        deferred["charter_gate"]["status"] = "awaiting_gate"
        deferred["charter_gate"]["evidence_consumed"] = available(False)
        normalize(deferred)
        final = response(frame())
        normalized = normalize_zhongguo_workforce_collective_snapshot_v1_response(
            final, expected_query=query(), expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION, expected_native_revision=NATIVE_REVISION,
            expected_connection_generation=4, expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        schema = json.loads((ROOT / "schemas" / "zhongguo-workforce-collective-snapshot-v1.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(normalized)


if __name__ == "__main__":
    unittest.main()
