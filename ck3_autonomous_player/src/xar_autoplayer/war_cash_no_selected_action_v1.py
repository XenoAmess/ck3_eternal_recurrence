"""Exact zero immediate war fee when this paused turn selects no war action.

This proves only the fee of the action selected for this turn. It says nothing
about earlier unresolved commitments or costs after a future turn advances.
"""

from __future__ import annotations

from collections.abc import Mapping

from .m5_observed_opportunity_selector import observed_frame


SCHEMA = "xar.ck3.war-cash-no-selected-action.v1"


def observe_no_selected_war_action_fee_v1(
    *, snapshot: Mapping[str, object], planned: Mapping[str, object],
    war_id: int,
) -> dict[str, object]:
    """Return a same-frame sourced zero only for an explicitly empty step."""
    frame = observed_frame(snapshot)
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("no-action fee needs a paused native map frame")
    wars = snapshot.get("active_wars")
    if (type(war_id) is not int or war_id <= 0
            or not isinstance(wars, list) or len(wars) != 1
            or not isinstance(wars[0], Mapping)
            or wars[0].get("war_id") != war_id):
        raise ValueError("no-action fee needs one matching active WarID")
    if (not isinstance(planned, Mapping)
            or planned.get("snapshot_id") != frame["snapshot_id"]
            or planned.get("revision") != frame["revision"]):
        raise ValueError("no-action fee plan crossed the paused snapshot")
    plan = planned.get("plan")
    if (not isinstance(plan, Mapping)
            or plan.get("policy") != "one-life-turn-v1"
            or "selected_step" not in plan
            or plan["selected_step"] is not None):
        raise ValueError("a selected war step has no zero-fee proof")
    construction = plan.get("construction_wartime_observation")
    source = (construction.get("source_frame")
              if isinstance(construction, Mapping) else None)
    expected_source = {
        "snapshot_id": frame["snapshot_id"],
        "revision": frame["revision"],
        "native_revision": frame["native_revision"],
        "date_raw": frame["date_raw"],
        "episode_run_id": frame["episode_run_id"],
        "actor_character_id": frame["played_character_id"],
    }
    if source != expected_source:
        raise ValueError("no-action fee lacks a full same-frame native source")
    amount = {
        "raw": 0, "scale": 100_000,
        "source": "formal_selected_step_absent_same_frame_v1",
        "source_frame": frame, "war_id": war_id,
    }
    return {
        "schema": SCHEMA, "status": "no_selected_action_fee_proven",
        "read_only": True, "source_frame": frame, "war_id": war_id,
        "selected_step": None, "immediate_war_action_cost_raw": amount,
        "pending_war_cash_raw": None,
        "future_war_cost_upper_raw": None,
        "future_risk_budget_raw": None,
        "policy_minimum_gold_reserve_raw": None,
        "formal_cash_receipt_eligible": False,
    }
