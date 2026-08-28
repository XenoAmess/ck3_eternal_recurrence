from __future__ import annotations

from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.battle_terminal_cruise_policy import (
    BATTLE_TERMINAL_CRUISE_POLICY_VERSION,
    assess_battle_terminal_cruise,
)


def _frame(
    *,
    phase: str = "main",
    winner: str = "none",
    finalized: bool = False,
    player_side_index: int = 0,
    player_current: int = 400,
    opponent_current: int = 100,
    player_strength: int = 800,
    opponent_strength: int = 200,
) -> dict[str, object]:
    player = {
        "derived_current_fighting_raw": player_current,
        "side_strength_raw": player_strength,
    }
    opponent = {
        "derived_current_fighting_raw": opponent_current,
        "side_strength_raw": opponent_strength,
    }
    return {
        "battle_control_ready": True,
        "observed_date_raw": 10_000,
        "side_index": player_side_index,
        "phase": phase,
        "winner_side": winner,
        "finalized": finalized,
        "attacker": player if player_side_index == 0 else opponent,
        "defender": player if player_side_index == 1 else opponent,
    }


def _assess(
    frame: object,
    **overrides: object,
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "paused": True,
        "map_ready": True,
        "active_event_present": False,
        "pending_interaction_present": False,
        "all_controllable_army_ids": [101, 202],
        "watched_army_ids": [202, 101],
        "absolute_target_date_raw": 10_000 + 45 * 24,
        "speed_5_available": True,
        "terminal_sentinel_implemented": True,
    }
    arguments.update(overrides)
    return assess_battle_terminal_cruise(frame, **arguments)


def test_exact_double_dominance_is_a_research_candidate_only() -> None:
    result = _assess(_frame())

    assert result["policy_version"] == BATTLE_TERMINAL_CRUISE_POLICY_VERSION
    assert result["candidate_ready"] is True
    assert result["research_run_ready"] is True
    assert result["production_ready"] is False
    assert result["candidate_kind"] == "double_dominance_hold"
    assert result["selected_action"] == (
        "run_speed_5_until_terminal_or_sentinel"
    )
    assert result["requested_speed"] == 5
    assert result["expected_external_intermediate_pause_count"] == 0
    assert result["production_blockers"] == [
        "terminal_sentinel_live_matrix_pending",
        "overwhelming_checkpoint_matrix_pending",
    ]


def test_both_current_fighting_and_side_strength_must_meet_floor() -> None:
    current_short = _assess(_frame(player_current=399))
    strength_short = _assess(_frame(player_strength=799))

    assert current_short["candidate_ready"] is False
    assert current_short["candidate_blockers"] == [
        "current_fighting_dominance_not_met"
    ]
    assert strength_short["candidate_ready"] is False
    assert strength_short["candidate_blockers"] == [
        "side_strength_dominance_not_met"
    ]


def test_player_defender_polarity_is_respected() -> None:
    result = _assess(_frame(player_side_index=1))

    assert result["candidate_ready"] is True
    assert result["player_role"] == "defender"
    assert result["opponent_role"] == "attacker"
    assert result["player_current_fighting_raw"] == 400
    assert result["opponent_current_fighting_raw"] == 100


def test_pursuit_cleanup_needs_no_dominance_ratio() -> None:
    result = _assess(
        _frame(
            phase="pursuit",
            winner="defender",
            player_current=1,
            opponent_current=1000,
            player_strength=1,
            opponent_strength=1000,
        )
    )

    assert result["candidate_ready"] is True
    assert result["candidate_kind"] == "pursuit_cleanup"
    assert result["current_fighting_ratio_floor_met"] is None
    assert result["side_strength_ratio_floor_met"] is None


def test_exhausted_opponent_is_terminal_imminent_without_ratio() -> None:
    result = _assess(
        _frame(
            player_current=1,
            opponent_current=0,
            player_strength=1,
            opponent_strength=0,
        )
    )

    assert result["candidate_ready"] is True
    assert result["candidate_kind"] == "opponent_fighting_pool_exhausted"


@pytest.mark.parametrize(
    ("override", "blocker"),
    [
        ({"paused": False}, "paused_prearm_frame_required"),
        ({"map_ready": False}, "map_ready_prearm_frame_required"),
        ({"active_event_present": True}, "active_event_requires_decision"),
        (
            {"pending_interaction_present": True},
            "pending_interaction_requires_decision",
        ),
        (
            {"watched_army_ids": [101]},
            "all_controllable_armies_must_be_watched",
        ),
        ({"speed_5_available": False}, "speed_5_unavailable"),
        (
            {"absolute_target_date_raw": 10_001},
            "positive_whole_day_absolute_target_required",
        ),
        (
            {"terminal_sentinel_implemented": False},
            "terminal_sentinel_not_implemented",
        ),
    ],
)
def test_prearm_and_native_run_requirements_are_explicit(
    override: dict[str, object], blocker: str
) -> None:
    result = _assess(_frame(), **override)

    assert result["candidate_ready"] is True
    assert result["research_run_ready"] is False
    assert blocker in result["run_blockers"]
    assert result["selected_action"] is None


def test_production_requires_both_live_matrices() -> None:
    one_missing = _assess(
        _frame(),
        terminal_sentinel_live_ready=True,
    )
    ready = _assess(
        _frame(),
        terminal_sentinel_live_ready=True,
        overwhelming_matrix_live_ready=True,
    )

    assert one_missing["production_ready"] is False
    assert one_missing["production_blockers"] == [
        "overwhelming_checkpoint_matrix_pending"
    ]
    assert ready["production_ready"] is True
    assert ready["production_blockers"] == []


@pytest.mark.parametrize(
    "frame",
    [
        None,
        {"battle_control_ready": False},
        _frame(phase="done", finalized=True),
        _frame(phase="main", winner="attacker"),
        _frame(phase="pursuit", winner="none"),
    ],
)
def test_malformed_or_non_actionable_battle_frames_do_not_admit(
    frame: object,
) -> None:
    result = _assess(frame)

    assert result["candidate_ready"] is False
    assert result["research_run_ready"] is False
    assert result["candidate_blockers"]


@pytest.mark.parametrize("value", [True, 1, "4", 0, -1])
def test_dominance_multiplier_must_be_an_integer_at_least_two(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        _assess(_frame(), dominance_multiplier=value)
