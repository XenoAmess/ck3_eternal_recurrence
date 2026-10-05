"""Pure 1.20.0.3 integer loss requests from actual allocation-stage inputs.

24E3430 applies supply first, then the original siege + raid budgets. Each
residual pass recounts current soldiers after the preferred writer calls.
These helpers never synthesize that current by subtracting requested losses.
The initial associated-DATA replay and an independent derived four-pass
replay stay separate from the actual-stage observation requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Sequence

from .army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes
from .army_loss_sequence_replay import project_conditional_army_loss_sequence
from .army_monthly_loss_budget_projection import construct_conditional_monthly_loss_budgets
from .army_monthly_caller_effect_projection import project_conditional_monthly_caller_effects
from .army_daily_queue_transfer_projection import project_conditional_daily_id_transfer


FRACTION_SCALE = 100_000
LossPhase = Literal[
    "supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"
]
_PHASES = {"supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"}


@dataclass(frozen=True)
class EligibleArmyRegiment:
    """One identity-valid selected ArRg, in the actual stored allocation order."""

    army_regiment_id: int
    current_soldiers: int


@dataclass(frozen=True)
class LossAllocationInputs:
    """Rows and total read immediately before this pass, after earlier writes.

    supply preferred: tier <= 0 AND native 2A956D0;
    supply residual: native 2A956D0;
    siege/raid preferred: tier <= 0;
    siege/raid residual: every identity-valid row.
    """

    native_eligible_total_soldiers: int
    ordered_eligible_rows: Sequence[EligibleArmyRegiment]


def _int32(value: object, name: str) -> int:
    if type(value) is not int or not -(2**31) <= value < 2**31:
        raise ValueError(f"{name} must be signed int32")
    return value


def _signed_i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _truncate_toward_zero(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def project_native_loss_requests(
    *,
    request_budget_soldiers: int,
    native_eligible_total_soldiers: int,
    ordered_eligible_rows: Sequence[EligibleArmyRegiment],
    phase: LossPhase,
) -> dict[str, object]:
    """Reproduce preferred/2A95800 request arithmetic, without a soldier debit.

    Native signed32 IMUL keeps only the low32 bits before signed IDIV. The
    remaining budget decreases by the request, regardless of writer skip or
    clamp. A selected zero-current row still emits a zero writer request.
    """
    if phase not in _PHASES:
        raise ValueError("unsupported loss allocation phase")
    budget = _int32(request_budget_soldiers, "request_budget_soldiers")
    total = _int32(native_eligible_total_soldiers, "native_eligible_total_soldiers")
    remaining_budget = min(budget, total)
    capped_budget = remaining_budget
    overflow_residual = _signed_i32(budget - capped_budget)
    requests = []

    for row in ordered_eligible_rows:
        if remaining_budget <= 0 or total <= 0:
            break
        regiment_id = _int32(row.army_regiment_id, "army_regiment_id")
        current = _int32(row.current_soldiers, "current_soldiers")
        product = _signed_i32(current * remaining_budget)
        requested_soldiers = _truncate_toward_zero(product, total)
        requests.append({
            "army_regiment_id": regiment_id,
            "current_soldiers_read": current,
            "remaining_budget_before": remaining_budget,
            "remaining_eligible_before": total,
            "multiply_signed32": product,
            "requested_soldiers": requested_soldiers,
            "writer_quantity_raw": requested_soldiers * FRACTION_SCALE,
            "writer_quantity_scale": FRACTION_SCALE,
        })
        remaining_budget = _signed_i32(remaining_budget - requested_soldiers)
        total = _signed_i32(total - current)

    return {
        "projection_kind": "native_integer_writer_requests",
        "phase": phase,
        "request_budget_soldiers": budget,
        "native_eligible_total_soldiers": native_eligible_total_soldiers,
        "capped_request_budget_soldiers": capped_budget,
        "caller_overflow_residual_soldiers": overflow_residual,
        "remaining_request_budget_soldiers": remaining_budget,
        "remaining_eligible_soldiers": total,
        "requests": requests,
    }


def project_native_loss_sequence(
    *,
    supply_budget_soldiers: int,
    siege_budget_soldiers: int,
    raid_budget_soldiers: int,
    supply_preferred: LossAllocationInputs | None = None,
    supply_residual: LossAllocationInputs | None = None,
    post_supply_siege_raid_preferred: LossAllocationInputs | None = None,
    post_preferred_siege_raid_residual: LossAllocationInputs | None = None,
) -> dict[str, object]:
    """Project the four ordered passes from explicitly supplied stage inputs.

    Each residual receives only its preferred pass's initial over-capacity
    amount. Its rows must be observed after the preferred writer calls.
    Siege/raid uses original budgets and actual post-supply current. Missing
    stages stop the sequence; requested amounts cannot substitute for writes.
    Budgets supplied here describe a conditional execution, not a future month.
    """
    supply_budget = _int32(supply_budget_soldiers, "supply_budget_soldiers")
    siege_budget = _int32(siege_budget_soldiers, "siege_budget_soldiers")
    raid_budget = _int32(raid_budget_soldiers, "raid_budget_soldiers")
    combined_budget = _signed_i32(siege_budget + raid_budget)
    passes: list[dict[str, object]] = []
    missing: list[str] = []

    def preferred_and_residual(
        budget: int, preferred_inputs: LossAllocationInputs | None,
        residual_inputs: LossAllocationInputs | None, prefix: str,
    ) -> bool:
        residual_budget = 0
        for suffix, inputs in (("preferred", preferred_inputs), ("residual", residual_inputs)):
            phase = f"{prefix}_{suffix}"
            pass_budget = budget if suffix == "preferred" else residual_budget
            if pass_budget > 0 and inputs is None:
                missing.append(f"{phase}_stage_inputs")
                return False
            # An empty budget does not need eligibility or a later-stage snapshot.
            selected = inputs if pass_budget > 0 else LossAllocationInputs(0, ())
            projection = project_native_loss_requests(
                request_budget_soldiers=pass_budget,
                native_eligible_total_soldiers=selected.native_eligible_total_soldiers,
                ordered_eligible_rows=selected.ordered_eligible_rows,
                phase=phase,
            )
            passes.append(projection)
            if suffix == "preferred":
                residual_budget = int(projection["caller_overflow_residual_soldiers"])
        return True

    supply_complete = preferred_and_residual(
        supply_budget, supply_preferred, supply_residual, "supply"
    )
    if supply_complete:
        preferred_and_residual(
            combined_budget, post_supply_siege_raid_preferred,
            post_preferred_siege_raid_residual, "siege_raid",
        )
    else:
        missing.append("post_supply_current_soldiers")
    return {
        "projection_kind": "native_integer_writer_requests",
        "source_contract_game_version": "1.20.0.3",
        "status": "available" if not missing else ("partial" if passes else "unavailable"),
        "writer_requests_ready": not missing,
        "applied_loss_ready": False,
        "applied_soldier_loss": None,
        "supply_budget_soldiers": supply_budget,
        "siege_budget_soldiers": siege_budget,
        "raid_budget_soldiers": raid_budget,
        "combined_siege_raid_budget_soldiers": combined_budget,
        "passes": passes,
        "missing_inputs": missing,
        "application_boundary": "Actual post-write stage current and complete monthly applied loss are not observed",
    }


def project_observed_army_loss_requests(
    army_strengths: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Consume normalized army rows without another query or native execution.

    The current readonly supply budget is not an updater result. Observed
    per-row 2A956D0 can select the supply preferred pass. Positive supply still
    needs real later-stage current; requests do not stand in for writes. With
    budget0, current rows can supply the conditional siege/raid preferred pass.
    Nonzero overflow needs actual post-preferred residual rows.
    """
    result = []
    for army in army_strengths:
        conditional_budgets = construct_conditional_monthly_loss_budgets(army)
        conditional_caller_effects = project_conditional_monthly_caller_effects(army, conditional_budgets)
        conditional_daily_transfer = project_conditional_daily_id_transfer(army)
        inputs = army.get("loss_application_inputs_v1")
        if army.get("status") != "available" or not isinstance(inputs, dict) or inputs.get("status") != "available":
            result.append({
                "army_id": army.get("army_id"), "status": "unavailable",
                "writer_requests_ready": False, "applied_loss_ready": False,
                "applied_soldier_loss": None, "passes": [],
                "missing_inputs": ["available_loss_application_inputs_v1"],
                "same_input_conditional_monthly_loss_budgets_v1":
                    conditional_budgets,
                "same_input_conditional_monthly_caller_effects_v1": conditional_caller_effects,
                "same_input_conditional_daily_id_transfer_v1": conditional_daily_transfer,
            })
            continue
        preferred = None
        supply_preferred = None
        rows = army.get("regiment_strengths")
        supply_budget = inputs["current_supply_loss_budget"]
        tiers_available = isinstance(rows, list) and all(
            row.get("siege_tier_observable") is True for row in rows
        )
        supply_eligibility_available = isinstance(rows, list) and all(
            type(row.get("native_supply_loss_eligible")) is bool for row in rows
        )
        if supply_budget > 0 and tiers_available and supply_eligibility_available:
            supply_preferred = LossAllocationInputs(
                native_eligible_total_soldiers=inputs["definition_le_zero_supply_eligible_soldiers"],
                ordered_eligible_rows=tuple(
                    EligibleArmyRegiment(row["army_regiment_id"], row["current_soldiers"])
                    for row in rows
                    if row["siege_tier"] <= 0 and row["native_supply_loss_eligible"]
                ),
            )
        if supply_budget == 0 and tiers_available:
            preferred = LossAllocationInputs(
                native_eligible_total_soldiers=inputs["definition_le_zero_soldiers"],
                ordered_eligible_rows=tuple(
                    EligibleArmyRegiment(row["army_regiment_id"], row["current_soldiers"])
                    for row in rows if row["siege_tier"] <= 0
                ),
            )
        projection = project_native_loss_sequence(
            supply_budget_soldiers=supply_budget,
            siege_budget_soldiers=inputs["siege_loss_budget"],
            raid_budget_soldiers=inputs["raid_loss_budget"],
            supply_preferred=supply_preferred,
            post_supply_siege_raid_preferred=preferred,
        )
        if supply_budget > 0 and not supply_eligibility_available:
            projection["missing_inputs"].append("per_regiment_native_2a956d0")
        if supply_budget > 0 and projection["combined_siege_raid_budget_soldiers"] > 0:
            if "post_supply_current_soldiers" not in projection["missing_inputs"]:
                projection["missing_inputs"].append("post_supply_current_soldiers")
        projection["same_input_conditional_chunk_writeback_v1"] = (
            _project_initial_preferred_chunk_changes(army, projection)
        )
        projection["same_input_conditional_loss_sequence_v1"] = (
            project_conditional_army_loss_sequence(army)
        )
        projection["same_input_conditional_monthly_loss_budgets_v1"] = (
            conditional_budgets
        )
        projection["same_input_conditional_monthly_caller_effects_v1"] = conditional_caller_effects
        projection["same_input_conditional_daily_id_transfer_v1"] = conditional_daily_transfer
        result.append({
            "army_id": army["army_id"], **projection,
            "input_basis": "current_readonly_inputs; conditional requests, not updater execution",
        })
    return result


