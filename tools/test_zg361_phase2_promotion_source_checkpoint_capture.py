#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from test_zg361_phase2_promotion_compensation_action_cell import (  # noqa: E402
    GENERATION,
    OWNER,
    _FakeService,
)
from zg361_phase2_promotion_source_checkpoint_capture import (  # noqa: E402
    CAPTURE_ARTIFACT_KIND,
    EXACT_EXE_SHA256,
    EXACT_GAME_VERSION,
    PromotionSourceCheckpointCaptureError,
    build_no_launch_preflight,
    capture_promotion_source_checkpoint_v2,
    validate_promotion_source_capture_artifact_v2,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
)


SEED_LINEAGE_ID = "zg361-phase2-seed-live-promotion-unit"
TRACKED_PID = 2468


def _lineage() -> dict[str, object]:
    return {
        "seed_lineage_id": SEED_LINEAGE_ID,
        "evidence_class": "real_ck3",
        "session_kind": "managed_product_session",
        "product_only_runtime": True,
        "tracked_ck3_pid": TRACKED_PID,
        "connection_generation": GENERATION,
        "game_version": EXACT_GAME_VERSION,
        "executable_sha256": EXACT_EXE_SHA256,
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }


def _session() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_managed_product_session",
        "result": "GREEN",
        "managed_native_session": True,
        "product_only_runtime": True,
        "acceptance_fixture_loaded": False,
        "same_pid_gameplay_continuation_authorized": True,
        "tracked_ck3_pid": TRACKED_PID,
        "connection_generation": GENERATION,
        "seed_lineage_id": SEED_LINEAGE_ID,
        "game_version": EXACT_GAME_VERSION,
        "executable_sha256": EXACT_EXE_SHA256,
    }


class CaptureService(_FakeService):
    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.save_calls = 0

    def capabilities(self) -> dict[str, object]:
        result = super().capabilities()
        result.update(
            {
                "mode": "native-headless",
                "backend_id": "native-headless",
                "visual_fallback": False,
                "action_steps": ["save-checkpoint"],
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": TRACKED_PID,
                    "connection_generation": GENERATION,
                },
                "current_event_window_context_v1_query_supported": True,
                "checkpoint_materialization": {"configured": True},
            }
        )
        result["bridge_capabilities"].append("game.command.save-checkpoint")
        return result

    def snapshot(self) -> dict[str, object]:
        result = super().snapshot()
        result["played_character"]["alive"] = True
        result["diagnostics"]["bridge_pid"] = TRACKED_PID
        return result

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.save_calls += 1
        snapshot = self.snapshot()
        self.assert_revision = expected_revision
        path = self.root / "native-promotion-source.ck3"
        path.write_bytes(b"real-managed-product-promotion-source-checkpoint")
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        return {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "size": path.stat().st_size,
                "sha256": digest,
                "date_raw": snapshot["date_raw"],
                "episode_character_id": OWNER,
                "strategy": "native-save",
            },
            "materialization": {"available": True},
        }


