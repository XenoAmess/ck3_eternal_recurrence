"""Desktop fallback transport for the already supervised, unique CK3 process."""
from __future__ import annotations

import ctypes
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from .evidence import checked_file, load_json, require, sha256, write_new


DWORD, WORD, LONG, HANDLE = ctypes.c_uint32, ctypes.c_uint16, ctypes.c_int32, ctypes.c_void_p


class KeyboardInput(ctypes.Structure):
    _fields_ = [("wVk", WORD), ("wScan", WORD), ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", LONG), ("dy", LONG), ("mouseData", DWORD), ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD)]


class InputUnion(ctypes.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyboardInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", DWORD), ("data", InputUnion)]


class Rect(ctypes.Structure):
    _fields_ = [(key, LONG) for key in ("left", "top", "right", "bottom")]


class GuiThreadInfo(ctypes.Structure):
    _fields_ = [("cbSize", DWORD), ("flags", DWORD)] + [(key, HANDLE) for key in
        ("hwndActive", "hwndFocus", "hwndCapture", "hwndMenuOwner", "hwndMoveSize", "hwndCaret")] + [("rcCaret", Rect)]


def abi() -> tuple[int, ...]:
    return ctypes.sizeof(Input), ctypes.sizeof(KeyboardInput), Input.data.offset, ctypes.sizeof(GuiThreadInfo)


class OwnedWindowsBackend:
    """Observes custody, without registering or renewing its screen task."""
    def __init__(self):
        require(sys.platform == "win32", "Windows desktop fallback requires Windows")
        require(abi() == {4: (28, 16, 4, 48), 8: (40, 24, 8, 72)}[ctypes.sizeof(HANDLE)], "Win32 INPUT ABI differs")
        self.u = ctypes.WinDLL("user32", use_last_error=True)
        for name, arguments, result in [
            ("GetKeyboardLayout", [DWORD], HANDLE),
            ("LoadKeyboardLayoutW", [ctypes.c_wchar_p, DWORD], HANDLE),
            ("GetGUIThreadInfo", [DWORD, ctypes.POINTER(GuiThreadInfo)], LONG),
            ("MapVirtualKeyExW", [DWORD, DWORD, HANDLE], DWORD),
            ("GetAsyncKeyState", [ctypes.c_int], ctypes.c_int16),
            ("SendInput", [DWORD, ctypes.POINTER(Input), ctypes.c_int], DWORD),
            ("SendMessageTimeoutW", [HANDLE, DWORD, ctypes.c_size_t, ctypes.c_ssize_t,
                                    DWORD, DWORD, ctypes.POINTER(ctypes.c_size_t)], ctypes.c_ssize_t),
        ]:
            function = getattr(self.u, name)
            function.argtypes, function.restype = arguments, result

    def guard(self, profile: dict, initial: bool = False) -> dict:
        import psutil
        import pyautogui
        import win32gui
        import win32process
        owner = profile["owner"]
        cli = checked_file(owner["bus_cli"])
        command = [sys.executable, "-B", str(cli), "--bus-dir", owner["bus_dir"],
                   "--expected-cli-sha256", owner["bus_cli"]["sha256"], "list"]
        tasks = json.loads(subprocess.check_output(command, timeout=10))["tasks"]
        holders = [t for t in tasks if "ck3-screen:acquired" in t.get("resources", [])]
        require(len(holders) == 1, "screen ownership is not unique")
        task = holders[0]
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(task["updated_at_utc"])).total_seconds()
        require(task["task_id"] == owner["screen_task"] and task["state"] == "running"
                and task["resources"] == ["ck3-screen:acquired"] and 0 <= age < 600,
                "screen lease differs/expired")
        git = profile.get("git_executable", "git")
        def git_read(*args):
            return subprocess.check_output([git, *args], cwd=owner["repo"], timeout=10)
        require(not git_read("status", "--porcelain=v1", "--untracked-files=normal"), "owner checkout dirty")
        require(git_read("rev-parse", "HEAD").decode().strip() == owner["head"], "owner HEAD changed")
        control = load_json(checked_file(owner["control"]))
        require(control["ck3_pid"] == owner["pid"], "control PID differs")
        process = psutil.Process(owner["pid"])
        require(abs(process.create_time() - owner["process_create_time"]) < .1, "PID creation differs")
        require(Path(process.exe()).resolve() == Path(owner["executable"]["path"]).resolve()
                == Path(control["executable"]).resolve(), "process executable differs")
        require({p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "ck3.exe"}
                == {owner["pid"]}, "CK3 process inventory differs")
        hwnd = win32gui.GetForegroundWindow()
        thread, pid = win32process.GetWindowThreadProcessId(hwnd)
        require(pid == owner["pid"] and win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd),
                "owned CK3 window is not foreground")
        require(tuple(pyautogui.size()) == tuple(profile["routing"]["frame_size"]), "live desktop size changed")
        if initial:
            checked_file(owner["executable"])
            fallback = profile["fallback"]
            require(fallback["reason"], "MCP fallback needs an actual recorded blocker")
            checked_file(fallback["evidence"])
            handoff = load_json(checked_file(fallback["consumer_handoff"]))
            require(handoff.get("consumer_stopped") is True and handoff.get("run_id") == owner["run_id"]
                    and handoff.get("pid") == owner["pid"], "original consumer-stop handoff differs")
            require(profile["steam_offline_review"].get("reviewed_offline") is True,
                    "fresh offline screenshot must have been directly reviewed")
            checked_file(profile["steam_offline_review"])
        return {"pid": pid, "hwnd": hwnd, "thread": thread,
                "process_create_time": process.create_time(), "control_sha256": owner["control"]["sha256"],
                "head": owner["head"], "screen_task": owner["screen_task"]}

    def capture(self, path: Path) -> dict:
        import pyautogui
        require(not path.exists(), "capture already exists")
        image = pyautogui.screenshot()
        image.save(path)
        return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size, "size": list(image.size)}

    def focus(self, profile: dict) -> tuple[dict, int]:
        import win32gui
        import win32process
        bound = self.guard(profile)
        info = GuiThreadInfo(cbSize=ctypes.sizeof(GuiThreadInfo))
        require(self.u.GetGUIThreadInfo(bound["thread"], ctypes.byref(info)), "focused control unavailable")
        require(info.hwndActive == bound["hwnd"] and info.hwndFocus
                and (info.hwndFocus == bound["hwnd"] or win32gui.IsChild(bound["hwnd"], info.hwndFocus))
                and not info.flags & 0x1e, "control focus/menu differs")
        thread, pid = win32process.GetWindowThreadProcessId(info.hwndFocus)
        layout = self.u.GetKeyboardLayout(thread)
        require(pid == bound["pid"] and layout and layout & 0xffff == 0x0409,
                "focused control PID/US0409 differs")
        return bound, layout

    def send_key(self, key: str, profile: dict, step: Path) -> dict:
        require(key in {"Shift+1", "Escape"}, "unsupported stability-assistance key")
        bound = self.guard(profile)
        layout = self.u.LoadKeyboardLayoutW("00000409", 0)
        reply = ctypes.c_size_t()
        require(layout and self.u.SendMessageTimeoutW(bound["hwnd"], 0x50, 0, layout, 0x23, 1000, ctypes.byref(reply)),
                "US layout request failed")
        current, layout = self.focus(profile)
        require(current == bound, "owner changed before key")
        virtuals = (0xa0, 0x31) if key == "Shift+1" else (0x1b,)
        require(not any(self.u.GetAsyncKeyState(vk) & 0x8000
                        for vk in {*virtuals, 0x10, 0x11, 0x12, 0x5b, 0x5c}), "key/modifier already held")
        scans = []
        for vk in virtuals:
            mapped = int(self.u.MapVirtualKeyExW(vk, 4, layout))
            require(mapped & 255 and mapped >> 8 in (0, 0xe0), "invalid scancode mapping")
            scans.append((mapped & 255, 8 | (1 if mapped >> 8 else 0)))
        receipt = {"key": key, "ABI": abi(), "phases": [], "business_result": "NOT_VERIFIED"}
        held = []
        try:
            for scan, flags in scans:
                current, current_layout = self.focus(profile)
                require(current == bound and current_layout == layout, "focus/layout changed before key down")
                event = Input(type=1, ki=KeyboardInput(wScan=scan, dwFlags=flags))
                accepted = int(self.u.SendInput(1, ctypes.byref(event), ctypes.sizeof(Input)))
                receipt["phases"].append({"scan": scan, "flags": flags, "accepted": accepted})
                if accepted == 1:
                    held.append((scan, flags))
                require(accepted == 1, "key down not fully accepted; no retry")
            # CK3 must observe the chord across input polling, rather than four
            # down/up entries disappearing within one SendInput batch.
            time.sleep(.12)
            current, current_layout = self.focus(profile)
            require(current == bound and current_layout == layout, "focus/layout changed while key held")
        finally:
            # Release only successfully inserted downs; never repeat a down.
            for scan, flags in reversed(held):
                event = Input(type=1, ki=KeyboardInput(wScan=scan, dwFlags=flags | 2))
                accepted = int(self.u.SendInput(1, ctypes.byref(event), ctypes.sizeof(Input)))
                receipt["phases"].append({"scan": scan, "flags": flags | 2, "accepted": accepted, "cleanup_keyup": True})
            write_new(step / "keyboard.json", receipt)
        require(all(row["accepted"] == 1 for row in receipt["phases"]), "partial key stream; no retry")
        self.focus(profile)
        return receipt
