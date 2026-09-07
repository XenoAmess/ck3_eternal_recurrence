#!/usr/bin/env python3
"""Shared Win32 process primitive for ``WinSta0\\Default`` relays."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
from typing import Sequence


TARGET_DESKTOP = r"WinSta0\Default"
CREATE_NO_WINDOW = 0x08000000
CREATE_UNICODE_ENVIRONMENT = 0x00000400
STARTF_USESHOWWINDOW = 0x00000001
STARTF_USESTDHANDLES = 0x00000100
SW_HIDE = 0
INFINITE = 0xFFFFFFFF
WAIT_FAILED = 0xFFFFFFFF


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


def _handle_from_file(stream: object) -> int:
    import msvcrt  # pylint: disable=import-outside-toplevel

    return int(msvcrt.get_osfhandle(stream.fileno()))  # type: ignore[attr-defined]


def execute_on_default_desktop(
    command: Sequence[str],
    working_directory: Path,
    stdout_log: Path,
    stderr_log: Path,
) -> tuple[int, int]:
    """Run one command on the interactive Default desktop and wait for it."""

    if os.name != "nt":
        raise RuntimeError("Default-desktop relay is supported only on Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_process = kernel32.CreateProcessW
    create_process.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW),
        ctypes.POINTER(PROCESS_INFORMATION),
    ]
    create_process.restype = wintypes.BOOL
    wait_for_single_object = kernel32.WaitForSingleObject
    wait_for_single_object.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    wait_for_single_object.restype = wintypes.DWORD
    get_exit_code = kernel32.GetExitCodeProcess
    get_exit_code.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    get_exit_code.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    with (
        open(os.devnull, "rb", buffering=0) as stdin_stream,
        stdout_log.open("ab", buffering=0) as stdout_stream,
        stderr_log.open("ab", buffering=0) as stderr_stream,
    ):
        handles = tuple(
            _handle_from_file(stream)
            for stream in (stdin_stream, stdout_stream, stderr_stream)
        )
        for handle in handles:
            os.set_handle_inheritable(handle, True)
        startup = STARTUPINFOW()
        startup.cb = ctypes.sizeof(startup)
        startup.lpDesktop = TARGET_DESKTOP
        startup.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES
        startup.wShowWindow = SW_HIDE
        startup.hStdInput = handles[0]
        startup.hStdOutput = handles[1]
        startup.hStdError = handles[2]
        process = PROCESS_INFORMATION()
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        try:
            created = create_process(
                None,
                command_line,
                None,
                None,
                True,
                CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
                None,
                str(working_directory.resolve()),
                ctypes.byref(startup),
                ctypes.byref(process),
            )
        finally:
            for handle in handles:
                os.set_handle_inheritable(handle, False)
        if not created:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            waited = wait_for_single_object(process.hProcess, INFINITE)
            if waited == WAIT_FAILED:
                raise ctypes.WinError(ctypes.get_last_error())
            exit_code = wintypes.DWORD()
            if not get_exit_code(process.hProcess, ctypes.byref(exit_code)):
                raise ctypes.WinError(ctypes.get_last_error())
            return int(process.dwProcessId), int(exit_code.value)
        finally:
            close_handle(process.hThread)
            close_handle(process.hProcess)
