"""Narrow CK3 1.19.0.6 stock phase-event reward arithmetic.

These functions evaluate source-defined amounts when the caller supplies the
relevant native character facts. They do not choose/fire an event, draw the
prowess branch, apply game callbacks, or authorize battle planning.
"""

from __future__ import annotations

from .combat_core import FIXED_SCALE, trunc_div_toward_zero


MEDIUM_PRESTIGE_GAIN_RAW = 150 * FIXED_SCALE


def knight_kill_inverse_prestige_raw(
    *, victim_primary_title_tier: int | None, victim_is_lowborn: bool
) -> int:
    """Mirror `knight_prestige_gain_on_kill_inverse` at signed Q100000.

    `root` in `knight_killed` is the slain knight. The script starts at 150,
    multiplies by a positive primary-title tier if present, then halves for
    lowborn roots. A missing primary title leaves the base amount unchanged.
    """
    if (victim_primary_title_tier is not None and (
        isinstance(victim_primary_title_tier, bool)
        or not isinstance(victim_primary_title_tier, int)
        or not 1 <= victim_primary_title_tier <= 5
    )):
        raise ValueError("victim_primary_title_tier must be 1..5 or None")
    if not isinstance(victim_is_lowborn, bool):
        raise ValueError("victim_is_lowborn must be boolean")
    amount = MEDIUM_PRESTIGE_GAIN_RAW
    if victim_primary_title_tier is not None:
        amount *= victim_primary_title_tier
    if victim_is_lowborn:
        amount = trunc_div_toward_zero(amount, 2)
    return amount


__all__ = ["MEDIUM_PRESTIGE_GAIN_RAW", "knight_kill_inverse_prestige_raw"]
