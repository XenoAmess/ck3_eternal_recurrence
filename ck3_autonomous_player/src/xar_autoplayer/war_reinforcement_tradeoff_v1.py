"""Explain wartime spending priority and a deliberately coarse reinforcement model.

Current counts are not battle power or victory probabilities.  The local staging
model permits a useful hire without inventing a pre-hire Army route or an ETA.
"""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.domain_construction_private_transport_v1 import RESERVE_RAW
from .war_reinforcement_finance_v1 import observe_reinforcement_finance_v1


def _armies(value: object) -> list[Mapping[str, object]]:
    return [row for row in value if isinstance(row, Mapping)] if isinstance(value, list) else []


def _count(rows: list[Mapping[str, object]], *, snapshot: Mapping[str, object],
           role: str, war_id: int | None = None) -> int | None:
    cache_current = (snapshot.get("army_strengths_status") in {"available", "partial"}
                     and snapshot.get("army_strengths_queried_snapshot_id") == snapshot.get("snapshot_id")
                     and snapshot.get("army_strengths_queried_revision") == snapshot.get("revision"))
    strength_rows = _armies(snapshot.get("army_strengths")) if cache_current else []
    counts: dict[int, int] = {}
    for row in rows:
        identity, number = row.get("army_id"), row.get("soldiers")
        matched = [strength for strength in strength_rows
                   if strength.get("army_id") == identity and strength.get("scope_role") == role
                   and (war_id is None or war_id in strength.get("war_ids", []))]
        if len(matched) == 1 and matched[0].get("status") == "available":
            number = matched[0].get("current_soldiers")
        if type(identity) is not int or type(number) is not int or number < 0:
            return None
        if identity in counts and counts[identity] != number:
            return None
        counts[identity] = number
    return sum(counts.values())


def _current_root(snapshot: Mapping[str, object], root: object) -> Mapping[str, object]:
    player = snapshot.get("played_character")
    actor = player.get("character_id") if isinstance(player, Mapping) else None
    return (root if type(actor) is int and actor > 0
            and type(snapshot.get("native_revision")) is int and snapshot["native_revision"] > 0
            and type(snapshot.get("date_raw")) is int
            and isinstance(root, Mapping) and root.get("status") == "available"
            and root.get("player_character_id") == actor
            and root.get("snapshot_revision") == snapshot.get("native_revision")
            and root.get("date_raw") == snapshot.get("date_raw") else {})


