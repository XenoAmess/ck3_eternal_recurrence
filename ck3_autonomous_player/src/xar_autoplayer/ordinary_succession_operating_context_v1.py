"""Pure current-estate feedback for ordinary long-term planning.

This is a consumer of the original complete retained expectation, not a new
query, legal player-heir classifier, law policy or submission authorization.
"""
from __future__ import annotations

from copy import deepcopy

from .bridge.succession_transition_contract import normalize_succession_expectation_v1

SCHEMA = "xar.ck3.ordinary-succession-operating-context/v1"
_FRAME_KEYS = ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "episode_character_id")


def _unavailable(reason, *, pending=False):
    return {"schema": SCHEMA, "status": "deferred_player_decision" if pending else "unavailable",
            "source_binding": None, "estate": None, "issues": [], "observed_changes": None,
            "unavailable_reason": reason, "action_candidates": [], "queries_performed": 0,
            "ordinary_priority_override": False, "submission_authorized": False}


def _assignments(expectation):
    return {row["title"]["title_id"]: row["first_heir_character_id"] for row in expectation["title_expectations"]}


def build_ordinary_succession_operating_context_v1(snapshot, *, previous_expectation=None):
    """Report personal-estate split and changes only on its exact living frame.

    A different heir for a held title is not proof that the title leaves the
    realm. A primary-title heir is not independently proved to be the legal
    player heir, of the player's dynasty, or alive at the future death.
    """
    if not isinstance(snapshot, dict):
        return _unavailable("current_snapshot_unavailable")
    if snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None:
        return _unavailable("resolve_original_player_decision_before_operating_review", pending=True)
    actor = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or not isinstance(actor, dict) or actor.get("alive") is not True
            or actor.get("character_id") != snapshot.get("episode_character_id")):
        return _unavailable("current_living_paused_episode_unavailable")
    lifecycle = snapshot.get("succession_lifecycle")
    if not isinstance(lifecycle, dict) or lifecycle.get("lifecycle") != "ordinary_campaign_succession":
        return _unavailable("ordinary_campaign_lifecycle_unavailable")
    try:
        current = normalize_succession_expectation_v1(snapshot.get("succession_expectation"))
    except (ValueError, TypeError, KeyError):
        return _unavailable("complete_retained_title_expectation_unavailable")
    binding = current["binding"]
    if any(binding[key] != snapshot.get(key) for key in _FRAME_KEYS):
        return _unavailable("retained_estate_requires_original_same_frame_refresh")
    if current["predecessor_character_id"] != actor["character_id"]:
        return _unavailable("retained_estate_belongs_to_another_actor")

    rows = current["title_expectations"]
    primary = next(row for row in rows if row["primary"])
    primary_tier = primary["title"].get("tier_raw")
    primary_heir = current["expected_successor_character_id"]
    other = [row for row in rows if row["first_heir_character_id"] not in (None, primary_heir)]
    unassigned = [row for row in rows if row["first_heir_character_id"] is None]
    same_or_higher = [row["title"]["title_id"] for row in other
                     if type(primary_tier) is int and type(row["title"].get("tier_raw")) is int
                     and row["title"]["tier_raw"] >= primary_tier]
    unknown_rank = [row["title"]["title_id"] for row in other
                    if type(primary_tier) is not int or type(row["title"].get("tier_raw")) is not int]
    issues = []
    if primary_heir is None:
        issues.append({"kind": "no_observed_primary_title_heir", "title_ids": [primary["title"]["title_id"]]})
    if other:
        issues.append({"kind": "personal_estate_split_between_observed_heirs",
                       "title_ids": [row["title"]["title_id"] for row in other]})
    if same_or_higher:
        issues.append({"kind": "other_heir_receives_equal_or_higher_rank_title",
                       "title_ids": same_or_higher, "actual_realm_exit_proven": False})
    if unassigned:
        issues.append({"kind": "held_titles_without_observed_heir",
                       "title_ids": [row["title"]["title_id"] for row in unassigned]})

    changes = None
    previous_issue = "previous_complete_projection_not_supplied"
    if previous_expectation is not None:
        try:
            previous = normalize_succession_expectation_v1(previous_expectation)
            old_binding = previous["binding"]
            if (old_binding["episode_run_id"] != binding["episode_run_id"]
                    or previous["predecessor_character_id"] != current["predecessor_character_id"]
                    or any(old_binding[key] > binding[key] for key in ("date_raw", "revision", "native_revision"))):
                raise ValueError("prior projection belongs to another source sequence")
            old, new = _assignments(previous), _assignments(current)
            old_primary = next(row["title"]["title_id"] for row in previous["title_expectations"] if row["primary"])
            changes = {"source_binding": deepcopy(old_binding),
                       "added_held_title_ids": sorted(new.keys() - old.keys()),
                       "removed_held_title_ids": sorted(old.keys() - new.keys()),
                       "changed_first_heir_title_ids": sorted(key for key in new.keys() & old.keys() if new[key] != old[key]),
                       "primary_title_changed": old_primary != primary["title"]["title_id"],
                       "primary_title_heir_changed": previous["expected_successor_character_id"] != primary_heir}
            previous_issue = None
        except (ValueError, TypeError, KeyError):
            previous_issue = "previous_projection_not_comparable_to_current_episode"
    return {"schema": SCHEMA, "status": "available", "source_binding": deepcopy(binding),
            "source_kind": "original_complete_expectation_on_same_published_frame",
            "published_frame_is_not_an_estate_or_law_epoch": True,
            "estate": {"primary_title_id": primary["title"]["title_id"],
                       "primary_title_heir_character_id": primary_heir,
                       "risk_state": current["risk_state"], "title_expectations": deepcopy(rows),
                       "personal_estate_titles_to_primary_title_heir": [row["title"]["title_id"] for row in rows
                           if primary_heir is not None and row["first_heir_character_id"] == primary_heir],
                       "personal_estate_titles_to_other_heirs": [row["title"]["title_id"] for row in other],
                       "titles_without_observed_heir": [row["title"]["title_id"] for row in unassigned],
                       "equal_or_higher_rank_titles_to_other_heirs": same_or_higher,
                       "other_heir_title_rank_unavailable": unknown_rank},
            "issues": issues, "observed_changes": changes, "previous_comparison_unavailable_reason": previous_issue,
            "missing_operating_inputs": ["same_published_frame_estate_or_law_change_witness",
                "independently_qualified_current_legal_player_heir_and_dynasty",
                "current_realm_and_title_succession_laws", "candidate_action_final_permission_cost_and_political_consequences",
                "native_counterfactual_distribution_for_a_supported_action", "actual_post_partition_realm_relationships"],
            "law_change_inferred_from_title_distribution": False,
            "actual_land_loss_or_realm_exit_inferred": False,
            "action_candidates": [], "queries_performed": 0,
            "ordinary_priority_override": False, "submission_authorized": False, "unavailable_reason": None}
