#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def install_optional_desktop_import_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


install_optional_desktop_import_stubs()

import run_zhongguo_acceptance as runner  # noqa: E402


def natural_entry() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_production_entry",
        "result": "GREEN",
        "readiness": "paused-real-zg361we.356",
        "prefer_natural_cycle": True,
        "pause_on_event_definition_key": "zg361we.356",
        "pause_on_event_occurrence": 3,
        "target_occurrence_index": 3,
        "target_binding": {"instance_id": 35603},
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "action_ack_used_as_state_evidence": False,
        "timeline_interrupt_drains": [
            {"event_definition_key": "zg361cl.390", "result": "GREEN"},
            {"event_definition_key": "zg361we.355", "result": "GREEN"},
            {"event_definition_key": "zg361we.356", "result": "GREEN"},
            {"event_definition_key": "zg361we.355", "result": "GREEN"},
            {"event_definition_key": "zg361we.356", "result": "GREEN"},
        ],
    }


class EndgameSourceProductionEntryRunnerTests(unittest.TestCase):
    def test_natural_third_source_entry_precedes_capture_and_binds_lineage(
        self,
    ) -> None:
        calls: list[str] = []

        def enter(_service: object, **kwargs: object) -> dict[str, object]:
            calls.append("entry")
            retained = kwargs["evidence_out"]
            self.assertIsInstance(retained, dict)
            assert isinstance(retained, dict)
            retained.update(copy.deepcopy(natural_entry()))
            return retained

        def capture(_service: object, **kwargs: object) -> dict[str, object]:
            calls.append("capture")
            return {
                "result": "GREEN",
                "readiness": "live-pending",
                "source_checkpoint_captured": True,
                "phase2_complete": False,
            }

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with (
                mock.patch.object(
                    runner,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=enter,
                ) as entry,
                mock.patch.object(
                    runner,
                    "_phase2_promo_receipt_sources",
                    return_value=(
                        {"seed_lineage_id": "zg361-phase2-seed-unit"},
                        object(),
                        object(),
                    ),
                ),
                mock.patch.object(
                    runner,
                    "capture_cross_cycle_endgame_source_checkpoint_v1",
                    side_effect=capture,
                ) as capture_call,
            ):
                result = runner.run_phase2_endgame_source_capture_scenario(
                    object(),
                    artifacts,
                    prefix_manifest={"kind": "unit-prefix"},
                    expected_owner_character_id=32904,
                    expected_date_raw=53230000,
                    seed_install={"result": "GREEN"},
                    bootstrap={"enabled_mods": ["product"]},
                    runtime_identity={"identity": "unit"},
                    game_version="1.19.0.6",
                    executable_sha256="A" * 64,
                    production_entry_timeout_seconds=12.5,
                )
            entry_artifact = json.loads(
                (
                    artifacts
                    / "04_phase2_endgame_source_production_entry.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(calls, ["entry", "capture"])
        self.assertEqual(result["result"], "GREEN")
        entry.assert_called_once()
        self.assertEqual(entry.call_args.kwargs["timeout_seconds"], 12.5)
        self.assertTrue(entry.call_args.kwargs["prefer_natural_cycle"])
        self.assertEqual(
            entry.call_args.kwargs["pause_on_event_definition_key"],
            "zg361we.356",
        )
        self.assertEqual(entry.call_args.kwargs["pause_on_event_occurrence"], 3)
        lineage = capture_call.call_args.kwargs["runtime_capture_lineage"]
        contract = lineage["endgame_production_entry"]
        self.assertEqual(contract["result"], "GREEN")
        self.assertEqual(contract["stage_nine_digest_drain_ordinal"], 1)
        self.assertEqual(contract["prior_endgame_source_drain_ordinals"], [3, 5])
        self.assertFalse(contract["fixture_used"])
        self.assertFalse(contract["console_used"])
        self.assertFalse(contract["generic_character_rebind_used"])
        self.assertEqual(
            entry_artifact["natural_entry_contract"], contract
        )
        self.assertTrue(entry_artifact["runner_call_completed"])

    def test_invalid_natural_entry_never_reaches_capture(self) -> None:
        invalid_entries = {}
        fixture = natural_entry()
        fixture["fixture_used"] = True
        invalid_entries["fixture"] = fixture
        missing_stage_nine = natural_entry()
        missing_stage_nine["timeline_interrupt_drains"] = [
            row
            for row in missing_stage_nine["timeline_interrupt_drains"]
            if row["event_definition_key"] != "zg361cl.390"
        ]
        invalid_entries["missing_stage_nine"] = missing_stage_nine
        red_drain = natural_entry()
        red_drain["timeline_interrupt_drains"][2]["result"] = "RED"
        invalid_entries["red_prior_source_drain"] = red_drain
        wrong_occurrence = natural_entry()
        wrong_occurrence["target_occurrence_index"] = 2
        invalid_entries["wrong_occurrence"] = wrong_occurrence

        for label, entry_value in invalid_entries.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                artifacts = Path(temporary)

                def enter(
                    _service: object, **kwargs: object
                ) -> dict[str, object]:
                    retained = kwargs["evidence_out"]
                    assert isinstance(retained, dict)
                    retained.update(copy.deepcopy(entry_value))
                    return retained

                with (
                    mock.patch.object(
                        runner,
                        "enter_promotion_source_checkpoint_v1",
                        side_effect=enter,
                    ),
                    mock.patch.object(
                        runner, "_phase2_promo_receipt_sources"
                    ) as receipt_sources,
                    mock.patch.object(
                        runner,
                        "capture_cross_cycle_endgame_source_checkpoint_v1",
                    ) as capture_call,
                ):
                    with self.assertRaisesRegex(
                        runner.acceptance.RunnerError,
                        "natural production entry contract RED",
                    ):
                        runner.run_phase2_endgame_source_capture_scenario(
                            object(),
                            artifacts,
                            prefix_manifest={"kind": "unit-prefix"},
                            expected_owner_character_id=32904,
                            expected_date_raw=53230000,
                            seed_install={"result": "GREEN"},
                            bootstrap={"enabled_mods": ["product"]},
                            runtime_identity={"identity": "unit"},
                            game_version="1.19.0.6",
                            executable_sha256="A" * 64,
                        )
                receipt_sources.assert_not_called()
                capture_call.assert_not_called()
                artifact = json.loads(
                    (
                        artifacts
                        / "04_phase2_endgame_source_production_entry.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    artifact["natural_entry_contract"]["result"], "RED"
                )

    def test_entry_exception_is_durable_and_capture_is_not_attempted(self) -> None:
        def enter(_service: object, **kwargs: object) -> None:
            retained = kwargs["evidence_out"]
            assert isinstance(retained, dict)
            retained.update(copy.deepcopy(natural_entry()))
            raise RuntimeError("natural entry interrupted")

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with (
                mock.patch.object(
                    runner,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=enter,
                ),
                mock.patch.object(
                    runner,
                    "capture_cross_cycle_endgame_source_checkpoint_v1",
                ) as capture_call,
            ):
                with self.assertRaisesRegex(
                    runner.acceptance.RunnerError,
                    "natural entry interrupted",
                ):
                    runner.run_phase2_endgame_source_capture_scenario(
                        object(),
                        artifacts,
                        prefix_manifest={"kind": "unit-prefix"},
                        expected_owner_character_id=32904,
                        expected_date_raw=53230000,
                        seed_install={"result": "GREEN"},
                        bootstrap={"enabled_mods": ["product"]},
                        runtime_identity={"identity": "unit"},
                        game_version="1.19.0.6",
                        executable_sha256="A" * 64,
                    )
            artifact = json.loads(
                (
                    artifacts
                    / "04_phase2_endgame_source_production_entry.json"
                ).read_text(encoding="utf-8")
            )
        capture_call.assert_not_called()
        self.assertFalse(artifact["runner_call_completed"])
        self.assertEqual(artifact["natural_entry_contract"]["result"], "RED")
        self.assertIn("natural entry interrupted", artifact["error_reason"])

    def test_focused_capability_gate_is_the_exact_entry_capture_union(self) -> None:
        self.assertEqual(
            runner.PHASE2_ENDGAME_SOURCE_CAPTURE_REQUIRED_BRIDGE_CAPABILITY_LABELS,
            (
                "paused_snapshot",
                "map_ready_state",
                "played_character_state",
                "active_event_state",
                "save_checkpoint",
                "current_event_context",
                "pause_timeline",
                "resume_timeline",
                "fast_timeline_speed",
                "event_option_action_ack",
                "promotion_source_progress_transport",
                "review_now_action_transport",
            ),
        )
        self.assertEqual(
            runner.PHASE2_ENDGAME_SOURCE_CAPTURE_REQUIRED_QUERY_FLAG_LABELS,
            ("current_event_context",),
        )
        self.assertEqual(
            runner.PHASE2_ENDGAME_SOURCE_CAPTURE_REQUIRED_ACTION_STEP_LABELS,
            (
                "save_checkpoint",
                "pause_timeline",
                "resume_timeline",
                "fast_timeline_speed",
            ),
        )

    def test_timeout_is_validated_and_exposed_by_cli(self) -> None:
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError,
            "endgame production entry timeout must be positive",
        ):
            runner.main(phase2_endgame_production_entry_timeout_seconds=0)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(
                runner.acceptance.RunnerError,
                "endgame production entry timeout must be positive",
            ):
                runner.run_cell(
                    root / "artifacts",
                    root / "userdir",
                    True,
                    state_dir=root / "state",
                    native_bridge=object(),
                    phase2_endgame_production_entry_timeout_seconds=0,
                )
        runner_source = (TOOLS / "run_zhongguo_acceptance.py").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn(
            "--phase2-endgame-production-entry-timeout-seconds",
            runner_source,
        )


if __name__ == "__main__":
    unittest.main()
