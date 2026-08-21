"""Serializable models for visible CK3 observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


Rect: TypeAlias = tuple[int, int, int, int]
RelativeRegion: TypeAlias = tuple[float, float, float, float]


@dataclass(frozen=True)
class OcrSpan:
    text: str
    normalized: str
    score: float
    center: tuple[int, int]
    bbox: Rect

    def to_json(self) -> dict[str, object]:
        return {
            "text": self.text,
            "normalized": self.normalized,
            "score": self.score,
            "center": list(self.center),
            "bbox": list(self.bbox),
        }


@dataclass(frozen=True)
class VisibleAnchor:
    anchor_id: str
    text: str
    score: float
    bbox: Rect
    center: tuple[int, int]

    def to_json(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "text": self.text,
            "score": self.score,
            "bbox": list(self.bbox),
            "center": list(self.center),
        }


@dataclass(frozen=True)
class VisibleControl:
    control_id: str
    label: str
    token: str
    bbox: Rect
    center: tuple[int, int]

    def to_json(self) -> dict[str, object]:
        return {
            "control_id": self.control_id,
            "label": self.label,
            "control_token": self.token,
            "bbox": list(self.bbox),
            "center": list(self.center),
        }


@dataclass(frozen=True)
class Observation:
    observation_id: str
    frame_id: str
    captured_at: str
    screen: str
    pid: int
    hwnd: int
    client_rect: Rect
    screenshot: str
    screenshot_sha256: str
    spans: tuple[OcrSpan, ...]
    anchors: tuple[VisibleAnchor, ...]
    controls: tuple[VisibleControl, ...] = ()
    confidence: float = 0.0
    unknown_reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_policy_json(self) -> dict[str, object]:
        return {
            "format_version": 2,
            "observation_id": self.observation_id,
            "frame_id": self.frame_id,
            "captured_at": self.captured_at,
            "screen": self.screen,
            "image": {
                "ref": f"frame:{self.frame_id}",
                "sha256": self.screenshot_sha256,
                "width": self.client_rect[2] - self.client_rect[0],
                "height": self.client_rect[3] - self.client_rect[1],
            },
            "ocr": [span.to_json() for span in self.spans],
            "visible_anchors": [anchor.to_json() for anchor in self.anchors],
            "visible_controls": [control.to_json() for control in self.controls],
            "visible_facts": {
                "screen": self.screen,
                "anchors": [anchor.anchor_id for anchor in self.anchors],
            },
            "confidence": self.confidence,
            "unknown_reasons": list(self.unknown_reasons),
            "policy_boundary": "player-visible pixels and OCR only",
        }

    def to_audit_json(self) -> dict[str, object]:
        return {
            "format_version": 2,
            "policy_observation": self.to_policy_json(),
            "private_audit": {
                "process": {"pid": self.pid, "hwnd": self.hwnd},
                "client_rect": list(self.client_rect),
                "screenshot_path": self.screenshot,
            },
        }
