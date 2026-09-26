"""Same-frame arbitration of already approved, observed M5 proposals.

Each domain keeps ownership of value and legality.  This module compares only
measured shared costs and resource identities, so native legality, skill,
opinion, power, and alliance projections are never converted into invented
cross-domain utility points.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping


_DOMAINS = {
    "war", "council", "marriage", "diplomacy", "building", "lifestyle",
}
_CLAIM_FIELDS = (
    "army_ids", "ally_character_ids", "character_ids", "commitment_keys",
)
_FRAME_FIELDS = (
    "played_character_id", "native_revision", "date_raw", "snapshot_id",
    "revision", "episode_run_id",
)


def observed_frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Return the full identity used by every proposal and commitment read."""
    player = snapshot.get("played_character_id")
    if player is None and isinstance(snapshot.get("played_character"), Mapping):
        player = snapshot["played_character"].get("character_id")
    values = {
        "played_character_id": player,
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "episode_run_id": snapshot.get("episode_run_id"),
    }
    if (
        type(values["played_character_id"]) is not int
        or values["played_character_id"] <= 0
        or type(values["native_revision"]) is not int
        or values["native_revision"] <= 0
        or type(values["date_raw"]) is not int
        or values["date_raw"] < 0
        or type(values["snapshot_id"]) is not str
        or not values["snapshot_id"]
        or type(values["revision"]) is not int
        or values["revision"] <= 0
        or type(values["episode_run_id"]) is not str
        or not values["episode_run_id"]
    ):
        raise ValueError("M5 observed frame identity is incomplete")
    return values


def council_steward_proposal(
    *, frame: Mapping[str, object], observation: Mapping[str, object],
    decision: Mapping[str, object],
) -> dict[str, object]:
    """Adapt the existing steward policy's action-ready decision."""
    if (
        decision.get("policy") != "council-composition-steward-v1"
        or decision.get("outcome") not in {"ASSIGN_REQUIRED", "REPLACE_REQUIRED"}
        or decision.get("action_routable") is not True
        or decision.get("required_capability")
        != "game.action.assign-councillor-v1"
    ):
        raise ValueError("action-ready steward decision required")
    snapshot = observation.get("snapshot")
    position = observation.get("position")
    candidates = observation.get("candidates")
    if (
        not isinstance(snapshot, Mapping)
        or snapshot.get("snapshot_id") != frame.get("snapshot_id")
        or snapshot.get("public_revision") != frame.get("revision")
        or snapshot.get("native_revision") != frame.get("native_revision")
        or snapshot.get("date_raw") != frame.get("date_raw")
        or snapshot.get("paused") is not True
        or observation.get("owner_character_id") != frame.get("played_character_id")
        or not isinstance(position, Mapping)
        or not isinstance(candidates, list)
        or observation.get("candidate_collection_complete") is not True
    ):
        raise ValueError("same-frame steward observation required")
    selected = decision.get("selected_candidate")
    skill = selected.get("main_skill") if isinstance(selected, Mapping) else None
    character_id = selected.get("character_id") if isinstance(selected, Mapping) else None
    if (
        type(character_id) is not int or character_id <= 0
        or not isinstance(skill, Mapping)
        or skill.get("key") != "stewardship"
        or type(skill.get("value")) is not int or skill["value"] < 0
    ):
        raise ValueError("steward decision lacks its observed candidate")
    matched = [row for row in candidates if isinstance(row, Mapping)
               and row.get("character_id") == character_id]
    if len(matched) != 1 or matched[0].get("main_skill") != skill:
        raise ValueError("steward choice is not in the same-frame observation")
    incumbent = decision.get("incumbent_character_id")
    incumbent_skill = decision.get("incumbent_main_skill")
    if (
        position.get("incumbent_character_id") != incumbent
        or position.get("incumbent_main_skill") != incumbent_skill
    ):
        raise ValueError("steward incumbent crossed the observed frame")
    if decision["outcome"] == "REPLACE_REQUIRED":
        if (
            type(incumbent) is not int or incumbent <= 0
            or not isinstance(incumbent_skill, Mapping)
            or type(incumbent_skill.get("value")) is not int
            or skill["value"] <= incumbent_skill["value"]
        ):
            raise ValueError("replacement lacks an observed stewardship gain")
    return _proposal(
        frame=frame, candidate_id=f"council:steward:{character_id}",
        domain="council", source_policy=str(decision["policy"]),
        gold_cost_raw=0, minimum_gold_reserve_raw=0,
        projected_supply_margin_raw=None, war_slot_claim=0,
        army_ids=[], ally_character_ids=[], character_ids=[character_id],
        commitment_keys=["council-seat:councillor_steward"],
        evidence={
            "outcome": decision["outcome"],
            "candidate_stewardship": skill["value"],
            "incumbent_stewardship": (
                incumbent_skill.get("value")
                if isinstance(incumbent_skill, Mapping) else None
            ),
        },
    )


