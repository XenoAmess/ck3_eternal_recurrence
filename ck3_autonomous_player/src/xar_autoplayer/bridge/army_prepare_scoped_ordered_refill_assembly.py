"""Compose captured fixed-chunk0 preparation with the shared ordered core."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from .army_scoped_ordered_refill_projection import (
    project_observed_prepared_ordered_physical_core_v1,
    project_scoped_ordered_refill_from_physical_v1,
)

_INPUT_BASIS = "same_capture_fixed_chunk0_conditional_preparation_ordered_occurrences"


def project_fixed_chunk0_prepare_scoped_ordered_refill_v1(
    row: Mapping[str, object], preparation: Mapping[str, object],
) -> dict[str, object]:
    """Replace private prepared scalars, execute one core, then refresh DATA.

    Both arguments come from the same normalized Strength row. Preparation
    changes no held predicate context, physical chunk or observed prepared148.
    The shared core retains native occurrence order and decides which missing
    fractions are actually demanded by that execution roster.
    """
    inputs = row.get("scoped_ordered_refill_inputs_v1")
    prepared_by_id = {
        item["persistent_regiment_id"]: item
        for item in preparation["persistent_regiments"]
    }
    joins = []
    if isinstance(inputs, dict):
        private_inputs = deepcopy(inputs)
        for persistent in private_inputs["persistent_regiments"]:
            identity = persistent["persistent_regiment_id"]
            prepared = prepared_by_id.get(identity)
            ready = prepared is not None and prepared["preparation_ready"]
            fraction = prepared["conditional_prepared_fraction_raw"] if ready else None
            joins.append({
                "persistent_regiment_id": identity,
                "fixed_chunk_index": 0,
                "observed_prepared_fraction_raw": persistent["prepared_fraction_raw"],
                "conditional_prepared_fraction_raw": fraction,
                "preparation_ready": bool(ready),
                "preparation_branch": prepared["preparation_branch"] if prepared else "unavailable",
                "missing_inputs": list(prepared["missing_inputs"]) if prepared else
                    ["fixed_chunk0_preparation_inputs_v1:persistent_row"],
            })
            persistent["prepared_fraction_raw"] = fraction
        physical = project_observed_prepared_ordered_physical_core_v1(
            private_inputs, prepared_input_basis=_INPUT_BASIS)
    else:
        physical = {
            "input_basis": _INPUT_BASIS, "missing_inputs": [],
            "physical_chunks": [], "occurrences": [], "failed_persistent_ids": [],
        }
    result = project_scoped_ordered_refill_from_physical_v1(row, physical)
    # Keep useful per-persistent preparation failures next to the shared core's
    # own missing-input receipts; known independent physical rows stay visible.
    failed = set(physical["failed_persistent_ids"])
    preparation_missing = [
        f'persistent:{join["persistent_regiment_id"]}:preparation:{missing}'
        for join in joins if join["persistent_regiment_id"] in failed
        for missing in join["missing_inputs"]
    ]
    result["missing_inputs"] = list(dict.fromkeys(
        [*result["missing_inputs"], *preparation_missing]))
    result.update({
        "projection_kind": "conditional_fixed_chunk0_prepare_scoped_ordered_core",
        "ordered_refill_entry_mode": "fixed_chunk0_prepare",
        "input_basis": _INPUT_BASIS,
        "preparation_context_basis": "current_frozen_context_preparation",
        "conditional_preparation_projected": True,
        "preparation_inputs_ready": preparation["preparation_ready"],
        "preparation_join": joins,
        "cache_write": False,
        "full_ordered_regular_refill": False,
    })
    return result


def project_fixed_chunk0_prepare_scoped_ordered_refills_v1(
    selected_rows: Sequence[Mapping[str, object]],
    preparation_projections: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Consume the service's aligned same-row preparation results once."""
    return [project_fixed_chunk0_prepare_scoped_ordered_refill_v1(row, preparation)
            for row, preparation in zip(selected_rows, preparation_projections, strict=True)]
