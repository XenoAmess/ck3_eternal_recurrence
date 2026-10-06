"""Conditional associated current/max writes for one regular refill core call.

Prepared fractions and chunk predicates belong to the observed input frame.
This does not execute manager dispatch or replace the monthly entry frame.
"""
from __future__ import annotations

from collections.abc import Mapping

from ..replenishment_numeric import observed_persistent_outputs
from .army_regiment_refresh_projection import project_observed_raised_regiment_refresh


def _signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def project_conditional_associated_refill_current(
    army: Mapping[str, object],
) -> dict[str, object]:
    """Apply one observed262C9D0 q per physical chunk, then refresh DATA sums.

    Native2A98BA8 ADD wraps signed32. Available associated chunks cannot enter
    the dispatcher pair-clear branch, which requires association minus one.
    DATA aliases share one ADD and remain separate refresh contributions.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_associated_regular_refill_current_maximum",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "observed_prepared_cache_and_chunk_predicates; one_explicit_core_invocation_per_observed_persistent",
        "status": "unavailable", "associated_chunks_ready": False,
        "associated_current_maximum_ready": False,
        "complete_persistent_requests_ready": False,
        "actual_replenishment": False, "actual_post_stage_current": None,
        "full_regular_refill_ready": False, "full_monthly_ready": False,
        "physical_chunks": [], "regiment_refreshes": [],
        "conditional_regiment_strengths": None, "persistent_core_coverage": [],
        "missing_inputs": [],
        "excluded_stages": ["manager_roster_order_and_preparation",
                            "24e11b0_army_statistics",
                            "post_refill_supply_change_and_capacity"],
    }
    snapshots = army.get("regiment_replenishment_records_v1")
    if army.get("status") != "available" or not isinstance(snapshots, list):
        result["missing_inputs"] = ["available_associated_DATA_snapshot"]
        return result

    outputs = observed_persistent_outputs([army])
    calculations = {
        (group["persistent_regiment_id"], ordinal): (
            group["status_by_chunk"][ordinal], group["same_input_q_by_chunk"][ordinal])
        for group in outputs for ordinal in range(7)
    }
    coverage = []
    core_admission = {}
    for group in outputs:
        qualified = [item["calculation"]["native_core_chunk_qualifies"]
                     for observations in group["observations_by_chunk"]
                     for item in observations if item["calculation"] is not None]
        coverage.append({
            "persistent_regiment_id": group["persistent_regiment_id"],
            "all_seven_requests_observed": group["all_seven_observed"],
            "native_core_any_qualified": (True if any(qualified) else
                                          False if group["all_seven_observed"] else None),
            "status_by_chunk": group["status_by_chunk"],
        })
        core_admission[group["persistent_regiment_id"]] = coverage[-1]["native_core_any_qualified"]

    observations: dict[tuple[int, int], list[tuple[Mapping[str, object], Mapping[str, object]]]] = {}
    for snapshot in snapshots:
        for record in snapshot["records"]:
            key = (record["persistent_regiment_id"], record["chunk_index"])
            if key[0] != -1 and 0 <= key[1] < 7:
                observations.setdefault(key, []).append((snapshot, record))
    chunks = []
    missing = []
    for key, aliases in observations.items():
        chunk: dict[str, object] = {
            "persistent_regiment_id": key[0], "chunk_index": key[1],
            "status": "unavailable", "current_soldiers_before": None,
            "same_input_q": None, "current_soldiers": None,
            "maximum_soldiers": None, "state_raw": None,
            "chunk_army_regiment_id": None,
            "physical_add_count": None, "pair_clear_reachable": None,
            "data_occurrences": [{"army_regiment_id": snapshot["army_regiment_id"],
                                  "record_index": record["record_index"]}
                                 for snapshot, record in aliases],
            "missing_inputs": [],
        }
        status, quantity = calculations.get(key, ("unobserved", None))
        reasons = []
        if status != "available":
            reasons.append("available_same_input_262c9d0_request")
        if any(record["status"] != "available" for _, record in aliases):
            reasons.append("available_physical_chunk_observation")
        if any(record.get("chunk_army_regiment_id") != snapshot["army_regiment_id"]
               or record.get("chunk_army_regiment_id") in (None, -1)
               for snapshot, record in aliases):
            reasons.append("observed_non_minus_one_chunk_association")
        fields = ("current_soldiers", "maximum_soldiers", "state_raw", "chunk_army_regiment_id")
        signatures = [tuple(record.get(field) for field in fields) for _, record in aliases]
        if any(signature != signatures[0] for signature in signatures[1:]):
            reasons.append("consistent_physical_alias_observations")
        if reasons:
            chunk["missing_inputs"] = reasons
            missing.append({"persistent_regiment_id": key[0], "chunk_index": key[1],
                            "inputs": reasons})
        else:
            record = aliases[0][1]
            chunk.update({
                "status": "available", "current_soldiers_before": record["current_soldiers"],
                "same_input_q": quantity,
                "current_soldiers": _signed32(record["current_soldiers"] + quantity),
                "maximum_soldiers": record["maximum_soldiers"],
                "state_raw": record["state_raw"],
                "chunk_army_regiment_id": record["chunk_army_regiment_id"],
                "physical_add_count": (None if core_admission[key[0]] is None else
                                       1 if core_admission[key[0]] else 0),
                "pair_clear_reachable": False,
            })
        chunks.append(chunk)

    ready_chunks = [chunk for chunk in chunks if chunk["status"] == "available"]
    refreshes = [project_observed_raised_regiment_refresh(
        snapshot, physical_chunks_after=ready_chunks) for snapshot in snapshots]
    strengths = army.get("regiment_strengths")
    roster_ready = isinstance(strengths, list) and [
        row["army_regiment_id"] for row in strengths
    ] == [row["army_regiment_id"] for row in snapshots]
    if not roster_ready:
        missing.append("complete_same_order_ArRg_DATA_roster")
    for refresh in refreshes:
        if not refresh["current_maximum_ready"]:
            missing.append({"army_regiment_id": refresh["army_regiment_id"],
                            "inputs": refresh["missing_inputs"]})
    aggregate_ready = roster_ready and all(row["current_maximum_ready"] for row in refreshes)
    chunks_ready = len(ready_chunks) == len(chunks)
    return {
        **result,
        "status": "available" if chunks_ready and aggregate_ready else (
            "partial" if ready_chunks or any(row["current_maximum_ready"] for row in refreshes)
            else "unavailable"),
        "associated_chunks_ready": chunks_ready,
        "associated_current_maximum_ready": aggregate_ready,
        "complete_persistent_requests_ready": all(group["all_seven_observed"] for group in outputs),
        "physical_chunks": chunks, "regiment_refreshes": refreshes,
        "conditional_regiment_strengths": [
            {"army_regiment_id": row["army_regiment_id"],
             "current_soldiers": row["current_soldiers"],
             "maximum_soldiers": row["maximum_soldiers"], "scale": 1}
            for row in refreshes
        ] if aggregate_ready else None,
        "persistent_core_coverage": coverage, "missing_inputs": missing,
    }
