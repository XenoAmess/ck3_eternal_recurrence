"""Optional sanctioned screenshot mapper fallback for a live UIA-bound target."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import io
import json
from pathlib import Path
import subprocess
import sys
import time

from steam_versions_core import VersionError, sha256_file


def identity(node):
    element = node.element_info
    rectangle = node.rectangle()
    return {"name": element.name, "automation_id": element.automation_id,
            "control_type": element.control_type, "process_id": int(element.process_id),
            "rectangle": [rectangle.left, rectangle.top, rectangle.right, rectangle.bottom]}


def mapper_argv(mapper, source, receipt, width, height, x, y, hwnd):
    return [sys.executable, "-B", "-X", "utf8", str(mapper), "--source-image", str(source),
            "--preview-left", "0", "--preview-top", "0", "--preview-width", str(width),
            "--preview-height", str(height), "--observed-x", str(x), "--observed-y", str(y),
            "--click", "--expected-foreground-hwnd", str(hwnd), "--receipt", str(receipt)]


def mapped_click(node, root, *, mapper, receipt_dir, guard, emit, budget_check, reason):
    import pyautogui
    pyautogui.FAILSAFE = True
    mapper = Path(mapper).resolve()
    if not mapper.is_file():
        raise VersionError("explicit coordinate mapper path does not exist")
    guard()
    hwnd = int(root.element_info.handle)
    root_pid = int(root.element_info.process_id)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    if int(user32.GetForegroundWindow() or 0) != hwnd:
        try:
            root.element_info.element.SetFocus()
        except Exception:
            user32.SetForegroundWindow(hwnd)
        deadline = time.monotonic() + 1
        while int(user32.GetForegroundWindow() or 0) != hwnd and time.monotonic() < deadline:
            time.sleep(0.05)
    if int(user32.GetForegroundWindow() or 0) != hwnd:
        raise VersionError("CK3 Steam properties did not become foreground; no mapped input")
    before = identity(node)
    if before["process_id"] != root_pid or not node.is_enabled() or not node.is_visible():
        raise VersionError("mapped target no longer belongs to visible enabled CK3 Steam UI")
    left, top, right, bottom = before["rectangle"]
    if right <= left or bottom <= top:
        raise VersionError("mapped UIA target has no visible bounding rectangle")
    screenshot = pyautogui.screenshot()
    width, height = screenshot.size
    desktop_size = tuple(pyautogui.size())
    if (width, height) != desktop_size:
        raise VersionError("raw screenshot and current desktop dimensions differ")
    x, y = (left + right) / 2, (top + bottom) / 2
    if not (0 <= x < width and 0 <= y < height):
        raise VersionError("UIA control center is outside the current raw desktop image")
    if identity(node) != before or int(user32.GetForegroundWindow() or 0) != hwnd:
        raise VersionError("UIA target or foreground changed while capturing; no mapped input")
    encoded = io.BytesIO()
    screenshot.save(encoded, format="PNG")
    raw = encoded.getvalue()
    # Source and after screenshots are ordinary bounded runtime evidence,
    # counted in the same attempt, not hidden outside its declared budget.
    budget_check(5 * len(raw) + 131072)
    parent = Path(receipt_dir)
    index = 1
    while (parent / f"mapped-{index:03d}").exists():
        index += 1
    directory = parent / f"mapped-{index:03d}"
    directory.mkdir()
    source, receipt = directory / "source.png", directory / "after.png"
    with source.open("xb") as stream:
        stream.write(raw)
    arguments = mapper_argv(mapper, source, receipt, width, height, x, y, hwnd)
    emit("mapped_fallback_prepared", reason=reason, target=before, root_hwnd=hwnd,
         raw_image_dimensions=[width, height], current_desktop_dimensions=list(desktop_size),
         preview_content_rectangle={"left": 0, "top": 0, "width": width, "height": height},
         mapper={"path": str(mapper), "sha256": sha256_file(mapper)},
         source={"path": str(source), "sha256": sha256_file(source)}, argv=arguments)
    guard()
    if identity(node) != before or int(user32.GetForegroundWindow() or 0) != hwnd:
        raise VersionError("UIA target changed before mapper invocation; no mapped input")
    result = subprocess.run(arguments, capture_output=True, timeout=30)
    record = {"argv": arguments, "exit_code": result.returncode,
              "stdout": result.stdout.decode("utf-8", errors="replace"),
              "stderr": result.stderr.decode("utf-8", errors="replace")}
    with (directory / "mapper-result.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    emit("mapped_fallback_returned", exit_code=result.returncode, receipt_dir=str(directory),
         actual_ui_readback_still_required=True)
    if result.returncode:
        raise VersionError("mapped input/readback incomplete; inspect saved mapper result before retrying")
