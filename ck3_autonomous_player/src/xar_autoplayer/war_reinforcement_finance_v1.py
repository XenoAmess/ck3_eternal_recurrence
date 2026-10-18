"""Current contract quote and an explicit military cash allocation, not net income."""

from collections.abc import Mapping

from .activity_feast_stage5_budget_v1 import DISCRETIONARY_MAINTENANCE_RESERVATION_MONTHS


def observe_reinforcement_finance_v1(
    snapshot: Mapping[str, object], campaign_root: Mapping[str, object] | None, *,
    contract_gold_raw: object, contract_months: object, gold_floor_raw: int,
    maintenance_reservation_months: int = DISCRETIONARY_MAINTENANCE_RESERVATION_MONTHS,
    other_reserved_gold_raw: int = 0,
) -> dict[str, object]:
    """Reserve current maximum maintenance with no speculative future income.

    The native company quote purchases the whole observed contract. Current
    game's contract definition describes a one-time payment; we do not multiply
    it by months or add an invented recurring mercenary maintenance charge.
    """
    if type(maintenance_reservation_months) is not int or not 1 <= maintenance_reservation_months <= 18:
        raise ValueError("military allocation window must be a declared positive policy up to eighteen months")
    if type(other_reserved_gold_raw) is not int or other_reserved_gold_raw < 0:
        raise ValueError("other existing gold commitments must be a nonnegative raw amount")
    actor = snapshot.get("played_character")
    actor = actor.get("character_id") if isinstance(actor, Mapping) else None
    root = campaign_root if isinstance(campaign_root, Mapping) else {}
    gross = root.get("player_monthly_gold_income")
    maximum = root.get("player_max_monthly_gold_maintenance_v1")
    maximum = maximum.get("value") if isinstance(maximum, Mapping) and maximum.get("status") == "available" else None
    money = snapshot.get("played_character_gold")
    valid_amount = lambda row: (isinstance(row, Mapping) and type(row.get("raw")) is int
                                and row.get("scale") == 100_000)
    ready = (root.get("status") == "available" and root.get("player_character_id") == actor
             and root.get("snapshot_revision") == snapshot.get("native_revision")
             and root.get("date_raw") == snapshot.get("date_raw")
             and valid_amount(gross) and valid_amount(maximum) and maximum["raw"] >= 0
             and valid_amount(money) and type(contract_gold_raw) is int and contract_gold_raw >= 0
             and type(contract_months) is int and contract_months > 0)
    if not ready:
        return {"status": "unavailable", "reason": "same_frame_contract_treasury_income_or_maximum_maintenance_missing",
                "retains_military_allocation": False}
    months = min(contract_months, maintenance_reservation_months)
    reserve = max(gold_floor_raw, maximum["raw"] * months) + other_reserved_gold_raw
    after = money["raw"] - contract_gold_raw
    return {
        "status": "available", "scale": 100_000, "contract_gold_raw": contract_gold_raw,
        "source_frame": {"actor_character_id": actor, "native_revision": snapshot["native_revision"],
                         "date_raw": snapshot["date_raw"]},
        "contract_months": contract_months,
        "contract_payment_model": "native current one-time contract quote; no invented monthly company fee",
        "observed_treasury_raw": money["raw"], "gold_after_contract_raw": after,
        "gross_monthly_income_raw": gross["raw"],
        "maximum_monthly_military_maintenance_raw": maximum["raw"],
        "gross_less_maximum_military_raw": gross["raw"] - maximum["raw"],
        "gross_less_maximum_military_is_net_income": False,
        "maintenance_allocation_months": months,
        "maintenance_allocation_raw": maximum["raw"] * months,
        "required_gold_reserve_raw": reserve, "reserve_floor_includes_military_allocation": True,
        **({"other_reserved_gold_raw": other_reserved_gold_raw} if other_reserved_gold_raw else {}),
        "retains_military_allocation": after >= reserve,
        "cash_only_maximum_military_runway": {
            "numerator_gold_raw": max(0, after), "denominator_gold_per_month_raw": maximum["raw"],
            "whole_months": max(0, after) // maximum["raw"] if maximum["raw"] else None},
        "future_gross_income_credited_raw": 0,
        "complete_monthly_net_observed": False,
        "future_cost_upper_bound": False,
        "scope": "constant current maximum military-rate allocation; nonmilitary expenses and new conditions excluded",
    }
