"""Typed subprocess wrapper for the PowerShell PDX Launcher UIA bridge."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_CONTROL_TYPES = frozenset({"Hyperlink", "Button", "ComboBox", "ListItem", "Edit", "RadioButton"})
_SCRIPT = Path(__file__).with_name("uia_bridge.ps1")


class UiaBridgeError(RuntimeError):
    """The UIA bridge could not execute or did not return exact JSON."""


def keys(hwnd: int, automation_id: str, sequence: str) -> dict[str, Any]:
    if not automation_id.strip():
        raise UiaBridgeError("Navigation requires an exact AutomationId")
    return _run_bridge("keys", hwnd=_validate_hwnd(hwnd, allow_zero=False), automation_id=automation_id, keys=sequence)


def inspect(hwnd: int = 0) -> dict[str, Any]:
    """List top-level windows (0) or the complete UIA tree for one HWND."""

    return _run_bridge("inspect", hwnd=_validate_hwnd(hwnd))


def invoke(
    hwnd: int,
    name: str,
    control_type: str,
    automation_id: str = "",
) -> dict[str, Any]:
    """Invoke one semantic UIA control; no coordinate fallback is used."""

    hwnd = _validate_hwnd(hwnd, allow_zero=False)
    if not name.strip() and not automation_id.strip():
        raise UiaBridgeError("UIA invoke requires an accessible Name or AutomationId")
    control_type = _validate_control_type(control_type)
    return _run_bridge(
        "invoke",
        hwnd=hwnd,
        name=name,
        control_type=control_type,
        automation_id=automation_id,
    )


def set_text(hwnd: int, automation_id: str, text: str) -> dict[str, Any]:
    """Set an Edit control using an ephemeral UTF-8 file for exact text bytes."""

    hwnd = _validate_hwnd(hwnd, allow_zero=False)
    temporary_path: Path | None = None
    try:
        handle, raw_path = tempfile.mkstemp(prefix="ck3-workshop-uia-", suffix=".utf8.txt")
        temporary_path = Path(raw_path)
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        return _run_bridge(
            "set_text",
            hwnd=hwnd,
            automation_id=automation_id,
            control_type="Edit",
            text_file=temporary_path,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_hwnd(hwnd: int, *, allow_zero: bool = True) -> int:
    if isinstance(hwnd, bool):
        raise UiaBridgeError("HWND must be an integer")
    try:
        value = int(hwnd)
    except (TypeError, ValueError) as error:
        raise UiaBridgeError("HWND must be an integer") from error
    minimum = 0 if allow_zero else 1
    if value < minimum:
        raise UiaBridgeError(f"HWND must be >= {minimum}")
    return value


def _validate_control_type(control_type: str) -> str:
    if control_type not in _CONTROL_TYPES:
        allowed = ", ".join(sorted(_CONTROL_TYPES))
        raise UiaBridgeError(f"unsupported ControlType {control_type!r}; expected one of {allowed}")
    return control_type


def _run_bridge(
    operation: str,
    *,
    hwnd: int,
    name: str = "",
    control_type: str = "",
    automation_id: str = "",
    text_file: Path | None = None,
    timeout: float = 30.0,
    keys: str = "",
) -> dict[str, Any]:
    if not _SCRIPT.is_file():
        raise UiaBridgeError(f"UIA bridge script is missing: {_SCRIPT}")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if powershell is None:
        raise UiaBridgeError("Windows PowerShell was not found")
    arguments = [
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(_SCRIPT),
        "-Operation",
        operation,
        "-Hwnd",
        str(hwnd),
    ]
    if name:
        arguments.extend(("-Name", name))
    if control_type:
        arguments.extend(("-ControlType", control_type))
    if automation_id:
        arguments.extend(("-AutomationId", automation_id))
    if text_file is not None:
        arguments.extend(("-TextFile", str(text_file)))
    if keys:
        arguments.extend(("-Keys", keys))
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        completed = subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            creationflags=creation_flags,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise UiaBridgeError(f"UIA bridge execution failed: {error}") from error
    stdout = completed.stdout.decode("utf-8-sig", errors="strict").strip()
    stderr = completed.stderr.decode("utf-8-sig", errors="replace").strip()
    if completed.returncode != 0:
        detail = stderr or stdout or "no diagnostic output"
        raise UiaBridgeError(
            f"UIA bridge returned exit code {completed.returncode}: {detail[:2000]}"
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise UiaBridgeError("UIA bridge stdout was not one exact JSON value") from error
    if not isinstance(payload, dict):
        raise UiaBridgeError("UIA bridge must return a JSON object")
    return payload
