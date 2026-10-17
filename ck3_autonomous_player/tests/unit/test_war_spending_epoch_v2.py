"""Later offline epoch: real no-purchase frame and independent multi-war cases."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_war_reinforcement_tradeoff_v1 import WarDriver, army, company, context
from xar_autoplayer.construction_formal_consumer import plan_construction_private
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer.war_mercenary_consumer_v1 import (
    QUERY_CAPABILITY, HIRE_CAPABILITY, QUERY_STEP, plan_war_mercenary_turn_v1,
)
from xar_autoplayer.war_reinforcement_tradeoff_v1 import (
    assess_mercenary_reinforcement_v1, observe_mercenary_purchase_model_need_v1,
    observe_war_spending_priority_v1,
)


def test_actual_heir_current_advantage_skips_market_without_claiming_war_safety(tmp_path):
    source = Path(__file__).resolve().parents[3] / "docs/ck3-native-ai/evidence/p51-war-epoch-actual-review-2026-10-18.json"
    evidence = json.loads(source.read_bytes())
    snapshot = evidence["same_frame_actual_snapshot_projection"]
    driver = WarDriver(tmp_path)
    plan = plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"}, snapshot=snapshot,
                                    history=[], bridge_capabilities={QUERY_CAPABILITY, HIRE_CAPABILITY})
    assert plan["selected_step"] == "life-advance" and driver.query_count == 0
    priority = plan["war_spending_priority_v1"]
    assert priority["wars"][0]["observed_player_raised_soldiers"] == 1358
    assert priority["wars"][0]["observed_enemy_raised_soldiers"] == 751
    assert priority["defer_new_economic_construction"] is True
    assert priority["primary_war_hostile_union_v1"]["future_or_unraised_reinforcements_bounded"] is False
    assert plan["war_mercenary_purchase_model_need_v1"]["overall_war_safe"] is None
    assert plan["war_mercenary_purchase_model_need_v1"]["query_can_change_current_headcount_flip_model"] is False


def test_pending_employer_observation_bypasses_no_deficit_market_gate(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["player_armies"][0]["soldiers"] = 2000
    write_json_atomic(tmp_path / "war-mercenary-pending-v1.json", {
        "schema": "xar.war-mercenary-pending.v1", "observed": [],
        "pending": {"source_frame": observed_frame(driver.snapshot), "pre_capture_epoch": 1, "company_id": 0}})
    result = plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"}, snapshot=driver.snapshot,
                                      history=[], bridge_capabilities={QUERY_CAPABILITY, HIRE_CAPABILITY})
    assert result["selected_step"] == QUERY_STEP


def test_unknown_current_strength_keeps_existing_query_path_and_no_safety_claim(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["active_wars"][0]["enemy_armies"][0]["soldiers"] = None
    priority = observe_war_spending_priority_v1(driver.snapshot)
    need = observe_mercenary_purchase_model_need_v1(priority)
    assert need["query_can_change_current_headcount_flip_model"] is True
    assert need["overall_war_safe"] is None


def two_wars(driver, *, shared=False, unknown_second=False):
    driver.snapshot["player_armies"][0]["soldiers"] = 1000
    first = driver.snapshot["active_wars"][0]
    first["enemy_armies"] = [army(2, 700, controllable=False)]
    second = deepcopy(first)
    second.update(war_id=100663324, targeted_title_ids=[2231], player_relative_war_score=-5)
    second["enemy_armies"] = ([deepcopy(first["enemy_armies"][0])] if shared else
                               [army(3, None if unknown_second else 600, controllable=False)])
    driver.snapshot["active_wars"].append(second)


def test_two_own_wars_cannot_each_spend_the_same_army_full_strength(tmp_path):
    driver = WarDriver(tmp_path)
    two_wars(driver)
    priority = observe_war_spending_priority_v1(driver.snapshot)
    assert all(war["raised_force_deficit"] is False for war in priority["wars"])
    assert priority["primary_war_hostile_union_v1"]["observed_current_soldiers"] == 1300
    assert priority["primary_war_hostile_union_v1"]["shared_force_deficit"] is True
    assert observe_mercenary_purchase_model_need_v1(priority)["query_can_change_current_headcount_flip_model"] is True
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot, [
        company(1, price=10_000_000, troops=200), company(2, price=15_000_000, troops=500)]),
        campaign_root=driver.snapshot["campaign_root_context"])
    assert decision["selected_company_id"] == 2
    assert decision["selected_candidate"]["comparison_enemy_current_soldiers"] == 1300
    assert decision["selected_candidate"]["multiple_primary_wars_share_force"] is True
    assert decision["battle_win_probability"] is None


def test_same_hostile_army_in_two_wars_is_counted_once(tmp_path):
    driver = WarDriver(tmp_path)
    two_wars(driver, shared=True)
    priority = observe_war_spending_priority_v1(driver.snapshot)
    union = priority["primary_war_hostile_union_v1"]
    assert union["observed_current_soldiers"] == 700 and union["unique_army_ids"] == [2]
    assert union["shared_force_deficit"] is False
    assert observe_mercenary_purchase_model_need_v1(priority)["query_can_change_current_headcount_flip_model"] is False


def test_unknown_other_war_prevents_promising_shared_force_reinforcement(tmp_path):
    driver = WarDriver(tmp_path)
    two_wars(driver, unknown_second=True)
    driver.snapshot["active_wars"][0]["enemy_armies"][0]["soldiers"] = 1500
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot),
                                               campaign_root=driver.snapshot["campaign_root_context"])
    assert decision["selected_company_id"] is None
    assert "multi_war_hostile_union_unknown_no_shared_force_allocation" in decision["candidates"][0]["rejection_reasons"]


@pytest.mark.parametrize("pressure", ["known_own_siege", "known_opponent_occupation", "unknown_occupation"])
def test_actual_hostile_pressure_can_keep_cash_before_score_turns_negative(tmp_path, pressure):
    driver = WarDriver(tmp_path)
    war = driver.snapshot["active_wars"][0]
    war.update(player_relative_war_score=12, primary_opponent_character_id=777)
    if pressure == "known_own_siege":
        war["enemy_armies"][0].update(army_state="sieging", siege_province_in_player_subrealm=True)
    elif pressure == "known_opponent_occupation":
        war["objective_province_states"] = [{"province_id": 2623, "occupation_observable": True,
                                              "is_occupied": True, "occupying_character_id": 777}]
    else:
        war["objective_province_states"] = []
        war["enemy_armies"][0].update(army_state="sieging", siege_province_in_player_subrealm=None)
    priority = observe_war_spending_priority_v1(driver.snapshot)
    assert priority["defer_new_economic_construction"] is (pressure != "unknown_occupation")
    if pressure != "unknown_occupation":
        baseline = {"revision": driver.snapshot["revision"], "plan": {"selected_step": "life-advance"}}
        result = plan_construction_private(driver, baseline, driver.snapshot, [], {"life-advance"})
        assert result["plan"]["selected_step"] == "life-advance"
        assert result["plan"]["construction_spending_deferred_v1"]["deferred_domain"] == "new_economic_construction"
        assert driver.requests == []


def test_primary_title_cash_priority_uses_only_same_frame_root_without_claiming_transfer(tmp_path):
    driver = WarDriver(tmp_path)
    two_wars(driver)
    root = driver.snapshot["campaign_root_context"]
    root.update(primary_title={"title_id": 2231}, held_title_partition=[{"title": {"title_id": 2231}}])
    priority = observe_war_spending_priority_v1(driver.snapshot, campaign_root=root)
    assert priority["cash_protection_priority_war_ids"][0] == 100663324
    assert priority["cash_priority_does_not_assign_armies"] is True
    assert all(war["defeat_title_transfer_verified"] is False for war in priority["wars"])
    stale = {**root, "snapshot_revision": root["snapshot_revision"] - 1}
    priority = observe_war_spending_priority_v1(driver.snapshot, campaign_root=stale)
    assert all(war["target_stakes_v1"]["primary_title_targeted"] is None for war in priority["wars"])


def test_current_complete_retreat_keeps_cash_without_inventing_a_historical_battle_loss(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["active_wars"][0]["player_relative_war_score"] = 12
    driver.snapshot["player_armies"][0].update(retreating=True, army_state="retreating")
    priority = observe_war_spending_priority_v1(driver.snapshot)
    assert priority["defer_new_economic_construction"] is True
    assert "entire_observed_own_raised_force_currently_retreating" in priority["wars"][0]["protect_cash_reasons"]
    # One retreating detachment does not establish total operational absence.
    driver.snapshot["player_armies"].append(army(3, 1000))
    assert observe_war_spending_priority_v1(driver.snapshot)["defer_new_economic_construction"] is False
