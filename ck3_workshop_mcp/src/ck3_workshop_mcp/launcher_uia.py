"""Typed Python bridge for semantic PDX Launcher UI Automation."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

_CONTROL_TYPES = frozenset({"Hyperlink", "Button", "ComboBox", "ListItem", "Edit", "RadioButton"})
KEY_SEQUENCE_PATTERN = re.compile(r"(?:\{(?:ENTER|HOME|END|UP|DOWN|TAB|ESC)\})+\Z")
_KEY_TOKENS = re.compile(r"\{(ENTER|HOME|END|UP|DOWN|TAB|ESC)\}")
_CONTROL_TYPE_IDS = {
    "Button": 50000,
    "ComboBox": 50003,
    "Edit": 50004,
    "Hyperlink": 50005,
    "ListItem": 50007,
    "RadioButton": 50013,
}
_CONTROL_TYPE_NAMES = {value: key for key, value in _CONTROL_TYPE_IDS.items()}


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
    try:
        return _execute_uia(
            operation,
            hwnd=hwnd,
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            text_file=text_file,
            timeout=timeout,
            keys=keys,
        )
    except UiaBridgeError:
        raise
    except BaseException as error:
        raise UiaBridgeError(f"UIA bridge execution failed: {error}") from error


def _load_automation() -> tuple[Any, Any]:
    if os.name != "nt":
        raise UiaBridgeError("PDX Launcher UI Automation requires Windows")
    try:
        import comtypes.client

        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen import UIAutomationClient
    except (ImportError, OSError) as error:
        raise UiaBridgeError(
            "Python UI Automation dependency is unavailable; install the package with Windows UIA dependencies"
        ) from error
    automation = comtypes.client.CreateObject(
        UIAutomationClient.CUIAutomation,
        interface=UIAutomationClient.IUIAutomation,
    )
    return automation, UIAutomationClient


def _elements(array: Any) -> list[Any]:
    return [array.GetElement(index) for index in range(int(array.Length))]


def _pattern(element: Any, module: Any, pattern_id: int, interface: str) -> Any | None:
    try:
        value = element.GetCurrentPattern(pattern_id)
        return value.QueryInterface(getattr(module, interface))
    except BaseException:
        return None


def _describe(element: Any, module: Any) -> dict[str, Any]:
    patterns: list[str] = []
    invoke_pattern = _pattern(element, module, 10000, "IUIAutomationInvokePattern")
    value_pattern = _pattern(element, module, 10002, "IUIAutomationValuePattern")
    expand_pattern = _pattern(element, module, 10005, "IUIAutomationExpandCollapsePattern")
    selection_pattern = _pattern(element, module, 10010, "IUIAutomationSelectionItemPattern")
    if invoke_pattern is not None:
        patterns.append("InvokePatternIdentifiers.Pattern")
    if value_pattern is not None:
        patterns.append("ValuePatternIdentifiers.Pattern")
    if expand_pattern is not None:
        patterns.append("ExpandCollapsePatternIdentifiers.Pattern")
    if selection_pattern is not None:
        patterns.append("SelectionItemPatternIdentifiers.Pattern")
    rectangle = element.CurrentBoundingRectangle
    value = None
    if value_pattern is not None and not bool(element.CurrentIsPassword):
        value = value_pattern.CurrentValue
    return {
        "name": str(element.CurrentName),
        "type": _CONTROL_TYPE_NAMES.get(
            int(element.CurrentControlType), str(element.CurrentControlType)
        ),
        "automation_id": str(element.CurrentAutomationId),
        "pid": int(element.CurrentProcessId),
        "hwnd": int(element.CurrentNativeWindowHandle),
        "enabled": bool(element.CurrentIsEnabled),
        "offscreen": bool(element.CurrentIsOffscreen),
        "rect": (
            f"{float(rectangle.left)},{float(rectangle.top)},"
            f"{float(rectangle.right)},{float(rectangle.bottom)}"
        ),
        "patterns": patterns,
        "value": value,
        "selected": (
            bool(selection_pattern.CurrentIsSelected)
            if selection_pattern is not None
            else None
        ),
    }


def _process_image_name(pid: int) -> str:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise UiaBridgeError(f"could not inspect target process {pid}")
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise UiaBridgeError(f"could not resolve target process {pid}")
        return Path(buffer.value).name
    finally:
        kernel32.CloseHandle(handle)


_ULONG_PTR = ctypes.c_size_t


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


_VIRTUAL_KEYS = {
    "ENTER": 0x0D,
    "HOME": 0x24,
    "END": 0x23,
    "UP": 0x26,
    "DOWN": 0x28,
    "TAB": 0x09,
    "ESC": 0x1B,
}


def _send_virtual_keys(values: list[tuple[int, bool]]) -> None:
    inputs = (_INPUT * len(values))()
    for index, (virtual_key, key_up) in enumerate(values):
        inputs[index].type = 1
        inputs[index].ki = _KEYBDINPUT(
            virtual_key, 0, 0x0002 if key_up else 0, 0, 0
        )
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendInput.argtypes = [
        wintypes.UINT,
        ctypes.POINTER(_INPUT),
        ctypes.c_int,
    ]
    user32.SendInput.restype = wintypes.UINT
    sent = user32.SendInput(len(values), inputs, ctypes.sizeof(_INPUT))
    if int(sent) != len(values):
        raise UiaBridgeError("SendInput did not acknowledge the exact key sequence")


def _send_chord(*keys: int) -> None:
    _send_virtual_keys(
        [(key, False) for key in keys] + [(key, True) for key in reversed(keys)]
    )


def _set_clipboard_text(text: str) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    if not user32.OpenClipboard(None):
        raise UiaBridgeError("could not open the Windows clipboard")
    memory = None
    try:
        if not user32.EmptyClipboard():
            raise UiaBridgeError("could not clear the Windows clipboard")
        encoded = (text + "\0").encode("utf-16-le")
        memory = kernel32.GlobalAlloc(0x0002, len(encoded))
        if not memory:
            raise UiaBridgeError("could not allocate clipboard memory")
        address = kernel32.GlobalLock(memory)
        if not address:
            raise UiaBridgeError("could not lock clipboard memory")
        try:
            ctypes.memmove(address, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(memory)
        if not user32.SetClipboardData(13, memory):
            raise UiaBridgeError("could not publish Unicode clipboard text")
        memory = None
    finally:
        if memory:
            kernel32.GlobalFree(memory)
        user32.CloseClipboard()


def _prepare_foreground(hwnd: int) -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.LoadKeyboardLayoutW.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
    user32.LoadKeyboardLayoutW.restype = wintypes.HANDLE
    user32.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = wintypes.HANDLE
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow(wintypes.HWND(hwnd))
    english = user32.LoadKeyboardLayoutW("00000409", 1)
    user32.PostMessageW(wintypes.HWND(hwnd), 0x50, 0, english)
    time.sleep(0.15)
    pid = wintypes.DWORD()
    thread = user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    layout = int(user32.GetKeyboardLayout(thread)) & 0xFFFF
    if layout != 0x0409:
        raise UiaBridgeError("English keyboard layout was not confirmed")
    if int(user32.GetForegroundWindow()) != hwnd:
        raise UiaBridgeError("Foreground window was not confirmed")
    return layout


def _execute_uia(
    operation: str,
    *,
    hwnd: int,
    name: str,
    control_type: str,
    automation_id: str,
    text_file: Path | None,
    timeout: float,
    keys: str,
) -> dict[str, Any]:
    del timeout
    automation, module = _load_automation()
    true_condition = automation.CreateTrueCondition()
    if hwnd == 0:
        if operation != "inspect":
            raise UiaBridgeError("An exact window handle is required")
        windows = _elements(
            automation.GetRootElement().FindAll(2, true_condition)
        )
        return {
            "ok": True,
            "windows": [
                _describe(window, module)
                for window in windows
                if re.search(
                    r"Crusader Kings|Paradox|Steam", str(window.CurrentName)
                )
            ],
        }
    root = automation.ElementFromHandle(wintypes.HWND(hwnd))
    if _process_image_name(int(root.CurrentProcessId)).lower() != "paradox launcher.exe":
        raise UiaBridgeError("Target is not a Paradox Launcher window")
    all_elements = _elements(root.FindAll(4, true_condition))
    if operation == "inspect":
        return {
            "ok": True,
            "window": _describe(root, module),
            "controls": [_describe(element, module) for element in all_elements],
        }
    matches = [
        element
        for element in all_elements
        if (not name or str(element.CurrentName) == name)
        and (
            (not automation_id and operation != "set_text")
            or str(element.CurrentAutomationId) == automation_id
        )
        and (
            not control_type
            or int(element.CurrentControlType) == _CONTROL_TYPE_IDS[control_type]
        )
    ]
    if len(matches) != 1:
        raise UiaBridgeError(f"Expected one control, found {len(matches)}")
    target = matches[0]
    if not bool(target.CurrentIsEnabled):
        raise UiaBridgeError("Target control is disabled")
    if operation == "invoke":
        before = _describe(target, module)
        selection = _pattern(target, module, 10010, "IUIAutomationSelectionItemPattern")
        invoke_pattern = _pattern(target, module, 10000, "IUIAutomationInvokePattern")
        expand = _pattern(target, module, 10005, "IUIAutomationExpandCollapsePattern")
        if control_type != "ListItem":
            ctypes.windll.user32.SetForegroundWindow(wintypes.HWND(hwnd))
            target.SetFocus()
        if control_type == "ListItem" and selection is not None:
            selection.Select()
        elif invoke_pattern is not None:
            invoke_pattern.Invoke()
        elif expand is not None:
            expand.Expand()
        elif selection is not None:
            selection.Select()
        else:
            raise UiaBridgeError("Control has no semantic invocation pattern")
        time.sleep(0.6)
        return {"ok": True, "action": "invoke", "target": before}
    layout = _prepare_foreground(hwnd)
    target.SetFocus()
    if operation == "keys":
        if KEY_SEQUENCE_PATTERN.fullmatch(keys) is None:
            raise UiaBridgeError("Unsupported navigation key sequence")
        values: list[tuple[int, bool]] = []
        for token in _KEY_TOKENS.findall(keys):
            virtual_key = _VIRTUAL_KEYS[token]
            values.extend(((virtual_key, False), (virtual_key, True)))
        _send_virtual_keys(values)
        time.sleep(0.6)
        return {"ok": True, "action": "keys", "keys": keys, "langid": layout}
    if operation != "set_text" or text_file is None:
        raise UiaBridgeError(f"unsupported UIA operation: {operation}")
    text = text_file.resolve().read_bytes().decode("utf-8")
    value_pattern = _pattern(target, module, 10002, "IUIAutomationValuePattern")
    if value_pattern is None:
        raise UiaBridgeError("Target Edit control lacks ValuePattern")
    _set_clipboard_text(text)
    _send_chord(0x11, 0x41)
    _send_chord(0x11, 0x56)
    time.sleep(0.2)
    method = "clipboard"
    got = str(value_pattern.CurrentValue)
    if got.replace("\r\n", "\n") != text.replace("\r\n", "\n"):
        value_pattern.SetValue(text)
        method = "ValuePattern after clipboard mismatch"
        time.sleep(0.15)
        got = str(value_pattern.CurrentValue)
    if got.replace("\r\n", "\n") != text.replace("\r\n", "\n"):
        raise UiaBridgeError("Control text readback mismatch")
    return {
        "ok": True,
        "action": "set_text",
        "method": method,
        "langid": layout,
        "characters": len(got),
        "readback": got,
        "target": _describe(target, module),
    }
