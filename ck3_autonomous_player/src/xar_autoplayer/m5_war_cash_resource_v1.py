"""Same-frame active-war cash slice for the existing M5 shared budget.

This read-only contract does not estimate upkeep from net income or interpret
missing pending actions as zero.  It only combines independently sourced
nonnegative raw Q100000 gold amounts for one explicitly bounded horizon.
"""

from __future__ import annotations

from collections.abc import Mapping

from .m5_observed_opportunity_selector import observed_frame

SCHEMA = "xar.ck3.m5-active-war-cash-resource.v1"
_AMOUNTS = (
    "pending_war_cash_raw",
    "immediate_war_action_cost_raw",
    "future_war_cost_upper_raw",
    "future_risk_budget_raw",
    "policy_minimum_gold_reserve_raw",
)


def observe_active_war_cash_resource_v1(
    *, snapshot: Mapping[str, object], war_id: int,
    inputs: Mapping[str, object],
) -> dict[str, object]:
    """Publish a typed incomplete or complete cash receipt for one WarID.

    Every amount is a ``{raw, scale, source, source_frame, war_id}`` object.
    A real zero needs an explicit source proving absence; a missing value remains null with a
    machine-readable reason.  The future upper bound includes only its stated
    horizon, while the separate risk budget covers uncertainty within it.
    """
    frame = observed_frame(snapshot)
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("war cash requires a paused map frame")
    wars = snapshot.get("active_wars")
    if (type(war_id) is not int or war_id <= 0 or not isinstance(wars, list)
            or sum(isinstance(row, Mapping) and row.get("war_id") == war_id
                   for row in wars) != 1):
        raise ValueError("war cash requires one same-frame active WarID")
    if not isinstance(inputs, Mapping) or inputs.get("source_frame") != frame:
        raise ValueError("war cash inputs crossed the full paused frame")
    if inputs.get("war_id") != war_id:
        raise ValueError("war cash inputs crossed WarID")
    treasury = snapshot.get("played_character_gold")
    if (not isinstance(treasury, Mapping)
            or type(treasury.get("raw")) is not int
            or treasury.get("scale") != 100_000):
        raise ValueError("war cash lacks same-frame treasury Q100000")

    amounts: dict[str, int | None] = {}
    provenance: dict[str, str | None] = {}
    observations: dict[str, dict[str, object] | None] = {}
    missing: dict[str, str] = {}
    for name in _AMOUNTS:
        raw = inputs.get(name)
        if raw is None:
            amounts[name] = None
            provenance[name] = None
            observations[name] = None
            missing[name] = f"{name}_source_not_observed_same_frame"
            continue
        if (not isinstance(raw, Mapping)
                or type(raw.get("raw")) is not int or raw["raw"] < 0
                or raw.get("scale") != 100_000
                or type(raw.get("source")) is not str or not raw["source"]
                or raw.get("source_frame") != frame
                or raw.get("war_id") != war_id):
            raise ValueError(f"{name} needs same-frame sourced nonnegative Q100000 raw")
        amounts[name] = raw["raw"]
        provenance[name] = raw["source"]
        observations[name] = {
            "raw": raw["raw"], "scale": 100_000, "source": raw["source"],
            "source_frame": dict(frame), "war_id": war_id,
        }

    horizon = inputs.get("horizon_days")
    assumptions = inputs.get("future_bound_assumptions")
    if type(horizon) is not int or horizon <= 0:
        missing["horizon_days"] = "bounded_future_war_horizon_not_observed"
        horizon = None
    if (not isinstance(assumptions, list) or not assumptions
            or any(type(item) is not str or not item for item in assumptions)):
        missing["future_bound_assumptions"] = "future_war_cost_bound_assumptions_not_observed"
        assumptions = None
    complete = not missing
    pending = amounts["pending_war_cash_raw"]
    immediate = amounts["immediate_war_action_cost_raw"]
    future = amounts["future_war_cost_upper_raw"]
    risk = amounts["future_risk_budget_raw"]
    policy = amounts["policy_minimum_gold_reserve_raw"]
    future_ready = (
        future is not None and risk is not None
        and horizon is not None and assumptions is not None
    )
    return {
        "schema": SCHEMA, "status": "complete" if complete else "incomplete",
        "read_only": True, "source_frame": frame, "war_id": war_id,
        "gold_scale": 100_000,
        "observed_treasury_raw": treasury["raw"],
        "existing_shared_gold_commitment_raw": pending,
        "immediate_war_action_cost_raw": immediate,
        "war_future_gold_cost_raw": (
            future + risk if future_ready else None
        ),
        "minimum_gold_reserve_raw": policy,
        "joint_gold_reserve_raw": (
            future + risk + policy
            if future_ready and policy is not None
            else None
        ),
        "horizon_days": horizon,
        "future_bound_assumptions": assumptions,
        "amount_values_raw": amounts,
        "amount_sources": provenance,
        "amount_observations": observations,
        "missing": missing,
        "formal_action_ready": False,
    }


