"""Preventive observed-count policy; all scenes and contracts are synthetic."""
from copy import deepcopy

import pytest

from test_war_reinforcement_tradeoff_v1 import WarDriver
from xar_autoplayer.war_mercenary_consumer_v1 import (
    QUERY_CAPABILITY, HIRE_CAPABILITY, QUERY_STEP, HIRE_STEP,
    _LEDGER, _ledger, plan_war_mercenary_turn_v1,
)
from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame


REASON = "primary_defence_observed_raised_force_outnumbered"
CAPS = {QUERY_CAPABILITY, HIRE_CAPABILITY}


def scene(path, score=0):
    driver = WarDriver(path)
    driver.snapshot["active_wars"][0]["player_relative_war_score"] = score
    return driver


def plan(driver, step="life-advance", history=None):
    return plan_war_mercenary_turn_v1(driver, {"selected_step": step},
        snapshot=driver.snapshot, history=[] if history is None else history,
        bridge_capabilities=CAPS)


@pytest.mark.parametrize("score", [0, 12])
def test_nonnegative_primary_defence_compares_reserve_before_another_day(tmp_path, score):
    driver = scene(tmp_path, score)
    before = deepcopy(driver.snapshot)
    priority = observe_war_spending_priority_v1(driver.snapshot)
    war = priority["wars"][0]
    assert war["protect_cash_reasons"] == [REASON]
    assert (war["observed_player_raised_soldiers"], war["observed_enemy_raised_soldiers"]) == (800, 1500)
    assert priority["defer_new_economic_construction"] is True
    assert priority["war_win_probability"] is None
    chosen = plan(driver)
    assert chosen["selected_step"] == QUERY_STEP
    assert driver.snapshot == before
    assert driver.query_count == driver.hire_count == 0  # planning submits nothing


@pytest.mark.parametrize("missing", ["offensive", "nonprimary", "equal", "own_unknown",
    "enemy_unknown", "own_roster_unknown", "enemy_roster_unknown", "own_row_missing",
    "enemy_row_missing", "stale_strengths"])
def test_only_current_complete_observed_primary_defence_deficit_triggers(tmp_path, missing):
    driver = scene(tmp_path)
    snap, war = driver.snapshot, driver.snapshot["active_wars"][0]
    if missing == "offensive":
        war["player_side"] = "attacker"
    elif missing == "nonprimary":
        war["player_is_primary_war_leader"] = False
    elif missing == "equal":
        snap["player_armies"][0]["soldiers"] = 1500
    elif missing == "own_unknown":
        snap["player_armies"][0]["soldiers"] = None
    elif missing == "enemy_unknown":
        war["enemy_armies"][0]["soldiers"] = None
    elif missing == "own_roster_unknown":
        snap["player_armies"] = None
    elif missing == "enemy_roster_unknown":
        war["enemy_armies"] = None
    elif missing == "own_row_missing":
        snap["player_armies"].append(None)
    elif missing == "enemy_row_missing":
        war["enemy_armies"].append(None)
    else:
        snap["player_armies"][0]["soldiers"] = None
        war["enemy_armies"][0]["soldiers"] = None
        snap.update(army_strengths_status="available", army_strengths=[
            {"army_id": 1, "scope_role": "player", "status": "available", "current_soldiers": 800},
            {"army_id": 2, "scope_role": "active_war_enemy", "war_ids": [war["war_id"]],
             "status": "available", "current_soldiers": 1500}],
            army_strengths_queried_snapshot_id=snap["snapshot_id"],
            army_strengths_queried_revision=snap["revision"] - 1)
    priority = observe_war_spending_priority_v1(snap)
    assert REASON not in priority["wars"][0]["protect_cash_reasons"]
    assert plan(driver)["selected_step"] == "life-advance"
    assert driver.query_count == driver.hire_count == 0


def test_concrete_order_and_unresolved_hire_keep_original_priority(tmp_path):
    driver = scene(tmp_path)
    assert plan(driver, "move-army-1-to-2629")["selected_step"] == "move-army-1-to-2629"
    pending = {"company_id": 0, "source_frame": observed_frame(driver.snapshot),
               "pre_capture_epoch": 1, "status": "submission_unresolved"}
    write_json_atomic(tmp_path / _LEDGER, {
        "schema": "xar.war-mercenary-pending.v1", "pending": pending, "observed": []})
    assert plan(driver)["selected_step"] == QUERY_STEP  # independent receipt query only
    driver.execute_step(QUERY_STEP, expected_revision=driver.snapshot["revision"])
    driver.execute_step(QUERY_STEP, expected_revision=driver.snapshot["revision"])
    history = driver.take_snapshot()["native_command_history"]
    result = plan(driver, history=history)
    assert result["selected_step"] == "life-advance"
    assert result["war_mercenary_status"] == "pending_unresolved_never_resubmit"
    assert _ledger(tmp_path)["pending"] == pending and driver.hire_count == 0


@pytest.mark.parametrize("missing", ["finance", "native_quote"])
def test_current_deficit_never_bypasses_finance_or_native_hire_terms(tmp_path, missing):
    driver = scene(tmp_path)
    driver.execute_step(QUERY_STEP, expected_revision=driver.snapshot["revision"])
    if missing == "finance":
        driver.snapshot.pop("campaign_root_context")
    else:
        driver.recorded[-1][1]["player_mercenary_context"]["rows"][0]["final_terms"]["can_hire"] = False
    history = driver.take_snapshot()["native_command_history"]
    result = plan(driver, history=history)
    assert result["selected_step"] != HIRE_STEP
    assert result["selected_step"] == "life-advance" and driver.hire_count == 0
    assert _ledger(tmp_path)["pending"] is None
