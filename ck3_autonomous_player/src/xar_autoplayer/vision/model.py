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
    capture_sequence: int = 0
    captured_monotonic: float = 0.0
    audit_path: str = ""

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
                "observation_path": self.audit_path,
                "capture_sequence": self.capture_sequence,
                "captured_monotonic": self.captured_monotonic,
            },
        }


@dataclass(frozen=True)
class StableObservation:
    """Exactly two consecutive observations accepted as one visible state."""

    expected_screen: str
    frames: tuple[Observation, Observation]

    def __post_init__(self) -> None:
        first, second = self.frames
        if (
            first.screen != self.expected_screen
            or second.screen != self.expected_screen
            or first.capture_sequence <= 0
            or second.capture_sequence != first.capture_sequence + 1
            or first.captured_monotonic < 0
            or second.captured_monotonic <= first.captured_monotonic
        ):
            raise ValueError("stable observations must be two consecutive ordered frames")

    @property
    def latest(self) -> Observation:
        return self.frames[1]

    @property
    def screen(self) -> str:
        return self.latest.screen

    @property
    def observation_id(self) -> str:
        return self.latest.observation_id

    @property
    def frame_id(self) -> str:
        return self.latest.frame_id

    @property
    def controls(self) -> tuple[VisibleControl, ...]:
        return self.latest.controls

    @staticmethod
    def _frame_policy_evidence(frame: Observation) -> dict[str, object]:
        return {
            "observation_id": frame.observation_id,
            "frame_id": frame.frame_id,
            "captured_at": frame.captured_at,
            "capture_sequence": frame.capture_sequence,
            "captured_monotonic": frame.captured_monotonic,
            "screenshot_sha256": frame.screenshot_sha256,
        }

    @staticmethod
    def _frame_audit_evidence(frame: Observation) -> dict[str, object]:
        return {
            **StableObservation._frame_policy_evidence(frame),
            "screenshot": frame.screenshot,
            "observation": frame.audit_path,
            "pid": frame.pid,
            "hwnd": frame.hwnd,
            "client_rect": list(frame.client_rect),
        }

    def to_policy_json(self) -> dict[str, object]:
        payload = self.latest.to_policy_json()
        payload["stability"] = {
            "stable_frames": 2,
            "expected_screen": self.expected_screen,
            "frames": [self._frame_policy_evidence(frame) for frame in self.frames],
            "monotonic_delta": (
                self.frames[1].captured_monotonic
                - self.frames[0].captured_monotonic
            ),
        }
        return payload

    def to_audit_evidence(self) -> dict[str, object]:
        return {
            "stable_frames": 2,
            "expected_screen": self.expected_screen,
            "frames": [self._frame_audit_evidence(frame) for frame in self.frames],
            "monotonic_delta": (
                self.frames[1].captured_monotonic
                - self.frames[0].captured_monotonic
            ),
        }
