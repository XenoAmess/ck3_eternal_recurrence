"""Opt-in Win32 window used by visible-UI integration tests; never launches CK3."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import site
import sys
import tempfile


if os.name != "nt":
    raise SystemExit("Windows helper")


user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetDpiForWindow.argtypes = (ctypes.c_void_p,)
user32.GetDpiForWindow.restype = ctypes.c_uint


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(raw, path)
    finally:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass


def main() -> int:
    helper_site_packages = os.environ.get("XAR_HELPER_SITE_PACKAGES")
    if helper_site_packages:
        site.addsitedir(helper_site_packages)
    import win32api
    import win32con
    import win32gui

    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--overlay", action="store_true")
    args = parser.parse_args()

    user32.SetProcessDPIAware()
    width, height = ((180, 120) if args.overlay else (2560, 1440))
    x, y = ((590, 550) if args.overlay else (23, 31))
    state = {"down": 0, "up": 0, "completed_clicks": 0, "outside": 0}

    def window_proc(hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message in (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP):
            client_x = win32api.LOWORD(lparam)
            client_y = win32api.HIWORD(lparam)
            within = 560 <= client_x <= 640 and 530 <= client_y <= 590
            key = "down" if message == win32con.WM_LBUTTONDOWN else "up"
            state[key] += 1
            if not within:
                state["outside"] += 1
            if message == win32con.WM_LBUTTONUP and within:
                state["completed_clicks"] += 1
            _atomic_json(args.events, {**state, "pid": os.getpid(), "hwnd": int(hwnd)})
            return 0
        if message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    class_name = f"XarVisibleUiHelper_{os.getpid()}"
    instance = win32api.GetModuleHandle(None)
    window_class = win32gui.WNDCLASS()
    window_class.lpfnWndProc = window_proc
    window_class.lpszClassName = class_name
    window_class.hInstance = instance
    window_class.hbrBackground = win32con.COLOR_WINDOW + 1
    win32gui.RegisterClass(window_class)
    hwnd = win32gui.CreateWindowEx(
        0,
        class_name,
        "XAR visible UI helper",
        win32con.WS_POPUP | win32con.WS_VISIBLE,
        x,
        y,
        width,
        height,
        0,
        0,
        instance,
        None,
    )
    win32gui.SetWindowPos(
        hwnd, win32con.HWND_TOPMOST, x, y, width, height, win32con.SWP_SHOWWINDOW
    )
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.UpdateWindow(hwnd)
    # Windows foreground-lock policy may reject a newly spawned overlay even
    # though it is visible and topmost.  Foreground acquisition is not a
    # readiness requirement for this helper; the parent test observes the
    # actual foreground HWND and still requires the target pixels to be
    # rejected as obscured.
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    client = win32gui.GetClientRect(hwnd)
    origin = win32gui.ClientToScreen(hwnd, (0, 0))
    _atomic_json(
        args.ready,
        {
            "pid": os.getpid(),
            "hwnd": int(hwnd),
            "dpi": int(user32.GetDpiForWindow(hwnd)),
            "foreground": int(win32gui.GetForegroundWindow()) == int(hwnd),
            "client_rect": [
                int(origin[0]),
                int(origin[1]),
                int(origin[0] + client[2]),
                int(origin[1] + client[3]),
            ],
        },
    )
    win32gui.PumpMessages()
    return 0


if __name__ == "__main__":
    sys.exit(main())
