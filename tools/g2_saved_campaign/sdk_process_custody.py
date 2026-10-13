"""Retain exact Windows process generations for SDK custody receipts.

Only query/synchronize access is requested. A signaled kernel handle proves
exit even when GetExitCodeProcess returns 259; an exit code alone does not.
The MCP adapter captures the actual stdio factory result without PID scans.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import ctypes
from ctypes import wintypes
import ntpath
import os
import threading
from typing import AsyncIterator, Protocol


WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000


class ProcessCustodyError(RuntimeError):
    """An exact process identity or retained-handle observation is unavailable."""


class ProcessAPI(Protocol):
    """Injectable retained-handle operations; observe never reopens a PID."""

    def open_process(self, pid: int) -> object: ...
    def query_creation_filetime(self, handle: object) -> int: ...
    def query_executable(self, handle: object) -> str: ...
    def wait_zero(self, handle: object) -> int: ...
    def get_exit_code(self, handle: object) -> int: ...
    def close_handle(self, handle: object) -> None: ...


class WindowsProcessAPI:
    """Minimal Win32 implementation with no launch or termination operation."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise ProcessCustodyError("Windows process custody requires Windows or an injected API")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        self._kernel = kernel

    def open_process(self, pid: int) -> object:
        handle = self._kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def query_creation_filetime(self, handle: object) -> int:
        creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        if not self._kernel.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exit_time),
            ctypes.byref(kernel_time), ctypes.byref(user_time),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime

    def query_executable(self, handle: object) -> str:
        buffer = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buffer))
        if not self._kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer[:length.value]

    def wait_zero(self, handle: object) -> int:
        result = int(self._kernel.WaitForSingleObject(handle, 0))
        if result == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def get_exit_code(self, handle: object) -> int:
        code = wintypes.DWORD()
        if not self._kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value

    def close_handle(self, handle: object) -> None:
        if not self._kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def _positive_integer(value: object, name: str, maximum: int) -> int:
    if type(value) is not int or not 0 < value <= maximum:
        raise ProcessCustodyError(f"{name} must be a positive integer no larger than {maximum}")
    return value


def _executable_path(value: object) -> str:
    try:
        path = os.fspath(value)
    except TypeError as error:
        raise ProcessCustodyError("process executable must be an absolute Windows path") from error
    if (not isinstance(path, str) or not path or "\0" in path
            or not ntpath.splitdrive(path)[0] or not ntpath.isabs(path)):
        raise ProcessCustodyError("process executable must be an absolute Windows path")
    return path


def _path_identity(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value))


def _error(stage: str, error: Exception) -> dict[str, str]:
    return {"stage": stage, "type": type(error).__name__, "message": str(error)}


class RetainedProcessGeneration:
    """Own one query/synchronize handle until an explicit, idempotent close."""

    def __init__(self, *, pid: int, creation_filetime: int, executable: str,
                 handle: object, api: ProcessAPI) -> None:
        self._pid = pid
        self._creation_filetime = creation_filetime
        self._executable = executable
        self._handle = handle
        self._api = api
        self._lock = threading.Lock()
        self._closed = False

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def creation_filetime(self) -> int:
        return self._creation_filetime

    @property
    def executable(self) -> str:
        return self._executable

    @classmethod
    def capture(cls, pid: int, *, expected_executable: object = None,
                expected_creation_filetime: int | None = None,
                api: ProcessAPI | None = None) -> RetainedProcessGeneration:
        pid = _positive_integer(pid, "pid", 0xFFFFFFFF)
        expected_path = (_executable_path(expected_executable)
                         if expected_executable is not None else None)
        if expected_creation_filetime is not None:
            _positive_integer(expected_creation_filetime, "expected_creation_filetime", 0xFFFFFFFFFFFFFFFF)
        process_api = WindowsProcessAPI() if api is None else api
        handle = process_api.open_process(pid)
        if handle is None or handle == 0:
            raise ProcessCustodyError("OpenProcess returned no retained handle")
        try:
            creation = _positive_integer(
                process_api.query_creation_filetime(handle), "creation_filetime", 0xFFFFFFFFFFFFFFFF,
            )
            executable = _executable_path(process_api.query_executable(handle))
            if expected_creation_filetime is not None and creation != expected_creation_filetime:
                raise ProcessCustodyError("process creation_filetime differs from the expected generation")
            if expected_path is not None and _path_identity(executable) != _path_identity(expected_path):
                raise ProcessCustodyError("process executable differs from the expected image")
            return cls(pid=pid, creation_filetime=creation, executable=executable,
                       handle=handle, api=process_api)
        except BaseException as error:
            try:
                process_api.close_handle(handle)
            except Exception as close_error:
                error.add_note(f"capture handle close failed: {type(close_error).__name__}: {close_error}")
            raise

    def identity(self, role: str) -> dict[str, object]:
        if not isinstance(role, str) or not role:
            raise ProcessCustodyError("process role must be a nonempty string")
        return {"role": role, "pid": self.pid, "creation_filetime": self.creation_filetime,
                "executable": self.executable}

    def observe(self) -> dict[str, object]:
        """Return independently observed signal and exit code; errors stay explicit."""
        with self._lock:
            result: dict[str, object] = {
                "pid": self.pid, "creation_filetime": self.creation_filetime,
                "executable": self.executable, "kernel_exit_observed": None,
                "wait_result": None, "exit_code": None, "observation_error": None,
            }
            if self._closed:
                result["observation_error"] = _error("closed", ProcessCustodyError("retained handle is closed"))
                return result
            try:
                wait_result = self._api.wait_zero(self._handle)
                if type(wait_result) is int:
                    result["wait_result"] = wait_result
                if type(wait_result) is not int or wait_result not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
                    raise ProcessCustodyError(f"unexpected kernel wait result: {wait_result!r}")
                result["kernel_exit_observed"] = wait_result == WAIT_OBJECT_0
            except Exception as error:
                result["observation_error"] = _error("wait", error)
                return result
            try:
                code = self._api.get_exit_code(self._handle)
                if type(code) is not int or not 0 <= code <= 0xFFFFFFFF:
                    raise ProcessCustodyError("process exit code is not a DWORD")
                result["exit_code"] = code
            except Exception as error:
                result["observation_error"] = _error("exit_code", error)
            return result

    def require_live(self) -> dict[str, object]:
        observed = self.observe()
        if observed["kernel_exit_observed"] is not False or observed["observation_error"] is not None:
            raise ProcessCustodyError(f"retained process is not verified live: {observed}")
        return observed

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            # A failed CloseHandle is not silently retried or reported successful.
            self._closed = True
            self._api.close_handle(self._handle)

    def __enter__(self) -> RetainedProcessGeneration:
        return self

    def __exit__(self, exc_type: object, exc: BaseException | None, traceback: object) -> None:
        try:
            self.close()
        except Exception as error:
            if exc is None:
                raise
            exc.add_note(f"retained handle close failed: {type(error).__name__}: {error}")


