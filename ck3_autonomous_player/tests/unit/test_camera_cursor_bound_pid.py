"""Bound camera cursor checks use synthetic windows and never touch the desktop."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import camera_cursor_parking as parking


def _park(*, expected_game_pid: int | None, identity_pid: int = 127268,
          on_current_desktop: bool = False):
    def read_title(_hwnd, buffer, _length):
        buffer.value = "Other application"
        return len(buffer.value)

    user32 = SimpleNamespace(
        GetForegroundWindow=mock.Mock(return_value=17),
        GetWindowTextLengthW=mock.Mock(return_value=len("Other application")),
        GetWindowTextW=mock.Mock(side_effect=read_title),
        GetClientRect=mock.Mock(side_effect=AssertionError("client access")),
        ClientToScreen=mock.Mock(side_effect=AssertionError("client access")),
        GetCursorPos=mock.Mock(side_effect=AssertionError("cursor access")),
        SetCursorPos=mock.Mock(side_effect=AssertionError("mouse input")),
    )
    gui = SimpleNamespace(
        EnumWindows=lambda visit, extra: visit(99, extra),
        IsWindowVisible=lambda _hwnd: True,
        IsIconic=lambda _hwnd: False,
        GetWindowText=lambda _hwnd: "Crusader Kings III",
    )
    process = SimpleNamespace(
        GetWindowThreadProcessId=lambda _hwnd: (1, 127268),
    )
    virtual_desktop = SimpleNamespace(
        window_virtual_desktop=lambda _hwnd: {
            "on_current_virtual_desktop": on_current_desktop,
            "dwm_cloaked_flags": 0 if on_current_desktop else 2,
        },
    )
    identity = {
        "pid": identity_pid, "name": "ck3.exe",
        "executable": r"C:\CK3\binaries\ck3.exe",
    }
    inventory = {"processes": [{"pid": 127268, "name": "ck3.exe"}]}
    with (
        mock.patch.object(parking.os, "name", "nt"),
        mock.patch.object(parking.ctypes, "windll", SimpleNamespace(user32=user32),
                          create=True),
        mock.patch.object(parking, "_toolhelp_process_identity", return_value=identity) as bound,
        mock.patch.object(parking, "ck3_process_inventory", return_value=inventory) as scan,
        mock.patch.dict(sys.modules, {
            "win32gui": gui,
            "win32process": process,
            "xar_autoplayer.bridge.windows_virtual_desktop": virtual_desktop,
        }),
    ):
        receipt = parking.park_foreground_ck3_cursor(
            expected_game_pid=expected_game_pid)
    user32.SetCursorPos.assert_not_called()
    user32.GetCursorPos.assert_not_called()
    return receipt, bound, scan


def test_bound_pid_skips_other_virtual_desktop_without_global_inventory() -> None:
    receipt, bound, scan = _park(expected_game_pid=127268)
    assert receipt["status"] == "skipped_other_virtual_desktop"
    assert receipt["mouse_input"] is False
    bound.assert_called_once_with(127268)
    scan.assert_not_called()


def test_mismatched_bound_pid_fails_closed_without_global_inventory() -> None:
    receipt, bound, scan = _park(expected_game_pid=127268, identity_pid=999)
    assert receipt == {"status": "bound_game_pid_unconfirmed", "mouse_input": False}
    bound.assert_called_once_with(127268)
    scan.assert_not_called()


def test_unbound_other_virtual_desktop_uses_one_inventory() -> None:
    receipt, bound, scan = _park(expected_game_pid=None)
    assert receipt["status"] == "skipped_other_virtual_desktop"
    assert receipt["mouse_input"] is False
    bound.assert_not_called()
    scan.assert_called_once_with()
