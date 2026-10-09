"""Source-closed native duration factors and same-query scalar clock meaning.

The actual flag parser374CE20 writes these factors into the duration node
consumed by374D350. Caller2D567AE forwards that result to3728400 on the same
Character context+8; its inner clock+20 is the full scalar context clock+28.
This module interprets that numeric domain. An explicit projected unit also
retains the producer's same-context calendar retry. Keyword names and the
scalar set_variable parser remain separate source dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass


# Actual decimal token IDs read from ScriptNode+E8. Names are not inferred.
NATIVE_DURATION_FACTORS_12004 = ((1300, 1), (1301, 30), (1302, 365), (1327, 7))


@dataclass(frozen=True)
class NativeDurationLiteral12004:
    token_id: int
    literal_i32: int
    accepted: bool
    multiplier_i32: int
    clock_steps_i32: int | None


@dataclass(frozen=True)
class CrownCooldownNativeClock12004:
    state: str
    current_clock_raw: int | None
    native_clock_deadline_raw: int | None
    remaining_native_clock_steps: int | None
    query_retry_date_raw: int | None
    duration_token_factors: tuple[tuple[int, int], ...] = NATIVE_DURATION_FACTORS_12004
    keyword_names_qualified: bool = False
    calendar_deadline_ready: bool = False


def scale_native_duration_literal_12004(
    token_id: int, literal_i32: int,
) -> NativeDurationLiteral12004:
    """Scale a supplied native literal using the actual parser's token factor.

    This is the evaluator's nonrange, nonexpression literal path. It does
    not parse a script keyword name, supply the observed law's token, select
    a random range or evaluate a native expression. IMUL's low32 result is
    returned as signed32, including zero/negative/overflow results. The
    subsequent writer's nonpositive-duration classification is separate.
    """
    if type(token_id) is not int:
        raise ValueError("native duration token must be an integer ID")
    if type(literal_i32) is not int or not -(1 << 31) <= literal_i32 < (1 << 31):
        raise ValueError("native duration literal must be signed32")
    factor = dict(NATIVE_DURATION_FACTORS_12004).get(token_id)
    if factor is None:
        # Actual parser writes factor0 and returns false before evaluation.
        return NativeDurationLiteral12004(token_id, literal_i32, False, 0, None)
    product = (literal_i32 * factor) & 0xFFFFFFFF
    if product >= 0x80000000:
        product -= 0x100000000
    return NativeDurationLiteral12004(token_id, literal_i32, True, factor, product)


def interpret_crown_cooldown_native_clock_12004(
    raw_observation: object, *, date_raw: int,
) -> CrownCooldownNativeClock12004:
    """Interpret existing raw9 through its production strict normalizer.

    Old-unit timed rows retain their native-counter deadline without a
    calendar claim. The new projected unit retains the producer's positive
    retry date, whose same-query context/count relationship is checked by
    the production law transport. No date is inferred from duration factors.
    Timed remaining-1, absence and untimed rows keep their distinct meanings.
    """
    from .realm_law_paused_private_transport import (
        COOLDOWN_PROJECTED_REMAINING_UNIT,
        normalize_crown_authority_cooldown_raw_v1,
    )

    value = normalize_crown_authority_cooldown_raw_v1(raw_observation, date_raw=date_raw)
    if not value["read_available"]:
        return CrownCooldownNativeClock12004("unavailable", None, None, None, None)
    current = value["current_clock_raw"]
    remaining = value["remaining_raw"]
    if not value["present"]:
        return CrownCooldownNativeClock12004(
            "absent", current, None, remaining, value["retry_date_raw"],
        )
    if not value["timed"]:
        return CrownCooldownNativeClock12004("untimed", current, None, remaining, None)
    return CrownCooldownNativeClock12004(
        "timed", current, value["expiry_raw"], remaining, value["retry_date_raw"],
        calendar_deadline_ready=(
            value["remaining_unit"] == COOLDOWN_PROJECTED_REMAINING_UNIT
        ),
    )
