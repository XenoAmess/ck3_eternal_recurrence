"""Logical six-stage aggregate from the actual pre-state and captured appends.

The baseline is copied at the natural first callback, not inferred from current
Model values. Completion comparison is an observation at the existing paused
same-thread completion boundary, not a claim that intervening native code had
no effect. Full Person/Entry remain outside this family.
"""
from __future__ import annotations

from itertools import chain

from ..bridge.battle_person_six_stage_capture_12004 import (
    FIELD_NAME,
    emit_captured_person_pre_six_aggregate_12004,
    emit_captured_person_six_stage_requests_12004,
    normalize_person_six_stage_capture_12004,
)
from .battle_person_pc_merger_12004 import (
    Q_12004,
    fold_ordered_pc_contribution_12004,
)


def compose_captured_six_stage_postimage_12004(section: object) -> dict:
    """Start from the captured PC and apply only the actual ordered append calls."""
    baseline = emit_captured_person_pre_six_aggregate_12004(section)
    requests = emit_captured_person_six_stage_requests_12004(section)
    # The already qualified merger's unit-copy path initializes the logical
    # container with these exact baseline rows. This private seed is state,
    # not a claimed native append and is never included in emitted ordinals.
    initial_state = {"source_ordinal": None,
                     "property_block": baseline["property_block"],
                     "weight_q100000": Q_12004}
    result = fold_ordered_pc_contribution_12004(chain((initial_state,), requests))
    result.update(
        composition_kind="captured_pre_six_aggregate_and_natural_appends",
        source_ordinals=[request["source_ordinal"] for request in requests],
        pre_six_baseline_observed=True,
        historical_postimage_ready=True,
        character_id=baseline["character_id"],
        capture_sequence=baseline["capture_sequence"],
        capture_date_raw=baseline["capture_date_raw"],
        capture_thread_id=baseline["capture_thread_id"],
        context_identity=baseline["context_identity"],
        baseline_pc_identity=baseline["source_pc_identity"],
    )
    leaf = normalize_person_six_stage_capture_12004(section[FIELD_NAME])
    completion = leaf["post_six_aggregate"]
    comparison_ready = leaf["aggregate_postimage_comparison_ready"]
    result["completion_observation_ready"] = comparison_ready
    result["completion_observation_source_stage"] = completion["source_stage"]
    result["completion_pc_identity"] = completion["pc"]["identity"]
    result["completion_matches_composition"] = None
    if comparison_ready:
        observed = completion["pc"]["properties"]
        result["completion_matches_composition"] = (
            result["keys_u16"] == observed["keys_u16"]
            and result["values_q64"] == observed["values_q64"])
    return result
