from __future__ import annotations

from types import SimpleNamespace
import sys
from unittest import mock

from xar_autoplayer.bridge import camera_cursor_parking as parking


def test_only_the_single_iconic_ck3_pid_can_skip_cursor_parking() -> None:
    windows = {11: (321, True), 12: (321, True), 19: (999, False)}

    def enumerate_windows(visit, _extra):
        for hwnd in windows:
            visit(hwnd, None)

    gui = SimpleNamespace(
        EnumWindows=enumerate_windows,
        IsWindowVisible=lambda hwnd: True,
        IsIconic=lambda hwnd: windows[hwnd][1],
    )
    process = SimpleNamespace(
        GetWindowThreadProcessId=lambda hwnd: (1, windows[hwnd][0])
    )
    inventory = {"processes": [{"pid": 321, "name": "ck3.exe"}]}
    with (
        mock.patch.dict(sys.modules, {"win32gui": gui, "win32process": process}),
        mock.patch.object(parking, "ck3_process_inventory", return_value=inventory),
    ):
        assert parking._minimized_owned_ck3_window() == {
            "status": "skipped_minimized", "ck3_pid": 321, "window_count": 2
        }
        windows[12] = (321, False)
        assert parking._minimized_owned_ck3_window() is None
        windows[12] = (321, True)
        inventory["processes"].append({"pid": 999, "name": "ck3.exe"})
        assert parking._minimized_owned_ck3_window() is None


def test_minimized_ck3_does_not_move_the_users_pointer() -> None:
    user32 = SimpleNamespace(
        GetForegroundWindow=mock.Mock(return_value=0),
        GetWindowTextLengthW=mock.Mock(),
        GetWindowTextW=mock.Mock(),
        GetClientRect=mock.Mock(),
        ClientToScreen=mock.Mock(),
        GetCursorPos=mock.Mock(),
        SetCursorPos=mock.Mock(),
    )
    with (
        mock.patch.object(parking.os, "name", "nt"),
        mock.patch.object(parking.ctypes, "windll", SimpleNamespace(user32=user32),
                          create=True),
        mock.patch.object(parking, "_minimized_owned_ck3_window", return_value={
            "status": "skipped_minimized", "ck3_pid": 321, "window_count": 1
        }),
    ):
        assert parking.park_foreground_ck3_cursor()["status"] == "skipped_minimized"
    user32.SetCursorPos.assert_not_called()
