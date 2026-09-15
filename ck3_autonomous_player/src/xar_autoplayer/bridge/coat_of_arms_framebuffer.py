"""Bounded, read-only CK3 CoA framebuffer comparison for the managed MCP."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import os
import re
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
COAT_OF_ARMS_FRAMEBUFFER_V2_CALIBRATION_DIFFERENCE_THRESHOLD: Final = 48
COAT_OF_ARMS_FRAMEBUFFER_V2_MAXIMUM_CALIBRATIONS: Final = 4
COAT_OF_ARMS_FRAMEBUFFER_V3_ANCHOR_POSITIONS: Final = (
    (0.30, 0.30),
    (0.50, 0.30),
    (0.70, 0.30),
    (0.30, 0.50),
    (0.50, 0.50),
    (0.70, 0.50),
    (0.30, 0.70),
    (0.50, 0.70),
    (0.70, 0.70),
)
COAT_OF_ARMS_FRAMEBUFFER_V3_ANCHOR_DIFFERENCE_THRESHOLD: Final = 48
COAT_OF_ARMS_FRAMEBUFFER_V3_MAXIMUM_REPROJECTION_ERROR: Final = 2.5


class CoatOfArmsFramebufferError(RuntimeError):
    """The bounded framebuffer contract could not produce valid evidence."""


@dataclass(frozen=True)
class CoatOfArmsFramebufferCalibrationV2:
    calibration_id: str
    bridge_pid: int
    framebuffer_size: tuple[int, int]
    rect: tuple[int, int, int, int]
    mask: np.ndarray
    begin_pixel_sha256: str
    complete_pixel_sha256: str
    component_count: int
    changed_pixels: int
    selected_pixels: int


@dataclass(frozen=True)
class CoatOfArmsFramebufferCalibrationV3:
    calibration_id: str
    bridge_pid: int
    framebuffer_size: tuple[int, int]
    rect: tuple[int, int, int, int]
    mask: np.ndarray
    canonical_to_framebuffer: np.ndarray
    anchor_positions: tuple[tuple[float, float], ...]
    observed_anchor_centers: tuple[tuple[float, float], ...]
    reprojection_errors: tuple[float, ...]
    surface_receipt: dict[str, object]
    anchor_base_pixel_sha256: str
    anchors_complete_pixel_sha256: str


def _calibration_id(value: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value) is None
    ):
        raise CoatOfArmsFramebufferError("calibration ID is malformed")
    return value


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
    direct_activation_error: str | None = None
    attached_activation_error: str | None = None
    if before != hwnd:
        mode = "direct"
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.BringWindowToTop(hwnd)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except BaseException as error:
            direct_activation_error = f"{type(error).__name__}: {error}"
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
                attached_activation_error = f"{type(error).__name__}: {error}"
            finally:
                detach_succeeded = bool(
                    user32.AttachThreadInput(current_thread, foreground_thread, False)
                )
            if not detach_succeeded:
                raise CoatOfArmsFramebufferError(
                    "AttachThreadInput detach failed after CK3 activation"
                )
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
        "directActivationError": direct_activation_error,
        "attachedActivationError": attached_activation_error,
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


def derive_two_state_calibration_v2(
    calibration_id: str,
    bridge_pid: int,
    begin: Image.Image,
    complete: Image.Image,
) -> CoatOfArmsFramebufferCalibrationV2:
    """Locate the largest CoA surface changed by two caller-applied solid states.

    The two images are independent of the later reference image.  This prevents
    the evidence path from choosing a different, reference-friendly GUI crop
    for every test case.
    """

    identifier = _calibration_id(calibration_id)
    if isinstance(bridge_pid, bool) or not isinstance(bridge_pid, int) or bridge_pid < 1:
        raise CoatOfArmsFramebufferError("native bridge PID is malformed")
    if begin.size != complete.size or begin.width < 1 or begin.height < 1:
        raise CoatOfArmsFramebufferError("calibration frame sizes differ")
    begin_rgb = np.asarray(begin.convert("RGB"), dtype=np.uint8)
    complete_rgb = np.asarray(complete.convert("RGB"), dtype=np.uint8)
    difference = np.max(
        np.abs(begin_rgb.astype(np.int16) - complete_rgb.astype(np.int16)), axis=2
    )
    changed = np.where(
        difference >= COAT_OF_ARMS_FRAMEBUFFER_V2_CALIBRATION_DIFFERENCE_THRESHOLD,
        255,
        0,
    ).astype(np.uint8)
    changed_pixels = int(np.count_nonzero(changed))
    if changed_pixels < 512:
        raise CoatOfArmsFramebufferError(
            "two-state calibration did not change enough framebuffer pixels"
        )
    opened = cv2.morphologyEx(
        changed,
        cv2.MORPH_OPEN,
        np.ones((3, 3), dtype=np.uint8),
    )
    connected_count, labels, statistics, _centroids = cv2.connectedComponentsWithStats(
        opened, connectivity=8
    )
    candidates: list[tuple[int, int, int, int, int, int, int]] = []
    for label in range(1, connected_count):
        x = int(statistics[label, cv2.CC_STAT_LEFT])
        y = int(statistics[label, cv2.CC_STAT_TOP])
        width = int(statistics[label, cv2.CC_STAT_WIDTH])
        height = int(statistics[label, cv2.CC_STAT_HEIGHT])
        area = int(statistics[label, cv2.CC_STAT_AREA])
        aspect = width / height if height else 0.0
        fill = area / (width * height) if width and height else 0.0
        if (
            width >= 32
            and height >= 32
            and area >= 512
            and 0.55 <= aspect <= 1.8
            and fill >= 0.12
        ):
            candidates.append((area, width * height, x, y, width, height, label))
    if not candidates:
        raise CoatOfArmsFramebufferError(
            "two-state calibration found no bounded CoA-sized component"
        )
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
    _area, _box_area, x, y, width, height, selected_label = candidates[0]
    component = np.where(labels == selected_label, 255, 0).astype(np.uint8)
    component = cv2.morphologyEx(
        component,
        cv2.MORPH_CLOSE,
        np.ones((5, 5), dtype=np.uint8),
    )
    mask = component[y : y + height, x : x + width]
    selected_pixels = int(np.count_nonzero(mask))
    if selected_pixels < 512:
        raise CoatOfArmsFramebufferError("calibrated CoA surface mask is empty")
    return CoatOfArmsFramebufferCalibrationV2(
        calibration_id=identifier,
        bridge_pid=bridge_pid,
        framebuffer_size=begin.size,
        rect=(x, y, x + width, y + height),
        mask=mask,
        begin_pixel_sha256=_sha256(begin_rgb.tobytes()),
        complete_pixel_sha256=_sha256(complete_rgb.tobytes()),
        component_count=len(candidates),
        changed_pixels=changed_pixels,
        selected_pixels=selected_pixels,
    )


def _calibration_receipt_v2(
    calibration: CoatOfArmsFramebufferCalibrationV2,
) -> dict[str, object]:
    mask_image = Image.fromarray(calibration.mask, mode="L")
    output = BytesIO()
    mask_image.save(output, format="PNG", optimize=True)
    mask_png = output.getvalue()
    return {
        "schema": "ck3-coat-of-arms-framebuffer-calibration-v2",
        "schemaVersion": 2,
        "calibrationId": calibration.calibration_id,
        "bridgePid": calibration.bridge_pid,
        "framebufferSize": list(calibration.framebuffer_size),
        "rect": list(calibration.rect),
        "differenceThreshold": (
            COAT_OF_ARMS_FRAMEBUFFER_V2_CALIBRATION_DIFFERENCE_THRESHOLD
        ),
        "candidateComponentCount": calibration.component_count,
        "changedPixels": calibration.changed_pixels,
        "selectedPixels": calibration.selected_pixels,
        "beginPixelSha256": calibration.begin_pixel_sha256,
        "completePixelSha256": calibration.complete_pixel_sha256,
        "maskPngSha256": _sha256(mask_png),
        "maskPngBase64": base64.b64encode(mask_png).decode("ascii"),
        "referenceIndependent": True,
        "fixedScreenCoordinatesUsed": False,
        "usesOcr": False,
        "usesKeyboard": False,
        "usesMouse": False,
    }


def compare_reference_to_calibrated_framebuffer_v2(
    reference: Image.Image,
    framebuffer: Image.Image,
    calibration: CoatOfArmsFramebufferCalibrationV2,
) -> dict[str, object]:
    if framebuffer.size != calibration.framebuffer_size:
        raise CoatOfArmsFramebufferError("framebuffer size changed after calibration")
    left, top, right, bottom = calibration.rect
    if not (
        0 <= left < right <= framebuffer.width
        and 0 <= top < bottom <= framebuffer.height
    ):
        raise CoatOfArmsFramebufferError("calibrated CoA rectangle is outside the frame")
    reference_rgba = np.asarray(reference.convert("RGBA"), dtype=np.uint8)
    reference_rgb = reference_rgba[:, :, :3]
    crop = framebuffer.convert("RGB").crop((left, top, right, bottom))
    normalized = crop.resize(reference.size, Image.Resampling.BILINEAR)
    observed_rgb = np.asarray(normalized, dtype=np.uint8)
    mask = cv2.resize(
        calibration.mask,
        reference.size,
        interpolation=cv2.INTER_NEAREST,
    )
    erosion_radius = max(1, round(reference.width * 0.02))
    comparison_mask = cv2.erode(
        mask,
        np.ones((erosion_radius * 2 + 1, erosion_radius * 2 + 1), dtype=np.uint8),
    )
    alpha = reference_rgba[:, :, 3]
    comparison_mask = cv2.bitwise_and(comparison_mask, alpha)
    metrics = _masked_metrics(reference_rgb, observed_rgb, comparison_mask)
    crop_output = BytesIO()
    crop.save(crop_output, format="PNG", optimize=True)
    crop_png = crop_output.getvalue()
    visible_surface = np.dstack((observed_rgb, mask)).astype(np.uint8)
    normalized_output = BytesIO()
    Image.fromarray(visible_surface, mode="RGBA").save(
        normalized_output, format="PNG", optimize=True
    )
    normalized_png = normalized_output.getvalue()
    return {
        "locatorContract": "two-solid-state-reference-independent-surface-v2",
        "calibrationId": calibration.calibration_id,
        "searchedWholeFramebuffer": False,
        "referenceUsedForLocalization": False,
        "fixedScreenCoordinatesUsed": False,
        "bestMatch": {
            "rect": list(calibration.rect),
            "cropPngSha256": _sha256(crop_png),
            "cropPngBase64": base64.b64encode(crop_png).decode("ascii"),
            "alignedContentPngSha256": _sha256(normalized_png),
            "alignedContentPngBase64": base64.b64encode(normalized_png).decode(
                "ascii"
            ),
        },
        "comparisonMask": {
            "contract": "two-solid-state-dynamic-surface-eroded-v2",
            "erosionRadiusPixels": erosion_radius,
            "maskPixels": int(np.count_nonzero(comparison_mask)),
        },
        "metrics": metrics,
    }


def derive_anchor_calibration_v3(
    surface: CoatOfArmsFramebufferCalibrationV2,
    anchor_base: Image.Image,
    anchors_complete: Image.Image,
    *,
    anchor_positions: tuple[tuple[float, float], ...] = (
        COAT_OF_ARMS_FRAMEBUFFER_V3_ANCHOR_POSITIONS
    ),
) -> CoatOfArmsFramebufferCalibrationV3:
    """Recover canonical CoA UV coordinates from nine native marker centers."""

    if (
        anchor_base.size != surface.framebuffer_size
        or anchors_complete.size != surface.framebuffer_size
    ):
        raise CoatOfArmsFramebufferError(
            "anchor calibration frame size differs from the surface calibration"
        )
    if len(anchor_positions) != 9:
        raise CoatOfArmsFramebufferError("anchor calibration requires nine positions")
    left, top, right, bottom = surface.rect
    base_rgb = np.asarray(anchor_base.convert("RGB"), dtype=np.uint8)[
        top:bottom, left:right
    ]
    complete_rgb = np.asarray(anchors_complete.convert("RGB"), dtype=np.uint8)[
        top:bottom, left:right
    ]
    difference = np.max(
        np.abs(base_rgb.astype(np.int16) - complete_rgb.astype(np.int16)), axis=2
    )
    marker_pixels = np.where(
        (difference >= COAT_OF_ARMS_FRAMEBUFFER_V3_ANCHOR_DIFFERENCE_THRESHOLD)
        & (surface.mask > 0),
        255,
        0,
    ).astype(np.uint8)
    marker_pixels = cv2.morphologyEx(
        marker_pixels,
        cv2.MORPH_OPEN,
        np.ones((3, 3), dtype=np.uint8),
    )
    count, _labels, statistics, centroids = cv2.connectedComponentsWithStats(
        marker_pixels, connectivity=8
    )
    maximum_area = max(16, round(surface.selected_pixels * 0.04))
    candidates: list[tuple[int, float, float]] = []
    for label in range(1, count):
        width = int(statistics[label, cv2.CC_STAT_WIDTH])
        height = int(statistics[label, cv2.CC_STAT_HEIGHT])
        area = int(statistics[label, cv2.CC_STAT_AREA])
        aspect = width / height if height else 0.0
        if (
            width >= 3
            and height >= 3
            and 9 <= area <= maximum_area
            and 0.45 <= aspect <= 2.20
        ):
            candidates.append(
                (area, float(centroids[label, 0]), float(centroids[label, 1]))
            )
    if len(candidates) != len(anchor_positions):
        raise CoatOfArmsFramebufferError(
            "anchor calibration did not isolate exactly nine native markers: "
            f"found {len(candidates)}"
        )
    ordered_by_y = sorted(candidates, key=lambda value: (value[2], value[1]))
    ordered: list[tuple[int, float, float]] = []
    for row_start in range(0, len(ordered_by_y), 3):
        ordered.extend(
            sorted(
                ordered_by_y[row_start : row_start + 3],
                key=lambda value: value[1],
            )
        )
    observed = np.asarray(
        [(x + left, y + top) for _area, x, y in ordered], dtype=np.float32
    )
    canonical = np.asarray(anchor_positions, dtype=np.float32)
    affine, inliers = cv2.estimateAffine2D(
        canonical,
        observed,
        method=cv2.RANSAC,
        ransacReprojThreshold=1.5,
        maxIters=2000,
        confidence=0.999,
        refineIters=10,
    )
    if affine is None or inliers is None or int(np.count_nonzero(inliers)) != 9:
        raise CoatOfArmsFramebufferError(
            "anchor calibration could not fit all markers to one affine UV map"
        )
    projected = cv2.transform(canonical.reshape(1, -1, 2), affine)[0]
    errors = np.linalg.norm(projected - observed, axis=1)
    if float(np.max(errors)) > COAT_OF_ARMS_FRAMEBUFFER_V3_MAXIMUM_REPROJECTION_ERROR:
        raise CoatOfArmsFramebufferError(
            "anchor calibration reprojection error exceeds the bounded contract"
        )
    return CoatOfArmsFramebufferCalibrationV3(
        calibration_id=surface.calibration_id,
        bridge_pid=surface.bridge_pid,
        framebuffer_size=surface.framebuffer_size,
        rect=surface.rect,
        mask=surface.mask.copy(),
        canonical_to_framebuffer=affine.astype(np.float64),
        anchor_positions=tuple(anchor_positions),
        observed_anchor_centers=tuple(
            (float(value[0]), float(value[1])) for value in observed
        ),
        reprojection_errors=tuple(float(value) for value in errors),
        surface_receipt=_calibration_receipt_v2(surface),
        anchor_base_pixel_sha256=_sha256(
            np.asarray(anchor_base.convert("RGB"), dtype=np.uint8).tobytes()
        ),
        anchors_complete_pixel_sha256=_sha256(
            np.asarray(anchors_complete.convert("RGB"), dtype=np.uint8).tobytes()
        ),
    )


def _calibration_receipt_v3(
    calibration: CoatOfArmsFramebufferCalibrationV3,
) -> dict[str, object]:
    return {
        "schema": "ck3-coat-of-arms-framebuffer-calibration-v3",
        "schemaVersion": 3,
        "calibrationId": calibration.calibration_id,
        "bridgePid": calibration.bridge_pid,
        "framebufferSize": list(calibration.framebuffer_size),
        "rect": list(calibration.rect),
        "surface": calibration.surface_receipt,
        "anchorPositions": [list(value) for value in calibration.anchor_positions],
        "observedAnchorCenters": [
            list(value) for value in calibration.observed_anchor_centers
        ],
        "canonicalToFramebufferAffine": calibration.canonical_to_framebuffer.tolist(),
        "reprojectionErrors": list(calibration.reprojection_errors),
        "maximumReprojectionError": max(calibration.reprojection_errors),
        "maximumAllowedReprojectionError": (
            COAT_OF_ARMS_FRAMEBUFFER_V3_MAXIMUM_REPROJECTION_ERROR
        ),
        "anchorDifferenceThreshold": (
            COAT_OF_ARMS_FRAMEBUFFER_V3_ANCHOR_DIFFERENCE_THRESHOLD
        ),
        "anchorBasePixelSha256": calibration.anchor_base_pixel_sha256,
        "anchorsCompletePixelSha256": calibration.anchors_complete_pixel_sha256,
        "referenceIndependent": True,
        "uvRegistered": True,
        "fixedScreenCoordinatesUsed": False,
        "usesOcr": False,
        "usesKeyboard": False,
        "usesMouse": False,
    }


def compare_reference_to_calibrated_framebuffer_v3(
    reference: Image.Image,
    framebuffer: Image.Image,
    calibration: CoatOfArmsFramebufferCalibrationV3,
) -> dict[str, object]:
    """Compare in canonical UV space, excluding the native frame geometry."""

    if framebuffer.size != calibration.framebuffer_size:
        raise CoatOfArmsFramebufferError("framebuffer size changed after calibration")
    side = reference.width
    reference_rgba = np.asarray(reference.convert("RGBA"), dtype=np.uint8)
    reference_rgb = reference_rgba[:, :, :3]
    frame_rgb = np.asarray(framebuffer.convert("RGB"), dtype=np.uint8)
    pixel_to_framebuffer = calibration.canonical_to_framebuffer.copy()
    denominator = max(1, side - 1)
    pixel_to_framebuffer[:, :2] /= denominator
    aligned_rgb = cv2.warpAffine(
        frame_rgb,
        pixel_to_framebuffer,
        (side, side),
        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    full_mask = np.zeros((framebuffer.height, framebuffer.width), dtype=np.uint8)
    left, top, right, bottom = calibration.rect
    full_mask[top:bottom, left:right] = calibration.mask
    aligned_mask = cv2.warpAffine(
        full_mask,
        pixel_to_framebuffer,
        (side, side),
        flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    erosion_radius = max(1, round(side * 0.02))
    comparison_mask = cv2.erode(
        aligned_mask,
        np.ones((erosion_radius * 2 + 1, erosion_radius * 2 + 1), dtype=np.uint8),
    )
    comparison_mask = cv2.bitwise_and(comparison_mask, reference_rgba[:, :, 3])
    metrics = _masked_metrics(reference_rgb, aligned_rgb, comparison_mask)
    crop = framebuffer.convert("RGB").crop(calibration.rect)
    crop_output = BytesIO()
    crop.save(crop_output, format="PNG", optimize=True)
    crop_png = crop_output.getvalue()
    visible_surface = np.dstack((aligned_rgb, aligned_mask)).astype(np.uint8)
    aligned_output = BytesIO()
    Image.fromarray(visible_surface, mode="RGBA").save(
        aligned_output, format="PNG", optimize=True
    )
    aligned_png = aligned_output.getvalue()
    return {
        "locatorContract": "two-solid-state-surface-nine-marker-affine-uv-v3",
        "calibrationId": calibration.calibration_id,
        "searchedWholeFramebuffer": False,
        "referenceUsedForLocalization": False,
        "referenceUsedForRegistration": False,
        "fixedScreenCoordinatesUsed": False,
        "bestMatch": {
            "rect": list(calibration.rect),
            "cropPngSha256": _sha256(crop_png),
            "cropPngBase64": base64.b64encode(crop_png).decode("ascii"),
            "alignedContentPngSha256": _sha256(aligned_png),
            "alignedContentPngBase64": base64.b64encode(aligned_png).decode(
                "ascii"
            ),
        },
        "comparisonMask": {
            "contract": "native-surface-affine-uv-eroded-v3",
            "erosionRadiusPixels": erosion_radius,
            "maskPixels": int(np.count_nonzero(comparison_mask)),
        },
        "metrics": metrics,
    }


def _aligned_content(
    reference_rgb: np.ndarray,
    framebuffer: Image.Image,
    outer_rect: tuple[int, int, int, int],
    mask: np.ndarray,
) -> tuple[Image.Image, dict[str, object], dict[str, object]]:
    left, top, right, bottom = outer_rect
    outer_side = right - left
    reference_side = reference_rgb.shape[0]
    candidates: list[tuple[float, int, int, int, dict[str, object], Image.Image]] = []
    for ratio in (0.82, 0.85, 0.875, 0.90, 0.925, 0.95, 1.0):
        content_side = max(1, round(outer_side * ratio))
        nominal_left = left + (outer_side - content_side) // 2
        nominal_top = top + (outer_side - content_side) // 2
        for offset_y_ratio in (-0.025, 0.0, 0.025):
            for offset_x_ratio in (-0.025, 0.0, 0.025):
                content_left = nominal_left + round(outer_side * offset_x_ratio)
                content_top = nominal_top + round(outer_side * offset_y_ratio)
                content_right = content_left + content_side
                content_bottom = content_top + content_side
                if (
                    content_left < left
                    or content_top < top
                    or content_right > right
                    or content_bottom > bottom
                ):
                    continue
                crop = framebuffer.convert("RGB").crop(
                    (content_left, content_top, content_right, content_bottom)
                )
                normalized = crop.resize(
                    (reference_side, reference_side), Image.Resampling.BILINEAR
                )
                observed = np.asarray(normalized, dtype=np.uint8)
                metrics = _masked_metrics(reference_rgb, observed, mask)
                score = (
                    0.62 * float(metrics["colorMse"])
                    + 0.38 * float(metrics["edgeLoss"])
                )
                candidates.append(
                    (
                        score,
                        content_side,
                        content_left,
                        content_top,
                        metrics,
                        normalized,
                    )
                )
    if not candidates:
        raise CoatOfArmsFramebufferError("no bounded content alignment candidate")
    candidates.sort(key=lambda value: (value[0], -value[1], value[2], value[3]))
    score, content_side, content_left, content_top, metrics, normalized = candidates[0]
    return normalized, metrics, {
        "contract": "outer-frame-local-square-alignment-v1",
        "candidateCount": len(candidates),
        "outerRect": list(outer_rect),
        "contentRect": [
            content_left,
            content_top,
            content_left + content_side,
            content_top + content_side,
        ],
        "contentToOuterRatio": content_side / outer_side,
        "alignmentLoss": score,
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
    reference_rgb = reference_rgba[:, :, :3]
    mask = _shield_mask(reference.width, reference_rgba[:, :, 3])
    erosion_radius = max(1, round(reference.width * 0.025))
    erosion_kernel = np.ones(
        (erosion_radius * 2 + 1, erosion_radius * 2 + 1), dtype=np.uint8
    )
    comparison_mask = cv2.erode(mask, erosion_kernel)
    aligned, metrics, alignment = _aligned_content(
        reference_rgb,
        framebuffer,
        (x, y, x + side, y + side),
        comparison_mask,
    )
    output = BytesIO()
    crop.save(output, format="PNG", optimize=True)
    crop_png = output.getvalue()
    aligned_output = BytesIO()
    aligned.save(aligned_output, format="PNG", optimize=True)
    aligned_png = aligned_output.getvalue()
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
            "alignment": alignment,
            "alignedContentPngSha256": _sha256(aligned_png),
            "alignedContentPngBase64": base64.b64encode(aligned_png).decode(
                "ascii"
            ),
        },
        "scaleCandidates": candidates,
        "comparisonMask": {
            "contract": "shield-polygon-alpha-eroded-v1",
            "erosionRadiusPixels": erosion_radius,
            "maskPixels": int(np.count_nonzero(comparison_mask)),
        },
        "metrics": metrics,
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


class CoatOfArmsFramebufferCalibrationStoreV2:
    """Bounded process-local calibration state for the developer MCP."""

    def __init__(self) -> None:
        self._begins: dict[str, tuple[int, Image.Image]] = {}
        self._calibrations: dict[str, CoatOfArmsFramebufferCalibrationV2] = {}

    def begin(self, bridge_pid: int, calibration_id: str) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        if identifier in self._begins or identifier in self._calibrations:
            raise CoatOfArmsFramebufferError("calibration ID is already in use")
        if len(self._begins) + len(self._calibrations) >= (
            COAT_OF_ARMS_FRAMEBUFFER_V2_MAXIMUM_CALIBRATIONS
        ):
            raise CoatOfArmsFramebufferError("calibration store is full")
        framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        pixels = framebuffer.tobytes()
        self._begins[identifier] = (bridge_pid, framebuffer.copy())
        return {
            "schema": "ck3-coat-of-arms-framebuffer-calibration-stage-v2",
            "schemaVersion": 2,
            "calibrationId": identifier,
            "phase": "begin",
            "bridgePid": bridge_pid,
            "framebufferSize": list(framebuffer.size),
            "pixelSha256": _sha256(pixels),
            "readyForComplete": True,
            "readOnlyCapture": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

    def complete(self, bridge_pid: int, calibration_id: str) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        begin = self._begins.pop(identifier, None)
        if begin is None:
            raise CoatOfArmsFramebufferError("calibration begin state is missing")
        begin_pid, begin_framebuffer = begin
        if begin_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID changed during calibration")
        complete_framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        calibration = derive_two_state_calibration_v2(
            identifier,
            bridge_pid,
            begin_framebuffer,
            complete_framebuffer,
        )
        self._calibrations[identifier] = calibration
        return {
            **_calibration_receipt_v2(calibration),
            "phase": "complete",
            "readyForComparison": True,
        }

    def compare(
        self,
        bridge_pid: int,
        calibration_id: str,
        reference_png_base64: str,
        reference_png_sha256: str,
    ) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        calibration = self._calibrations.get(identifier)
        if calibration is None:
            raise CoatOfArmsFramebufferError("completed calibration is missing")
        if calibration.bridge_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID differs from calibration")
        reference = decode_reference_png_v1(
            reference_png_base64, reference_png_sha256
        )
        framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        framebuffer_bytes = framebuffer.tobytes()
        comparison = compare_reference_to_calibrated_framebuffer_v2(
            reference, framebuffer, calibration
        )
        return {
            "schema": "ck3-coat-of-arms-framebuffer-comparison-v2",
            "schemaVersion": 2,
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
            "calibration": _calibration_receipt_v2(calibration),
            "comparison": comparison,
            "readOnly": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }


class CoatOfArmsFramebufferCalibrationStoreV3:
    """Bounded four-frame surface and UV calibration for the developer MCP."""

    def __init__(self) -> None:
        self._surface_begins: dict[str, tuple[int, Image.Image]] = {}
        self._surfaces: dict[str, CoatOfArmsFramebufferCalibrationV2] = {}
        self._anchor_bases: dict[str, tuple[int, Image.Image]] = {}
        self._calibrations: dict[str, CoatOfArmsFramebufferCalibrationV3] = {}

    def _active_identifiers(self) -> set[str]:
        return (
            set(self._surface_begins)
            | set(self._surfaces)
            | set(self._anchor_bases)
            | set(self._calibrations)
        )

    @staticmethod
    def _stage_receipt(
        identifier: str,
        bridge_pid: int,
        phase: str,
        framebuffer: Image.Image,
        next_phase: str,
    ) -> dict[str, object]:
        return {
            "schema": "ck3-coat-of-arms-framebuffer-calibration-stage-v3",
            "schemaVersion": 3,
            "calibrationId": identifier,
            "phase": phase,
            "bridgePid": bridge_pid,
            "framebufferSize": list(framebuffer.size),
            "pixelSha256": _sha256(framebuffer.tobytes()),
            "nextPhase": next_phase,
            "readOnlyCapture": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

    def begin(self, bridge_pid: int, calibration_id: str) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        if identifier in self._active_identifiers():
            raise CoatOfArmsFramebufferError("calibration ID is already in use")
        if len(self._active_identifiers()) >= (
            COAT_OF_ARMS_FRAMEBUFFER_V2_MAXIMUM_CALIBRATIONS
        ):
            raise CoatOfArmsFramebufferError("calibration store is full")
        framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        self._surface_begins[identifier] = (bridge_pid, framebuffer.copy())
        return self._stage_receipt(
            identifier, bridge_pid, "begin", framebuffer, "surface_complete"
        )

    def surface_complete(
        self, bridge_pid: int, calibration_id: str
    ) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        begin = self._surface_begins.pop(identifier, None)
        if begin is None:
            raise CoatOfArmsFramebufferError("surface calibration begin is missing")
        begin_pid, begin_framebuffer = begin
        if begin_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID changed during calibration")
        complete_framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        surface = derive_two_state_calibration_v2(
            identifier, bridge_pid, begin_framebuffer, complete_framebuffer
        )
        self._surfaces[identifier] = surface
        return {
            **_calibration_receipt_v2(surface),
            "schema": "ck3-coat-of-arms-framebuffer-calibration-stage-v3",
            "schemaVersion": 3,
            "phase": "surface_complete",
            "nextPhase": "anchor_base",
            "readyForAnchorBase": True,
        }

    def anchor_base(
        self, bridge_pid: int, calibration_id: str
    ) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        surface = self._surfaces.get(identifier)
        if surface is None:
            raise CoatOfArmsFramebufferError("surface calibration is missing")
        if surface.bridge_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID changed during calibration")
        if identifier in self._anchor_bases:
            raise CoatOfArmsFramebufferError("anchor base is already captured")
        framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        self._anchor_bases[identifier] = (bridge_pid, framebuffer.copy())
        return self._stage_receipt(
            identifier,
            bridge_pid,
            "anchor_base",
            framebuffer,
            "anchors_complete",
        )

    def anchors_complete(
        self, bridge_pid: int, calibration_id: str
    ) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        surface = self._surfaces.pop(identifier, None)
        anchor_base = self._anchor_bases.pop(identifier, None)
        if surface is None or anchor_base is None:
            raise CoatOfArmsFramebufferError("anchor calibration state is incomplete")
        base_pid, base_framebuffer = anchor_base
        if surface.bridge_pid != bridge_pid or base_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID changed during calibration")
        complete_framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        calibration = derive_anchor_calibration_v3(
            surface, base_framebuffer, complete_framebuffer
        )
        self._calibrations[identifier] = calibration
        return {
            **_calibration_receipt_v3(calibration),
            "phase": "anchors_complete",
            "readyForComparison": True,
        }

    def compare(
        self,
        bridge_pid: int,
        calibration_id: str,
        reference_png_base64: str,
        reference_png_sha256: str,
    ) -> dict[str, object]:
        identifier = _calibration_id(calibration_id)
        calibration = self._calibrations.get(identifier)
        if calibration is None:
            raise CoatOfArmsFramebufferError("completed calibration is missing")
        if calibration.bridge_pid != bridge_pid:
            raise CoatOfArmsFramebufferError("native bridge PID differs from calibration")
        reference = decode_reference_png_v1(
            reference_png_base64, reference_png_sha256
        )
        framebuffer = capture_ck3_client_framebuffer_v1(bridge_pid)
        comparison = compare_reference_to_calibrated_framebuffer_v3(
            reference, framebuffer, calibration
        )
        return {
            "schema": "ck3-coat-of-arms-framebuffer-comparison-v3",
            "schemaVersion": 3,
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "captureBackend": "windows-imagegrab-authenticated-client-framebuffer",
            "bridgePid": bridge_pid,
            "framebuffer": {
                "width": framebuffer.width,
                "height": framebuffer.height,
                "pixelFormat": "RGB8",
                "pixelSha256": _sha256(framebuffer.tobytes()),
            },
            "reference": {
                "width": reference.width,
                "height": reference.height,
                "pngSha256": reference_png_sha256,
            },
            "calibration": _calibration_receipt_v3(calibration),
            "comparison": comparison,
            "readOnly": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }


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
