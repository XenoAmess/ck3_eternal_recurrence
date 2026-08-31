"""Strict, deterministic Advanced SubStation Alpha subtitle generation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
import re
import unicodedata
from typing import Collection, Sequence

from .errors import PromoToolchainError


_ASS_COLOR = re.compile(r"^&H[0-9A-Fa-f]{8}$")
_FIELD_IDENTIFIER = re.compile(r"^[^,\r\n\x00-\x1f\x7f]+$")
_TRACK_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MATRIX_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_CENTISECONDS = 35_999_999  # 99:59:59.99


class SubtitleError(PromoToolchainError):
    """Subtitle data cannot be rendered without violating its contract."""


@dataclass(frozen=True)
class AssDocumentConfig:
    title: str
    play_res_x: int
    play_res_y: int
    duration_seconds: int | float | Decimal | None = None
    wrap_style: int = 2
    cue_wrap_style: int | None = 2
    scaled_border_and_shadow: bool = True
    ycbcr_matrix: str = "TV.709"

    def __post_init__(self) -> None:
        _safe_header_value(self.title, "ASS title")
        _positive_integer(self.play_res_x, "PlayResX")
        _positive_integer(self.play_res_y, "PlayResY")
        if self.duration_seconds is not None:
            duration = _centiseconds(self.duration_seconds, "document duration")
            if duration <= 0:
                raise SubtitleError("document duration must be greater than zero")
        _integer_in_range(self.wrap_style, "WrapStyle", 0, 3)
        if self.cue_wrap_style is not None:
            _integer_in_range(self.cue_wrap_style, "cue_wrap_style", 0, 3)
        if not isinstance(self.scaled_border_and_shadow, bool):
            raise SubtitleError("scaled_border_and_shadow must be a boolean")
        if not isinstance(self.ycbcr_matrix, str) or _MATRIX_IDENTIFIER.fullmatch(
            self.ycbcr_matrix
        ) is None:
            raise SubtitleError("YCbCr matrix must be a safe ASS identifier")


@dataclass(frozen=True)
class AssStyleConfig:
    name: str
    font_name: str
    font_size: int | float
    primary_colour: str = "&H00FFFFFF"
    secondary_colour: str = "&H000000FF"
    outline_colour: str = "&H00101018"
    back_colour: str = "&H78081018"
    bold: bool = True
    italic: bool = False
    underline: bool = False
    strike_out: bool = False
    scale_x: int | float = 100
    scale_y: int | float = 100
    spacing: int | float = 0
    angle: int | float = 0
    border_style: int = 1
    outline: int | float = 3
    shadow: int | float = 1
    alignment: int = 2
    margin_left: int = 0
    margin_right: int = 0
    margin_vertical: int = 0
    encoding: int = 1

    def __post_init__(self) -> None:
        _safe_ass_field(self.name, "style name")
        _safe_ass_field(self.font_name, "font name")
        _positive_number(self.font_size, "font size")
        for label, colour in (
            ("primary_colour", self.primary_colour),
            ("secondary_colour", self.secondary_colour),
            ("outline_colour", self.outline_colour),
            ("back_colour", self.back_colour),
        ):
            if not isinstance(colour, str) or _ASS_COLOR.fullmatch(colour) is None:
                raise SubtitleError(f"{label} must use &HAABBGGRR format")
        for label, value in (
            ("bold", self.bold),
            ("italic", self.italic),
            ("underline", self.underline),
            ("strike_out", self.strike_out),
        ):
            if not isinstance(value, bool):
                raise SubtitleError(f"{label} must be a boolean")
        _positive_number(self.scale_x, "ScaleX")
        _positive_number(self.scale_y, "ScaleY")
        _finite_number(self.spacing, "Spacing")
        _finite_number(self.angle, "Angle")
        if self.border_style not in {1, 3}:
            raise SubtitleError("BorderStyle must be 1 or 3")
        _nonnegative_number(self.outline, "Outline")
        _nonnegative_number(self.shadow, "Shadow")
        _integer_in_range(self.alignment, "Alignment", 1, 9)
        _nonnegative_integer(self.margin_left, "MarginL")
        _nonnegative_integer(self.margin_right, "MarginR")
        _nonnegative_integer(self.margin_vertical, "MarginV")
        _nonnegative_integer(self.encoding, "Encoding")


@dataclass(frozen=True)
class SubtitleTrackConfig:
    """One independently configurable subtitle track.

    ``locale`` is opaque metadata.  Neither locale nor track id influences
    style, layout, layer, ordering, or voice selection.
    """

    track_id: str
    locale: str
    layer: int
    style: AssStyleConfig

    def __post_init__(self) -> None:
        _track_identifier(self.track_id, "track id")
        _safe_ass_field(self.locale, "track locale")
        _nonnegative_integer(self.layer, "track layer")
        if not isinstance(self.style, AssStyleConfig):
            raise SubtitleError("track style must be an AssStyleConfig")


@dataclass(frozen=True)
class AssCue:
    cue_id: str
    track_id: str
    start_seconds: int | float | Decimal
    end_seconds: int | float | Decimal
    text: str

    def __post_init__(self) -> None:
        _track_identifier(self.cue_id, "cue id")
        _track_identifier(self.track_id, "cue track id")
        start = _centiseconds(self.start_seconds, f"cue {self.cue_id} start")
        end = _centiseconds(self.end_seconds, f"cue {self.cue_id} end")
        if end <= start:
            raise SubtitleError(
                f"cue {self.cue_id!r} must remain positive after centisecond rounding"
            )
        if not isinstance(self.text, str) or not self.text.strip():
            raise SubtitleError(f"cue {self.cue_id!r} text must be renderable")
        # Validate now rather than discovering an unsupported control character
        # halfway through document generation.
        ass_escape(self.text)


def ass_timestamp(seconds: int | float | Decimal) -> str:
    """Convert a strict non-negative time to ``H:MM:SS.cc``.

    Centiseconds use decimal half-up rounding.  This avoids platform-dependent
    binary floating-point edge behavior and Python's banker rounding.
    """

    centiseconds = _centiseconds(seconds, "ASS timestamp")
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def ass_escape(text: str) -> str:
    """Escape plain text for the final ASS event field.

    Newlines become explicit ASS line breaks and tabs become hard spaces.
    Other control characters and surrogate code points fail closed.
    """

    if not isinstance(text, str):
        raise SubtitleError("ASS text must be a string")
    escaped: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\r":
            if index + 1 < len(text) and text[index + 1] == "\n":
                index += 1
            escaped.append(r"\N")
        elif char == "\n":
            escaped.append(r"\N")
        elif char == "\t":
            escaped.append(r"\h")
        elif char == "\\":
            escaped.append(r"\\")
        elif char == "{":
            escaped.append(r"\{")
        elif char == "}":
            escaped.append(r"\}")
        elif unicodedata.category(char) in {"Cc", "Cs", "Zl", "Zp"}:
            raise SubtitleError("ASS text contains an unsupported control character")
        else:
            escaped.append(char)
        index += 1
    return "".join(escaped)


def render_ass_document(
    config: AssDocumentConfig,
    tracks: Sequence[SubtitleTrackConfig],
    cues: Sequence[AssCue],
    *,
    available_font_names: Collection[str],
) -> str:
    """Render a deterministic ASS document after full contract validation."""

    if not isinstance(config, AssDocumentConfig):
        raise SubtitleError("config must be an AssDocumentConfig")
    try:
        configured_tracks = tuple(tracks)
    except TypeError as exc:
        raise SubtitleError("tracks must be a sequence") from exc
    try:
        configured_cues = tuple(cues)
    except TypeError as exc:
        raise SubtitleError("cues must be a sequence") from exc
    if not configured_tracks:
        raise SubtitleError("at least one subtitle track must be configured")
    if not configured_cues:
        raise SubtitleError("at least one subtitle cue is required")
    if any(not isinstance(track, SubtitleTrackConfig) for track in configured_tracks):
        raise SubtitleError("tracks must contain SubtitleTrackConfig values")
    if any(not isinstance(cue, AssCue) for cue in configured_cues):
        raise SubtitleError("cues must contain AssCue values")

    track_by_id: dict[str, SubtitleTrackConfig] = {}
    style_by_name: dict[str, AssStyleConfig] = {}
    for track in configured_tracks:
        if track.track_id in track_by_id:
            raise SubtitleError(f"duplicate subtitle track id {track.track_id!r}")
        track_by_id[track.track_id] = track
        style_key = track.style.name.casefold()
        existing_style = style_by_name.get(style_key)
        if existing_style is not None and existing_style != track.style:
            raise SubtitleError(
                f"style name {track.style.name!r} has conflicting definitions"
            )
        style_by_name[style_key] = track.style
        _validate_style_bounds(track.style, config)

    available = _available_fonts(available_font_names)
    for style in style_by_name.values():
        if style.font_name.casefold() not in available:
            raise SubtitleError(
                f"required font {style.font_name!r} is not in the resolved font set"
            )

    cue_ids: set[str] = set()
    normalized: list[tuple[int, int, AssCue, SubtitleTrackConfig]] = []
    duration = (
        None
        if config.duration_seconds is None
        else _centiseconds(config.duration_seconds, "document duration")
    )
    for cue in configured_cues:
        if cue.cue_id in cue_ids:
            raise SubtitleError(f"duplicate cue id {cue.cue_id!r}")
        cue_ids.add(cue.cue_id)
        track = track_by_id.get(cue.track_id)
        if track is None:
            raise SubtitleError(
                f"cue {cue.cue_id!r} references unknown track {cue.track_id!r}"
            )
        start = _centiseconds(cue.start_seconds, f"cue {cue.cue_id} start")
        end = _centiseconds(cue.end_seconds, f"cue {cue.cue_id} end")
        if duration is not None and end > duration:
            raise SubtitleError(
                f"cue {cue.cue_id!r} ends outside the declared document duration"
            )
        normalized.append((start, end, cue, track))

    _reject_track_overlaps(normalized)
    ordered_styles = sorted(
        style_by_name.values(), key=lambda style: (style.name.casefold(), style.name)
    )
    ordered_events = sorted(
        normalized,
        key=lambda item: (
            item[0],
            item[3].layer,
            item[3].track_id,
            item[2].cue_id,
        ),
    )

    header = [
        "[Script Info]",
        f"Title: {config.title}",
        "ScriptType: v4.00+",
        f"PlayResX: {config.play_res_x}",
        f"PlayResY: {config.play_res_y}",
        f"WrapStyle: {config.wrap_style}",
        "ScaledBorderAndShadow: "
        + ("yes" if config.scaled_border_and_shadow else "no"),
        f"YCbCr Matrix: {config.ycbcr_matrix}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
    ]
    header.extend(_style_row(style) for style in ordered_styles)
    header.extend(
        (
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
            "MarginV, Effect, Text",
        )
    )

    prefix = ""
    if config.cue_wrap_style is not None:
        prefix = "{\\q" + str(config.cue_wrap_style) + "}"
    events = [
        "Dialogue: "
        f"{track.layer},{_timestamp_from_centiseconds(start)},"
        f"{_timestamp_from_centiseconds(end)},{track.style.name},"
        f"{cue.cue_id},0,0,0,,{prefix}{ass_escape(cue.text)}"
        for start, end, cue, track in ordered_events
    ]
    return "\n".join(header + events) + "\n"


def _style_row(style: AssStyleConfig) -> str:
    fields = (
        style.name,
        style.font_name,
        _format_number(style.font_size),
        style.primary_colour.upper(),
        style.secondary_colour.upper(),
        style.outline_colour.upper(),
        style.back_colour.upper(),
        _ass_boolean(style.bold),
        _ass_boolean(style.italic),
        _ass_boolean(style.underline),
        _ass_boolean(style.strike_out),
        _format_number(style.scale_x),
        _format_number(style.scale_y),
        _format_number(style.spacing),
        _format_number(style.angle),
        str(style.border_style),
        _format_number(style.outline),
        _format_number(style.shadow),
        str(style.alignment),
        str(style.margin_left),
        str(style.margin_right),
        str(style.margin_vertical),
        str(style.encoding),
    )
    return "Style: " + ",".join(fields)


def _validate_style_bounds(style: AssStyleConfig, config: AssDocumentConfig) -> None:
    if style.margin_left + style.margin_right >= config.play_res_x:
        raise SubtitleError(
            f"style {style.name!r} horizontal margins consume the render width"
        )
    if style.margin_vertical >= config.play_res_y:
        raise SubtitleError(
            f"style {style.name!r} vertical margin is outside the render frame"
        )
    if float(style.font_size) + style.margin_vertical > config.play_res_y:
        raise SubtitleError(
            f"style {style.name!r} cannot fit one line inside the render frame"
        )


def _reject_track_overlaps(
    normalized: Sequence[tuple[int, int, AssCue, SubtitleTrackConfig]],
) -> None:
    by_track: dict[str, list[tuple[int, int, AssCue]]] = {}
    for start, end, cue, track in normalized:
        by_track.setdefault(track.track_id, []).append((start, end, cue))
    for track_id, rows in by_track.items():
        previous_end = -1
        previous_cue = ""
        for start, end, cue in sorted(rows, key=lambda row: (row[0], row[1], row[2].cue_id)):
            if start < previous_end:
                raise SubtitleError(
                    f"cue {cue.cue_id!r} overlaps cue {previous_cue!r} "
                    f"on track {track_id!r}"
                )
            previous_end = end
            previous_cue = cue.cue_id


def _available_fonts(values: Collection[str]) -> frozenset[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Collection):
        raise SubtitleError("available_font_names must be a collection of names")
    normalized: set[str] = set()
    for value in values:
        _safe_ass_field(value, "available font name")
        folded = value.casefold()
        if folded in normalized:
            raise SubtitleError("available font names must be unique case-insensitively")
        normalized.add(folded)
    if not normalized:
        raise SubtitleError("available_font_names must not be empty")
    return frozenset(normalized)


def _centiseconds(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise SubtitleError(f"{label} must be a finite non-negative number")
    if isinstance(value, float) and not math.isfinite(value):
        raise SubtitleError(f"{label} must be a finite non-negative number")
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SubtitleError(f"{label} must be a finite non-negative number") from exc
    if not decimal_value.is_finite() or decimal_value < 0:
        raise SubtitleError(f"{label} must be a finite non-negative number")
    centiseconds = int(
        (decimal_value * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    if centiseconds > _MAX_CENTISECONDS:
        raise SubtitleError(f"{label} exceeds the supported 99:59:59.99 range")
    return centiseconds


def _timestamp_from_centiseconds(centiseconds: int) -> str:
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def _format_number(value: int | float) -> str:
    decimal_value = Decimal(str(value))
    rendered = format(decimal_value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return "0" if rendered in {"", "-0"} else rendered


def _ass_boolean(value: bool) -> str:
    return "-1" if value else "0"


def _safe_header_value(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SubtitleError(f"{label} must be a non-empty string")
    if any(unicodedata.category(char) in {"Cc", "Cs", "Zl", "Zp"} for char in value):
        raise SubtitleError(f"{label} must not contain control or line-break characters")
    return value


def _safe_ass_field(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or _FIELD_IDENTIFIER.fullmatch(value) is None
    ):
        raise SubtitleError(f"{label} must be a non-empty, comma-free ASS field")
    if any(unicodedata.category(char) in {"Cc", "Cs", "Zl", "Zp"} for char in value):
        raise SubtitleError(f"{label} contains an unsupported character")
    return value


def _track_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _TRACK_IDENTIFIER.fullmatch(value) is None:
        raise SubtitleError(
            f"{label} must use only ASCII letters, digits, '.', '_' or '-'"
        )
    return value


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SubtitleError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise SubtitleError(f"{label} must be a finite number")
    return result


def _positive_number(value: object, label: str) -> float:
    result = _finite_number(value, label)
    if result <= 0:
        raise SubtitleError(f"{label} must be greater than zero")
    return result


def _nonnegative_number(value: object, label: str) -> float:
    result = _finite_number(value, label)
    if result < 0:
        raise SubtitleError(f"{label} must be non-negative")
    return result


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SubtitleError(f"{label} must be a positive integer")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SubtitleError(f"{label} must be a non-negative integer")
    return value


def _integer_in_range(value: object, label: str, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise SubtitleError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value