def observe_war_spending_priority_v1(
    snapshot: Mapping[str, object], *, campaign_root: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Identify concrete reasons to protect cash before a new economic building.

    A target on a defensive primary war is *exposure*, not proof of its eventual
    transfer. The observed armies exclude unraised troops and unobserved allies.
    """
    own = _armies(snapshot.get("player_armies"))
    own_count = _count(own, snapshot=snapshot, role="player") if isinstance(snapshot.get("player_armies"), list) else None
    all_own_retreating = bool(own) and all(army.get("retreating") is True for army in own)
    active = _armies(snapshot.get("active_wars"))
    primary_wars = [war for war in active if war.get("player_is_primary_war_leader") is True]
    hostile_rows = [army for war in primary_wars for army in _armies(war.get("enemy_armies"))]
    union_complete = all(isinstance(war.get("enemy_armies"), list) for war in primary_wars)
    aggregate_enemy = (_count(hostile_rows, snapshot=snapshot, role="active_war_enemy")
                       if union_complete and primary_wars else None)
    aggregate_deficit = (own_count < aggregate_enemy
                         if own_count is not None and aggregate_enemy is not None else None)
    root = _current_root(snapshot, campaign_root)
    primary_title = root.get("primary_title")
    primary_title = primary_title.get("title_id") if isinstance(primary_title, Mapping) else None
    held = {row["title"]["title_id"] for row in _armies(root.get("held_title_partition"))
            if isinstance(row.get("title"), Mapping) and type(row["title"].get("title_id")) is int}
    wars = []
    for war in active:
        score = war.get("player_relative_war_score")
        primary = war.get("player_is_primary_war_leader") is True
        targets = war.get("targeted_title_ids")
        targets = ([v for v in targets if type(v) is int and v >= 0]
                   if isinstance(targets, list) else [])
        exposed = primary and war.get("player_side") == "defender" and bool(targets)
        hostile_sieges = [army.get("army_id") for army in _armies(war.get("enemy_armies"))
                          if army.get("army_state") == "sieging"
                          and army.get("siege_province_in_player_subrealm") is True]
        objective_states = _armies(war.get("objective_province_states"))
        opponent = war.get("primary_opponent_character_id")
        hostile_occupations = [state.get("province_id") for state in objective_states
                               if state.get("occupation_observable") is True and state.get("is_occupied") is True
                               and type(opponent) is int and opponent > 0
                               and state.get("occupying_character_id") == opponent]
        enemy = (_count(_armies(war.get("enemy_armies")), snapshot=snapshot,
                        role="active_war_enemy", war_id=war.get("war_id"))
                 if isinstance(war.get("enemy_armies"), list) else None)
        deficit = own_count is not None and enemy is not None and own_count < enemy
        operational = None
        if (snapshot.get("army_strengths_queried_snapshot_id") == snapshot.get("snapshot_id")
                and snapshot.get("army_strengths_queried_revision") == snapshot.get("revision")):
            from .strategy import _same_frame_army_strength_balance

            operational = _same_frame_army_strength_balance(dict(snapshot), war.get("war_id"))
        losing = type(score) is int and score < 0
        reasons = []
        if primary and losing and exposed:
            reasons.append("losing_primary_defence_exposes_target_titles")
        if primary and losing and deficit:
            reasons.append("losing_own_war_and_observed_raised_force_outnumbered")
        if primary and losing and len(primary_wars) > 1 and aggregate_deficit is True:
            reasons.append("losing_own_war_and_shared_raised_force_below_unique_primary_hostiles")
        if primary and hostile_sieges:
            reasons.append("observed_hostile_siege_in_player_subrealm")
        if primary and all_own_retreating:
            reasons.append("entire_observed_own_raised_force_currently_retreating")
        if primary and war.get("player_side") == "defender" and hostile_occupations:
            reasons.append("observed_primary_opponent_occupation_of_defensive_objective")
        if primary and type(score) is int and score <= -100:
            reasons.append("score_defeat_threshold_reached_war_still_observed_active")
        wars.append({
            "war_id": war.get("war_id"), "primary_player_war": primary,
            "player_side": war.get("player_side"), "player_relative_war_score": score,
            "possible_defensive_target_title_ids": targets if exposed else [],
            "target_stakes_v1": {
                "current_root_available": bool(root),
                "primary_title_targeted": primary_title in targets if type(primary_title) is int else None,
                "directly_held_target_title_ids": sorted(held.intersection(targets)) if root else None,
                "source": "same-native-frame root title identities; CB defeat transfer remains unverified"},
            "major_direct_title_targeted": any(
                isinstance(row.get("title"), Mapping) and row["title"].get("title_id") in targets
                and type(row["title"].get("tier_raw")) is int and row["title"]["tier_raw"] >= 3
                for row in _armies(root.get("held_title_partition"))),
            "defeat_title_transfer_verified": False,
            "active_war_observed": True, "war_resolution_verified": False,
            "new_procurement_suppressed_by_score_policy": type(score) is int and score <= -100,
            "observed_hostile_siege_in_player_subrealm_army_ids": hostile_sieges,
            "observed_primary_opponent_objective_occupation_province_ids": hostile_occupations,
            "objective_control_projection_available": bool(objective_states),
            "all_observed_own_raised_armies_currently_retreating": all_own_retreating,
            "observed_player_raised_soldiers": own_count,
            "observed_enemy_raised_soldiers": enemy,
            "raised_force_deficit": deficit if own_count is not None and enemy is not None else None,
            "existing_operational_strength_balance_v1": operational,
            "protect_cash_reasons": reasons,
        })
    protected = [war for war in wars if war["protect_cash_reasons"]]
    protected.sort(key=lambda war: (
        war["target_stakes_v1"]["primary_title_targeted"] is not True,
        not bool(war["target_stakes_v1"]["directly_held_target_title_ids"]),
        not bool(war["possible_defensive_target_title_ids"]),
        war["player_relative_war_score"] if type(war["player_relative_war_score"]) is int else 0,
        war["war_id"] if type(war["war_id"]) is int else -1))
    return {
        "schema": "xar.war-spending-priority.v1", "read_only": True,
        "defer_new_economic_construction": any(row["protect_cash_reasons"] for row in wars),
        "wars": wars, "count_scope": "observed raised armies; no unraised reserves or promised allies",
        "cash_protection_priority_war_ids": [war["war_id"] for war in protected],
        "cash_priority_does_not_assign_armies": True,
        "primary_war_hostile_union_v1": {
            "war_ids": [war.get("war_id") for war in primary_wars],
            "unique_army_ids": sorted({row["army_id"] for row in hostile_rows if type(row.get("army_id")) is int}),
            "observed_current_soldiers": aggregate_enemy,
            "shared_player_raised_soldiers": own_count, "shared_force_deficit": aggregate_deficit,
            "future_or_unraised_reinforcements_bounded": False},
        "war_win_probability": None,
    }


def observe_mercenary_purchase_model_need_v1(priority: Mapping[str, object]) -> dict[str, object]:
    """Prune an impossible current headcount-flip purchase, never declare safety.

    Pending hire observations must bypass this optimization. Unknown strengths
    preserve the existing query path; future enemy reserves are not bounded.
    """
    wars = [war for war in _armies(priority.get("wars")) if war.get("protect_cash_reasons")
            and type(war.get("player_relative_war_score")) is int
            and war["player_relative_war_score"] > -100]
    union = priority.get("primary_war_hostile_union_v1")
    union = union if isinstance(union, Mapping) else {}
    unknown = any(war.get("observed_player_raised_soldiers") is None
                  or war.get("observed_enemy_raised_soldiers") is None for war in wars)
    deficit = any(war.get("raised_force_deficit") is True for war in wars)
    shared = len(union.get("war_ids", [])) > 1 and union.get("shared_force_deficit") is not False
    useful = bool(wars) and (unknown or deficit or shared)
    return {"query_can_change_current_headcount_flip_model": useful,
            "reason": "current_deficit_or_unknown_scope" if useful else "no_recoverable_current_headcount_deficit",
            "scope": "only the existing current-headcount-flip purchase model",
            "future_enemy_reinforcements_bounded": False, "overall_war_safe": None,
            "pending_hire_observations_must_bypass": True}


def _stationary_staging(row: Mapping[str, object], province: int) -> bool:
    stationary_route = (row.get("move_target_observable") is True
                        and row.get("move_target_province_id") is None
                        or row.get("route_read_status") == "complete_empty"
                        and row.get("route_source_count") == 0
                        and row.get("army_state") == "regular"
                        or row.get("army_state") == "regular"
                        and row.get("move_target_province_id") is None
                        and row.get("route_province_ids") == [])
    return (row.get("controllable") is True
            and row.get("current_province_id") == province
            and stationary_route
            and row.get("in_combat") is False and row.get("retreating") is False
            and row.get("route_province_ids") == [])


def assess_mercenary_reinforcement_v1(
    snapshot: Mapping[str, object], context: Mapping[str, object], *,
    minimum_gold_reserve_raw: int = RESERVE_RAW,
    campaign_root: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Choose the cheapest legal local reinforcement which reverses a count deficit.

    This counter-policy protects the existing cash floor and a current maximum
    maintenance allocation. It buys a contract, not an immediate battle win.
    """
    if type(minimum_gold_reserve_raw) is not int or minimum_gold_reserve_raw < 0:
        raise ValueError("reinforcement reserve must be a nonnegative raw gold amount")
    priority = observe_war_spending_priority_v1(snapshot, campaign_root=campaign_root)
    player = snapshot.get("played_character")
    actor = player.get("character_id") if isinstance(player, Mapping) else None
    gold = snapshot.get("played_character_gold")
    treasury = (gold.get("raw") if isinstance(gold, Mapping)
                and gold.get("scale") == 100_000 and type(gold.get("raw")) is int else None)
    wars = [row for row in priority["wars"] if row["protect_cash_reasons"]
            and type(row["war_id"]) is int
            and type(row["player_relative_war_score"]) is int
            and row["player_relative_war_score"] > -100]
    assessments = []
    for company in _armies(context.get("rows")):
        terms = company.get("final_terms")
        strength = company.get("troop_strength")
        location = company.get("location")
        terms = terms if isinstance(terms, Mapping) else {}
        strength = strength if isinstance(strength, Mapping) else {}
        location = location if isinstance(location, Mapping) else {}
        costs = terms.get("resource_costs_raw")
        price = costs[0] if isinstance(costs, list) and len(costs) == 10 else None
        finance = observe_reinforcement_finance_v1(
            snapshot, campaign_root, contract_gold_raw=price,
            contract_months=terms.get("hire_duration_months"), gold_floor_raw=minimum_gold_reserve_raw,
        )
        troops = strength.get("current_soldiers")
        spawn = location.get("hire_auto_raise_province_id")
        ready = company.get("readiness_v1")
        reasons = []
        if not isinstance(ready, Mapping) or ready.get("hire_ready") is not True:
            reasons.append("native_composition_or_hire_terms_not_ready")
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
        if context.get("available") is not True:
            reasons.append("native_company_collection_unavailable")
        staging = [row for row in _armies(snapshot.get("player_armies"))
                   if _stationary_staging(row, spawn)] if type(spawn) is int else []
        local = _count(staging, snapshot=snapshot, role="player") if staging else None
        if local is None:
            reasons.append("spawn_is_not_a_current_stationary_friendly_staging_province")
        union = priority["primary_war_hostile_union_v1"]
        multi = len(union["war_ids"]) > 1
        union_enemy = union["observed_current_soldiers"]
        if multi and union_enemy is None:
            reasons.append("multi_war_hostile_union_unknown_no_shared_force_allocation")
        flips = [war["war_id"] for war in wars
                 if type(enemy_count := union_enemy if multi else war["observed_enemy_raised_soldiers"]) is int
                 and local is not None and type(troops) is int
                  and local < enemy_count < local + troops]
        if not flips:
            reasons.append("does_not_reverse_an_observed_own_war_headcount_deficit")
        assessments.append({
            "company_id": company.get("company_id"), "gold_cost_raw": price,
            "gold_after_hire_raw": treasury - price if treasury is not None and type(price) is int else None,
            "company_current_soldiers": troops, "friendly_staging_soldiers": local,
            "reinforced_staging_soldiers": local + troops if local is not None and type(troops) is int else None,
            "predicted_auto_raise_province_id": spawn,
            "staging_army_ids": sorted({row["army_id"] for row in staging}),
            "numerical_balance_reversed_war_ids": flips, "rejection_reasons": reasons,
            "multiple_primary_wars_share_force": multi,
            "comparison_enemy_current_soldiers": union_enemy if multi else None,
            "finance": finance,
        })
    eligible = [row for row in assessments if not row["rejection_reasons"]]
    chosen = min(eligible, key=lambda row: (row["gold_cost_raw"], row["company_id"])) if eligible else None
    return {
        "schema": "xar.mercenary-reinforcement-tradeoff.v1", "actor_character_id": actor,
        "war_spending_priority": priority, "candidates": assessments,
        "selected_company_id": chosen["company_id"] if chosen else None,
        "selected_candidate": chosen, "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        "recommendation": "hire_local_reinforcement" if chosen else "continue_existing_war_action",
        "arrival_model": "inference: native predicted spawn equals current stationary friendly staging province",
        "arrival_eta_days": None, "battle_win_probability": None,
        "model_limits": ["headcount is not combat power", "no rescue credit for a current battle",
                         "no pre-hire route or guaranteed arrival time", "current military allocation is not a future cost bound"],
        "postcondition_verified": False,
    }