class PromotionSourceCheckpointCaptureTests(unittest.TestCase):
    def test_no_launch_preflight_is_static_ready_and_incomplete(self) -> None:
        report = build_no_launch_preflight()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["service_instantiated"])
        self.assertFalse(report["checkpoint_written"])
        self.assertTrue(report["incomplete_for_canonical_4_entry_registry"])
        self.assertEqual(
            report["required_handler_order"], list(CHECKPOINT_REQUIRED_HANDLERS)
        )

    def test_live_callable_captures_exact_first_schema2_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = CaptureService(root)
            artifact_path = root / "promotion-source-capture-v2.json"
            result = capture_promotion_source_checkpoint_v2(
                service,
                checkpoint_root=root / "archive",
                capture_artifact_path=artifact_path,
                seed_lineage_id=SEED_LINEAGE_ID,
                capture_lineage=_lineage(),
                managed_product_session=_session(),
                sleeper=lambda _seconds: None,
            )

            self.assertEqual(result["schema_version"], 2)
            self.assertEqual(result["kind"], CAPTURE_ARTIFACT_KIND)
            self.assertEqual(result["result"], "GREEN")
            self.assertTrue(result["incomplete_for_canonical_4_entry_registry"])
            self.assertFalse(result["canonical_registry_ready"])
            self.assertEqual(
                result["captured_handlers"], [CHECKPOINT_REQUIRED_HANDLERS[0]]
            )
            self.assertEqual(
                result["missing_handlers"], list(CHECKPOINT_REQUIRED_HANDLERS[1:])
            )
            entry = result["entries"][0]
            self.assertEqual(entry["source_event_definition_key"], "zg361pp.147")
            self.assertEqual(entry["owner_character_id"], OWNER)
            self.assertEqual(entry["player_character_id"], OWNER)
            receipt = entry["source_receipt"]
            self.assertEqual(receipt["option_number"], 1)
            self.assertTrue(receipt["option_shown"])
            self.assertTrue(receipt["option_enabled"])
            self.assertFalse(receipt["event_option_action_executed"])
            self.assertFalse(receipt["action_ack_used_as_state_evidence"])
            self.assertEqual(
                set(receipt["saved_scope_bindings"]),
                {
                    "zg361_pp_prompt_owner",
                    "zg361_pp_prompt_subject",
                    "zg361_pp_prompt_case",
                    "zg361_pp_prompt_cycle",
                    "zg361_pp_prompt_mechanism",
                    "zg361_pp_prompt_state",
                },
            )
            self.assertEqual(service.save_calls, 1)
            self.assertFalse(service.selected)
            self.assertTrue(artifact_path.is_file())
            self.assertEqual(
                validate_promotion_source_capture_artifact_v2(
                    result, expected_seed_lineage_id=SEED_LINEAGE_ID
                ),
                result,
            )

    def test_live_callable_waits_for_the_real_event_without_advancing(self) -> None:
        class DelayedEventService(CaptureService):
            def __init__(self, root: Path) -> None:
                super().__init__(root)
                self.snapshot_calls = 0

            def snapshot(self) -> dict[str, object]:
                self.snapshot_calls += 1
                result = super().snapshot()
                if self.snapshot_calls <= 2:
                    result.pop("active_event")
                return result

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = DelayedEventService(root)
            result = capture_promotion_source_checkpoint_v2(
                service,
                checkpoint_root=root / "archive",
                capture_artifact_path=root / "capture.json",
                seed_lineage_id=SEED_LINEAGE_ID,
                capture_lineage=_lineage(),
                managed_product_session=_session(),
                poll_interval_seconds=0,
            )

        self.assertEqual(result["result"], "GREEN")
        self.assertGreaterEqual(service.snapshot_calls, 5)
        self.assertFalse(service.selected)

    def test_disabled_option_fails_before_native_save(self) -> None:
        class DisabledOptionService(CaptureService):
            def query_current_event_window_context_v1(
                self, event_instance_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                result = super().query_current_event_window_context_v1(
                    event_instance_id, expected_revision=expected_revision
                )
                result["current_event_window_context"]["options"][0][
                    "enabled"
                ] = False
                return result

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = DisabledOptionService(root)
            with self.assertRaises(
                PromotionSourceCheckpointCaptureError
            ) as raised:
                capture_promotion_source_checkpoint_v2(
                    service,
                    checkpoint_root=root / "archive",
                    capture_artifact_path=root / "capture.json",
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage=_lineage(),
                    managed_product_session=_session(),
                    sleeper=lambda _seconds: None,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "promotion_source_event_contract_invalid",
            )
            self.assertEqual(service.save_calls, 0)
            self.assertFalse(service.selected)

    def test_artifact_ack_or_completion_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = capture_promotion_source_checkpoint_v2(
                CaptureService(root),
                checkpoint_root=root / "archive",
                capture_artifact_path=root / "capture.json",
                seed_lineage_id=SEED_LINEAGE_ID,
                capture_lineage=_lineage(),
                managed_product_session=_session(),
                sleeper=lambda _seconds: None,
            )
            tampered = copy.deepcopy(result)
            tampered["entries"][0]["source_receipt"][
                "action_ack_used_as_state_evidence"
            ] = True
            with self.assertRaises(PromotionSourceCheckpointCaptureError):
                validate_promotion_source_capture_artifact_v2(tampered)
            completed = copy.deepcopy(result)
            completed["incomplete_for_canonical_4_entry_registry"] = False
            completed["canonical_registry_ready"] = True
            with self.assertRaises(PromotionSourceCheckpointCaptureError):
                validate_promotion_source_capture_artifact_v2(completed)

            wrong_subject = copy.deepcopy(result)
            wrong_subject["entries"][0]["source_receipt"][
                "subject_character_id"
            ] += 1
            with self.assertRaises(PromotionSourceCheckpointCaptureError):
                validate_promotion_source_capture_artifact_v2(wrong_subject)

            wrong_build = copy.deepcopy(result)
            wrong_build["capture_lineage"]["game_version"] = "drifted"
            with self.assertRaises(PromotionSourceCheckpointCaptureError):
                validate_promotion_source_capture_artifact_v2(wrong_build)


if __name__ == "__main__":
    unittest.main()
