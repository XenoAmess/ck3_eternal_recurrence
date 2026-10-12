"""Place one attested CK3 generation on Desktop1 without activating it.

No game input, desktop switch, process launch or termination is exposed here.
The caller owns the runtime admission; --deadline-utc retains its original end.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import importlib.metadata
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid


def deadline_check(value: str) -> None:
    end = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if end.tzinfo is None or datetime.now(timezone.utc) >= end:
        raise RuntimeError("original runtime admission deadline reached or missing UTC offset")


class ProcessGeneration:
    """Keep an exact query/synchronization handle until the owner finishes."""

    def __init__(self, pid: int, executable: Path, *, creation_date=None, creation_filetime=None):
        if os.name != "nt" or type(pid) is not int or pid <= 0:
            raise ValueError("an exact positive Windows process PID is required")
        self.pid, self.executable = pid, executable.resolve()
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_uint64)] * 4
        self.kernel.GetProcessTimes.restype = wintypes.BOOL
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.OpenProcess(0x00101000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            values = [ctypes.c_uint64() for _ in range(4)]
            if not self.kernel.GetProcessTimes(self.handle, *(ctypes.byref(v) for v in values)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.creation_filetime = values[0].value
            if creation_filetime is not None and self.creation_filetime != creation_filetime:
                raise RuntimeError("process creation FILETIME differs from the pinned generation")
            if creation_date is not None:
                stamp = datetime.strptime(creation_date[:21], "%Y%m%d%H%M%S.%f").replace(
                    tzinfo=timezone(timedelta(minutes=int(creation_date[21:]))))
                actual = self.creation_filetime / 10_000_000 - 11_644_473_600
                if abs(actual - stamp.timestamp()) > .001:
                    raise RuntimeError("process creation date differs from the launch receipt")
            self.check()
        except BaseException:
            self.close()
            raise

    def check(self):
        if not self.handle or self.kernel.WaitForSingleObject(self.handle, 0) != 258:
            raise RuntimeError("pinned process is exited or its kernel state is unknown")
        length = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(length.value)
        if not self.kernel.QueryFullProcessImageNameW(self.handle, 0, image, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(image.value).resolve() != self.executable:
            raise RuntimeError("pinned process image differs from the explicit executable")

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def game_generation(launch: dict) -> ProcessGeneration:
    command = launch.get("command")
    if not isinstance(command, list) or not command or not isinstance(launch.get("creation_date"), str):
        raise ValueError("use the exact Root Game launch receipt with command and creation_date")
    executable = Path(command[0]).resolve()
    if executable.name.casefold() != "ck3.exe":
        raise ValueError("launch receipt is not the CK3 executable")
    return ProcessGeneration(launch.get("pid"), executable, creation_date=launch["creation_date"])


def check_game_window(generation, hwnd, classname=None):
    import win32gui
    import win32process
    generation.check()
    if (not win32gui.IsWindow(hwnd)
            or win32process.GetWindowThreadProcessId(hwnd)[1] != generation.pid
            or win32gui.GetWindowText(hwnd) != "Crusader Kings III"
            or (classname is not None and win32gui.GetClassName(hwnd) != classname)):
        raise RuntimeError("the exact Game HWND disappeared, changed generation or identity")


def wait_game_window(generation, seconds, deadline_utc):
    import win32gui
    import win32process
    if not 0 < seconds <= 300:
        raise ValueError("window wait must be finite and at most 300 seconds")
    end = time.monotonic() + seconds
    while True:
        deadline_check(deadline_utc)
        generation.check()
        windows = []
        def collect(hwnd, _):
            if (win32gui.IsWindowVisible(hwnd)
                    and win32process.GetWindowThreadProcessId(hwnd)[1] == generation.pid
                    and win32gui.GetWindowText(hwnd) == "Crusader Kings III"):
                windows.append(hwnd)
        win32gui.EnumWindows(collect, None)
        if len(windows) > 1:
            raise RuntimeError("multiple windows match this exact Game generation")
        if windows:
            check_game_window(generation, windows[0])
            return windows[0]
        if time.monotonic() >= end:
            raise TimeoutError("no unique Game HWND appeared within the bounded wait")
        time.sleep(.25)


def desktop_inventory():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops") as key:
        raw, _ = winreg.QueryValueEx(key, "VirtualDesktopIDs")
        current, _ = winreg.QueryValueEx(key, "CurrentVirtualDesktop")
    if not isinstance(raw, bytes) or not raw or len(raw) % 16 or not isinstance(current, bytes) or len(current) != 16:
        raise RuntimeError("Shell desktop inventory is malformed")
    ids = [str(uuid.UUID(bytes_le=raw[i:i + 16])) for i in range(0, len(raw), 16)]
    current_id = str(uuid.UUID(bytes_le=current))
    if len(ids) != len(set(ids)) or current_id not in ids:
        raise RuntimeError("Shell desktop inventory is ambiguous")
    return ids, current_id


def explicit_pyvda(root):
    root = root.resolve(strict=True)
    versions = {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions(path=[str(root)])}
    if versions.get("pyvda") != "0.6.0" or versions.get("comtypes") != "1.4.16":
        raise RuntimeError("explicit UI root must contain pyvda0.6.0 and comtypes1.4.16")
    for name in ("pyvda", "comtypes"):
        for loaded_name, module in list(sys.modules.items()):
            if loaded_name == name or loaded_name.startswith(name + "."):
                origin = getattr(module, "__file__", None)
                if not origin or not Path(origin).resolve().is_relative_to(root):
                    raise RuntimeError("ambient UI dependency already loaded: " + loaded_name)
    sys.path.insert(0, str(root))
    import pyvda
    import comtypes
    origins = {name: str(Path(module.__file__).resolve())
               for name, module in (("pyvda", pyvda), ("comtypes", comtypes))}
    if any(not Path(path).is_relative_to(root) for path in origins.values()):
        raise RuntimeError("UI imports escaped the explicit dependency root")
    if getattr(pyvda, "__version__", None) != "0.6.0":
        raise RuntimeError("loaded pyvda version differs from its explicit metadata")
    return pyvda, {"root": str(root), "versions": versions, "module_origins": origins,
                  "entry_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                   for name, path in origins.items()}}


def place(args):
    data = {"schema": "xar.g2.managed-desktop1-placement/v1", "status": "RED",
            "launch_receipt": str(args.launch_receipt.resolve()), "gameplay_input_sent": False,
            "desktop_switches": 0, "process_launch_or_stop_calls": 0,
            "runtime_rendering_qualified": False}
    primary = None
    ole = None
    initialized = False
    try:
        import win32api
        import win32con
        import win32gui
        deadline_check(args.deadline_utc)
        launch = json.loads(args.launch_receipt.read_text(encoding="utf-8-sig"))
        data["pid"] = launch.get("pid")
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.windows_virtual_desktop import window_virtual_desktop
        ids, current = desktop_inventory()
        target_id = str(uuid.UUID(args.desktop_id))
        foreground = win32gui.GetForegroundWindow()
        data.update(target_desktop_id=target_id, current_desktop_id=current, foreground_before=foreground)
        if target_id != ids[0]:
            raise RuntimeError("explicit target is not the current Shell Desktop1")
        if args.expected_current_desktop_id and current != str(uuid.UUID(args.expected_current_desktop_id)):
            raise RuntimeError("the active user desktop differs from the supplied fresh identity")
        ole = ctypes.WinDLL("ole32", use_last_error=True)
        ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        ole.CoInitializeEx.restype = ctypes.c_long
        ole.CoUninitialize.argtypes = []
        ole.CoUninitialize.restype = None
        result = ole.CoInitializeEx(None, 2)
        data["sta_hresult"] = result & 0xffffffff
        if result not in (0, 1):
            raise RuntimeError("Shell placement requires an explicit STA apartment")
        initialized = True
        with game_generation(launch) as generation:
            hwnd = wait_game_window(generation, args.wait_seconds, args.deadline_utc)
            classname = win32gui.GetClassName(hwnd)
            data.update(hwnd=hwnd, window_class=classname, creation_filetime=generation.creation_filetime,
                        before=window_virtual_desktop(hwnd))
            pyvda, dependencies = explicit_pyvda(args.ui_dependencies)
            data["dependencies"] = dependencies
            desktops = pyvda.get_virtual_desktops()
            if [str(uuid.UUID(str(d.id).strip("{}"))) for d in desktops] != ids:
                raise RuntimeError("pyvda desktop sequence differs from the Shell inventory")
            target = pyvda.VirtualDesktop(1)
            if str(uuid.UUID(str(target.id).strip("{}"))) != target_id:
                raise RuntimeError("pyvda Desktop1 identity changed")
            def guard():
                deadline_check(args.deadline_utc)
                check_game_window(generation, hwnd, classname)
                if desktop_inventory() != (ids, current) or win32gui.GetForegroundWindow() != foreground:
                    raise RuntimeError("user desktop or foreground changed; no focus restoration will be attempted")
            guard()
            view = pyvda.AppView(hwnd=hwnd)
            if view.hwnd != hwnd:
                raise RuntimeError("Shell AppView does not bind the exact Game HWND")
            view.move(target)
            guard()
            if window_virtual_desktop(hwnd)["desktop_id"] != target_id:
                raise RuntimeError("Desktop1 move was not materially observed")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            guard()
            monitor = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd, 2))["Monitor"]
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style = (style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE)) | win32con.WS_POPUP
            if style >= 0x80000000:
                style -= 0x100000000
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            guard()
            left, top, right, bottom = monitor
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, left, top, right - left, bottom - top,
                win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW)
            guard()
            final = window_virtual_desktop(hwnd)
            client = win32gui.GetClientRect(hwnd)
            actual_rect = win32gui.GetWindowRect(hwnd)
            actual_topmost = bool(win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST)
            actual_minimized = bool(win32gui.IsIconic(hwnd))
            observed_foreground = win32gui.GetForegroundWindow()
            observed_ids, observed_current = desktop_inventory()
            generation.check()
            data.update(after=final, window_rect=list(actual_rect),
                        client_rect=list(client), foreground_after=observed_foreground,
                        current_desktop_after=observed_current,
                        topmost=actual_topmost, minimized=actual_minimized)
            if (final["desktop_id"] != target_id or actual_minimized
                    or not actual_topmost or actual_rect != monitor
                    or client != (0, 0, right - left, bottom - top)
                    or observed_foreground != foreground or (observed_ids, observed_current) != (ids, current)
                    or (current != target_id and (final["on_current_virtual_desktop"] is not False
                                                  or not final["dwm_cloaked_flags"] & 2))):
                raise RuntimeError("final Desktop1 geometry/topmost/nonmin qualification failed")
            deadline_check(args.deadline_utc)
            check_game_window(generation, hwnd, classname)
            data.update(status="GREEN", current_desktop_unchanged=True,
                        foreground_unchanged=True, background_assignment_verified=current != target_id)
    except Exception as error:
        data["error"] = str(error)
        primary = error
    finally:
        if initialized:
            ole.CoUninitialize()
        data["at_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            with args.receipt.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
        except OSError as receipt_error:
            raise RuntimeError("placement receipt write failed; primary=" + repr(primary)) from receipt_error
    if primary is not None:
        raise primary
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("launch-receipt", "ui-dependencies", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--desktop-id", required=True)
    parser.add_argument("--expected-current-desktop-id")
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--wait-seconds", type=float, default=30)
    args = parser.parse_args()
    if args.receipt.exists() or not args.receipt.parent.is_dir():
        parser.error("receipt must be a new file in the caller's admitted output directory")
    print(json.dumps(place(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
