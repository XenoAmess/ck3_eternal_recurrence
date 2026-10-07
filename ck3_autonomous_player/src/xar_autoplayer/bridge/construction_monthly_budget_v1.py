"""Construction cash scenarios using observed monthly rates, without actions.

These are constant-current-state extrapolations over explicit policy months.
They do not predict future war costs or the upkeep of a newly bought regiment.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .version_identity import CK3_12003, CK3_12004, require_exact_native_build
from .war_cash_private_transport_v1 import _monthly_flow


SCHEMA = "xar.ck3.construction-monthly-budget.v1"
SCALE = 100_000


def _arguments(cost: int, reserve: int, commitments: int, months: int) -> None:
    for name, amount in (
        ("construction_gold_cost_raw", cost), ("reserve_gold_raw", reserve),
        ("existing_commitment_gold_raw", commitments),
    ):
        if type(amount) is not int or amount < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if type(months) is not int or not 1 <= months <= 24:
        raise ValueError("horizon_months must be an integer from 1 to 24")


def _fixed(
    cash: Mapping[str, object], key: str, flag: str, reason: str,
    missing: dict[str, str],
) -> int | None:
    value = cash.get(key)
    ready = cash["readiness"].get(flag)
    if value is None:
        if ready is not False or not isinstance(cash.get(reason), str) or not cash[reason]:
            raise ValueError(f"{key} unavailable observation is malformed")
        missing[key] = cash[reason]
        return None
    if (not isinstance(value, Mapping) or type(value.get("raw")) is not int
            or not -(1 << 63) <= value["raw"] < (1 << 63)
            or type(value.get("scale")) is not int or value["scale"] != SCALE
            or ready is not True or cash.get(reason) is not None):
        raise ValueError(f"{key} available observation is malformed")
    return value["raw"]


def _maintenance(
    cash: Mapping[str, object], kind: str, missing: dict[str, str],
) -> int | None:
    expenses = cash.get("military_expenses")
    row = expenses.get(kind) if isinstance(expenses, Mapping) else None
    key = f"military_expenses.{kind}"
    flag = f"{kind}_military_expenses_ready"
    if not isinstance(row, Mapping):
        raise ValueError(f"{key} normalized observation is absent")
    if row.get("status") == "unavailable":
        reason = row.get("unavailable_reason")
        if (cash["readiness"].get(flag) is not False
                or not isinstance(reason, str) or not reason):
            raise ValueError(f"{key} unavailable observation is malformed")
        missing[key] = reason
        return None
    vector = row.get("resource_raw_native")
    if (row.get("status") != "available"
            or cash["readiness"].get(flag) is not True
            or not isinstance(vector, list) or len(vector) != 10
            or any(type(raw) is not int or not -(1 << 63) <= raw < (1 << 63)
                   for raw in vector)
            or row.get("gold_raw") != vector[0]):
        raise ValueError(f"{key} available observation is malformed")
    return vector[0]


def _scenario(
    *, treasury: int | None, rate: int | None, cost: int, reserve: int,
    commitments: int, months: int, missing: dict[str, str],
) -> dict[str, object]:
    start = (treasury - cost - commitments
             if treasury is not None and "same_frame_ready" not in missing else None)
    result: dict[str, object] = {
        "scenario_ready": not missing,
        "net_monthly_gold_raw": rate,
        "cash_after_construction_and_commitments_raw": start,
        "projected_ending_gold_raw": None,
        "burn_reservation_raw": None,
        "minimum_projected_gold_raw": None,
        "scenario_floor_ready": None,
        "maximum_one_off_spend_raw": None,
        "first_month_reserve_breach": None,
        "missing_inputs": dict(missing),
    }
    if missing:
        return result
    end = start + rate * months
    burn = max(0, -rate) * months
    minimum = min(start, end)
    breach = None
    if start < reserve:
        breach = 0
    elif rate < 0:
        crossing = (start - reserve) // -rate + 1
        if crossing <= months:
            breach = crossing
    result.update(
        projected_ending_gold_raw=end, burn_reservation_raw=burn,
        minimum_projected_gold_raw=minimum,
        scenario_floor_ready=minimum >= reserve,
        maximum_one_off_spend_raw=max(0, treasury - commitments - reserve - burn),
        first_month_reserve_breach=breach,
    )
    return result


def project_construction_monthly_budget_v1(
    cash: dict[str, object], *, construction_gold_cost_raw: int,
    reserve_gold_raw: int, existing_commitment_gold_raw: int,
    horizon_months: int,
) -> dict[str, object]:
    """Consume a normalized .3/.4 cash-v2 observation without choosing a step.

    Current NET already contains military expenses. The all-raised scenario
    substitutes its alternative military total once, keeping other income and
    expenses fixed. Maximum one-off spend includes commitments, reserve and
    negative-rate burn, and never borrows against a positive projected income.
    Construction cost is the caller's quoted gold amount; this helper neither
    queries nor verifies that construction quote's native provenance.
    A breach at month 0 means the construction/commitments already cross the
    floor; null means no breach within a ready scenario's stated horizon.
    """
    _arguments(construction_gold_cost_raw, reserve_gold_raw,
               existing_commitment_gold_raw, horizon_months)
    if (not isinstance(cash, dict)
            or cash.get("schema") != "xar.ck3.war-cash-current-resources.v1"
            or cash.get("read_only") is not True):
        raise ValueError("normalized current cash resources are required")
    build = require_exact_native_build(cash.get("game_version"), cash.get("executable_sha256"))
    if build not in (CK3_12003, CK3_12004):
        raise ValueError("construction monthly budget requires exact .3 or .4")
    if cash.get("monthly_income_semantics") is None:
        raise ValueError("construction monthly budget requires a v2 NET semantics marker")
    _monthly_flow(cash)
    missing: dict[str, str] = {}
    if cash["readiness"].get("same_frame_ready") is not True:
        missing["same_frame_ready"] = "war_cash_same_frame_unavailable"
    treasury = _fixed(cash, "current_treasury", "current_treasury_ready",
                      "current_treasury_unavailable_reason", missing)
    net = _fixed(cash, "player_monthly_net_income", "monthly_net_income_ready",
                 "monthly_net_income_unavailable_reason", missing)
    maintenance_missing: dict[str, str] = {}
    current = _maintenance(cash, "current", maintenance_missing)
    all_raised = _maintenance(cash, "all_raised", maintenance_missing)
    all_raised_rate = net + current - all_raised if all(
        amount is not None for amount in (net, current, all_raised)) else None
    args = {
        "treasury": treasury, "cost": construction_gold_cost_raw,
        "reserve": reserve_gold_raw, "commitments": existing_commitment_gold_raw,
        "months": horizon_months,
    }
    scenarios = {
        "current": _scenario(**args, rate=net, missing=missing),
        "all_raised": _scenario(**args, rate=all_raised_rate,
                                missing={**missing, **maintenance_missing}),
    }
    return {
        "schema": SCHEMA,
        "status": "available" if all(row["scenario_ready"] for row in scenarios.values()) else "partial",
        "projection_kind": "constant_current_state_cash_scenarios",
        "read_only": True, "game_version": build.game_version,
        "executable_sha256": build.executable_sha256, "gold_scale": SCALE,
        "time_basis": "month", "horizon_months": horizon_months,
        "construction_gold_cost_raw": construction_gold_cost_raw,
        "construction_cost_basis": "caller_supplied_gold_quote",
        "reserve_gold_raw": reserve_gold_raw,
        "existing_commitment_gold_raw": existing_commitment_gold_raw,
        "source_frame": {key: cash.get(key) for key in (
            "played_character_id", "snapshot_revision", "date_raw",
            "queried_snapshot_id", "queried_revision", "queried_native_revision",
        )},
        "source_cash_resources": deepcopy(cash), "scenarios": scenarios,
        "assumptions": [
            "observed monthly income and nonmilitary expenses remain constant",
            "each scenario holds its observed military total constant for the explicit policy months",
            "all-raised replaces current military expense once across all wars",
            "only the explicit construction cost and existing commitments are deducted up front",
            "no future events, embark fees, new regiments, income gains or other transactions are predicted",
        ],
        "future_war_cost_upper_ready": False, "per_regiment_upkeep_ready": False,
        "selected_step": None, "formal_action_ready": False,
    }


def query_construction_monthly_budget_private_v1(
    driver: object, *, expected_revision: int, construction_gold_cost_raw: int,
    reserve_gold_raw: int, existing_commitment_gold_raw: int,
    horizon_months: int,
) -> dict[str, object]:
    """Read existing current-resource MCP exactly once, then project locally."""
    _arguments(construction_gold_cost_raw, reserve_gold_raw,
               existing_commitment_gold_raw, horizon_months)
    cash = driver.query_war_cash_current_resources_private_v1(
        expected_revision=expected_revision)
    return {
        **project_construction_monthly_budget_v1(
            cash, construction_gold_cost_raw=construction_gold_cost_raw,
            reserve_gold_raw=reserve_gold_raw,
            existing_commitment_gold_raw=existing_commitment_gold_raw,
            horizon_months=horizon_months),
        "source": "ck3_query_war_cash_current_resources_private_v1",
    }
