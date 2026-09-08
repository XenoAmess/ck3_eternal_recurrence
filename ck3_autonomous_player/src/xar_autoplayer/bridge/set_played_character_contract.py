"""Typed public contract for rebinding the local CK3 player character."""

from __future__ import annotations

from typing import Final


SET_PLAYED_CHARACTER_V1_CAPABILITY: Final = (
    "game.command.set-played-character-v1-N"
)
SET_PLAYED_CHARACTER_V1_STEP_PREFIX: Final = "set-played-character-v1-"
SET_PLAYED_CHARACTER_V1_GAME_VERSION: Final = "1.19.0.6"
SET_PLAYED_CHARACTER_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
SET_PLAYED_CHARACTER_V1_REJECTION_CODES: Final = frozenset(
    {
        "target_not_found",
        "target_dead",
        "target_controlled",
        "requires_paused",
        "map_not_ready",
        "postcondition_failed",
        "state_changed",
        "submission_failed",
        "unavailable",
        "invalid_request",
    }
)


def validate_character_id(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > 2**31 - 1
    ):
        raise ValueError("character_id must be a positive signed int32")
    return value


def set_played_character_v1_step(character_id: object) -> str:
    return f"{SET_PLAYED_CHARACTER_V1_STEP_PREFIX}{validate_character_id(character_id)}"
