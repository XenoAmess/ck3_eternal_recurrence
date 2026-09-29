"""One-action feudal lifestyle recommendation for a controlled private trial.

This consumes the exact private LIFE2 snapshot shape. It does not submit a
command or register a production capability; the single CK3 owner must first
validate the native source and later-state receipt in a bounded live run.
"""

from __future__ import annotations

from typing import Mapping


POLICY_ID = "g2-m4-lifestyle-min-v1"
WAR_PERK_POLICY_ID = "g2-lifestyle-wartime-stewardship-perk-v1"
WAR_MARTIAL_PERK_POLICY_ID = "g2-lifestyle-wartime-martial-perk-v1"
WAR_DIPLOMACY_PERK_POLICY_ID = "g2-lifestyle-wartime-diplomacy-perk-v1"
_STEWARDSHIP = "stewardship_lifestyle"
_BUILD_COST_PERK = "cutting_corners_perk"
_BUILD_SPEED_PERK = "professional_workforce_perk"
_CAPITAL_DEVELOPMENT_PERK = "centralization_perk"
_COLLECT_TAXES_PERK = "tax_man_perk"
_WEALTH_FOCUS = "stewardship_wealth_focus"
_MARTIAL_FOCUS = "martial_authority_focus"
_MARTIAL = "martial_lifestyle"
_MARTIAL_CONTROL_PERK = "serve_the_crown_perk"
_DIPLOMACY = "diplomacy_lifestyle"
_DIPLOMACY_GIFT_PERK = "thoughtful_perk"
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


def choose_first_focus_target(
    *, wealth: Mapping[str, object] | None,
    martial: Mapping[str, object] | None,
    actor_traits: Mapping[str, object] | None,
    at_peace: bool,
) -> dict[str, object]:
    """Compare two exact final verdicts for a focusless actor's first focus.

    A current unspent wealth point is a realized near-term opportunity during
    peace. A martial education and active war favor authority over the wealth
    income modifier for the initial 60-month commitment. XP values are kept
    as observed opportunity inputs, never estimated from age.
    """

    def target(query: Mapping[str, object] | None, key: str,
               lifestyle: str) -> dict[str, object] | None:
        if not isinstance(query, Mapping) or query.get("status") != "observed":
            return None
        if not isinstance(query.get("native_legal"), bool):
            return None
        if query.get("target_key") != key or query.get("target_lifestyle_key") != lifestyle:
            return None
        progress = query.get("target_lifestyle_progress")
        if not isinstance(progress, Mapping) or progress.get("presence") != "present":
            return None
        fields = ("xp_total_raw", "xp_within_level_raw", "xp_per_level",
                  "unspent_perk_points", "used_perk_points")
        if not all(isinstance(progress.get(field), int)
                   and not isinstance(progress.get(field), bool)
                   and progress[field] >= 0 for field in fields):
            return None
        if (progress["xp_per_level"] == 0 or
                progress["xp_within_level_raw"] >=
                progress["xp_per_level"] * 100000):
            return None
        return {
            "native_legal": query.get("native_legal") is True,
            "progress": {field: progress[field] for field in fields},
        }

    wealth_row = target(wealth, _WEALTH_FOCUS, _STEWARDSHIP)
    martial_row = target(martial, _MARTIAL_FOCUS, _MARTIAL)
    observed = {"wealth": wealth_row, "martial": martial_row}
    traits = actor_traits.get("observed_keys") if isinstance(actor_traits, Mapping) \
        and actor_traits.get("status") == "available" else None
    martial_ranks = (
        [rank for rank in range(1, 6)
         if isinstance(traits, list) and f"education_martial_{rank}" in traits]
    )
    rank = max(martial_ranks, default=0)
    martial_role = rank >= (4 if at_peace else 3)
    wealth_point_due = bool(
        wealth_row is not None and martial_row is not None
        and wealth_row["progress"]["unspent_perk_points"] > 0
        and martial_row["progress"]["unspent_perk_points"] == 0
    )
    only_final_legal_martial = bool(
        wealth_row is not None and not wealth_row["native_legal"]
    )
    if (wealth_row is not None and martial_row is not None
            and martial_row["native_legal"]
            and (only_final_legal_martial or (
                martial_role and (not at_peace or not wealth_point_due)
            ))):
        return {
            "status": "selected", "target_key": _MARTIAL_FOCUS,
            "reason": "only_observed_final_legal_focus" if only_final_legal_martial
            else "martial_education_and_war_objective" if not at_peace
            else "high_martial_education_without_ready_wealth_point",
            "martial_education_rank": rank,
            "at_peace": at_peace,
            "commitment_months": 60,
            "observed_target_progress": observed,
        }
    if wealth_row is not None and wealth_row["native_legal"]:
        return {
            "status": "selected", "target_key": _WEALTH_FOCUS,
            "reason": "ready_wealth_point_in_peace" if wealth_point_due and at_peace
            else "existing_income_baseline",
            "martial_education_rank": rank,
            "at_peace": at_peace,
            "commitment_months": 60,
            "observed_target_progress": observed,
        }
    return {
        "status": "no_final_legal_focus_or_source_unavailable",
        "target_key": None,
        "martial_education_rank": rank,
        "at_peace": at_peace,
        "observed_target_progress": observed,
    }


