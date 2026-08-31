"""Dependency-free, measured text wrapping and subtitle-safe layout.

The module deliberately knows nothing about languages, projects, renderers, or
installed font APIs.  A caller resolves fonts into :class:`FontSpec` objects and
injects a measurer that uses the exact same font implementation as the final
renderer.  This keeps layout deterministic in tests while still allowing a
Pillow, Qt, browser, or native renderer in production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import unicodedata
from typing import Callable, Mapping, Sequence

from .errors import PromoToolchainError


_EPSILON = 0.01
_ALIGNMENTS = frozenset({"left", "center", "right"})


class LayoutError(PromoToolchainError):
    """Text cannot be laid out without violating the declared contract."""


@dataclass(frozen=True)
class FontSpec:
    """A renderer-independent resolved font identity.

    ``key`` is the stable registry key used by a project.  ``family`` is the
    family passed to the eventual renderer.  Supplying both makes a missing or
    accidentally substituted font observable instead of silently falling back.
    """

    key: str
    family: str
    size_px: float
    weight: int = 400
    italic: bool = False

    def __post_init__(self) -> None:
        _nonempty_string(self.key, "font key")
        _nonempty_string(self.family, "font family")
        _positive_number(self.size_px, "font size_px")
        if isinstance(self.weight, bool) or not isinstance(self.weight, int):
            raise LayoutError("font weight must be an integer")
        if not 1 <= self.weight <= 1000:
            raise LayoutError("font weight must be between 1 and 1000")
        if not isinstance(self.italic, bool):
            raise LayoutError("font italic must be a boolean")


TextMeasurer = Callable[[str, FontSpec], float]


@dataclass(frozen=True)
class SafeArea:
    """Inclusive-exclusive safe rectangle inside a render frame."""

    frame_width: float
    frame_height: float
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        frame_width = _positive_number(self.frame_width, "frame width")
        frame_height = _positive_number(self.frame_height, "frame height")
        left = _nonnegative_number(self.left, "safe-area left")
        top = _nonnegative_number(self.top, "safe-area top")
        right = _positive_number(self.right, "safe-area right")
        bottom = _positive_number(self.bottom, "safe-area bottom")
        if not left < right:
            raise LayoutError("safe-area left must be less than right")
        if not top < bottom:
            raise LayoutError("safe-area top must be less than bottom")
        if right > frame_width or bottom > frame_height:
            raise LayoutError("safe area must remain inside the render frame")

    @classmethod
    def from_margins(
        cls,
        *,
        frame_width: float,
        frame_height: float,
        left: float,
        top: float,
        right: float,
        bottom: float,
    ) -> "SafeArea":
        """Build a safe area from four non-negative frame margins."""

        width = _positive_number(frame_width, "frame width")
        height = _positive_number(frame_height, "frame height")
        margin_left = _nonnegative_number(left, "left margin")
        margin_top = _nonnegative_number(top, "top margin")
        margin_right = _nonnegative_number(right, "right margin")
        margin_bottom = _nonnegative_number(bottom, "bottom margin")
        return cls(
            frame_width=width,
            frame_height=height,
            left=margin_left,
            top=margin_top,
            right=width - margin_right,
            bottom=height - margin_bottom,
        )

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass(frozen=True)
class WrapPolicy:
    """Language-agnostic break preferences supplied by a project.

    Characters in ``force_break_after`` terminate a semantic line even when
    more text would fit.  ``prefer_break_after`` and Unicode punctuation are
    considered when an overlong segment must be split.  No locale is inferred.
    """

    force_break_after: frozenset[str] = field(default_factory=frozenset)
    prefer_break_after: frozenset[str] = field(default_factory=frozenset)
    decimal_separators: frozenset[str] = field(default_factory=frozenset)
    prefer_whitespace: bool = True
    prefer_unicode_punctuation: bool = True
    boundary_search_floor: float = 0.5

    def __post_init__(self) -> None:
        for label, values in (
            ("force_break_after", self.force_break_after),
            ("prefer_break_after", self.prefer_break_after),
            ("decimal_separators", self.decimal_separators),
        ):
            if not isinstance(values, frozenset):
                raise LayoutError(f"{label} must be a frozenset")
            if any(not isinstance(value, str) or len(value) != 1 for value in values):
                raise LayoutError(f"{label} entries must be single characters")
        if not isinstance(self.prefer_whitespace, bool):
            raise LayoutError("prefer_whitespace must be a boolean")
        if not isinstance(self.prefer_unicode_punctuation, bool):
            raise LayoutError("prefer_unicode_punctuation must be a boolean")
        floor = _finite_number(self.boundary_search_floor, "boundary_search_floor")
        if not 0 < floor <= 1:
            raise LayoutError("boundary_search_floor must be in (0, 1]")


@dataclass(frozen=True)
class TextLayout:
    lines: tuple[str, ...]
    widths: tuple[float, ...]
    width_limit: float

    def __post_init__(self) -> None:
        if not self.lines or len(self.lines) != len(self.widths):
            raise LayoutError("text layout must contain matching lines and widths")
        limit = _positive_number(self.width_limit, "text layout width_limit")
        for index, (line, width) in enumerate(zip(self.lines, self.widths)):
            if not isinstance(line, str) or not line.strip():
                raise LayoutError(f"text layout line {index} must be renderable")
            measured = _nonnegative_number(width, f"text layout width {index}")
            if measured > limit + _EPSILON:
                raise LayoutError(f"text layout line {index} exceeds its width limit")


@dataclass(frozen=True)
class TrackLayoutConfig:
    """Configurable hierarchy and geometry for one subtitle track.

    ``stack_order=0`` is closest to the bottom edge of the safe area.  ``layer``
    is preserved for the compositor/ASS layer and is not guessed from locale.
    """

    track_id: str
    font_key: str
    layer: int
    stack_order: int
    max_lines: int
    line_height_px: float
    horizontal_inset_px: float = 0.0
    gap_above_px: float = 0.0
    alignment: str = "center"
    wrap_policy: WrapPolicy = field(default_factory=WrapPolicy)

    def __post_init__(self) -> None:
        _identifier(self.track_id, "track id")
        _identifier(self.font_key, "font key")
        _nonnegative_integer(self.layer, "track layer")
        _nonnegative_integer(self.stack_order, "track stack_order")
        _positive_integer(self.max_lines, "track max_lines")
        _positive_number(self.line_height_px, "track line_height_px")
        _nonnegative_number(self.horizontal_inset_px, "track horizontal_inset_px")
        _nonnegative_number(self.gap_above_px, "track gap_above_px")
        if self.alignment not in _ALIGNMENTS:
            raise LayoutError(
                "track alignment must be one of: " + ", ".join(sorted(_ALIGNMENTS))
            )
        if not isinstance(self.wrap_policy, WrapPolicy):
            raise LayoutError("track wrap_policy must be a WrapPolicy")


@dataclass(frozen=True)
class PositionedLine:
    text: str
    width: float
    x: float
    y: float


@dataclass(frozen=True)
class PositionedTrack:
    track_id: str
    layer: int
    stack_order: int
    font: FontSpec
    left: float
    top: float
    right: float
    bottom: float
    lines: tuple[PositionedLine, ...]


def wrap_text(
    text: str,
    *,
    font: FontSpec,
    measure: TextMeasurer,
    max_width: float,
    max_lines: int,
    policy: WrapPolicy | None = None,
) -> TextLayout:
    """Wrap ``text`` using actual injected font measurements.

    The function never truncates or substitutes text.  If even one code point
    cannot fit, the measurer is invalid, or the line budget is exceeded, it
    fails closed with :class:`LayoutError`.
    """

    if not isinstance(text, str) or not text.strip():
        raise LayoutError("text must contain at least one renderable character")
    for char in text:
        if char in {"\r", "\n", "\t"}:
            continue
        if unicodedata.category(char) in {"Cc", "Cs", "Zl", "Zp"}:
            raise LayoutError("text contains an unsupported control character")
    if not isinstance(font, FontSpec):
        raise LayoutError("font must be a resolved FontSpec")
    if not callable(measure):
        raise LayoutError("measure must be callable")
    width_limit = _positive_number(max_width, "max_width")
    line_limit = _positive_integer(max_lines, "max_lines")
    selected_policy = WrapPolicy() if policy is None else policy
    if not isinstance(selected_policy, WrapPolicy):
        raise LayoutError("policy must be a WrapPolicy")

    lines: list[str] = []
    for raw_paragraph in _paragraphs(text):
        paragraph = raw_paragraph.strip()
        if not paragraph:
            continue
        for segment in _semantic_segments(paragraph, selected_policy):
            lines.extend(
                _wrap_segment(
                    segment,
                    font=font,
                    measure=measure,
                    max_width=width_limit,
                    policy=selected_policy,
                )
            )
            if len(lines) > line_limit:
                raise LayoutError(
                    f"text requires more than the configured {line_limit} lines"
                )

    if not lines:
        raise LayoutError("text produced no renderable lines")
    widths = tuple(_measured_width(measure, line, font) for line in lines)
    for index, width in enumerate(widths):
        if width > width_limit + _EPSILON:
            raise LayoutError(
                f"measured line {index} exceeds {width_limit:g}px safe width"
            )
    return TextLayout(tuple(lines), widths, width_limit)


def balance_lines(
    lines: Sequence[str], *, max_lines_per_block: int
) -> tuple[tuple[str, ...], ...]:
    """Partition lines into deterministic, near-even cue blocks."""

    per_block = _positive_integer(max_lines_per_block, "max_lines_per_block")
    materialized = tuple(lines)
    if not materialized:
        raise LayoutError("cannot balance an empty line sequence")
    if any(not isinstance(line, str) or not line.strip() for line in materialized):
        raise LayoutError("balanced lines must all be renderable strings")
    block_count = math.ceil(len(materialized) / per_block)
    base_size, larger_blocks = divmod(len(materialized), block_count)
    blocks: list[tuple[str, ...]] = []
    cursor = 0
    for index in range(block_count):
        block_size = base_size + (1 if index < larger_blocks else 0)
        blocks.append(materialized[cursor : cursor + block_size])
        cursor += block_size
    if cursor != len(materialized) or any(len(block) > per_block for block in blocks):
        raise LayoutError("internal error: invalid balanced line partition")
    return tuple(blocks)


def layout_tracks(
    text_by_track: Mapping[str, str],
    *,
    tracks: Sequence[TrackLayoutConfig],
    fonts: Mapping[str, FontSpec],
    safe_area: SafeArea,
    measure: TextMeasurer,
) -> tuple[PositionedTrack, ...]:
    """Measure and stack configured tracks upward inside ``safe_area``.

    Track identity, compositing layer, and vertical hierarchy are all explicit.
    Missing/extra text, missing fonts, duplicate hierarchy slots, horizontal
    overflow, and vertical overflow are hard errors.
    """

    if not isinstance(text_by_track, Mapping):
        raise LayoutError("text_by_track must be a mapping")
    if not isinstance(fonts, Mapping):
        raise LayoutError("fonts must be a mapping")
    if not isinstance(safe_area, SafeArea):
        raise LayoutError("safe_area must be a SafeArea")
    if not callable(measure):
        raise LayoutError("measure must be callable")

    try:
        configured = tuple(tracks)
    except TypeError as exc:
        raise LayoutError("tracks must be a sequence") from exc
    if not configured:
        raise LayoutError("at least one track layout must be configured")
    if any(not isinstance(track, TrackLayoutConfig) for track in configured):
        raise LayoutError("tracks must contain TrackLayoutConfig values")
    track_ids = [track.track_id for track in configured]
    if len(set(track_ids)) != len(track_ids):
        raise LayoutError("track ids must be unique")
    stack_orders = [track.stack_order for track in configured]
    if len(set(stack_orders)) != len(stack_orders):
        raise LayoutError("track stack_order values must be unique")

    if any(not isinstance(key, str) for key in text_by_track):
        raise LayoutError("text_by_track keys must be track-id strings")
    supplied_ids = set(text_by_track)
    expected_ids = set(track_ids)
    if supplied_ids != expected_ids:
        missing = sorted(expected_ids - supplied_ids)
        extra = sorted(supplied_ids - expected_ids)
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("unexpected=" + ",".join(extra))
        raise LayoutError("subtitle track text mismatch: " + "; ".join(details))

    layouts: dict[str, tuple[TrackLayoutConfig, FontSpec, TextLayout, float, float]] = {}
    for track in configured:
        font = fonts.get(track.font_key)
        if font is None:
            raise LayoutError(
                f"font {track.font_key!r} required by track {track.track_id!r} is missing"
            )
        if not isinstance(font, FontSpec):
            raise LayoutError(f"font registry entry {track.font_key!r} is not a FontSpec")
        if font.key != track.font_key:
            raise LayoutError(
                f"font registry key {track.font_key!r} does not match FontSpec.key {font.key!r}"
            )
        inset = track.horizontal_inset_px
        available_width = safe_area.width - (2 * inset)
        if available_width <= 0:
            raise LayoutError(
                f"track {track.track_id!r} horizontal inset consumes its safe width"
            )
        layout = wrap_text(
            text_by_track[track.track_id],
            font=font,
            measure=measure,
            max_width=available_width,
            max_lines=track.max_lines,
            policy=track.wrap_policy,
        )
        height = len(layout.lines) * track.line_height_px
        layouts[track.track_id] = (track, font, layout, available_width, height)

    ordered_tracks = sorted(configured, key=lambda item: (item.stack_order, item.track_id))
    positioned: list[PositionedTrack] = []
    cursor_bottom = safe_area.bottom
    for track_index, track in enumerate(ordered_tracks):
        _, font, layout, available_width, height = layouts[track.track_id]
        bottom = cursor_bottom
        top = bottom - height
        if top < safe_area.top - _EPSILON:
            raise LayoutError(
                f"track {track.track_id!r} exceeds the vertical safe area"
            )
        left = safe_area.left + track.horizontal_inset_px
        right = left + available_width
        placed_lines: list[PositionedLine] = []
        for index, (line, width) in enumerate(zip(layout.lines, layout.widths)):
            if track.alignment == "left":
                x = left
            elif track.alignment == "right":
                x = right - width
            else:
                x = left + ((available_width - width) / 2)
            y = top + (index * track.line_height_px)
            if x < left - _EPSILON or x + width > right + _EPSILON:
                raise LayoutError(
                    f"track {track.track_id!r} line {index} escaped its safe bounds"
                )
            placed_lines.append(PositionedLine(line, width, x, y))
        positioned.append(
            PositionedTrack(
                track_id=track.track_id,
                layer=track.layer,
                stack_order=track.stack_order,
                font=font,
                left=left,
                top=top,
                right=right,
                bottom=bottom,
                lines=tuple(placed_lines),
            )
        )
        cursor_bottom = top - track.gap_above_px
        if (
            cursor_bottom < safe_area.top - _EPSILON
            and track_index + 1 < len(ordered_tracks)
        ):
            raise LayoutError(
                f"gap above track {track.track_id!r} exceeds the vertical safe area"
            )
    return tuple(positioned)


def _paragraphs(text: str) -> tuple[str, ...]:
    # ``splitlines`` handles CRLF/CR/LF consistently.  A trailing newline does
    # not create a fake renderable line, and tabs are normalized to spaces so
    # measurement and final renderers do not disagree about tab stops.
    return tuple(line.expandtabs(4) for line in text.splitlines()) or (text.expandtabs(4),)


def _semantic_segments(paragraph: str, policy: WrapPolicy) -> tuple[str, ...]:
    segments: list[str] = []
    current: list[str] = []
    for index, char in enumerate(paragraph):
        current.append(char)
        if char in policy.force_break_after and not _is_decimal_separator(
            paragraph, index, policy
        ):
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
    remainder = "".join(current).strip()
    if remainder:
        segments.append(remainder)
    return tuple(segments)


def _wrap_segment(
    segment: str,
    *,
    font: FontSpec,
    measure: TextMeasurer,
    max_width: float,
    policy: WrapPolicy,
) -> list[str]:
    lines: list[str] = []
    remainder = segment.strip()
    while remainder:
        if _measured_width(measure, remainder, font) <= max_width + _EPSILON:
            lines.append(remainder)
            break
        fitting = _longest_fitting_prefix(
            remainder,
            font=font,
            measure=measure,
            max_width=max_width,
        )
        if fitting <= 0:
            raise LayoutError(
                "the configured font cannot fit one character inside the safe width"
            )
        split_at = _preferred_break_index(remainder, fitting, policy)
        piece = remainder[:split_at].rstrip()
        if not piece:
            split_at = fitting
            piece = remainder[:split_at].strip()
        if not piece:
            raise LayoutError("text wrapping made no progress")
        lines.append(piece)
        remainder = remainder[split_at:].lstrip()
    return lines


def _longest_fitting_prefix(
    text: str,
    *,
    font: FontSpec,
    measure: TextMeasurer,
    max_width: float,
) -> int:
    low = 1
    high = len(text)
    best = 0
    while low <= high:
        middle = (low + high) // 2
        candidate = text[:middle].rstrip()
        width = _measured_width(measure, candidate, font)
        if candidate and width <= max_width + _EPSILON:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best


def _preferred_break_index(text: str, fitting: int, policy: WrapPolicy) -> int:
    floor = max(1, math.ceil(fitting * policy.boundary_search_floor))
    candidates: list[tuple[int, int]] = []
    for index in range(floor, fitting + 1):
        char = text[index - 1]
        if char in policy.force_break_after and not _is_decimal_separator(
            text, index - 1, policy
        ):
            priority = 3
        elif policy.prefer_whitespace and char.isspace():
            priority = 2
        elif char in policy.prefer_break_after and not _is_decimal_separator(
            text, index - 1, policy
        ):
            priority = 1
        elif (
            policy.prefer_unicode_punctuation
            and unicodedata.category(char).startswith("P")
            and not _is_decimal_separator(text, index - 1, policy)
        ):
            priority = 1
        else:
            continue
        candidates.append((priority, index))
    if not candidates:
        return fitting
    highest_priority = max(priority for priority, _ in candidates)
    return max(index for priority, index in candidates if priority == highest_priority)


def _is_decimal_separator(text: str, index: int, policy: WrapPolicy) -> bool:
    return (
        text[index] in policy.decimal_separators
        and index > 0
        and index + 1 < len(text)
        and text[index - 1].isdigit()
        and text[index + 1].isdigit()
    )


def _measured_width(measure: TextMeasurer, text: str, font: FontSpec) -> float:
    try:
        raw = measure(text, font)
    except Exception as exc:  # the injected renderer is part of the contract
        raise LayoutError(f"font measurement failed: {exc}") from exc
    return _nonnegative_number(raw, "measured text width")


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LayoutError(f"{label} must be a non-empty string")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise LayoutError(f"{label} must not contain control characters")
    return value


def _identifier(value: object, label: str) -> str:
    result = _nonempty_string(value, label)
    if any(char.isspace() or char in {",", "[", "]"} for char in result):
        raise LayoutError(f"{label} must not contain whitespace, commas, or brackets")
    return result


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LayoutError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise LayoutError(f"{label} must be a finite number")
    return result


def _positive_number(value: object, label: str) -> float:
    result = _finite_number(value, label)
    if result <= 0:
        raise LayoutError(f"{label} must be greater than zero")
    return result


def _nonnegative_number(value: object, label: str) -> float:
    result = _finite_number(value, label)
    if result < 0:
        raise LayoutError(f"{label} must be non-negative")
    return result


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LayoutError(f"{label} must be a positive integer")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LayoutError(f"{label} must be a non-negative integer")
    return value