def _project_initial_preferred_chunk_changes(
    army: Mapping[str, object], allocation: Mapping[str, object],
) -> dict[str, object]:
    """Only the first actual-input preferred pass may use current query DATA.

    The positive-supply preferred pass has the initial frame. Siege/raid
    preferred has it only when supply budget is zero. Residual and later
    positive-supply stages need their own observations; none are synthesized.
    """
    positive_supply = allocation["supply_budget_soldiers"] > 0
    phase = "supply_preferred" if positive_supply else "siege_raid_preferred"
    budget = (allocation["supply_budget_soldiers"] if positive_supply
              else allocation["combined_siege_raid_budget_soldiers"])
    result = {
        "projection_kind": "conditional_initial_preferred_chunk_writeback",
        "input_basis": "initial_same_query_DATA_and_preferred_writer_requests",
        "phase": phase, "status": "unavailable",
        "same_input_chunk_writeback_ready": False,
        "actual_loss": False, "actual_post_stage_current": None,
        "requests": [], "missing_inputs": [],
    }
    if budget <= 0:
        return {**result, "status": "not_applicable"}
    preferred = next((row for row in allocation["passes"] if row["phase"] == phase), None)
    if preferred is None:
        return {**result, "missing_inputs": ["initial_preferred_writer_requests"]}
    conditional = [project_observed_writer_chunk_changes(army, request)
                   for request in preferred["requests"]]
    complete = all(row["chunk_writeback_ready"] for row in conditional)
    return {
        **result,
        "status": "available" if complete else (
            "partial" if any(row["chunk_writeback_ready"] for row in conditional) else "unavailable"
        ),
        "same_input_chunk_writeback_ready": complete,
        "requests": conditional,
        "missing_inputs": [
            {"army_regiment_id": row["army_regiment_id"], "inputs": row["missing_inputs"]}
            for row in conditional if not row["chunk_writeback_ready"]
        ],
    }
