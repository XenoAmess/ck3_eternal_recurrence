"""CK3 1.19.0.6 per-battle war-score arithmetic from observed inputs.

This is a reusable terminal/forecast component.  Callers must supply the
losing war participants' denominator and the loaded CB scale; a combat-side
starting strength or a UI score is not a substitute for either input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


Q = 100_000


@dataclass(frozen=True)
class NativeBattleScore:
    ratio_raw_q100000: int
    uncapped_raw_q100000: int
    row_raw_q100000: int
    attacker_relative_raw_q100000: int


def denominator_from_native_buckets(rows: Sequence[Sequence[int]]) -> tuple[int, int]:
    """Return native signed-int32 sum and its at-least-one divisor.

    Each row has eight quantity buckets in +C0,+00,+20,+40,+60,+80,+A0,+E0
    order.  Native accumulation wraps at 32 bits before the minimum is taken.
    """

    if not rows:
        raise ValueError("war participant bucket rows are required")
    total_u32 = 0
    for row in rows:
        if len(row) != 8 or any(
            isinstance(value, bool) or not isinstance(value, int)
            or not 0 <= value <= 2**31 - 1 for value in row
        ):
            raise ValueError("each participant needs eight nonnegative int32 buckets")
        total_u32 = (total_u32 + sum(row)) & 0xFFFFFFFF
    signed = total_u32 if total_u32 < 2**31 else total_u32 - 2**32
    return signed, max(1, signed)


def calculate_native_battle_score(
    *,
    hard_loss_raw_q100000: int,
    denominator_count: int,
    selected_cb_scale_raw_q100000: int,
    single_battle_cap_raw_q100000: int,
    winner_is_war_attacker: bool,
) -> NativeBattleScore:
    """Apply native integer order to one normal-result battle-score row."""

    values = (
        hard_loss_raw_q100000, denominator_count,
        selected_cb_scale_raw_q100000, single_battle_cap_raw_q100000,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0
           for value in values) or denominator_count == 0:
        raise ValueError("battle score needs nonnegative integers and a positive divisor")
    if not isinstance(winner_is_war_attacker, bool):
        raise ValueError("war winner side must be boolean")
    ratio = min(Q, hard_loss_raw_q100000 // denominator_count)
    uncapped = ratio * selected_cb_scale_raw_q100000 // Q
    row = min(uncapped, single_battle_cap_raw_q100000)
    return NativeBattleScore(
        ratio_raw_q100000=ratio,
        uncapped_raw_q100000=uncapped,
        row_raw_q100000=row,
        attacker_relative_raw_q100000=(row if winner_is_war_attacker else -row),
    )
