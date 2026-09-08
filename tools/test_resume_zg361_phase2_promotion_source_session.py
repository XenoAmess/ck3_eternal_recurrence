#!/usr/bin/env python3
"""CK3-free retained promotion-source diagnostic regression tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def _install_optional_desktop_stubs() -> None:
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
        if importlib.util.find_spec(name) is not None:
            continue
        module = types.ModuleType(name)
        module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
        for attribute in names:
            setattr(module, attribute, None)
        sys.modules[name] = module


_install_optional_desktop_stubs()
sys.path.insert(0, str(ROOT / "tools"))

import resume_zg361_phase2_promotion_source_session as client  # noqa: E402
import zg361_phase2_promotion_source_production_entry as entry  # noqa: E402
import run_zhongguo_acceptance as runner  # noqa: E402


PREFIX = b"[11:00:00][I][unit.cpp:1]: source client boundary\n"
PROJECT_ERROR = (
    b"[11:01:00][E][pdx_data_factory.cpp:1364]: Failed to find type "
    b"'scope:zg361_ch_a_event_subject'\n"
    b"[11:01:00][E][pdx_data_localize.cpp:146]: Data error in loc string "
    b"'zg361ch.m001.desc'\n"
)


def _player_manager_seed_contract() -> dict[str, object]:
    return {
        "kind": runner.PHASE2_PLAYER_MANAGER_SEED_KIND,
        "seed_purpose": runner.PHASE2_PLAYER_MANAGER_SEED_PURPOSE,
        "ready": True,
        "status": "ready",
        "source": {"sha256": "a" * 64},
        "saved_state": {
            "played_character_id": 29037,
            "player_history_id": None,
        },
        "manager_entry": {
            "schema_version": 1,
            "manager_character_id": 29037,
            "reviewable_subject_character_id": 32904,
            "manager_scope": "zga_phase2_manager_owner",
            "subject_scope": "zga_phase2_manager_subject",
            "human": True,
            "alive": True,
            "landed": True,
            "celestial_liege": True,
            "game_rule_enabled": True,
            "existing_direct_reviewable_vassal_count_minimum": 1,
            "b1_active": False,
            "central_active": False,
            "pp_active": False,
            "review_now_eligible": True,
        },
    }


class _Driver:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class RetainedRuntimeDiagnosticTests(unittest.TestCase):
    def test_capture_lineage_uses_canonical_managed_session_kind(self) -> None:
        source = Path(client.__file__).read_text(encoding="utf-8")
        self.assertIn('"session_kind": "managed_product_session",', source)
        self.assertNotIn("managed_product_session_retained_reconnect", source)

    def _arrange_source(self, root: Path) -> tuple[Path, Path, str]:
        state = root / "state"
        profile = state / "profile"
        logs = profile / "logs"
        logs.mkdir(parents=True)
        cell = root / "source-cell"
        cell.mkdir()
        pipe = r"\\.\pipe\retained-diagnostic-unit"
        (cell / "09_phase2_native_session_retained.json").write_text(
            json.dumps(
                {
                    "result": "RETAINED",
                    "reconnect_authorized": True,
                    "process_restart_required": False,
                    "state_dir": str(state.resolve()),
                    "profile_dir": str(profile.resolve()),
                    "pipe": pipe,
                    "bridge_pid": 361116,
                }
            ),
            encoding="utf-8",
        )
        (cell / "00_phase2_seed_install.json").write_text(
            json.dumps(
                {
                    "result": "GREEN",
                    "contract": _player_manager_seed_contract(),
                }
            ),
            encoding="utf-8",
        )
        (cell / "03_loader_gate.json").write_text(
            json.dumps({"result": "GREEN"}), encoding="utf-8"
        )
        for name in ("error.log", "debug.log"):
            (cell / f"final_{name}").write_bytes(PREFIX)
            (logs / name).write_bytes(PREFIX + PROJECT_ERROR)
        return state, cell, pipe

    def test_source_cold_offsets_do_not_rebaseline_at_reconnect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, _pipe = self._arrange_source(root)
            offsets, evidence = client.source_cold_runtime_diagnostic_offsets(
                source_run_cell=cell,
                profile_dir=state / "profile",
            )

        self.assertEqual(offsets["error.log"], len(PREFIX))
        self.assertEqual(offsets["debug.log"], len(PREFIX))
        self.assertEqual(
            evidence["reconnect_observed_offsets"]["error.log"],
            len(PREFIX + PROJECT_ERROR),
        )
        self.assertEqual(
            evidence["reconnect_observed_offsets"]["debug.log"],
            len(PREFIX + PROJECT_ERROR),
        )

    def test_error_and_debug_mirror_is_one_product_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, _pipe = self._arrange_source(root)
            offsets, _evidence = client.source_cold_runtime_diagnostic_offsets(
                source_run_cell=cell,
                profile_dir=state / "profile",
            )
            blocking, warnings = client.retained_runtime_project_diagnostics(
                state / "profile", offsets
            )

        self.assertEqual(len(blocking), 1)
        self.assertIn("zg361ch.m001.desc", blocking[0])
        self.assertEqual(warnings, [])

    def test_entry_probe_preempts_absolute_550_day_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": (
                    entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
                    + entry.MAX_ADVANCE_DAYS * entry.HOURS_PER_DAY
                    + 1
                ),
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )
            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )

        self.assertEqual(report["result"], "RED")
        self.assertIn("1 product runtime diagnostic(s)", report["error_reason"])
        self.assertIn("zg361ch.m001.desc", report["error_reason"])
        self.assertNotIn("550-day", report["error_reason"])
        diagnostics = report["runtime_diagnostics"]
        self.assertEqual(diagnostics["blocking_diagnostic_count"], 1)
        self.assertGreaterEqual(diagnostics["scan_count"], 2)

    def test_terminal_scan_overrides_entry_timeout_that_skipped_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            logs = state / "profile" / "logs"
            for name in ("error.log", "debug.log"):
                (logs / name).write_bytes(PREFIX)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )

            def timeout_after_writing_error(*args: object, **kwargs: object) -> None:
                for name in ("error.log", "debug.log"):
                    with (logs / name).open("ab") as handle:
                        handle.write(PROJECT_ERROR)
                raise entry.PromotionProductionEntryError(
                    "promotion path exceeded its 550-day product observation bound"
                )

            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
                mock.patch.object(
                    client,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=timeout_after_writing_error,
                ),
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )
            persisted = json.loads(
                (artifacts / "02_retained_runtime_diagnostics.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(report["result"], "RED")
        self.assertIn("1 product runtime diagnostic(s)", report["error_reason"])
        self.assertNotIn("550-day", report["error_reason"])
        self.assertEqual(persisted["blocking_diagnostic_count"], 1)

    def test_binding_failure_report_preserves_rejected_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            for name in ("error.log", "debug.log"):
                (state / "profile" / "logs" / name).write_bytes(PREFIX)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )
            rejected = {
                "snapshot_id": "native:117",
                "map_ready": False,
                "actual_player_character_id": None,
                "expected_player_character_id": 29037,
                "actual_connection_generation": 1,
                "expected_connection_generation": 1,
            }
            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
                mock.patch.object(
                    client,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=entry.PromotionBindingError(rejected),
                ),
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )

        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["promotion_binding_failure"], rejected)
        self.assertIn("PromotionBindingError", report["error_reason"])

    def test_unknown_interrupt_attempts_durable_checkpoint_before_client_close(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            for name in ("error.log", "debug.log"):
                (state / "profile" / "logs" / name).write_bytes(PREFIX)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )
            unexpected = {"event_definition_key": "natural_disaster.9999"}

            def unknown_event(*args: object, **kwargs: object) -> None:
                kwargs["evidence_out"]["unexpected_event"] = unexpected
                raise entry.PromotionProductionEntryError("unknown interrupt")

            durable = {
                "result": "GREEN",
                "durable_recovery_ready": True,
            }
            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
                mock.patch.object(
                    client,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=unknown_event,
                ),
                mock.patch.object(
                    client,
                    "attempt_unexpected_event_durable_checkpoint",
                    return_value=durable,
                ) as checkpoint,
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )

        self.assertEqual(report["result"], "RED")
        self.assertTrue(report["unknown_interrupt_retention"])
        self.assertTrue(report["unexpected_event_durable_recovery_ready"])
        self.assertEqual(report["unexpected_event_durable_checkpoint"], durable)
        checkpoint.assert_called_once_with(
            service,
            state_dir=state.resolve(),
            unexpected_event=unexpected,
            artifact_path=(
                artifacts.resolve()
                / "05_unexpected_event_durable_checkpoint.json"
            ),
        )


if __name__ == "__main__":
    unittest.main()