def construction_proposal(
    *, frame: Mapping[str, object], query: Mapping[str, object],
) -> dict[str, object]:
    """Adapt one existing native-legal, cost-observed building choice."""
    candidate = query.get("candidate")
    source = query.get("source_frame")
    if query.get("status") != "selected" or not isinstance(candidate, Mapping):
        raise ValueError("selected construction query required")
    _same_frame(source, frame, actor_key="actor_character_id")
    identifiers = {}
    for key in ("barony_title_id", "province_id", "building_type_id"):
        value = candidate.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"construction {key} is not observed")
        identifiers[key] = value
    slot = candidate.get("slot_index")
    gold = candidate.get("stock_gold_cost_raw")
    before = candidate.get("gold_before_raw")
    if (
        type(slot) is not int or slot < 0 or type(gold) is not int or gold <= 0
        or type(before) is not int or before < gold
    ):
        raise ValueError("construction cost or slot is not observed")
    # Reuse the formal construction route's reserve instead of allowing an
    # M5 caller to invent or weaken a second budget.
    from .bridge.domain_construction_private_transport_v1 import RESERVE_RAW

    return _proposal(
        frame=frame,
        candidate_id=(f"building:{identifiers['barony_title_id']}:"
                      f"{identifiers['building_type_id']}:{slot}"),
        domain="building", source_policy="private-native-budgeted-construction-v1",
        gold_cost_raw=gold,
        minimum_gold_reserve_raw=RESERVE_RAW,
        projected_supply_margin_raw=None, war_slot_claim=0,
        army_ids=[], ally_character_ids=[], character_ids=[],
        commitment_keys=[f"building-slot:{identifiers['barony_title_id']}:{slot}"],
        evidence={**identifiers, "slot_index": slot, "gold_before_raw": before,
                  "authored_monthly_income_hundredths": candidate.get(
                      "authored_monthly_income_hundredths")},
    )


def faction_gift_proposal(
    *, frame: Mapping[str, object], candidate: Mapping[str, object],
) -> dict[str, object]:
    """Adapt the existing native preview plus budget-approved faction gift."""
    choice = candidate.get("choice")
    if candidate.get("status") != "selected" or not isinstance(choice, Mapping):
        raise ValueError("selected faction-gift candidate required")
    if (
        choice.get("snapshot_revision") != frame.get("native_revision")
        or choice.get("native_snapshot_revision") != frame.get("native_revision")
        or choice.get("date_raw") != frame.get("date_raw")
        or choice.get("player_character_id") != frame.get("played_character_id")
    ):
        raise ValueError("faction-gift candidate crossed the observed frame")
    source = choice.get("source_faction_id")
    recipient = choice.get("recipient_character_id")
    gold = choice.get("gold_cost_raw")
    reserve = choice.get("minimum_gold_reserve_raw")
    opinion = choice.get("opinion_delta")
    if (
        type(source) is not int or source <= 0
        or type(recipient) is not int or recipient <= 0
        or type(gold) is not int or gold <= 0
        or type(reserve) is not int or reserve < 0
        or type(opinion) is not int or opinion <= 0
    ):
        raise ValueError("faction-gift material inputs are incomplete")
    return _proposal(
        frame=frame, candidate_id=f"diplomacy:faction-gift:{source}:{recipient}",
        domain="diplomacy", source_policy="faction-gift-v1",
        gold_cost_raw=gold, minimum_gold_reserve_raw=reserve,
        projected_supply_margin_raw=None, war_slot_claim=0,
        army_ids=[], ally_character_ids=[], character_ids=[recipient],
        commitment_keys=[f"faction-gift:{source}:{recipient}"],
        evidence={"source_faction_id": source, "opinion_delta": opinion},
    )


