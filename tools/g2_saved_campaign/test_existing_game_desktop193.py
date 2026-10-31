"""Policy193 software cases: every process/window/registry boundary is a double."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

REPOSITORY = Path(os.environ.get("VIDEO_SOURCE193_REPO", str(Path(__file__).resolve().parents[2])))
CANDIDATE = Path(os.environ.get("VIDEO_SOURCE193_ROOT", str(REPOSITORY)))
spec = importlib.util.spec_from_file_location("obs_existing_policy193", CANDIDATE / "tools/ck3_obs_capture.py")
capture = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = capture
spec.loader.exec_module(capture)
PID, HWND, BIRTH = 71464, 319967214, 134378397668266369
D1, D2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"


class BeforeProcess193(RuntimeError):
    pass


class ExistingGameDesktop193Tests(unittest.TestCase):
    def setUp(self):
        temporary = Path(os.environ.get("VIDEO_SOURCE193_TMP", tempfile.gettempdir()))
        temporary.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary)
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def job(self):
        return {"schema": capture.SCHEMA, "session_id": D1, "pid": PID, "hwnd": HWND,
                "duration_seconds": 15, "max_output_bytes": 192 * 1024**2,
                "recording_root": str(self.root), "receipt_root": str(self.root / "receipts"),
                "capture_mode": "game_decision_text", "overlay": None,
                "decision_text_file": str(self.root / "current.txt"), "desktop_id": D2,
                "game_creation_filetime": BIRTH, "decision_text_publisher": {},
                "decision_text_publisher_receipt": {}, "placement_observation_policy": "existingGameDesktop"}

    def placement(self):
        desktop = {"window_hwnd": HWND, "desktop_id": D2, "on_current_virtual_desktop": True,
                   "dwm_cloaked_flags": 0}
        return {"status": "GREEN", "pid": PID, "hwnd": HWND, "creation_filetime": BIRTH,
                "observation_policy": "existingGameDesktop", "target_desktop_id": D2,
                "current_desktop_id": D2, "current_desktop_after": D2,
                "observation_only": True, "window_mutations": 0, "fully_visible": True,
                "current_desktop_unchanged": True, "foreground_unchanged": True,
                "visible": True, "minimized": False, "before": desktop, "after": dict(desktop),
                "monitor_rect": [0, 0, 2560, 1440], "work_rect": [0, 0, 2560, 1392],
                "window_rect": [0, 0, 2560, 1440], "client_screen_rect": [0, 0, 2560, 1440]}

    @contextmanager
    def ports(self):
        gui, api, placement = ModuleType("win32gui"), ModuleType("win32api"), ModuleType("managed_desktop1_placement")
        gui.GetForegroundWindow = Mock(return_value=777)
        gui.GetWindowRect = Mock(return_value=(0, 0, 2560, 1440))
        gui.GetClientRect = Mock(return_value=(0, 0, 2560, 1440))
        gui.ClientToScreen = Mock(side_effect=lambda hwnd, point: point)
        gui.IsWindowVisible = Mock(return_value=True)
        gui.IsIconic = Mock(return_value=False)
        forbidden = ("ShowWindow", "SetWindowPos", "SetWindowLong", "SetForegroundWindow", "MoveWindow")
        for name in forbidden:
            setattr(gui, name, Mock(side_effect=AssertionError("window mutation forbidden: " + name)))
        api.MonitorFromWindow = Mock(return_value=1)
        api.GetMonitorInfo = Mock(return_value={"Monitor": (0, 0, 2560, 1440), "Work": (0, 0, 2560, 1392)})
        placement.desktop_inventory = Mock(return_value=([D1, D2], D2))
        desktop = Mock(return_value={"window_hwnd": HWND, "desktop_id": D2,
                                   "on_current_virtual_desktop": True, "dwm_cloaked_flags": 0})
        game, check = SimpleNamespace(check=Mock()), Mock()
        value = SimpleNamespace(gui=gui, api=api, placement=placement, desktop=desktop, game=game, check=check)
        with patch.dict(sys.modules, {"win32gui": gui, "win32api": api, "managed_desktop1_placement": placement}):
            yield value
        for name in forbidden:
            getattr(gui, name).assert_not_called()

    def observe(self, ports):
        return capture._check_existing_game_desktop(ports.game, HWND, D2, ports.check, ports.desktop)

    def test_missing_legacy_and_explicit_bad_policy(self):
        row = self.job()
        row.pop("placement_observation_policy")
        capture.validate_job(row)
        for value in (None, "unknown", 0, False, []):
            row["placement_observation_policy"] = value
            with self.subTest(policy=value), self.assertRaises(ValueError):
                capture.validate_job(row)

    def test_complete_group_required_for_new_policy(self):
        base = self.job()
        capture.validate_job(base)
        for key in ("decision_text_publisher", "decision_text_publisher_receipt", "decision_text_file", "desktop_id", "game_creation_filetime"):
            row = dict(base)
            row[key] = None
            with self.subTest(missing=key), self.assertRaises(ValueError):
                capture.validate_job(row)
        only = dict(base)
        only["capture_mode"] = "game_only"
        for key in ("overlay", "desktop_id", "decision_text_file", "game_creation_filetime", "decision_text_publisher", "decision_text_publisher_receipt"):
            only[key] = None
        with self.assertRaisesRegex(ValueError, "game_only"):
            capture.validate_job(only)
        only.pop("placement_observation_policy")
        capture.validate_job(only)

    def test_receipt_monitor_fit_and_actual_identity_negatives(self):
        base = self.placement()
        capture._validate_existing_game_placement193(base, pid=PID, hwnd=HWND)
        for changes in ({"window_mutations": False}, {"observation_only": False}, {"fully_visible": False},
                {"foreground_unchanged": False}, {"current_desktop_unchanged": False}, {"visible": False},
                {"minimized": True}, {"hwnd": HWND + 1}, {"current_desktop_id": D1},
                {"current_desktop_after": D1}, {"window_rect": [0, 0, 0, 1440]},
                {"client_screen_rect": [-1, 0, 2559, 1440]}, {"creation_filetime": 0},
                {"before": {**base["before"], "window_hwnd": HWND + 1}},
                {"after": {**base["after"], "dwm_cloaked_flags": 2}}):
            row = deepcopy(base)
            row.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                capture._validate_existing_game_placement193(row, pid=PID, hwnd=HWND)

    def test_fresh_current_desktop2_monitor_fit_with_unrelated_foreground(self):
        with self.ports() as ports:
            actual = self.observe(ports)
            self.assertEqual(actual["window"], (0, 0, 2560, 1440))
            self.assertEqual(actual["client_screen"], (0, 0, 2560, 1440))
            self.assertEqual(actual["current"], D2)
            self.assertEqual(actual["foreground"], 777)
            self.assertEqual(ports.placement.desktop_inventory.call_count, 2)
            self.assertGreaterEqual(ports.game.check.call_count, 4)
            self.assertGreaterEqual(ports.check.call_count, 4)

    def test_double_snapshot_race_and_generation_changes_rejected(self):
        for field in ("foreground", "inventory", "current", "window", "monitor_handle", "monitor_geometry", "generation"):
            with self.subTest(field=field), self.ports() as ports:
                if field == "foreground":
                    ports.gui.GetForegroundWindow.side_effect = [777, 888]
                elif field == "inventory":
                    ports.placement.desktop_inventory.side_effect = [([D1, D2], D2), ([D2, D1], D2)]
                elif field == "current":
                    ports.placement.desktop_inventory.side_effect = [([D1, D2], D2), ([D1, D2], D1)]
                elif field == "window":
                    ports.gui.GetWindowRect.side_effect = [(0, 0, 2560, 1440), (0, 0, 2559, 1440)]
                elif field == "monitor_handle":
                    ports.api.MonitorFromWindow.side_effect = [1, 2]
                elif field == "monitor_geometry":
                    ports.api.GetMonitorInfo.side_effect = [
                        {"Monitor": (0, 0, 2560, 1440), "Work": (0, 0, 2560, 1392)},
                        {"Monitor": (0, 0, 2560, 1440), "Work": (0, 0, 2560, 1391)}]
                else:
                    ports.game.check.side_effect = [None, RuntimeError("generation changed")]
                with self.assertRaises((RuntimeError, ValueError)):
                    self.observe(ports)

    def test_hidden_cloaked_identity_and_geometry_rejected(self):
        for field in ("hidden", "minimized", "cloaked", "hwnd", "offscreen", "empty_client", "client_origin"):
            with self.subTest(field=field), self.ports() as ports:
                if field == "hidden":
                    ports.gui.IsWindowVisible.return_value = False
                elif field == "minimized":
                    ports.gui.IsIconic.return_value = True
                elif field == "cloaked":
                    ports.desktop.return_value = {"window_hwnd": HWND, "desktop_id": D2, "on_current_virtual_desktop": True, "dwm_cloaked_flags": 2}
                elif field == "hwnd":
                    ports.desktop.return_value = {"window_hwnd": HWND + 1, "desktop_id": D2, "on_current_virtual_desktop": True, "dwm_cloaked_flags": 0}
                elif field == "offscreen":
                    ports.gui.GetWindowRect.return_value = (-1, 0, 2559, 1440)
                elif field == "empty_client":
                    ports.gui.GetClientRect.return_value = (0, 0, 0, 1440)
                else:
                    ports.gui.ClientToScreen.side_effect = lambda hwnd, point: (point[0] + 1, point[1])
                with self.assertRaises((RuntimeError, ValueError)):
                    self.observe(ports)

    def launch(self, placement, name):
        output = self.root / name
        output.mkdir()
        obs = self.root / "private-obs"
        profile_name = "ManagedWindowCapture-" + "1" * 32
        profile = {"schema": capture.SCHEMA, "strict_isolation": True, "host": "127.0.0.1", "port": 11917,
                "obs_root": str(obs), "executable": str(obs / "bin/64bit/obs64.exe"),
                "config_root": str(obs / "config/obs-studio"), "profile_name": profile_name,
                "collection_name": profile_name, "recording_root": str(output),
                "deadline_utc": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                "max_output_bytes": 192 * 1024**2}
        profile_path, place_path = output / "profile.json", output / "placement.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        place_path.write_text(json.dumps(placement), encoding="utf-8")
        text = output / "current.txt"
        text.write_text("智能体实时决策\nfixture", encoding="utf-8")
        probe = output / "ffprobe.exe"
        probe.write_bytes(b"metadata only; never execute")
        publisher = {"schema": "xar.java-root-decision-text/v1", "binding_path": str(output / "current.binding.json"),
                "session": str(output), "decision_text_file": str(text), "publisher": {}}
        module = ModuleType("managed_desktop1_placement")
        module._read_launch_document = Mock(return_value={"pid": PID, "command": [str(self.root / "ck3.exe")], "creation_date": "literal-not-used-by-this-boundary"})
        module.parse_launch_receipt = Mock(side_effect=AssertionError("Java launch validation is a separate existing branch"))
        self.last_popen, self.last_output = Mock(side_effect=BeforeProcess193()), output
        with patch.dict(sys.modules, {"managed_desktop1_placement": module}), \
                patch.object(capture, "_generation_helpers", return_value=(Mock(), Mock(), Mock(), Mock())), \
                patch.object(capture, "require_no_retired_decision_window", return_value={}), \
                patch.object(capture, "read_java_decision_binding", return_value=publisher), \
                patch.object(capture.subprocess, "Popen", self.last_popen):
            capture.launch_recording(profile_path, output, PID, HWND, 15,
                    launch_receipt=output / "not-read-owner.json", ffprobe=probe,
                    placement_receipt=place_path, java_decision_binding=output / "current.binding.json")

    def test_launch_propagates_actual_new_and_legacy_policy_before_process(self):
        for name, expected in (("current", "existingGameDesktop"), ("legacy", "legacyDesktop1")):
            row = self.placement()
            if name == "legacy":
                row.pop("observation_policy")
            with self.subTest(policy=expected), self.assertRaises(BeforeProcess193):
                self.launch(row, name)
            paths = list(self.last_output.glob("*/job.json"))
            self.assertEqual(len(paths), 1)
            job = json.loads(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(job["placement_observation_policy"], expected)
            self.last_popen.assert_called_once()

    def test_invalid_receipt_stops_before_job_and_process(self):
        for index, changes in enumerate(({"observation_policy": "unknown"}, {"observation_policy": None},
                {"observation_only": False}, {"window_mutations": False}, {"current_desktop_id": D1})):
            row = self.placement()
            row.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.launch(row, "rejected-" + str(index))
            self.last_popen.assert_not_called()
            self.assertEqual(list(self.last_output.glob("*/job.json")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
