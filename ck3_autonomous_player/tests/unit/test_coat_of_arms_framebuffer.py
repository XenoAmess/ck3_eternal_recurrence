from __future__ import annotations

import base64
import hashlib
from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from xar_autoplayer.bridge.coat_of_arms_framebuffer import (
    CoatOfArmsFramebufferError,
    compare_reference_to_framebuffer_v1,
    decode_reference_png_v1,
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
