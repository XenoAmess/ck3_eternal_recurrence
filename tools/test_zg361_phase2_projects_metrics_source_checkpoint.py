#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from preflight_zg361_phase2_projects_metrics_source_checkpoint import (  # noqa: E402
    audit_projects_metrics_source_checkpoint_capture,
)
from xar_autoplayer.bridge.zhongguo_projects_metrics_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
)
from zg361_phase2_projects_metrics_source_checkpoint import (  # noqa: E402
    LIVE_MODE,
    REGISTRY_KIND,
    ProjectsMetricsSourceCheckpointError,
    capture_projects_metrics_source_checkpoint_live,
    observe_cp26_route_ui_live,
    validate_projects_metrics_source_checkpoint_registry,
)


OWNER = 147
SUBJECT = 361
CYCLE = 12
CASE = 44
DATE_RAW = 53147040
RECEIPT_ID = 26001
RECEIPT_REVISION = 12


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


def lineage() -> dict[str, object]:
    return {
        "schema_version": 2,
        "kind": "zg361_projects_metrics_capture_lineage",
        "evidence_class": "real_ck3",
        "state_origin": "managed_product",
        "single_player": True,
        "product_only_mount": True,
        "seed_lineage_id": "zg361-seed-unit",
        "capture_lineage_id": "zg361-projects-unit",
        "source_git_commit": "27b66b3ea34c3ad03bdc72a4fb14345628a7a606",
        "product_tree_sha256": "A" * 64,
        "runtime_product_tree_sha256": "A" * 64,
        "product_enabled_mod": "mod/zg361_acceptance.mod",
        "enabled_mods": ["mod/zg361_acceptance.mod"],
        "fixture_used": False,
        "console_used": False,
        "test_decision_used": False,
        "generic_character_rebind_used": False,
    }


def subject_snapshot(*, active_event: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": "native:70",
        "revision": 20,
        "native_revision": 70,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": SUBJECT},
        "diagnostics": {"bridge_pid": 1234, "connection_generation": 4},
        "active_event": (
            {"instance_id": 88, "option_count": 3} if active_event else None
        ),
    }


def provider_response(*, result_ready: bool = False) -> dict[str, object]:
    source = identity()
    result = identity(ready=result_ready)
    pending = available if result_ready else lambda _value: unavailable()
    return {
        "schema_version": 1,
        "status": "available",
        "capability": QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
        "case_kind": "zhongguo.projects-metrics.project-correlation",
        "request_nonce": "zg361.projects.metrics.source.capture.pre",
        "snapshot_revision": 70,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "source_identity": copy.deepcopy(source),
        "result_identity": copy.deepcopy(result),
        "projects_metrics": {
            "source_identity": copy.deepcopy(source),
            "result_identity": copy.deepcopy(result),
            "contribution": {
                "identity": copy.deepcopy(source),
                "receipt_id": available(RECEIPT_ID),
                "receipt_revision": available(RECEIPT_REVISION),
                "value": available(20),
                "provider_observed": True,
            },
            "metrics_result": {
                "identity": copy.deepcopy(result),
                "source_contribution_receipt_id": pending(RECEIPT_ID),
                "source_contribution_receipt_revision": pending(
                    RECEIPT_REVISION
                ),
                "metrics_revision": pending(1),
                "dictionary_key": pending("metric_dictionary_subject_v1"),
                "provider_observed": True,
            },
        },
        "readiness": {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "source_identity_ready": True,
            "result_identity_ready": result_ready,
            "contribution_ready": True,
            "metrics_ready": result_ready,
            "same_project_case_identity": result_ready,
            "receipt_lineage_ready": result_ready,
            "result_operation_committed": result_ready,
            "same_frame_ready": True,
            "ready": result_ready,
        },
        "source_backend_id": "native-headless",
        "provenance": {},
        "unavailable_reason": None,
        "binding": {
            "request_nonce": "zg361.projects.metrics.source.capture.pre",
            "snapshot_id": "native:70",
            "revision": 20,
            "native_revision": 70,
            "connection_generation": 4,
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": SUBJECT,
            "subject_character_id": SUBJECT,
            "owner_character_id": OWNER,
            "expected_revision": 20,
        },
    }