def require_complete_war_cash_resource_v1(
    receipt: object, *, frame: Mapping[str, object], war_id: int,
) -> dict[str, object]:
    """Reject missing or stale war cash before a joint spend is reserved."""
    if (not isinstance(receipt, Mapping) or receipt.get("schema") != SCHEMA
            or receipt.get("status") != "complete"
            or receipt.get("read_only") is not True
            or receipt.get("source_frame") != dict(frame)
            or receipt.get("war_id") != war_id
            or receipt.get("gold_scale") != 100_000
            or receipt.get("missing") != {}):
        raise ValueError("complete same-frame active-war cash resource required")
    for name in (
        "existing_shared_gold_commitment_raw",
        "immediate_war_action_cost_raw", "war_future_gold_cost_raw",
        "minimum_gold_reserve_raw", "joint_gold_reserve_raw",
    ):
        if type(receipt.get(name)) is not int or receipt[name] < 0:
            raise ValueError(f"war cash {name} is not a measured amount")
    if receipt["joint_gold_reserve_raw"] != (
        receipt["war_future_gold_cost_raw"]
        + receipt["minimum_gold_reserve_raw"]
    ):
        raise ValueError("war cash joint reserve does not balance")
    sources = receipt.get("amount_sources")
    values = receipt.get("amount_values_raw")
    observations = receipt.get("amount_observations")
    if (not isinstance(sources, Mapping)
            or not isinstance(values, Mapping)
            or not isinstance(observations, Mapping)
            or any(type(sources.get(name)) is not str or not sources[name]
                   for name in _AMOUNTS)
            or any(type(values.get(name)) is not int or values[name] < 0
                   for name in _AMOUNTS)
            or type(receipt.get("horizon_days")) is not int
            or receipt["horizon_days"] <= 0
            or not isinstance(receipt.get("future_bound_assumptions"), list)
            or not receipt["future_bound_assumptions"]):
        raise ValueError("war cash lacks bound provenance or horizon")
    for name in _AMOUNTS:
        observation = observations.get(name)
        if (not isinstance(observation, Mapping)
                or type(observation.get("raw")) is not int
                or observation["raw"] != values[name]
                or observation.get("scale") != 100_000
                or observation.get("source") != sources[name]
                or observation.get("source_frame") != dict(frame)
                or type(observation.get("war_id")) is not int
                or observation["war_id"] != war_id):
            raise ValueError(f"war cash {name} lost same-frame provenance")
    if (
        receipt["existing_shared_gold_commitment_raw"]
        != values["pending_war_cash_raw"]
        or receipt["immediate_war_action_cost_raw"]
        != values["immediate_war_action_cost_raw"]
        or receipt["war_future_gold_cost_raw"]
        != values["future_war_cost_upper_raw"] + values["future_risk_budget_raw"]
        or receipt["minimum_gold_reserve_raw"]
        != values["policy_minimum_gold_reserve_raw"]
    ):
        raise ValueError("war cash receipt differs from sourced amounts")
    return dict(receipt)
