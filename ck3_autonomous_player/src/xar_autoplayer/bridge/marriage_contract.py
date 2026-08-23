"""Canonical native CK3 arrange-marriage query and command contract."""

from __future__ import annotations

import re


QUERY_ARRANGE_MARRIAGE_CHOICES_STEP = "query-arrange-marriage-choices"
ARRANGE_MARRIAGE_CAPABILITY = "game.command.arrange-marriage-N"
_CHOICE_ID = re.compile(r"(?P<played>\d+)-(?P<candidate>\d+)")


def normalize_arrange_marriage_choices(
    value: object,
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("native arrange_marriage_choices must be an array")
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise ValueError(
                f"native arrange_marriage_choices[{index}] must be an object"
            )
        played = _non_negative(
            raw.get("played_character_id"), "played_character_id"
        )
        candidate = _non_negative(
            raw.get("candidate_character_id"), "candidate_character_id"
        )
        if candidate == played:
            raise ValueError("arrange-marriage candidate cannot be the player")
        choice_id = f"{played}-{candidate}"
        if raw.get("choice_id") != choice_id:
            raise ValueError(
                f"native arrange_marriage_choices[{index}].choice_id is malformed"
            )
        if choice_id in seen:
            raise ValueError(
                "native arrange_marriage_choices contains a duplicate choice"
            )
        seen.add(choice_id)
        result.append(
            {
                "choice_id": choice_id,
                "played_character_id": played,
                "candidate_character_id": candidate,
                "source": "native",
            }
        )
    return result


def arrange_marriage_step(choice_id: str) -> str:
    if not isinstance(choice_id, str) or _CHOICE_ID.fullmatch(choice_id) is None:
        raise ValueError("arrange-marriage choice_id is malformed")
    return f"arrange-marriage-{choice_id}"


def parse_arrange_marriage_step(step: object) -> str | None:
    if not isinstance(step, str) or not step.startswith("arrange-marriage-"):
        return None
    choice_id = step.removeprefix("arrange-marriage-")
    return choice_id if _CHOICE_ID.fullmatch(choice_id) else None


def is_native_marriage_step(step: object) -> bool:
    return (
        step == QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        or parse_arrange_marriage_step(step) is not None
    )


def observed_marriage_status(
    played_character: object,
    *,
    played_character_id: int,
    candidate_character_id: int,
) -> str | None:
    """Return the exact relationship outcome for one submitted candidate."""
    if not isinstance(played_character, dict):
        return None
    if played_character.get("character_id") != played_character_id:
        return None
    if played_character.get("betrothed_id") == candidate_character_id:
        return "accepted_betrothal"
    spouse_ids = played_character.get("spouse_ids")
    if isinstance(spouse_ids, list) and candidate_character_id in spouse_ids:
        return "accepted_marriage"
    return None


def _non_negative(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
