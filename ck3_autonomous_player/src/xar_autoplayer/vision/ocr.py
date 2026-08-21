"""Lazy RapidOCR adapter with client-relative bounding boxes."""

from __future__ import annotations

import re
import unicodedata

from .model import OcrSpan, RelativeRegion, Rect


def normalize_visible_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("：", ":")
    return re.sub(r"\s+", "", normalized).casefold()


def region_bbox(
    size: tuple[int, int], region: RelativeRegion
) -> Rect:
    width, height = size
    left, top, right, bottom = region
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError(f"invalid relative region: {region!r}")
    return (
        int(width * left),
        int(height * top),
        int(width * right),
        int(height * bottom),
    )


def point_in_region(
    point: tuple[int, int], size: tuple[int, int], region: RelativeRegion
) -> bool:
    left, top, right, bottom = region_bbox(size, region)
    return left <= point[0] <= right and top <= point[1] <= bottom


def ocr_spans(
    image: object,
    region: RelativeRegion = (0.0, 0.0, 1.0, 1.0),
    *,
    minimum_score: float = 0.45,
) -> tuple[OcrSpan, ...]:
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    if not hasattr(ocr_spans, "engine"):
        ocr_spans.engine = RapidOCR()  # type: ignore[attr-defined]
    crop = region_bbox(image.size, region)
    result, _ = ocr_spans.engine(  # type: ignore[attr-defined]
        np.asarray(image.crop(crop))
    )
    spans: list[OcrSpan] = []
    for box, text, score in result or []:
        score = float(score)
        text = str(text).strip()
        if not text or score < minimum_score:
            continue
        xs = [int(point[0] + crop[0]) for point in box]
        ys = [int(point[1] + crop[1]) for point in box]
        spans.append(
            OcrSpan(
                text=text,
                normalized=normalize_visible_text(text),
                score=round(score, 4),
                center=(int(sum(xs) / len(xs)), int(sum(ys) / len(ys))),
                bbox=(min(xs), min(ys), max(xs), max(ys)),
            )
        )
    return tuple(spans)


def matching_spans(
    spans: tuple[OcrSpan, ...],
    text: str,
    size: tuple[int, int],
    region: RelativeRegion,
    *,
    contains: bool = False,
) -> list[OcrSpan]:
    target = normalize_visible_text(text)
    matches = []
    for span in spans:
        if not point_in_region(span.center, size, region):
            continue
        if (target in span.normalized) if contains else (target == span.normalized):
            matches.append(span)
    return matches

