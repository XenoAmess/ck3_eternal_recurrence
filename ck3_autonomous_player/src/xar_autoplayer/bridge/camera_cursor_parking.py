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

from ..environment import ck3_process_inventory
from ..errors import AgentError


def _minimized_owned_ck3_window() -> dict[str, object] | None:
    """Find the sole live CK3 PID only when all its visible windows are iconic."""

    import win32gui
    import win32process

    try:
        inventory = ck3_process_inventory().get("processes", [])
    except AgentError:
        return None
    if len(inventory) != 1:
        return None
    process = inventory[0]
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


def park_foreground_ck3_cursor() -> dict[str, object]:
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
    if not hwnd:
        minimized = _minimized_owned_ck3_window()
        if minimized is not None:
            return minimized
        return {"status": "no_foreground_window"}
    length = user32.GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title_buffer, length + 1)
    title = title_buffer.value
    if title != "Crusader Kings III":
        minimized = _minimized_owned_ck3_window()
        if minimized is not None:
            return minimized
        return {"status": "ck3_not_foreground", "foreground_title": title}
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
