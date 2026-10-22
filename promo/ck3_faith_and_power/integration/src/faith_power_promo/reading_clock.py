"""Explicit reading time extends rendering, never the measured voice clock."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class ReadingClock:
    source_base_duration_seconds: float
    reading_hold_seconds: float
    render_duration_seconds: float


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + ' must be a JSON object')
    result: dict[str, object] = {}
    for key, child in value.items():
        if not isinstance(key, str):
            raise ValueError(label + ' needs string keys')
        result[key] = child
    return result


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label + ' must be a finite non-bool number')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(label + ' must be finite')
    return result


def selected_reading_clock(selected: object, source: object, *, enabled: bool) -> ReadingClock:
    """Validate a selected render clock against its unchanged voice catalog."""
    row = _mapping(selected, 'selected cue')
    original = _mapping(source, 'source cue')
    base = _number(original.get('duration_seconds'), 'source duration_seconds')
    render = _number(row.get('duration_seconds'), 'selected duration_seconds')
    if base <= 0 or render <= 0:
        raise ValueError('Voice and render durations must be positive')
    if 'reading_hold_seconds' not in row:
        if row['duration_seconds'] != original['duration_seconds']:
            raise ValueError('Selected measured source field changed: duration_seconds')
        return ReadingClock(base, 0.0, render)
    if enabled is not True:
        raise ValueError('Reading holds require source-mechanism-full mode')
    hold = _number(row['reading_hold_seconds'], 'reading_hold_seconds')
    if not 0 <= hold <= 20 or abs(hold * 30 - round(hold * 30)) > 1e-6:
        raise ValueError('Reading hold must be within 0..20 seconds and align to 30fps')
    if abs(render - (base + hold)) > 1e-6:
        raise ValueError('Selected render duration must equal source base plus reading hold')
    return ReadingClock(base, hold, render)


def checked_reading_hold_total(clocks: Sequence[ReadingClock]) -> float:
    """Bound only explicit author reading time, independently of speech length."""
    total = math.fsum(clock.reading_hold_seconds for clock in clocks)
    if total > 120 + 1e-6:
        raise ValueError('Full-episode reading holds exceed 120 seconds')
    return total
