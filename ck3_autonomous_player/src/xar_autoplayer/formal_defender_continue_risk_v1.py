"""Typed, read-only continuation risk envelope for a CK3 defender war.

This contract preserves bounded *observations*. It never converts soldier
counts, current score, a siege timer, or route order into a win probability,
loss amount, utility value, or war-exit action.
"""

from __future__ import annotations

from collections.abc import Mapping
import re


POLICY = "formal-defender-continue-risk-envelope-v1"
RAW_TICKS_PER_DAY = 24
_SHA = re.compile(r"[0-9A-F]{64}\Z")
_FRAME_KEYS = frozenset({
    "snapshot_id", "revision", "native_revision", "date_raw",
    "episode_run_id", "connection_generation", "played_character_id",
    "war_id", "player_relative_war_score",
})
_CONTACT_KEYS = frozenset({
    "source_frame", "source_sha256", "subject_army_id",
    "target_province_id", "horizon_start_date_raw", "horizon_end_date_raw",
    "one_day_contact_free", "conflicts", "first_waypoint_arrival_date_raw",
    "subject_target_arrival_date_raw", "offsite_target_arrivals",
})
_SIEGE_KEYS = frozenset({
    "source_frame", "source_sha256", "province_id", "besieging_army_ids",
    "remaining_days_estimate",
})
_OFFSITE_KEYS = frozenset({"army_id", "arrival_date_raw"})


