"""Narrow Windows UI Automation helpers used by native acceptance recovery."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
from typing import Any


class WindowsUiaError(RuntimeError):
    """Raised when a semantic UI Automation contract cannot be proven."""


def _load_automation() -> tuple[Any, Any]:
    if os.name != "nt":
        raise WindowsUiaError("Windows UI Automation requires Windows")
    try:
        import comtypes.client

        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen import UIAutomationClient
    except (ImportError, OSError) as error:
        raise WindowsUiaError(
            "Python UI Automation dependency is unavailable; install tools requirements"
        ) from error
    automation = comtypes.client.CreateObject(
        UIAutomationClient.CUIAutomation,
        interface=UIAutomationClient.IUIAutomation,
    )
    return automation, UIAutomationClient


def _window_process_id(hwnd: int) -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    pid = wintypes.DWORD()
    if not user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid)):
        raise WindowsUiaError("could not resolve the foreground window process")
    return int(pid.value)


def _process_image_path(pid: int) -> Path:
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
        raise WindowsUiaError(f"could not inspect notification process {pid}")
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(
            handle, 0, buffer, ctypes.byref(size)
        ):
            raise WindowsUiaError(f"could not resolve notification process {pid}")
        return Path(buffer.value)
    finally:
        kernel32.CloseHandle(handle)


def _is_exact_shell_experience_host(path: Path) -> bool:
    parts = tuple(part.casefold() for part in path.parts)
    return (
        len(parts) >= 4
        and parts[-1] == "shellexperiencehost.exe"
        and parts[-2].startswith("shellexperiencehost_")
        and parts[-3] == "systemapps"
        and parts[0].rstrip("\\/") == "c:"
        and parts[1] == "windows"
    )


def _elements(array: Any) -> list[Any]:
    return [array.GetElement(index) for index in range(int(array.Length))]


def dismiss_exact_notification_toast(
    hwnd: int,
    *,
    sender_name: str,
    dismiss_name: str,
) -> dict[str, object]:
    """Invoke one allowlisted notification dismiss control through native UIA.

    The caller must separately attest the foreground title and window class.
    This function binds that HWND to the exact Windows notification host image,
    then requires unique sender and dismiss controls before invoking anything.
    """

    pid = _window_process_id(hwnd)
    image = _process_image_path(pid)
    if not _is_exact_shell_experience_host(image):
        raise WindowsUiaError(
            f"foreground is not the exact notification host: {image}"
        )
    automation, module = _load_automation()
    root = automation.ElementFromHandle(wintypes.HWND(hwnd))
    if int(root.CurrentProcessId) != pid:
        raise WindowsUiaError("UIA root process differs from the foreground HWND")
    descendants = _elements(root.FindAll(4, automation.CreateTrueCondition()))
    senders = [
        element
        for element in descendants
        if str(element.CurrentAutomationId) == "SenderName"
    ]
    dismiss_buttons = [
        element
        for element in descendants
        if str(element.CurrentAutomationId) == "DismissButton"
    ]
    if len(senders) != 1 or str(senders[0].CurrentName) != sender_name:
        raise WindowsUiaError("foreground notification sender is not allowlisted")
    if (
        len(dismiss_buttons) != 1
        or str(dismiss_buttons[0].CurrentName) != dismiss_name
        or not bool(dismiss_buttons[0].CurrentIsEnabled)
    ):
        raise WindowsUiaError("foreground notification dismiss control differs")
    try:
        invoke = dismiss_buttons[0].GetCurrentPattern(10000).QueryInterface(
            module.IUIAutomationInvokePattern
        )
    except BaseException as error:
        raise WindowsUiaError(
            "foreground notification dismiss control lacks InvokePattern"
        ) from error
    invoke.Invoke()
    return {
        "dismissed": True,
        "sender": sender_name,
        "control": "DismissButton",
        "pid": pid,
        "image": str(image),
    }