class MCPStdioProcessCapture:
    """Actual returned creator object and its independently retained generation."""

    def __init__(self) -> None:
        self.creator_process: object = None
        self.generation: RetainedProcessGeneration | None = None
        self.capture_error: BaseException | None = None

    def require_generation(self) -> RetainedProcessGeneration:
        if self.generation is None:
            raise ProcessCustodyError("MCP stdio factory has not supplied a qualified child") from self.capture_error
        return self.generation


_HOOK_LOCK = threading.Lock()
_ACTIVE_STDIO_HOOKS: set[int] = set()


@asynccontextmanager
async def retain_mcp_stdio_process(
    stdio_module: object, *, expected_executable: object = None,
    expected_creation_filetime: int | None = None, api: ProcessAPI | None = None,
) -> AsyncIterator[MCPStdioProcessCapture]:
    """Wrap MCP's async private creator for exactly one returned application.

    Keep this context around the stdio_client lifetime and supervisor ACK. The
    original creator object remains referenced while OpenProcess acquires the
    independent handle. No process enumeration, argv inference or second child
    is used. On capture failure the actual creator object is retained for the
    caller's existing cleanup path; no process exit is invented. The wrapper
    returns that child even if capture fails, so stdio_client acquires cleanup
    ownership. Call require_generation inside the active stdio_client context.
    """
    if expected_executable is not None:
        _executable_path(expected_executable)
    if expected_creation_filetime is not None:
        _positive_integer(expected_creation_filetime, "expected_creation_filetime", 0xFFFFFFFFFFFFFFFF)
    attribute = "_create_platform_compatible_process"
    original = getattr(stdio_module, attribute, None)
    if not callable(original):
        raise ProcessCustodyError("MCP stdio private process factory is unavailable")
    key = id(stdio_module)
    with _HOOK_LOCK:
        if key in _ACTIVE_STDIO_HOOKS:
            raise ProcessCustodyError("MCP stdio process capture is already active")
        _ACTIVE_STDIO_HOOKS.add(key)
    capture = MCPStdioProcessCapture()
    factory_called = False

    async def retained_factory(*args: object, **kwargs: object) -> object:
        nonlocal factory_called
        if factory_called:
            raise ProcessCustodyError("MCP stdio capture permits only one process creation")
        factory_called = True
        try:
            child = await original(*args, **kwargs)
        except BaseException as error:
            capture.capture_error = error
            raise
        capture.creator_process = child
        try:
            capture.generation = RetainedProcessGeneration.capture(
                getattr(child, "pid", None), expected_executable=expected_executable,
                expected_creation_filetime=expected_creation_filetime, api=api,
            )
        except BaseException as error:
            capture.capture_error = error
        return child

    body_error: BaseException | None = None
    installed = False
    try:
        setattr(stdio_module, attribute, retained_factory)
        installed = True
        try:
            yield capture
        except BaseException as error:
            body_error = error
            raise
        if capture.generation is None:
            raise ProcessCustodyError("MCP stdio capture ended without a qualified factory child") from capture.capture_error
    finally:
        try:
            if installed:
                setattr(stdio_module, attribute, original)
        finally:
            with _HOOK_LOCK:
                _ACTIVE_STDIO_HOOKS.discard(key)
            if capture.generation is not None:
                try:
                    capture.generation.close()
                except Exception as error:
                    if body_error is None:
                        raise
                    body_error.add_note(f"MCP retained handle close failed: {type(error).__name__}: {error}")
