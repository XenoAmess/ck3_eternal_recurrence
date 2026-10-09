"""Python-native Windows process creation helpers."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import ctypes.wintypes
import os
from typing import Any


def is_process_signaled(pid: int) -> bool:
    """Return true only when a zero-time kernel wait proves termination.

    A retained process object can still expose its image and exit code 259.
    Timeouts, access denial and unreadable wait state do not exclude a PID.
    """
    if os.name != "nt":
        return False
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [
            ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
        ]
        kernel32.WaitForSingleObject.restype = ctypes.wintypes.DWORD
        kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
        handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            return False
        try:
            return kernel32.WaitForSingleObject(handle, 0) == 0  # WAIT_OBJECT_0
        finally:
            kernel32.CloseHandle(handle)
    except (OSError, AttributeError):
        return False


def active_process_pids(
    image_name: str, *, signaled_dead_pids: set[int] | None = None
) -> list[int]:
    """Enumerate matching names, excluding only positively signaled objects."""
    import psutil

    active = []
    for process in psutil.process_iter(["pid", "name"]):
        if (process.info["name"] or "").casefold() != image_name.casefold():
            continue
        pid = int(process.info["pid"])
        if is_process_signaled(pid):
            if signaled_dead_pids is not None:
                signaled_dead_pids.add(pid)
        else:
            active.append(pid)
    return sorted(active)


@dataclass(frozen=True)
class WindowsProcessCreationError(RuntimeError):
    return_value: int

    def __str__(self) -> str:
        return f"Win32_Process.Create returned {self.return_value}"


def _property_value(properties: Any, name: str) -> Any:
    return properties(name).Value


def _execute_wmi_method(service: Any, *arguments: Any) -> Any:
    """Call the pywin32 spelling exposed by either dynamic dispatch mode."""

    try:
        execute = service.ExecMethod_
    except AttributeError:
        execute = service.ExecMethod
    return execute(*arguments)


def _create_process_in_current_com_apartment(
    command_line: str, current_directory: str | None
) -> int | None:
    """Perform the WMI call while every IDispatch proxy can still be released."""

    import win32com.client

    service: Any = None
    process_class: Any = None
    method: Any = None
    parameters: Any = None
    output: Any = None
    try:
        service = win32com.client.GetObject("winmgmts:")
        process_class = service.Get("Win32_Process")
        method = process_class.Methods_("Create")
        parameters = method.InParameters.SpawnInstance_()
        parameters.Properties_("CommandLine").Value = command_line
        if current_directory is not None:
            parameters.Properties_("CurrentDirectory").Value = current_directory
        output = _execute_wmi_method(
            service, "Win32_Process", "Create", parameters
        )
        return_value = int(_property_value(output.Properties_, "ReturnValue"))
        if return_value != 0:
            raise WindowsProcessCreationError(return_value)
        raw_pid = _property_value(output.Properties_, "ProcessId")
        return int(raw_pid) if raw_pid not in (None, "") else None
    finally:
        # pywin32 releases these wrappers from their destructors.  Drop every
        # reference before the caller tears down this thread's COM apartment;
        # releasing them after CoUninitialize can fault in pythoncom313.dll.
        output = None
        parameters = None
        method = None
        process_class = None
        service = None


def create_process_via_windows_management(
    command_line: str, current_directory: str | None = None
) -> int | None:
    """Create a process through the Windows management provider without a shell.

    The provider service owns the new process, so the child does not inherit a
    caller-side job object.  ``None`` is returned only when the provider reports
    success but suppresses its optional ProcessId projection.
    """

    if os.name != "nt":
        raise OSError("Windows process management is only available on Windows")
    if not command_line or "\0" in command_line:
        raise ValueError("command line must be non-empty and contain no NUL")
    if current_directory is not None and "\0" in current_directory:
        raise ValueError("current directory contains a NUL character")
    import pythoncom

    pythoncom.CoInitialize()
    try:
        return _create_process_in_current_com_apartment(
            command_line, current_directory
        )
    finally:
        pythoncom.CoUninitialize()
