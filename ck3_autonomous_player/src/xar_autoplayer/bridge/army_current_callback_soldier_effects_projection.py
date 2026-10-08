"""Actual4 current-callback budget to associated current/max soldier effects.

Only the copied supply budget changes. Original siege/raid budgets precede
the writers; every intermediate count and DATA frame remains conditional.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_loss_sequence_replay import project_conditional_army_loss_sequence


def project_current_callback_soldier_effects_v1(
    army: Mapping[str, object], callback_risk: Mapping[str, object],
) -> dict[str, object]:
    """Join an independently ready one-entry budget to the existing loss core.

    The caller supplies the already computed same-query callback projection.
    Its overall stock readiness is not required for a known zero supply budget.
    This does not replay earlier manager stages or future callback occurrences.
    """
    result: dict[str, object] = {
        "schema_version": 1,
        "source": "same_input_conditional_current_callback_soldier_effects",
        "source_contract_game_version": "1.20.0.4",
        "source_contract_scope": "associated_DATA_current_stores_and_raised_current_maximum",
        "source_entries": {
            "caller": "24E3410", "writer": "2634190", "record_selector": "260DB50",
            "current_setter": "2657E80", "raised_refresh": "2633320",
            "residual_allocator": "2A957E0",
        },
        "arithmetic_implementation_lineage": "existing_1.20.0.3_four_pass_core",
        "input_basis": "one_captured_current_context_before_one_supply_callback_entry",
        "predicate_basis": "fixed_captured_supply_eligibility_writer_admission_and_refresh_context",
        "intermediate_state_basis": "derived_DATA_aliases_and_target_cached_current_maximum",
        "status": "unavailable", "ready": False,
        "conditional_soldier_effects_ready": False,
        "conditional_supply_budget_ready": callback_risk.get("conditional_supply_budget_ready") is True,
        "conditional_supply_budget_soldiers": callback_risk.get("conditional_supply_budget_soldiers"),
        "conditional_post_stock_ready": callback_risk.get("conditional_post_stock_ready") is True,
        "conditional_post_stock_raw": callback_risk.get("conditional_post_stock_raw"),
        "observed_current_supply_budget_soldiers": None,
        "observed_siege_budget_soldiers": None, "observed_raid_budget_soldiers": None,
        "observed_current_soldiers": army.get("current_soldiers"),
        "conditional_loss_sequence_v1": None, "missing_inputs": [],
        "actual_callback_observed": False, "actual_loss": False,
        "actual_post_stage_current": None, "earlier_stage_outputs_reconstructed": False,
        "future_callback_selection_ready": False,
        "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
    }
    operands = army.get("loss_application_inputs_v1")
    if isinstance(operands, Mapping):
        result.update(
            observed_current_supply_budget_soldiers=operands.get("current_supply_loss_budget"),
            observed_siege_budget_soldiers=operands.get("siege_loss_budget"),
            observed_raid_budget_soldiers=operands.get("raid_loss_budget"),
        )
    budget = result["conditional_supply_budget_soldiers"]
    if (not result["conditional_supply_budget_ready"] or type(budget) is not int
            or not -(1 << 31) <= budget < 1 << 31):
        result["missing_inputs"] = ["conditional_current_callback_supply_budget"]
        return result
    if not isinstance(operands, Mapping):
        result.update(status="partial", missing_inputs=["loss_application_inputs_v1"])
        return result

    copied = deepcopy(dict(army))
    copied["loss_application_inputs_v1"] = dict(copied["loss_application_inputs_v1"])
    copied["loss_application_inputs_v1"]["current_supply_loss_budget"] = budget
    sequence = project_conditional_army_loss_sequence(copied)
    # The reused kernels retain their own historical source labels. This
    # wrapper's new proof applies only to the explicitly listed actual4 domain.
    ready = sequence["conditional_sequence_ready"] is True
    result.update(
        status="available" if ready else "partial", ready=ready,
        conditional_soldier_effects_ready=ready,
        conditional_loss_sequence_v1=sequence,
        missing_inputs=deepcopy(sequence["missing_inputs"]),
    )
    return result
