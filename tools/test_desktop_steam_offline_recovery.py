"""Focused safety tests for the offline desktop recovery state machine."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import desktop_steam_offline_recovery as recovery


TASK = "offline-recovery-test"


def task(task_id: str, resource: bool = True) -> dict:
    return {"task_id": task_id, "state": "running",
            "resources": [recovery.SCREEN_RESOURCE] if resource else []}


def snapshot() -> dict:
    return {"schema": "ck3.desktop_steam_offline_recovery.v1",
            "todesk_service": {"status": "running", "pid": 11},
            "ck3_pids": [], "steam_windows": [{"hwnd": 123, "pid": 456}],
            "screen_owners": [TASK], "steam_offline_status_observed": None}


class DesktopRecoveryTests(unittest.TestCase):
    def test_foreground_activation_waits_for_async_window_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with (patch.object(recovery.win32gui, "GetForegroundWindow",
                               side_effect=[999, 999, 123]),
                  patch.object(recovery.win32gui, "ShowWindow"),
                  patch.object(recovery.win32gui, "SetForegroundWindow") as activate,
                  patch.object(recovery.win32gui, "IsWindow", return_value=False),
                  patch.object(recovery.time, "sleep") as sleep,
                  patch.object(recovery.steam_offline_fresh_frame, "capture",
                               return_value={"moving_edge_changed": True}) as capture):
                receipt = recovery.capture_fresh_frame(Path(temp), 123, True)
            self.assertTrue(receipt["moving_edge_changed"])
            activate.assert_called_once_with(123)
            sleep.assert_called_once_with(0.05)
            capture.assert_called_once()

    def test_stale_screen_record_is_ignored_only_when_its_pid_is_dead(self) -> None:
        old = {**task("old"), "stale": True, "pid": 2696}
        with patch.object(recovery.psutil, "pid_exists", return_value=False):
            self.assertEqual(recovery.screen_owners([old, task(TASK)]), [TASK])
        with patch.object(recovery.psutil, "pid_exists", return_value=True):
            self.assertEqual(recovery.screen_owners([old, task(TASK)]), [TASK, "old"])

    def test_foreign_screen_owner_blocks_even_when_steam_and_service_exist(self) -> None:
        reasons = recovery.preflight([task("other"), task(TASK)], TASK, [99],
                                     {"status": "running"}, [(123, 456)])
        self.assertEqual(reasons, ["exclusive_screen_lease_missing_or_conflicted", "ck3_running"])

    def test_successful_fresh_frame_never_restarts_running_todesk(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            args = Namespace(output_dir=Path(temp) / "attempt", task_bus=Path("bus"),
                             task_id=TASK, bring_steam_forward=False,
                             restart_running_todesk_on_stale=True,
                             service_timeout_seconds=2)
            with (patch.object(recovery, "inspect", return_value=snapshot()),
                  patch.object(recovery, "task_bus_tasks", return_value=[task(TASK)]),
                  patch.object(recovery, "ck3_pids", return_value=[]),
                  patch.object(recovery, "recorder_pids", return_value=[]),
                  patch.object(recovery, "service_state", return_value={"status": "running", "pid": 11}),
                  patch.object(recovery.steam_offline_fresh_frame, "_steam_windows",
                               return_value=[(123, 456)]),
                  patch.object(recovery, "ensure_service_running") as ensure,
                  patch.object(recovery, "capture_fresh_frame",
                               return_value={"moving_edge_changed": True,
                                             "moved_identity": {"path": "new.png", "sha256": "abc"}}),
                  patch.object(recovery, "restart_running_service") as restart):
                report = recovery.recover(args)
            self.assertEqual(report["outcome"], "fresh_frame_needs_offline_visual_review")
            self.assertIsNone(report["steam_offline_status_observed"])
            self.assertEqual(report["fresh_frame"]["image_identity"]["sha256"], "abc")
            self.assertFalse(report["steam_mode_mutation_attempted"])
            ensure.assert_called_once()
            restart.assert_not_called()

    def test_stale_capture_restarts_service_only_with_lease_then_reprobes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            args = Namespace(output_dir=Path(temp) / "attempt", task_bus=Path("bus"),
                             task_id=TASK, bring_steam_forward=True,
                             restart_running_todesk_on_stale=True,
                             service_timeout_seconds=2)
            with (patch.object(recovery, "inspect", return_value=snapshot()),
                  patch.object(recovery, "task_bus_tasks", return_value=[task(TASK)]),
                  patch.object(recovery, "ck3_pids", return_value=[]),
                  patch.object(recovery, "recorder_pids", return_value=[]),
                  patch.object(recovery, "service_state", return_value={"status": "running", "pid": 11}),
                  patch.object(recovery.steam_offline_fresh_frame, "_steam_windows",
                               return_value=[(123, 456)]),
                  patch.object(recovery, "ensure_service_running"),
                  patch.object(recovery, "capture_fresh_frame",
                               side_effect=[RuntimeError(recovery.STALE_CAPTURE_ERROR),
                                            {"moving_edge_changed": True}]) as capture,
                  patch.object(recovery, "restart_running_service",
                               return_value={"status": "running", "pid": 12}) as restart):
                report = recovery.recover(args)
            self.assertEqual(report["outcome"], "fresh_frame_needs_offline_visual_review")
            self.assertEqual(capture.call_count, 2)
            restart.assert_called_once_with(2)
            self.assertTrue((args.output_dir / "probe-1").is_dir())
            self.assertTrue((args.output_dir / "probe-2").is_dir())

    def test_stale_capture_does_not_restart_service_while_recording(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            args = Namespace(output_dir=Path(temp) / "attempt", task_bus=Path("bus"),
                             task_id=TASK, bring_steam_forward=True,
                             restart_running_todesk_on_stale=True,
                             service_timeout_seconds=2)
            with (patch.object(recovery, "inspect", return_value=snapshot()),
                  patch.object(recovery, "task_bus_tasks", return_value=[task(TASK)]),
                  patch.object(recovery, "ck3_pids", return_value=[]),
                  patch.object(recovery, "recorder_pids", return_value=[99]),
                  patch.object(recovery, "service_state", return_value={"status": "running", "pid": 11}),
                  patch.object(recovery.steam_offline_fresh_frame, "_steam_windows",
                               return_value=[(123, 456)]),
                  patch.object(recovery, "ensure_service_running"),
                  patch.object(recovery, "capture_fresh_frame",
                               side_effect=RuntimeError(recovery.STALE_CAPTURE_ERROR)),
                  patch.object(recovery, "restart_running_service") as restart):
                report = recovery.recover(args)
            self.assertEqual(report["outcome"], "stale_or_unavailable")
            restart.assert_not_called()
            self.assertFalse((args.output_dir / "probe-2").exists())

    def test_recovery_refuses_without_own_screen_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            args = Namespace(output_dir=Path(temp) / "attempt", task_bus=Path("bus"),
                             task_id=TASK, bring_steam_forward=True,
                             restart_running_todesk_on_stale=True,
                             service_timeout_seconds=2)
            with (patch.object(recovery, "inspect", return_value=snapshot()),
                  patch.object(recovery, "task_bus_tasks", return_value=[task("other")]),
                  patch.object(recovery, "ck3_pids", return_value=[]),
                  patch.object(recovery, "service_state", return_value={"status": "running", "pid": 11}),
                  patch.object(recovery.steam_offline_fresh_frame, "_steam_windows",
                               return_value=[(123, 456)]),
                  patch.object(recovery, "ensure_service_running") as ensure,
                  patch.object(recovery, "capture_fresh_frame") as capture):
                report = recovery.recover(args)
            self.assertEqual(report["outcome"], "blocked")
            ensure.assert_not_called()
            capture.assert_not_called()

    def test_service_restart_attempts_to_start_after_stop_probe_error(self) -> None:
        with (patch.object(recovery, "service_state",
                           side_effect=[{"status": "running"}, {"status": "stopped"},
                                        {"status": "stopped"}, {"status": "stopped"}]),
              patch.object(recovery, "sc") as sc,
              patch.object(recovery, "wait_service",
                           side_effect=[RuntimeError("probe failed"), {"status": "running"}])):
            with self.assertRaisesRegex(RuntimeError, "probe failed"):
                recovery.restart_running_service(2)
        self.assertEqual([call.args[0] for call in sc.call_args_list], ["stop", "start"])


if __name__ == "__main__":
    unittest.main()
