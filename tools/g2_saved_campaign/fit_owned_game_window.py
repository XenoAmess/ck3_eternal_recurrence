"""Fit only the generation-bound demo game window to its actual monitor."""
import argparse
import ctypes
import json
from ctypes import wintypes as w
from datetime import datetime, timedelta, timezone
from pathlib import Path
import win32con
import win32api
import win32gui
import win32process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    assert not args.receipt.exists()
    launch = json.loads(args.launch_receipt.read_text(encoding="utf-8"))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
    kernel.GetProcessTimes.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.OpenProcess(0x101000, False, launch["pid"])
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        times = [w.FILETIME() for _ in range(4)]
        assert kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times))
        raw = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        date = launch["creation_date"]
        expected = datetime.strptime(date[:21], "%Y%m%d%H%M%S.%f").replace(
            tzinfo=timezone(timedelta(minutes=int(date[21:]))))
        assert abs((raw - 116444736000000000) / 10000000 - expected.timestamp()) < .001
        windows = []
        def collect(hwnd, unused):
            if (win32gui.IsWindowVisible(hwnd)
                    and win32process.GetWindowThreadProcessId(hwnd)[1] == launch["pid"]
                    and win32gui.GetWindowText(hwnd) == "Crusader Kings III"):
                windows.append(hwnd)
        win32gui.EnumWindows(collect, None)
        assert len(windows) == 1
        hwnd = windows[0]
        assert not win32gui.IsIconic(hwnd)
        monitor = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd, 2))["Monitor"]
        before = {"window": win32gui.GetWindowRect(hwnd), "client": win32gui.GetClientRect(hwnd),
                  "style": win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)}
        # The requested fullscreen content had restored window decorations and
        # an oversized client. Use a borderless popup inside this monitor.
        style = before["style"] & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                                     win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE)
        style |= win32con.WS_POPUP
        if style >= 0x80000000:
            style -= 0x100000000
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        left, top, right, bottom = monitor
        win32gui.SetWindowPos(hwnd, 0, left, top, right-left, bottom-top,
                              win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED)
        assert win32process.GetWindowThreadProcessId(hwnd)[1] == launch["pid"]
        after = {"window": win32gui.GetWindowRect(hwnd), "client": win32gui.GetClientRect(hwnd),
                 "style": win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)}
        assert after["window"] == monitor
        assert after["client"] == (0, 0, right-left, bottom-top)
        result = {"at_utc": datetime.now(timezone.utc).isoformat(), "pid": launch["pid"],
                  "creation_filetime": raw, "hwnd": hwnd, "monitor": monitor,
                  "before": before, "after": after, "no_gameplay_input": True}
        with args.receipt.open("x", encoding="utf-8") as file:
            json.dump(result, file, indent=2)
        print(json.dumps(result), flush=True)
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    main()
