"""Explicit schema variants for unchanged adopted Army read DTOs."""

from __future__ import annotations


_ARMY_COMMANDER_CANDIDATES_V1_SCHEMAS = (
    "ck3_12003_army_commander_candidates_v1",
    "ck3_12004_army_commander_candidates_v1",
)
_ARMY_CURRENT_MOVEMENT_SPEED_V1_SCHEMAS = (
    "ck3_12003_army_current_movement_speed_v1",
    "ck3_12004_army_current_movement_speed_v1",
)


def is_army_commander_candidates_v1_schema(value: object) -> bool:
    """Accept the preserved candidates DTO for its explicit adopted builds."""
    return value in _ARMY_COMMANDER_CANDIDATES_V1_SCHEMAS


def is_army_current_movement_speed_v1_schema(value: object) -> bool:
    """Accept the preserved optional selected-unit movement DTO."""
    return value in _ARMY_CURRENT_MOVEMENT_SPEED_V1_SCHEMAS
