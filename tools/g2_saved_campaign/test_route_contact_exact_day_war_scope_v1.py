"""Actual AUTO79 scope projection plus bounded hypothetical failure cases."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SOURCE = HERE / "route_contact_exact_day_war_scope_v1.py"
FIXTURE = HERE / "fixtures/p28_auto79_route_contact_war_scope_actual.json"
spec = importlib.util.spec_from_file_location("route_contact_exact_day_war_scope_v1", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
observe = module.observe_route_contact_exact_day_war_scope_v1


def actual():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def args(case):
    return {
        "before": case["war_progress_before"],
        "after": case["war_progress_after"],
        "planned_wars": case["planned_wars"],
        "selected_hostile_ids": case["selected_hostile_ids"],
        "subject_army_id": case["subject_army_id"],
        "start_date_raw": case["starting_date_raw"],
        "end_date_raw": case["ending_date_raw"],
    }


def test_actual_auto79_excludes_only_explicit_native_retreaters():
    case = actual()
    assert case["result_status"] == "postcondition"
    assert case["paused"] is True and case["final_screen"] == "map_hud"
    assert case["native_clock"] == {
        "completed_daily_ticks": 1, "overshoot_days": 0,
        "trigger_reasons": ["date_deadline"], "pause_observed": True,
    }
    observed = observe(**args(case))
    before = case["war_progress_before"]["wars"]
    enemies = [row for war in before for row in war["enemy_armies"]]
    assert len(enemies) == 12
    assert len([row for row in enemies if row["retreating"] is True]) == 11
    assert observed["selected_hostile_ids"] == [
        row["army_id"] for row in enemies if row["retreating"] is not True]
    assert len(observed["excluded_observed_retreating_ids"]) == 11
    assert observed["starting_war_ids"] == observed["ending_war_ids"]
    assert observed["war_scope_transition_observed"] is False
    assert observed["action_credit"] is False
    assert observed["war_outcome_credit"] is False
    assert observed["material_credit"] is False
    assert case["replay_allowed"] is False


@pytest.mark.parametrize("change", ["unselected_nonretreater", "unknown_retreat_bit",
    "missing_retreat_bit", "selected_marked_retreating", "wrong_planned_war",
    "missing_subject", "wrong_after_date", "duplicate_after_war", "malformed_after_roster"])
def test_scope_and_after_readback_fail_closed(change):
    case = actual()
    before = case["war_progress_before"]["wars"][0]
    after = case["war_progress_after"]["wars"][0]
    retreating = next(row for row in before["enemy_armies"] if row["retreating"] is True)
    selected = next(row for row in before["enemy_armies"] if row["army_id"] in case["selected_hostile_ids"])
    if change == "unselected_nonretreater":
        retreating["retreating"] = False
    elif change == "unknown_retreat_bit":
        retreating["retreating"] = None
    elif change == "missing_retreat_bit":
        del retreating["retreating"]
    elif change == "selected_marked_retreating":
        selected["retreating"] = True
    elif change == "wrong_planned_war":
        case["planned_wars"][0]["war_id"] += 1
    elif change == "missing_subject":
        before["player_armies"].clear()
    elif change == "wrong_after_date":
        case["war_progress_after"]["date_raw"] += 24
    elif change == "duplicate_after_war":
        case["war_progress_after"]["wars"].append(deepcopy(after))
    else:
        after["enemy_armies"] = None
    with pytest.raises(ValueError):
        observe(**args(case))


def test_public_cunit_zero_remains_a_valid_identifier():
    case = actual()
    before = case["war_progress_before"]["wars"][0]
    case["subject_army_id"] = 0
    before["player_armies"][0]["army_id"] = 0
    assert observe(**args(case))["status"] == "observed_starting_scope"
    case = actual()
    before = case["war_progress_before"]["wars"][0]
    selected_id = case["selected_hostile_ids"][0]
    next(row for row in before["enemy_armies"] if row["army_id"] == selected_id)["army_id"] = 0
    case["selected_hostile_ids"] = [0]
    assert observe(**args(case))["selected_hostile_ids"] == [0]


def test_natural_war_transition_preserves_date_observation_only():
    case = actual()
    case["war_progress_after"]["wars"] = []
    terminal = observe(**args(case))
    assert terminal["war_scope_transition_observed"] is True
    assert terminal["war_outcome_credit"] is False
    case = actual()
    added = {"war_id": max(w["war_id"] for w in case["war_progress_after"]["wars"]) + 1,
             "player_armies": [], "enemy_armies": []}
    case["war_progress_after"]["wars"].append(added)
    new_war = observe(**args(case))
    assert new_war["war_scope_transition_observed"] is True
    assert new_war["action_credit"] is False