class UiService:
    def __init__(self) -> None:
        self.active = True
        self.selected: list[dict[str, object]] = []

    def snapshot(self) -> dict[str, object]:
        value = subject_snapshot(active_event=self.active)
        value["snapshot_id"] = "native:60"
        value["native_revision"] = 60
        value["revision"] = 10
        value["played_character"] = {"character_id": OWNER}
        return value

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.asserted_query = (event_instance_id, expected_revision)

        def character(character_id: int) -> dict[str, object]:
            return {
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            }

        return {
            "status": "available",
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": "zg361cp.26",
                "current_event_instance_id": 88,
                "snapshot_revision": 60,
                "date_raw": DATE_RAW,
                "root_scope": character(OWNER),
                "saved_scopes": [
                    {"name": "zg361_cp_e_owner", "scope": character(OWNER)},
                    {"name": "zg361_cp_e_subject", "scope": character(SUBJECT)},
                    {"name": "zg361_cp_e_cycle", "scope": {}},
                    {"name": "zg361_cp_e_case", "scope": {}},
                ],
                "options": [
                    {"native_option_index": 0, "shown": True, "enabled": True},
                    {"native_option_index": 1, "shown": True, "enabled": True},
                    {"native_option_index": 2, "shown": True, "enabled": True},
                ],
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selected.append(
            {
                "option_number": option_number,
                "event_instance_id": event_instance_id,
                "expected_revision": expected_revision,
            }
        )
        self.active = False
        return {"accepted": True, "status": "submitted"}


class CheckpointService:
    def __init__(
        self,
        checkpoint_path: Path,
        *,
        result_ready: bool = False,
        source_absent: bool = False,
        active_event: bool = False,
    ) -> None:
        self.checkpoint_path = checkpoint_path.resolve()
        self.checkpoint_path.write_bytes(b"managed-real-product-checkpoint")
        self.result_ready = result_ready
        self.source_absent = source_absent
        self.active_event = active_event
        self.saved: list[int | None] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
            ],
            "action_steps": ["life-advance"],
        }

    def snapshot(self) -> dict[str, object]:
        return subject_snapshot(active_event=self.active_event)

    def query_zhongguo_projects_metrics_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        value = provider_response(result_ready=self.result_ready)
        value["request_nonce"] = request_nonce
        value["binding"]["request_nonce"] = request_nonce
        if self.source_absent:
            value["status"] = "unavailable"
            value["unavailable_reason"] = "project_source_not_found"
        return value

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.saved.append(expected_revision)
        return {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(self.checkpoint_path),
                "size": self.checkpoint_path.stat().st_size,
                "sha256": hashlib.sha256(
                    self.checkpoint_path.read_bytes()
                ).hexdigest().upper(),
                "date_raw": DATE_RAW,
                "strategy": "managed-native-save",
            },
            "materialization": {"result": "GREEN"},
        }


def write_ui_receipt(path: Path, *, route: str = "A") -> dict[str, object]:
    receipt = observe_cp26_route_ui_live(
        UiService(),
        route=route,
        capture_lineage=lineage(),
        live_mode=LIVE_MODE,
    )
    path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


