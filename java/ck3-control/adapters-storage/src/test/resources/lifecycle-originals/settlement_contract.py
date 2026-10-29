"""Canonical one-life settlement projection shared by CK3 bridge backends."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re


ONE_LIFE_SETTLEMENT_CAPABILITY = "game.state.xar-one-life-settlement"
ONE_LIFE_SETTLEMENT_KEY = "one_life_settlement"
RECORD_LESSON_PREFIX = "xar_hs_ge_"

_COMPLETED_LESSONS = re.compile(
    r"\bcompleted_lessons\s*=\s*\{(?P<body>.*?)\}",
    re.DOTALL,
)
_LESSON_TOKEN = re.compile(r'"([^"\r\n]+)"|([A-Za-z0-9_.:-]+)')


def normalize_one_life_settlement(value: object) -> dict[str, object] | None:
    """Normalize a published Mod settlement without guessing CK3 raw scales.

    ``final_score`` and ``score_before_reject`` may be semantic JSON numbers or
    explicit ``{"raw": ..., "scale": ...}`` objects.  The latter are divided
    only by their published scale, so Python never guesses CK3's fixed scale.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("one_life_settlement must be an object or null")

    ready = _boolean(value.get("ready"), "ready")
    commit_serial = _optional_non_negative_integer(
        value.get("commit_serial"), "commit_serial"
    )
    if not ready:
        return {
            "ready": False,
            "commit_serial": commit_serial,
        }

    if commit_serial != 1:
        raise ValueError(
            "ready one_life_settlement must have commit_serial 1"
        )
    source_character_id = _non_negative_integer(
        value.get("source_character_id"), "source_character_id"
    )
    final_score = normalize_fixed_score(
        value.get("final_score"), "final_score"
    )
    score_before_reject = normalize_fixed_score(
        value.get("score_before_reject"), "score_before_reject"
    )
    record_candidate = _non_negative_integer(
        value.get("record_candidate"), "record_candidate"
    )
    old_record = _non_negative_integer(value.get("old_record"), "old_record")
    record_delta = _integer(value.get("record_delta"), "record_delta")
    blessing_count = _non_negative_integer(
        value.get("blessing_count"), "blessing_count"
    )
    refusal_count = _non_negative_integer(
        value.get("refusal_count"), "refusal_count"
    )
    contract_progress = _non_negative_integer(
        value.get("contract_progress"), "contract_progress"
    )
    record_written = _boolean(value.get("record_written"), "record_written")
    if record_delta != record_candidate - old_record:
        raise ValueError(
            "one_life_settlement record_delta does not match candidate-old_record"
        )
    if record_written and not record_candidate > old_record:
        raise ValueError(
            "one_life_settlement record_written requires a new record"
        )

    return {
        "ready": True,
        "commit_serial": commit_serial,
        "source_character_id": source_character_id,
        "final_score": final_score,
        "score_before_reject": score_before_reject,
        "record_candidate": record_candidate,
        "old_record": old_record,
        "record_delta": record_delta,
        "blessing_count": blessing_count,
        "refusal_count": refusal_count,
        "contract_progress": contract_progress,
        "record_written": record_written,
    }


def normalize_fixed_score(value: object, name: str = "score") -> int | float:
    """Return semantic points from a number or an explicit raw/scale pair."""
    if isinstance(value, dict):
        if set(value) != {"raw", "scale"}:
            raise ValueError(
                f"one_life_settlement {name} fixed value must contain raw and scale"
            )
        raw = value.get("raw")
        scale = value.get("scale")
        if (
            isinstance(raw, bool)
            or not isinstance(raw, int)
            or isinstance(scale, bool)
            or not isinstance(scale, int)
            or scale <= 0
        ):
            raise ValueError(
                f"one_life_settlement {name} fixed raw/scale is malformed"
            )
        quotient, remainder = divmod(abs(raw), scale)
        if remainder == 0:
            return -quotient if raw < 0 else quotient
        return raw / scale
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"one_life_settlement {name} must be a JSON number or fixed object"
        )
    if not math.isfinite(float(value)):
        raise ValueError(f"one_life_settlement {name} must be finite")
    if isinstance(value, int):
        return value
    return int(value) if value.is_integer() else value


def settlement_ready_for_episode(
    settlement: object, episode_character_id: object
) -> bool:
    """Whether a complete payload belongs to the immutable episode character."""
    return bool(
        isinstance(settlement, dict)
        and settlement.get("ready") is True
        and isinstance(episode_character_id, int)
        and not isinstance(episode_character_id, bool)
        and settlement.get("source_character_id") == episode_character_id
    )


def record_lesson_id(record_candidate: int) -> str | None:
    candidate = _non_negative_integer(record_candidate, "record_candidate")
    return f"{RECORD_LESSON_PREFIX}{candidate}" if candidate > 0 else None


def parse_completed_tutorial_lessons(text: str) -> frozenset[str]:
    """Parse CK3's completed lesson set from ``tutorial.txt``."""
    if not isinstance(text, str):
        raise TypeError("tutorial text must be a string")
    match = _COMPLETED_LESSONS.search(text.lstrip("\ufeff"))
    if match is None:
        raise ValueError("tutorial.txt lacks completed_lessons")
    lessons: set[str] = set()
    for token in _LESSON_TOKEN.finditer(match.group("body")):
        lessons.add(token.group(1) or token.group(2))
    return frozenset(lessons)


def tutorial_record_observation(
    path: Path, record_candidate: int
) -> dict[str, object]:
    """Read one persistence observation suitable for consecutive stability checks."""
    lesson_id = record_lesson_id(record_candidate)
    if lesson_id is None:
        return {
            "path": str(path),
            "lesson_id": None,
            "present": True,
            "size": 0,
            "sha256": None,
        }
    try:
        payload = path.read_bytes()
    except FileNotFoundError:
        return {
            "path": str(path),
            "lesson_id": lesson_id,
            "present": False,
            "size": None,
            "sha256": None,
        }
    text = payload.decode("utf-8-sig")
    lessons = parse_completed_tutorial_lessons(text)
    return {
        "path": str(path),
        "lesson_id": lesson_id,
        "present": lesson_id in lessons,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _boolean(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool) and value in {0, 1}:
        return bool(value)
    raise ValueError(f"one_life_settlement {name} must be boolean or 0/1")


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"one_life_settlement {name} must be an integer")
    return value


def _non_negative_integer(value: object, name: str) -> int:
    result = _integer(value, name)
    if result < 0:
        raise ValueError(f"one_life_settlement {name} must be non-negative")
    return result


def _optional_non_negative_integer(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _non_negative_integer(value, name)
