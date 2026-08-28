"""Research admission policy for zero-intermediate-pause battle cruise.

This module does not submit a CK3 command.  It classifies one already
normalized, paused ``battle-control-v1`` frame for a future native
``run-until-terminal-or-sentinel`` arm.  Production admission remains
separate from candidate selection so an overwhelming live matrix cannot be
silently replaced by a ratio heuristic.
"""

from __future__ import annotations

BATTLE_TERMINAL_CRUISE_POLICY_VERSION = "battle-terminal-cruise-research-v1"
DEFAULT_DOMINANCE_MULTIPLIER = 4


def assess_battle_terminal_cruise(
    battle_frame: object,
    *,
    paused: object,
    map_ready: object,
    active_event_present: object,
    pending_interaction_present: object,
    all_controllable_army_ids: object,
    watched_army_ids: object,
    absolute_target_date_raw: object,
    speed_5_available: object,
    terminal_sentinel_implemented: object,
    terminal_sentinel_live_ready: object = False,
    overwhelming_matrix_live_ready: object = False,
    dominance_multiplier: int = DEFAULT_DOMINANCE_MULTIPLIER,
) -> dict[str, object]:
    """Classify a paused battle frame for a speed-5 terminal cruise.

    ``candidate_ready`` answers only whether the current battle decision can
    be pre-committed as hold-to-terminal. ``research_run_ready`` additionally
    requires a complete native watch set and an implemented sentinel.
    ``production_ready`` additionally requires sentinel live evidence.
    Dominance-based candidates also require an overwhelming-checkpoint
    matrix; a player-won pursuit is already outcome-locked and does not.
    The three levels are intentionally distinct.
    """

    if (
        isinstance(dominance_multiplier, bool)
        or not isinstance(dominance_multiplier, int)
        or dominance_multiplier < 2
    ):
        raise ValueError("dominance_multiplier must be an integer >= 2")

    controllable = _positive_unique_ids(all_controllable_army_ids)
    watched = _positive_unique_ids(watched_army_ids)
    watch_set_complete = (
        controllable is not None
        and watched is not None
        and bool(controllable)
        and set(controllable) == set(watched)
    )

    candidate_blockers: list[str] = []
    run_blockers: list[str] = []
    production_blockers: list[str] = []
    start_date_raw: int | None = None
    target_date_raw = _plain_int(absolute_target_date_raw)
    target_elapsed_days: int | None = None

    frame = battle_frame if isinstance(battle_frame, dict) else None
    if frame is None or frame.get("battle_control_ready") is not True:
        candidate_blockers.append("battle_control_frame_not_ready")
    elif (start_date_raw := _plain_int(frame.get("observed_date_raw"))) is None:
        candidate_blockers.append("battle_observed_date_unavailable")

    candidate_kind: str | None = None
    player_role: str | None = None
    opponent_role: str | None = None
    current_fighting_ratio_floor_met: bool | None = None
    side_strength_ratio_floor_met: bool | None = None
    player_current_fighting_raw: int | None = None
    opponent_current_fighting_raw: int | None = None
    player_side_strength_raw: int | None = None
    opponent_side_strength_raw: int | None = None

    if frame is not None and not candidate_blockers:
        side_index = _plain_int(frame.get("side_index"))
        if side_index == 0:
            player_role, opponent_role = "attacker", "defender"
        elif side_index == 1:
            player_role, opponent_role = "defender", "attacker"
        else:
            candidate_blockers.append("player_battle_side_unavailable")

        phase = frame.get("phase")
        winner = frame.get("winner_side")
        if frame.get("finalized") is True or phase == "done":
            candidate_blockers.append("battle_already_terminal")
        elif phase not in {"maneuver", "main", "pursuit"}:
            candidate_blockers.append("battle_phase_not_cruise_eligible")

        if phase in {"maneuver", "main"} and winner != "none":
            candidate_blockers.append("preterminal_winner_state_changed")
        elif phase == "pursuit":
            if winner not in {"attacker", "defender"}:
                candidate_blockers.append("pursuit_winner_unavailable")
            elif player_role is not None and winner != player_role:
                candidate_blockers.append("pursuit_player_not_winner")

        if player_role is not None and opponent_role is not None:
            player_side = frame.get(player_role)
            opponent_side = frame.get(opponent_role)
            if not isinstance(player_side, dict) or not isinstance(
                opponent_side, dict
            ):
                candidate_blockers.append("battle_side_metrics_unavailable")
            else:
                player_current_fighting_raw = _nonnegative_int(
                    player_side.get("derived_current_fighting_raw")
                )
                opponent_current_fighting_raw = _nonnegative_int(
                    opponent_side.get("derived_current_fighting_raw")
                )
                player_side_strength_raw = _nonnegative_int(
                    player_side.get("side_strength_raw")
                )
                opponent_side_strength_raw = _nonnegative_int(
                    opponent_side.get("side_strength_raw")
                )
                if None in {
                    player_current_fighting_raw,
                    opponent_current_fighting_raw,
                    player_side_strength_raw,
                    opponent_side_strength_raw,
                }:
                    candidate_blockers.append(
                        "battle_side_metrics_unavailable"
                    )

        if not candidate_blockers:
            assert player_current_fighting_raw is not None
            assert opponent_current_fighting_raw is not None
            assert player_side_strength_raw is not None
            assert opponent_side_strength_raw is not None
            if phase == "pursuit":
                candidate_kind = "pursuit_cleanup"
            elif (
                player_current_fighting_raw > 0
                and opponent_current_fighting_raw == 0
            ):
                candidate_kind = "opponent_fighting_pool_exhausted"
            else:
                current_fighting_ratio_floor_met = _ratio_floor_met(
                    player_current_fighting_raw,
                    opponent_current_fighting_raw,
                    dominance_multiplier,
                )
                side_strength_ratio_floor_met = _ratio_floor_met(
                    player_side_strength_raw,
                    opponent_side_strength_raw,
                    dominance_multiplier,
                )
                if not current_fighting_ratio_floor_met:
                    candidate_blockers.append(
                        "current_fighting_dominance_not_met"
                    )
                if not side_strength_ratio_floor_met:
                    candidate_blockers.append(
                        "side_strength_dominance_not_met"
                    )
                if not candidate_blockers:
                    candidate_kind = "double_dominance_hold"

    if paused is not True:
        run_blockers.append("paused_prearm_frame_required")
    if map_ready is not True:
        run_blockers.append("map_ready_prearm_frame_required")
    if active_event_present is not False:
        run_blockers.append("active_event_requires_decision")
    if pending_interaction_present is not False:
        run_blockers.append("pending_interaction_requires_decision")
    if (
        start_date_raw is None
        or target_date_raw is None
        or target_date_raw <= start_date_raw
        or (target_date_raw - start_date_raw) % 24 != 0
    ):
        run_blockers.append("positive_whole_day_absolute_target_required")
    else:
        target_elapsed_days = (target_date_raw - start_date_raw) // 24
    if not watch_set_complete:
        run_blockers.append("all_controllable_armies_must_be_watched")
    if speed_5_available is not True:
        run_blockers.append("speed_5_unavailable")
    if terminal_sentinel_implemented is not True:
        run_blockers.append("terminal_sentinel_not_implemented")

    candidate_ready = not candidate_blockers
    research_run_ready = candidate_ready and not run_blockers

    overwhelming_matrix_required = candidate_kind in {
        "double_dominance_hold",
        "opponent_fighting_pool_exhausted",
    }
    if terminal_sentinel_live_ready is not True:
        production_blockers.append("terminal_sentinel_live_matrix_pending")
    if (
        overwhelming_matrix_required
        and overwhelming_matrix_live_ready is not True
    ):
        production_blockers.append("overwhelming_checkpoint_matrix_pending")
    production_ready = research_run_ready and not production_blockers

    return {
        "policy_version": BATTLE_TERMINAL_CRUISE_POLICY_VERSION,
        "candidate_ready": candidate_ready,
        "research_run_ready": research_run_ready,
        "production_ready": production_ready,
        "candidate_kind": candidate_kind,
        "overwhelming_matrix_required": overwhelming_matrix_required,
        "selected_action": (
            "run_speed_5_until_terminal_or_sentinel"
            if research_run_ready
            else None
        ),
        "sentinel_mode": "terminal" if research_run_ready else None,
        "requested_speed": 5 if research_run_ready else None,
        "dominance_multiplier": dominance_multiplier,
        "player_role": player_role,
        "opponent_role": opponent_role,
        "player_current_fighting_raw": player_current_fighting_raw,
        "opponent_current_fighting_raw": opponent_current_fighting_raw,
        "current_fighting_ratio_floor_met": (
            current_fighting_ratio_floor_met
        ),
        "player_side_strength_raw": player_side_strength_raw,
        "opponent_side_strength_raw": opponent_side_strength_raw,
        "side_strength_ratio_floor_met": side_strength_ratio_floor_met,
        "all_controllable_army_ids": controllable,
        "watched_army_ids": watched,
        "watch_set_complete": watch_set_complete,
        "start_date_raw": start_date_raw,
        "absolute_target_date_raw": target_date_raw,
        "absolute_target_elapsed_days": target_elapsed_days,
        "candidate_blockers": candidate_blockers,
        "run_blockers": run_blockers,
        "production_blockers": production_blockers,
        "expected_external_intermediate_pause_count": (
            0 if research_run_ready else None
        ),
        "post_stop_rule": (
            "terminal/removal -> terminal journal query; any other sentinel "
            "reason -> one paused rich query and replan"
            if research_run_ready
            else None
        ),
    }


def _ratio_floor_met(
    player_raw: int, opponent_raw: int, multiplier: int
) -> bool:
    return opponent_raw > 0 and player_raw >= opponent_raw * multiplier


def _positive_unique_ids(value: object) -> list[int] | None:
    if not isinstance(value, (list, tuple)):
        return None
    result: list[int] = []
    for item in value:
        parsed = _plain_int(item)
        if parsed is None or parsed <= 0 or parsed in result:
            return None
        result.append(parsed)
    return sorted(result)


def _plain_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _nonnegative_int(value: object) -> int | None:
    parsed = _plain_int(value)
    return parsed if parsed is not None and parsed >= 0 else None


__all__ = [
    "BATTLE_TERMINAL_CRUISE_POLICY_VERSION",
    "DEFAULT_DOMINANCE_MULTIPLIER",
    "assess_battle_terminal_cruise",
]
