#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from preflight_zg361_phase2_projects_metrics_action_cell import (
    audit_projects_metrics_action_cell_contract,
)
from xar_autoplayer.bridge.zhongguo_projects_metrics_postcondition_contract import (
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
)
from zg361_phase2_projects_metrics_action_cell import (
    ProjectsMetricsActionCellError,
    preflight_projects_metrics_gameplay_action_cell,
    run_projects_metrics_gameplay_action_cell,
)


OWNER = 147
SUBJECT = 361
CYCLE = 9
CASE = 26
RECEIPT = 26_001
RECEIPT_REVISION = 9


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable() -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": "postcondition_unavailable",
    }


def identity(*, ready: bool = True) -> dict[str, object]:
    field = available if ready else lambda _value: unavailable()
    return {
        "owner_character_id": field(OWNER),
        "subject_character_id": field(SUBJECT),
        "cycle_serial": field(CYCLE),
        "case_serial": field(CASE),
    }


def snapshot(index: int, *, active_event: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": f"fixture:{100 + index}",
        "revision": 10 + index,
        "native_revision": 100 + index,
        "date_raw": 2_400 + index * 24,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": SUBJECT},
        "diagnostics": {"connection_generation": 7},
        "active_event": {"instance_id": 500 + index} if active_event else None,
    }


def response(
    index: int,
    *,
    ready: bool,
    receipt_id: int = RECEIPT,
    source_owner: int = OWNER,
) -> dict[str, object]:
    source = identity()
    if source_owner != OWNER:
        source["owner_character_id"] = available(source_owner)
    result = identity(ready=ready)
    contribution_identity = json.loads(json.dumps(source))
    metrics_identity = identity(ready=ready)
    pending_field = available if ready else lambda _value: unavailable()
    readiness = {
        "player_subject_binding_ready": True,
        "owner_binding_ready": True,
        "source_identity_ready": True,
        "result_identity_ready": ready,
        "contribution_ready": True,
        "metrics_ready": ready,
        "same_project_case_identity": ready,
        "receipt_lineage_ready": ready,
        "result_operation_committed": ready,
        "same_frame_ready": True,
        "ready": ready,
    }
    snap = snapshot(index)
    return {
        "schema_version": 1,
        "status": "available",
        "capability": QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
        "case_kind": "zhongguo.projects-metrics.project-correlation",
        "request_nonce": "fixture",
        "snapshot_revision": snap["native_revision"],
        "date_raw": snap["date_raw"],
        "paused": True,
        "player_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "checkpoint_state": (
            "p3_result_committed" if ready else "cp26_ready_p3_absent"
        ),
        "source_identity": source,
        "result_identity": result,
        "projects_metrics": {
            "source_identity": json.loads(json.dumps(source)),
            "result_identity": json.loads(json.dumps(result)),
            "contribution": {
                "identity": contribution_identity,
                "receipt_id": available(receipt_id),
                "receipt_revision": available(RECEIPT_REVISION),
                "value": available(1),
                "provider_observed": True,
            },
            "metrics_result": {
                "identity": metrics_identity,
                "source_contribution_receipt_id": pending_field(receipt_id),
                "source_contribution_receipt_revision": pending_field(
                    RECEIPT_REVISION
                ),
                "metrics_revision": pending_field(3),
                "dictionary_key": pending_field("metric_dictionary_subject_v1"),
                "provider_observed": True,
            },
        },
        "readiness": readiness,
        "source_backend_id": "native-headless",
        "provenance": {},
        "unavailable_reason": None,
        "binding": {
            "request_nonce": "fixture",
            "snapshot_id": snap["snapshot_id"],
            "revision": snap["revision"],
            "native_revision": snap["native_revision"],
            "connection_generation": 7,
            "date_raw": snap["date_raw"],
            "paused": True,
            "player_character_id": SUBJECT,
            "subject_character_id": SUBJECT,
            "owner_character_id": OWNER,
            "expected_revision": snap["revision"],
        },
    }


def source_absent_response(index: int) -> dict[str, object]:
    result = response(index, ready=False)
    result["status"] = "unavailable"
    result["checkpoint_state"] = "unavailable"
    result["unavailable_reason"] = "project_source_not_found"
    return result


class FakeService:
    def __init__(
        self,
        *,
        advertise: bool = True,
        green_after: int | None = 1,
        malformed_ack: bool = False,
        drift_receipt: bool = False,
        active_event: bool = False,
        initial_source_absent: bool = False,
    ) -> None:
        self.advertise = advertise
        self.green_after = green_after
        self.malformed_ack = malformed_ack
        self.drift_receipt = drift_receipt
        self.active_event = active_event
        self.initial_source_absent = initial_source_absent
        self.index = 0
        self.queries: list[dict[str, object]] = []
        self.actions: list[dict[str, object]] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY]
                if self.advertise
                else []
            ),
            "action_steps": ["life-advance"],
        }

    def snapshot(self) -> dict[str, object]:
        return snapshot(self.index, active_event=self.active_event)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.actions.append(
            {"step": step, "expected_revision": expected_revision}
        )
        self.index += 1
        return {
            "step": "wrong" if self.malformed_ack else "life-advance",
            "paused": True,
            "revision": 10 + self.index,
        }

    def query_zhongguo_projects_metrics_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.queries.append(
            {
                "request_nonce": request_nonce,
                "expected_revision": expected_revision,
                "owner_character_id": owner_character_id,
            }
        )
        is_ready = (
            self.green_after is not None and self.index >= self.green_after
        )
        if self.initial_source_absent and self.index == 0:
            return source_absent_response(self.index)
        receipt_id = (
            RECEIPT + 1 if self.drift_receipt and self.index > 0 else RECEIPT
        )
        return response(self.index, ready=is_ready, receipt_id=receipt_id)


