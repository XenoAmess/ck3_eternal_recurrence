#!/usr/bin/env python3
"""No-launch desktop eligibility check for the frozen generic war-bound live.

This verifier never prepares a profile or invokes the runner.  It binds a
fresh successful ``--verify-only`` report back to the frozen runner/manifest,
proves the shared launcher inherits the caller's desktop, and reports whether
the current caller is on Windows' normal ``Default`` desktop with an empty CK3
inventory.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _desktop_name() -> str:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user32.GetThreadDesktop.restype = wintypes.HANDLE
    user32.GetUserObjectInformationW.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetUserObjectInformationW.restype = wintypes.BOOL
    desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
    needed = wintypes.DWORD()
    user32.GetUserObjectInformationW(desktop, 2, None, 0, ctypes.byref(needed))
    if needed.value == 0:
        raise OSError(ctypes.get_last_error(), "desktop name size unavailable")
    buffer = ctypes.create_unicode_buffer((needed.value // 2) + 1)
    if not user32.GetUserObjectInformationW(
        desktop, 2, buffer, ctypes.sizeof(buffer), ctypes.byref(needed)
    ):
        raise OSError(ctypes.get_last_error(), "desktop name unavailable")
    return buffer.value


def _process_rows() -> list[dict[str, object]]:
    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    names = {"ck3.exe", "xar_ck3_bridge_injector.exe"}
    rows: list[dict[str, object]] = []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot in (None, wintypes.HANDLE(-1).value):
        raise OSError(ctypes.get_last_error(), "process snapshot unavailable")
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        available = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while available:
            name = entry.szExeFile
            if name.casefold() in names:
                rows.append({"pid": int(entry.th32ProcessID), "name": name})
            available = bool(
                kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    return sorted(rows, key=lambda row: (str(row["name"]), int(row["pid"])))


def audit(
    *,
    base_verify_report: Path,
    runner: Path,
    manifest: Path,
    runtime: Path,
    desktop_name: str | None = None,
    process_rows: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    base = json.loads(base_verify_report.read_text(encoding="utf-8"))
    identities = _mapping(base.get("identities"))
    checks_value = base.get("checks")
    base_checks = checks_value if isinstance(checks_value, dict) else {}
    runner_text = runner.read_text(encoding="utf-8")
    runtime_text = runtime.read_text(encoding="utf-8")
    observed_desktop = desktop_name if desktop_name is not None else _desktop_name()
    inventory = process_rows if process_rows is not None else _process_rows()
    static_checks = {
        "base_verify_ready": base.get("ok") is True
        and base.get("status") == "ready-to-run",
        "base_verify_no_launch": base.get("ck3_started") is False
        and base.get("profile_prepared") is False,
        "base_checks_all_true": bool(base_checks)
        and all(value is True for value in base_checks.values()),
        "runner_identity": identities.get("runner_sha256") == _sha256(runner),
        "manifest_identity": identities.get("manifest_sha256") == _sha256(manifest),
        "attempt_still_absent": not Path(str(base.get("attempt_dir", ""))).exists(),
        "runner_delegates_managed_launch": "terms_live._run(" in runner_text,
        "runner_locks_two_queries": runner_text.count(
            "query_war_termination_terms_step(war_id)"
        ) >= 2 and '"no_mutation_commands"' in runner_text,
        "launcher_uses_suspended_createprocess":
            "creation_flags = win32process.CREATE_SUSPENDED" in runtime_text
            and "win32process.CreateProcess(" in runtime_text,
        "launcher_inherits_calling_desktop":
            "startup = win32process.STARTUPINFO()" in runtime_text
            and "startup.lpDesktop" not in runtime_text,
    }
    static_ready = all(static_checks.values())
    desktop_eligible = observed_desktop.casefold() == "default"
    inventory_empty = inventory == []
    current_ready = static_ready and desktop_eligible and inventory_empty
    if current_ready:
        status = "ready-to-run-on-normal-desktop"
    elif static_ready and not desktop_eligible:
        status = "candidate-ready-current-desktop-ineligible"
    else:
        status = "red"
    return {
        "format_version": 1,
        "kind": "raiktor_generic_war_bound_normal_desktop_no_launch_preflight",
        "status": status,
        "ok": current_ready,
        "launch_attempted": False,
        "profile_prepared": False,
        "normal_desktop_direct_execution_supported": static_ready,
        "current_desktop": observed_desktop,
        "current_desktop_eligible": desktop_eligible,
        "process_inventory": inventory,
        "process_inventory_empty": inventory_empty,
        "static_checks": static_checks,
        "frozen_identity": {
            "runner_sha256": _sha256(runner),
            "manifest_sha256": _sha256(manifest),
            "base_verify_sha256": _sha256(base_verify_report),
        },
        "execution_boundary": {
            "required_caller_desktop": "Default",
            "desktop_selection": "inherited-from-caller",
            "queries": 2,
            "mutation_commands": [],
            "same_frozen_attempt_must_remain_absent": True,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-verify-report", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = audit(
        base_verify_report=args.base_verify_report.resolve(),
        runner=args.runner.resolve(),
        manifest=args.manifest.resolve(),
        runtime=args.runtime.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, args.output)
    print(json.dumps({
        "status": report["status"],
        "ok": report["ok"],
        "normal_desktop_direct_execution_supported": report[
            "normal_desktop_direct_execution_supported"
        ],
        "current_desktop": report["current_desktop"],
        "launch_attempted": False,
        "output": str(args.output.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0 if report["normal_desktop_direct_execution_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
