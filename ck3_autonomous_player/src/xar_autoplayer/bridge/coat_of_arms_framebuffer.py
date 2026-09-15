"""Bounded, read-only CK3 CoA framebuffer comparison for the managed MCP."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import os
from typing import Final

import cv2
import numpy as np
from PIL import Image


COAT_OF_ARMS_FRAMEBUFFER_V1_MAXIMUM_REFERENCE_BYTES: Final = 512 * 1024
COAT_OF_ARMS_FRAMEBUFFER_V1_MINIMUM_REFERENCE_SIDE: Final = 32
COAT_OF_ARMS_FRAMEBUFFER_V1_MAXIMUM_REFERENCE_SIDE: Final = 512
COAT_OF_ARMS_FRAMEBUFFER_V1_SEARCH_SIDES: Final = (
    128,
    160,
    192,
    224,
    230,
    256,
    288,
    320,
    384,
    448,
    512,
)
COAT_OF_ARMS_FRAMEBUFFER_V1_SPATIAL_GRID: Final = 8


class CoatOfArmsFramebufferError(RuntimeError):
    """The bounded framebuffer contract could not produce valid evidence."""


def prepare_ck3_framebuffer_capture_v1(bridge_pid: int) -> dict[str, object]:
    """Bring the exact CK3 client forward with Win32 APIs and no input."""

    if os.name != "nt":
        raise CoatOfArmsFramebufferError("CK3 framebuffer capture requires Windows")
    if isinstance(bridge_pid, bool) or not isinstance(bridge_pid, int) or bridge_pid < 1:
        raise CoatOfArmsFramebufferError("native bridge PID is malformed")
    import ctypes
    import win32api
    import win32con
    import win32gui
    import win32process

    from ..vision.window import _eligible_windows, _root_window

    candidates = _eligible_windows(bridge_pid)
    if len(candidates) != 1:
        raise CoatOfArmsFramebufferError(
            f"expected one exact CK3 client for PID {bridge_pid}, found {candidates!r}"
        )
    hwnd, client_rect = candidates[0]
    raw_before = int(win32gui.GetForegroundWindow())
    before = _root_window(raw_before) if raw_before else 0
    mode = "already_foreground"
    attached_thread = 0
    detach_succeeded: bool | None = None
    if before != hwnd:
        mode = "direct"
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        raw_after_direct = int(win32gui.GetForegroundWindow())
        after_direct = _root_window(raw_after_direct) if raw_after_direct else 0
        if after_direct != hwnd:
            mode = "attached_foreground_thread"
            current_thread = int(win32api.GetCurrentThreadId())
            foreground_thread = int(
                win32process.GetWindowThreadProcessId(raw_after_direct)[0]
            )
            if foreground_thread <= 0 or foreground_thread == current_thread:
                raise CoatOfArmsFramebufferError(
                    "foreground thread cannot be attached for CK3 activation"
                )
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            attached = bool(
                user32.AttachThreadInput(current_thread, foreground_thread, True)
            )
            if not attached:
                raise CoatOfArmsFramebufferError(
                    "AttachThreadInput failed for CK3 framebuffer preparation"
                )
            attached_thread = foreground_thread
            activation_error: BaseException | None = None
            try:
                win32gui.SetForegroundWindow(hwnd)
            except BaseException as error:
                activation_error = error
            finally:
                detach_succeeded = bool(
                    user32.AttachThreadInput(current_thread, foreground_thread, False)
                )
            if not detach_succeeded:
                raise CoatOfArmsFramebufferError(
                    "AttachThreadInput detach failed after CK3 activation"
                )
            if activation_error is not None:
                raise CoatOfArmsFramebufferError(
                    f"CK3 foreground activation failed: {activation_error}"
                ) from activation_error
    candidates_after = _eligible_windows(bridge_pid)
    raw_after = int(win32gui.GetForegroundWindow())
    after = _root_window(raw_after) if raw_after else 0
    if candidates_after != candidates or after != hwnd:
        raise CoatOfArmsFramebufferError(
            "exact CK3 client did not obtain stable foreground"
        )
    return {
        "schema": "ck3-coat-of-arms-framebuffer-preparation-v1",
        "schemaVersion": 1,
        "bridgePid": bridge_pid,
        "hwnd": hwnd,
        "clientRect": list(client_rect),
        "foregroundRootBefore": before,
        "foregroundRootAfter": after,
        "mode": mode,
        "attachedForegroundThread": attached_thread,
        "detachSucceeded": detach_succeeded,
        "presentationOnly": True,
        "usesOcr": False,
        "usesKeyboard": False,
        "usesMouse": False,
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def decode_reference_png_v1(
    png_base64: str,
    expected_sha256: str,
) -> Image.Image:
    if not isinstance(png_base64, str) or not png_base64:
        raise CoatOfArmsFramebufferError("reference PNG base64 is empty")
    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789ABCDEF" for character in expected_sha256)
    ):
        raise CoatOfArmsFramebufferError("reference PNG SHA-256 is malformed")
    try:
        encoded = png_base64.encode("ascii")
        raw = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise CoatOfArmsFramebufferError("reference PNG base64 is malformed") from error
    if not 0 < len(raw) <= COAT_OF_ARMS_FRAMEBUFFER_V1_MAXIMUM_REFERENCE_BYTES:
        raise CoatOfArmsFramebufferError("reference PNG exceeds the bounded contract")
    if _sha256(raw) != expected_sha256:
        raise CoatOfArmsFramebufferError("reference PNG SHA-256 mismatch")
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format != "PNG":
                raise CoatOfArmsFramebufferError("reference payload is not PNG")
            width, height = source.size
            if (
                width != height
                or width < COAT_OF_ARMS_FRAMEBUFFER_V1_MINIMUM_REFERENCE_SIDE
                or width > COAT_OF_ARMS_FRAMEBUFFER_V1_MAXIMUM_REFERENCE_SIDE
            ):
                raise CoatOfArmsFramebufferError(
                    "reference PNG must be a bounded square canonical preview"
                )
            source.load()
            image = source.convert("RGBA")
    except CoatOfArmsFramebufferError:
        raise
    except Exception as error:
        raise CoatOfArmsFramebufferError(
            "reference payload is not a readable PNG"
        ) from error
    return image


def _shield_mask(side: int, alpha: np.ndarray | None = None) -> np.ndarray:
    mask = np.zeros((side, side), dtype=np.uint8)
    polygon = np.asarray(
        [
            [0, 0],
            [side - 1, 0],
            [side - 1, round((side - 1) * 0.72)],
            [round((side - 1) * 0.88), round((side - 1) * 0.88)],
            [round((side - 1) * 0.50), side - 1],
            [round((side - 1) * 0.12), round((side - 1) * 0.88)],
            [0, round((side - 1) * 0.72)],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(mask, [polygon], 255)
    if alpha is not None:
        mask = cv2.bitwise_and(mask, alpha.astype(np.uint8))
    return mask


def _gradient_u8(rgb: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    return np.clip(cv2.magnitude(x, y), 0, 255).astype(np.uint8)


def _finite_score_map(value: np.ndarray, fallback: float) -> np.ndarray:
    return np.nan_to_num(value, nan=fallback, posinf=fallback, neginf=fallback)


def _masked_metrics(
    reference_rgb: np.ndarray,
    observed_rgb: np.ndarray,
    mask: np.ndarray,
) -> dict[str, object]:
    selected = mask > 0
    if not np.any(selected):
        raise CoatOfArmsFramebufferError("comparison mask is empty")
    reference_float = reference_rgb.astype(np.float32) / 255.0
    observed_float = observed_rgb.astype(np.float32) / 255.0
    difference = observed_float - reference_float
    absolute = np.abs(difference)
    squared = difference * difference
    mean_absolute_error = float(np.mean(absolute[selected]))
    color_mse = float(np.mean(squared[selected]))
    reference_gradient = _gradient_u8(reference_rgb).astype(np.float32) / 255.0
    observed_gradient = _gradient_u8(observed_rgb).astype(np.float32) / 255.0
    edge_loss = float(np.mean(np.abs(observed_gradient - reference_gradient)[selected]))
    side = reference_rgb.shape[0]
    grid = COAT_OF_ARMS_FRAMEBUFFER_V1_SPATIAL_GRID
    spatial: list[list[float | None]] = []
    per_pixel = np.mean(absolute, axis=2)
    for grid_y in range(grid):
        row: list[float | None] = []
        top = grid_y * side // grid
        bottom = (grid_y + 1) * side // grid
        for grid_x in range(grid):
            left = grid_x * side // grid
            right = (grid_x + 1) * side // grid
            tile_mask = selected[top:bottom, left:right]
            tile = per_pixel[top:bottom, left:right]
            row.append(float(np.mean(tile[tile_mask])) if np.any(tile_mask) else None)
        spatial.append(row)
    return {
        "contract": "masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1",
        "maskPixels": int(np.count_nonzero(selected)),
        "meanAbsoluteError": mean_absolute_error,
        "colorMse": color_mse,
        "edgeLoss": edge_loss,
        "spatialMeanAbsoluteError8x8": spatial,
    }


def compare_reference_to_framebuffer_v1(
    reference: Image.Image,
    framebuffer: Image.Image,
    *,
    search_sides: tuple[int, ...] = COAT_OF_ARMS_FRAMEBUFFER_V1_SEARCH_SIDES,
) -> dict[str, object]:
    reference_rgba = np.asarray(reference.convert("RGBA"), dtype=np.uint8)
    frame_rgb = np.asarray(framebuffer.convert("RGB"), dtype=np.uint8)
    if frame_rgb.ndim != 3 or frame_rgb.shape[2] != 3:
        raise CoatOfArmsFramebufferError("framebuffer is not RGB")
    frame_height, frame_width = frame_rgb.shape[:2]
    candidates: list[dict[str, object]] = []
    frame_gradient = _gradient_u8(frame_rgb)
    for side in search_sides:
        if (
            isinstance(side, bool)
            or not isinstance(side, int)
            or side < COAT_OF_ARMS_FRAMEBUFFER_V1_MINIMUM_REFERENCE_SIDE
            or side > min(frame_width, frame_height)
        ):
            raise CoatOfArmsFramebufferError("search side is outside the bounded frame")
        resized = cv2.resize(reference_rgba, (side, side), interpolation=cv2.INTER_AREA)
        template_rgb = resized[:, :, :3]
        mask = _shield_mask(side, resized[:, :, 3])
        color = cv2.matchTemplate(
            frame_rgb,
            template_rgb,
            cv2.TM_SQDIFF_NORMED,
            mask=mask,
        )
        template_gradient = _gradient_u8(template_rgb)
        edge = cv2.matchTemplate(
            frame_gradient,
            template_gradient,
            cv2.TM_CCORR_NORMED,
            mask=mask,
        )
        combined = (
            0.72 * _finite_score_map(color, 1.0)
            + 0.28 * (1.0 - _finite_score_map(edge, 0.0))
        )
        minimum, _maximum, location, _maximum_location = cv2.minMaxLoc(combined)
        distinct = combined.copy()
        distinct[
            max(0, location[1] - side) : min(
                distinct.shape[0], location[1] + side + 1
            ),
            max(0, location[0] - side) : min(
                distinct.shape[1], location[0] + side + 1
            ),
        ] = np.inf
        (
            second_minimum,
            _maximum,
            second_location,
            _maximum_location,
        ) = cv2.minMaxLoc(distinct)
        candidates.append(
            {
                "side": side,
                "x": int(location[0]),
                "y": int(location[1]),
                "locatorLoss": float(minimum),
                "secondDistinctX": int(second_location[0]),
                "secondDistinctY": int(second_location[1]),
                "secondDistinctLoss": float(second_minimum),
                "distinctMargin": float(second_minimum - minimum),
            }
        )
    candidates.sort(key=lambda row: (float(row["locatorLoss"]), int(row["side"])))
    best = candidates[0]
    side = int(best["side"])
    x = int(best["x"])
    y = int(best["y"])
    crop = framebuffer.convert("RGB").crop((x, y, x + side, y + side))
    observed = np.asarray(
        crop.resize(reference.size, Image.Resampling.BILINEAR), dtype=np.uint8
    )
    reference_rgb = reference_rgba[:, :, :3]
    mask = _shield_mask(reference.width, reference_rgba[:, :, 3])
    output = BytesIO()
    crop.save(output, format="PNG", optimize=True)
    crop_png = output.getvalue()
    return {
        "locatorContract": "full-client-global-shield-mask-color72-edge28-v1",
        "searchedWholeFramebuffer": True,
        "fixedScreenCoordinatesUsed": False,
        "searchSides": list(search_sides),
        "bestMatch": {
            **best,
            "rect": [x, y, x + side, y + side],
            "cropPngSha256": _sha256(crop_png),
            "cropPngBase64": base64.b64encode(crop_png).decode("ascii"),
        },
        "scaleCandidates": candidates,
        "metrics": _masked_metrics(reference_rgb, observed, mask),
    }


def _require_unobscured_client(
    hwnd: int, client_rect: tuple[int, int, int, int]
) -> None:
    import win32gui

    from ..vision.window import _root_window

    blockers: list[tuple[int, tuple[int, int, int, int]]] = []
    reached_target = False

    def intersects(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> bool:
        return (
            max(first[0], second[0]) < min(first[2], second[2])
            and max(first[1], second[1]) < min(first[3], second[3])
        )

    def visit(candidate: int, _: object) -> None:
        nonlocal reached_target
        root = _root_window(candidate)
        if root == hwnd:
            reached_target = True
            return
        if (
            reached_target
            or not win32gui.IsWindowVisible(root)
            or win32gui.IsIconic(root)
        ):
            return
        rect = tuple(int(value) for value in win32gui.GetWindowRect(root))
        if rect[2] - rect[0] <= 1 and rect[3] - rect[1] <= 1:
            return
        if intersects(client_rect, rect):
            blockers.append((int(root), rect))

    win32gui.EnumWindows(visit, None)
    if not reached_target:
        raise CoatOfArmsFramebufferError("bound CK3 window disappeared from Z order")
    if blockers:
        raise CoatOfArmsFramebufferError(f"CK3 client is obscured: {blockers!r}")


def capture_ck3_client_framebuffer_v1(bridge_pid: int) -> Image.Image:
    if os.name != "nt":
        raise CoatOfArmsFramebufferError("CK3 framebuffer capture requires Windows")
    if isinstance(bridge_pid, bool) or not isinstance(bridge_pid, int) or bridge_pid < 1:
        raise CoatOfArmsFramebufferError("native bridge PID is malformed")
    import win32gui
    from PIL import ImageGrab

    from ..vision.window import EXPECTED_CLIENT_SIZE, _eligible_windows, _root_window

    candidates = _eligible_windows(bridge_pid)
    if len(candidates) != 1:
        raise CoatOfArmsFramebufferError(
            f"expected one exact CK3 client for PID {bridge_pid}, found {candidates!r}"
        )
    hwnd, client_rect = candidates[0]
    if _root_window(int(win32gui.GetForegroundWindow())) != hwnd:
        raise CoatOfArmsFramebufferError("bound CK3 client is not foreground")
    _require_unobscured_client(hwnd, client_rect)
    image = ImageGrab.grab(bbox=client_rect, all_screens=True).convert("RGB")
    after = _eligible_windows(bridge_pid)
    if after != candidates or _root_window(int(win32gui.GetForegroundWindow())) != hwnd:
        raise CoatOfArmsFramebufferError("CK3 binding changed during framebuffer capture")
    _require_unobscured_client(hwnd, client_rect)
    if image.size != EXPECTED_CLIENT_SIZE:
        raise CoatOfArmsFramebufferError(
            f"captured CK3 client has size {image.size}, expected {EXPECTED_CLIENT_SIZE}"
        )
    return image


def capture_and_compare_coat_of_arms_framebuffer_v1(
    bridge_pid: int,
    reference_png_base64: str,
    reference_png_sha256: str,
) -> dict[str, object]:
    reference = decode_reference_png_v1(reference_png_base64, reference_png_sha256)
    framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
    framebuffer_bytes = framebuffer.tobytes()
    comparison = compare_reference_to_framebuffer_v1(reference, framebuffer)
    return {
        "schema": "ck3-coat-of-arms-framebuffer-comparison-v1",
        "schemaVersion": 1,
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "captureBackend": "windows-imagegrab-authenticated-client-framebuffer",
        "bridgePid": bridge_pid,
        "framebuffer": {
            "width": framebuffer.width,
            "height": framebuffer.height,
            "pixelFormat": "RGB8",
            "pixelSha256": _sha256(framebuffer_bytes),
        },
        "reference": {
            "width": reference.width,
            "height": reference.height,
            "pngSha256": reference_png_sha256,
        },
        "comparison": comparison,
        "readOnly": True,
        "usesOcr": False,
        "usesKeyboard": False,
        "usesMouse": False,
    }
