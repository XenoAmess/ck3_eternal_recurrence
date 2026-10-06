"""Strict optional native roll bounds for one candidate at a requested target.

The observation is independent of manual assignment eligibility and of the
candidate's generic quality. Signed zero, negative and reversed bounds are
native values; this module adds no commander selection policy.
"""

from __future__ import annotations


CANDIDATE_TARGET_ROLL_SOURCE = "native_current_candidate_target_roll_context"


def commander_target_province_id(value: object) -> int:
    """Validate the requested native positive int32 ProvinceID."""
    if type(value) is not int or not 1 <= value <= 2**31 - 1:
        raise ValueError("target_province_id must be a positive native int32 ProvinceID")
    return value


def normalize_candidate_target_roll_bounds(
    value: object,
    *,
    expected_target_province_id: int | None,
) -> dict[str, object] | None:
    """Preserve null compatibility and validate a present native observation."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("native candidate.target_roll_bounds must be an object or null")
    if expected_target_province_id is None:
        raise ValueError("native candidate.target_roll_bounds lacks a requested target")
    target = commander_target_province_id(expected_target_province_id)
    status = value.get("status")
    if (
        status not in {"available", "unavailable"}
        or value.get("source") != CANDIDATE_TARGET_ROLL_SOURCE
        or type(value.get("source_target_province_id")) is not int
        or value.get("source_target_province_id") != target
    ):
        raise ValueError("native candidate.target_roll_bounds status/source/target disagrees")
    for name in ("effective_min_roll", "effective_max_roll"):
        if name not in value:
            raise ValueError(f"native candidate.target_roll_bounds.{name} is missing")
        amount = value[name]
        if (
            status == "available"
            and (type(amount) is not int or not -(2**31) <= amount <= 2**31 - 1)
            or status == "unavailable" and amount is not None
        ):
            raise ValueError(f"native candidate.target_roll_bounds.{name} must match its native status")
    if "unavailable_reason" not in value:
        raise ValueError("native candidate.target_roll_bounds.unavailable_reason is missing")
    reason = value["unavailable_reason"]
    if (
        status == "available" and reason is not None
        or status == "unavailable" and (not isinstance(reason, str) or not reason.strip())
    ):
        raise ValueError("native candidate.target_roll_bounds.unavailable_reason must match its native status")
    return dict(value)