class ProjectsMetricsSourceCheckpointTests(unittest.TestCase):
    def test_ui_observation_accepts_only_real_cp26_route_a_or_b(self) -> None:
        service = UiService()
        receipt = observe_cp26_route_ui_live(
            service,
            route="B",
            capture_lineage=lineage(),
            live_mode=LIVE_MODE,
        )
        self.assertEqual(receipt["event_definition_key"], "zg361cp.26")
        self.assertEqual(receipt["route"], "B")
        self.assertEqual(receipt["option_number"], 2)
        self.assertEqual(receipt["owner_character_id"], OWNER)
        self.assertEqual(receipt["subject_character_id"], SUBJECT)
        self.assertFalse(receipt["business_state_proven"])
        self.assertFalse(receipt["action_ack_is_business_postcondition"])
        self.assertEqual(service.selected[0]["option_number"], 2)

        with self.assertRaises(ProjectsMetricsSourceCheckpointError) as raised:
            observe_cp26_route_ui_live(
                UiService(),
                route="C",
                capture_lineage=lineage(),
                live_mode=LIVE_MODE,
            )
        self.assertEqual(raised.exception.reason_code, "cp26_route_not_captureable")

    def test_capture_writes_schema2_registry_and_hash_bound_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ui_path = root / "ui.json"
            write_ui_receipt(ui_path, route="A")
            service = CheckpointService(root / "native.ck3")
            registry_path = root / "registry.json"
            registry = capture_projects_metrics_source_checkpoint_live(
                service,
                owner_character_id=OWNER,
                capture_lineage=lineage(),
                ui_receipt_path=ui_path,
                checkpoint_root=root / "frozen",
                registry_path=registry_path,
                live_mode=LIVE_MODE,
            )
            self.assertEqual(registry["schema_version"], 2)
            self.assertEqual(registry["registry_kind"], REGISTRY_KIND)
            self.assertTrue(registry["provider_observed_business_state"])
            self.assertFalse(registry["action_ack_is_business_postcondition"])
            entry = registry["entries"][0]
            self.assertEqual(entry["player_character_id"], SUBJECT)
            self.assertNotEqual(entry["owner_character_id"], SUBJECT)
            self.assertEqual(entry["cycle_serial"], CYCLE)
            self.assertEqual(entry["case_serial"], CASE)
            self.assertEqual(entry["contribution_receipt_id"], RECEIPT_ID)
            self.assertEqual(
                entry["source_receipt"]["event_definition_key"], "zg361cp.26"
            )
            self.assertTrue(entry["source_receipt"]["provider_observed"])
            self.assertFalse(
                entry["source_receipt"]["action_ack_is_business_postcondition"]
            )
            self.assertTrue(Path(entry["checkpoint"]["path"]).is_file())
            self.assertTrue(Path(entry["ui_receipt"]["path"]).is_file())
            self.assertTrue(Path(entry["provider_receipt"]["path"]).is_file())
            self.assertEqual(service.saved, [20])
            summary = validate_projects_metrics_source_checkpoint_registry(
                json.loads(registry_path.read_text(encoding="utf-8")),
                expected_seed_lineage_id="zg361-seed-unit",
            )
            self.assertEqual(summary["result"], "GREEN")
            self.assertTrue(summary["provider_observed_business_state"])

    def test_capture_rejects_absent_or_committed_source_and_active_event(self) -> None:
        for kwargs in (
            {"source_absent": True},
            {"result_ready": True},
            {"active_event": True},
        ):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                ui_path = root / "ui.json"
                write_ui_receipt(ui_path)
                service = CheckpointService(root / "native.ck3", **kwargs)
                with self.assertRaises(ProjectsMetricsSourceCheckpointError):
                    capture_projects_metrics_source_checkpoint_live(
                        service,
                        owner_character_id=OWNER,
                        capture_lineage=lineage(),
                        ui_receipt_path=ui_path,
                        checkpoint_root=root / "frozen",
                        registry_path=root / "registry.json",
                        live_mode=LIVE_MODE,
                    )
                self.assertEqual(service.saved, [])

    def test_explicit_live_and_real_lineage_are_required_before_observation(self) -> None:
        with self.assertRaises(ProjectsMetricsSourceCheckpointError) as mode:
            observe_cp26_route_ui_live(
                UiService(),
                route="A",
                capture_lineage=lineage(),
                live_mode="fixture",
            )
        self.assertEqual(mode.exception.reason_code, "explicit_live_mode_required")

        invalid = lineage()
        invalid["fixture_used"] = True
        with self.assertRaises(ProjectsMetricsSourceCheckpointError) as fixture:
            observe_cp26_route_ui_live(
                UiService(),
                route="A",
                capture_lineage=invalid,
                live_mode=LIVE_MODE,
            )
        self.assertEqual(fixture.exception.reason_code, "capture_lineage_invalid")

    def test_ui_ack_or_receipt_drift_cannot_substitute_for_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ui_path = root / "ui.json"
            receipt = write_ui_receipt(ui_path)
            receipt["action_ack_is_business_postcondition"] = True
            ui_path.write_text(json.dumps(receipt), encoding="utf-8")
            service = CheckpointService(root / "native.ck3")
            with self.assertRaises(ProjectsMetricsSourceCheckpointError) as raised:
                capture_projects_metrics_source_checkpoint_live(
                    service,
                    owner_character_id=OWNER,
                    capture_lineage=lineage(),
                    ui_receipt_path=ui_path,
                    checkpoint_root=root / "frozen",
                    registry_path=root / "registry.json",
                    live_mode=LIVE_MODE,
                )
            self.assertEqual(raised.exception.reason_code, "cp26_ui_receipt_invalid")
            self.assertEqual(service.saved, [])

    def test_registry_validation_rejects_archived_provider_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ui_path = root / "ui.json"
            write_ui_receipt(ui_path)
            registry = capture_projects_metrics_source_checkpoint_live(
                CheckpointService(root / "native.ck3"),
                owner_character_id=OWNER,
                capture_lineage=lineage(),
                ui_receipt_path=ui_path,
                checkpoint_root=root / "frozen",
                registry_path=root / "registry.json",
                live_mode=LIVE_MODE,
            )
            provider_path = Path(registry["entries"][0]["provider_receipt"]["path"])
            provider_path.write_bytes(b"drift")
            with self.assertRaises(ProjectsMetricsSourceCheckpointError) as raised:
                validate_projects_metrics_source_checkpoint_registry(registry)
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_registry_entry_invalid",
            )

    def test_static_preflight_is_green_and_performs_no_live_work(self) -> None:
        report = audit_projects_metrics_source_checkpoint_capture()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertTrue(all(report["checks"].values()))
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["driver_instantiated"])
        self.assertFalse(report["bridge_attached"])
        self.assertFalse(report["checkpoint_captured"])
        self.assertFalse(report["registry_written"])
        self.assertFalse(report["live_proof_claimed"])


if __name__ == "__main__":
    unittest.main()
