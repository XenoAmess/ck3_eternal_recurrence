"""Python-native Windows process creation helpers."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


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
