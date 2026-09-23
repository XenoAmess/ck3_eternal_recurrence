"""Same-frame arbitration of already approved, observed M5 proposals.

Each domain keeps ownership of value and legality.  This module compares only
measured shared costs and resource identities, so native legality, skill,
opinion, power, and alliance projections are never converted into invented
cross-domain utility points.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping


_DOMAINS = {"war", "council", "marriage", "diplomacy", "building"}
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
        evidence={**identifiers, "slot_index": slot, "gold_before_raw": before},
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


def select_observed_m5_opportunity(
    *, snapshot: Mapping[str, object], proposals: list[dict[str, object]],
    commitments: Mapping[str, object], gold_reserve_raw: int,
    max_active_wars: int,
) -> dict[str, object]:
    """Choose the least shared-cost feasible domain-approved proposal.

    The comparison order is military commitment, observed gold spend, other
    exclusive identities, then stable candidate ID. It is a transparent
    resource policy; it is not a conversion of domain benefits into utility.
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
    selected = min(eligible, key=_opportunity_key) if eligible else None
    return {
        "policy": "g2-m5-observed-opportunity-selector-v1",
        "frame": frame,
        "status": "selected" if selected is not None else "wait",
        "evaluated": evaluated,
        "selected_candidate_id": (
            selected["candidate_id"] if selected is not None else None
        ),
        "selection_basis": [
            "war_slot_claim", "army_claim_count", "ally_claim_count",
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
) -> dict[str, object]:
    return {
        "schema": "xar.ck3.m5-observed-opportunity.v1",
        "frame": dict(frame), "candidate_id": candidate_id, "domain": domain,
        "source_policy": source_policy, "domain_policy_ready": True,
        "gold_cost_raw": gold_cost_raw,
        "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        "projected_supply_margin_raw": projected_supply_margin_raw,
        "war_slot_claim": war_slot_claim,
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
        if type(supply) is not int or result["war_slot_claim"] != 1:
            raise ValueError("war proposal lacks measured supply and one slot")
    elif supply is not None or result["war_slot_claim"] != 0:
        raise ValueError("non-war proposal cannot claim war supply or a slot")
    for key in _CLAIM_FIELDS:
        result[key] = sorted(_claims(value.get(key), key))
    if value["domain"] == "war" and not result["army_ids"]:
        raise ValueError("war proposal requires observed army claims")
    if value["domain"] == "marriage" and (
        len(result["character_ids"]) < 2 or not result["commitment_keys"]
    ):
        raise ValueError("marriage proposal lacks observed roles or commitment")
    return result


def _opportunity_key(row: Mapping[str, object]) -> tuple[object, ...]:
    supply = row["projected_supply_margin_raw"]
    return (
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
