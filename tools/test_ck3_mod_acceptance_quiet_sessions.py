"""Execute the shared session delegates and Win32 boundary without a Game."""
from __future__ import annotations

import ast
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
HOST_PATH = ROOT / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
SPEC = importlib.util.spec_from_file_location("quiet_actual_shared_host_test", HOST_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Actual shared host loader unavailable")
HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST)

from xar_autoplayer import native_session as SESSION  # noqa: E402


def fake_session() -> ModuleType:
    """Keep the wrapper's real rebinding; replace the managed OS boundary."""
    module = ModuleType("quiet_managed_session_fixture")
    exec("""
calls = []
def launch(*args, **kwargs):
    calls.append(kwargs)
    return handle
def _native_session_locked(*args, **kwargs):
    launch(*args, start_minimized=kwargs.get('start_minimized', False))
    return {'os_boundary': 'mocked'}
def native_session(*args, **kwargs):
    return _native_session_locked(*args, **kwargs)
""", module.__dict__)
    module.handle = SimpleNamespace(
        command=["ck3.exe", "-loadsave=restored_campaign"],
        process=SimpleNamespace(pid=4242), ck3_creation_date="fixture-birth",
    )
    return module


class SharedHostQuietTests(unittest.TestCase):
    def test_saved_campaign_uses_minimized_managed_launch(self) -> None:
        module = fake_session()
        args = SimpleNamespace(timeout=1, hold_seconds=0)
        with patch("importlib.import_module", return_value=module):
            report = HOST.saved_campaign_session(object(), object(), args, threading.Event(),
                output_stream=io.StringIO(), launch_record={})
        self.assertTrue(module.calls[0]["start_minimized"])
        self.assertEqual(module.calls[0]["load_save_name"], "restored_campaign")
        self.assertTrue(report["single_saved_campaign_launch"])

    def test_fixture_uses_same_minimized_managed_launch(self) -> None:
        module = fake_session()
        args = SimpleNamespace(timeout=1, hold_seconds=0, cold_start_checkpoint=False)
        with patch("importlib.import_module", return_value=module):
            report = HOST.fixture_session(object(), object(), args, threading.Event(),
                output_stream=io.StringIO())
        self.assertTrue(module.calls[0]["start_minimized"])
        self.assertFalse(module.calls[0]["verify_prepared_profile"])
        self.assertTrue(report["fixture_profile"])

    def test_regular_supervisor_delegates_minimized_without_game_or_thread(self) -> None:
        # Execute the actual nested producer body. All its process boundaries
        # are mocked, so this also checks its real exception/finally handling.
        tree = ast.parse(HOST_PATH.read_text(encoding="utf-8-sig"))
        owners = [node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "supervise"]
        self.assertEqual(len(owners), 1)
        managed = Mock(return_value={"os_boundary": "mocked"})
        done = threading.Event()
        with tempfile.TemporaryDirectory(prefix="quiet-host-boundary-") as temporary:
            state: dict[str, object] = {}
            scope: dict[str, object] = {
                "args": SimpleNamespace(output=Path(temporary) / "host.json",
                    saved_campaign_save=None, fixture_profile=False, timeout=1,
                    hold_seconds=0, cold_start_checkpoint=False),
                "session_state": state, "native_session": managed, "spec": object(),
                "config": object(), "stop": threading.Event(), "done": done,
                "json": __import__("json"),
            }
            exec(compile(ast.Module(body=owners, type_ignores=[]), str(HOST_PATH), "exec"), scope)
            supervise = scope["supervise"]
            if not callable(supervise):
                raise TypeError("Actual supervisor is not callable")
            supervise()
        managed.assert_called_once()
        self.assertIs(managed.call_args.kwargs["start_minimized"], True)
        self.assertEqual(state, {"report": {"os_boundary": "mocked"}})
        self.assertTrue(done.is_set())


