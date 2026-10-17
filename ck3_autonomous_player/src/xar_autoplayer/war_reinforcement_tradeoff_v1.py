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


def observe_war_spending_priority_v1(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Identify concrete reasons to protect cash before a new economic building.

    A target on a defensive primary war is *exposure*, not proof of its eventual
    transfer. The observed armies exclude unraised troops and unobserved allies.
    """
    own = _armies(snapshot.get("player_armies"))
    own_count = _count(own, snapshot=snapshot, role="player") if isinstance(snapshot.get("player_armies"), list) else None
    wars = []
    for war in _armies(snapshot.get("active_wars")):
        score = war.get("player_relative_war_score")
        primary = war.get("player_is_primary_war_leader") is True
        targets = war.get("targeted_title_ids")
        targets = ([v for v in targets if type(v) is int and v >= 0]
                   if isinstance(targets, list) else [])
        exposed = primary and war.get("player_side") == "defender" and bool(targets)
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
        if primary and type(score) is int and score <= -100:
            reasons.append("native_score_already_terminal_defeat")
        wars.append({
            "war_id": war.get("war_id"), "primary_player_war": primary,
            "player_side": war.get("player_side"), "player_relative_war_score": score,
            "possible_defensive_target_title_ids": targets if exposed else [],
            "defeat_title_transfer_verified": False,
            "observed_player_raised_soldiers": own_count,
            "observed_enemy_raised_soldiers": enemy,
            "raised_force_deficit": deficit if own_count is not None and enemy is not None else None,
            "existing_operational_strength_balance_v1": operational,
            "protect_cash_reasons": reasons,
        })
    return {
        "schema": "xar.war-spending-priority.v1", "read_only": True,
        "defer_new_economic_construction": any(row["protect_cash_reasons"] for row in wars),
        "wars": wars, "count_scope": "observed raised armies; no unraised reserves or promised allies",
        "war_win_probability": None,
    }


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
    priority = observe_war_spending_priority_v1(snapshot)
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
        flips = [war["war_id"] for war in wars
                 if type(war["observed_enemy_raised_soldiers"]) is int
                 and local is not None and type(troops) is int
                 and local < war["observed_enemy_raised_soldiers"] < local + troops]
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