def active_defensive_war_continuation_proposal(
    *, frame: Mapping[str, object], snapshot: Mapping[str, object],
    plan: Mapping[str, object], observation: Mapping[str, object],
) -> dict[str, object]:
    """Adapt one observed primary-defender continuation resource slice.

    The war policy still owns route, exit and action legality.  This adapter
    only admits its current resource identities after a separate same-frame
    observation publishes the incremental budget and projected supply margin.
    """
    if (
        plan.get("policy") != "one-life-turn-v1"
        or type(plan.get("war_id")) is not int
        or plan["war_id"] <= 0
        or type(plan.get("selected_step")) is not str
        or not plan["selected_step"]
        or observation.get("status") != "available"
        or observation.get("read_only") is not True
    ):
        raise ValueError("observed defensive-war continuation is required")
    _same_frame(observation.get("source_frame"), frame,
                actor_key="played_character_id")
    if observed_frame(snapshot) != dict(frame):
        raise ValueError("defensive-war continuation crossed the observed frame")
    war_id = plan["war_id"]
    if observation.get("war_id") != war_id:
        raise ValueError("defensive-war continuation WarID changed")
    snapshot_wars = snapshot.get("active_wars")
    plan_wars = plan.get("active_wars")
    if not isinstance(snapshot_wars, list) or not isinstance(plan_wars, list):
        raise ValueError("defensive-war continuation lacks active wars")
    current = [row for row in snapshot_wars if isinstance(row, Mapping)
               and row.get("war_id") == war_id]
    planned = [row for row in plan_wars if isinstance(row, Mapping)
               and row.get("war_id") == war_id]
    if (
        len(current) != 1 or len(planned) != 1
        or current[0].get("player_side") != "defender"
        or current[0].get("player_is_primary_war_leader") is not True
        or planned[0].get("player_side") != "defender"
        or planned[0].get("player_is_primary_war_leader") is not True
    ):
        raise ValueError("primary-defender active-war identity is not observed")
    armies = _positive_ids(observation.get("army_ids"), "continuation.army_ids")
    allies = _positive_ids(
        observation.get("ally_character_ids"),
        "continuation.ally_character_ids",
    )
    characters = _positive_ids(
        observation.get("character_ids"), "continuation.character_ids",
    )
    if not armies:
        raise ValueError("defensive-war continuation lacks an observed army")
    public_armies = snapshot.get("player_armies")
    bindings = observation.get("army_war_bindings")
    if not isinstance(public_armies, list) or not isinstance(bindings, list):
        raise ValueError("defensive-war continuation army scope is unavailable")
    controllable = {
        row.get("army_id") for row in public_armies
        if isinstance(row, Mapping) and row.get("controllable") is True
    }
    bound_to_war = {
        row.get("army_id") for row in bindings
        if isinstance(row, Mapping) and row.get("war_id") == war_id
    }
    if len(bindings) != len(armies) or any(
        not isinstance(row, Mapping)
        or row.get("war_id") != war_id
        or row.get("army_id") not in armies for row in bindings
    ):
        raise ValueError("defensive-war continuation army binding is incomplete")
    if not set(armies) <= controllable or not set(armies) <= bound_to_war:
        raise ValueError("defensive-war continuation army is not controllable and bound")
    supply = observation.get("projected_supply_margin_raw")
    if type(supply) is not int:
        raise ValueError("defensive-war continuation lacks measured supply")
    gold = _nonnegative(
        observation.get("incremental_gold_cost_raw"),
        "continuation.incremental_gold_cost_raw",
    )
    reserve = _nonnegative(
        observation.get("minimum_gold_reserve_raw"),
        "continuation.minimum_gold_reserve_raw",
    )
    return _proposal(
        frame=frame, candidate_id=f"war:continue:defender:{war_id}",
        domain="war", source_policy=str(plan["policy"]),
        gold_cost_raw=gold, minimum_gold_reserve_raw=reserve,
        projected_supply_margin_raw=supply, war_slot_claim=0,
        army_ids=armies, ally_character_ids=allies,
        character_ids=characters,
        commitment_keys=[
            f"active-war:{war_id}",
            *(f"active-war-army:{war_id}:{army_id}" for army_id in armies),
        ],
        evidence={
            "war_id": war_id, "player_side": "defender",
            "player_is_primary_war_leader": True,
            "phase": plan.get("phase"), "selected_step": plan["selected_step"],
            "active_war_slot_already_occupied": True,
        },
        war_operation="active_defensive_continuation",
    )


