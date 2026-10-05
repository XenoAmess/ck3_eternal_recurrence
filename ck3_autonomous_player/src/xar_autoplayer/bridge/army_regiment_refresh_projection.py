"""Conditional2633340 current/max stores from complete associated native DATA.

Other refresh statistics and invalid-record removals are outside this helper.
This is a same-input source replay, never an observed post-stage aggregate.
"""
from __future__ import annotations

from typing import Mapping, Sequence


def _signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def project_observed_raised_regiment_refresh(
    data_snapshot: Mapping[str, object], *,
    physical_chunks_after: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Project only the exact current/max stores at26338C0/26338C3.

    With an explicit chunk replay, every DATA occurrence reads its matching
    resulting physical chunk. Aliases count repeatedly, as in the native loop.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_raised_regiment_refresh",
        "source_contract_game_version": "1.20.0.3",
        "army_regiment_id": data_snapshot.get("army_regiment_id"),
        "status": "unavailable", "current_maximum_ready": False,
        "actual_refresh": False, "current_soldiers": None,
        "maximum_soldiers": None, "soldiers_scale": 1,
        "input_basis": "conditional_chunk_writeback" if physical_chunks_after is not None else "observed_same_frame_DATA",
        "missing_inputs": [], "record_contributions": [],
    }
    character = data_snapshot.get("native_loss_writer_skipped")
    if type(character) is not bool:
        result["missing_inputs"] = ["native_2634880_character_predicate"]
        return result
    if character:
        return {**result, "status": "available", "current_maximum_ready": True,
                "character_override": True, "current_soldiers": 1,
                "maximum_soldiers": 1}
    records = data_snapshot.get("records")
    if data_snapshot.get("status") != "available" or not isinstance(records, list):
        result["missing_inputs"] = ["complete_available_DATA"]
        return result
    projected = None
    if physical_chunks_after is not None:
        projected = {(chunk["persistent_regiment_id"], chunk["chunk_index"]): chunk
                     for chunk in physical_chunks_after}
    current_sum = maximum_sum = 0
    contributions = []
    for record in records:
        key = (record["persistent_regiment_id"], record["chunk_index"])
        if projected is not None and key not in projected:
            result["missing_inputs"] = ["complete_projected_physical_chunks"]
            return result
        physical = record if projected is None else projected[key]
        current = physical.get("current_soldiers")
        maximum = physical.get("maximum_soldiers")
        state = record.get("state_raw")
        if any(type(value) is not int for value in (current, maximum, state)):
            result["missing_inputs"] = ["complete_current_maximum_state"]
            return result
        contribution = maximum if state == 3 and current == 0 else current
        current_sum = _signed32(current_sum + contribution)
        maximum_sum = _signed32(maximum_sum + maximum)
        contributions.append({"record_index": record["record_index"],
                              "persistent_regiment_id": key[0], "chunk_index": key[1],
                              "physical_current_soldiers": current,
                              "effective_current_contribution": contribution,
                              "maximum_contribution": maximum})
    return {**result, "status": "available", "current_maximum_ready": True,
            "character_override": False, "current_soldiers": current_sum,
            "maximum_soldiers": maximum_sum, "record_contributions": contributions}