def choose_min_feudal_lifestyle_action(
    snapshot: Mapping[str, object] | None,
    *,
    feudal_scope_admitted: bool | None,
    at_peace: bool | None,
    collect_taxes_active: bool | None = None,
    allow_wartime_perk: bool = False,
    allow_wartime_initial_focus: bool = False,
    preferred_focus_target_key: str = _WEALTH_FOCUS,
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
        perk_keys = _available_keys(
            snapshot.get("legal_perk_candidates"), current_lifestyle
        )
        if perk_keys is None:
            return {**result, "status": "legal_candidates_unavailable"}
        if current_lifestyle == _MARTIAL:
            if at_peace is False:
                result["policy_id"] = WAR_MARTIAL_PERK_POLICY_ID
            points = progress.get("unspent_perk_points")
            if not isinstance(points, int) or isinstance(points, bool) or points < 0:
                return {**result, "status": "observation_unavailable"}
            if (points > 0 and _MARTIAL_CONTROL_PERK in perk_keys
                    and _MARTIAL_CONTROL_PERK not in owned):
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _MARTIAL_CONTROL_PERK,
                        "target_lifestyle_key": _MARTIAL,
                        "expected": binding,
                        "reason": "feudal_county_control_growth_add_0_3",
                    },
                }
        if current_lifestyle == _DIPLOMACY:
            if at_peace is False:
                result["policy_id"] = WAR_DIPLOMACY_PERK_POLICY_ID
            points = progress.get("unspent_perk_points")
            if not isinstance(points, int) or isinstance(points, bool) or points < 0:
                return {**result, "status": "observation_unavailable"}
            if (points > 0 and _DIPLOMACY_GIFT_PERK in perk_keys
                    and _DIPLOMACY_GIFT_PERK not in owned):
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _DIPLOMACY_GIFT_PERK,
                        "target_lifestyle_key": _DIPLOMACY,
                        "expected": binding,
                        "reason": "send_gift_opinion_gain_doubled",
                    },
                }
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
            if (
                points > 0
                and _BUILD_SPEED_PERK in owned
                and _CAPITAL_DEVELOPMENT_PERK in perk_keys
                and _CAPITAL_DEVELOPMENT_PERK not in owned
            ):
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _CAPITAL_DEVELOPMENT_PERK,
                        "target_lifestyle_key": _STEWARDSHIP,
                        "expected": binding,
                        "reason": "capital_county_monthly_development_growth_add_0_3",
                    },
                }
            if (
                points > 0
                and collect_taxes_active is True
                and all(key in owned for key in (
                    _BUILD_COST_PERK, _BUILD_SPEED_PERK,
                    _CAPITAL_DEVELOPMENT_PERK,
                ))
                and _COLLECT_TAXES_PERK in perk_keys
                and _COLLECT_TAXES_PERK not in owned
            ):
                return {
                    **result,
                    "status": "recommend_action",
                    "selected_action": {
                        "kind": "perk",
                        "target_key": _COLLECT_TAXES_PERK,
                        "target_lifestyle_key": _STEWARDSHIP,
                        "expected": binding,
                        "reason": "active_collect_taxes_effectiveness_plus_25_percent",
                    },
                }
        return {**result, "status": "no_legal_minimum"}
    if at_peace is not True and not allow_wartime_initial_focus:
        return {**result, "status": "outside_admitted_scene"}
    if focus.get("presence") != "absent" or progress.get("presence") != "absent":
        return {**result, "status": "observation_unavailable"}
    if readiness.get("legal_focus_candidates_ready") is not True:
        return {**result, "status": "legal_candidates_unavailable"}
    focus_targets = {
        _WEALTH_FOCUS: _STEWARDSHIP,
        _MARTIAL_FOCUS: _MARTIAL,
    }
    target_lifestyle = focus_targets.get(preferred_focus_target_key)
    if target_lifestyle is None:
        return {**result, "status": "unsupported_focus_target"}
    focus_keys = _available_keys(
        snapshot.get("legal_focus_candidates"), target_lifestyle
    )
    if focus_keys is None:
        return {**result, "status": "legal_candidates_unavailable"}
    if preferred_focus_target_key in focus_keys:
        # LIFE2 currently observes progress only for the current lifestyle.
        # When focus is absent, LIFE6 cannot capture its mandatory target
        # stewardship progress row from that source. A later exact read-only
        # producer must supply it before typed focus submission is possible.
        target_progress = snapshot.get("target_lifestyle_progress")
        if (
            not isinstance(target_progress, Mapping)
            or target_progress.get("presence") != "present"
            or target_progress.get("lifestyle_key") != target_lifestyle
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
                "target_key": preferred_focus_target_key,
                "target_lifestyle_key": target_lifestyle,
                "expected": binding,
                "reason": (
                    "first_focus_martial_control_and_war_role"
                    if preferred_focus_target_key == _MARTIAL_FOCUS
                    else "feudal_monthly_income_modifier_10_percent"
                ),
            },
        }
    return {**result, "status": "no_legal_minimum"}