def wartime_lifestyle_perk_proposal(
    *, frame: Mapping[str, object], query: Mapping[str, object],
    decision: Mapping[str, object], current_war_plan: Mapping[str, object],
) -> dict[str, object]:
    """Adapt one native-final-legal perk while war has no gameplay step."""
    selected_war_step = current_war_plan.get("selected_step")
    if not (
        current_war_plan.get("policy") == "one-life-turn-v1"
        and (
            selected_war_step is None
            or (isinstance(selected_war_step, str)
                and selected_war_step.startswith("query-"))
        )
    ):
        raise ValueError("formal war gameplay step has priority over lifestyle")
    source = query.get("source_frame")
    if not isinstance(source, Mapping):
        raise ValueError("wartime perk source frame is absent")
    _same_frame(
        {**source, "episode_run_id": query.get("episode_run_id")},
        frame, actor_key="player_character_id",
    )
    life = query.get("snapshot")
    action = decision.get("selected_action")
    if (
        query.get("status") != "available"
        or query.get("formal_precondition_status") != "ready"
        or not isinstance(life, Mapping)
        or decision.get("policy_id")
        != "g2-lifestyle-wartime-stewardship-perk-v1"
        or decision.get("status") != "recommend_action"
        or not isinstance(action, Mapping)
        or action.get("kind") != "perk"
    ):
        raise ValueError("native-final-legal wartime perk is required")
    expected = action.get("expected")
    if not isinstance(expected, Mapping) or any((
        expected.get("expected_snapshot_id") != frame.get("snapshot_id"),
        expected.get("expected_episode_run_id") != frame.get("episode_run_id"),
        expected.get("expected_native_revision") != frame.get("native_revision"),
        expected.get("expected_public_revision") != frame.get("native_revision"),
        expected.get("expected_date_raw") != frame.get("date_raw"),
        expected.get("expected_player_character_id")
        != frame.get("played_character_id"),
    )):
        raise ValueError("wartime perk decision crossed the observed frame")
    readiness = life.get("readiness")
    focus = life.get("current_focus")
    progress = life.get("current_lifestyle_progress")
    legal = life.get("legal_perk_candidates")
    owned = life.get("owned_perk_keys")
    target = action.get("target_key")
    lifestyle = action.get("target_lifestyle_key")
    legal_items = legal.get("items") if isinstance(legal, Mapping) else None
    if (
        life.get("snapshot_id") != frame.get("snapshot_id")
        or life.get("episode_run_id") != frame.get("episode_run_id")
        or life.get("public_revision") != frame.get("native_revision")
        or life.get("native_revision") != frame.get("native_revision")
        or life.get("date_raw") != frame.get("date_raw")
        or life.get("player_character_id") != frame.get("played_character_id")
        or target != "cutting_corners_perk"
        or lifestyle != "stewardship_lifestyle"
        or not isinstance(readiness, Mapping)
        or any(readiness.get(key) is not True for key in (
            "current_focus_ready", "lifestyle_progress_ready",
            "owned_perks_ready", "legal_perk_candidates_ready",
            "same_frame_ready",
        ))
        or not isinstance(focus, Mapping)
        or focus.get("presence") != "present"
        or focus.get("lifestyle_key") != lifestyle
        or type(focus.get("key")) is not str or not focus["key"]
        or not isinstance(progress, Mapping)
        or progress.get("presence") != "present"
        or progress.get("lifestyle_key") != lifestyle
        or type(progress.get("unspent_perk_points")) is not int
        or progress["unspent_perk_points"] <= 0
        or type(progress.get("used_perk_points")) is not int
        or progress["used_perk_points"] < 0
        or not isinstance(owned, list)
        or any(type(key) is not str or not key for key in owned)
        or target in owned
        or not isinstance(legal_items, list)
        or sum(
            isinstance(row, Mapping) and row.get("key") == target
            and row.get("lifestyle_key") == lifestyle for row in legal_items
        ) != 1
    ):
        raise ValueError("wartime perk point or final legality is unobserved")
    return _proposal(
        frame=frame, candidate_id=f"lifestyle:perk:{target}",
        domain="lifestyle", source_policy=str(decision["policy_id"]),
        gold_cost_raw=0, minimum_gold_reserve_raw=0,
        projected_supply_margin_raw=None, war_slot_claim=0,
        army_ids=[], ally_character_ids=[], character_ids=[],
        commitment_keys=[f"lifestyle-perk-point:{lifestyle}"],
        evidence={
            "current_focus_key": focus.get("key"),
            "target_lifestyle_key": lifestyle, "target_perk_key": target,
            "unspent_perk_points": progress["unspent_perk_points"],
            "used_perk_points": progress["used_perk_points"],
            "date_advance_expected": False,
            "war_plan_selected_step": selected_war_step,
        },
    )


