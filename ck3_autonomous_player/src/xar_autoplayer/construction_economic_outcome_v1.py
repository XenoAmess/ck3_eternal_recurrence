"""Consume existing construction material and aggregate income observations.

The native construction receipt proves the slot. Income observations prove
aggregate changes across time, without assigning them to one building.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .bridge.construction_monthly_budget_v1 import project_construction_monthly_budget_v1
from .bridge.version_identity import require_exact_native_build
from .bridge.war_cash_private_transport_v1 import _monthly_flow


def construction_economic_outcome_v1(
    receipt: Mapping[str, object], *, exact_ck3_build: str,
    pre_cash_v2: Mapping[str, object] | None = None,
    post_cash_v2: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Classify a durable receipt; do not read the game or schedule an action."""
    candidate = receipt.get("candidate")
    candidate = candidate if isinstance(candidate, Mapping) else {}
    verified = receipt.get("postcondition_verified") is True
    completed = (receipt.get("status") == "applied" and verified
                 and receipt.get("completion_status") == "completed")
    completion_date = receipt.get("completion_observed_date_raw")
    if receipt.get("status") == "restored_before_action":
        phase = "restored_before_action"
    elif completed:
        phase = "completed"
    elif (receipt.get("status") == "applied" and verified
          and receipt.get("completion_status") == "in_progress"):
        phase = "active"
    else:
        phase = "pending"

    pre = receipt.get("pre_player_monthly_gold_income_raw")
    post = receipt.get("observed_player_monthly_gold_income_raw")
    post_date = receipt.get("income_observed_date_raw")
    gross_semantics_ready = exact_ck3_build in {"1.20.0.3", "1.20.0.4"}
    gross_ready = (completed and gross_semantics_ready
                   and type(pre) is int and type(post) is int
                   and type(completion_date) is int and type(post_date) is int
                   and post_date >= completion_date)
    gross_reason = (
        None if gross_ready else
        "construction_not_completed" if not completed else
        "player_income_semantics_not_qualified" if not gross_semantics_ready else
        "pre_submit_player_income_unavailable" if type(pre) is not int else
        "post_completion_player_income_unavailable"
    )

    def province(value: object, *, post_completion: bool) -> int | None:
        if (not isinstance(value, Mapping) or value.get("status") != "observed"
                or value.get("barony_title_id") != candidate.get("barony_title_id")
                or value.get("province_id") != candidate.get("province_id")
                or type(value.get("native_province_monthly_income_raw")) is not int):
            return None
        if post_completion and (
                type(completion_date) is not int
                or type(value.get("date_raw")) is not int
                or value["date_raw"] < completion_date):
            return None
        return value["native_province_monthly_income_raw"]

    province_pre = province(receipt.get("pre_province_income_observation"),
                            post_completion=False)
    province_post = province(receipt.get("construction_province_income_observation"),
                             post_completion=True)
    province_ready = completed and province_pre is not None and province_post is not None
    province_reason = (
        None if province_ready else
        "construction_not_completed" if not completed else
        "pre_submit_province_income_unavailable" if province_pre is None else
        "post_completion_province_income_unavailable"
    )
    if phase == "pending":
        next_observation = "independent_construction_material_receipt"
    elif phase == "active":
        next_observation = "scheduled_completion_watch"
    elif completed and type(pre) is int and not gross_ready:
        next_observation = ("existing_player_root_then_material_receipt"
                            if gross_semantics_ready else "income_source_qualification")
    elif completed and province_pre is not None and not province_ready:
        next_observation = "scheduled_province_income_receipt_retry"
    else:
        next_observation = None

    pre_cash = pre_cash_v2 if pre_cash_v2 is not None else receipt.get("pre_cash_v2")
    post_cash = post_cash_v2 if post_cash_v2 is not None else receipt.get("post_cash_v2")
    cash_change: dict[str, object] = {
        "status": "unavailable", "unavailable_reason": "construction_not_completed",
        "source_frames": None, "elapsed_game_hours": None,
        "monthly_rate_changes": {}, "personal_gold_change": None,
        "verified_construction_gold_debit_raw": None,
        "personal_gold_residual_after_verified_debit_raw": None,
        "unallocated_other_transactions": True,
        "building_attribution_ready": False, "actual_roi_ready": False,
        "future_war_cost_upper_ready": False,
    }
    if completed:
        if not isinstance(pre_cash, Mapping):
            cash_change["unavailable_reason"] = "pre_submit_cash_v2_unavailable"
        elif not isinstance(post_cash, Mapping):
            cash_change["unavailable_reason"] = "post_completion_cash_v2_unavailable"
        else:
            for cash in (pre_cash, post_cash):
                if cash.get("monthly_income_semantics") is None:
                    raise ValueError("construction cash change requires v2 NET semantics")
                _monthly_flow(cash)
                build = require_exact_native_build(
                    cash.get("game_version"), cash.get("executable_sha256"))
                if build.game_version != exact_ck3_build:
                    raise ValueError("construction cash interval crossed its exact build")
            before_date, after_date = pre_cash.get("date_raw"), post_cash.get("date_raw")
            actor = receipt.get("actor_character_id")
            bound = (
                gross_semantics_ready and type(actor) is int
                and pre_cash.get("played_character_id") == actor
                and post_cash.get("played_character_id") == actor
                and pre_cash["readiness"].get("same_frame_ready") is True
                and post_cash["readiness"].get("same_frame_ready") is True
                and type(before_date) is int and type(after_date) is int
                and before_date == receipt.get("pre_date_raw")
                and type(completion_date) is int and after_date >= completion_date
                and after_date >= before_date
            )
            if not bound:
                cash_change["unavailable_reason"] = "cash_interval_actor_or_dates_not_bound"
            else:
                cash_change["source_frames"] = [
                    {key: cash.get(key) for key in (
                        "game_version", "executable_sha256", "played_character_id",
                        "snapshot_revision", "date_raw", "queried_snapshot_id",
                        "queried_revision", "queried_native_revision",
                    )} for cash in (pre_cash, post_cash)
                ]
                cash_change["elapsed_game_hours"] = after_date - before_date
                observed = 0
                for key, flag in (
                    ("player_monthly_gross_income", "monthly_gross_income_ready"),
                    ("player_monthly_total_expenses", "monthly_total_expenses_ready"),
                    ("player_monthly_net_income", "monthly_net_income_ready"),
                    ("current_treasury", "current_treasury_ready"),
                ):
                    before, after = pre_cash.get(key), post_cash.get(key)
                    ready = (
                        isinstance(before, Mapping) and isinstance(after, Mapping)
                        and type(before.get("raw")) is int and type(after.get("raw")) is int
                        and before.get("scale") == after.get("scale") == 100_000
                        and pre_cash["readiness"].get(flag) is True
                        and post_cash["readiness"].get(flag) is True
                    )
                    change = {
                        "ready": ready, "scale": 100_000,
                        "before_raw": before["raw"] if ready else None,
                        "after_raw": after["raw"] if ready else None,
                        "delta_raw": after["raw"] - before["raw"] if ready else None,
                    }
                    if key == "current_treasury":
                        cash_change["personal_gold_change"] = change
                    else:
                        cash_change["monthly_rate_changes"][key] = change
                    observed += int(ready)
                cash_change["status"] = "observed" if observed else "unavailable"
                cash_change["unavailable_reason"] = None if observed else "cash_interval_values_unavailable"
                start = receipt.get("start_receipt")
                cost, gold_before = candidate.get("stock_gold_cost_raw"), candidate.get("gold_before_raw")
                debit_verified = (
                    isinstance(start, Mapping) and start.get("status") == "applied"
                    and start.get("postcondition_verified") is True
                    and isinstance(receipt.get("action_request_id"), str)
                    and start.get("action_request_id") == receipt["action_request_id"]
                    and type(cost) is int and cost > 0 and type(gold_before) is int
                    and start.get("post_player_gold_raw") == gold_before - cost
                )
                if debit_verified:
                    cash_change["verified_construction_gold_debit_raw"] = cost
                    wallet = cash_change["personal_gold_change"]
                    if wallet["ready"]:
                        cash_change["personal_gold_residual_after_verified_debit_raw"] = wallet["delta_raw"] + cost

    return {
        "schema": "xar.ck3.construction-economic-outcome.v1",
        "phase": phase,
        "action_request_id": receipt.get("action_request_id"),
        "actor_character_id": receipt.get("actor_character_id"),
        "episode_run_id": receipt.get("episode_run_id"),
        "exact_ck3_build": exact_ck3_build,
        "material_completed": completed,
        "completion_observed_date_raw": completion_date if completed else None,
        "authored_direct_monthly_income_delta_hundredths": candidate.get(
            "authored_monthly_income_delta_hundredths"),
        "player_gross_monthly_income_change": {
            "ready": gross_ready, "unavailable_reason": gross_reason,
            "scale": 100_000, "time_basis": "month",
            "source_scope": "played_character_gross_income_aggregate",
            "before_raw": pre if type(pre) is int else None,
            "after_raw": post if type(post) is int else None,
            "delta_raw": post - pre if gross_ready else None,
            "observation_date_raw": post_date if type(post_date) is int else None,
        },
        "province_income_change": {
            "ready": province_ready, "unavailable_reason": province_reason,
            "scale": None, "source_scope": "province_income_aggregate",
            "before_raw": province_pre, "after_raw": province_post,
            "delta_raw": province_post - province_pre if province_ready else None,
        },
        "next_observation_kind": next_observation,
        "observed_cash_change": cash_change,
        "readiness": {
            "material_completed": completed,
            "player_gross_aggregate_change_ready": gross_ready,
            "province_aggregate_change_ready": province_ready,
            "player_net_monthly_change_ready": (
                cash_change["monthly_rate_changes"].get(
                    "player_monthly_net_income", {}).get("ready") is True),
            "building_attribution_ready": False,
            "net_benefit_ready": False,
            "m5_realized_value_ready": False,
        },
        "formal_action_ready": False,
    }


