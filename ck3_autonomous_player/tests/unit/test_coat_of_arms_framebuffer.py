from __future__ import annotations

import base64
import ctypes
import hashlib
from io import BytesIO
from unittest.mock import Mock

from PIL import Image, ImageDraw
import numpy as np
import pytest
import win32api
import win32gui
import win32process

from xar_autoplayer.bridge.coat_of_arms_framebuffer import (
    CoatOfArmsFramebufferError,
    capture_calibrated_framebuffer_v3,
    compare_reference_to_calibrated_framebuffer_v2,
    compare_reference_to_calibrated_framebuffer_v3,
    compare_reference_to_framebuffer_v1,
    decode_reference_png_v1,
    derive_anchor_calibration_v3,
    derive_two_state_calibration_v2,
    prepare_ck3_framebuffer_capture_v1,
)


def _reference() -> Image.Image:
    image = Image.new("RGB", (64, 64), (22, 31, 49))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 7, 42, 41), fill=(232, 51, 73))
    draw.polygon(((19, 55), (33, 18), (55, 53)), fill=(35, 219, 144))
    draw.rectangle((4, 12, 11, 58), fill=(246, 218, 67))
    return image


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_decodes_only_hash_bound_bounded_square_png() -> None:
    raw = _png(_reference())
    digest = hashlib.sha256(raw).hexdigest().upper()
    decoded = decode_reference_png_v1(base64.b64encode(raw).decode("ascii"), digest)
    assert decoded.size == (64, 64)
    with pytest.raises(CoatOfArmsFramebufferError, match="SHA-256 mismatch"):
        decode_reference_png_v1(base64.b64encode(raw).decode("ascii"), "0" * 64)
    oversized = _png(Image.new("RGB", (513, 513), (0, 0, 0)))
    with pytest.raises(CoatOfArmsFramebufferError, match="bounded square"):
        decode_reference_png_v1(
            base64.b64encode(oversized).decode("ascii"),
            hashlib.sha256(oversized).hexdigest().upper(),
        )


def test_foreground_preparation_falls_back_after_direct_win32_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from xar_autoplayer.vision import window

    client_rect = (0, 0, 2560, 1440)
    monkeypatch.setattr(window, "_eligible_windows", lambda _pid: [(100, client_rect)])
    monkeypatch.setattr(window, "_root_window", lambda hwnd: hwnd)
    foreground = iter((200, 200, 100))
    monkeypatch.setattr(win32gui, "GetForegroundWindow", lambda: next(foreground))
    monkeypatch.setattr(win32gui, "ShowWindow", Mock())
    monkeypatch.setattr(win32gui, "BringWindowToTop", Mock())
    monkeypatch.setattr(win32gui, "SetActiveWindow", Mock())
    set_foreground = Mock(side_effect=(RuntimeError("access denied"), None))
    monkeypatch.setattr(win32gui, "SetForegroundWindow", set_foreground)
    monkeypatch.setattr(win32api, "GetCurrentThreadId", lambda: 10)
    monkeypatch.setattr(
        win32process,
        "GetWindowThreadProcessId",
        lambda hwnd: ((20, 999) if hwnd == 200 else (30, 1234)),
    )
    user32 = Mock()
    user32.AttachThreadInput.side_effect = (True, True, True, True)
    monkeypatch.setattr(ctypes, "WinDLL", lambda *_args, **_kwargs: user32)

    result = prepare_ck3_framebuffer_capture_v1(1234)

    assert result["foregroundRootBefore"] == 200
    assert result["foregroundRootAfter"] == 100
    assert result["mode"] == "attached_foreground_thread"
    assert result["detachSucceeded"] is True
    assert result["attachedForegroundThread"] == 20
    assert result["attachedTargetThread"] == 30
    assert result["directActivationError"].startswith("RuntimeError:")
    assert result["attachedActivationError"] is None
    assert set_foreground.call_count == 2


