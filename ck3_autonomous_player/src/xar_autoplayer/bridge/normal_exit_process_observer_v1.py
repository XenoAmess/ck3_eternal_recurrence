"""Read-only original-process observer for the map normal-exit driver.

Importing this module performs no Win32, process, UI or pipe calls. Production
constructs Win32ProcessApi explicitly only immediately before terminal dispatch.
The API seam permits offline tests of the actual observer without touching a game.
"""
from __future__ import annotations

import ctypes
from dataclasses import asdict, dataclass
import os
import secrets
import time
from typing import Callable, Protocol

SYNCHRONIZE = 0x00100000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
WAIT_FAILED = 0xFFFFFFFF
MAX_OBSERVATION_WAIT_MS = 30_000


def exact_integer(value: object, minimum: int, maximum: int, field: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{field} requires an exact integer in [{minimum}, {maximum}]")
    return value


class ProcessApi(Protocol):
    def open_process(self, access: int, pid: int) -> int: ...
    def process_id(self, handle: int) -> int: ...
    def creation_filetime(self, handle: int) -> int: ...
    def wait(self, handle: int, timeout_ms: int) -> int: ...
    def exit_code(self, handle: int) -> int: ...
    def close(self, handle: int) -> None: ...


class Win32ProcessApi:
    """Exact handle APIs; no process discovery, signaling or termination."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise RuntimeError("original-process observation requires Windows")
        from ctypes import wintypes

        class FileTime(ctypes.Structure):
            _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

        self._filetime = FileTime
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        prototypes = {
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "GetProcessId": ([wintypes.HANDLE], wintypes.DWORD),
            "GetProcessTimes": ([wintypes.HANDLE] + [ctypes.POINTER(FileTime)] * 4, wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
            "GetExitCodeProcess": ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in prototypes.items():
            function = getattr(self._kernel, name)
            function.argtypes = arguments
            function.restype = result
        self._dword = wintypes.DWORD

    @staticmethod
    def _error() -> OSError:
        return ctypes.WinError(ctypes.get_last_error())

    def open_process(self, access: int, pid: int) -> int:
        handle = self._kernel.OpenProcess(access, False, pid)
        if not handle:
            raise self._error()
        return int(handle)

    def process_id(self, handle: int) -> int:
        pid = int(self._kernel.GetProcessId(handle))
        if not pid:
            raise self._error()
        return pid

    def creation_filetime(self, handle: int) -> int:
        creation, exit_time, kernel, user = (self._filetime() for _ in range(4))
        if not self._kernel.GetProcessTimes(handle, ctypes.byref(creation),
                                            ctypes.byref(exit_time), ctypes.byref(kernel),
                                            ctypes.byref(user)):
            raise self._error()
        return (int(creation.high) << 32) | int(creation.low)

    def wait(self, handle: int, timeout_ms: int) -> int:
        return int(self._kernel.WaitForSingleObject(handle, timeout_ms))

    def exit_code(self, handle: int) -> int:
        code = self._dword()
        if not self._kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise self._error()
        return int(code.value)

    def close(self, handle: int) -> None:
        if not self._kernel.CloseHandle(handle):
            raise self._error()


@dataclass(frozen=True)
class RetainedProcessIdentity:
    pid: int
    creation_filetime_100ns: int
    retained_handle_token: str

    def __post_init__(self) -> None:
        exact_integer(self.pid, 1, 0xFFFFFFFF, 'retained pid')
        exact_integer(self.creation_filetime_100ns, 1, 0xFFFFFFFFFFFFFFFF, 'retained creation FILETIME')
        if type(self.retained_handle_token) is not str or not self.retained_handle_token:
            raise ValueError('original retained handle identity token required')


class RetainedProcessObserver:
    """Pin once, check before dispatch, and observe only that original handle."""

    def __init__(self, api: ProcessApi, pid: int, creation_filetime_100ns: int,
                 *, clock: Callable[[], int] = time.monotonic_ns,
                 token_factory: Callable[[], str] = lambda: secrets.token_hex(16)) -> None:
        pid = exact_integer(pid, 1, 0xFFFFFFFF, "pid")
        creation_filetime_100ns = exact_integer(
            creation_filetime_100ns, 1, 0xFFFFFFFFFFFFFFFF, "creation_filetime_100ns")
        self._api, self._clock = api, clock
        self._handle: int | None = None
        self.close_error: str | None = None
        self._handle = exact_integer(api.open_process(
            SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, pid), 1,
            (1 << (8 * ctypes.sizeof(ctypes.c_void_p))) - 1, "retained_handle")
        try:
            actual_pid = exact_integer(api.process_id(self._handle), 1, 0xFFFFFFFF, "actual_pid")
            actual_creation = exact_integer(api.creation_filetime(self._handle), 1,
                                            0xFFFFFFFFFFFFFFFF, "actual_creation_filetime")
            if actual_pid != pid or actual_creation != creation_filetime_100ns:
                raise ValueError("original process identity differs from native exit context")
            token = token_factory()
            if type(token) is not str or not token:
                raise ValueError("retained handle token required")
            self.identity = RetainedProcessIdentity(pid, creation_filetime_100ns, token)
            self.pinned_monotonic_ns = exact_integer(clock(), 0, 0xFFFFFFFFFFFFFFFF,
                                                    "pinned_monotonic_ns")
        except BaseException:
            self.close()
            raise

    def _original_handle(self) -> int:
        if self._handle is None:
            raise RuntimeError("original process handle is closed")
        return self._handle

    def verify_before_dispatch(self) -> dict:
        handle = self._original_handle()
        pid = exact_integer(self._api.process_id(handle), 1, 0xFFFFFFFF, "preconfirm_pid")
        creation = exact_integer(self._api.creation_filetime(handle), 1,
                                 0xFFFFFFFFFFFFFFFF, "preconfirm_creation_filetime")
        if (pid, creation) != (self.identity.pid, self.identity.creation_filetime_100ns):
            raise ValueError("original handle identity changed before confirmation")
        wait = exact_integer(self._api.wait(handle, 0), 0, 0xFFFFFFFF, "preconfirm_wait_result")
        if wait != WAIT_TIMEOUT:
            raise ValueError("original process is not proven running before confirmation")
        return {**asdict(self.identity), "wait_result": wait,
                "verified_monotonic_ns": exact_integer(self._clock(), 0, 0xFFFFFFFFFFFFFFFF,
                                                       "verified_monotonic_ns"),
                "observation_clock_domain": "driver_monotonic_v1"}

    def observe(self, timeout_ms: int = 5000) -> dict:
        timeout_ms = exact_integer(timeout_ms, 0, MAX_OBSERVATION_WAIT_MS, "timeout_ms")
        handle = self._original_handle()
        errors: list[str] = []
        identity_verified=False
        try:
            actual_pid=exact_integer(self._api.process_id(handle),1,0xFFFFFFFF,'observed original PID')
            actual_creation=exact_integer(self._api.creation_filetime(handle),1,0xFFFFFFFFFFFFFFFF,
                                          'observed original creation FILETIME')
            identity_verified=(actual_pid,actual_creation)==(self.identity.pid,self.identity.creation_filetime_100ns)
            if not identity_verified: errors.append('original handle identity differs from its retained pin')
        except Exception as error:
            errors.append(f'identity: {type(error).__name__}: {error}')
        try:
            wait = exact_integer(self._api.wait(handle, timeout_ms), 0, 0xFFFFFFFF, "wait_result")
        except Exception as error:
            wait = WAIT_FAILED
            errors.append(f"wait: {type(error).__name__}: {error}")
        # This read is independent even when waiting failed or timed out.
        try:
            code = exact_integer(self._api.exit_code(handle), 0, 0xFFFFFFFF, "exit_code")
        except Exception as error:
            code = None
            errors.append(f"exit_code: {type(error).__name__}: {error}")
        state = "signaled" if wait == WAIT_OBJECT_0 else "timeout" if wait == WAIT_TIMEOUT else "failed"
        return {**asdict(self.identity), "wait_result": wait, "wait_state": state,
                "exit_code": code, "process_identity_verified":identity_verified,
                "process_exit_observed": identity_verified and state == "signaled" and code is not None,
                "observed_monotonic_ns": exact_integer(self._clock(), 0, 0xFFFFFFFFFFFFFFFF,
                                                       "observed_monotonic_ns"), "timeout_ms": timeout_ms,
                "observation_deadline_reached": state == "timeout",
                "observation_clock_domain": "driver_monotonic_v1", "errors": errors}

    def close(self) -> None:
        if self._handle is not None:
            handle, self._handle = self._handle, None
            try:
                self._api.close(handle)
            except Exception as error:
                # Cleanup errors cannot erase an independently recorded exit fact.
                self.close_error = f'{type(error).__name__}: {error}'

    def __enter__(self) -> RetainedProcessObserver:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
