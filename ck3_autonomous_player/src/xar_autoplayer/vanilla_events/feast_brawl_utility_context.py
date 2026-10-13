"""Bounded .6003 choice using existing directed guest-to-player opinion reads.

The registry policy calls this only after its existing projection checks pass.
This comparison adopts the already documented cooperation-balance objective;
it does not predict friend/rival progress or claim a native AI optimum.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy


EVENT_KEY = "feast_default.6003"
_SOURCE = "events/activities/feast_activity/main_events/feast_default_events.txt"
_SOURCE_SHA = "D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1"
_OPINION_SCHEMA = "activity-feast-guest-opinion-private-read-v1"


def _character_id(scope: object) -> int | None:
    identity = scope.get("typed_identity") if isinstance(scope, Mapping) else None
    value = identity.get("character_id") if isinstance(identity, Mapping) else None
    if (isinstance(scope, Mapping) and scope.get("status") == "available"
            and scope.get("type_key") == "character"
            and isinstance(identity, Mapping)
            and identity.get("status") == "available"
            and identity.get("kind") == "character"
            and type(value) is int and value > 0):
        return value
    return None


def _current_opinions(
    observations: object, *, event: Mapping[str, object],
    knowledge: Mapping[str, object], actor_id: int, fighters: Mapping[str, int],
) -> tuple[dict[str, int] | None, str | None]:
    if observations is None:
        return None, "current_guest_opinion_inputs_missing"
    if (not isinstance(observations, Sequence)
            or isinstance(observations, (str, bytes, bytearray))
            or len(observations) != 2):
        return None, "current_guest_opinion_pair_unavailable"
    by_guest = {}
    for row in observations:
        if not isinstance(row, Mapping) or row.get("status") != "observed":
            return None, "current_guest_opinion_pair_unavailable"
        guest_id = row.get("guest_character_id")
        value = row.get("guest_opinion_of_actor")
        digest = row.get("exe_sha256")
        if not (
            row.get("schema") == _OPINION_SCHEMA
            and type(guest_id) is int and guest_id in fighters.values()
            and guest_id not in by_guest
            and row.get("actor_character_id") == actor_id
            and type(value) is int and -100 <= value <= 100
            and row.get("read_only") is True
            and row.get("raw_pointer_fields_persisted") is False
            and type(row.get("snapshot_revision")) is int
            and row["snapshot_revision"] > 0
            and row.get("queried_native_revision") == row["snapshot_revision"]
            and row.get("date_raw") == event.get("date_raw")
            and row.get("exact_ck3_build") == knowledge.get("ck3_build")
            and isinstance(digest, str)
            and digest.upper() == knowledge.get("ck3_exe_sha256")
            and isinstance(row.get("queried_snapshot_id"), str)
            and row.get("post_snapshot_id") == row.get("queried_snapshot_id")
        ):
            return None, "current_guest_opinion_pair_does_not_match_event"
        by_guest[guest_id] = value
    return {name: by_guest[identity] for name, identity in fighters.items()}, None


def compare_feast_brawl_choices_v1(
    event_context: Mapping[str, object], knowledge: Mapping[str, object], *,
    opinion_observations: object = None,
) -> dict[str, object] | None:
    """Select the weaker-affinity side, or explicitly retain the bounded route.

    ``opinion_observations`` contains the two unchanged normalized dictionaries
    returned by ``query_activity_feast_guest_opinion_private_v1``. Their direction
    is fighter -> current player. Missing inputs do not become neutral opinions.
    Each query has its own stable revision. The caller observes that the paused
    event instance/scopes remain current between queries; published revisions
    need not equal the earlier event-context revision or each other.
    """
    analysis = knowledge.get("analysis")
    sources = analysis.get("source_sha256") if isinstance(analysis, Mapping) else None
    if not (
        event_context.get("event_definition_key") == EVENT_KEY
        and knowledge.get("ck3_build") in {"1.20.0.3", "1.20.0.4"}
        and isinstance(sources, Mapping) and sources.get(_SOURCE) == _SOURCE_SHA
    ):
        return None
    options = event_context.get("options")
    by_index = {row.get("native_option_index"): row for row in options
        if isinstance(row, Mapping) and row.get("shown") is True
        and row.get("enabled") is True} if isinstance(options, list) else {}
    if set(by_index) != {0, 1}:
        return None
    actor_id = _character_id(event_context.get("root_scope"))
    rows = event_context.get("saved_scopes")
    scopes = {row.get("name"): row.get("scope") for row in rows
        if isinstance(row, Mapping)} if isinstance(rows, list) else {}
    fighters = {name: _character_id(scopes.get(name))
        for name in ("fighter_1", "fighter_2")}
    if (actor_id is None or None in fighters.values()
            or len(set(fighters.values())) != 2 or actor_id in fighters.values()):
        return None
    contract = knowledge.get("contract")
    selected = contract.get("selected_native_option_index") \
        if isinstance(contract, Mapping) else None
    if selected not in by_index:
        return None
    effect_profiles = analysis.get("authored_option_effect_profiles")
    baseline_utility = analysis.get("selected_choice_campaign_utility_profile")
    if (not isinstance(effect_profiles, Mapping)
            or not all(isinstance(effect_profiles.get(str(index)), Mapping)
                       for index in (0, 1))
            or not isinstance(baseline_utility, Mapping)):
        return None
    opinions, fallback_reason = _current_opinions(
        opinion_observations, event=event_context, knowledge=knowledge,
        actor_id=actor_id, fighters=fighters,
    )
    reason = "retain_source_reviewed_bounded_route_without_current_opinion_pair"
    if opinions is not None:
        if opinions["fighter_1"] < opinions["fighter_2"]:
            selected = 0
            reason = "support_fighter_1_with_lower_current_opinion_of_player"
        elif opinions["fighter_2"] < opinions["fighter_1"]:
            selected = 1
            reason = "support_fighter_2_with_lower_current_opinion_of_player"
        else:
            reason = "equal_current_opinions_retain_source_reviewed_bounded_route"
    opposed = 1 - selected
    utility = deepcopy(dict(baseline_utility))
    utility.update(
        selected_native_option_index=selected,
        selected_rank=1, rank_count=2,
        alternatives=[{"native_option_index": opposed, "rank": 2,
            "tradeoff": "supports_the_other_fighter_and_opposes_this_side"}],
        selection_basis=reason,
    )
    utility["selected_utility"]["material_direction"] = (
        f"support_fighter_{selected + 1}_and_oppose_fighter_{opposed + 1}"
    )
    effect_profile = deepcopy(dict(effect_profiles[str(selected)]))
    return {
        "selected_native_option_index": selected,
        "selected_option_number": selected + 1,
        "selected_rendered_index": by_index[selected]["rendered_index"],
        "selected_option": dict(by_index[selected]),
        "choice_effect_profile": effect_profile,
        "campaign_utility_profile": utility,
        "decision_context": {
            "schema": "xar.ck3.feast-brawl-current-opinion-context/v1",
            "policy": "support_lower_current_guest_opinion_v1",
            "objective_id": utility["objective_id"],
            "comparison_status": "current_inputs_compared" if opinions is not None
                else "bounded_fallback",
            "current_opinion_inputs_used": opinions is not None,
            "fallback_reason": fallback_reason,
            "selected_reason": reason,
            "event_instance_id": event_context.get("current_event_instance_id"),
            "snapshot_revision": event_context.get("snapshot_revision"),
            "date_raw": event_context.get("date_raw"),
            "actor_character_id": actor_id,
            "opinion_query_native_revisions": {
                str(row["guest_character_id"]): row["queried_native_revision"]
                for row in opinion_observations} if opinions is not None else None,
            "fighters": {name: {"character_id": identity,
                "opinion_of_player": opinions[name] if opinions is not None else None}
                for name, identity in fighters.items()},
            "relationship_identity_used": False,
            "predicted_relationship_outcomes": None,
            "generic_semantic_decision_ready": False,
        },
    }


__all__ = ["compare_feast_brawl_choices_v1"]
