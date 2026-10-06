"""Pure current-frame leaf adapter for the existing normal-finalizer kernel."""

from __future__ import annotations

from typing import Literal, Mapping

from ..bridge.current_finalizer_manager_inputs_contract_v1 import (
    CURRENT_FINALIZER_MANAGER_INPUTS_V1_KEY,
    normalize_current_finalizer_manager_inputs_v1,
)
from .battle_current_normal_finalizer import CurrentNormalFinalizerManagerInputs


def _optional_bool(value: object, field: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise ValueError(f"{field} requires an explicit boolean or unavailable None")
    return value


def current_finalizer_manager_inputs_from_frame_v1(
    frame: Mapping[str, object],
    *,
    entry_kind: Literal["daily_row", "suppression_sweep"] = "daily_row",
    primary_hostile: bool | None = None,
    finalized: bool | None = None,
    processing: bool | None = None,
    result_present: bool | None = None,
) -> CurrentNormalFinalizerManagerInputs:
    """Map observed admission/pending and preserve explicit caller conditions.

    ``frame`` is an already normalized available battle-control frame. Only
    row admission and pending are supplied by its readonly manager leaf.
    ``entry_kind`` names the caller's hypothetical invocation context; it is
    never inferred from phase3. The remaining arguments are caller conditions,
    even if a condition coincides with a field in the current snapshot. The
    existing daily-row kernel itself models the post-phase processing clear.
    Missing/null manager data remain None and cannot unlock a normal branch.
    """
    if not isinstance(frame, Mapping) or frame.get("status") != "available":
        raise ValueError("an available normalized battle-control frame is required")
    if frame.get("battle_control_ready") is not True:
        raise ValueError("a ready normalized battle-control frame is required")
    if entry_kind not in ("daily_row", "suppression_sweep"):
        raise ValueError("entry_kind requires daily_row or suppression_sweep")
    conditions = {
        "primary_hostile": _optional_bool(primary_hostile, "primary_hostile"),
        "finalized": _optional_bool(finalized, "finalized"),
        "processing": _optional_bool(processing, "processing"),
        "result_present": _optional_bool(result_present, "result_present"),
    }
    leaf = normalize_current_finalizer_manager_inputs_v1(
        frame.get(CURRENT_FINALIZER_MANAGER_INPUTS_V1_KEY),
        expected_combat_id=frame.get("combat_id"),
    )
    context = {
        "source_kind": "same_frame_readonly_manager_inputs",
        "source_field": CURRENT_FINALIZER_MANAGER_INPUTS_V1_KEY,
        "observed_frame": {
            key: frame[key]
            for key in ("snapshot_revision", "observed_date_raw", "combat_id", "province_id")
        },
        "manager_leaf_state": (
            "absent" if CURRENT_FINALIZER_MANAGER_INPUTS_V1_KEY not in frame
            else "null" if leaf is None else "available"
        ),
        "pending_suppression_sweep_raw": (
            None if leaf is None else leaf["pending_suppression_sweep_raw"]
        ),
        "observed_operands": (
            [] if leaf is None
            else ["combat_manager_row_admitted", "pending_suppression_sweep"]
        ),
        "caller_conditional_context": {"entry_kind": entry_kind, **conditions},
        "future_manager_state_observed": False,
        "native_primary_hostility_observed": False,
        "actual_native_finalizer_executed": False,
    }
    return CurrentNormalFinalizerManagerInputs(
        entry_kind=entry_kind,
        combat_manager_row_admitted=(
            None if leaf is None else leaf["combat_manager_row_admitted"]
        ),
        pending_suppression_sweep=(
            None if leaf is None else leaf["pending_suppression_sweep"]
        ),
        primary_hostile=conditions["primary_hostile"],
        finalized=conditions["finalized"],
        processing=conditions["processing"],
        result_present=conditions["result_present"],
        source_context=context,
    )
