"""One-action feudal lifestyle recommendation for a controlled private trial.

This consumes the exact private LIFE2 snapshot shape. It does not submit a
command or register a production capability; the single CK3 owner must first
validate the native source and later-state receipt in a bounded live run.
"""

from __future__ import annotations

from typing import Mapping


POLICY_ID = "g2-m4-lifestyle-min-v1"
WAR_PERK_POLICY_ID = "g2-lifestyle-wartime-stewardship-perk-v1"
_STEWARDSHIP = "stewardship_lifestyle"
_BUILD_COST_PERK = "cutting_corners_perk"
_BUILD_SPEED_PERK = "professional_workforce_perk"
_WEALTH_FOCUS = "stewardship_wealth_focus"
_REQUIRED_READINESS = (
    "current_focus_ready",
    "lifestyle_progress_ready",
    "owned_perks_ready",
    "same_frame_ready",
)


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _binding(snapshot: Mapping[str, object]) -> dict[str, object] | None:
    snapshot_id = snapshot.get("snapshot_id")
    episode_run_id = snapshot.get("episode_run_id")
    date_raw = snapshot.get("date_raw")
    player_id = snapshot.get("player_character_id")
    revisions = (
        snapshot.get("public_revision"),
        snapshot.get("native_revision"),
        snapshot.get("proof_epoch"),
    )
    if not isinstance(snapshot_id, str) or not snapshot_id:
        return None
    if not isinstance(episode_run_id, str) or not episode_run_id:
        return None
    if not isinstance(date_raw, int) or isinstance(date_raw, bool):
        return None
    if not isinstance(player_id, int) or isinstance(player_id, bool) or player_id < 0:
        return None
    if not all(_positive_int(value) for value in revisions):
        return None
    return {
        "expected_snapshot_id": snapshot_id,
        "expected_episode_run_id": episode_run_id,
        "expected_public_revision": revisions[0],
        "expected_native_revision": revisions[1],
        "expected_proof_epoch": revisions[2],
        "expected_date_raw": date_raw,
        "expected_player_character_id": player_id,
    }


def _available_keys(collection: object, lifestyle_key: str) -> set[str] | None:
    if not isinstance(collection, Mapping) or collection.get("status") != "available":
        return None
    items = collection.get("items")
    if not isinstance(items, list):
        return None
    keys: set[str] = set()
    for row in items:
        if not isinstance(row, Mapping):
            return None
        key, owner = row.get("key"), row.get("lifestyle_key")
        if not isinstance(key, str) or not key or not isinstance(owner, str):
            return None
        if owner == lifestyle_key:
            keys.add(key)
    return keys


