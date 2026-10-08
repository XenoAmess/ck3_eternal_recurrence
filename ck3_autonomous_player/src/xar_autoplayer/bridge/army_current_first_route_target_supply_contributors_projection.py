"""Current first-route target roster view; no arrival or incoming-usage model."""
from __future__ import annotations

from copy import deepcopy

from .army_current_first_route_target_supply_contributors_contract import (
    FAMILY_KEY,
    INPUT_BASIS,
    normalize_current_first_route_target_supply_contributors_v1,
)


def project_current_first_route_target_supply_contributors_v1(row, armycontext=None):
    """Expose the native current target witness with an optional same-frame join.

    The native wrapper already captures the subject and committed route target.
    An absent published Army context does not downgrade that observation.  When
    context exists, its observed route must agree; it never represents arrival.
    """
    if not isinstance(row, dict):
        raise ValueError("current first-route target projection requires an ArmyStrength row")
    value = row.get(FAMILY_KEY)
    family = None if value is None else normalize_current_first_route_target_supply_contributors_v1(
        value, expected_army_id=row.get("army_id"), expected_carmy_id=row.get("native_carmy_id"),
        army_context=armycontext,
    )
    nested = family["target_contributors_v1"] if family is not None else None
    ready = family is not None and family["current_target_inputs_ready"] is True
    witness_ready = nested is not None and nested["contributors_ready"] is True
    context_ready = (family is not None and isinstance(armycontext, dict)
                     and armycontext.get("current_province_id") == family["current_province_id"]
                     and isinstance(armycontext.get("route_province_ids"), list)
                     and (bool(armycontext["route_province_ids"])
                          if family["first_route_target_province_id"] is not None
                          else family["status"] == "no_committed_target"))
    count = family["subject_included_occurrence_count"] if family is not None else None
    witness = ("observed_present" if count is not None and count > 0 else "observed_absent") if witness_ready else "unavailable"
    return {
        "schema_version": 1,
        "source": "current_first_route_target_supply_contributors_observation",
        "input_basis": INPUT_BASIS,
        "status": family["status"] if family is not None else "unavailable",
        "ready": ready,
        "current_target_inputs_ready": ready,
        "same_frame_army_context_ready": context_ready,
        "only_current_target_inputs": True,
        "missing_inputs": ([] if ready or family is not None and family["status"] == "no_committed_target"
                           else [family["unavailable_reason"] if family is not None else FAMILY_KEY]),
        "observed_inputs": deepcopy(family),
        "target_current_usage_ready": nested is not None and nested["current_usage_ready"] is True,
        "target_native_supply_limit_soldiers": nested["native_supply_limit_soldiers"] if nested is not None else None,
        "target_native_supply_usage_soldiers": nested["native_supply_usage_soldiers"] if nested is not None else None,
        "subject_presence_witness_ready": witness_ready,
        "subject_presence_witness": witness,
        "actual_arrival_observed": False,
        "actual_after_arrival_usage_observed": False,
        "full_arrival_supply_transition_ready": False,
    }
