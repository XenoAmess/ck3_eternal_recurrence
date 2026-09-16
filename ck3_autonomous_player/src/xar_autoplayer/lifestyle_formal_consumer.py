"""Controlled LIFE recommendation after the ordinary forced-state/war turn.

The source and action are private until native final legality, an independent
material receipt, and a following formal turn have been seen in one build.
"""

from __future__ import annotations

from typing import Mapping

from .lifestyle_min_policy import choose_min_feudal_lifestyle_action


ROOT_QUERY_STEP = "query-campaign-root-context-v1"
PERK_SUBMIT_STEP = "private-select-player-lifestyle-perk-v1"
RECEIPT_STEP = "private-query-player-lifestyle-receipt-v1"


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def unresolved_lifestyle_perk_action(
    snapshot: Mapping[str, object], history: list[dict[str, object]]
) -> dict[str, object] | None:
    """Retain an in-flight action ID across formal turns; never blind retry."""

    episode = snapshot.get("episode_run_id")
    if not isinstance(episode, str) or not episode:
        return None
    for row in reversed(history):
        command = row.get("command")
        result = row.get("result")
        if command not in {PERK_SUBMIT_STEP, RECEIPT_STEP} or not isinstance(
            result, Mapping
        ):
            continue
        if result.get("episode_run_id") != episode:
            continue
        if command == RECEIPT_STEP and result.get("status") == "applied":
            return None
        if command == PERK_SUBMIT_STEP:
            if result.get("status") in {
                "action_state_unknown",
                "submitted_verification_pending",
            }:
                return dict(result)
            return None
    return None


def latest_lifestyle_applied_receipt(
    snapshot: Mapping[str, object], history: list[dict[str, object]]
) -> dict[str, object] | None:
    """Expose the independent material result to the following formal turn."""

    episode = snapshot.get("episode_run_id")
    for row in reversed(history):
        if row.get("command") != RECEIPT_STEP or row.get("ok") is not True:
            continue
        result = row.get("result")
        if (
            isinstance(result, Mapping)
            and result.get("status") == "applied"
            and result.get("post_target_perk_owned") is True
            and result.get("postcondition_verified") is True
            and result.get("episode_run_id") == episode
        ):
            return {
                key: result.get(key) for key in (
                    "action_request_id", "target_key", "post_snapshot_id",
                    "post_public_revision", "post_date_raw", "episode_run_id",
                    "post_target_perk_owned", "postcondition_verified",
                )
            }
    return None


def same_frame_feudal_peace_scope(
    snapshot: Mapping[str, object], history: list[dict[str, object]]
) -> dict[str, object]:
    """Use an independent public campaign-root query, never a guessed flag."""

    if snapshot.get("paused") is not True:
        return {"status": "scope_unavailable"}
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return {"status": "scope_unavailable"}
    if wars:
        return {"status": "outside_scene", "at_peace": False}
    played = snapshot.get("played_character")
    player_id = played.get("character_id") if isinstance(played, Mapping) else None
    revision = snapshot.get("native_revision")
    if not (
        _positive(revision)
        and snapshot.get("revision") == revision
        and _positive(player_id)
        and isinstance(snapshot.get("date_raw"), int)
    ):
        return {"status": "scope_unavailable"}
    for row in reversed(history):
        if row.get("command") != ROOT_QUERY_STEP or row.get("ok") is not True:
            continue
        result = row.get("result")
        root = (
            result.get("campaign_root_context")
            if isinstance(result, Mapping)
            else None
        )
        if not (
            isinstance(root, Mapping)
            and root.get("status") == "available"
            and root.get("snapshot_revision") == revision
            and root.get("date_raw") == snapshot.get("date_raw")
            and root.get("player_character_id") == player_id
        ):
            continue
        government = root.get("government")
        if not isinstance(government, Mapping):
            return {"status": "scope_unavailable"}
        flags = government.get("flags")
        if not isinstance(flags, list):
            return {"status": "scope_unavailable"}
        if (
            government.get("key") == "feudal_government"
            and "government_is_feudal" in flags
        ):
            return {
                "status": "admitted",
                "at_peace": True,
                "government_key": "feudal_government",
                "snapshot_revision": revision,
                "player_character_id": player_id,
            }
        return {"status": "outside_scene", "at_peace": True}
    return {"status": "root_query_needed", "at_peace": True}


def consume_lifestyle_private_query(
    baseline_plan: Mapping[str, object],
    *,
    scope: Mapping[str, object],
    query: Mapping[str, object] | None,
) -> dict[str, object]:
    """Choose one typed perk only after native final legality and LIFE2 state."""

    plan = dict(baseline_plan)
    if plan.get("selected_step") != "life-advance":
        return plan
    scope_status = scope.get("status")
    if scope_status == "outside_scene":
        return plan
    if scope_status == "root_query_needed":
        return {
            **plan,
            "phase": "lifestyle_scope_query",
            "selected_step": ROOT_QUERY_STEP,
            "reason": "read exact same-frame feudal government before LIFE action",
        }
    if scope_status != "admitted":
        return {
            **plan,
            "phase": "lifestyle_scope_unavailable",
            "selected_step": None,
            "reason": "peace or feudal scope has no independent true observation",
        }
    if not isinstance(query, Mapping) or query.get("status") != "available":
        return {
            **plan,
            "phase": "lifestyle_native_query_unavailable",
            "selected_step": None,
            "lifestyle_query_status": (
                query.get("status") if isinstance(query, Mapping) else "not_executed"
            ),
            "lifestyle_native_error": (
                query.get("native_error") if isinstance(query, Mapping) else None
            ),
            "reason": "LIFE2 state or LIFE4 final candidates did not bind this paused player",
        }
    life_snapshot = query.get("snapshot")
    recommendation = choose_min_feudal_lifestyle_action(
        life_snapshot if isinstance(life_snapshot, Mapping) else None,
        feudal_scope_admitted=True,
        at_peace=True,
    )
    if recommendation.get("status") == "recommend_action":
        action = recommendation.get("selected_action")
        if (
            isinstance(action, Mapping)
            and action.get("kind") == "perk"
            and query.get("formal_precondition_status") == "ready"
        ):
            return {
                **plan,
                "phase": "lifestyle_min_perk_action",
                "selected_step": PERK_SUBMIT_STEP,
                "lifestyle_action": dict(action),
                "lifestyle_query": dict(query),
                "lifestyle_decision": recommendation,
                "reason": "one native-final-legal stewardship build-cost perk",
            }
        return {
            **plan,
            "phase": "lifestyle_action_not_fireable",
            "selected_step": None,
            "lifestyle_decision": recommendation,
            "reason": "the private wire only admits a ready final-legal perk",
        }
    if recommendation.get("status") == "no_legal_minimum":
        return {**plan, "lifestyle_decision": recommendation}
    return {
        **plan,
        "phase": "lifestyle_min_observation_unavailable",
        "selected_step": None,
        "lifestyle_decision": recommendation,
        "reason": "the minimum governance action lacks a complete same-frame input",
    }
