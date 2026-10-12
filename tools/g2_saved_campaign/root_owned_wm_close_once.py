"""Root-only one-shot graceful WM_CLOSE for the already-owned CK3 window.

No window restoration, focus, input synthesis, kill, SDK/Driver or native-map
call. WM_CLOSE accepted is only a request; retained process signaled is separate.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
from pathlib import Path

def utc():
    return datetime.now(timezone.utc).isoformat()

def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--hwnd", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--wait-ms", type=int, default=30000)
    parser.add_argument("--expected-creation-filetime-100ns", type=int, required=True)
    args = parser.parse_args()
    if not 0 <= args.wait_ms <= 60000:
        parser.error("--wait-ms must be 0..60000")
    if not 0 < args.expected_creation_filetime_100ns <= 0xffffffffffffffff:
        parser.error("--expected-creation-filetime-100ns must be a positive uint64")
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.PostMessageW.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessId.argtypes = [wintypes.HANDLE]
    kernel.GetProcessId.restype = wintypes.DWORD
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    owner = wintypes.DWORD()
    thread = user.GetWindowThreadProcessId(args.hwnd, ctypes.byref(owner))
    if not thread or owner.value != args.pid:
        raise RuntimeError("Root-owned HWND no longer belongs to the selected PID; no close posted")
    handle = kernel.OpenProcess(0x00100000 | 0x1000, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if kernel.GetProcessId(handle) != args.pid:
            raise RuntimeError("opened process differs from Root-owned PID; no close posted")
        creation, exited, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exited),
                                      ctypes.byref(kernel_time), ctypes.byref(user_time)):
            raise ctypes.WinError(ctypes.get_last_error())
        identity = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        if identity != args.expected_creation_filetime_100ns:
            raise RuntimeError("held process creation differs from Root-owned raw ticks; no close posted")
        args.output_dir.mkdir(parents=True, exist_ok=False)
        requested = {
            "schema": "xar.r0084.owned-window-graceful-close.v1",
            "start_utc": utc(), "pid": args.pid, "hwnd": args.hwnd,
            "process_creation_filetime_100ns": identity,
            "expected_creation_filetime_100ns": args.expected_creation_filetime_100ns,
            "held_process_identity_matched": True,
            "action": "one PostMessageW WM_CLOSE(0x0010)",
            "window_restore_or_focus_calls": 0, "kill_or_terminate_calls": 0,
            "SDK_Driver_native_map_calls": 0,
            "typed_normal_exit_observed": False, "autosave_verified": False,
            "saved_checkpoint_reference": None,
            "checkpoint_provenance": "Root caller supplies independent actual checkpoint; sender does not verify SAVE",
        }
        posted = bool(user.PostMessageW(args.hwnd, 0x0010, 0, 0))
        requested.update({"close_request_posted": posted,
                          "post_error": 0 if posted else ctypes.get_last_error(),
                          "process_exit_observed": False,
                          "status": "WM_CLOSE_REQUEST_POSTED_NOT_EXIT_PROOF" if posted else "POST_FAILED"})
        write_new(args.output_dir / "ROOT-WM-CLOSE-REQUEST.json", requested)
        if not posted:
            print(json.dumps(requested), flush=True)
            return 1
        waited = kernel.WaitForSingleObject(handle, args.wait_ms)
        result = dict(requested)
        result.update({"end_utc": utc(), "wait_ms": args.wait_ms,
                       "wait_result": waited, "WM_CLOSE_submission_count": 1,
                       "orderly_exit_verified": False, "retry_close_authorized": False})
        if waited == 0:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            result.update({"status": "OWNED_PROCESS_EXIT_OBSERVED_AFTER_WM_CLOSE",
                           "process_exit_observed": True, "exit_code": code.value})
        elif waited == 258:
            result.update({"status": "WM_CLOSE_PENDING_NO_EXIT_OBSERVED", "exit_code": None,
                           "instruction": "Retain minimized state; do not replay close or force terminate. Root chooses actual next stock close path."})
        else:
            result.update({"status": "PROCESS_WAIT_FAILED", "wait_error": ctypes.get_last_error(),
                           "exit_code": None})
        write_new(args.output_dir / "ROOT-WM-CLOSE-RESULT.json", result)
        print(json.dumps(result), flush=True)
        return 0 if result["process_exit_observed"] else 2
    finally:
        kernel.CloseHandle(handle)

if __name__ == "__main__":
    raise SystemExit(main())
