"""Capture a provably new Steam desktop frame before a managed CK3 launch.

This tool proves that the desktop capture responded to a reversible movement
of the live Steam window. It does not infer Steam's online/offline status from
pixels; the operator must inspect the resulting image separately.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import psutil
import pyautogui
from PIL import Image, ImageChops
import win32gui
import win32process


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _identity(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _steam_windows() -> list[tuple[int, int]]:
    """Enumerate Steam-owned main windows; callers reject ambiguous results.

    Steam can host its main UI in either the native steam.exe SDL window or
    the steamwebhelper.exe CEF window. The exact title and live process owner
    remain required for both hosts.
    """
    found: list[tuple[int, int]] = []

    def visit(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd) or win32gui.GetWindowText(hwnd) != "Steam":
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            if psutil.Process(pid).name().lower() in {"steam.exe", "steamwebhelper.exe"}:
                found.append((hwnd, pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return

    win32gui.EnumWindows(visit, None)
    return found


def _shift_for_rect(rect: tuple[int, int, int, int], screen_width: int) -> int:
    left, _, right, _ = rect
    if right + 20 <= screen_width:
        return 20
    if left - 20 >= 0:
        return -20
    raise RuntimeError("Steam window has no 20-pixel horizontal movement room")


def _unchanged_clock_region(
    reference_path: Path, moved: Image.Image, rect: tuple[int, int, int, int]
) -> dict[str, object]:
    """Reject a moving window composited over an older, frozen desktop clock.

    The caller must select a visibly updating clock region from a previously
    reviewed screenshot. This is a fail-closed freshness check, not OCR or an
    inference about Steam's offline mode.
    """
    reference = Image.open(reference_path).convert("RGB")
    if reference.size != moved.size:
        raise ValueError("clock reference and current desktop dimensions differ")
    left, top, right, bottom = rect
    if not (0 <= left < right <= moved.width and 0 <= top < bottom <= moved.height):
        raise ValueError("clock region is outside the captured desktop")
    age_seconds = time.time() - reference_path.stat().st_mtime
    if age_seconds < 120:
        raise ValueError("clock reference must be at least two minutes old")
    old_clock = reference.crop(rect)
    new_clock = moved.convert("RGB").crop(rect)
    # Steam window movement can recolor the taskbar background while the
    # composited clock glyphs stay frozen. Compare their bright foreground.
    old_glyphs = old_clock.convert("L").point(lambda value: 255 if value >= 160 else 0)
    new_glyphs = new_clock.convert("L").point(lambda value: 255 if value >= 160 else 0)
    if old_glyphs.getbbox() is None:
        raise ValueError("clock reference region has no bright clock glyphs")
    return {
        "reference_path": str(reference_path.resolve()),
        "reference_sha256": _sha256(reference_path),
        "reference_age_seconds": round(age_seconds, 1),
        "clock_rect": list(rect),
        "clock_pixels_unchanged": ImageChops.difference(old_glyphs, new_glyphs).getbbox() is None,
        "clock_foreground_threshold": 160,
    }


def capture(
    output_dir: Path, *, clock_reference: Path | None = None,
    clock_rect: tuple[int, int, int, int] | None = None,
) -> dict[str, object]:
    if not output_dir.is_dir():
        raise ValueError("output directory must exist")
    before_path = output_dir / "steam-before.png"
    moved_path = output_dir / "steam-moved.png"
    receipt_path = output_dir / "steam-frame-freshness.json"
    if any(path.exists() for path in (before_path, moved_path, receipt_path)):
        raise FileExistsError("capture files already exist; use a new attempt directory")
    if any(process.info["name"] and process.info["name"].lower() == "ck3.exe"
           for process in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 must not be running during Steam preflight")
    windows = _steam_windows()
    if len(windows) != 1:
        raise RuntimeError(f"expected one live Steam window, found {len(windows)}")
    hwnd, pid = windows[0]
    if win32gui.GetForegroundWindow() != hwnd:
        raise RuntimeError("Steam must be the foreground window for this capture")
    original = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = original
    screen = pyautogui.size()
    if not (0 <= left < right <= screen.width and
            0 <= top < bottom <= screen.height):
        raise RuntimeError("Steam window is not wholly inside the desktop")
    shift = _shift_for_rect(original, screen.width)
    moved_rect = (left + shift, top, right + shift, bottom)
    before = pyautogui.screenshot()
    if before.size != (screen.width, screen.height):
        raise RuntimeError("desktop screenshot dimensions disagree with desktop")
    before.save(before_path)
    try:
        win32gui.MoveWindow(hwnd, moved_rect[0], top,
                            right - left, bottom - top, True)
        time.sleep(1)
        observed_moved = win32gui.GetWindowRect(hwnd)
        if observed_moved != moved_rect:
            raise RuntimeError("Steam window did not reach its expected position")
        moved = pyautogui.screenshot()
        if moved.size != before.size:
            raise RuntimeError("desktop dimensions changed during capture")
        moved.save(moved_path)
    finally:
        win32gui.MoveWindow(hwnd, left, top, right - left, bottom - top, True)
    restored = win32gui.GetWindowRect(hwnd)
    if restored != original:
        raise RuntimeError("Steam window could not be restored")
    difference = ImageChops.difference(before.convert("RGB"), moved.convert("RGB"))
    bbox = difference.getbbox()
    edge_left = min(left, left + shift)
    edge_right = max(left, left + shift)
    edge_change = difference.crop((edge_left, top, edge_right, bottom)).getbbox()
    if bbox is None or edge_change is None or _sha256(before_path) == _sha256(moved_path):
        raise RuntimeError("desktop capture did not respond to live Steam movement")
    if (clock_reference is None) != (clock_rect is None):
        raise ValueError("clock reference and rectangle must be supplied together")
    clock_check = None
    if clock_reference is not None and clock_rect is not None:
        cl, ct, cr, cb = clock_rect
        if (cl < moved_rect[2] and cr > moved_rect[0]
                and ct < moved_rect[3] and cb > moved_rect[1]):
            raise ValueError("clock region overlaps the moved Steam window")
        clock_check = _unchanged_clock_region(clock_reference, moved, clock_rect)
        if clock_check["clock_pixels_unchanged"]:
            with (output_dir / "steam-frame-stale.json").open(
                "x", encoding="utf-8", newline="\n"
            ) as stream:
                json.dump({"schema": "ck3.steam_frozen_clock_frame.v1",
                           "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                           "before_sha256": _sha256(before_path),
                           "moved_sha256": _sha256(moved_path),
                           "clock_check": clock_check}, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            raise RuntimeError("desktop capture did not respond to live Steam movement")
    receipt = {
        "schema": "ck3.steam_fresh_desktop_frame.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "steam_hwnd": hwnd,
        "steam_pid": pid,
        "desktop_size": [screen.width, screen.height],
        "before_rect": list(original),
        "moved_rect": list(moved_rect),
        "restored_rect": list(restored),
        "before_path": str(before_path),
        "before_sha256": _sha256(before_path),
        "moved_path": str(moved_path),
        "moved_sha256": _sha256(moved_path),
        "moved_identity": _identity(moved_path),
        "pixel_difference_bbox": list(bbox),
        "moving_edge_changed": True,
        "clock_check": clock_check,
        "offline_status_observed": None,
    }
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(capture(args.output_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