def test_locates_reference_over_the_whole_frame_without_fixed_coordinates() -> None:
    reference = _reference()
    framebuffer = Image.new("RGB", (420, 300), (91, 83, 76))
    side = 128
    location = (173, 91)
    framebuffer.paste(
        reference.resize((side, side), Image.Resampling.BILINEAR),
        location,
    )
    result = compare_reference_to_framebuffer_v1(
        reference,
        framebuffer,
        search_sides=(128,),
    )
    match = result["bestMatch"]
    assert match["rect"] == [173, 91, 301, 219]
    assert match["distinctMargin"] > 0
    assert result["searchedWholeFramebuffer"] is True
    assert result["fixedScreenCoordinatesUsed"] is False
    metrics = result["metrics"]
    # The synthetic observation is resized up and down once, so the metric is
    # deliberately bounded above zero while the globally located rect is exact.
    assert metrics["meanAbsoluteError"] < 0.02
    assert metrics["colorMse"] < 0.002
    assert metrics["edgeLoss"] < 0.08
    assert len(metrics["spatialMeanAbsoluteError8x8"]) == 8


def test_aligns_content_inside_native_decorative_frame() -> None:
    reference = _reference()
    framebuffer = Image.new("RGB", (420, 300), (91, 83, 76))
    outer = Image.new("RGB", (128, 128), (49, 35, 31))
    outer.paste(
        reference.resize((112, 112), Image.Resampling.BILINEAR),
        (8, 8),
    )
    framebuffer.paste(outer, (173, 91))

    result = compare_reference_to_framebuffer_v1(
        reference,
        framebuffer,
        search_sides=(128,),
    )

    alignment = result["bestMatch"]["alignment"]
    assert 0.84 <= alignment["contentToOuterRatio"] <= 0.93
    assert result["metrics"]["meanAbsoluteError"] < 0.04
    assert result["metrics"]["colorMse"] < 0.02


def test_two_state_calibration_selects_largest_reference_independent_surface() -> None:
    begin = Image.new("RGB", (420, 300), (31, 29, 27))
    complete = begin.copy()
    begin_draw = ImageDraw.Draw(begin)
    complete_draw = ImageDraw.Draw(complete)
    begin_draw.ellipse((30, 30, 93, 93), fill=(240, 20, 20))
    complete_draw.ellipse((30, 30, 93, 93), fill=(20, 240, 20))
    begin_draw.polygon(((170, 40), (300, 40), (280, 220), (235, 270), (190, 220)), fill=(240, 20, 20))
    complete_draw.polygon(((170, 40), (300, 40), (280, 220), (235, 270), (190, 220)), fill=(20, 240, 20))

    calibration = derive_two_state_calibration_v2(
        "fixture-1", 1234, begin, complete
    )

    assert calibration.rect == (170, 40, 301, 270)
    assert calibration.component_count == 2
    assert calibration.selected_pixels > 20_000


def test_calibrated_comparison_never_relocalizes_from_reference() -> None:
    reference = _reference()
    begin = Image.new("RGB", (420, 300), (31, 29, 27))
    complete = begin.copy()
    begin_draw = ImageDraw.Draw(begin)
    complete_draw = ImageDraw.Draw(complete)
    surface = ((170, 40), (300, 40), (280, 220), (235, 270), (190, 220))
    begin_draw.polygon(surface, fill=(240, 20, 20))
    complete_draw.polygon(surface, fill=(20, 240, 20))
    calibration = derive_two_state_calibration_v2(
        "fixture-2", 1234, begin, complete
    )
    observed = Image.new("RGB", begin.size, (31, 29, 27))
    observed.paste(
        reference.resize((131, 230), Image.Resampling.BILINEAR),
        (170, 40),
    )
    # Place a second exact copy elsewhere. A reference-driven global search
    # would choose this decoy; v2 must retain the calibrated rectangle.
    observed.paste(reference, (20, 180))

    result = compare_reference_to_calibrated_framebuffer_v2(
        reference, observed, calibration
    )

    assert result["referenceUsedForLocalization"] is False
    assert result["bestMatch"]["rect"] == [170, 40, 301, 270]
    assert result["metrics"]["meanAbsoluteError"] < 0.03
    aligned = Image.open(
        BytesIO(
            base64.b64decode(result["bestMatch"]["alignedContentPngBase64"])
        )
    )
    assert aligned.mode == "RGBA"
    assert aligned.getpixel((0, aligned.height - 1))[3] == 0


