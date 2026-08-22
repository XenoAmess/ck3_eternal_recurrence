"""Declarative multi-anchor screen classification and control contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
class PixelProbeSpec:
    probe_id: str
    rect: tuple[int, int, int, int]
    mean_rgb_min: tuple[float, float, float]
    mean_rgb_max: tuple[float, float, float]


@dataclass(frozen=True)
class PixelProbeProvenance:
    source_run_count: int
    source_run_ids_sha256: str
    source_artifact: str
    measurement: str
    lobby_source_run_count: int
    lobby_source_frame_count: int
    lobby_source_run_ids_sha256: str
    lobby_source_artifacts_sha256: str
    lobby_source_artifact: str
    lobby_measurement: str


@dataclass(frozen=True)
class ScreenSpec:
    screen_id: str
    anchors: tuple[AnchorSpec, ...]
    negative_anchors: tuple[AnchorSpec, ...] = ()
    pixel_probes: tuple[PixelProbeSpec, ...] = ()


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
    hover_tolerance_px: int = 3
    click_offset_px: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class UiContract:
    format_version: int
    game_version: str
    language: str
    resolution: tuple[int, int]
    screens: tuple[ScreenSpec, ...]
    controls: tuple[ControlSpec, ...]
    forbidden_capabilities: frozenset[str]
    pixel_probe_provenance: PixelProbeProvenance | None = None
    source_sha256: str = ""

    def classify(
        self, spans: tuple[OcrSpan, ...], image: object | None = None
    ) -> tuple[str, float, tuple[str, ...], tuple[VisibleAnchor, ...]]:
        matches: list[tuple[str, tuple[VisibleAnchor, ...]]] = []
        failures_by_screen: dict[str, list[str]] = {}
        for screen in self.screens:
            failures: list[str] = []
            evidence: list[VisibleAnchor] = []
            used_boxes: set[tuple[int, int, int, int]] = set()
            for blocker in screen.negative_anchors:
                found = matching_spans(
                    spans,
                    blocker.text,
                    self.resolution,
                    blocker.region,
                    contains=blocker.contains,
                )
                if found:
                    failures.append(
                        f"negative:{blocker.anchor_id}:matches={len(found)}"
                    )
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
            for probe in screen.pixel_probes:
                if image is None:
                    failures.append(f"pixel:{probe.probe_id}:image-missing")
                    continue
                size = tuple(getattr(image, "size", ()))
                crop_method = getattr(image, "crop", None)
                if size != self.resolution or not callable(crop_method):
                    failures.append(f"pixel:{probe.probe_id}:image-invalid")
                    continue
                from PIL import ImageStat

                crop = crop_method(probe.rect).convert("RGB")
                mean = tuple(float(value) for value in ImageStat.Stat(crop).mean)
                if any(
                    value < minimum or value > maximum
                    for value, minimum, maximum in zip(
                        mean, probe.mean_rgb_min, probe.mean_rgb_max
                    )
                ):
                    failures.append(
                        f"pixel:{probe.probe_id}:mean="
                        + ",".join(f"{value:.2f}" for value in mean)
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


def _anchor_list(raw: object, label: str, *, minimum: int) -> tuple[AnchorSpec, ...]:
    if not isinstance(raw, list) or len(raw) < minimum:
        raise AgentError(f"UI contract {label} has too few entries")
    anchors: list[AnchorSpec] = []
    for index, value in enumerate(raw):
        item = _object(value, f"{label}[{index}]")
        _keys(
            item,
            {"anchor_id", "text", "region"},
            {"contains"},
            f"{label}[{index}]",
        )
        anchors.append(
            AnchorSpec(
                anchor_id=_text(item["anchor_id"], "anchor_id"),
                text=_text(item["text"], "anchor text"),
                region=_region(item["region"]),
                contains=(
                    _flag(item["contains"], "anchor contains")
                    if "contains" in item
                    else False
                ),
            )
        )
    if len({item.anchor_id for item in anchors}) != len(anchors):
        raise AgentError(f"UI contract {label} has duplicate anchor IDs")
    return tuple(anchors)


def _pixel_rect(
    raw: object, resolution: tuple[int, int], label: str
) -> tuple[int, int, int, int]:
    if (
        not isinstance(raw, list)
        or len(raw) != 4
        or any(type(value) is not int for value in raw)
    ):
        raise AgentError(f"UI contract {label} rectangle is invalid")
    left, top, right, bottom = (int(value) for value in raw)
    if not (
        0 <= left < right <= resolution[0]
        and 0 <= top < bottom <= resolution[1]
    ):
        raise AgentError(f"UI contract {label} rectangle is out of bounds")
    return left, top, right, bottom


def _rgb_triplet(raw: object, label: str) -> tuple[float, float, float]:
    if (
        not isinstance(raw, list)
        or len(raw) != 3
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 <= float(value) <= 255
            for value in raw
        )
    ):
        raise AgentError(f"UI contract {label} RGB range is invalid")
    return tuple(float(value) for value in raw)  # type: ignore[return-value]


def _pixel_probes(
    raw: object, resolution: tuple[int, int], label: str
) -> tuple[PixelProbeSpec, ...]:
    if not isinstance(raw, list):
        raise AgentError(f"UI contract {label} must be an array")
    probes: list[PixelProbeSpec] = []
    for index, value in enumerate(raw):
        item = _object(value, f"{label}[{index}]")
        _keys(
            item,
            {"probe_id", "rect", "mean_rgb_min", "mean_rgb_max"},
            set(),
            f"{label}[{index}]",
        )
        minimum = _rgb_triplet(item["mean_rgb_min"], "mean_rgb_min")
        maximum = _rgb_triplet(item["mean_rgb_max"], "mean_rgb_max")
        if any(first > second for first, second in zip(minimum, maximum)):
            raise AgentError(f"UI contract {label}[{index}] RGB bounds are reversed")
        probes.append(
            PixelProbeSpec(
                probe_id=_text(item["probe_id"], "probe_id"),
                rect=_pixel_rect(item["rect"], resolution, "pixel probe"),
                mean_rgb_min=minimum,
                mean_rgb_max=maximum,
            )
        )
    if len({item.probe_id for item in probes}) != len(probes):
        raise AgentError(f"UI contract {label} has duplicate probe IDs")
    return tuple(probes)


def _valid_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return value == value.casefold()


def load_ui_contract(
    path: Path, *, expected_sha256: str | None = None
) -> UiContract:
    raw = path.read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and (
        not _valid_sha256(expected_sha256)
        or source_sha256 != expected_sha256
    ):
        raise AgentError("UI contract SHA-256 differs from the frozen environment")
    payload = _object(json.loads(raw.decode("utf-8")), "root")
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
            "pixel_probe_provenance",
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
    resolution = (int(resolution_raw[0]), int(resolution_raw[1]))
    provenance_raw = _object(
        payload["pixel_probe_provenance"], "pixel_probe_provenance"
    )
    _keys(
        provenance_raw,
        {
            "source_run_count",
            "source_run_ids_sha256",
            "source_artifact",
            "measurement",
            "lobby_source_run_count",
            "lobby_source_frame_count",
            "lobby_source_run_ids_sha256",
            "lobby_source_artifacts_sha256",
            "lobby_source_artifact",
            "lobby_measurement",
        },
        set(),
        "pixel_probe_provenance",
    )
    if (
        type(provenance_raw["source_run_count"]) is not int
        or int(provenance_raw["source_run_count"]) <= 0
        or not _valid_sha256(provenance_raw["source_run_ids_sha256"])
        or type(provenance_raw["lobby_source_run_count"]) is not int
        or int(provenance_raw["lobby_source_run_count"]) <= 0
        or type(provenance_raw["lobby_source_frame_count"]) is not int
        or int(provenance_raw["lobby_source_frame_count"]) <= 0
        or not _valid_sha256(provenance_raw["lobby_source_run_ids_sha256"])
        or not _valid_sha256(provenance_raw["lobby_source_artifacts_sha256"])
    ):
        raise AgentError("UI pixel-probe provenance differs")
    provenance = PixelProbeProvenance(
        source_run_count=int(provenance_raw["source_run_count"]),
        source_run_ids_sha256=str(provenance_raw["source_run_ids_sha256"]),
        source_artifact=_text(
            provenance_raw["source_artifact"], "source artifact"
        ),
        measurement=_text(provenance_raw["measurement"], "probe measurement"),
        lobby_source_run_count=int(provenance_raw["lobby_source_run_count"]),
        lobby_source_frame_count=int(provenance_raw["lobby_source_frame_count"]),
        lobby_source_run_ids_sha256=str(
            provenance_raw["lobby_source_run_ids_sha256"]
        ),
        lobby_source_artifacts_sha256=str(
            provenance_raw["lobby_source_artifacts_sha256"]
        ),
        lobby_source_artifact=_text(
            provenance_raw["lobby_source_artifact"], "lobby source artifact"
        ),
        lobby_measurement=_text(
            provenance_raw["lobby_measurement"], "lobby probe measurement"
        ),
    )
    screens_raw = payload["screens"]
    if not isinstance(screens_raw, list) or not screens_raw:
        raise AgentError("UI contract screens must be a non-empty array")
    screens_list: list[ScreenSpec] = []
    for screen_index, screen_value in enumerate(screens_raw):
        item = _object(screen_value, f"screen[{screen_index}]")
        _keys(
            item,
            {"screen_id", "anchors", "negative_anchors", "pixel_probes"},
            set(),
            f"screen[{screen_index}]",
        )
        screens_list.append(
            ScreenSpec(
                screen_id=_text(item["screen_id"], "screen_id"),
                anchors=_anchor_list(
                    item["anchors"], f"screen[{screen_index}].anchors", minimum=2
                ),
                negative_anchors=_anchor_list(
                    item["negative_anchors"],
                    f"screen[{screen_index}].negative_anchors",
                    minimum=0,
                ),
                pixel_probes=_pixel_probes(
                    item["pixel_probes"],
                    resolution,
                    f"screen[{screen_index}].pixel_probes",
                ),
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
            {"contains", "hover_tolerance_px", "click_offset_px"},
            f"control[{control_index}]",
        )
        hover_tolerance = item.get("hover_tolerance_px", 3)
        if type(hover_tolerance) is not int or not 0 <= hover_tolerance <= 15:
            raise AgentError("UI contract hover tolerance is invalid")
        click_offset_raw = item.get("click_offset_px", [0, 0])
        if (
            not isinstance(click_offset_raw, list)
            or len(click_offset_raw) != 2
            or any(
                type(value) is not int or abs(value) > 400
                for value in click_offset_raw
            )
        ):
            raise AgentError("UI contract click offset is invalid")
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
                hover_tolerance_px=hover_tolerance,
                click_offset_px=(
                    int(click_offset_raw[0]), int(click_offset_raw[1])
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
        or not 0 <= item.hover_tolerance_px <= 15
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
        resolution=resolution,
        screens=screens,
        controls=controls,
        forbidden_capabilities=forbidden,
        pixel_probe_provenance=provenance,
        source_sha256=source_sha256,
    )


_CANONICAL_PROVENANCE = PixelProbeProvenance(
    source_run_count=15,
    source_run_ids_sha256=(
        "6cd31810411218c5ac6787a121844d5113698520f1547ca3a8ef4b4ed27b18c3"
    ),
    source_artifact="runs/*/artifacts/main-menu.png",
    measurement="20x20 RGB arithmetic mean with frozen safety margins",
    lobby_source_run_count=190,
    lobby_source_frame_count=377,
    lobby_source_run_ids_sha256=(
        "48936aa1d19a50e7b8c3d26a8d86ea25f7ad023c42f205711766f0114acfaf0b"
    ),
    lobby_source_artifacts_sha256=(
        "56f09a76539e0e5f2642eeaab11c519d6d5e1c6866364cbf76b8feb345a1d66e"
    ),
    lobby_source_artifact="**/03_start_enabled.png + **/03_ruler_selected.png",
    lobby_measurement=(
        "20x20 RGB arithmetic mean across 377 stable lobby frames with +/-9 "
        "channel margins"
    ),
)

_CANONICAL_SCREENS = (
    ScreenSpec(
        "main_menu",
        (
            AnchorSpec("main.continue", "继续游戏", (0.18, 0.30, 0.30, 0.36)),
            AnchorSpec("main.new_game", "新游戏", (0.18, 0.36, 0.30, 0.42)),
            AnchorSpec("main.load", "载入游戏", (0.18, 0.42, 0.30, 0.48)),
        ),
        (
            AnchorSpec("modal.tutorial", "开始教程", (0.0, 0.0, 1.0, 1.0)),
            AnchorSpec("modal.confirm", "确认", (0.0, 0.0, 1.0, 1.0)),
            AnchorSpec("modal.cancel", "取消", (0.0, 0.0, 1.0, 1.0)),
            AnchorSpec(
                "modal.exit_question", "确定要退出游戏吗", (0.0, 0.0, 1.0, 1.0), True
            ),
        ),
        (
            PixelProbeSpec(
                "main.arch_edge", (700, 300, 720, 320), (60, 68, 74), (78, 84, 90)
            ),
            PixelProbeSpec(
                "main.logo_arch", (480, 180, 500, 200), (40, 41, 46), (58, 59, 64)
            ),
            PixelProbeSpec(
                "main.lower_stone",
                (680, 800, 700, 820),
                (27, 28, 30),
                (39, 40, 43),
            ),
            PixelProbeSpec(
                "main.new_game", (560, 540, 580, 560), (65, 55, 45), (95, 85, 75)
            ),
            PixelProbeSpec(
                "main.center_void", (1000, 600, 1020, 620), (0, 0, 0), (2, 2, 2)
            ),
        ),
    ),
    ScreenSpec(
        "bookmark_lobby",
        (
            AnchorSpec("lobby.title", "选择初始日期和角色", (0.08, 0.00, 0.32, 0.07)),
            AnchorSpec(
                "lobby.central_bookmark",
                "公爵弗拉季斯拉夫",
                (0.45, 0.20, 0.67, 0.47),
            ),
            AnchorSpec("lobby.robert", "公爵罗贝尔", (0.45, 0.68, 0.72, 0.91)),
        ),
        (
            AnchorSpec("modal.welcome", "欢迎来到", (0.0, 0.0, 1.0, 1.0), True),
            AnchorSpec("modal.confirm", "确认", (0.0, 0.0, 1.0, 1.0)),
            AnchorSpec("modal.cancel", "取消", (0.0, 0.0, 1.0, 1.0)),
        ),
        (
            PixelProbeSpec(
                "lobby.central_parchment",
                (1050, 350, 1070, 370),
                (178.1, 170.6, 154.2),
                (196.1, 188.6, 172.2),
            ),
            PixelProbeSpec(
                "lobby.southern_parchment",
                (950, 1000, 970, 1020),
                (174.0, 166.8, 151.7),
                (192.0, 184.8, 169.7),
            ),
            PixelProbeSpec(
                "lobby.eastern_parchment",
                (1200, 850, 1220, 870),
                (180.3, 172.9, 155.8),
                (198.3, 190.9, 173.8),
            ),
        ),
    ),
)

_CANONICAL_CONTROLS = (
    ControlSpec(
        "main_menu.new_game",
        "main_menu",
        "新游戏",
        "新游戏",
        (0.18, 0.36, 0.30, 0.42),
        "bookmark_lobby",
        "reversible",
    ),
)


def require_canonical_phase_b_contract(
    contract: UiContract, expected_sha256: str
) -> None:
    """Reject a hash-valid but semantically substituted Phase-B contract."""
    if (
        not _valid_sha256(expected_sha256)
        or contract.source_sha256 != expected_sha256
        or contract.format_version != 1
        or contract.game_version != "1.19.0.6"
        or contract.language != "l_simp_chinese"
        or contract.resolution != (2560, 1440)
        or contract.pixel_probe_provenance != _CANONICAL_PROVENANCE
        or contract.screens != _CANONICAL_SCREENS
        or contract.controls != _CANONICAL_CONTROLS
        or contract.forbidden_capabilities
        != frozenset({"bookmark_lobby.start_game"})
    ):
        raise AgentError("UI contract is not the exact canonical Phase-B contract")
