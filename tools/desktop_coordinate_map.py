"""Map coordinates from a rendered image preview to the live desktop.

The caller must provide the exact rendered preview dimensions.  There are no
defaults because preview renderers may independently resize either axis.
Interactive actions additionally require a full-resolution desktop screenshot
and an after receipt screenshot. Pointer-only moves require an explicit reviewed
region and record pointer, focus and dimension readback without clicking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Mapping:
    preview_bounds: tuple[float, float, int, int]
    observed_point: tuple[float, float]
    source_image_size: tuple[int, int]
    live_screen_size: tuple[int, int]
    screen_point: tuple[int, int]


def map_point(
    *,
    preview_bounds: tuple[float, float, int, int],
    observed_point: tuple[float, float],
    target_size: tuple[int, int],
) -> tuple[int, int]:
    preview_left, preview_top, preview_width, preview_height = preview_bounds
    observed_x, observed_y = observed_point
    target_width, target_height = target_size

    if preview_width <= 0 or preview_height <= 0:
        raise ValueError("preview dimensions must both be positive")
    if target_width <= 0 or target_height <= 0:
        raise ValueError("target dimensions must both be positive")
    preview_x = observed_x - preview_left
    preview_y = observed_y - preview_top
    if not 0 <= preview_x < preview_width:
        raise ValueError("observed x is outside the supplied image-content bounds")
    if not 0 <= preview_y < preview_height:
        raise ValueError("observed y is outside the supplied image-content bounds")

    # Scale axes independently.  Never infer or require an aspect ratio.
    target_x = round(preview_x * target_width / preview_width)
    target_y = round(preview_y * target_height / preview_height)
    return (
        min(max(target_x, 0), target_width - 1),
        min(max(target_y, 0), target_height - 1),
    )


def validate_reviewed_region(
    mapping: Mapping,
    reviewed_bounds: tuple[float, float, int, int],
) -> None:
    """Keep both the observed point and rounded target in the reviewed region."""
    left, top, width, height = reviewed_bounds
    preview_left, preview_top, preview_width, preview_height = mapping.preview_bounds
    if not all(math.isfinite(value) for value in reviewed_bounds):
        raise ValueError("reviewed region geometry must be finite")
    if width <= 0 or height <= 0:
        raise ValueError("reviewed region dimensions must both be positive")
    if (
        left < preview_left or top < preview_top
        or left + width > preview_left + preview_width
        or top + height > preview_top + preview_height
    ):
        raise ValueError("reviewed region is outside the supplied image-content bounds")
    observed_x, observed_y = mapping.observed_point
    if not (left <= observed_x < left + width and top <= observed_y < top + height):
        raise ValueError("pointer target is outside the explicitly reviewed region")
    screen_x, screen_y = mapping.screen_point
    screen_width, screen_height = mapping.live_screen_size
    if not (0 <= screen_x < screen_width and 0 <= screen_y < screen_height):
        raise ValueError("mapped pointer target is outside the live screen")
    if not (
        (left - preview_left) * screen_width / preview_width
        <= screen_x < (left + width - preview_left) * screen_width / preview_width
        and (top - preview_top) * screen_height / preview_height
        <= screen_y < (top + height - preview_top) * screen_height / preview_height
    ):
        raise ValueError("rounded pointer target is outside the explicitly reviewed region")


def foreground_state() -> dict[str, object]:
    """Read the active window and keyboard focus; never activate a window."""
    if sys.platform != "win32":
        raise RuntimeError("pointer move focus readback requires Windows")
    import ctypes
    from ctypes import wintypes

    class GuiThreadInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GuiThreadInfo)]
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("foreground window is unavailable")
    pid = wintypes.DWORD()
    thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    info = GuiThreadInfo()
    info.cbSize = ctypes.sizeof(info)
    if not thread_id or not user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    title = ctypes.create_unicode_buffer(32768)
    user32.GetWindowTextW(hwnd, title, len(title))
    return {
        "foreground_hwnd": int(hwnd), "foreground_pid": pid.value,
        "foreground_thread_id": thread_id, "focus_hwnd": int(info.hwndFocus or 0),
        "title": title.value,
    }


def mouse_button_state() -> dict[str, bool]:
    """A move while a button is held would drag; read current button state."""
    if sys.platform != "win32":
        raise RuntimeError("pointer move button readback requires Windows")
    import ctypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    return {name: bool(user32.GetAsyncKeyState(vk) & 0x8000)
            for name, vk in (("left", 0x01), ("right", 0x02), ("middle", 0x04),
                             ("x1", 0x05), ("x2", 0x06))}


def move_pointer(
    *, mapping: Mapping, reviewed_bounds: tuple[float, float, int, int],
    source_image: Path, receipt_path: Path, desktop: object,
    expected_foreground_hwnd: int | None,
) -> dict[str, object]:
    """Perform one immediate move and preserve exact actual readback."""
    validate_reviewed_region(mapping, reviewed_bounds)
    sidecar = receipt_path.with_name(receipt_path.name + ".json")
    if receipt_path.exists() or sidecar.exists():
        raise ValueError("pointer receipt or sidecar already exists; use a new path")
    before_size = tuple(desktop.size())
    if before_size != mapping.live_screen_size:
        raise ValueError("live screen size changed before pointer move")
    before_focus = foreground_state()
    if expected_foreground_hwnd is not None and before_focus["foreground_hwnd"] != expected_foreground_hwnd:
        raise ValueError("foreground window does not match the expected HWND")
    before_buttons = mouse_button_state()
    if any(before_buttons.values()):
        raise ValueError("a mouse button is held; refusing a move that could drag")
    result = {
        **asdict(mapping), "action": "move", "status": "pending-readback",
        "reviewed_bounds": reviewed_bounds,
        "source_image": {"path": str(source_image.resolve()),
                         "sha256": hashlib.sha256(source_image.read_bytes()).hexdigest().upper()},
        "pointer_before": tuple(desktop.position()), "focus_before": before_focus,
        "mouse_buttons_before": before_buttons,
        "screen_size_before": before_size, "receipt_path": str(receipt_path.resolve()),
        "sidecar_path": str(sidecar.resolve()), "move_completed": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    try:
        # Immediate pointer relocation only; no click, button, drag or window activation.
        desktop.moveTo(*mapping.screen_point, duration=0)
        result["move_completed"] = True
        result["pointer_after"] = tuple(desktop.position())
        result["screen_size_after"] = tuple(desktop.size())
        result["focus_after"] = foreground_state()
        result["mouse_buttons_after"] = mouse_button_state()
        receipt = desktop.screenshot(str(receipt_path))
        result["receipt_image_size"] = receipt.size
        result["receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest().upper()
        if result["pointer_after"] != mapping.screen_point:
            failures.append("pointer_readback_mismatch")
        if result["screen_size_after"] != mapping.live_screen_size:
            failures.append("screen_size_changed")
        if receipt.size != mapping.live_screen_size:
            failures.append("receipt_image_size_changed")
        if any(result["focus_after"][key] != before_focus[key]
               for key in ("foreground_hwnd", "foreground_pid", "focus_hwnd")):
            failures.append("focus_changed")
        if any(result["mouse_buttons_after"].values()):
            failures.append("mouse_button_pressed_after")
    except Exception as error:
        failures.append("action_or_readback_failed")
        result["error"] = repr(error)
    result["failures"] = failures
    result["status"] = "rejected-readback" if failures else "pointer-move-readback-matched"
    sidecar.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-image", type=Path, required=True)
    parser.add_argument("--preview-left", type=float, required=True)
    parser.add_argument("--preview-top", type=float, required=True)
    parser.add_argument("--preview-width", type=int, required=True)
    parser.add_argument("--preview-height", type=int, required=True)
    parser.add_argument("--observed-x", type=float, required=True)
    parser.add_argument("--observed-y", type=float, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--click", action="store_true")
    action.add_argument("--move", action="store_true")
    parser.add_argument("--button", choices=("left", "right"), default="left")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reviewed-left", type=float)
    parser.add_argument("--reviewed-top", type=float)
    parser.add_argument("--reviewed-width", type=int)
    parser.add_argument("--reviewed-height", type=int)
    parser.add_argument("--expected-foreground-hwnd", type=lambda value: int(value, 0))
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    if args.click and args.receipt is None:
        parser.error("--click requires --receipt")
    if args.button != "left" and not args.click:
        parser.error("--button right requires --click")
    if args.move and not args.dry_run and args.receipt is None:
        parser.error("--move requires --receipt")
    if not args.click and not args.move and args.receipt is not None:
        parser.error("--receipt is only valid with --click or --move")
    if args.dry_run and not args.move:
        parser.error("--dry-run is only valid with --move")
    reviewed = (args.reviewed_left, args.reviewed_top, args.reviewed_width, args.reviewed_height)
    if args.move and any(value is None for value in reviewed):
        parser.error("--move requires an explicit reviewed left/top/width/height region")
    if not args.move and (any(value is not None for value in reviewed) or args.expected_foreground_hwnd is not None):
        parser.error("reviewed region and expected HWND are only valid with --move")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    from PIL import Image
    import pyautogui

    with Image.open(args.source_image) as image:
        source_image_size = image.size
    live_screen_size = tuple(pyautogui.size())

    if source_image_size != live_screen_size:
        raise SystemExit(
            "refusing stale/foreign screenshot: "
            f"source image is {source_image_size[0]}x{source_image_size[1]}, "
            f"live screen is {live_screen_size[0]}x{live_screen_size[1]}"
        )

    screen_point = map_point(
        preview_bounds=(
            args.preview_left,
            args.preview_top,
            args.preview_width,
            args.preview_height,
        ),
        observed_point=(args.observed_x, args.observed_y),
        target_size=live_screen_size,
    )
    result = Mapping(
        preview_bounds=(
            args.preview_left,
            args.preview_top,
            args.preview_width,
            args.preview_height,
        ),
        observed_point=(args.observed_x, args.observed_y),
        source_image_size=source_image_size,
        live_screen_size=live_screen_size,
        screen_point=screen_point,
    )

    if args.move:
        reviewed_bounds = (args.reviewed_left, args.reviewed_top,
                           args.reviewed_width, args.reviewed_height)
        validate_reviewed_region(result, reviewed_bounds)
        if args.dry_run:
            output = {**asdict(result), "action": "move", "dry_run": True,
                      "reviewed_bounds": reviewed_bounds, "pointer_input_sent": False}
        else:
            output = move_pointer(mapping=result, reviewed_bounds=reviewed_bounds,
                                  source_image=args.source_image, receipt_path=args.receipt,
                                  desktop=pyautogui,
                                  expected_foreground_hwnd=args.expected_foreground_hwnd)
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0 if args.dry_run or not output["failures"] else 3

    if args.click:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        if args.button == "left":
            pyautogui.click(*screen_point)
        else:
            pyautogui.click(*screen_point, button=args.button)
        receipt = pyautogui.screenshot(str(args.receipt))
        if receipt.size != live_screen_size:
            raise SystemExit(
                "receipt screenshot size changed after click: "
                f"{receipt.size} != {live_screen_size}"
            )

    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