def test_anchor_calibration_removes_native_frame_geometry_from_uv_comparison() -> None:
    reference = _reference()
    size = (420, 300)
    background = (31, 29, 27)
    surface = ((60, 30), (260, 30), (260, 190), (160, 250), (60, 190))
    begin = Image.new("RGB", size, background)
    complete = begin.copy()
    ImageDraw.Draw(begin).polygon(surface, fill=(240, 20, 20))
    ImageDraw.Draw(complete).polygon(surface, fill=(20, 240, 20))
    surface_calibration = derive_two_state_calibration_v2(
        "fixture-uv", 1234, begin, complete
    )

    anchor_base = Image.new("RGB", size, background)
    ImageDraw.Draw(anchor_base).polygon(surface, fill=(8, 8, 8))
    anchors_complete = anchor_base.copy()
    anchor_draw = ImageDraw.Draw(anchors_complete)
    for normalized_y in (0.30, 0.50, 0.70):
        for normalized_x in (0.30, 0.50, 0.70):
            center_x = round(60 + normalized_x * 200)
            center_y = round(30 + normalized_y * 220)
            anchor_draw.rectangle(
                (center_x - 4, center_y - 4, center_x + 4, center_y + 4),
                fill=(245, 245, 245),
            )
    calibration = derive_anchor_calibration_v3(
        surface_calibration, anchor_base, anchors_complete
    )

    np.testing.assert_allclose(
        calibration.canonical_to_framebuffer,
        np.asarray(((200.0, 0.0, 60.0), (0.0, 220.0, 30.0))),
        atol=0.75,
    )
    assert max(calibration.reprojection_errors) < 0.75

    observed = Image.new("RGB", size, background)
    resized = reference.resize((201, 221), Image.Resampling.BILINEAR)
    surface_mask = Image.new("L", size, 0)
    ImageDraw.Draw(surface_mask).polygon(surface, fill=255)
    layer = Image.new("RGB", size, background)
    layer.paste(resized, (60, 30))
    observed.paste(layer, mask=surface_mask)

    result = compare_reference_to_calibrated_framebuffer_v3(
        reference, observed, calibration
    )

    assert result["referenceUsedForLocalization"] is False
    assert result["referenceUsedForRegistration"] is False
    assert result["bestMatch"]["rect"] == [60, 30, 261, 250]
    assert result["metrics"]["meanAbsoluteError"] < 0.025
    assert result["metrics"]["colorMse"] < 0.003

    capture = capture_calibrated_framebuffer_v3(
        observed, calibration, side=64
    )
    assert capture["referenceImageAccepted"] is False
    assert capture["referenceUsedForLocalization"] is False
    assert capture["referenceUsedForRegistration"] is False
    assert capture["captureSide"] == 64
    assert capture["rect"] == [60, 30, 261, 250]
    aligned = Image.open(
        BytesIO(base64.b64decode(capture["alignedContentPngBase64"]))
    )
    assert aligned.size == (64, 64)
    assert aligned.mode == "RGBA"
    assert hashlib.sha256(
        base64.b64decode(capture["alignedContentPngBase64"])
    ).hexdigest().upper() == capture["alignedContentPngSha256"]
    with pytest.raises(CoatOfArmsFramebufferError, match="bounded range"):
        capture_calibrated_framebuffer_v3(observed, calibration, side=10_000)
