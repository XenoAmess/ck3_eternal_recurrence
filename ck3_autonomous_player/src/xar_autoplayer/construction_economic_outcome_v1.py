"""Consume existing construction material and aggregate income observations.

The native construction receipt proves the slot. Income observations prove
aggregate changes across time, without assigning them to one building.
"""

from __future__ import annotations

from collections.abc import Mapping


def construction_economic_outcome_v1(
    receipt: Mapping[str, object], *, exact_ck3_build: str,
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
        "readiness": {
            "material_completed": completed,
            "player_gross_aggregate_change_ready": gross_ready,
            "province_aggregate_change_ready": province_ready,
            "building_attribution_ready": False,
            "net_benefit_ready": False,
            "m5_realized_value_ready": False,
        },
        "formal_action_ready": False,
    }
