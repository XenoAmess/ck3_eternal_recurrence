"""Join separately supplied prospective native dates to observed all-phase slots."""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Sequence

from .army_future_daily_supply_schedule_contract import (
    FAMILY_KEY,
    normalize_future_daily_supply_schedule_inputs_v1,
)


def project_future_daily_supply_schedule_v1(
    row_or_family: dict[str, object], *, prospective_frames: Sequence[dict[str, object]] = (),
) -> dict[str, object] | None:
    """No calendar is inferred: each prospective frame supplies its date and stored D.

    The current all30-phase input can identify every matching phase. A supplied
    prospective date maps to a count only while the observed bucket membership
    remains unchanged; callback eligibility and resulting stock stay separate.
    """
    family = (row_or_family if row_or_family.get("source") ==
              "native_future_daily_supply_schedule_inputs_12004" else row_or_family.get(FAMILY_KEY))
    normalized = normalize_future_daily_supply_schedule_inputs_v1(family)
    if normalized is None:
        return None
    phases = normalized["phases"]
    projected_frames: list[dict[str, object]] = []
    result: dict[str, object] = {
        "schema_version": 1,
        "source": "same_input_conditional_future_daily_supply_schedule_v1",
        "ready": normalized["ready"],
        "status": normalized["status"],
        "unavailable_reason": normalized["unavailable_reason"],
        "subject_army_id_u32": normalized["subject_army_id_u32"],
        "subject_carmy_id_u32": normalized["subject_carmy_id_u32"],
        "current_date_storage_raw64": normalized["current_date_storage_raw64"],
        "native_day_index_raw_i32": normalized["native_day_index_raw_i32"],
        "selected_phase_index_i32": normalized["selected_phase_index_i32"],
        "observed_matching_phases": [
            {"phase_index_i32": phase["phase_index_i32"],
             "matching_positions": list(phase["matching_positions"]),
             "subject_occurrence_count_i32": phase["subject_occurrence_count_i32"]}
            for phase in phases if phase["ready"] and phase["subject_occurrence_count_i32"] > 0
        ],
        "unavailable_phases": [phase["phase_index_i32"] for phase in phases if not phase["ready"]],
        "prospective_frames": projected_frames,
        "condition": "separately_supplied_native_date_and_day_with_observed_buckets_unchanged",
        "calendar_derived": False,
        "actual_future_callback_observed": False,
        "future_bucket_mutations_reconstructed": False,
        "future_supply_eligibility_ready": False,
        "future_stock_or_strength_ready": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
    for ordinal, frame in enumerate(prospective_frames):
        if not isinstance(frame, dict) or set(frame) != {"date_raw_i32", "native_day_index_raw_i32"}:
            raise ValueError("prospective supply frame needs its own native date and stored day")
        if any(type(frame[key]) is not int or not -(1 << 31) <= frame[key] < (1 << 31)
               for key in frame):
            raise ValueError("prospective supply frame date/day must be signed32")
        phase_index = (frame["native_day_index_raw_i32"] & 0xFFFFFFFF) % 30
        phase = phases[phase_index] if phases else None
        ready = bool(phase and phase["ready"])
        projected_frames.append({
            "prospective_index": ordinal,
            "date_raw_i32": frame["date_raw_i32"],
            "native_day_index_raw_i32": frame["native_day_index_raw_i32"],
            "selected_phase_index_i32": phase_index,
            "conditional_bucket_occurrences_ready": ready,
            "matching_positions": deepcopy(phase["matching_positions"]) if ready else None,
            "subject_occurrence_count_i32": phase["subject_occurrence_count_i32"] if ready else None,
            "unavailable_reason": None if ready else (
                phase["unavailable_reason"] if phase else normalized["unavailable_reason"]
            ),
            "actual_callback_observed": False,
        })
    return result