def prepare_construction_cash_fields_v1(
    candidate: Mapping[str, object], normalized_cash_v2: dict[str, object], *,
    reserve_gold_raw: int, existing_commitment_gold_raw: int, horizon_months: int,
) -> dict[str, object]:
    """Reuse one observed cash packet for the native quote's budget and baseline.

    The Root hook supplies the actual same paused actor/date/build/treasury
    quote. Persist these fields on pending and the first fresh material receipt.
    This utility neither reads nor selects an action.
    """
    budget = project_construction_monthly_budget_v1(
        normalized_cash_v2,
        construction_gold_cost_raw=candidate["stock_gold_cost_raw"],
        reserve_gold_raw=reserve_gold_raw,
        existing_commitment_gold_raw=existing_commitment_gold_raw,
        horizon_months=horizon_months,
    )
    return {
        "pre_cash_v2": deepcopy(budget["source_cash_resources"]),
        "construction_monthly_budget": budget,
    }


def completed_construction_cash_fields_v1(
    completed_receipt: Mapping[str, object], normalized_cash_v2: Mapping[str, object], *,
    exact_ck3_build: str,
) -> dict[str, object]:
    """Attach the observed post packet and consume the same material receipt.

    The existing classifier determines actual completion and interval readiness;
    attaching a packet does not qualify an active construction or start ACK.
    """
    receipt = {**completed_receipt, "post_cash_v2": deepcopy(normalized_cash_v2)}
    return {
        "receipt": receipt,
        "construction_economic_outcome": construction_economic_outcome_v1(
            receipt, exact_ck3_build=exact_ck3_build),
    }