def choose_min_feudal_lifestyle_action(
    snapshot: Mapping[str, object] | None,
    *,
    feudal_scope_admitted: bool | None,
    at_peace: bool | None,
    allow_wartime_perk: bool = False,
    pending_action: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Choose one native focus/perk target from a complete paused observation.

    The caller derives feudal scope and war state from independent campaign-root
    state. The wartime opt-in admits only an already focused perk. A pending
    submit must be verified against a fresh receipt before
    any further recommendation. No request ID or CK3 action is generated here.
    """
    result: dict[str, object] = {
        "policy_id": (
            WAR_PERK_POLICY_ID if at_peace is False and allow_wartime_perk
            else POLICY_ID
        ),
        "selected_action": None,
    }
    if feudal_scope_admitted is None or at_peace is None:
        return {**result, "status": "scope_observation_unavailable"}
    if feudal_scope_admitted is not True or (
        at_peace is not True and allow_wartime_perk is not True
    ):
        return {**result, "status": "outside_admitted_scene"}
    if isinstance(pending_action, Mapping):
        status = pending_action.get("status")
        if status == "submitted_verification_pending":
            return {**result, "status": "verify_pending_receipt"}
        if status == "applied":
            return {**result, "status": "consume_applied_receipt"}
        if status != "rejected_before_submit":
            return {**result, "status": "action_state_unknown"}
    if not isinstance(snapshot, Mapping) or snapshot.get("status") != "available":
        return {**result, "status": "observation_unavailable"}
    readiness = snapshot.get("readiness")
    if not isinstance(readiness, Mapping) or not all(
        readiness.get(name) is True for name in _REQUIRED_READINESS
    ):
        return {**result, "status": "observation_unavailable"}
    binding = _binding(snapshot)
    if binding is None:
        return {**result, "status": "observation_unavailable"}
    owned = snapshot.get("owned_perk_keys")
    if not isinstance(owned, list) or not all(isinstance(key, str) for key in owned):
        return {**result, "status": "observation_unavailable"}
    focus = snapshot.get("current_focus")
    progress = snapshot.get("current_lifestyle_progress")
    if not isinstance(focus, Mapping) or not isinstance(progress, Mapping):
        return {**result, "status": "observation_unavailable"}
    if focus.get("presence") == "present":
        if readiness.get("legal_perk_candidates_ready") is not True:
            return {**result, "status": "legal_candidates_unavailable"}
        perk_keys = _available_keys(
            snapshot.get("legal_perk_candidates"), _STEWARDSHIP
        )
        if perk_keys is None:
            return {**result, "status": "legal_candidates_unavailable"}
        current_key = focus.get("key")
        current_lifestyle = focus.get("lifestyle_key")
        if (
            not isinstance(current_key, str)
            or not current_key
            or not isinstance(current_lifestyle, str)
            or not current_lifestyle
            or progress.get("presence") != "present"
            or progress.get("lifestyle_key") != current_lifestyle
        ):
            return {**result, "status": "observation_unavailable"}
        if current_lifestyle == _STEWARDSHIP:
            points = progress.get("unspent_perk_points")
            if not isinstance(points, int) or isinstance(points, bool) or points < 0:
                return {**result, "status": "observation_unavailable"}
            if points > 0 and _BUILD_COST_PERK in perk_keys and _BUILD_COST_PERK not in owned:
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _BUILD_COST_PERK,
                        "target_lifestyle_key": _STEWARDSHIP,
                        "expected": binding,
                        "reason": "feudal_build_cost_reduction_5_percent",
                    },
                }
            if (
                points > 0
                and _BUILD_COST_PERK in owned
                and _BUILD_SPEED_PERK in perk_keys
                and _BUILD_SPEED_PERK not in owned
            ):
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _BUILD_SPEED_PERK,
                        "target_lifestyle_key": _STEWARDSHIP,
                        "expected": binding,
                        "reason": "feudal_build_speed_modifier_minus_30_percent",
                    },
                }
        return {**result, "status": "no_legal_minimum"}
    if at_peace is not True:
        return {**result, "status": "outside_admitted_scene"}
    if focus.get("presence") != "absent" or progress.get("presence") != "absent":
        return {**result, "status": "observation_unavailable"}
    if readiness.get("legal_focus_candidates_ready") is not True:
        return {**result, "status": "legal_candidates_unavailable"}
    focus_keys = _available_keys(
        snapshot.get("legal_focus_candidates"), _STEWARDSHIP
    )
    if focus_keys is None:
        return {**result, "status": "legal_candidates_unavailable"}
    if _WEALTH_FOCUS in focus_keys:
        # LIFE2 currently observes progress only for the current lifestyle.
        # When focus is absent, LIFE6 cannot capture its mandatory target
        # stewardship progress row from that source. A later exact read-only
        # producer must supply it before typed focus submission is possible.
        target_progress = snapshot.get("target_lifestyle_progress")
        if (
            not isinstance(target_progress, Mapping)
            or target_progress.get("presence") != "present"
            or target_progress.get("lifestyle_key") != _STEWARDSHIP
            or not isinstance(target_progress.get("unspent_perk_points"), int)
            or isinstance(target_progress.get("unspent_perk_points"), bool)
            or target_progress.get("unspent_perk_points") < 0
        ):
            return {**result, "status": "target_progress_source_unavailable"}
        return {
            **result,
            "status": "recommend_action",
            "selected_action": {
                "kind": "focus",
                "target_key": _WEALTH_FOCUS,
                "target_lifestyle_key": _STEWARDSHIP,
                "expected": binding,
                "reason": "feudal_monthly_income_modifier_10_percent",
            },
        }
    return {**result, "status": "no_legal_minimum"}