def select_observed_m5_opportunity(
    *, snapshot: Mapping[str, object], proposals: list[dict[str, object]],
    commitments: Mapping[str, object], gold_reserve_raw: int,
    max_active_wars: int,
) -> dict[str, object]:
    """Choose one feasible domain-approved proposal with observed benefit first.

    In the bounded peaceful building/gift comparison, a positive authored
    building income takes precedence over an unpriced gift. Other domains and
    remaining ties use measured shared costs.
    Authored income is a script value, not realized tax or cross-domain utility.
    """
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("M5 observed selector requires a paused map frame")
    frame = observed_frame(snapshot)
    gold = snapshot.get("played_character_gold")
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    if (
        not isinstance(gold, Mapping) or type(gold.get("raw")) is not int
        or gold.get("scale") != 100_000 or not isinstance(wars, list)
        or any(not isinstance(row, Mapping) or type(row.get("war_id")) is not int
               for row in wars)
        or not isinstance(armies, list)
        or any(not isinstance(row, Mapping) or type(row.get("army_id")) is not int
               or type(row.get("controllable")) is not bool for row in armies)
    ):
        raise ValueError("same-frame gold, wars and armies are required")
    if type(gold_reserve_raw) is not int or gold_reserve_raw < 0:
        raise ValueError("gold_reserve_raw must be observed policy input")
    if type(max_active_wars) is not int or max_active_wars < 0:
        raise ValueError("max_active_wars must be observed policy input")
    if not isinstance(commitments, Mapping) or commitments.get("frame") != frame:
        raise ValueError("same-frame observed commitments are required")
    reserved_gold = _nonnegative(commitments.get("gold_raw"), "commitments.gold_raw")
    pending_wars = _nonnegative(
        commitments.get("pending_war_slots"), "commitments.pending_war_slots")
    occupied = {key: _claims(commitments.get(key), key) for key in _CLAIM_FIELDS}
    usable_armies = {
        row["army_id"] for row in armies if row["controllable"] is True
    }
    if not isinstance(proposals, list):
        raise ValueError("observed proposals must be a list")
    seen: set[str] = set()
    evaluated: list[dict[str, object]] = []
    for raw in proposals:
        proposal = _normalize_proposal(raw, frame)
        candidate_id = proposal["candidate_id"]
        if candidate_id in seen:
            raise ValueError("observed proposal identity is duplicated")
        seen.add(candidate_id)
        claims = {key: set(proposal[key]) for key in _CLAIM_FIELDS}
        reason = "eligible"
        reserve = max(gold_reserve_raw, proposal["minimum_gold_reserve_raw"])
        if proposal["gold_cost_raw"] + reserved_gold + reserve > gold["raw"]:
            reason = "shared_gold_budget"
        elif claims["army_ids"] - usable_armies:
            reason = "army_not_controllable"
        elif any(claims[key] & occupied[key] for key in _CLAIM_FIELDS):
            reason = "existing_commitment_conflict"
        elif (
            proposal["war_slot_claim"] > 0
            and len(wars) + pending_wars + proposal["war_slot_claim"]
            > max_active_wars
        ):
            reason = "war_slot_budget"
        elif (
            proposal["domain"] == "war"
            and proposal["projected_supply_margin_raw"] < 0
        ):
            reason = "projected_supply_deficit"
        evaluated.append({**proposal, "reason": reason})
    eligible = [row for row in evaluated if row["reason"] == "eligible"]
    prefer_income = (
        not wars and not armies
        and all(row["domain"] in {"building", "diplomacy"} for row in evaluated)
    )
    selected = (min(eligible, key=lambda row: _opportunity_key(
        row, prefer_income=prefer_income)) if eligible else None)
    return {
        "policy": "g2-m5-observed-opportunity-selector-v1",
        "frame": frame,
        "status": "selected" if selected is not None else "wait",
        "evaluated": evaluated,
        "selected_candidate_id": (
            selected["candidate_id"] if selected is not None else None
        ),
        "selection_basis": [
            "positive_authored_building_income_in_peace", "war_slot_claim",
            "army_claim_count", "ally_claim_count",
            "gold_cost_raw", "commitment_key_count", "character_claim_count",
            "projected_supply_margin_raw_desc", "candidate_id",
        ],
        "selected_step": None,
        "formal_action_ready": False,
    }


