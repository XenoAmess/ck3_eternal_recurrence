"""Conditional native advantage arithmetic for the agent's combat model."""

from __future__ import annotations


def resolved_advantage_with_commander_rolls_raw(
    zero_roll_advantage_raw: int,
    side_0_roll_points: int,
    side_1_roll_points: int,
) -> int:
    """Apply commander rolls to a same-context Q100000 zero-roll advantage.

    The caller supplies a valid zero-roll context. This does not forecast its
    terrain, commander, event, or side sources, nor the future random draws.
    """
    return zero_roll_advantage_raw + (side_0_roll_points - side_1_roll_points) * 100_000
