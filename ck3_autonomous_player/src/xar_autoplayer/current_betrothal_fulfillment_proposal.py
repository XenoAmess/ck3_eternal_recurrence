"""Private observed resource inputs for fulfilling the current heir's betrothal.

Native legality and the zero-cost admission policy belong to the owning formal
consumer. This builder preserves that decision and the fixed pair's readback;
it does not enumerate candidates, price an alliance or reserve any resource.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .m5_observed_opportunity_selector import _proposal, observed_frame


MODE = "fulfill_existing_betrothal"
SUBMIT_STEP = "submit-current-first-heir-betrothal-fulfillment-v1-private"
SCHEMA = "xar.ck3.current-betrothal-fulfillment-resource-proposal.v1"
_ROLE_FIELDS = (
    "actor_character_id", "heir_character_id", "partner_character_id",
    "recipient_character_id", "intermediary_character_id",
)
_COST_FIELDS = (
    "gold_raw", "prestige_raw", "piety_raw", "renown_raw", "influence_raw",
    "herd_raw", "treasury_raw", "treasury_or_gold_raw", "merit_raw",
    "barter_goods_raw",
)


def build_current_betrothal_fulfillment_proposal(
    relation: Mapping[str, object], snapshot: Mapping[str, object], *,
    selected: bool, reasons: list[str],
) -> dict[str, object]:
    """Retain the owning policy's choice and the actual fixed-pair inputs."""
    frame = observed_frame(snapshot)
    value = relation.get("betrothal_actionability")
    value = value if isinstance(value, Mapping) else {}
    roles = {key: value.get(key) for key in _ROLE_FIELDS}
    roles["actor_character_id"] = frame["played_character_id"]
    roles["heir_character_id"] = relation.get("heir_character_id")
    roles["partner_character_id"] = relation.get("betrothed_character_id")
    claims = sorted({item for item in roles.values()
                     if type(item) is int and item > 0})
    heir = roles["heir_character_id"]
    partner = roles["partner_character_id"]
    costs = value.get("generic_costs")
    return {
        "schema": SCHEMA, "mode": MODE, "typed_step": SUBMIT_STEP,
        "source_frame": frame, "source_native_revision": relation.get("native_revision"),
        "selected": selected, "formal_action_ready": selected,
        "reasons": list(reasons), **roles,
        "character_claims": claims,
        "immediate_generic_costs": (
            deepcopy(dict(costs)) if isinstance(costs, Mapping) else None
        ),
        "existing_commitment": {
            "source": "native_bilateral_betrothal",
            "bilateral_verified": relation.get("bilateral_verified"),
            "heir_character_id": heir, "partner_character_id": partner,
            "commitment_key": (
                f"first-heir-marriage:{heir}" if type(heir) is int else None
            ),
            "mode": MODE, "new_betrothal_commitment": False,
        },
        "benefit": (
            "complete_existing_adult_betrothal"
            if value.get("ready_to_marry_betrothed") is True else None
        ),
        "predicted_outcome_if_accepted": value.get("predicted_outcome_if_accepted"),
        "matrilineal_option_selected": value.get("matrilineal_option_selected"),
        # The selected parent's current House/Dynasty is prospective input,
        # independent of the still-unpriced actual child result below.
        "native_child_house_preview": deepcopy(value.get("native_child_house_preview")),
        "effective_matrilineal_if_accepted": value.get("effective_matrilineal_if_accepted"),
        "recipient_ai_accept_raw": value.get("recipient_ai_accept_raw"),
        "recipient_answer_status_raw": value.get("recipient_answer_status_raw"),
        "alliance_established": None,
        "future_alliance_obligation": "unknown",
        "unpriced": ["child_dynasty_result", "alliance_result",
                     "alliance_war_obligation", "betrothal_break_cost"],
        "resource_reservation_performed": False,
    }


def current_betrothal_fulfillment_m5_proposal(
    *, frame: Mapping[str, object], plan: Mapping[str, object],
) -> dict[str, object]:
    """Adapt the owning consumer's selected fixed-pair plan to existing M5."""
    choice = plan.get("current_betrothal_choice")
    resource = choice.get("resource_proposal") if isinstance(choice, Mapping) else None
    if (not isinstance(resource, Mapping)
            or resource.get("schema") != SCHEMA or resource.get("mode") != MODE
            or plan.get("selected_step") != SUBMIT_STEP
            or resource.get("typed_step") != SUBMIT_STEP
            or resource.get("selected") is not True
            or resource.get("formal_action_ready") is not True
            or resource.get("source_frame") != dict(frame)
            or resource.get("source_native_revision") != frame.get("native_revision")):
        raise ValueError("selected same-frame current-betrothal resource proposal required")
    costs = resource.get("immediate_generic_costs")
    if (not isinstance(costs, Mapping)
            or costs.get("raw_scale") != 100_000
            or costs.get("payer_role") != "actor"
            or costs.get("application_timing") != "on_send"
            or any(type(costs.get(key)) is not int or costs[key] != 0
                   for key in _COST_FIELDS)):
        raise ValueError("current-betrothal joint proposal requires observed zero on-send costs")
    heir, partner, recipient = (resource.get(key) for key in (
        "heir_character_id", "partner_character_id", "recipient_character_id"))
    commitment = resource.get("existing_commitment")
    claims = resource.get("character_claims")
    if (any(type(item) is not int or item <= 0 for item in (heir, partner, recipient))
            or resource.get("actor_character_id") != frame["played_character_id"]
            or not isinstance(commitment, Mapping)
            or commitment.get("bilateral_verified") is not True
            or commitment.get("new_betrothal_commitment") is not False
            or commitment.get("commitment_key") != f"first-heir-marriage:{heir}"
            or not isinstance(claims, list)
            or claims != sorted({item for item in claims if type(item) is int and item > 0})
            or not {frame["played_character_id"], heir, partner, recipient} <= set(claims)):
        raise ValueError("current-betrothal resource role binding is incomplete")
    return _proposal(
        frame=frame,
        candidate_id=f"marriage:fulfill-betrothal:{heir}:{partner}:{recipient}",
        domain="marriage", source_policy="current-first-heir-betrothal-formal-v1",
        gold_cost_raw=costs["gold_raw"], minimum_gold_reserve_raw=0,
        projected_supply_margin_raw=None, war_slot_claim=0,
        army_ids=[], ally_character_ids=[],
        character_ids=[item for item in claims if item != frame["played_character_id"]],
        commitment_keys=[str(commitment["commitment_key"])],
        evidence={"mode": MODE, "resource_proposal": deepcopy(dict(resource)),
                  "existing_betrothal_commitment_reused": True,
                  "alliance_established": None},
    )