class FakeOwnedWindows:
    """Two HWNDs: one owned CK3 and the user's unrelated foreground window."""
    def __init__(self, *, minimized: bool, permit_demote: bool = True) -> None:
        self.minimized = minimized
        self.topmost = True
        self.foreground = 92
        self.permit_demote = permit_demote
        self.operations: list[tuple[str, int]] = []

    def EnumWindows(self, callback: object, context: object) -> None:
        if not callable(callback):
            raise TypeError("Window callback required")
        for hwnd in (91, 92):
            callback(hwnd, context)

    def IsWindowVisible(self, hwnd: int) -> bool:
        return hwnd in (91, 92)

    def IsIconic(self, hwnd: int) -> bool:
        return hwnd == 91 and self.minimized

    def GetForegroundWindow(self) -> int:
        return self.foreground

    def GetWindowLong(self, hwnd: int, index: int) -> int:
        if hwnd != 91 or index != -20:
            raise AssertionError("Only the owned Game style may be read")
        return 8 if self.topmost else 0

    def SetWindowPos(self, hwnd: int, insert_after: int, x: int, y: int,
                     width: int, height: int, flags: int) -> None:
        if (hwnd, insert_after, x, y, width, height, flags) != (91, -2, 0, 0, 0, 0, 19):
            raise AssertionError("Owned demotion must preserve position, size and activation")
        self.operations.append(("demote_without_activation", hwnd))
        if self.permit_demote:
            self.topmost = False

    def ShowWindow(self, hwnd: int, command: int) -> None:
        if hwnd != 91 or command != 7:
            raise AssertionError("Only the owned Game may be minimized without activation")
        self.operations.append(("minimize_without_activation", hwnd))
        self.minimized = True


class QuietWindowBoundaryTests(unittest.TestCase):
    def modules(self, windows: FakeOwnedWindows) -> dict[str, object]:
        constants = SimpleNamespace(HWND_NOTOPMOST=-2, SWP_NOMOVE=2, SWP_NOSIZE=1,
            SWP_NOACTIVATE=16, SW_SHOWMINNOACTIVE=7, GWL_EXSTYLE=-20, WS_EX_TOPMOST=8)
        process = SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (1, 4242 if hwnd == 91 else 77))
        return {"win32gui": windows, "win32con": constants, "win32process": process}

    def test_demotes_and_minimizes_only_owned_game_without_activating_it(self) -> None:
        windows = FakeOwnedWindows(minimized=False)
        with patch.dict(sys.modules, self.modules(windows)):
            self.assertTrue(SESSION._minimize_process_windows(
                4242, timeout_seconds=0.1, poll_interval_seconds=0.001))
            SESSION.require_game_windows_background(4242)
        self.assertEqual(windows.operations, [("demote_without_activation", 91),
            ("minimize_without_activation", 91)])
        self.assertEqual(windows.foreground, 92)
        self.assertTrue(windows.minimized)
        self.assertFalse(windows.topmost)

    def test_already_minimized_game_still_loses_topmost_without_restore(self) -> None:
        windows = FakeOwnedWindows(minimized=True)
        with patch.dict(sys.modules, self.modules(windows)):
            self.assertTrue(SESSION._minimize_process_windows(
                4242, timeout_seconds=0.1, poll_interval_seconds=0.001))
        self.assertEqual(windows.operations, [("demote_without_activation", 91)])
        self.assertEqual(windows.foreground, 92)

    def test_failed_demote_is_not_reported_as_background_success(self) -> None:
        windows = FakeOwnedWindows(minimized=True, permit_demote=False)
        with patch.dict(sys.modules, self.modules(windows)):
            self.assertFalse(SESSION._minimize_process_windows(
                4242, timeout_seconds=0, poll_interval_seconds=0))
        self.assertTrue(windows.topmost)
        self.assertEqual(windows.foreground, 92)


if __name__ == "__main__":
    unittest.main()
