"""Cash-bounded strategic reserves with explicit purpose and arrival risk.

Declared marginal/cash thresholds are policy, not native AI or win probability.
This assessor preserves every market row and authorizes no movement or contact.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from .bridge.domain_construction_private_transport_v1 import RESERVE_RAW
from .normal_army_projected_contact_v1 import select_normal_army_projected_contact_v1
from .war_reinforcement_finance_v1 import observe_reinforcement_finance_v1
from .war_reinforcement_tradeoff_v1 import (
    _armies, _count, _stationary_staging, observe_war_spending_priority_v1,
)


def _recoverable_wars(priority):
    # -100 is a policy suppression of new procurement, not proof that an
    # observed active war has ended. Its armies stay in the global risk ledger.
    rows = [row for row in _armies(priority.get("wars"))
            if row.get("protect_cash_reasons") and type(row.get("war_id")) is int
            and type(row.get("player_relative_war_score")) is int
            and row["player_relative_war_score"] > -100]
    order = priority.get("cash_protection_priority_war_ids", [])
    return sorted(rows, key=lambda row: order.index(row["war_id"]) if row["war_id"] in order else len(order))


def observe_procurement_package_budget_v1(snapshot, ledger, *, purpose_war_ids):
    """Do not reset a procurement package's treasury-share cap after each hire.

    Count independently observed employment contracts as committed quote cost,
    without claiming payment attribution. Unknown submissions remain governed
    by the existing single pending claim, before this assessment is reached.
    """
    if not isinstance(ledger, Mapping):
        return {"status": "no_prior_package", "remaining_package_gold_raw": None}
    episode = snapshot.get("episode_run_id")
    actor = snapshot.get("played_character", {}).get("character_id")
    purposes = set(purpose_war_ids)
    records = []
    connected_wars = purposes | {row["war_id"] for row in _armies(snapshot.get("active_wars"))
        if row.get("player_is_primary_war_leader") is True and type(row.get("war_id")) is int}
    for row in _armies(ledger.get("observed")):
        if row.get("status") != "employment_observed":
            continue
        source = row.get("source_frame", {})
        decision = row.get("decision", {})
        selected = decision.get("selected_candidate", {})
        if source.get("episode_run_id") != episode or source.get("played_character_id") != actor:
            continue
        prior_purposes = selected.get("purpose_war_ids", selected.get("numerical_balance_reversed_war_ids", []))
        prior_scope = decision.get("war_spending_priority", {}).get("primary_war_hostile_union_v1", {}).get("war_ids", [])
        records.append((row, selected, set(prior_purposes) | set(prior_scope)))
    # Shared simultaneous wars cannot alternate fresh half-treasury caps. A
    # later overlapping contract retains the old package while any linked war
    # remains active; genuinely disjoint later wars can start a new package.
    changed = True
    while changed:
        changed = False
        for _, _, scope in records:
            if connected_wars.intersection(scope) and not scope.issubset(connected_wars):
                connected_wars.update(scope)
                changed = True
    receipts = []
    seen = set()
    for row, selected, scope in records:
        if not connected_wars.intersection(scope):
            continue
        identity = row.get("action_request_id")
        if not isinstance(identity, str) or not identity or identity in seen:
            return {"status": "unavailable", "reason": "same_purpose_contract_claim_identity_missing_or_duplicated",
                    "remaining_package_gold_raw": None}
        seen.add(identity)
        receipts.append((row, selected))
    if not receipts:
        return {"status": "no_prior_package", "remaining_package_gold_raw": None}
    first, anchor = receipts[0]
    finance = anchor.get("finance", {})
    treasury, reserve, cap = (finance.get("observed_treasury_raw"), finance.get("required_gold_reserve_raw"),
                              anchor.get("cash_opportunity_cost_limit_raw"))
    costs = [selected.get("gold_cost_raw") for _, selected in receipts]
    if (any(type(value) is not int or value < 0 for value in (treasury, reserve, cap))
            or any(type(value) is not int or value < 0 for value in costs)):
        return {"status": "unavailable", "reason": "same_purpose_original_package_budget_or_committed_quote_missing",
                "remaining_package_gold_raw": None}
    envelope = max(0, min(cap, treasury - reserve))
    committed = sum(costs)
    return {"status": "available", "anchor_action_request_id": first["action_request_id"],
            "anchor_source_frame": dict(first["source_frame"]), "purpose_war_ids": sorted(purposes),
            "shared_active_war_package_scope_ids": sorted(connected_wars),
            "original_treasury_raw": treasury, "original_required_reserve_raw": reserve,
            "original_treasury_share_cap_raw": cap, "original_package_gold_limit_raw": envelope,
            "committed_contract_quote_gold_raw": committed,
            "remaining_package_gold_raw": max(0, envelope - committed),
            "committed_action_request_ids": [row["action_request_id"] for row, _ in receipts],
            "payment_attribution_verified": False, "future_income_credited_raw": 0,
            "current_cash_and_military_reserve_must_also_pass": True}


def _strategic_need(war):
    """Declared policy triggers, never native loss probabilities or CB effects."""
    if not war:
        return {"worth_strategic_reserve": False, "critical_primary_title": False, "reasons": []}
    score = war.get("player_relative_war_score")
    losing = type(score) is int and score < 0
    stakes = war.get("target_stakes_v1", {})
    defensive = war.get("player_side") == "defender"
    primary = defensive and losing and stakes.get("primary_title_targeted") is True
    reasons = []
    if primary:
        reasons.append("losing_defence_targets_current_primary_title")
    if defensive and losing and stakes.get("directly_held_target_title_ids"):
        reasons.append("losing_defence_targets_current_directly_held_title")
    if war.get("possible_defensive_target_title_ids") and type(score) is int and score <= -25:
        reasons.append("defensive_title_exposure_and_policy_score_at_most_minus25")
    if losing and war.get("observed_primary_opponent_objective_occupation_province_ids"):
        reasons.append("losing_defence_with_observed_objective_occupation")
    if losing and war.get("observed_hostile_siege_in_player_subrealm_army_ids"):
        reasons.append("losing_own_war_with_observed_player_subrealm_hostile_siege")
    return {"worth_strategic_reserve": bool(reasons), "critical_primary_title": bool(primary), "reasons": reasons}


def observe_mercenary_purchase_model_need_v1(priority):
    """A threatened own war can use reserves even without a count deficit."""
    wars = _recoverable_wars(priority)
    useful = any(_strategic_need(war)["worth_strategic_reserve"] or war.get("raised_force_deficit") is True for war in wars)
    return {
        # Compatibility key only; it no longer limits policy to a count flip.
        "query_can_change_current_headcount_flip_model": useful,
        "query_can_change_strategic_reserve_model": useful,
        "purpose_war_ids": [row["war_id"] for row in wars],
        "reason": "concrete_strategic_stakes_or_current_deficit_to_compare" if useful else "no_current_evidence_of_reserve_value",
        "scope": "bounded strategic reserves; a current headcount deficit is not required",
        "future_enemy_reinforcements_bounded": False, "overall_war_safe": None,
        "pending_hire_observations_must_bypass": True,
    }


def _current_local_scope(snapshot, plan, history, focus):
    """Use a real current projected-contact query; absent inputs stay unknown.

    Plan-provided IDs alone are insufficient. The existing normal selector
    revalidates the complete DTO and snapshot/public/native/connection/episode
    query binding. Each own unit is allocated to this one target only.
    """
    projection = plan.get("projected_contact_scope") if isinstance(plan, Mapping) else None
    missing = {"status": "unavailable", "reason": "no_valid_current_target_contact_query",
               "allocated_player_army_ids": [], "local_hostile_army_ids": [],
               "player_current_soldiers": None, "enemy_current_soldiers": None,
               "arrival_eta_days": None, "company_arrival_verified": False}
    if not isinstance(projection, Mapping) or not focus:
        return missing
    actor = snapshot.get("played_character", {}).get("character_id")
    subject = projection.get("subject_army_id")
    own_rows = _armies(snapshot.get("player_armies"))
    own = [row for row in own_rows if row.get("army_id") == subject
           and row.get("controllable") is True and row.get("owner_character_id") == actor]
    if len(own) != 1:
        return missing
    try:
        selected = select_normal_army_projected_contact_v1(
            dict(snapshot), [{**row, "step": row.get("command", row.get("step"))}
                             for row in history if isinstance(row, Mapping)],
            subject_army_id=subject, target_province_id=projection.get("target_province_id"),
            incoming_entry_province_id=projection.get("incoming_entry_province_id"),
            subject_current_province_id=own[0].get("current_province_id"),
            subject_owner_character_id=actor,
        )
    except (TypeError, ValueError):
        return missing
    if selected.get("status") != "available" or selected.get("transition_kind") == "none":
        return missing
    scope = selected["projection"]
    friendly = scope["projected_attacker_army_ids"] if selected["subject_side"] == "attacker" else scope["projected_defender_army_ids"]
    hostile = scope["projected_defender_army_ids"] if selected["subject_side"] == "attacker" else scope["projected_attacker_army_ids"]
    current_war = next((row for row in _armies(snapshot.get("active_wars")) if row.get("war_id") == focus["war_id"]), {})
    hostile_rows = _armies(current_war.get("enemy_armies"))
    own_by_id = {row.get("army_id"): row for row in own_rows}
    enemy_by_id = {row.get("army_id"): row for row in hostile_rows}
    if (not all(identity in own_by_id for identity in friendly)
            or not all(identity in enemy_by_id for identity in hostile)):
        return {**missing, "reason": "target_membership_not_complete_for_selected_war"}
    own_count = _count([own_by_id[identity] for identity in friendly], snapshot=snapshot, role="player")
    enemy_count = _count([enemy_by_id[identity] for identity in hostile], snapshot=snapshot,
                         role="active_war_enemy", war_id=focus["war_id"])
    return {"status": "available" if own_count is not None and enemy_count is not None else "counts_unavailable",
            "war_id": focus["war_id"], "target_province_id": scope["target_province_id"],
            "allocated_player_army_ids": list(friendly), "local_hostile_army_ids": list(hostile),
            "player_current_soldiers": own_count, "enemy_current_soldiers": enemy_count,
            "source": "same-frame native ordered projected-contact members; current target state only",
            "source_frame": {key: snapshot.get(key) for key in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")},
            "company_arrival_verified": False, "arrival_eta_days": None,
            "other_hostile_armies_excluded_from_local_comparison_only": True,
            "future_contact_authorized": False, "battle_win_probability": None}


def assess_mercenary_reinforcement_v1(snapshot, context, *, minimum_gold_reserve_raw=RESERVE_RAW,
                                     campaign_root=None, operational_plan=None, history=(), procurement_ledger=None):
    """Compare every company and select a legal cash-bounded reserve purchase.

    A current local count reversal is useful conditional arithmetic. Otherwise
    select the best observed soldiers/contract-gold ratio, then lower cost and
    CompanyID. These declared criteria are not calibrated combat utility.
    """
    if type(minimum_gold_reserve_raw) is not int or minimum_gold_reserve_raw < 0:
        raise ValueError("reinforcement reserve must be a nonnegative raw gold amount")
    priority = observe_war_spending_priority_v1(snapshot, campaign_root=campaign_root)
    wars = _recoverable_wars(priority)
    focus = wars[0] if wars else None
    reserve_need = _strategic_need(focus)
    package = observe_procurement_package_budget_v1(snapshot, procurement_ledger,
        purpose_war_ids=[focus["war_id"]] if focus else [])
    local = _current_local_scope(snapshot, operational_plan, history, focus)
    actor = snapshot.get("played_character", {}).get("character_id")
    money = snapshot.get("played_character_gold")
    treasury = money.get("raw") if isinstance(money, Mapping) and money.get("scale") == 100000 and type(money.get("raw")) is int else None
    context_current = (context.get("available") is True
                       and context.get("actor_character_id") == actor
                       and context.get("date_raw") == snapshot.get("date_raw")
                       and type(context.get("capture_epoch")) is int and context["capture_epoch"] > 0)
    hostiles = [army for war in _armies(snapshot.get("active_wars"))
                for army in _armies(war.get("enemy_armies"))]
    assessments = []
    for company in _armies(context.get("rows")):
        terms = company.get("final_terms") if isinstance(company.get("final_terms"), Mapping) else {}
        strength = company.get("troop_strength") if isinstance(company.get("troop_strength"), Mapping) else {}
        location = company.get("location") if isinstance(company.get("location"), Mapping) else {}
        costs = terms.get("resource_costs_raw")
        full_costs = (isinstance(costs, list) and len(costs) == 10
                      and all(type(amount) is int and amount >= 0 for amount in costs)
                      and terms.get("resource_scale") == 100000 and terms.get("available") is True)
        price = costs[0] if full_costs else None
        troops = strength.get("current_soldiers")
        spawn = location.get("hire_auto_raise_province_id")
        finance = observe_reinforcement_finance_v1(snapshot, campaign_root,
            contract_gold_raw=price, contract_months=terms.get("hire_duration_months"),
            gold_floor_raw=minimum_gold_reserve_raw)
        reasons = []
        if not context_current:
            reasons.append("native_current_actor_date_company_collection_unavailable")
        ready = company.get("readiness_v1")
        if not isinstance(ready, Mapping) or ready.get("hire_ready") is not True or not full_costs:
            reasons.append("native_composition_or_complete_hire_terms_not_ready")
        if terms.get("can_hire") is not True or terms.get("can_afford") is not True:
            reasons.append("native_hire_or_affordability_rejected")
        if company.get("employer_id") is not None:
            reasons.append("company_already_employed")
        if finance.get("retains_military_allocation") is not True:
            reasons.append("same_frame_contract_and_military_cash_allocation_not_ready_or_not_retained")
        if type(troops) is not int or troops <= 0 or strength.get("available") is not True:
            reasons.append("positive_current_company_strength_unavailable")
        if (type(spawn) is not int or spawn <= 0
                or location.get("hire_auto_raise_position_ready") is not True
                or location.get("hire_auto_raise_attempted_in_active_war") is not True):
            reasons.append("native_active_war_spawn_unavailable")
        if type(company.get("company_id")) is not int or company["company_id"] < 0:
            reasons.append("full_company_identity_unavailable")
        if not focus:
            reasons.append("no_current_recoverable_own_war_need")
        spawn_hostiles = sorted({row["army_id"] for row in hostiles
                                 if row.get("current_province_id") == spawn and type(row.get("army_id")) is int})
        if spawn_hostiles:
            reasons.append("currently_observed_hostile_army_at_predicted_spawn")
        staging = [row for row in _armies(snapshot.get("player_armies")) if _stationary_staging(row, spawn)] if type(spawn) is int else []
        staging_count = _count(staging, snapshot=snapshot, role="player") if staging else None
        own_count, enemy_count = local.get("player_current_soldiers"), local.get("enemy_current_soldiers")
        combined = own_count + troops if type(own_count) is int and type(troops) is int else None
        flip = (type(own_count) is int and type(enemy_count) is int and type(combined) is int
                and own_count < enemy_count < combined)
        purpose = "conditional_local_deficit_reinforcement" if flip else "strategic_reserve_for_threatened_own_war"
        # Headcount is a coarse marginal-value policy only. A local source
        # takes precedence over global own troops; otherwise use observed own
        # force, falling back to the focused war's enemies if none are raised.
        reference = own_count if type(own_count) is int and own_count > 0 else (focus or {}).get("observed_player_raised_soldiers")
        if type(reference) is not int or reference <= 0:
            reference = (focus or {}).get("observed_enemy_raised_soldiers")
        minimum_marginal = (reference + 3) // 4 if type(reference) is int and reference > 0 else None
        if not flip and not reserve_need["worth_strategic_reserve"]:
            reasons.append("no_concrete_stakes_or_current_deterioration_worth_strategic_spend")
        if not flip and (minimum_marginal is None or type(troops) is not int or troops < minimum_marginal):
            reasons.append("strategic_marginal_headcount_below_policy_quarter_or_unknown")
        cash_fraction_denominator = 2 if flip or reserve_need["critical_primary_title"] else 3
        cash_share_limit = treasury // cash_fraction_denominator if type(treasury) is int and treasury >= 0 else None
        if cash_share_limit is None or type(price) is not int or price > cash_share_limit:
            reasons.append("contract_exceeds_declared_cash_opportunity_cost_limit")
        if package["status"] == "unavailable":
            reasons.append("same_purpose_original_procurement_package_budget_unavailable")
        elif (package["status"] == "available"
              and (type(price) is not int or price > package["remaining_package_gold_raw"])):
            reasons.append("contract_exceeds_remaining_same_purpose_package_budget")
        assessments.append({
            "company_id": company.get("company_id"), "gold_cost_raw": price,
            "quoted_resource_costs_raw": list(costs) if full_costs else None,
            "gold_after_hire_raw": treasury - price if treasury is not None and type(price) is int else None,
            "company_current_soldiers": troops, "friendly_staging_soldiers": staging_count,
            "reinforced_staging_soldiers": staging_count + troops if staging_count is not None and type(troops) is int else None,
            "predicted_auto_raise_province_id": spawn,
            "staging_army_ids": sorted({row["army_id"] for row in staging}),
            "spawn_requires_preexisting_friendly_army": False,
            "observed_hostile_at_predicted_spawn_army_ids": spawn_hostiles,
            "purpose": purpose, "purpose_war_ids": [focus["war_id"]] if focus else [],
            "strategic_need": reserve_need,
            "marginal_reference_observed_soldiers": reference,
            "strategic_minimum_marginal_soldiers": minimum_marginal,
            "cash_opportunity_cost_limit_raw": cash_share_limit,
            "cash_opportunity_cost_fraction": f"1/{cash_fraction_denominator}",
            "procurement_package_budget_v1": package,
            "numerical_balance_reversed_war_ids": [focus["war_id"]] if flip else [],
            "conditional_local_player_soldiers_after_arrival": combined,
            "local_comparison": local,
            "comparison_condition": "company arrives and remains available; arrival and effective combat strength unverified",
            "multiple_primary_wars_share_force": len(priority["primary_war_hostile_union_v1"]["war_ids"]) > 1,
            "comparison_enemy_current_soldiers": priority["primary_war_hostile_union_v1"]["observed_current_soldiers"],
            "global_enemy_count_is_purchase_reversal_threshold": False,
            "arrival_eta_days": None, "arrival_risk_accepted_for_strategic_purpose": not bool(reasons),
            "guaranteed_emergency_rescue": False, "battle_win_probability": None,
            "finance": finance, "rejection_reasons": reasons,
        })
    eligible = [row for row in assessments if not row["rejection_reasons"]]
    local_flips = [row for row in eligible if row["numerical_balance_reversed_war_ids"]]
    if local_flips:
        chosen = min(local_flips, key=lambda row: (row["gold_cost_raw"], -row["company_current_soldiers"], row["company_id"]))
    else:
        chosen = min(eligible, key=lambda row: (
            row["gold_cost_raw"] != 0,
            -Fraction(row["company_current_soldiers"], max(1, row["gold_cost_raw"])),
            row["gold_cost_raw"], row["company_id"])) if eligible else None
    return {
        "schema": "xar.mercenary-reinforcement-tradeoff.v1", "policy_revision": "strategic-reserve-v1",
        "actor_character_id": actor, "war_spending_priority": priority,
        "candidates": assessments, "selected_company_id": chosen["company_id"] if chosen else None,
        "selected_candidate": chosen, "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        # Existing submission compatibility; purpose, not this legacy label,
        # describes whether local or longer-term reinforcements were selected.
        "recommendation": "hire_local_reinforcement" if chosen else "continue_existing_war_action",
        "selection_comparison": "highest-stakes protected war; cheapest conditional local count flip, otherwise soldiers per quoted gold; lower cost then full CompanyID",
        "policy_thresholds": {"strategic_defensive_exposure_score_at_most": -25,
                              "strategic_minimum_marginal_headcount_fraction": "1/4 of observed relevant current force",
                              "ordinary_strategic_treasury_spend_cap_fraction": "1/3",
                              "primary_title_or_conditional_local_flip_treasury_spend_cap_fraction": "1/2",
                              "native_rules_or_calibrated_win_probability": False},
        "arrival_model": "native predicted auto-raise province; no pre-hire CUnit route; ETA unknown accepted as strategic risk",
        "arrival_eta_days": None, "battle_win_probability": None,
        "model_limits": ["current headcount is not combat power", "no rescue credit for a current battle or siege deadline",
                         "no pre-hire route or guaranteed arrival time", "current military allocation is not a future cost bound",
                         "reserve efficiency is not a calibrated utility or win probability", "native spawn selector does not publish every safety branch"],
        "postcondition_verified": False,
    }


def observe_first_raised_inventory_v1(snapshot, employment):
    """Persist the first independent inventory delta, even if it later moves.

    This is an anti-duplicate observation milestone, not strict proof that a
    company created the army. Employment and company attribution stay separate.
    """
    prior = employment.get("first_raised_inventory_observation_v1")
    source = employment.get("source_frame", {})
    selected = employment.get("decision", {}).get("selected_candidate", {})
    if isinstance(prior, Mapping):
        binding = prior.get("source_frame", {})
        old_ids = set(employment.get("pre_player_army_ids", []))
        rows = _armies(prior.get("observed_new_player_armies"))
        if (prior.get("company_id") == employment.get("company_id")
                and binding.get("episode_run_id") == source.get("episode_run_id")
                and binding.get("episode_run_id") == snapshot.get("episode_run_id")
                and binding.get("played_character_id") == source.get("played_character_id")
                and binding.get("played_character_id") == snapshot.get("played_character", {}).get("character_id")
                and type(binding.get("native_revision")) is int
                and type(source.get("native_revision")) is int
                and type(snapshot.get("native_revision")) is int
                and snapshot["native_revision"] >= binding["native_revision"] > source["native_revision"]
                and prior.get("predicted_auto_raise_province_id") == selected.get("predicted_auto_raise_province_id")
                and rows and all(type(row.get("army_id")) is int and row["army_id"] not in old_ids
                    and row.get("controllable") is True
                    and row.get("current_province_id") == selected.get("predicted_auto_raise_province_id")
                    and type(row.get("current_soldiers")) is int and row["current_soldiers"] > 0 for row in rows)):
            return dict(prior)
    post = observe_post_hire_inventory_v1(snapshot, employment)
    frame = post["source_frame"]
    if (frame.get("episode_run_id") != source.get("episode_run_id")
            or frame.get("played_character_id") != source.get("played_character_id")
            or type(frame.get("native_revision")) is not int or type(source.get("native_revision")) is not int
            or frame["native_revision"] <= source["native_revision"]):
        return None
    matches = [row for row in post["new_observed_player_armies"]
               if row.get("controllable") is True
               and row.get("current_province_id") == selected.get("predicted_auto_raise_province_id")
               and type(row.get("current_soldiers")) is int and row["current_soldiers"] > 0]
    if not matches:
        return None
    return {"company_id": employment.get("company_id"), "source_frame": frame,
            "pre_source_frame": dict(source), "pre_player_army_ids": post["pre_player_army_ids"],
            "observed_new_player_armies": matches,
            "predicted_auto_raise_province_id": selected.get("predicted_auto_raise_province_id"),
            "observation_kind": "independent_player_inventory_delta_not_strict_company_attribution",
            "company_to_new_army_binding_verified": False, "army_creation_verified": False,
            "does_not_require_army_to_remain_at_spawn_on_later_turns": True}


def observe_post_hire_inventory_v1(snapshot, pending):
    """Record independent observations without asserting payment/army causation."""
    from .m5_observed_opportunity_selector import observed_frame
    selected = pending.get("decision", {}).get("selected_candidate", {})
    old_ids = set(pending.get("pre_player_army_ids", []))
    money = snapshot.get("played_character_gold")
    gold = money.get("raw") if isinstance(money, Mapping) and money.get("scale") == 100000 and type(money.get("raw")) is int else None
    before = selected.get("finance", {}).get("observed_treasury_raw")
    inventory = [{"army_id": row.get("army_id"), "current_province_id": row.get("current_province_id"),
                  "current_soldiers": _count([row], snapshot=snapshot, role="player"),
                  "controllable": row.get("controllable")}
                 for row in _armies(snapshot.get("player_armies")) if row.get("army_id") not in old_ids]
    return {"pre_source_frame": dict(pending.get("source_frame", {})),
            "pre_capture_epoch": pending.get("pre_capture_epoch"),
            "pre_player_army_ids": sorted(old_ids), "pre_treasury_raw": before,
            "source_frame": observed_frame(snapshot), "post_treasury_raw": gold,
            "treasury_delta_raw": gold - before if type(gold) is int and type(before) is int else None,
            "quoted_contract_gold_raw": selected.get("gold_cost_raw"),
            "new_observed_player_armies": inventory,
            "payment_verified": False, "army_creation_verified": False,
            "company_to_new_army_binding_verified": False,
            "limits": "wallet change may include other flows; new IDs may have other causes; employment, payment, and army attribution are separate"}
