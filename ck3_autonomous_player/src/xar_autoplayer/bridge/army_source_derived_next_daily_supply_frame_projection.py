"""Join only a same-row native-produced pair to the existing schedule projector."""
from __future__ import annotations

from .army_future_daily_supply_schedule_projection import project_future_daily_supply_schedule_v1
from .army_source_derived_next_daily_supply_frame_contract import (
    FAMILY_KEY, normalize_source_derived_next_daily_supply_frame_inputs_v1,
)


def project_native_next_daily_supply_schedule_v1(
    same_query_strength: dict[str, object],
) -> dict[str, object] | None:
    """No caller frame or calendar arithmetic; unavailable leaf retains old summary."""
    frame = normalize_source_derived_next_daily_supply_frame_inputs_v1(
        same_query_strength.get(FAMILY_KEY),
        expected_army_id=same_query_strength.get("army_id"),
        expected_carmy_id=same_query_strength.get("native_carmy_id"),
    )
    if frame is None or not frame["ready"]:
        return project_future_daily_supply_schedule_v1(same_query_strength)
    schedule = same_query_strength.get("future_daily_supply_schedule_inputs_v1")
    if isinstance(schedule, dict):
        for schedule_key, frame_key in (
            ("subject_army_id_u32", "subject_army_id_u32"),
            ("subject_carmy_id_u32", "subject_carmy_id_u32"),
            ("current_date_storage_raw64", "current_date_storage_raw64"),
            ("current_date_raw_i32", "current_date_raw_i32"),
            ("native_day_index_raw_i32", "current_native_day_index_raw_i32"),
        ):
            observed = schedule.get(schedule_key)
            if observed is not None and observed != frame[frame_key]:
                raise ValueError("native next supply frame clock differs from the same-row schedule")
    projected = project_future_daily_supply_schedule_v1(
        same_query_strength,
        prospective_frames=({
            "date_raw_i32": frame["source_derived_next_date_raw_i32"],
            "native_day_index_raw_i32": frame["source_derived_next_native_day_index_raw_i32"],
        },),
    )
    if projected is not None:
        projected.update(
            condition="source_derived_next_date_and_day_with_observed_buckets_unchanged",
            calendar_derived=True,
            actual_future_date_stage_observed=False,
            full_future_cdate64_reconstructed=False,
            source_next_pair=frame,
        )
        for selected in projected["prospective_frames"]:
            selected.update(
                origin="source_derived_conditional_next_date_pair",
                actual_native_frame_observed=False,
            )
    return projected
