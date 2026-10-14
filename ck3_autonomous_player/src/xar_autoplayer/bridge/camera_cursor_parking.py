"""Park the pointer inside the foreground CK3 client before map navigation.

CK3 pans the map continuously while a pointer rests near a screen edge. A
verified native camera receipt is therefore insufficient unless the pointer
cannot immediately undo that position. This module moves only the pointer;
it never clicks or sends a gameplay command.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os

from ..environment import ck3_process_inventory, _toolhelp_process_identity
from ..errors import AgentError


def _owned_ck3_processes(expected_game_pid: int | None) -> list[dict[str, object]]:
    if expected_game_pid is None:
        return ck3_process_inventory().get("processes", [])
    if type(expected_game_pid) is not int or expected_game_pid <= 0:
        return []
    identity = _toolhelp_process_identity(expected_game_pid)
    if (identity is None
            or type(identity.get("pid")) is not int
            or identity["pid"] != expected_game_pid
            or str(identity.get("name", "")).casefold() != "ck3.exe"
            or os.path.basename(str(identity.get("executable", ""))).casefold() != "ck3.exe"):
        return []
    return [identity]


def _minimized_owned_ck3_window(
    *, processes: list[dict[str, object]] | None = None,
    inventory_out: list[list[dict[str, object]]] | None = None,
) -> dict[str, object] | None:
    """Find the sole live CK3 PID only when all its visible windows are iconic."""

    import win32gui
    import win32process

    if processes is None:
        try:
            processes = _owned_ck3_processes(None)
        except AgentError:
            processes = []
    if inventory_out is not None:
        inventory_out.append(processes)
    if len(processes) != 1:
        return None
    process = processes[0]
    if str(process.get("name", "")).casefold() != "ck3.exe":
        return None
    pid = int(process["pid"])
    windows: list[int] = []

    def collect(hwnd: int, _extra: object) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            _thread, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(window_pid) == pid:
                windows.append(int(hwnd))
        return True

    win32gui.EnumWindows(collect, None)
    if not windows or not all(bool(win32gui.IsIconic(hwnd)) for hwnd in windows):
        return None
    return {"status": "skipped_minimized", "ck3_pid": pid,
            "window_count": len(windows)}


def _background_owned_ck3_window(
    *, processes: list[dict[str, object]] | None = None,
) -> dict[str, object] | None:
    """Skip global pointer input only for a verified hidden virtual desktop."""
    import win32gui
    import win32process
    from .windows_virtual_desktop import window_virtual_desktop

    try:
        if processes is None:
            processes = _owned_ck3_processes(None)
        if len(processes) != 1 or str(processes[0].get("name", "")).casefold() != "ck3.exe":
            return None
        pid = int(processes[0]["pid"])
        windows = []
        def collect(hwnd: int, _extra: object) -> bool:
            if (win32gui.IsWindowVisible(hwnd)
                    and win32process.GetWindowThreadProcessId(hwnd)[1] == pid):
                windows.append(int(hwnd))
            return True
        win32gui.EnumWindows(collect, None)
        if len(windows) != 1:
            return None
        hwnd = windows[0]
        if win32gui.GetWindowText(hwnd) != "Crusader Kings III" or win32gui.IsIconic(hwnd):
            return None
        observed = window_virtual_desktop(hwnd)
        if (observed["on_current_virtual_desktop"] is not False
                or not (int(observed["dwm_cloaked_flags"]) & 2)):
            return None
        return {"status": "skipped_other_virtual_desktop", "ck3_pid": pid,
                "mouse_input": False, **observed}
    except (AgentError, OSError, ValueError):
        return None


def park_foreground_ck3_cursor(*, expected_game_pid: int | None = None) -> dict[str, object]:
    """Move to an interior client point when CK3 owns the foreground window."""

    if os.name != "nt":
        return {"status": "unsupported_platform"}
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    hwnd = user32.GetForegroundWindow()
    title = None
    if hwnd:
        length = user32.GetWindowTextLengthW(hwnd)
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        title = title_buffer.value
    processes = None
    if expected_game_pid is not None:
        try:
            processes = _owned_ck3_processes(expected_game_pid)
        except AgentError:
            processes = []
        if not processes:
            return {"status": "bound_game_pid_unconfirmed", "mouse_input": False}
    if not hwnd:
        inventory_out: list[list[dict[str, object]]] = []
        minimized = _minimized_owned_ck3_window(
            processes=processes, inventory_out=inventory_out)
        if minimized is not None:
            return minimized
        background = _background_owned_ck3_window(
            processes=processes if processes is not None
            else inventory_out[0] if inventory_out else [])
        if background is not None:
            return background
        return {"status": "no_foreground_window"}
    if title != "Crusader Kings III":
        inventory_out: list[list[dict[str, object]]] = []
        minimized = _minimized_owned_ck3_window(
            processes=processes, inventory_out=inventory_out)
        if minimized is not None:
            return minimized
        background = _background_owned_ck3_window(
            processes=processes if processes is not None
            else inventory_out[0] if inventory_out else [])
        if background is not None:
            return background
        return {"status": "ck3_not_foreground", "foreground_title": title}
    import win32gui
    import win32process
    if processes is None:
        try:
            processes = _owned_ck3_processes(None)
        except AgentError:
            return {"status": "owned_process_unconfirmed", "mouse_input": False}
    if (len(processes) != 1
            or str(processes[0].get("name", "")).casefold() != "ck3.exe"
            or int(processes[0]["pid"]) != win32process.GetWindowThreadProcessId(hwnd)[1]
            or win32gui.IsIconic(hwnd)):
        return {"status": "owned_window_unconfirmed", "mouse_input": False}
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError("GetClientRect failed for the foreground CK3 window")
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width < 320 or height < 240:
        raise ValueError("CK3 client rect is too small for safe cursor parking")
    point = wintypes.POINT(width // 2, height * 73 // 100)
    if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
        raise OSError("ClientToScreen failed for the foreground CK3 window")
    before = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(before)):
        raise OSError("GetCursorPos failed before CK3 cursor parking")
    if user32.GetForegroundWindow() != hwnd:
        return {"status": "foreground_changed", "mouse_input": False}
    if not user32.SetCursorPos(point.x, point.y):
        raise OSError("SetCursorPos failed for the foreground CK3 window")
    after = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(after)) or (after.x, after.y) != (point.x, point.y):
        raise OSError("CK3 cursor parking postcondition failed")
    return {
        "status": "parked", "foreground_title": title,
        "client_size": [width, height],
        "before_screen_xy": [before.x, before.y],
        "parked_screen_xy": [after.x, after.y],
        "edge_margin_fraction": 0.15,
    }
