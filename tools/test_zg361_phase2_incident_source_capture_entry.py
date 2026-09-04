#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from test_zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    CaptureAndActionService,
    FakeClock,
    PLAYER,
)
from zg361_phase2_incident_source_capture_entry import (  # noqa: E402
    IncidentSourceCaptureEntryError,
    wait_for_and_capture_incident_source_checkpoint,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    phase2_event_sequence_plan,
)
from zhongguo_phase2_source_checkpoint_registry import (  # noqa: E402
    Phase2SourceCheckpointRegistryBuilder,
)
import preflight_zg361_phase2_incident_source_capture as preflight  # noqa: E402


SEED_LINEAGE_ID = "zg361-phase2-seed-" + "c" * 64


def lineage() -> dict[str, object]:
    return {
        "seed_lineage_id": SEED_LINEAGE_ID,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }


def run_capture(
    root: Path,
    service: CaptureAndActionService,
    *,
    timeout_seconds: float = 1.0,
    clock: FakeClock | None = None,
) -> dict[str, object]:
    clock = clock or FakeClock()
    return wait_for_and_capture_incident_source_checkpoint(
        service,
        evidence_path=root / "capture.json",
        checkpoint_root=root / "checkpoints",
        receipt_path=root / "strict-receipt.json",
        registry_entry_path=root / "registry-entry.json",
        seed_lineage_id=SEED_LINEAGE_ID,
        capture_lineage=lineage(),
        tracked_ck3_pid=service.pid,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=0.1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


def generic_receipt(
    *,
    plan,
    owner: int,
    player: int,
    date_raw: int,
    sha256: str,
) -> dict[str, object]:
    return {
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "span_id": plan.span_id,
        "event_definition_key": plan.source_event,
        "owner_character_id": owner,
        "player_character_id": player,
        "date_raw": date_raw,
        "checkpoint_sha256": sha256,
        "save_lineage_id": SEED_LINEAGE_ID,
    }


def focused_capture_cell_report() -> dict[str, object]:
    scenario = {
        "result": "GREEN",
        "kind": "zg361_phase2_incident_source_checkpoint_live_capture",
        "readiness": "captured-real-checkpoint",
        "provider_observed": True,
        "ui_state_verified": True,
        "player_character_id": PLAYER,
        "subject_character_id": PLAYER,
        "event_root_character_id": PLAYER,
        "owner_character_id": PLAYER + 1,
        "notice_owner_character_id": PLAYER + 1,
        "option_number": 1,
        "option_shown": True,
        "option_enabled": True,
        "provider_ui_same_frame": True,
        "fixture_used": False,
        "console_used": False,
        "gameplay_action_executed": False,
        "action_ack_used_as_state_evidence": False,
    }
    return {
        "result": "GREEN",
        "error_reason": None,
        "phase2_incident_source_checkpoint_capture": True,
        "phase2_incident_source_checkpoint_capture_complete": True,
        "gameplay_acceptance_executed": False,
        "gameplay_green_claimed": False,
        "scenario_evidence": scenario,
    }


class IncidentSourceCaptureEntryTests(unittest.TestCase):
    def test_main_forwards_capture_mode_and_keeps_gameplay_claim_false(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            steam_root = root / "steam"
            steam_root.mkdir()
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            dll.write_bytes(b"incident-capture-test-dll")
            injector.write_bytes(b"incident-capture-test-injector")
            artifacts = root / "artifacts"
            with (
                mock.patch.object(
                    preflight.runner,
                    "preflight",
                    return_value={"native_bridge_runtime": {"ready": True}},
                ),
                mock.patch.object(
                    preflight.runner.terminal,
                    "steam_userdata_root",
                    return_value=steam_root,
                ),
                mock.patch.object(
                    preflight.runner.isolated,
                    "steam_workshop_app_roots",
                    return_value=[],
                ),
                mock.patch.object(
                    preflight.runner.isolated,
                    "registered_workshop_targets",
                ),
                mock.patch.object(
                    preflight.runner.isolated, "ensure_test_paths_safe"
                ),
                mock.patch.object(
                    preflight.runner.isolated,
                    "protected_snapshot",
                    return_value={},
                ),
                mock.patch.object(
                    preflight.runner.isolated, "verify_protected_storage"
                ),
                mock.patch.object(preflight.runner, "write_evidence_index"),
                mock.patch.object(
                    preflight.runner,
                    "run_cell",
                    return_value=focused_capture_cell_report(),
                ) as run_cell,
            ):
                exit_code = preflight.runner.main(
                    artifacts_dir=str(artifacts),
                    keep_userdir=True,
                    phase2_incident_source_checkpoint_capture=True,
                    bridge_dll=str(dll),
                    bridge_injector=str(injector),
                    bridge_pipe=(
                        preflight.runner.NATIVE_TITLE_PIPE_PREFIX + "c" * 32
                    ),
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(
                run_cell.call_args.kwargs[
                    "phase2_incident_source_checkpoint_capture"
                ]
            )
            report = json.loads(
                (artifacts / "report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["result"], "GREEN")
            self.assertTrue(
                report["phase2_incident_source_checkpoint_capture_complete"]
            )
            self.assertFalse(report["gameplay_acceptance_executed"])
            self.assertFalse(report["gameplay_green_claimed"])

    def test_runner_uses_only_the_capture_capability_profile(self) -> None:
        required_bridge = {
            preflight.runner.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
            for label in (
                preflight.runner.PHASE2_INCIDENT_SOURCE_CAPTURE_REQUIRED_BRIDGE_CAPABILITY_LABELS
            )
        }
        required_steps = {
            preflight.runner.PHASE2_REQUIRED_ACTION_STEPS[label]
            for label in (
                preflight.runner.PHASE2_INCIDENT_SOURCE_CAPTURE_REQUIRED_ACTION_STEP_LABELS
            )
        }

        class Service:
            def capabilities(self) -> dict[str, object]:
                value: dict[str, object] = {
                    "mode": preflight.runner.NATIVE_BRIDGE_MODE,
                    "backend_id": preflight.runner.NATIVE_BRIDGE_MODE,
                    "visual_fallback": False,
                    "snapshot": True,
                    "wait_for_change": True,
                    "bridge_capabilities": sorted(required_bridge),
                    "action_steps": sorted(required_steps),
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 7711,
                        "connection_generation": 1,
                    },
                    "checkpoint_materialization": {"configured": True},
                    "native_session_control": {"configured": True},
                }
                for label in (
                    preflight.runner.PHASE2_INCIDENT_SOURCE_CAPTURE_REQUIRED_QUERY_FLAG_LABELS
                ):
                    value[
                        preflight.runner.PHASE2_REQUIRED_QUERY_FLAGS[label]
                    ] = True
                return value

        with tempfile.TemporaryDirectory() as temporary:
            report = preflight.runner.phase2_runtime_capability_preflight(
                Service(),
                Path(temporary),
                tracked_ck3_pid=7711,
                managed_restore_supervisor=True,
                focused_incident_source_capture=True,
            )
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(
            report["scope"],
            "focused_incident_source_capture_mcp_capability_profile",
        )
        self.assertTrue(report["focused_incident_source_capture"])
        self.assertNotIn(
            "incident_snapshot", report["required_bridge_capabilities"]
        )
        self.assertNotIn(
            "event_option_action_ack",
            report["required_bridge_capabilities"],
        )

    def test_waits_for_product_event_and_emits_consumable_schema2_entry(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            evidence = run_capture(root, service)
            entry = json.loads(
                (root / "registry-entry.json").read_text(encoding="utf-8")
            )

            self.assertEqual(evidence["result"], "GREEN")
            self.assertEqual(evidence["readiness"], "captured-real-checkpoint")
            self.assertFalse(evidence["gameplay_action_executed"])
            self.assertFalse(evidence["action_ack_used_as_state_evidence"])
            self.assertEqual(entry["schema_version"], 2)
            self.assertEqual(entry["source_event_definition_key"], "zg361.50")
            self.assertEqual(entry["seed_lineage_id"], SEED_LINEAGE_ID)
            self.assertEqual(entry["capture_lineage"], lineage())
            self.assertEqual(entry["player_character_id"], PLAYER)
            self.assertEqual(entry["owner_character_id"], service.notice_owner)
            self.assertNotEqual(
                entry["owner_character_id"], entry["player_character_id"]
            )
            self.assertFalse(
                entry["received_self_incident_checkpoint_receipt"][
                    "action_ack_used_as_state_evidence"
                ]
            )
            self.assertEqual(evidence["player_character_id"], PLAYER)
            self.assertEqual(evidence["subject_character_id"], PLAYER)
            self.assertEqual(evidence["event_root_character_id"], PLAYER)
            self.assertEqual(
                evidence["notice_owner_character_id"], service.notice_owner
            )
            self.assertTrue(evidence["option_shown"])
            self.assertTrue(evidence["option_enabled"])
            self.assertTrue(evidence["provider_ui_same_frame"])

            builder = Phase2SourceCheckpointRegistryBuilder(
                root / "registry-archive",
                seed_lineage_id=SEED_LINEAGE_ID,
                capture_lineage=lineage(),
            )
            for ordinal, handler in enumerate(
                ("capture_promotion_compensation", "capture_projects_metrics"),
                1,
            ):
                plan = phase2_event_sequence_plan(handler)
                checkpoint = root / f"prior-{ordinal}.ck3"
                checkpoint.write_bytes(f"prior-{ordinal}".encode("ascii"))
                sha256 = hashlib.sha256(
                    checkpoint.read_bytes()
                ).hexdigest().upper()
                builder.record(
                    plan,
                    source_checkpoint=checkpoint,
                    owner_character_id=9000 + ordinal,
                    player_character_id=PLAYER,
                    date_raw=100 + ordinal,
                    source_receipt=generic_receipt(
                        plan=plan,
                        owner=9000 + ordinal,
                        player=PLAYER,
                        date_raw=100 + ordinal,
                        sha256=sha256,
                    ),
                )
            incident_plan = phase2_event_sequence_plan(
                "capture_incidents_operations"
            )
            formal = builder.record(
                incident_plan,
                source_checkpoint=Path(entry["checkpoint"]["path"]),
                owner_character_id=entry["owner_character_id"],
                player_character_id=entry["player_character_id"],
                date_raw=entry["date_raw"],
                source_receipt=entry["source_receipt"],
                strict_incident_source_checkpoint_receipt=entry[
                    "received_self_incident_checkpoint_receipt"
                ],
            )
            self.assertTrue(
                Path(
                    formal["received_self_incident_checkpoint_receipt"][
                        "path"
                    ]
                ).is_file()
            )
            live_preflight = preflight.run_preflight(
                root / "capture.json", root / "registry-entry.json"
            )
            self.assertEqual(live_preflight["result"], "GREEN")
            self.assertTrue(live_preflight["live_gate_ready"])

    def test_visible_non_received_self_event_is_red_without_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            service.notice_owner = PLAYER
            with self.assertRaises(IncidentSourceCaptureEntryError) as raised:
                run_capture(root, service)
            self.assertEqual(
                raised.exception.reason_code,
                "visible_event_is_not_strict_received_self_zg361_50",
            )
            self.assertEqual(service.save_calls, 0)
            self.assertFalse((root / "strict-receipt.json").exists())

    def test_static_preflight_is_no_launch_and_live_pending(self) -> None:
        result = preflight.run_preflight()
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["readiness"], "static-ready-live-pending")
        self.assertFalse(result["ck3_started"])
        self.assertFalse(result["service_instantiated"])
        self.assertFalse(result["gameplay_result_claimed"])
        self.assertFalse(result["live_gate_ready"])
        self.assertEqual(
            result["live_checkpoint"]["reason_code"],
            "strict_incident_source_checkpoint_pending",
        )

    def test_wait_timeout_does_not_advance_or_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            service.event_key = None
            service.event_instance_id = None
            clock = FakeClock()
            with self.assertRaises(IncidentSourceCaptureEntryError) as raised:
                run_capture(
                    root,
                    service,
                    timeout_seconds=0.2,
                    clock=clock,
                )
            self.assertEqual(
                raised.exception.reason_code, "real_zg361_50_wait_timeout"
            )
            self.assertEqual(service.save_calls, 0)
            self.assertEqual(service.steps, [])
            self.assertFalse((root / "registry-entry.json").exists())

    def test_wrong_managed_pid_is_red_before_query_or_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureAndActionService(root)
            with self.assertRaises(IncidentSourceCaptureEntryError) as raised:
                wait_for_and_capture_incident_source_checkpoint(
                    service,
                    evidence_path=root / "capture.json",
                    checkpoint_root=root / "checkpoints",
                    receipt_path=root / "strict-receipt.json",
                    registry_entry_path=root / "registry-entry.json",
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage=lineage(),
                    tracked_ck3_pid=service.pid + 1,
                    timeout_seconds=1.0,
                    poll_interval_seconds=0.1,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_managed_session_mismatch",
            )
            self.assertEqual(service.save_calls, 0)


if __name__ == "__main__":
    unittest.main()
