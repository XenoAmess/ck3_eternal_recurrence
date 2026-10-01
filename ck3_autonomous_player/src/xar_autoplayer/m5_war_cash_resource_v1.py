"""Same-frame active-war cash slice for the existing M5 shared budget.

This read-only contract does not estimate upkeep from net income or interpret
missing pending actions as zero.  It only combines independently sourced
nonnegative raw Q100000 gold amounts for one explicitly bounded horizon.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from .m5_observed_opportunity_selector import observed_frame

SCHEMA = "xar.ck3.m5-active-war-cash-resource.v1"
AGGREGATE_SCHEMA = "xar.ck3.m5-aggregate-active-war-cash-resource.v1"
_CLAIMS = ("army_ids", "ally_character_ids", "character_ids", "commitment_keys")
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
        if "resource_components" in raw:
            observations[name]["resource_components"] = _resource_components(
                raw["resource_components"], amount=raw["raw"], frame=frame,
                war_id=war_id, active_war_ids=_active_war_ids(snapshot),
            )

    claims = inputs.get("resource_claims")
    if claims is not None:
        claims = _resource_claims(claims, frame=frame, war_id=war_id)

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
        "resource_claims": claims,
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
        if "resource_components" in observation:
            # The aggregate consumer also checks the full active-war coverage.
            components = observation["resource_components"]
            component_wars = {war_id}
            if isinstance(components, list):
                for component in components:
                    if isinstance(component, Mapping) and isinstance(
                        component.get("war_ids"), list,
                    ):
                        component_wars.update(component["war_ids"])
            _resource_components(
                components, amount=values[name], frame=frame, war_id=war_id,
                active_war_ids=sorted(component_wars),
            )
    if receipt.get("resource_claims") is not None:
        _resource_claims(receipt["resource_claims"], frame=frame, war_id=war_id)
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


def observe_aggregate_active_war_cash_resource_v1(
    *, snapshot: Mapping[str, object], receipts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Combine existing receipts by explicit cost resource, never by WarID.

    Rates are not forecasts. Missing receipts, attribution, occupation or
    future bounds remain incomplete; this function only consumes observations.
    Immediate fees remain alternatives indexed by WarID rather than a sum.
    """
    frame = observed_frame(snapshot)
    war_ids = _active_war_ids(snapshot)
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("aggregate war cash requires a paused map frame")
    treasury = snapshot.get("played_character_gold")
    if (not isinstance(treasury, Mapping) or type(treasury.get("raw")) is not int
            or treasury.get("scale") != 100_000):
        raise ValueError("aggregate war cash lacks same-frame treasury Q100000")
    if (not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes))
            or any(not isinstance(receipt, Mapping) for receipt in receipts)):
        raise ValueError("aggregate war cash receipts must be a sequence")

    by_war: dict[int, dict[str, object]] = {}
    for receipt in receipts:
        war_id = receipt.get("war_id")
        if type(war_id) is not int or war_id not in war_ids or war_id in by_war:
            raise ValueError("aggregate war cash has duplicate or inactive WarID")
        if (receipt.get("schema") != SCHEMA
                or receipt.get("read_only") is not True
                or receipt.get("source_frame") != frame
                or receipt.get("observed_treasury_raw") != treasury["raw"]):
            raise ValueError("aggregate war cash receipt crossed frame or treasury")
        observations = receipt.get("amount_observations")
        if not isinstance(observations, Mapping):
            raise ValueError("aggregate war cash receipt lacks amount observations")
        canonical = observe_active_war_cash_resource_v1(
            snapshot=snapshot, war_id=war_id, inputs={
                "source_frame": frame, "war_id": war_id,
                **{name: observations.get(name) for name in _AMOUNTS},
                "horizon_days": receipt.get("horizon_days"),
                "future_bound_assumptions": receipt.get("future_bound_assumptions"),
                "resource_claims": receipt.get("resource_claims"),
            },
        )
        for name, value in canonical.items():
            # Legacy single-war receipts may predate optional occupation rows.
            if name == "resource_claims" and value is None:
                continue
            if receipt.get(name) != value:
                raise ValueError(f"aggregate war cash receipt differs at {name}")
        by_war[war_id] = canonical

    missing: dict[str, str] = {}
    for war_id in war_ids:
        if war_id not in by_war:
            missing[f"war:{war_id}:receipt"] = "active_war_receipt_not_observed"
        else:
            missing.update({f"war:{war_id}:{key}": value
                            for key, value in by_war[war_id]["missing"].items()})

    values: dict[str, int | None] = {}
    resources: dict[str, list[dict[str, object]]] = {}
    for name in _AMOUNTS:
        unique: dict[tuple[str, str, int], dict[str, object]] = {}
        observed_in: dict[tuple[str, str, int], set[int]] = {}
        complete = len(by_war) == len(war_ids)
        for war_id, receipt in by_war.items():
            observation = receipt["amount_observations"][name]
            if (not isinstance(observation, Mapping)
                    or "resource_components" not in observation):
                missing[f"war:{war_id}:{name}:resources"] = (
                    "explicit_cost_resource_attribution_not_observed")
                complete = False
                continue
            for component in observation["resource_components"]:
                key = (component["resource_kind"], component["resource_id"],
                       component["owner_character_id"])
                if key in unique and unique[key] != component:
                    raise ValueError("shared war cash resource observations disagree")
                unique[key] = deepcopy(component)
                observed_in.setdefault(key, set()).add(war_id)
        for key, component in unique.items():
            if observed_in[key] != set(component["war_ids"]):
                missing[f"{name}:resource:{key}"] = (
                    "cost_resource_missing_from_declared_war_receipt")
                complete = False
        resources[name] = [unique[key] for key in sorted(unique)]
        values[name] = sum(row["raw"] for row in unique.values()) if complete else None

    horizon_values = {receipt["horizon_days"] for receipt in by_war.values()}
    horizon = (next(iter(horizon_values)) if len(horizon_values) == 1
               and None not in horizon_values and len(by_war) == len(war_ids)
               else None)
    if horizon is None:
        missing["horizon_days"] = "common_bounded_future_war_horizon_not_observed"
    claims_complete = len(by_war) == len(war_ids)
    claims: dict[str, set[object]] = {name: set() for name in _CLAIMS}
    for war_id, receipt in by_war.items():
        observed = receipt.get("resource_claims")
        if observed is None:
            missing[f"war:{war_id}:resource_claims"] = "war_resource_occupation_not_observed"
            claims_complete = False
        else:
            for name in _CLAIMS:
                claims[name].update(observed[name])
    occupied = ({name: sorted(items) for name, items in claims.items()}
                if claims_complete else None)
    future = values["future_war_cost_upper_raw"]
    risk = values["future_risk_budget_raw"]
    policy = values["policy_minimum_gold_reserve_raw"]
    future_ready = (future is not None and risk is not None and horizon is not None
                    and all(receipt["future_bound_assumptions"] is not None
                            for receipt in by_war.values()))
    return {
        "schema": AGGREGATE_SCHEMA,
        "status": "incomplete" if missing else "complete", "read_only": True,
        "formal_action_ready": False, "source_frame": frame, "war_ids": war_ids,
        "gold_scale": 100_000, "observed_treasury_raw": treasury["raw"],
        "existing_shared_gold_commitment_raw": values["pending_war_cash_raw"],
        "immediate_war_action_costs_raw": {
            str(war_id): by_war[war_id]["immediate_war_action_cost_raw"]
            if war_id in by_war else None for war_id in war_ids
        },
        "war_future_gold_cost_raw": future + risk if future_ready else None,
        "minimum_gold_reserve_raw": policy,
        "joint_gold_reserve_raw": (
            future + risk + policy if future_ready and policy is not None else None),
        "horizon_days": horizon,
        "future_bound_assumptions_by_war": {
            str(war_id): receipt["future_bound_assumptions"]
            for war_id, receipt in sorted(by_war.items())
        },
        "amount_values_raw": values, "amount_resources": resources,
        "existing_resource_claims": occupied,
        "war_receipts": [by_war[war_id] for war_id in sorted(by_war)],
        "missing": missing,
    }


