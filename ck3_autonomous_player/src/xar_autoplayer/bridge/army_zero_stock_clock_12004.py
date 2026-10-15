"""Readonly zero-stock capture candidates and exact-zero retained writer facts.

No clock, admission or casualty formula is duplicated. Existing native-produced
next dates and pointer buckets feed the existing source-owned projections.
"""
from __future__ import annotations

from collections.abc import Mapping

from .army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1
from .army_next_updater_write_projection import project_source_derived_next_updater_writes_v1
from .army_source_derived_next_daily_supply_frame_projection import project_native_next_daily_supply_schedule_v1
from .army_update_clock_contract import normalize_army_update_clock_v1


def _all_known(values: tuple[bool | None, ...]) -> bool | None:
    if False in values:
        return False
    return True if all(value is True for value in values) else None


def project_zero_stock_next_callback_candidate_12004(row: dict) -> dict:
    """One next-day capture opportunity, conditional on unchanged earlier inputs.

    True selects a useful zero-entry observation window. It does not assert that
    stock remains zero after the rate, a budget is positive, or a writer executes.
    Selected-phase readiness is independent of other unavailable phase headers.
    """
    schedule = project_native_next_daily_supply_schedule_v1(row)
    writes = project_source_derived_next_updater_writes_v1(row)
    clock = normalize_army_update_clock_v1(row.get("army_update_clock_v1"))
    source = schedule.get("source_next_pair") if schedule else None
    coherent = None
    if source and source["ready"] and clock and clock["ready"]:
        if any(clock[left] != source[right] for left, right in (
            ("current_date_raw", "current_date_raw_i32"),
            ("native_day_index", "current_native_day_index_raw_i32"),
        )):
            raise ValueError("zero-stock candidate clock differs from same-row native next seed")
        coherent = True
    frames = schedule["prospective_frames"] if schedule else []
    selected = frames[0] if len(frames) == 1 and source and source["ready"] else None
    positions = (list(selected["matching_positions"])
                 if selected and selected["conditional_bucket_occurrences_ready"] else None)
    count = len(positions) if positions is not None else None
    stock = row.get("current_supply_raw")
    zero = stock == 0 if type(stock) is int and -(1 << 63) <= stock < (1 << 63) else None
    admission = writes["next_admission"]
    admitted = admission["admitted"] if admission["ready"] else None
    typed = (row.get("status") == "available" and type(row.get("native_carmy_id")) is int
             and type(row.get("army_id")) is int)
    candidate = _all_known((typed, zero, count > 0 if count is not None else None,
                            admitted, coherent))
    return dict(
        source="existing_next_pair_bucket_and_updater_gate_join_12004",
        conditional_zero_entry_capture_candidate=candidate,
        observed_current_stock_is_exact_zero=zero,
        same_row_clock_seed_matches=coherent,
        next_date_raw_i32=selected["date_raw_i32"] if selected else None,
        next_native_day_index_raw_i32=selected["native_day_index_raw_i32"] if selected else None,
        next_selected_phase_i32=selected["selected_phase_index_i32"] if selected else None,
        conditional_original_pointer_positions=positions,
        conditional_callback_opportunity_count=count,
        next_admission=admission,
        condition="captured receiver, stock, bucket membership and all non-date gate inputs unchanged through earlier stages",
        repeated_occurrences_are_independent=True,
        successful_updater_count=None,
        zero_stock_at_actual_writer_observed=False,
        physical_loss_observed=False,
        complete_cycle_observed=False,
        full_daily_supply_transition_ready=False,
        full_monthly_ready=False,
    )


def select_actual_zero_stock_supply_preferred_12004(
    row: Mapping, *, game_version: str, executable_sha256: str,
    callback_after_sequence: int, loss_after_sequence: int,
) -> dict:
    """Select single complete direct supply debits with writer-time stock == 0.

    This narrow positive witness deliberately leaves residual, combined and full
    interval totals separate. It does not use callback entry/return stock or net
    Army strength. Exact-build/session normalization remains with the query owner.
    """
    result = dict(source="keyed_daily_supply_preferred_exact_zero_writer_facts",
                  positive_invocations=[], positive_physical_debit_observed=False,
                  selected_invocation_debit_sum=None, unknown_reasons=[],
                  complete_interval_loss_total_ready=False, complete_cycle_observed=False)
    for key in ("actual_supply_callback_observations_v1", "actual_loss_writer_observations_v1"):
        family = row.get(key)
        if not isinstance(family, Mapping) or family.get("observer_installed") is not True:
            result["unknown_reasons"].append(key + ".observer_installed")
    if result["unknown_reasons"]:
        return result
    joined = join_actual_supply_parent_writer_observations_v1(
        row, game_version=game_version, executable_sha256=executable_sha256,
        callback_after_sequence=callback_after_sequence, loss_after_sequence=loss_after_sequence)
    result["unknown_reasons"] = list(joined["unknown_reasons"])
    if result["unknown_reasons"]:
        return result
    callbacks = {event["sequence"]: event for event in
                 row["actual_supply_callback_observations_v1"]["events"]}
    for event in joined["events"]:
        debit = event["physical_debit_soldiers"]
        callback = callbacks.get(event["callback_sequence"])
        if (event["status"] == "joined" and event["source_supply_preferred"] is True
                and type(event["stock_at_writer_entry_raw"]) is int
                and event["stock_at_writer_entry_raw"] == 0
                and type(debit) is int and debit > 0 and callback
                and callback["caller_return_rva"] == 0x2A9AB4B):
            result["positive_invocations"].append(dict(event))
    if result["positive_invocations"]:
        result["positive_physical_debit_observed"] = True
        result["selected_invocation_debit_sum"] = sum(
            event["physical_debit_soldiers"] for event in result["positive_invocations"])
    return result