def observe_defender_continue_risk_v1(
    *, frame: Mapping[str, object],
    contact: Mapping[str, object] | None = None,
    siege: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return current-frame conditional bounds and explicit missing inputs.

    ``contact`` and ``siege`` are normalized by a caller from already verified
    native evidence. This function checks their full frame identity but does
    not itself attest that a source artifact was produced by CK3.
    """
    frozen = _frame(frame)
    date_raw = frozen["date_raw"]
    blockers = [
        "current_cb_material_terms_required",
        "current_asset_exposure_and_valuation_required",
        "finite_horizon_tail_loss_upper_required",
        "finite_horizon_war_cash_upper_required",
        "complete_encounter_participant_scope_required",
    ]

    contact_result: dict[str, object] = {
        "status": "typed_unavailable",
        "reason": "same_frame_route_contact_required",
        "current_orders_only": True,
        "contact_free_through_raw": None,
        "first_waypoint_outside_proven_window": None,
        "offsite_target_arrival_order": "unavailable",
        "offsite_roster_complete_proven": False,
        "target_arrival_date_raw": None,
    }
    if contact is not None:
        candidate = _contact(contact, frozen)
        free = (
            candidate["one_day_contact_free"] is True
            and not candidate["conflicts"]
            and candidate["horizon_start_date_raw"] == date_raw
            and candidate["horizon_end_date_raw"]
            == date_raw + RAW_TICKS_PER_DAY
        )
        arrivals = candidate["offsite_target_arrivals"]
        target_arrival = candidate["subject_target_arrival_date_raw"]
        if arrivals and target_arrival is not None:
            arrival_order = (
                "listed_offsite_hostile_may_precede_target_entry"
                if any(row["arrival_date_raw"] <= target_arrival for row in arrivals)
                else "listed_offsite_arrivals_later_under_current_orders"
            )
        else:
            arrival_order = "unavailable"
        first_waypoint = candidate["first_waypoint_arrival_date_raw"]
        contact_result = {
            "status": (
                "bounded_current_orders_one_day_only" if free
                else "contact_risk_or_horizon_unavailable"
            ),
            "reason": None if free else "no_verified_contact_free_game_day",
            "current_orders_only": True,
            "contact_free_through_raw": (
                candidate["horizon_end_date_raw"] if free else None
            ),
            "first_waypoint_outside_proven_window": (
                first_waypoint > candidate["horizon_end_date_raw"]
                if free and first_waypoint is not None else None
            ),
            "offsite_target_arrival_order": arrival_order,
            "offsite_roster_complete_proven": False,
            "target_arrival_date_raw": target_arrival,
            "source_sha256": candidate["source_sha256"],
        }
        if not free:
            blockers.append("same_frame_contact_free_day_not_proven")
        if arrival_order == "listed_offsite_hostile_may_precede_target_entry":
            blockers.append("offsite_hostile_may_join_by_target_entry")
    else:
        blockers.append("same_frame_route_contact_required")

    siege_result: dict[str, object] = {
        "status": "typed_unavailable",
        "reason": "same_frame_siege_clock_required",
        "completion_estimate_raw": None,
        "completion_upper_bound_proven": False,
    }
    if siege is not None:
        candidate = _siege(siege, frozen)
        if contact is not None and candidate["province_id"] != contact["target_province_id"]:
            raise ValueError("siege clock and route target crossed provinces")
        siege_result = {
            "status": "current_timer_estimate_only",
            "reason": None,
            "province_id": candidate["province_id"],
            "besieging_army_ids": candidate["besieging_army_ids"],
            "remaining_days_estimate": candidate["remaining_days_estimate"],
            "completion_estimate_raw": (
                date_raw + candidate["remaining_days_estimate"]
                * RAW_TICKS_PER_DAY
            ),
            "completion_upper_bound_proven": False,
            "source_sha256": candidate["source_sha256"],
        }
    else:
        blockers.append("same_frame_siege_clock_required")

    return {
        "policy": POLICY,
        "status": "partial_bounded_observation_no_exit_comparison",
        "read_only": True,
        "frame": frozen,
        "current_score": {
            "status": "observed_current_only",
            "player_relative_war_score": frozen["player_relative_war_score"],
            "future_score_bound": None,
            "trend_inferred": False,
        },
        "contact": contact_result,
        "siege": siege_result,
        "asset_exposure": {
            "status": "typed_unavailable",
            "reason": "current_material_effects_and_asset_valuation_required",
            "tail_loss_upper_raw": None,
        },
        "continuation_loss_upper_raw": None,
        "continuation_win_probability": None,
        "surrender_vs_continue_utility_interval": None,
        "material_comparison_ready": False,
        "recommended_outcome": None,
        "action_literal": None,
        "blockers": sorted(set(blockers)),
    }


def _frame(value: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _FRAME_KEYS:
        raise ValueError("complete defender war frame required")
    result = dict(value)
    for key in ("revision", "native_revision", "date_raw",
                "connection_generation", "played_character_id", "war_id",
                "player_relative_war_score"):
        if type(result[key]) is not int:
            raise ValueError(f"frame {key} must be integer")
    if (not isinstance(result["snapshot_id"], str) or not result["snapshot_id"]
            or not isinstance(result["episode_run_id"], str)
            or not result["episode_run_id"]
            or result["revision"] <= 0 or result["native_revision"] <= 0
            or result["connection_generation"] <= 0
            or result["played_character_id"] <= 0 or result["war_id"] <= 0):
        raise ValueError("invalid defender war frame identity")
    return result


def _source(value: Mapping[str, object], frame: dict[str, object],
            keys: frozenset[str], name: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"{name} schema invalid")
    result = dict(value)
    if result["source_frame"] != frame:
        raise ValueError(f"{name} crossed native frame")
    if not isinstance(result["source_sha256"], str) or not _SHA.fullmatch(result["source_sha256"]):
        raise ValueError(f"{name} source SHA-256 required")
    return result


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be positive integer")
    return value


def _contact(value: Mapping[str, object], frame: dict[str, object]) -> dict[str, object]:
    result = _source(value, frame, _CONTACT_KEYS, "contact")
    _positive(result["subject_army_id"], "subject_army_id")
    _positive(result["target_province_id"], "target_province_id")
    start = result["horizon_start_date_raw"]
    end = result["horizon_end_date_raw"]
    if (type(start) is not int or type(end) is not int or start != frame["date_raw"]
            or end <= start or end > start + RAW_TICKS_PER_DAY
            or type(result["one_day_contact_free"]) is not bool
            or not isinstance(result["conflicts"], list)):
        raise ValueError("contact horizon is not a bounded current game day")
    for key in ("first_waypoint_arrival_date_raw", "subject_target_arrival_date_raw"):
        arrival = result[key]
        if arrival is not None and (type(arrival) is not int or arrival <= start):
            raise ValueError(f"{key} must be future raw date or null")
    first = result["first_waypoint_arrival_date_raw"]
    target = result["subject_target_arrival_date_raw"]
    if first is not None and target is not None and first > target:
        raise ValueError("first waypoint cannot arrive after target")
    rows = result["offsite_target_arrivals"]
    if not isinstance(rows, list):
        raise ValueError("offsite arrivals must be a list")
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != _OFFSITE_KEYS:
            raise ValueError("offsite arrival schema invalid")
        army_id = _positive(row["army_id"], "offsite army ID")
        if (army_id == result["subject_army_id"] or army_id in seen
                or type(row["arrival_date_raw"]) is not int
                or row["arrival_date_raw"] <= start):
            raise ValueError("offsite arrival ID/date invalid")
        seen.add(army_id)
    return result


def _siege(value: Mapping[str, object], frame: dict[str, object]) -> dict[str, object]:
    result = _source(value, frame, _SIEGE_KEYS, "siege")
    _positive(result["province_id"], "siege province ID")
    armies = result["besieging_army_ids"]
    if not isinstance(armies, list) or not armies:
        raise ValueError("siege besieger list invalid")
    for army_id in armies:
        _positive(army_id, "besieging army ID")
    if len(armies) != len(set(armies)):
        raise ValueError("siege besieger list invalid")
    days = result["remaining_days_estimate"]
    if type(days) is not int or days < 0 or days > (2**31 - 1) // RAW_TICKS_PER_DAY:
        raise ValueError("siege timer estimate invalid")
    return result


__all__ = ["observe_defender_continue_risk_v1"]
