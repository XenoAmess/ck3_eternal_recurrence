"""Focused safety tests for the offline desktop recovery state machine."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import pywintypes
from PIL import Image

import desktop_steam_offline_recovery as recovery
import steam_offline_fresh_frame as freshness


TASK = "offline-recovery-test"


def task(task_id: str, resource: bool = True) -> dict:
    return {"task_id": task_id, "state": "running",
            "resources": [recovery.SCREEN_RESOURCE] if resource else []}


def snapshot() -> dict:
    return {"schema": "ck3.desktop_steam_offline_recovery.v1",
            "todesk_service": {"status": "running", "pid": 11},
            "ck3_pids": [], "steam_windows": [{"hwnd": 123, "pid": 456}],
            "screen_owners": [TASK], "steam_offline_status_observed": None}


class SteamWindowIdentityTests(unittest.TestCase):
    def enumerate_windows(self, windows: list[dict]) -> list[tuple[int, int]]:
        by_hwnd = {row["hwnd"]: row for row in windows}
        by_pid = {row["pid"]: row for row in windows}

        def enumerate_mock(visit, context) -> None:
            for row in windows:
                visit(row["hwnd"], context)

        def process_mock(pid: int) -> Mock:
            return Mock(**{"name.return_value": by_pid[pid]["process"]})

        with (patch.object(freshness.win32gui, "EnumWindows", side_effect=enumerate_mock),
              patch.object(freshness.win32gui, "IsWindowVisible",
                           side_effect=lambda hwnd: by_hwnd[hwnd]["visible"]),
              patch.object(freshness.win32gui, "GetWindowText",
                           side_effect=lambda hwnd: by_hwnd[hwnd]["title"]),
              patch.object(freshness.win32process, "GetWindowThreadProcessId",
                           side_effect=lambda hwnd: (1, by_hwnd[hwnd]["pid"])),
              patch.object(freshness.psutil, "Process", side_effect=process_mock)):
            return freshness._steam_windows()

    def test_native_steam_sdl_main_window_is_accepted(self) -> None:
        self.assertEqual(self.enumerate_windows([
            {"hwnd": 123, "pid": 456, "title": "Steam", "visible": True,
             "process": "steam.exe"},
        ]), [(123, 456)])

    def test_legacy_cef_main_window_is_accepted(self) -> None:
        self.assertEqual(self.enumerate_windows([
            {"hwnd": 123, "pid": 456, "title": "Steam", "visible": True,
             "process": "STEAMWEBHELPER.EXE"},
        ]), [(123, 456)])

    def test_title_visibility_and_live_steam_process_are_all_required(self) -> None:
        self.assertEqual(self.enumerate_windows([
            {"hwnd": 1, "pid": 11, "title": "Steam", "visible": True,
             "process": "other.exe"},
            {"hwnd": 2, "pid": 12, "title": "Steam Settings", "visible": True,
             "process": "steam.exe"},
            {"hwnd": 3, "pid": 13, "title": "steam", "visible": True,
             "process": "steamwebhelper.exe"},
            {"hwnd": 4, "pid": 14, "title": "Steam", "visible": False,
             "process": "steam.exe"},
        ]), [])

    def test_multiple_steam_hosts_remain_ambiguous_and_block_capture(self) -> None:
        windows = self.enumerate_windows([
            {"hwnd": 123, "pid": 456, "title": "Steam", "visible": True,
             "process": "steam.exe"},
            {"hwnd": 789, "pid": 987, "title": "Steam", "visible": True,
             "process": "steamwebhelper.exe"},
        ])
        self.assertEqual(windows, [(123, 456), (789, 987)])
        self.assertIn("steam_window_not_unique", recovery.preflight(
            [task(TASK)], TASK, [], {"status": "running"}, windows))
        with tempfile.TemporaryDirectory() as temp:
            with (patch.object(freshness.psutil, "process_iter", return_value=[]),
                  patch.object(freshness, "_steam_windows", return_value=windows),
                  patch.object(freshness.win32gui, "MoveWindow") as move,
                  patch.object(freshness.pyautogui, "screenshot") as screenshot):
                with self.assertRaisesRegex(RuntimeError, "found 2"):
                    freshness.capture(Path(temp))
            move.assert_not_called()
            screenshot.assert_not_called()


class DesktopRecoveryTests(unittest.TestCase):
    def test_repeated_full_frame_after_two_minutes_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = root / "reference.json"
            probe = root / "probe"
            probe.mkdir()
            captured = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
            receipt = {
                "schema": "ck3.steam_fresh_desktop_frame.v1",
                "captured_at_utc": captured,
                "steam_hwnd": 123,
                "desktop_size": [1024, 768],
                "moved_rect": [20, 0, 982, 768],
                "moved_identity": {"bytes": 63699, "sha256": "same"},
            }
            reference.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, recovery.STALE_CAPTURE_ERROR):
                recovery.reject_repeated_frame(reference, receipt, probe)
            stale = json.loads((probe / "steam-frame-stale.json").read_text(encoding="utf-8"))
            self.assertEqual(stale["moved_identity"]["sha256"], "same")

    def test_old_clock_pixels_detect_composited_stale_desktop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            reference = Path(temp) / "old.png"
            old = Image.new("RGB", (40, 20), "black")
            old.putpixel((35, 10), (255, 255, 255))
            old.save(reference)
            timestamp = time.time() - 180
            os.utime(reference, (timestamp, timestamp))
            moved = old.copy()
            moved.putpixel((2, 2), (200, 200, 200))
            same_clock = freshness._unchanged_clock_region(reference, moved, (30, 0, 40, 20))
            self.assertTrue(same_clock["clock_pixels_unchanged"])
            moved.putpixel((35, 10), (100, 100, 100))
            new_clock = freshness._unchanged_clock_region(reference, moved, (30, 0, 40, 20))
            self.assertFalse(new_clock["clock_pixels_unchanged"])

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

    def test_minimized_steam_is_restored_before_fresh_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with (patch.object(recovery.win32gui, "GetForegroundWindow",
                               side_effect=[999, 123]),
                  patch.object(recovery.win32gui, "IsIconic", return_value=True),
                  patch.object(recovery.win32gui, "ShowWindow") as show,
                  patch.object(recovery.win32gui, "SetForegroundWindow"),
                  patch.object(recovery.win32gui, "IsWindow", return_value=False),
                  patch.object(recovery.steam_offline_fresh_frame, "capture",
                               return_value={"moving_edge_changed": True})):
                receipt = recovery.capture_fresh_frame(Path(temp), 123, True)
        self.assertTrue(receipt["moving_edge_changed"])
        show.assert_called_once_with(123, recovery.win32con.SW_RESTORE)

    def test_foreground_denial_becomes_recovery_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with (patch.object(recovery.win32gui, "GetForegroundWindow", return_value=999),
                  patch.object(recovery.win32gui, "IsIconic", return_value=True),
                  patch.object(recovery.win32gui, "ShowWindow"),
                  patch.object(recovery.win32gui, "SetForegroundWindow",
                               side_effect=pywintypes.error(0, "SetForegroundWindow", "denied"))):
                with self.assertRaisesRegex(RuntimeError, "could not make Steam foreground"):
                    recovery.capture_fresh_frame(Path(temp), 123, True)

    def test_foreground_restore_denial_keeps_fresh_frame_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with (patch.object(recovery.win32gui, "GetForegroundWindow",
                               side_effect=[999, 123]),
                  patch.object(recovery.win32gui, "ShowWindow"),
                  patch.object(recovery.win32gui, "SetForegroundWindow",
                               side_effect=[None, pywintypes.error(
                                   0, "SetForegroundWindow", "denied")]),
                  patch.object(recovery.win32gui, "IsWindow", return_value=True),
                  patch.object(recovery.steam_offline_fresh_frame, "capture",
                               return_value={"moving_edge_changed": True})):
                receipt = recovery.capture_fresh_frame(Path(temp), 123, True)
        self.assertTrue(receipt["moving_edge_changed"])
        self.assertIn("SetForegroundWindow", receipt["foreground_restore_error"])

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