def require_complete_aggregate_war_cash_resource_v1(
    receipt: object, *, frame: Mapping[str, object], war_ids: Sequence[int],
) -> dict[str, object]:
    """Consume a complete aggregate while retaining its original receipts."""
    if (not isinstance(receipt, Mapping) or receipt.get("schema") != AGGREGATE_SCHEMA
            or receipt.get("status") != "complete"
            or receipt.get("source_frame") != dict(frame)
            or receipt.get("war_ids") != sorted(war_ids)):
        raise ValueError("complete same-frame aggregate active-war cash resource required")
    canonical = observe_aggregate_active_war_cash_resource_v1(
        snapshot={**dict(frame), "paused": True, "map_ready": True,
                  "played_character_gold": {
                      "raw": receipt.get("observed_treasury_raw"), "scale": 100_000},
                  "active_wars": [{"war_id": war_id} for war_id in war_ids]},
        receipts=receipt.get("war_receipts"),
    )
    if canonical != receipt or canonical["status"] != "complete":
        raise ValueError("aggregate war cash differs from its sourced receipts")
    return deepcopy(canonical)


def _active_war_ids(snapshot: Mapping[str, object]) -> list[int]:
    wars = snapshot.get("active_wars")
    if (not isinstance(wars, list) or not wars
            or any(not isinstance(row, Mapping) or type(row.get("war_id")) is not int
                   or row["war_id"] <= 0 for row in wars)):
        raise ValueError("war cash requires exact active WarIDs")
    war_ids = [row["war_id"] for row in wars]
    if len(war_ids) != len(set(war_ids)):
        raise ValueError("war cash active WarIDs are duplicated")
    return sorted(war_ids)


