"""Lazy RapidOCR adapter with client-relative bounding boxes."""

from __future__ import annotations

import re
import unicodedata

from .model import OcrSpan, RelativeRegion, Rect


CUDA_EXECUTION_PROVIDER = "CUDAExecutionProvider"
CUDA_DEVICE_ID = "0"
_CUDA_PROVIDER = (
    CUDA_EXECUTION_PROVIDER,
    {
        "device_id": CUDA_DEVICE_ID,
        "arena_extend_strategy": "kNextPowerOfTwo",
        "cudnn_conv_algo_search": "EXHAUSTIVE",
        "do_copy_in_default_stream": "1",
    },
)


def rapidocr_engine() -> object:
    """Return the process-wide RapidOCR engine backed by NVIDIA CUDA device 0."""
    if hasattr(rapidocr_engine, "engine"):
        return rapidocr_engine.engine  # type: ignore[attr-defined]

    import onnxruntime as ort
    from rapidocr_onnxruntime import RapidOCR

    ort.set_default_logger_severity(4)
    ort.preload_dlls(directory="")
    available = tuple(ort.get_available_providers())
    if ort.get_device() != "GPU" or CUDA_EXECUTION_PROVIDER not in available:
        raise RuntimeError(
            "NVIDIA CUDA OCR is unavailable; "
            f"device={ort.get_device()!r}, providers={available!r}"
        )

    # rapidocr-onnxruntime 1.2.3 wires its detector CUDA flag correctly, but
    # leaves the classifier and recognizer on CPU. Move all three frozen model
    # sessions to CUDA explicitly after construction.
    engine = RapidOCR(det_use_cuda=True, det_model_path=None)
    sessions = {
        "detector": engine.text_detector.infer.session,
        "classifier": engine.text_cls.infer.session,
        "recognizer": engine.text_recognizer.session.session,
    }
    for name, session in sessions.items():
        session.set_providers([_CUDA_PROVIDER, "CPUExecutionProvider"])
        if (
            not session.get_providers()
            or session.get_providers()[0] != CUDA_EXECUTION_PROVIDER
        ):
            raise RuntimeError(
                f"RapidOCR {name} did not select NVIDIA CUDA device {CUDA_DEVICE_ID}: "
                f"{session.get_providers()!r}"
            )
    rapidocr_engine.engine = engine  # type: ignore[attr-defined]
    rapidocr_engine.sessions = sessions  # type: ignore[attr-defined]
    return engine


def rapidocr_runtime() -> dict[str, object]:
    """Initialize OCR and report the execution provider used by each model."""
    rapidocr_engine()
    sessions = rapidocr_engine.sessions  # type: ignore[attr-defined]
    return {
        "device": "NVIDIA CUDA",
        "device_id": int(CUDA_DEVICE_ID),
        "models": {
            name: session.get_providers()[0]
            for name, session in sessions.items()
        },
    }


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
    crop = region_bbox(image.size, region)
    result, _ = rapidocr_engine()(np.asarray(image.crop(crop)))
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
