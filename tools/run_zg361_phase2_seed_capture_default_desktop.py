#!/usr/bin/env python3
"""Relay the exact phase-two seed runner onto the active Default desktop.

The normal Codex execution host is attached to an isolated desktop.  CK3's
authorized legal-consent handler uses Win32 desktop capture, so the runner must
itself execute on ``WinSta0\\Default``.  This wrapper only changes that process
desktop.  It does not classify UI, click anything, or alter the seed runner's
legal/commerce policy.

The default mode is a strict no-launch preflight.  ``--execute`` is deliberately
required to create the child process.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence


TARGET_DESKTOP = r"WinSta0\Default"
RUNNER_RELATIVE_PATH = Path("tools/run_zg361_phase2_seed_capture.py")
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def resolve_inputs(
    python_path: Path, source_root: Path, runner_arguments: Sequence[str]
) -> tuple[Path, Path, tuple[str, ...]]:
    python_path = python_path.resolve()
    source_root = source_root.resolve()
    runner = (source_root / RUNNER_RELATIVE_PATH).resolve()
    if not python_path.is_file():
        raise ValueError(f"Python executable is missing: {python_path}")
    if not runner.is_file():
        raise ValueError(f"phase-two seed runner is missing: {runner}")
    if not runner_arguments:
        raise ValueError("phase-two seed runner arguments are required after --")
    arguments = tuple(runner_arguments)
    if arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        raise ValueError("phase-two seed runner arguments are required after --")
    return python_path, runner, arguments


def preflight_payload(
    python_path: Path,
    source_root: Path,
    runner_arguments: Sequence[str],
    stdout_log: Path,
    stderr_log: Path,
) -> dict[str, object]:
    python_path, runner, arguments = resolve_inputs(
        python_path, source_root, runner_arguments
    )
    command = (str(python_path), str(runner), *arguments)
    return {
        "schema_version": 1,
        "result": "READY_TO_RUN",
        "mode": "no-launch-preflight",
        "target_desktop": TARGET_DESKTOP,
        "child_process_started": False,
        "ck3_launch_attempted": False,
        "python": {
            "path": str(python_path),
            "sha256": sha256(python_path),
        },
        "runner": {
            "path": str(runner),
            "sha256": sha256(runner),
        },
        "working_directory": str(source_root.resolve()),
        "stdout_log": str(stdout_log.resolve()),
        "stderr_log": str(stderr_log.resolve()),
        "command": list(command),
        "desktop_contract": (
            "CreateProcessW STARTUPINFO.lpDesktop is exactly " + TARGET_DESKTOP
        ),
        "legal_commerce_contract": (
            "unchanged: the child is the exact run_zg361_phase2_seed_capture.py "
            "runner and retains its authorized CK3 legal-consent classifier; "
            "external real-money purchase/payment/order/checkout/store actions "
            "remain unauthorized"
        ),
    }


def _handle_from_file(stream: object) -> int:
    import msvcrt  # pylint: disable=import-outside-toplevel

    return int(msvcrt.get_osfhandle(stream.fileno()))  # type: ignore[attr-defined]


def execute_on_default_desktop(
    command: Sequence[str],
    working_directory: Path,
    stdout_log: Path,
    stderr_log: Path,
) -> tuple[int, int]:
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("runner_arguments", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = preflight_payload(
            args.python,
            args.source_root,
            args.runner_arguments,
            args.stdout_log,
            args.stderr_log,
        )
        if args.execute:
            command = tuple(str(value) for value in payload["command"])
            pid, exit_code = execute_on_default_desktop(
                command,
                args.source_root,
                args.stdout_log,
                args.stderr_log,
            )
            payload.update(
                {
                    "result": "GREEN" if exit_code == 0 else "RED",
                    "mode": "execute",
                    "child_process_started": True,
                    "ck3_launch_attempted": True,
                    "child_pid": pid,
                    "child_exit_code": exit_code,
                }
            )
        write_json(args.result, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        return 0 if payload["result"] in {"READY_TO_RUN", "GREEN"} else 2
    except BaseException as error:
        failure = {
            "schema_version": 1,
            "result": "RED",
            "mode": "execute" if args.execute else "no-launch-preflight",
            "target_desktop": TARGET_DESKTOP,
            "child_process_started": False,
            "ck3_launch_attempted": False,
            "error": f"{type(error).__name__}: {error}",
        }
        write_json(args.result, failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
