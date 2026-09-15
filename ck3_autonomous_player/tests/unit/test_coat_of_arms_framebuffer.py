from __future__ import annotations

import base64
import hashlib
from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from xar_autoplayer.bridge.coat_of_arms_framebuffer import (
    CoatOfArmsFramebufferError,
    compare_reference_to_calibrated_framebuffer_v2,
    compare_reference_to_framebuffer_v1,
    decode_reference_png_v1,
    derive_two_state_calibration_v2,
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
