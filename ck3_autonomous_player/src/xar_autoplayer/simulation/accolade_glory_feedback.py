"""Isolated exact-build projection of one ``add_glory`` write.

This is a component of a future phase-event trial, not a battle probability.
The frozen phase-event AST currently records glory as ``observational_only``;
it does not identify every optional accolade target or the amount of a reached
branch.  Callers must supply those values from a separately proven execution.
"""

from __future__ import annotations


_SCALE = 100_000
_INT64_MAX = (1 << 63) - 1
_INT64_MIN = -(1 << 63)
_STOCK_RANK_THRESHOLDS_RAW = (
    10_000_000,
    30_000_000,
    60_000_000,
    100_000_000,
    150_000_000,
    210_000_000,
)
_STOCK_GAIN_RAW = {
    "minimal_glory_gain": 1_000_000,
    "minor_glory_gain": 2_500_000,
}


class AccoladeGloryProjectionUnavailable(ValueError):
    """An input lies outside the documented exact-build projection boundary."""


def stock_phase_glory_delta_raw(name: str) -> int:
    """Return the two stock gain values used in knight phase events."""

    try:
        return _STOCK_GAIN_RAW[name]
    except (KeyError, TypeError) as error:
        raise AccoladeGloryProjectionUnavailable(
            "unknown stock knight phase glory gain"
        ) from error


def project_accolade_glory_write(
    *,
    accolade_id: int,
    glory_before_raw: int,
    delta_raw: int,
    owner_gain_modifier_raw: int,
) -> dict[str, object]:
    """Project the native write/rank sequence with explicit Q100000 inputs.

    Positive input is multiplied by ``1 + accolade_glory_gain_mult``. Negative
    input is not multiplied. The projection rejects unusual arithmetic needing
    a wider native overflow trace and never promotes battle fidelity gates.
    """

    if isinstance(accolade_id, bool) or not isinstance(accolade_id, int) or accolade_id < 0:
        raise AccoladeGloryProjectionUnavailable("accolade ID is malformed")
    before = _int64(glory_before_raw, "glory before")
    delta = _int64(delta_raw, "glory delta")
    modifier = _int64(owner_gain_modifier_raw, "owner glory gain modifier")
    if before < 0:
        raise AccoladeGloryProjectionUnavailable("glory before is negative")
    factor = _int64(_SCALE + modifier, "positive gain factor")
    if factor < 0:
        raise AccoladeGloryProjectionUnavailable("positive gain factor is negative")
    if delta > 0:
        product = delta * factor
        if product > _INT64_MAX:
            raise AccoladeGloryProjectionUnavailable(
                "native wide positive multiplication requires readback"
            )
        effective_delta = product // _SCALE
    else:
        effective_delta = delta
    summed = _int64(before + effective_delta, "glory before clamp")
    after = max(0, summed)
    rank_before = _rank(before)
    rank_after = _rank(after)
    return {
        "status": "isolated_projection_requires_native_readback",
        "accolade_id": accolade_id,
        "glory_raw_before": before,
        "input_delta_raw": delta,
        "owner_gain_modifier_raw": modifier,
        "effective_delta_raw": effective_delta,
        "glory_raw_after": after,
        "actual_change_raw": after - before,
        "rank_before": rank_before,
        "rank_after": rank_after,
        "rank_changed": rank_before != rank_after,
        "on_accolade_glory_change_expected": True,
        "on_accolade_rank_change_expected": rank_before != rank_after,
        "parameter_and_combat_refresh_timing_verified": False,
        "battle_horizon_feedback_ready": False,
        "planner_usable": False,
        "active_attack_allowed": False,
    }


def _rank(glory_raw: int) -> int:
    for index in range(len(_STOCK_RANK_THRESHOLDS_RAW) - 1, -1, -1):
        if glory_raw >= _STOCK_RANK_THRESHOLDS_RAW[index]:
            return index + 1
    return 1


def _int64(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not _INT64_MIN <= value <= _INT64_MAX:
        raise AccoladeGloryProjectionUnavailable(f"{name} is not signed int64")
    return value
