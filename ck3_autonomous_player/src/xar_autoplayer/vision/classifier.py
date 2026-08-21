"""Declarative multi-anchor screen classification and control contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .model import OcrSpan, RelativeRegion, VisibleAnchor
from .ocr import matching_spans
from ..errors import AgentError


@dataclass(frozen=True)
class AnchorSpec:
    anchor_id: str
    text: str
    region: RelativeRegion
    contains: bool = False


@dataclass(frozen=True)
class ScreenSpec:
    screen_id: str
    anchors: tuple[AnchorSpec, ...]


@dataclass(frozen=True)
class ControlSpec:
    control_id: str
    screen: str
    label: str
    text: str
    region: RelativeRegion
    post_screen: str
    risk: str
    contains: bool = False


@dataclass(frozen=True)
class UiContract:
    format_version: int
    game_version: str
    language: str
    resolution: tuple[int, int]
    screens: tuple[ScreenSpec, ...]
    controls: tuple[ControlSpec, ...]
    forbidden_capabilities: frozenset[str]

    def classify(
        self, spans: tuple[OcrSpan, ...]
    ) -> tuple[str, float, tuple[str, ...], tuple[VisibleAnchor, ...]]:
        matches: list[tuple[str, tuple[VisibleAnchor, ...]]] = []
        failures_by_screen: dict[str, list[str]] = {}
        for screen in self.screens:
            failures: list[str] = []
            evidence: list[VisibleAnchor] = []
            used_boxes: set[tuple[int, int, int, int]] = set()
            for anchor in screen.anchors:
                found = matching_spans(
                    spans,
                    anchor.text,
                    self.resolution,
                    anchor.region,
                    contains=anchor.contains,
                )
                if len(found) != 1:
                    failures.append(f"{anchor.anchor_id}:matches={len(found)}")
                    continue
                span = found[0]
                if span.bbox in used_boxes:
                    failures.append(
                        f"{anchor.anchor_id}:reuses-visible-span={span.bbox!r}"
                    )
                    continue
                used_boxes.add(span.bbox)
                evidence.append(
                    VisibleAnchor(
                        anchor_id=anchor.anchor_id,
                        text=span.text,
                        score=span.score,
                        bbox=span.bbox,
                        center=span.center,
                    )
                )
            if not failures and len(evidence) == len(screen.anchors):
                matches.append((screen.screen_id, tuple(evidence)))
            failures_by_screen[screen.screen_id] = failures
        if len(matches) == 1:
            screen_id, evidence = matches[0]
            confidence = round(
                sum(anchor.score for anchor in evidence) / len(evidence), 4
            )
            return screen_id, confidence, (), evidence
        if matches:
            return (
                "unknown",
                0.0,
                (f"ambiguous screens: {[item[0] for item in matches]!r}",),
                (),
            )
        summary = "; ".join(
            f"{screen}:failures={failures!r}"
            for screen, failures in failures_by_screen.items()
        )
        return "unknown", 0.0, (summary,), ()

    def controls_for(self, screen: str) -> tuple[ControlSpec, ...]:
        return tuple(item for item in self.controls if item.screen == screen)

    def control(self, control_id: str) -> ControlSpec:
        found = [item for item in self.controls if item.control_id == control_id]
        if len(found) != 1:
            raise AgentError(f"unregistered or ambiguous visible control: {control_id}")
        return found[0]


def _region(raw: object) -> RelativeRegion:
    if not isinstance(raw, list) or len(raw) != 4:
        raise AgentError(f"UI region is invalid: {raw!r}")
    region = tuple(float(value) for value in raw)
    left, top, right, bottom = region
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise AgentError(f"UI region is out of bounds: {region!r}")
    return region  # type: ignore[return-value]


def _object(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise AgentError(f"UI contract {label} is not an object")
    return raw


def _keys(
    raw: dict[str, object], required: set[str], optional: set[str], label: str
) -> None:
    actual = set(raw)
    if not required <= actual or actual - required - optional:
        raise AgentError(
            f"UI contract {label} fields differ: actual={sorted(actual)!r}"
        )


def _text(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > 120:
        raise AgentError(f"UI contract {label} text is invalid")
    return raw


def _flag(raw: object, label: str) -> bool:
    if type(raw) is not bool:
        raise AgentError(f"UI contract {label} must be a boolean")
    return raw


def load_ui_contract(path: Path) -> UiContract:
    payload = _object(json.loads(path.read_text(encoding="utf-8")), "root")
    _keys(
        payload,
        {
            "format_version",
            "game_version",
            "language",
            "resolution",
            "screens",
            "controls",
            "forbidden_capabilities",
        },
        set(),
        "root",
    )
    if payload.get("format_version") != 1:
        raise AgentError("unsupported UI contract version")
    resolution_raw = payload["resolution"]
    if (
        not isinstance(resolution_raw, list)
        or len(resolution_raw) != 2
        or any(type(value) is not int or value <= 0 for value in resolution_raw)
    ):
        raise AgentError("UI contract resolution is invalid")
    screens_raw = payload["screens"]
    if not isinstance(screens_raw, list) or not screens_raw:
        raise AgentError("UI contract screens must be a non-empty array")
    screens_list: list[ScreenSpec] = []
    for screen_index, screen_value in enumerate(screens_raw):
        item = _object(screen_value, f"screen[{screen_index}]")
        _keys(item, {"screen_id", "anchors"}, set(), f"screen[{screen_index}]")
        anchors_raw = item["anchors"]
        if not isinstance(anchors_raw, list) or len(anchors_raw) < 2:
            raise AgentError("every screen requires at least two independent anchors")
        anchors: list[AnchorSpec] = []
        for anchor_index, anchor_value in enumerate(anchors_raw):
            anchor = _object(
                anchor_value, f"screen[{screen_index}].anchor[{anchor_index}]"
            )
            _keys(
                anchor,
                {"anchor_id", "text", "region"},
                {"contains"},
                f"screen[{screen_index}].anchor[{anchor_index}]",
            )
            anchors.append(
                AnchorSpec(
                    anchor_id=_text(anchor["anchor_id"], "anchor_id"),
                    text=_text(anchor["text"], "anchor text"),
                    region=_region(anchor["region"]),
                    contains=(
                        _flag(anchor["contains"], "anchor contains")
                        if "contains" in anchor
                        else False
                    ),
                )
            )
        if len({item.anchor_id for item in anchors}) != len(anchors):
            raise AgentError("UI contract has duplicate anchor IDs within a screen")
        screens_list.append(
            ScreenSpec(
                screen_id=_text(item["screen_id"], "screen_id"),
                anchors=tuple(anchors),
            )
        )
    screens = tuple(screens_list)
    screen_ids = {item.screen_id for item in screens}
    if len(screen_ids) != len(screens):
        raise AgentError("UI contract has duplicate screen IDs")

    controls_raw = payload["controls"]
    if not isinstance(controls_raw, list):
        raise AgentError("UI contract controls must be an array")
    controls_list: list[ControlSpec] = []
    for control_index, control_value in enumerate(controls_raw):
        item = _object(control_value, f"control[{control_index}]")
        _keys(
            item,
            {
                "control_id",
                "screen",
                "label",
                "text",
                "region",
                "post_screen",
                "risk",
            },
            {"contains"},
            f"control[{control_index}]",
        )
        controls_list.append(
            ControlSpec(
                control_id=_text(item["control_id"], "control_id"),
                screen=_text(item["screen"], "control screen"),
                label=_text(item["label"], "control label"),
                text=_text(item["text"], "control text"),
                region=_region(item["region"]),
                post_screen=_text(item["post_screen"], "post_screen"),
                risk=_text(item["risk"], "control risk"),
                contains=(
                    _flag(item["contains"], "control contains")
                    if "contains" in item
                    else False
                ),
            )
        )
    controls = tuple(controls_list)
    ids = [item.control_id for item in controls]
    if len(set(ids)) != len(ids):
        raise AgentError("UI contract has duplicate control IDs")
    if any(
        item.screen not in screen_ids
        or item.post_screen not in screen_ids
        or item.risk not in {"reversible", "irreversible"}
        for item in controls
    ):
        raise AgentError("UI contract control references or risk differ")
    forbidden_raw = payload["forbidden_capabilities"]
    if (
        not isinstance(forbidden_raw, list)
        or any(not isinstance(value, str) or not value for value in forbidden_raw)
        or len(set(forbidden_raw)) != len(forbidden_raw)
    ):
        raise AgentError("UI contract forbidden capabilities are invalid")
    forbidden = frozenset(forbidden_raw)
    if forbidden & set(ids):
        raise AgentError("UI contract registers a forbidden capability")
    return UiContract(
        format_version=1,
        game_version=_text(payload["game_version"], "game_version"),
        language=_text(payload["language"], "language"),
        resolution=(int(resolution_raw[0]), int(resolution_raw[1])),
        screens=screens,
        controls=controls,
        forbidden_capabilities=forbidden,
    )
