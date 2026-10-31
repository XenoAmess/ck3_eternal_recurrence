"""Only source193 policy boundaries; every process and window read is a double."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

REPOSITORY = Path(os.environ.get("PLACEMENT193_REPOSITORY", os.environ.get("VIDEO_SOURCE193_REPO", str(Path(__file__).resolve().parents[2]))))
SOURCE_ROOT = Path(os.environ.get("VIDEO_SOURCE193_ROOT", str(Path(__file__).resolve().parents[2])))
SOURCE = Path(os.environ.get("PLACEMENT193_SOURCE", str(SOURCE_ROOT / "tools/g2_saved_campaign/managed_desktop1_placement.py")))
sys.path.insert(0, str(REPOSITORY))
SPEC = importlib.util.spec_from_file_location("placement193_candidate", SOURCE)
placement = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = placement
SPEC.loader.exec_module(placement)

PID, BIRTH, HWND = 71464, 134378397668266369, 319967214
DESKTOP1 = "11111111-1111-1111-1111-111111111111"
DESKTOP2 = "22222222-2222-2222-2222-222222222222"
DESKTOP3 = "33333333-3333-3333-3333-333333333333"
FULL, WORK = (0, 0, 2560, 1440), (0, 0, 2560, 1392)


class ExistingGameDesktopPolicy193Tests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = Path(os.environ.get("PLACEMENT193_TMP", os.environ.get("VIDEO_SOURCE193_TMP", tempfile.gettempdir())))
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.serial = 0

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def observe(self, *, policy="existingGameDesktop", target=DESKTOP2, current=DESKTOP2,
                desktop=DESKTOP2, on_current=True, cloaked=0, window=FULL, client=FULL,
                origin=(0, 0), work=WORK, race=False, bad_generation=False, rejected=False,
                reason=None):
        self.serial += 1
        receipt = self.root / ("observation-" + str(self.serial) + ".json")
        args = SimpleNamespace(launch_receipt=self.root / "launch.json", receipt=receipt,
                desktop_id=target, expected_current_desktop_id=current,
                deadline_utc=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                wait_seconds=1, ui_dependencies=None)
        if policy is not None:
            args.observation_policy = policy
        gui, api, con, process = (ModuleType(name) for name in ("win32gui", "win32api", "win32con", "win32process"))
        gui.IsWindow = lambda hwnd: hwnd == HWND
        gui.IsWindowVisible = Mock(return_value=True)
        gui.GetWindowText = lambda hwnd: "Crusader Kings III"
        gui.GetClassName = lambda hwnd: "SDL_app"
        gui.GetWindowRect = Mock(side_effect=[FULL, (0, 0, 2559, 1440)] if race else None, return_value=window)
        gui.GetClientRect = Mock(return_value=client)
        gui.ClientToScreen = Mock(side_effect=lambda hwnd, point: (point[0] + origin[0], point[1] + origin[1]))
        gui.GetWindowLong = lambda hwnd, index: 0x10
        gui.IsIconic = Mock(return_value=False)
        gui.EnumWindows = lambda callback, extra: callback(HWND, extra)
        forbidden = ("ShowWindow", "SetWindowPos", "SetWindowLong", "SetForegroundWindow")
        for name in forbidden:
            setattr(gui, name, Mock(side_effect=AssertionError("forbidden window mutation: " + name)))
        api.MonitorFromWindow = Mock(return_value=1)
        api.GetMonitorInfo = Mock(return_value={"Monitor": FULL, "Work": work})
        con.GWL_EXSTYLE, con.WS_EX_TOPMOST = -20, 8
        con.MONITOR_DEFAULTTONEAREST, con.MONITOR_DEFAULTTONULL = 2, 0
        process.GetWindowThreadProcessId = lambda hwnd: (1, PID)
        virtual = ModuleType("xar_autoplayer.bridge.windows_virtual_desktop")
        virtual.window_virtual_desktop = Mock(return_value={"window_hwnd": HWND,
            "on_current_virtual_desktop": on_current, "desktop_id": desktop, "dwm_cloaked_flags": cloaked})
        generation = SimpleNamespace(pid=PID, creation_filetime=BIRTH, executable=self.root / "ck3.exe",
            check=Mock(side_effect=RuntimeError("fixture-generation-mismatch") if bad_generation else None))
        context = Mock()
        context.__enter__ = Mock(return_value=generation)
        context.__exit__ = Mock(return_value=False)
        launch = {"pid": PID, "command": [str(self.root / "ck3.exe")], "creation_date": "20261030131606.826636+000"}
        baseline = {"schema": "xar.g2.managed-desktop1-placement/v1", "status": "RED",
            "gameplay_input_sent": False, "desktop_switches": 0, "process_launch_or_stop_calls": 0,
            "runtime_rendering_qualified": False, "observation_policy": "legacyDesktop1"}
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {"win32gui": gui, "win32api": api, "win32con": con,
                "win32process": process, "xar_autoplayer.bridge.windows_virtual_desktop": virtual}))
            stack.enter_context(patch.object(placement, "_new_receipt", return_value=deepcopy(baseline)))
            stack.enter_context(patch.object(placement, "_read_launch_document", return_value=launch))
            inventory = stack.enter_context(patch.object(placement, "desktop_inventory", return_value=([DESKTOP1, DESKTOP2], current)))
            foreground = stack.enter_context(patch.object(placement, "read_foreground_window_v1", return_value=(HWND, PID)))
            stack.enter_context(patch.object(placement, "game_generation", return_value=context))
            if rejected:
                with self.assertRaises((ValueError, RuntimeError)) as caught:
                    placement.observe_placement(args)
                if reason is not None:
                    self.assertIn(reason, str(caught.exception))
                self.assertTrue(receipt.is_file(), "every observer rejection must publish its RED receipt")
                row = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(row["status"], "RED")
            else:
                row = placement.observe_placement(args)
                self.assertEqual(row["status"], "GREEN")
                self.assertEqual(json.loads(receipt.read_text(encoding="utf-8")), row)
                self.assertEqual(inventory.call_count, 4)
                self.assertEqual(foreground.call_count, 4)
                self.assertEqual(virtual.window_virtual_desktop.call_count, 2)
            for name in forbidden:
                getattr(gui, name).assert_not_called()
        return row

    def test_existing_current_desktop2_full_monitor_exceeds_work_and_is_read_only(self) -> None:
        row = self.observe()
        self.assertEqual(row["observation_policy"], "existingGameDesktop")
        self.assertEqual(row["target_desktop_id"], DESKTOP2)
        self.assertEqual(row["window_rect"], list(FULL))
        self.assertEqual(row["client_screen_rect"], list(FULL))
        self.assertEqual(row["work_rect"], list(WORK))
        self.assertEqual(row["window_mutations"], 0)
        self.assertEqual(row["desktop_switches"], 0)
        self.assertEqual(row["process_launch_or_stop_calls"], 0)
        self.assertIs(row["topmost"], False)
        self.assertIs(row["background_assignment_verified"], False)

    def test_same_desktop2_case_rejected_by_legacy_and_missing_field_fallback(self) -> None:
        for policy in ("legacyDesktop1", None):
            with self.subTest(policy=policy):
                self.observe(policy=policy, rejected=True, reason="Desktop1")

    def test_existing_policy_rejects_unknown_target_current_mismatch_and_membership(self) -> None:
        cases = [dict(target=DESKTOP3), dict(target=DESKTOP1), dict(current=DESKTOP1),
                 dict(desktop=DESKTOP1), dict(on_current=False), dict(cloaked=2)]
        for values in cases:
            with self.subTest(values=values):
                self.observe(**values, rejected=True)

    def test_frame_client_and_valid_work_area_remain_inside_monitor(self) -> None:
        cases = [dict(window=(-1, 0, 2559, 1440)), dict(origin=(1, 0)),
                 dict(work=(0, 0, 2561, 1392)), dict(work=(0, 0, 2560, 0))]
        for values in cases:
            with self.subTest(values=values):
                self.observe(**values, rejected=True)

    def test_two_individually_valid_but_different_snapshots_reject(self) -> None:
        self.observe(race=True, rejected=True, reason="changed between complete snapshots")

    def test_existing_policy_cannot_bypass_generation_check(self) -> None:
        self.observe(bad_generation=True, rejected=True, reason="fixture-generation-mismatch")

    def test_pure_policy_validator_accepts_only_two_literals(self) -> None:
        for policy in ("legacyDesktop1", "existingGameDesktop"):
            self.assertEqual(placement.validate_observation_policy(policy), policy)
        for value in (None, True, 1, "unknown", "", [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                placement.validate_observation_policy(value)

    def test_cli_nonlegacy_requires_observe_and_legacy_default_is_explicit(self) -> None:
        base = ["placement", "--launch-receipt", str(self.root / "launch.json"),
                "--receipt", str(self.root / "cli.json"), "--desktop-id", DESKTOP2,
                "--deadline-utc", (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                "--ui-dependencies", str(self.root)]
        errors = io.StringIO()
        with patch.object(sys, "argv", base + ["--observation-policy", "existingGameDesktop"]), \
                patch.object(sys, "stderr", errors), patch.object(placement, "place") as mover, \
                patch.object(placement, "observe_placement") as observer:
            with self.assertRaises(SystemExit) as caught:
                placement.main()
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("nonlegacy observation policy requires --observe-only", errors.getvalue())
            mover.assert_not_called()
            observer.assert_not_called()
        with patch.object(sys, "argv", base + ["--observe-only"]), patch.object(sys, "stdout", io.StringIO()), \
                patch.object(placement, "place") as mover, \
                patch.object(placement, "observe_placement", return_value={"fixture": True}) as observer:
            placement.main()
            self.assertEqual(observer.call_args.args[0].observation_policy, "legacyDesktop1")
            mover.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