def _resource_components(
    value: object, *, amount: int, frame: Mapping[str, object], war_id: int,
    active_war_ids: Sequence[int],
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("war cash resource_components must be explicit")
    result: list[dict[str, object]] = []
    identities: set[tuple[str, str, int]] = set()
    for row in value:
        if (not isinstance(row, Mapping)
                or any(type(row.get(key)) is not str or not row[key]
                       for key in ("resource_kind", "resource_id", "source"))
                or type(row.get("owner_character_id")) is not int
                or row["owner_character_id"] <= 0
                or type(row.get("raw")) is not int or row["raw"] < 0
                or row.get("scale") != 100_000 or row.get("source_frame") != dict(frame)):
            raise ValueError("war cash resource component lacks sourced identity or amount")
        wars = row.get("war_ids")
        if (not isinstance(wars, list) or war_id not in wars
                or any(type(item) is not int or item not in active_war_ids for item in wars)
                or len(wars) != len(set(wars))):
            raise ValueError("war cash resource component lacks exact war attribution")
        key = (row["resource_kind"], row["resource_id"], row["owner_character_id"])
        if key in identities:
            raise ValueError("war cash resource identity duplicated within one amount")
        identities.add(key)
        result.append({
            "resource_kind": key[0], "resource_id": key[1], "owner_character_id": key[2],
            "raw": row["raw"], "scale": 100_000, "source": row["source"],
            "source_frame": dict(frame), "war_ids": sorted(wars),
        })
    if sum(row["raw"] for row in result) != amount:
        raise ValueError("war cash amount differs from resource components")
    return sorted(result, key=lambda row: (
        row["resource_kind"], row["resource_id"], row["owner_character_id"]))


def _resource_claims(
    value: object, *, frame: Mapping[str, object], war_id: int,
) -> dict[str, object]:
    if (not isinstance(value, Mapping) or type(value.get("source")) is not str
            or not value["source"] or value.get("source_frame") != dict(frame)
            or value.get("war_id") != war_id):
        raise ValueError("war cash occupation needs same-frame sourced WarID")
    result: dict[str, object] = {
        "source": value["source"], "source_frame": dict(frame), "war_id": war_id,
    }
    for name in _CLAIMS:
        items = value.get(name)
        kind = str if name == "commitment_keys" else int
        if (not isinstance(items, list)
                or any(type(item) is not kind or (not item if kind is str else item <= 0)
                       for item in items) or len(items) != len(set(items))):
            raise ValueError(f"war cash occupation {name} must be explicit distinct claims")
        result[name] = sorted(items)
    return result
