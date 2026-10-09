"""Private same-frame M5 sources for peaceful building, gifts and family.

This module only composes existing read-only domain queries.  It does not
advertise a capability, submit an action, or turn partial data into a no-op.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping, Sequence

from .bridge.domain_construction_private_transport_v1 import (
    RESERVE_RAW as CONSTRUCTION_RESERVE_RAW,
    _identity as construction_process_identity,
    query_construction_private,
)
from .bridge.driver import BridgeUnavailableError
from .bridge.faction_gift_formal_route_v1 import (
    MINIMUM_GOLD_RESERVE_RAW as FACTION_GIFT_RESERVE_RAW,
)
from .construction_formal_consumer import (
    priority_construction_receipt,
    read_construction_ledger,
    same_construction_process_identity,
)
from .faction_gift_formal_candidate_v1 import (
    latest_same_frame_faction_root_v1,
)
from .faction_gift_pending_v1 import read_faction_gift_ledger_v1
from .faction_threat_response_inputs_v1 import observe_faction_gift_stock_threat_v1
from .family_marriage_formal_consumer import (
    plan_family_marriage_private, read_family_marriage_ledger,
)
from .player_child_default_formal_consumer import read_child_default_ledger
from .bridge.observed_heir_marriage_private_action_v1 import (
    SUBMIT_STEP as FAMILY_SUBMIT_STEP,
)
from .m5_formal_proposal_collector import (
    SOURCE_SCHEMA, _same_frame_root_returned_unavailable,
)
from .m5_observed_opportunity_selector import observed_frame


PRODUCER_POLICY = "g2-m5-peacetime-building-faction-family-source-v1"


def query_m5_peacetime_proposal_sources_v1(
    driver: object,
    *,
    snapshot: Mapping[str, object],
    history: Sequence[Mapping[str, object]],
    baseline_plan: Mapping[str, object],
    expected_revision: int,
) -> dict[str, object]:
    """Read at most one approved proposal per peaceful domain on one frame."""

    frame = _require_peaceful_frame(snapshot, expected_revision=expected_revision)
    observed_gold_raw = _snapshot_gold(snapshot)
    if (
        baseline_plan.get("policy") != "one-life-turn-v1"
        or baseline_plan.get("selected_step") != "life-advance"
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source requires the ordinary life-advance baseline"
        )
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks its managed durable state_dir"
        )

    construction_ledger = read_construction_ledger(state_dir)
    faction_ledger = read_faction_gift_ledger_v1(state_dir)
    gift_enabled = getattr(
        driver, "allow_private_faction_gift_formal_trial", False
    ) is True
    family_enabled = getattr(
        driver, "allow_private_family_marriage_formal_trial", False
    ) is True
    # Turning off new family submissions does not cancel an already sent
    # proposal. Its observed durable role claims still occupy this episode.
    family_ledger = read_family_marriage_ledger(state_dir)
    pending_family = family_ledger["pending"]
    family_claims = _pending_family_commitments(pending_family, frame)
    child_default_ledger = read_child_default_ledger(state_dir)
    pending_child_default = child_default_ledger["pending"]
    child_default_claims = _pending_child_default_commitments(
        pending_child_default, frame,
    )
    family_claims = {
        key: sorted(set(family_claims[key]) | set(child_default_claims[key]))
        for key in family_claims
    }
    if construction_ledger.get("pending") is not None:
        raise BridgeUnavailableError(
            "M5 peacetime source has an unresolved construction action"
        )
    if faction_ledger.get("pending") is not None:
        raise BridgeUnavailableError(
            "M5 peacetime source has an unresolved faction gift action"
        )
    try:
        priority_receipt = priority_construction_receipt(
            driver, construction_ledger, snapshot,
        )
    except BridgeUnavailableError:
        # Legacy single-applied readbacks may lack a process identity in a
        # query-only caller. Keep the old independent gift route; the latest
        # building stays unavailable through the release check below.
        if construction_ledger.get("applied_prior"):
            raise
        priority_receipt = None
    if priority_receipt is not None:
        raise BridgeUnavailableError(
            "M5 peacetime source must consume a prior construction receipt first"
        )
    applied = construction_ledger.get("applied")
    construction_blocked = _prior_construction_blocks_candidate(
        driver, applied=applied, frame=frame,
    )

    _require_driver_frame(driver, frame, expected_gold_raw=observed_gold_raw)
    root_view = (latest_same_frame_faction_root_v1(snapshot, history)
                 if gift_enabled else None)
    root_status = (root_view.get("status") if isinstance(root_view, Mapping)
                   else "gift_consumer_disabled")
    root_unavailable = (
        gift_enabled and root_status == "same_frame_root_not_observed"
        and _same_frame_root_returned_unavailable(snapshot, history)
    )
    if (gift_enabled and not root_unavailable
            and root_status not in {"known_empty", "targeting_present"}):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks a complete same-frame feudal faction root: "
            f"{root_status or 'unknown'}"
        )

    if construction_blocked:
        # The formal route must consume or recheck its earlier receipt before
        # another building can enter the joint comparison.  A faction gift
        # remains an independent opportunity on the same frame.
        construction = {"status": "prior_receipt_not_released"}
    else:
        construction = query_construction_private(
            driver, expected_revision=expected_revision
        )
        _require_driver_frame(
            driver, frame, expected_gold_raw=observed_gold_raw
        )
        construction_status = construction.get("status")
        if construction_status not in {
            "selected", "no_legal_budgeted_building",
        }:
            raise BridgeUnavailableError(
                "M5 peacetime construction source is incomplete: "
                f"{construction_status or 'unknown'}"
            )
        construction_world = construction.get("world")
        if (
            not isinstance(construction_world, Mapping)
            or construction_world.get("player_gold_raw") != observed_gold_raw
        ):
            raise BridgeUnavailableError(
                "M5 peacetime construction gold crossed the planning frame"
            )
    construction_status = construction["status"]

    faction: dict[str, object]
    if not gift_enabled:
        faction = {
            "status": "consumer_disabled",
            "reason": "formal_gift_trial_off",
            "public_capability_advertised": False,
            "gift_submission_enabled": False,
        }
    elif root_unavailable:
        # A completed unavailable read leaves diplomacy unresolved; it says
        # nothing about an independently legal building on this peace frame.
        faction = {
            "status": "same_frame_root_unavailable",
            "reason": "native_faction_root_unavailable",
            "public_capability_advertised": False,
            "gift_submission_enabled": False,
        }
    elif root_status == "known_empty":
        faction = {
            "status": "known_empty",
            "reason": "same_frame_public_targeting_count_zero",
            "public_capability_advertised": False,
            "gift_submission_enabled": False,
        }
    else:
        root = root_view.get("root") if isinstance(root_view, Mapping) else None
        reader = getattr(driver, "query_faction_gift_private_candidate_v1", None)
        if not isinstance(root, Mapping) or not callable(reader):
            raise BridgeUnavailableError(
                "M5 peacetime faction source reader is unavailable"
            )
        raw_faction = reader(
            snapshot=deepcopy(dict(snapshot)),
            same_frame_root=deepcopy(dict(root)),
            minimum_gold_reserve_raw=FACTION_GIFT_RESERVE_RAW,
        )
        if not isinstance(raw_faction, Mapping):
            raise BridgeUnavailableError(
                "M5 peacetime faction source returned a non-object"
            )
        faction = deepcopy(dict(raw_faction))
        faction_status = faction.get("status")
        if faction_status not in {"selected", "no_legal_candidate"}:
            raise BridgeUnavailableError(
                "M5 peacetime faction source is incomplete: "
                f"{faction_status or 'unknown'}"
            )
        observation = faction.get("observation")
        if (
            not isinstance(observation, Mapping)
            or observation.get("player_gold_raw") != observed_gold_raw
        ):
            raise BridgeUnavailableError(
                "M5 peacetime faction gold crossed the planning frame"
            )
        if faction_status == "selected":
            faction["stock_threat_response"] = observe_faction_gift_stock_threat_v1(
                driver, snapshot=snapshot, history=history, candidate=faction,
                expected_revision=expected_revision,
            )
            _require_driver_frame(driver, frame, expected_gold_raw=observed_gold_raw)

    family_status = "opt_in_off"
    family_plan: dict[str, object] | None = None
    family_plans: list[dict[str, object]] = []
    if family_enabled:
        prior_resolution = family_ledger["resolved"]
        relation_enabled = getattr(
            driver, "allow_private_current_first_heir_relationship_query", False
        ) is True
        if (family_ledger["pending"] is not None
                or (not relation_enabled
                    and isinstance(prior_resolution, Mapping)
                    and prior_resolution.get("episode_run_id") ==
                    frame["episode_run_id"])):
            family_status = "existing_formal_ledger"
        else:
            # The collector already consumed any matching material result.
            # A resolved prior heir may now be stale, so re-evaluate the
            # current relation before excluding a new family proposal.
            observed = plan_family_marriage_private(
                driver, {"revision": expected_revision,
                         "plan": deepcopy(dict(baseline_plan))},
                deepcopy(dict(snapshot)),
            )
            plan = observed.get("plan")
            if not isinstance(plan, Mapping):
                raise BridgeUnavailableError("M5 family policy returned no plan")
            if plan.get("selected_step") == FAMILY_SUBMIT_STEP:
                family_status = "selected"
                family_plan = deepcopy(dict(plan))
                choices = plan.get("family_marriage_valued_choices")
                if choices is None:
                    choices = [plan.get("family_marriage_choice")]
                diagnostic = plan.get("family_marriage_private_diagnostic")
                if (not isinstance(choices, list) or not 1 <= len(choices) <= 5
                        or not isinstance(diagnostic, Mapping)
                        or choices[0] != plan.get("family_marriage_choice")):
                    raise BridgeUnavailableError(
                        "M5 family valued choices lack one selected five-row proof"
                    )
                candidate_ids: set[int] = set()
                for choice in choices:
                    candidate_id = (choice.get("candidate_character_id")
                                    if isinstance(choice, Mapping) else None)
                    if (type(candidate_id) is not int or candidate_id <= 0
                            or candidate_id in candidate_ids):
                        raise BridgeUnavailableError(
                            "M5 family valued choices repeat or lack a candidate"
                        )
                    candidate_ids.add(candidate_id)
                    variant = deepcopy(dict(plan))
                    variant["family_marriage_choice"] = deepcopy(dict(choice))
                    variant_diagnostic = deepcopy(dict(diagnostic))
                    variant_diagnostic["selected_candidate_character_id"] = candidate_id
                    variant["family_marriage_private_diagnostic"] = variant_diagnostic
                    family_plans.append(variant)
            else:
                observed_status = plan.get("family_marriage_status")
                family_status = (observed_status if isinstance(observed_status, str)
                                 else "no_approved_proposal")

    _require_driver_frame(driver, frame, expected_gold_raw=observed_gold_raw)
    # The two existing query transports do not mutate either formal ledger.
    # Re-read them before publishing explicit empty commitments.
    if read_construction_ledger(state_dir) != construction_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime construction ledger changed during readback"
        )
    if read_faction_gift_ledger_v1(state_dir) != faction_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime faction ledger changed during readback"
        )
    if read_family_marriage_ledger(state_dir) != family_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime family ledger changed during readback"
        )
    if read_child_default_ledger(state_dir) != child_default_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime child-default ledger changed during readback"
        )

    domains: dict[str, object] = {}
    if construction_status == "selected":
        domains["building"] = {"query": deepcopy(dict(construction))}
    if faction.get("status") == "selected":
        domains["diplomacy"] = {"candidate": deepcopy(faction)}
    if family_plan is not None:
        domains["marriage"] = {"plan": family_plan, "plans": family_plans}

    return {
        "schema": SOURCE_SCHEMA,
        "status": "available",
        "read_only": True,
        "advertised": False,
        "frame": deepcopy(frame),
        "existing_commitments": {
            "frame": deepcopy(frame),
            "gold_raw": 0,
            "pending_war_slots": 0,
            "army_ids": [],
            "ally_character_ids": family_claims["ally_character_ids"],
            "character_ids": family_claims["character_ids"],
            "commitment_keys": family_claims["commitment_keys"],
        },
        # Each admitted proposal retains its existing domain reserve.  Zero is
        # the observed absence of an additional cross-domain cash commitment.
        "gold_reserve_raw": 0,
        # This producer proves an empty active-war vector and admits no war
        # proposal, so its observed joint war-slot budget is exactly zero.
        "max_active_wars": 0,
        "domains": domains,
        "producer": {
            "policy": PRODUCER_POLICY,
            "scope": "peacetime_building_faction_and_opted_family",
            "observed_player_gold_raw": observed_gold_raw,
            "domain_minimum_gold_reserves_raw": {
                "building": CONSTRUCTION_RESERVE_RAW,
                "diplomacy": FACTION_GIFT_RESERVE_RAW,
            },
            "observed_active_war_count": 0,
            "observed_player_army_count": 0,
            "construction_status": construction_status,
            "faction_status": faction.get("status"),
            "incomplete_domains": ["diplomacy"] if root_unavailable else [],
            "family_status": family_status,
            "pending_family_commitment_source": (
                "formal_pending_ledger" if pending_family is not None else None
            ),
            "pending_child_default_commitment_source": (
                "formal_pending_ledger" if pending_child_default is not None else None
            ),
            "pending_formal_ledgers_empty": (
                pending_family is None and pending_child_default is None),
            "formal_action_ready": False,
        },
    }


def _pending_family_commitments(
    pending: object, frame: Mapping[str, object],
) -> dict[str, list[int] | list[str]]:
    if pending is None:
        return {"ally_character_ids": [], "character_ids": [],
                "commitment_keys": []}
    if not isinstance(pending, Mapping) or (
        pending.get("episode_run_id") != frame["episode_run_id"]
        or pending.get("played_character_id") != frame["played_character_id"]
    ):
        raise BridgeUnavailableError(
            "M5 pending family commitment crossed the actor episode"
        )
    heir = pending.get("heir_character_id")
    candidate = pending.get("candidate_character_id")
    recipient = pending.get("recipient_character_id")
    actor = frame["played_character_id"]
    if (
        any(type(value) is not int or value <= 0
            for value in (heir, candidate, recipient))
        or heir == candidate or actor in {heir, candidate, recipient}
    ):
        raise BridgeUnavailableError(
            "M5 pending family commitment lacks exact role identities"
        )
    alliance_attempt = pending.get(
        "preproposal_realm_alliance_attempt_if_accepted", True)
    if type(alliance_attempt) is not bool:
        raise BridgeUnavailableError("M5 pending family alliance claim is unreadable")
    return {
        # Historical pending ledgers predate this field; retain their earlier
        # conservative recipient claim. A new no-attempt betrothal still
        # occupies three characters and the heir's marriage commitment.
        "ally_character_ids": [recipient] if alliance_attempt else [],
        "character_ids": sorted({heir, candidate, recipient}),
        "commitment_keys": [f"first-heir-marriage:{heir}"],
    }


def _pending_child_default_commitments(
    pending: object, frame: Mapping[str, object],
) -> dict[str, list[int] | list[str]]:
    if pending is None:
        return _pending_family_commitments(None, frame)
    if not isinstance(pending, Mapping) or (
        pending.get("episode_run_id") != frame["episode_run_id"]
        or pending.get("played_character_id") != frame["played_character_id"]
    ):
        raise BridgeUnavailableError(
            "M5 pending child-default commitment crossed the actor episode"
        )
    actor = frame["played_character_id"]
    subject = pending.get("heir_character_id")
    candidate = pending.get("candidate_character_id")
    recipient = pending.get("recipient_character_id")
    if (any(type(value) is not int or value <= 0
            for value in (subject, candidate, recipient))
            or subject == candidate or actor in {subject, candidate}):
        raise BridgeUnavailableError(
            "M5 pending child-default commitment lacks exact role identities"
        )
    projection = pending.get("selected_value_projection")
    costs = projection.get("generic_costs") if isinstance(projection, Mapping) else None
    pairs = (projection.get("possible_alliance_pairs")
             if isinstance(projection, Mapping) else None)
    if (not isinstance(costs, Mapping)
            or costs.get("application_timing") != "on_send"
            or not isinstance(pairs, list)):
        raise BridgeUnavailableError(
            "M5 pending child-default resource projection is unavailable"
        )
    allies: set[int] = set()
    for pair in pairs:
        if (not isinstance(pair, Mapping)
                or type(pair.get("would_attempt_if_accepted")) is not bool
                or any(type(pair.get(key)) is not int or pair[key] <= 0
                       for key in ("first_character_id", "second_character_id"))):
            raise BridgeUnavailableError("M5 pending child-default alliance claim is unreadable")
        members = {pair["first_character_id"], pair["second_character_id"]}
        if pair["would_attempt_if_accepted"] and actor in members:
            allies.update(members - {actor})
    return {
        "ally_character_ids": sorted(allies),
        "character_ids": sorted({subject, candidate, recipient} - {actor}),
        "commitment_keys": [f"player-child-default-marriage:{subject}"],
    }


def _prior_construction_blocks_candidate(
    driver: object, *, applied: object, frame: Mapping[str, object],
) -> bool:
    if not (isinstance(applied, Mapping)
            and applied.get("episode_run_id") == frame["episode_run_id"]):
        return False
    try:
        process = construction_process_identity(driver)
    except BridgeUnavailableError:
        return True
    return not (
        applied.get("status") == "applied"
        and applied.get("postcondition_verified") is True
        and applied.get("actor_character_id") == frame["played_character_id"]
        and same_construction_process_identity(process, (
            applied.get("post_bridge_pid"), applied.get("post_bridge_creation_date")))
        and type(applied.get("post_native_revision")) is int
        and type(applied.get("post_date_raw")) is int
        and frame["native_revision"] > applied["post_native_revision"]
        and frame["date_raw"] > applied["post_date_raw"]
    )


def _require_peaceful_frame(
    snapshot: Mapping[str, object], *, expected_revision: int
) -> dict[str, object]:
    if type(expected_revision) is not int or expected_revision <= 0:
        raise BridgeUnavailableError(
            "M5 peacetime source lacks the planning revision"
        )
    frame = observed_frame(snapshot)
    played = snapshot.get("played_character")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or played.get("character_id") != frame["played_character_id"]
        or snapshot.get("active_event") is not None
        or snapshot.get("pending_character_interaction") is not None
        or snapshot.get("one_life_terminal_reason") is not None
        or snapshot.get("active_wars") != []
        or snapshot.get("player_armies") != []
        or frame["revision"] != expected_revision
        or frame["snapshot_id"] != f"native:{frame['native_revision']}"
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source requires one stable peaceful paused actor frame"
        )
    _snapshot_gold(snapshot)
    return frame


def _snapshot_gold(snapshot: Mapping[str, object]) -> int:
    gold = snapshot.get("played_character_gold")
    raw = gold.get("raw") if isinstance(gold, Mapping) else None
    if (
        type(raw) is not int
        or raw < 0
        or gold.get("scale") != 100_000
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks observed player gold"
        )
    return raw


def _require_driver_frame(
    driver: object, expected_frame: Mapping[str, object], *,
    expected_gold_raw: int,
) -> None:
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    if not callable(reader):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks an internal semantic snapshot reader"
        )
    current = reader()
    if not isinstance(current, Mapping):
        raise BridgeUnavailableError(
            "M5 peacetime source internal snapshot is malformed"
        )
    current_frame = _require_peaceful_frame(
        current, expected_revision=int(expected_frame["revision"])
    )
    if current_frame != dict(expected_frame):
        raise BridgeUnavailableError(
            "M5 peacetime source crossed its paused frame"
        )
    if _snapshot_gold(current) != expected_gold_raw:
        raise BridgeUnavailableError(
            "M5 peacetime source player gold changed during readback"
        )
