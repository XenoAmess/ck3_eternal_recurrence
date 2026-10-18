"""Narrow, source-bound emergency funding policy; no movement or win forecast."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json

from .m5_observed_opportunity_selector import observed_frame
from .war_reinforcement_finance_v1 import observe_reinforcement_finance_v1


def priority_emergency_level_v1(war):
    """Require identified major defensive stakes and corroborated deterioration."""
    stakes = war.get("target_stakes_v1", {})
    major = (stakes.get("current_root_available") is True
             and (stakes.get("primary_title_targeted") is True or war.get("major_direct_title_targeted") is True))
    score = war.get("player_relative_war_score")
    occupied = bool(war.get("observed_primary_opponent_objective_occupation_province_ids"))
    siege = bool(war.get("observed_hostile_siege_in_player_subrealm_army_ids"))
    deficit = war.get("raised_force_deficit") is True
    if (war.get("primary_player_war") is not True or war.get("player_side") != "defender"
            or not major or type(score) is not int):
        return 0
    # Policy values, not native thresholds: an isolated bad score is insufficient.
    deadline = war.get("observed_risk_deadline_days")
    imminent_siege = siege and type(deadline) is int and deadline <= 7
    if score <= -75 and (occupied and (deficit or siege) or imminent_siege and deficit):
        return 2
    return int((score <= -50 and (deficit or occupied or siege))
               or (score <= -25 and occupied and siege))


def observe_emergency_policy_v1(snapshot, priority, root, spending):
    """A missing input preserves normal policy and the existing war action."""
    from .war_reinforcement_tradeoff_v1 import _armies, _current_root

    normal = {"level": 0, "eligible": False, "reason": "normal_policy_or_missing_emergency_evidence"}
    current_root = _current_root(snapshot, root)
    if not current_root or not isinstance(spending, Mapping) or spending.get("status") != "observed":
        return normal
    frame = spending.get("frame", {})
    if (not isinstance(frame, Mapping)
            or frame.get("actor_character_id") != snapshot.get("played_character", {}).get("character_id")
            or frame.get("native_revision") != snapshot.get("native_revision")
            or frame.get("date_raw") != snapshot.get("date_raw")
            or frame.get("snapshot_id") != snapshot.get("snapshot_id")):
        return normal
    budget = spending.get("budget")
    reserved = budget.get("reserved_raw") if isinstance(budget, Mapping) else None
    if (not isinstance(reserved, Mapping) or type(reserved.get("gold")) is not int
            or reserved["gold"] < 0):
        return normal
    union = priority.get("primary_war_hostile_union_v1", {})
    if (not isinstance(union, Mapping) or type(union.get("observed_current_soldiers")) is not int
            or type(union.get("shared_player_raised_soldiers")) is not int):
        return normal
    major_ids = {row["title"]["title_id"] for row in _armies(current_root.get("held_title_partition"))
                 if isinstance(row.get("title"), Mapping) and type(row["title"].get("title_id")) is int
                 and type(row["title"].get("tier_raw")) is int and row["title"]["tier_raw"] >= 3}
    candidates = []
    for original in _armies(priority.get("wars")):
        war = dict(original)
        live_war = next((row for row in _armies(snapshot.get("active_wars"))
                         if row.get("war_id") == war.get("war_id")), {})
        enemies = {row.get("army_id") for row in _armies(live_war.get("enemy_armies"))}
        deadlines = [{"province_id": row.get("province_id"), "days_left": row["active_siege"]["days_left"]}
                     for row in _armies(live_war.get("objective_province_states"))
                     if row.get("siege_observable") is True and isinstance(row.get("active_siege"), Mapping)
                     and isinstance(row.get("current_besieging_army_selection"), Mapping)
                     and row["current_besieging_army_selection"].get("public_unit_id") in enemies
                     and type(row["active_siege"].get("days_left")) is int and row["active_siege"]["days_left"] >= 0]
        war["observed_risk_deadlines"] = deadlines
        war["observed_risk_deadline_days"] = min((row["days_left"] for row in deadlines), default=None)
        targets = war.get("target_stakes_v1", {}).get("directly_held_target_title_ids") or []
        war["major_direct_title_targeted"] = bool(major_ids.intersection(targets))
        level = priority_emergency_level_v1(war)
        if level:
            candidates.append((level, war))
    if not candidates:
        return normal
    level, war = max(candidates, key=lambda item: (item[0], -item[1]["player_relative_war_score"]))
    return {"level": level, "eligible": True, "war_id": war["war_id"],
            "policy": "major-defence-emergency-funding-candidate-v1",
            "maintenance_window_months": 3 if level == 2 else 6,
            "fixed_gold_floor_raw": 0, "other_reserved_gold_raw": reserved["gold"],
            "source_frame": observed_frame(snapshot), "trigger_evidence": war,
            "global_hostile_scope": union,
            "thresholds_are_policy_not_user_or_native_hard_limits": True,
            "defeat_title_transfer_verified": False, "war_resolution_verified": False}


def valid_saved_emergency_revision_v1(selected, source_frame, snapshot):
    revision = selected.get("emergency_budget_revision_v1")
    if not isinstance(revision, Mapping):
        return None
    binding = revision.get("source_frame")
    if (not isinstance(binding, Mapping) or not isinstance(source_frame, Mapping)
            or type(snapshot.get("native_revision")) is not int
            or binding != source_frame or binding.get("episode_run_id") != snapshot.get("episode_run_id")
            or binding.get("played_character_id") != snapshot.get("played_character", {}).get("character_id")
            or type(binding.get("native_revision")) is not int
            or binding["native_revision"] > snapshot.get("native_revision", -1)
            or type(revision.get("level")) is not int or revision["level"] not in (1, 2, 3)
            or not isinstance(revision.get("epoch_id"), str)
            or not revision["epoch_id"]
            or any(type(revision.get(key)) is not int or revision[key] < 0 for key in
                   ("anchor_treasury_raw", "total_package_limit_raw", "ordinary_reserve_target_raw"))
            or revision["total_package_limit_raw"] > revision["anchor_treasury_raw"]):
        return None
    if revision["level"] == 3:
        crisis = revision.get("crisis_spend_down_v1")
        if (not isinstance(crisis, Mapping)
                or crisis.get("policy") != "major-defence-conditional-count-reversal-spend-down-v1"
                or crisis.get("future_funding_credited_raw") != 0
                or crisis.get("ordinary_military_allocation_retained") is not False
                or crisis.get("future_debt_occurrence_verified") is not False
                or any(type(crisis.get(key)) is not int or crisis[key] < 0 for key in
                       ("current_treasury_raw", "complete_contract_gold_raw", "other_reserved_gold_raw"))
                or crisis["current_treasury_raw"] < crisis["complete_contract_gold_raw"] + crisis["other_reserved_gold_raw"]):
            return None
    return dict(revision)


def emergency_quote_budget_v1(snapshot, *, policy, focus, local, troops, price, contract_months,
                              root, normal_finance, package):
    """A count improvement buys an uncertain reserve, never an attack license."""
    inactive = {"applied": False, "reason": "no_qualified_emergency_marginal_value"}
    if (not policy.get("eligible") or not focus or focus.get("war_id") != policy.get("war_id")
            or normal_finance.get("status") != "available" or package.get("status") == "unavailable"):
        return inactive
    own = local.get("player_current_soldiers") if local.get("status") == "available" else focus.get("observed_player_raised_soldiers")
    enemy = local.get("enemy_current_soldiers") if local.get("status") == "available" else focus.get("observed_enemy_raised_soldiers")
    if (type(own) is not int or type(enemy) is not int or enemy <= own
            or type(troops) is not int or troops <= 0 or troops * 2 < enemy - own):
        return inactive
    finance = observe_reinforcement_finance_v1(snapshot, root, contract_gold_raw=price,
        contract_months=contract_months, gold_floor_raw=policy["fixed_gold_floor_raw"],
        other_reserved_gold_raw=policy["other_reserved_gold_raw"],
        maintenance_reservation_months=policy["maintenance_window_months"])
    if finance.get("status") != "available":
        return inactive
    # A one-time contract can be affordable now even when the current military
    # cash buffer is not retained. Only the strongest existing major-defence
    # crisis may accept that later cash-flow risk, and only for a conditional
    # count reversal. This does not forecast arrival, victory or an actual debt.
    live_war = next((war for war in (snapshot.get("active_wars") or [])
                     if isinstance(war, Mapping) and war.get("war_id") == policy.get("war_id")), {})
    crisis = (policy.get("level") == 2
              and live_war.get("player_is_primary_war_leader") is True
              and live_war.get("player_side") == "defender"
              and live_war.get("player_relative_war_score") == focus.get("player_relative_war_score")
              and finance.get("retains_military_allocation") is False
              and own + troops > enemy
              and normal_finance["observed_treasury_raw"] >= price + policy["other_reserved_gold_raw"])
    spend_down = None
    if crisis:
        spend_down = {"policy": "major-defence-conditional-count-reversal-spend-down-v1",
            "current_treasury_raw": normal_finance["observed_treasury_raw"],
            "complete_contract_gold_raw": price,
            "other_reserved_gold_raw": policy["other_reserved_gold_raw"],
            "ordinary_military_allocation_retained": False,
            "overridden_policy_checks": ["military_cash_allocation", "treasury_share_limit"],
            "conditional_count_reversal_only": True,
            "future_funding_credited_raw": 0, "future_debt_occurrence_verified": False,
            "future_maintenance_debt_risk_accepted": True,
            "loan_principal_or_debt_capacity": None,
            "arrival_eta_days": None, "battle_win_probability": None}
    effective_level = 3 if crisis else policy["level"]
    # Known unrelated unpaid obligations remain protected in every mode.
    required_cash = policy["other_reserved_gold_raw"] if crisis else finance["required_gold_reserve_raw"]
    committed = package.get("committed_contract_quote_gold_raw", 0)
    previous = package.get("emergency_budget_epoch_v1")
    anchor_cash = package.get("original_treasury_raw", normal_finance["observed_treasury_raw"])
    prior_limit = package.get("effective_package_gold_limit_raw", package.get("original_package_gold_limit_raw", 0))
    epoch_id = (previous["epoch_id"] if isinstance(previous, Mapping) else
        str(package.get("anchor_action_request_id") or hashlib.sha256(json.dumps(
            [observed_frame(snapshot), sorted(policy["global_hostile_scope"]["war_ids"])], sort_keys=True).encode()).hexdigest()[:24]))
    previous_level = previous.get("level", 0) if isinstance(previous, Mapping) else 0
    if previous_level >= effective_level:
        # More current cash or another war cannot refresh this level's funding.
        limit = previous["total_package_limit_raw"]
        revision = dict(previous)
        revision["source_frame"] = observed_frame(snapshot)
        revision["reuses_locked_level_limit"] = True
    else:
        if (previous_level and snapshot["native_revision"] <= previous["source_frame"]["native_revision"]):
            return {**inactive, "reason": "higher_emergency_level_requires_new_native_observation"}
        limit = max(prior_limit, min(anchor_cash, committed + max(0,
            finance["observed_treasury_raw"] - required_cash)))
        revision = {"epoch_id": epoch_id, "level": effective_level,
                    "source_frame": observed_frame(snapshot), "anchor_treasury_raw": anchor_cash,
                    "total_package_limit_raw": limit, "prior_total_limit_raw": prior_limit,
                    "ordinary_reserve_target_raw": (previous.get("ordinary_reserve_target_raw")
                        if isinstance(previous, Mapping) else normal_finance["required_gold_reserve_raw"]),
                    "committed_before_quote_raw": committed,
                    "newly_opened_package_gold_raw": max(0, limit - prior_limit),
                    "reuses_locked_level_limit": False,
                    "policy_evidence": policy}
        if crisis:
            revision["crisis_spend_down_v1"] = spend_down
    remaining = max(0, limit - committed)
    return {"applied": True, "finance": finance, "revision": revision,
            "crisis_spend_down_policy_eligible": crisis,
            **({"crisis_spend_down_v1": spend_down} if crisis else {}),
            "remaining_package_gold_raw": remaining, "total_package_limit_raw": limit,
            "conditional_counts": {"player": own, "enemy": enemy, "after_company_arrival": own + troops,
                "deficit_closed_soldiers": min(troops, enemy - own), "local_native_members_available": local.get("status") == "available",
                "scope": "validated local native members" if local.get("status") == "available" else "deduplicated war armies; concentration and joint arrival unverified"},
            "arrival_eta_days": None, "arrival_estimate": "unbought company has no real CUnit route; ETA unknown",
            "cannot_guarantee_arrival_before_loss": True, "battle_win_probability": None}


def observe_emergency_recovery_v1(snapshot, ledger, root):
    revisions = []
    rows = list(ledger.get("observed", []))
    if isinstance(ledger.get("pending"), Mapping):
        rows.append(ledger["pending"])
    for row in rows:
        if row.get("status") == "native_rejected":
            continue
        selected = row.get("decision", {}).get("selected_candidate", {})
        revision = valid_saved_emergency_revision_v1(selected, row.get("source_frame", {}), snapshot)
        if revision:
            revisions.append(revision)
    if not revisions:
        return None
    normal = observe_reinforcement_finance_v1(snapshot, root, contract_gold_raw=0,
        contract_months=18, gold_floor_raw=20000000)
    known = normal.get("status") == "available"
    ready = known and normal["observed_treasury_raw"] >= normal["required_gold_reserve_raw"]
    return {"status": "normal_buffer_restored" if ready else "recovering_emergency_cash_buffer",
            "defer_new_economic_construction": not ready,
            "normal_reserve_target_raw": normal.get("required_gold_reserve_raw"),
            "source_frame": observed_frame(snapshot), "finance_observed": known,
            "latest_emergency_epoch_id": revisions[-1]["epoch_id"],
            "unknown_pending_preserved": ledger.get("pending") is not None,
            "future_income_credited_raw": 0}