class ProjectsMetricsActionCellTests(unittest.TestCase):
    def test_preflight_requires_exact_cp26_ready_p3_absent_checkpoint(self) -> None:
        absent = preflight_projects_metrics_gameplay_action_cell(
            FakeService(initial_source_absent=True), owner_character_id=OWNER
        )
        self.assertEqual(absent["result"], "RED")
        self.assertEqual(absent["reason_code"], "source_checkpoint_unavailable")

        service = FakeService(green_after=1)
        report = preflight_projects_metrics_gameplay_action_cell(
            service, owner_character_id=OWNER
        )
        self.assertEqual(report["result"], "READY")
        self.assertTrue(report["ready_to_run"])
        self.assertFalse(report["gameplay_action_executed"])
        self.assertFalse(report["action_ack_is_business_postcondition"])
        self.assertEqual(report["checkpoint_mode"], "cp26_ready_p3_absent")
        self.assertEqual(
            report["source_checkpoint"]["contribution_receipt_id"], RECEIPT
        )

    def test_green_requires_later_provider_observed_same_receipt(self) -> None:
        service = FakeService(green_after=2)
        result = run_projects_metrics_gameplay_action_cell(
            service,
            owner_character_id=OWNER,
            max_advance_steps=3,
            max_elapsed_days=3,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["gameplay_action_executed"])
        self.assertTrue(result["business_postcondition_complete"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(
            result["terminal_condition"],
            "same_cp26_receipt_consumed_by_committed_p3m229_result",
        )
        self.assertEqual(result["postcondition"]["identity"], [147, 361, 9, 26])
        self.assertEqual(
            result["postcondition"]["contribution_receipt_id"], RECEIPT
        )
        self.assertEqual(len(service.actions), 2)
        self.assertEqual(
            [query["request_nonce"] for query in service.queries],
            [
                "zg361.projects.metrics.pre",
                "zg361.projects.metrics.d1",
                "zg361.projects.metrics.d2",
            ],
        )

    def test_capability_and_active_event_fail_preflight_without_action(self) -> None:
        unavailable_report = preflight_projects_metrics_gameplay_action_cell(
            FakeService(advertise=False), owner_character_id=OWNER
        )
        self.assertEqual(
            unavailable_report["reason_code"],
            "projects_metrics_provider_not_advertised",
        )
        event_service = FakeService(active_event=True)
        event_report = preflight_projects_metrics_gameplay_action_cell(
            event_service, owner_character_id=OWNER
        )
        self.assertEqual(event_report["reason_code"], "player_visible_event_pending")
        self.assertEqual(event_service.actions, [])

    def test_timeline_ack_cannot_substitute_for_provider_postcondition(self) -> None:
        service = FakeService(green_after=None)
        with self.assertRaises(ProjectsMetricsActionCellError) as caught:
            run_projects_metrics_gameplay_action_cell(
                service,
                owner_character_id=OWNER,
                max_advance_steps=2,
                max_elapsed_days=2,
            )
        self.assertEqual(
            caught.exception.reason_code,
            "projects_metrics_postcondition_unobserved",
        )
        self.assertTrue(caught.exception.evidence["gameplay_action_executed"])
        self.assertFalse(
            caught.exception.evidence["business_postcondition_complete"]
        )
        for row in caught.exception.evidence["timeline_actions"]:
            self.assertFalse(row["ack_is_business_postcondition"])

    def test_malformed_ack_and_source_receipt_drift_fail_closed(self) -> None:
        with self.assertRaises(ProjectsMetricsActionCellError) as malformed:
            run_projects_metrics_gameplay_action_cell(
                FakeService(malformed_ack=True),
                owner_character_id=OWNER,
                max_advance_steps=1,
                max_elapsed_days=1,
            )
        self.assertEqual(
            malformed.exception.reason_code,
            "timeline_acknowledgement_malformed",
        )
        with self.assertRaises(ProjectsMetricsActionCellError) as drifted:
            run_projects_metrics_gameplay_action_cell(
                FakeService(
                    drift_receipt=True, initial_source_absent=False
                ),
                owner_character_id=OWNER,
                max_advance_steps=1,
                max_elapsed_days=1,
            )
        self.assertEqual(
            drifted.exception.reason_code, "source_checkpoint_drifted"
        )

    def test_static_preflight_records_current_live_gaps_without_claiming_live(self) -> None:
        report = audit_projects_metrics_action_cell_contract(ROOT)
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["live_proof_claimed"])
        self.assertTrue(all(report["checks"].values()))
        gap_ids = {row["id"] for row in report["known_live_gaps"]}
        self.assertIn("provider-capability-withheld", gap_ids)
        self.assertNotIn("central-stage-order", gap_ids)


if __name__ == "__main__":
    unittest.main()