def _proposal(
    *, frame: Mapping[str, object], candidate_id: str, domain: str,
    source_policy: str, gold_cost_raw: int, minimum_gold_reserve_raw: int,
    projected_supply_margin_raw: int | None, war_slot_claim: int,
    army_ids: list[int], ally_character_ids: list[int],
    character_ids: list[int], commitment_keys: list[str],
    evidence: Mapping[str, object],
    war_operation: str | None = None,
) -> dict[str, object]:
    return {
        "schema": "xar.ck3.m5-observed-opportunity.v1",
        "frame": dict(frame), "candidate_id": candidate_id, "domain": domain,
        "source_policy": source_policy, "domain_policy_ready": True,
        "gold_cost_raw": gold_cost_raw,
        "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        "projected_supply_margin_raw": projected_supply_margin_raw,
        "war_slot_claim": war_slot_claim,
        "war_operation": war_operation,
        "army_ids": army_ids, "ally_character_ids": ally_character_ids,
        "character_ids": character_ids, "commitment_keys": commitment_keys,
        "evidence": deepcopy(dict(evidence)),
    }


def _same_frame(
    value: object, frame: Mapping[str, object], *, actor_key: str,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("proposal source frame is absent")
    for key in ("native_revision", "date_raw", "snapshot_id", "revision",
                "episode_run_id"):
        if value.get(key) != frame.get(key):
            raise ValueError("proposal crossed the observed frame")
    if value.get(actor_key) != frame.get("played_character_id"):
        raise ValueError("proposal actor crossed the observed frame")


def _normalize_proposal(
    value: object, frame: Mapping[str, object],
) -> dict[str, object]:
    if (
        not isinstance(value, Mapping)
        or value.get("schema") != "xar.ck3.m5-observed-opportunity.v1"
        or value.get("frame") != frame
        or value.get("domain") not in _DOMAINS
        or value.get("domain_policy_ready") is not True
        or type(value.get("candidate_id")) is not str or not value["candidate_id"]
        or type(value.get("source_policy")) is not str or not value["source_policy"]
    ):
        raise ValueError("domain-approved same-frame proposal required")
    result = deepcopy(dict(value))
    result["gold_cost_raw"] = _nonnegative(value.get("gold_cost_raw"), "gold_cost_raw")
    result["minimum_gold_reserve_raw"] = _nonnegative(
        value.get("minimum_gold_reserve_raw"), "minimum_gold_reserve_raw")
    result["war_slot_claim"] = _nonnegative(
        value.get("war_slot_claim"), "war_slot_claim")
    if result["war_slot_claim"] not in {0, 1}:
        raise ValueError("war_slot_claim must be zero or one")
    supply = value.get("projected_supply_margin_raw")
    if value["domain"] == "war":
        operation = value.get("war_operation")
        if operation is None and result["war_slot_claim"] == 1:
            operation = "entry"
        if type(supply) is not int:
            raise ValueError("war proposal lacks measured supply")
        if operation == "entry" and result["war_slot_claim"] != 1:
            raise ValueError("war entry proposal must claim one slot")
        if (
            operation == "active_defensive_continuation"
            and result["war_slot_claim"] != 0
        ):
            raise ValueError("active war continuation cannot claim a new slot")
        if operation not in {"entry", "active_defensive_continuation"}:
            raise ValueError("war proposal operation is unsupported")
        result["war_operation"] = operation
    elif supply is not None or result["war_slot_claim"] != 0:
        raise ValueError("non-war proposal cannot claim war supply or a slot")
    elif value.get("war_operation") is not None:
        raise ValueError("non-war proposal cannot set a war operation")
    for key in _CLAIM_FIELDS:
        result[key] = sorted(_claims(value.get(key), key))
    if value["domain"] == "war" and not result["army_ids"]:
        raise ValueError("war proposal requires observed army claims")
    if value["domain"] == "marriage" and (
        len(result["character_ids"]) < 2 or not result["commitment_keys"]
    ):
        raise ValueError("marriage proposal lacks observed roles or commitment")
    if value["domain"] == "lifestyle" and (
        result["army_ids"] or result["ally_character_ids"]
        or result["character_ids"]
        or len(result["commitment_keys"]) != 1
        or not result["commitment_keys"][0].startswith("lifestyle-perk-point:")
    ):
        raise ValueError("lifestyle proposal lacks one observed perk point")
    return result


def _opportunity_key(
    row: Mapping[str, object], *, prefer_income: bool,
) -> tuple[object, ...]:
    supply = row["projected_supply_margin_raw"]
    evidence = row["evidence"]
    income = (evidence.get("authored_monthly_income_hundredths")
              if row["domain"] == "building" else None)
    return (
        0 if prefer_income and type(income) is int and income > 0 else 1,
        row["war_slot_claim"], len(row["army_ids"]),
        len(row["ally_character_ids"]), row["gold_cost_raw"],
        len(row["commitment_keys"]), len(row["character_ids"]),
        -(supply if type(supply) is int else 0), row["candidate_id"],
    )


def _nonnegative(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _claims(value: object, name: str) -> set[int] | set[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    kind = str if name == "commitment_keys" else int
    if any(type(item) is not kind or (not item if kind is str else item <= 0)
           for item in value):
        raise ValueError(f"{name} contains an invalid resource identity")
    result = set(value)
    if len(result) != len(value):
        raise ValueError(f"{name} contains duplicate resource identities")
    return result


def _positive_ids(value: object, name: str) -> list[int]:
    result = _claims(value, name)
    if any(type(item) is not int for item in result):
        raise ValueError(f"{name} must contain positive integer identities")
    return sorted(result)
