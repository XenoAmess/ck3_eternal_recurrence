#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import zg361_phase2_incidents_operations_preflight as preflight


PLAYER = 29_037
OWNER = 32_904
INSTANCE = 801


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def live_report() -> dict[str, object]:
    return {
        "kind": "zg361_minimal_full_entry_probe",
        "result": "GREEN",
        "game": {
            "installed_version": (
                preflight.ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION
            ),
            "exe_sha256": (
                preflight.ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256
            ),
        },
        "candidate": {
            "file_count": preflight.INCIDENT_X_LIVE_FILE_COUNT,
            "tree_sha256": preflight.INCIDENT_X_LIVE_TREE_SHA256,
        },
        "entry": {
            "candidate_mounted": True,
            "game_state_ready": True,
            "map_rendered": True,
            "paused": True,
        },
        "logs": {"material_error_lines": []},
        "cleanup": {"ck3_running_after": False},
    }


def source_checkpoint_receipt(checkpoint: Path) -> dict[str, object]:
    payload = checkpoint.read_bytes()
    return {
        "schema_version": 1,
        "kind": preflight.SOURCE_CHECKPOINT_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "provider_observed": True,
        "ui_state_verified": True,
        "span_id": preflight.SPAN_ID,
        "producer_key": preflight.PRODUCER_KEY,
        "handler": preflight.HANDLER,
        "source_event_definition_key": "zg361.50",
        "paused": True,
        "map_ready": True,
        "owner_character_id": OWNER,
        "player_character_id": PLAYER,
        "event_root_character_id": PLAYER,
        "notice_owner_character_id": OWNER,
        "event_instance_id": INSTANCE,
        "option_number": 1,
        "event_context_query": {
            "capability": (
                preflight.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            ),
            "status": "available",
            "event_definition_key": "zg361.50",
            "event_instance_id": INSTANCE,
            "root_character_id": PLAYER,
            "notice_owner_character_id": OWNER,
            "option_number": 1,
            "option_shown": True,
            "option_enabled": True,
        },
        "checkpoint": {
            "path": str(checkpoint),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest().upper(),
        },
    }


class IncidentsOperationsPreflightTests(unittest.TestCase):
    def build(
        self,
        root: Path,
        *,
        checkpoint_receipt: dict[str, object] | None = None,
    ) -> dict[str, object]:
        live = root / "incident-x-live.json"
        write_json(live, live_report())
        live_hash = hashlib.sha256(live.read_bytes()).hexdigest().upper()
        receipt_path = None
        if checkpoint_receipt is not None:
            receipt_path = root / "source-checkpoint-receipt.json"
            write_json(receipt_path, checkpoint_receipt)
        with patch.object(
            preflight, "INCIDENT_X_LIVE_REPORT_SHA256", live_hash
        ):
            return preflight.build_preflight(
                incident_x_live_report_path=live,
                source_checkpoint_receipt_path=receipt_path,
                expected_seed_lineage_id=(
                    "zg361-phase2-seed-unit" if receipt_path is not None else None
                ),
            )

    def test_current_contracts_and_live_entry_leave_only_checkpoint_pending(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = self.build(Path(temporary))
        self.assertEqual(report["status"], "GREEN_STATIC")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertFalse(report["live_run_ready"])
        self.assertEqual(report["live_gameplay_result"], "pending")
        self.assertEqual(
            report["blockers"],
            ["received_self_incident_source_checkpoint_pending"],
        )
        self.assertFalse(report["cell"]["ack_only_is_green"])
        self.assertTrue(
            report["cell"]["green_requires_provider_observed_postcondition"]
        )
        self.assertFalse(
            report["incident_x_full_entry_live_evidence"]
            ["proves_gameplay_action"]
        )

    def test_legacy_flat_checkpoint_shape_cannot_make_live_run_ready(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "incident-source.ck3"
            checkpoint.write_bytes(b"real-ck3-checkpoint-fixture")
            with self.assertRaisesRegex(
                preflight.IncidentsOperationsPreflightError,
                "incident_source_capture_lineage_invalid",
            ):
                self.build(
                    root,
                    checkpoint_receipt=source_checkpoint_receipt(checkpoint),
                )

    def test_ack_only_shape_cannot_be_declared_by_preflight(self) -> None:
        contract = preflight._static_cell_contract()
        self.assertFalse(contract["ack_only_is_green"])
        self.assertEqual(
            contract["sequence"],
            [
                "provider-query-exact-entry-event-context",
                "select-fixed-authored-option-and-observe-old-instance-disappear",
                "provider-query-x-y-z-terminal-and-kpi-matrix",
                "provider-query-wrong-owner-acl-negative-control",
            ],
        )
        self.assertEqual(
            contract["readiness"], "static-ready-live-pending"
        )

    def test_changed_or_red_live_entry_report_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            live = root / "incident-x-live.json"
            payload = live_report()
            payload["result"] = "RED"
            write_json(live, payload)
            digest = hashlib.sha256(live.read_bytes()).hexdigest().upper()
            with patch.object(
                preflight, "INCIDENT_X_LIVE_REPORT_SHA256", digest
            ):
                with self.assertRaisesRegex(
                    preflight.IncidentsOperationsPreflightError,
                    "not GREEN",
                ):
                    preflight.build_preflight(
                        incident_x_live_report_path=live
                    )


if __name__ == "__main__":
    unittest.main()
