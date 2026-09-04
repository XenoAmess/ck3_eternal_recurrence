#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
UNIT_TESTS = ROOT / "ck3_autonomous_player" / "tests" / "unit"
for import_root in (TOOLS, AUTOPLAYER_SRC, UNIT_TESTS):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from test_event_window_context_v1_bridge import (  # noqa: E402
    _frame as event_frame,
    _scope as event_scope,
)
from test_zhongguo_incident_action_cell import (  # noqa: E402
    DATE_RAW,
    OWNER,
    PLAYER,
    FakeClock,
    FakeIncidentService,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    IncidentCheckpointSeamError,
    capture_current_received_self_incident_checkpoint_v1,
    load_received_self_incident_checkpoint_receipt,
    run_received_self_incident_checkpoint_action_cell,
    validate_received_self_incident_checkpoint_receipt,
)
import zg361_phase2_incidents_operations_preflight as preflight  # noqa: E402


SEED_LINEAGE_ID = "zg361-phase2-seed-" + "a" * 64


def capture_lineage() -> dict[str, object]:
    return {
        "seed_lineage_id": SEED_LINEAGE_ID,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }


def _full_event_frame(
    *,
    event_key: str,
    event_instance_id: int,
    native_revision: int,
    date_raw: int,
    option_one_enabled: bool,
    notice_owner: int,
) -> dict[str, object]:
    frame = event_frame()
    frame["snapshot_revision"] = native_revision
    frame["date_raw"] = date_raw
    frame["current_event_instance_id"] = event_instance_id
    frame["event_definition_key"] = event_key
    frame["root_scope"] = event_scope(character_id=PLAYER)
    frame["saved_scopes"] = (
        [
            {
                "name": "zg361_notice_prompt_owner",
                "name_identifier": 91,
                "scope": event_scope(character_id=notice_owner),
            }
        ]
        if event_key == "zg361.50"
        else []
    )
    option_template = copy.deepcopy(frame["options"][0])
    options = []
    for index in range(3):
        option = copy.deepcopy(option_template)
        option.update(
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": option_one_enabled if index == 0 else True,
                "fallback": False,
                "cancel": False,
                "resolved_name": f"option-{index + 1}",
                "unavailable_reason": "",
            }
        )
        options.append(option)
    frame["options"] = options
    return frame


class CaptureAndActionService(FakeIncidentService):
    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.pid = 4100
        self.connection_generation = 3
        self.save_path = root / "native-checkpoint.ck3"
        self.save_calls = 0
        self.restore_calls: list[dict[str, object]] = []
        self.option_one_enabled = True
        self.notice_owner = OWNER
        self.query_drift = False
        self.save_drift = False
        self.restore_ack_only = False

    def snapshot(self) -> dict[str, object]:
        value = super().snapshot()
        value["diagnostics"] = {
            "bridge_pid": self.pid,
            "connection_generation": self.connection_generation,
        }
        return value

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if (
            expected_revision != self.revision
            or event_instance_id != self.event_instance_id
            or self.event_key is None
            or not self.paused
        ):
            raise AssertionError("event context binding changed")
        frame = _full_event_frame(
            event_key=self.event_key,
            event_instance_id=event_instance_id,
            native_revision=self.native_revision,
            date_raw=self.date_raw,
            option_one_enabled=self.option_one_enabled,
            notice_owner=self.notice_owner,
        )
        result = {
            "status": "available",
            "scope": "exact-current-event-window",
            "current_event_window_context_ready": True,
            "current_event_effect_indicators_ready": True,
            "binding": {
                "snapshot_id": f"snapshot-{self.revision}",
                "revision": self.revision,
                "native_revision": self.native_revision,
                "date_raw": self.date_raw,
                "expected_revision": expected_revision,
                "event_instance_id": event_instance_id,
            },
            "source": {
                "snapshot_id": f"snapshot-{self.revision}",
                "revision": self.revision,
                "native_revision": self.native_revision,
                "date_raw": self.date_raw,
                "paused": True,
                "backend_id": "native-headless",
            },
            "current_event_window_context": frame,
        }
        if self.query_drift:
            self.revision += 1
            self.native_revision += 1
        return result

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("save revision changed")
        self.save_calls += 1
        self.save_path.write_bytes(b"real-ck3-incident-source")
        sha256 = hashlib.sha256(self.save_path.read_bytes()).hexdigest().upper()
        result = {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(self.save_path.resolve()),
                "size": self.save_path.stat().st_size,
                "sha256": sha256,
                "date_raw": self.date_raw,
                "episode_character_id": PLAYER,
                "strategy": "native-autosave-command-v1",
            },
            "materialization": {"available": True},
        }
        if self.save_drift:
            self.revision += 1
            self.native_revision += 1
        return result

    def restore_phase2_span_source_checkpoint_v1(
        self, **arguments: object
    ) -> dict[str, object]:
        self.restore_calls.append(dict(arguments))
        if self.restore_ack_only:
            return {"accepted": True, "status": "submitted"}
        previous_pid = self.pid
        previous_generation = self.connection_generation
        self.pid += 1
        self.connection_generation += 1
        self.event_key = "zg361.50"
        self.event_instance_id = 700
        self.paused = True
        self.speed = 1
        self.revision = 40
        self.native_revision = 400
        self.date_raw = DATE_RAW
        self.entry_selected = False
        self.result_selected = False
        self.terminal_ready = False
        self.selections = []
        return {
            "schema_version": 1,
            "result": "GREEN",
            "provider_observed": True,
            "restore_materialized": True,
            "checkpoint_sha256": arguments["expected_checkpoint_sha256"],
            "checkpoint_bytes": arguments["expected_checkpoint_bytes"],
            "save_lineage_id": arguments["expected_save_lineage_id"],
            "event_definition_key": arguments[
                "expected_event_definition_key"
            ],
            "owner_character_id": arguments["expected_owner_character_id"],
            "player_character_id": arguments[
                "expected_player_character_id"
            ],
            "date_raw": arguments["expected_date_raw"],
            "lifecycle": {
                "lifecycle_intent": "restore",
                "previous_pid": previous_pid,
                "pid": self.pid,
                "previous_connection_generation": previous_generation,
                "connection_generation": self.connection_generation,
            },
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }


def capture(
    root: Path, service: CaptureAndActionService
) -> tuple[dict[str, object], Path]:
    receipt_path = root / "incident-source-receipt.json"
    receipt = capture_current_received_self_incident_checkpoint_v1(
        service,
        checkpoint_root=root / "frozen",
        receipt_path=receipt_path,
        seed_lineage_id=SEED_LINEAGE_ID,
        capture_lineage=capture_lineage(),
    )
    return receipt, receipt_path


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


class IncidentCheckpointSeamTests(unittest.TestCase):
    def test_capture_freezes_exact_query_save_and_makes_preflight_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            receipt, receipt_path = capture(root, service)
            validated = load_received_self_incident_checkpoint_receipt(
                receipt_path, expected_seed_lineage_id=SEED_LINEAGE_ID
            )
            live_path = root / "incident-x-live.json"
            live_path.write_text(
                json.dumps(live_report(), indent=2) + "\n",
                encoding="utf-8",
            )
            live_hash = hashlib.sha256(live_path.read_bytes()).hexdigest().upper()
            with patch.object(
                preflight, "INCIDENT_X_LIVE_REPORT_SHA256", live_hash
            ):
                report = preflight.build_preflight(
                    incident_x_live_report_path=live_path,
                    source_checkpoint_receipt_path=receipt_path,
                    expected_seed_lineage_id=SEED_LINEAGE_ID,
                )
                with self.assertRaisesRegex(
                    preflight.IncidentsOperationsPreflightError,
                    "expected seed lineage ID is required",
                ):
                    preflight.build_preflight(
                        incident_x_live_report_path=live_path,
                        source_checkpoint_receipt_path=receipt_path,
                    )

        self.assertEqual(service.save_calls, 1)
        self.assertEqual(receipt["player_character_id"], PLAYER)
        self.assertEqual(receipt["subject_character_id"], PLAYER)
        self.assertEqual(receipt["owner_character_id"], OWNER)
        self.assertNotEqual(OWNER, PLAYER)
        self.assertTrue(receipt["provider_observed"])
        self.assertTrue(receipt["ui_state_verified"])
        self.assertFalse(receipt["action_ack_used_as_state_evidence"])
        self.assertEqual(validated["result"], "GREEN")
        self.assertEqual(report["status"], "READY_FOR_LIVE_RUN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertEqual(report["live_gameplay_result"], "pending")

    def test_capture_rejects_non_actionable_source_before_saving(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for mutation in ("disabled-option", "owner-equals-player"):
                service = CaptureAndActionService(root)
                if mutation == "disabled-option":
                    service.option_one_enabled = False
                else:
                    service.notice_owner = PLAYER
                with self.assertRaises(IncidentCheckpointSeamError) as raised:
                    capture_current_received_self_incident_checkpoint_v1(
                        service,
                        checkpoint_root=root / mutation / "frozen",
                        receipt_path=root / mutation / "receipt.json",
                        seed_lineage_id=SEED_LINEAGE_ID,
                        capture_lineage=capture_lineage(),
                    )
                self.assertEqual(
                    raised.exception.reason_code,
                    "incident_source_event_context_not_received_self",
                )
                self.assertEqual(service.save_calls, 0)

    def test_capture_rejects_query_or_save_frame_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            query_drift = CaptureAndActionService(root)
            query_drift.query_drift = True
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                capture_current_received_self_incident_checkpoint_v1(
                    query_drift,
                    checkpoint_root=root / "query-frozen",
                    receipt_path=root / "query.json",
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage=capture_lineage(),
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_query_crossed_binding",
            )
            self.assertEqual(query_drift.save_calls, 0)

            save_drift = CaptureAndActionService(root)
            save_drift.save_drift = True
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                capture_current_received_self_incident_checkpoint_v1(
                    save_drift,
                    checkpoint_root=root / "save-frozen",
                    receipt_path=root / "save.json",
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage=capture_lineage(),
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_save_crossed_binding",
            )

    def test_preflight_rejects_checkpoint_hash_or_lineage_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            receipt, _ = capture(root, service)
            drifted_lineage = copy.deepcopy(receipt)
            drifted_lineage["capture_lineage"]["console_used"] = True
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                validate_received_self_incident_checkpoint_receipt(
                    drifted_lineage,
                    expected_seed_lineage_id=SEED_LINEAGE_ID,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_capture_lineage_invalid",
            )

            Path(receipt["checkpoint"]["path"]).write_bytes(b"drift")
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                validate_received_self_incident_checkpoint_receipt(
                    receipt, expected_seed_lineage_id=SEED_LINEAGE_ID
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_checkpoint_receipt_invalid",
            )

    def test_restore_reobserve_and_existing_action_cell_prove_xyz_and_acl(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            receipt, _ = capture(root, service)
            clock = FakeClock()
            clock.on_sleep = service.advance
            result = run_received_self_incident_checkpoint_action_cell(
                service,
                receipt,
                expected_seed_lineage_id=SEED_LINEAGE_ID,
                timeout_seconds=3.0,
                poll_interval_seconds=0.1,
                monotonic=clock.monotonic,
                sleep=clock.sleep,
            )

        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["restore_materialized"])
        self.assertTrue(result["source_provider_ui_reobserved"])
        self.assertTrue(result["provider_observed_postcondition"])
        self.assertFalse(result["ack_only_is_green"])
        self.assertEqual(
            service.selections, [("zg361.50", 1), ("zg361.4", 1)]
        )
        action = result["action_cell"]
        self.assertEqual(set(action["terminal_profiles"]), {"x", "y", "z"})
        self.assertEqual(
            {
                row["kind"]
                for row in action["terminal_profiles"].values()
            },
            {"na", "incident"},
        )
        self.assertTrue(action["checks"]["wrong_owner_acl_typed_red"])
        self.assertFalse(service.restore_calls[0]["allow_fixture"])
        self.assertFalse(service.restore_calls[0]["allow_console"])
        self.assertFalse(
            service.restore_calls[0]["allow_generic_character_rebind"]
        )

    def test_ack_only_restore_and_acl_leak_are_explicit_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ack_service = CaptureAndActionService(root)
            receipt, _ = capture(root, ack_service)
            ack_service.restore_ack_only = True
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                run_received_self_incident_checkpoint_action_cell(
                    ack_service,
                    receipt,
                    expected_seed_lineage_id=SEED_LINEAGE_ID,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_checkpoint_restore_invalid",
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            acl_service = CaptureAndActionService(root)
            receipt, _ = capture(root, acl_service)
            acl_service.acl_leak = True
            clock = FakeClock()
            clock.on_sleep = acl_service.advance
            with self.assertRaises(IncidentCheckpointSeamError) as raised:
                run_received_self_incident_checkpoint_action_cell(
                    acl_service,
                    receipt,
                    expected_seed_lineage_id=SEED_LINEAGE_ID,
                    timeout_seconds=3.0,
                    poll_interval_seconds=0.1,
                    monotonic=clock.monotonic,
                    sleep=clock.sleep,
                )
            self.assertEqual(
                raised.exception.reason_code, "incident_action_cell_red"
            )
            self.assertIn(
                "wrong-owner ACL leaked state",
                raised.exception.evidence["failure_reason"],
            )


if __name__ == "__main__":
    unittest.main()
