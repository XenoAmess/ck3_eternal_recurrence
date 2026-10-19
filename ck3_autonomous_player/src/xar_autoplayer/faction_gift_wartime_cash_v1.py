"""Preserve military cash before a new optional faction gift; never query CK3."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .activity_feast_stage5_budget_v1 import DISCRETIONARY_MAINTENANCE_RESERVATION_MONTHS
from .m5_observed_opportunity_selector import observed_frame


# The existing ordinary military finance policy uses this floor and eighteen
# months of current maximum maintenance. These are policy allocations, not
# native affordability rules or an upper bound on future war costs.
MILITARY_CASH_FLOOR_RAW = 20_000_000


def assess_faction_gift_wartime_cash_v1(snapshot, candidate, *, root=None,
        spending=None, market=None, market_source_frame=None, mercenary_ledger=None):
    result = {"schema": "xar.faction-gift-wartime-cash/v1",
        "source_frame": observed_frame(snapshot), "new_gift_spending_allowed": False,
        "policy_floor_raw": MILITARY_CASH_FLOOR_RAW,
        "future_income_or_unreceived_financing_credited_raw": 0,
        "thresholds_are_native_or_user_hard_limits": False}

    def defer(reason):
        return {**result, "status": "defer_new_gift", "reason": reason}

    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or any(not isinstance(war, Mapping)
            or type(war.get("war_id")) is not int or war["war_id"] <= 0 for war in wars):
        return defer("current_war_scope_unobserved")
    if not wars:
        return {**result, "status": "outside_wartime", "new_gift_spending_allowed": True}
    choice = candidate.get("choice") if isinstance(candidate, Mapping) else None
    observation = candidate.get("observation") if isinstance(candidate, Mapping) else None
    actor = snapshot.get("played_character", {}).get("character_id")
    money = snapshot.get("played_character_gold")
    if (not isinstance(choice, Mapping) or not isinstance(observation, Mapping)
            or choice.get("player_character_id") != actor
            or choice.get("native_snapshot_revision") != snapshot.get("native_revision")
            or choice.get("date_raw") != snapshot.get("date_raw")
            or observation.get("native_snapshot_revision") != snapshot.get("native_revision")
            or observation.get("observed_date_raw") != snapshot.get("date_raw")
            or observation.get("player_character_id") != actor
            or not isinstance(money, Mapping) or money.get("scale") != 100000
            or type(money.get("raw")) is not int
            or observation.get("player_gold_scale") != 100000
            or observation.get("player_gold_raw") != money["raw"]
            or type(choice.get("gold_cost_raw")) is not int or choice["gold_cost_raw"] < 0
            or not isinstance(observation.get("gift_preview"), Mapping)
            or observation["gift_preview"].get("gold_cost_raw") != choice["gold_cost_raw"]):
        return defer("same_frame_gift_quote_and_treasury_unobserved")
    after = money["raw"] - choice["gold_cost_raw"]
    result.update(observed_treasury_raw=money["raw"], gift_gold_cost_raw=choice["gold_cost_raw"],
                  gold_after_gift_raw=after)
    # A failed lower bound is decisive even if additional commitments or the
    # emergency market are unknown. Never invent zeroes to approve a spend.
    if after < MILITARY_CASH_FLOOR_RAW:
        return defer("wartime_gift_would_breach_military_cash_floor")
    if (not isinstance(root, Mapping) or root.get("status") != "available"
            or root.get("player_character_id") != actor
            or root.get("snapshot_revision") != snapshot.get("native_revision")
            or root.get("date_raw") != snapshot.get("date_raw")):
        return defer("same_frame_maximum_military_maintenance_unobserved")
    maximum = root.get("player_max_monthly_gold_maintenance_v1")
    rate = maximum.get("value") if isinstance(maximum, Mapping) and maximum.get("status") == "available" else None
    if (not isinstance(rate, Mapping) or rate.get("scale") != 100000
            or type(rate.get("raw")) is not int or rate["raw"] < 0):
        return defer("same_frame_maximum_military_maintenance_unobserved")
    frame = {"actor_character_id": actor, "native_revision": snapshot.get("native_revision"),
             "date_raw": snapshot.get("date_raw"), "snapshot_id": snapshot.get("snapshot_id")}
    budget = spending.get("budget") if isinstance(spending, Mapping) and spending.get("status") == "observed" else None
    reserved = budget.get("reserved_raw") if isinstance(budget, Mapping) else None
    if (not isinstance(spending, Mapping) or spending.get("frame") != frame
            or not isinstance(reserved, Mapping) or type(reserved.get("gold")) is not int
            or reserved["gold"] < 0 or budget.get("active_war_count") != len(wars)):
        return defer("same_frame_existing_spending_commitments_unobserved")
    if not isinstance(mercenary_ledger, Mapping) or mercenary_ledger.get("pending") is not None:
        return defer("mercenary_commitment_unknown_or_pending")
    if (not isinstance(market, Mapping) or market.get("available") is not True
            or market.get("actor_character_id") != actor or market.get("date_raw") != snapshot.get("date_raw")
            or market_source_frame != observed_frame(snapshot) or not isinstance(market.get("rows"), list)):
        return defer("same_frame_native_emergency_quotes_unobserved")
    hostile = {army.get("current_province_id") for war in wars
        for army in (war.get("enemy_armies") if isinstance(war.get("enemy_armies"), list) else [])
        if isinstance(army, Mapping)}
    quotes = []
    for row in market["rows"]:
        if not isinstance(row, Mapping):
            continue
        terms, strength, location, readiness = (row.get(key) for key in
            ("final_terms", "troop_strength", "location", "readiness_v1"))
        if not all(isinstance(item, Mapping) for item in (terms, strength, location, readiness)):
            continue
        costs = terms.get("resource_costs_raw")
        spawn = location.get("hire_auto_raise_province_id")
        if (isinstance(costs, list) and len(costs) == 10
                and all(type(value) is int and value >= 0 for value in costs)
                and terms.get("resource_scale") == 100000 and terms.get("available") is True
                and terms.get("can_hire") is True and terms.get("can_afford") is True
                and readiness.get("hire_ready") is True and row.get("employer_id") is None
                and type(row.get("company_id")) is int and row["company_id"] >= 0
                and strength.get("available") is True and type(strength.get("current_soldiers")) is int
                and strength["current_soldiers"] > 0 and type(spawn) is int and spawn > 0
                and location.get("hire_auto_raise_position_ready") is True
                and location.get("hire_auto_raise_attempted_in_active_war") is True and spawn not in hostile):
            quotes.append({"company_id": row["company_id"], "complete_contract_gold_raw": costs[0]})
    if not quotes:
        return defer("no_current_native_usable_emergency_contract_quote")
    emergency = max(quotes, key=lambda row: (row["complete_contract_gold_raw"], row["company_id"]))
    military = max(MILITARY_CASH_FLOOR_RAW, rate["raw"] * DISCRETIONARY_MAINTENANCE_RESERVATION_MONTHS)
    required = military + reserved["gold"] + emergency["complete_contract_gold_raw"]
    return {**result, "status": "war_cash_retained" if after >= required else "defer_new_gift",
        "reason": "retain_current_military_commitments_and_emergency_contract",
        "new_gift_spending_allowed": after >= required, "required_remaining_gold_raw": required,
        "military_buffer_raw": military, "existing_unpaid_commitments_raw": reserved["gold"],
        "emergency_quote": emergency, "qualified_quote_count": len(quotes),
        "arrival_or_victory_verified": False}


def observe_faction_gift_wartime_cash_v1(driver, snapshot, candidate, *, root, history):
    """Reuse existing same-frame inputs and bounded local spending ledgers."""
    early = assess_faction_gift_wartime_cash_v1(snapshot, candidate, root=root)
    if early.get("status") == "outside_wartime" or early.get("reason") not in {
            "same_frame_existing_spending_commitments_unobserved"}:
        return early
    from .activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1
    from .war_mercenary_consumer_v1 import _context_with_reference, _ledger
    directory = getattr(driver, "state_dir", None)
    if not isinstance(directory, Path):
        return early
    frame = observed_frame(snapshot)
    spending = observe_feast_start_budget_v1(snapshot, {
        "actor_character_id": frame["played_character_id"], "snapshot_revision": frame["native_revision"],
        "date_raw": frame["date_raw"], "post_snapshot_id": frame["snapshot_id"],
        "queried_revision": frame["revision"]}, state_dir=directory, campaign_root=root)
    market, reference = _context_with_reference(history, snapshot)
    return assess_faction_gift_wartime_cash_v1(snapshot, candidate, root=root, spending=spending,
        market=market, market_source_frame=reference.get("source_frame") if isinstance(reference, Mapping) else None,
        mercenary_ledger=_ledger(directory))
