"""Synthetic follow-up and package policy, no live game or native endpoint."""
from copy import deepcopy

import pytest

from test_war_reinforcement_tradeoff_v1 import WarDriver, army, company, context
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer import war_mercenary_consumer_v1 as consumer
from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1
from xar_autoplayer.war_strategic_reserve_v1 import (
    assess_mercenary_reinforcement_v1, observe_first_raised_inventory_v1,
    observe_procurement_package_budget_v1,
)


def purchase_fixture(driver):
    # Only these numbers mirror the separately recorded R8 quote/wallet delta.
    # All employment, source-frame changes and inventory scenes here are fixtures.
    driver.snapshot["played_character_gold"]["raw"] = 43489448
    driver.snapshot["player_armies"] = [army(1, 844)]
    quote = context(driver.snapshot, [company(152, 21100000, 856)])
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, quote,
        campaign_root=driver.snapshot["campaign_root_context"])
    assert decision["selected_company_id"] == 152
    return {"action_request_id": "synthetic-contract-a", "company_id": 152,
            "source_frame": observed_frame(driver.snapshot), "status": "employment_observed",
            "pre_capture_epoch": 1, "pre_player_army_ids": [1], "decision": decision,
            "payment_verified": False, "army_creation_verified": False}


def after_frame(driver, *, new_army=True):
    snapshot = deepcopy(driver.snapshot)
    snapshot["revision"] += 1
    snapshot["native_revision"] += 1
    snapshot["snapshot_id"] = "fixture-after-hire"
    snapshot["campaign_root_context"]["snapshot_revision"] = snapshot["native_revision"]
    snapshot["played_character_gold"]["raw"] = 22389448
    if new_army:
        snapshot["player_armies"].append(army(4, 856))
    return snapshot


@pytest.mark.parametrize("later", ["moves", "merges"])
def test_first_independent_inventory_survives_cold_move_or_merge(tmp_path, later):
    driver = WarDriver(tmp_path)
    employed = purchase_fixture(driver)
    post = after_frame(driver)
    first = observe_first_raised_inventory_v1(post, employed)
    assert first["observed_new_player_armies"][0]["army_id"] == 4
    assert first["company_to_new_army_binding_verified"] is False
    employed["first_raised_inventory_observation_v1"] = first
    write_json_atomic(tmp_path / "war-mercenary-pending-v1.json",
        {"schema": "xar.war-mercenary-pending.v1", "pending": None, "observed": [employed]})
    cold = WarDriver(tmp_path)
    cold.snapshot = deepcopy(post)
    if later == "moves":
        cold.snapshot["player_armies"][1]["current_province_id"] = 8755
    else:
        cold.snapshot["player_armies"] = [army(1, 1700)]
    planned = consumer.plan_war_mercenary_turn_v1(cold, {"selected_step": "life-advance"},
        snapshot=cold.snapshot, history=[], bridge_capabilities={consumer.QUERY_CAPABILITY})
    assert planned["selected_step"] == consumer.QUERY_STEP
    assert "no_duplicate_hire" not in planned.get("war_mercenary_status", "")
    saved = consumer._ledger(tmp_path)["observed"][0]
    assert saved["first_raised_inventory_observation_v1"] == first
    assert saved["source_frame"] == employed["source_frame"]
    assert saved["pre_player_army_ids"] == [1]
    assert saved["payment_verified"] is False and saved["army_creation_verified"] is False


@pytest.mark.parametrize("case", ["not_independent", "no_first_observation", "wrong_actor", "empty_marker"])
def test_inventory_milestone_requires_actual_first_fresh_observation(tmp_path, case):
    driver = WarDriver(tmp_path)
    employed = purchase_fixture(driver)
    post = after_frame(driver)
    if case == "not_independent":
        post["native_revision"] = employed["source_frame"]["native_revision"]
    elif case == "no_first_observation":
        post["player_armies"][1]["current_province_id"] = 8755
    else:
        marker = observe_first_raised_inventory_v1(post, employed)
        employed["first_raised_inventory_observation_v1"] = marker
        post["player_armies"] = [army(1, 1700)]
        if case == "wrong_actor":
            marker["source_frame"]["played_character_id"] += 1
        else:
            marker["observed_new_player_armies"] = []
    assert observe_first_raised_inventory_v1(post, employed) is None


def test_package_budget_keeps_original_half_cash_envelope(tmp_path):
    driver = WarDriver(tmp_path)
    employed = purchase_fixture(driver)
    post = after_frame(driver)
    ledger = {"observed": [employed], "pending": None}
    budget = observe_procurement_package_budget_v1(post, ledger, purpose_war_ids=[100663323])
    assert budget["original_package_gold_limit_raw"] == 21744724
    assert budget["committed_contract_quote_gold_raw"] == 21100000
    assert budget["remaining_package_gold_raw"] == 644724
    assert post["played_character_gold"]["raw"] - 20000000 == 2389448
    # A synthetic fresh 10g offer fits the CURRENT reserve/share cap but exceeds
    # the original package remainder. This prevents repeated-half-cash spending.
    root = post["campaign_root_context"]
    market = context(post, [company(99, 1000000, 1000)])
    decision = assess_mercenary_reinforcement_v1(post, market, campaign_root=root, procurement_ledger=ledger)
    assert decision["selected_company_id"] is None
    assert decision["candidates"][0]["finance"]["retains_military_allocation"] is True
    assert "contract_exceeds_remaining_same_purpose_package_budget" in decision["candidates"][0]["rejection_reasons"]
    affordable = context(post, [company(99, 500000, 1000)])
    allowed = assess_mercenary_reinforcement_v1(post, affordable, campaign_root=root, procurement_ledger=ledger)
    assert allowed["selected_company_id"] == 99
    assert allowed["selected_candidate"]["procurement_package_budget_v1"] == budget
    assert allowed["arrival_eta_days"] is None and allowed["battle_win_probability"] is None


def test_overlapping_wars_cannot_reset_package_by_changing_purpose(tmp_path):
    driver = WarDriver(tmp_path)
    employed = purchase_fixture(driver)
    post = after_frame(driver)
    second_war = {**deepcopy(post["active_wars"][0]), "war_id": 134217796, "targeted_title_ids": [2231]}
    post["active_wars"].append(second_war)
    budget = observe_procurement_package_budget_v1(post, {"observed": [employed]}, purpose_war_ids=[134217796])
    assert budget["remaining_package_gold_raw"] == 644724
    # A later contract made while both wars were active retains connectivity
    # to the old anchor after the original war disappears from active_wars.
    second = deepcopy(employed)
    second["action_request_id"] = "synthetic-contract-b"
    second["decision"]["selected_candidate"].update(gold_cost_raw=500000, purpose_war_ids=[134217796])
    second["decision"]["war_spending_priority"]["primary_war_hostile_union_v1"]["war_ids"] = [100663323, 134217796]
    post["active_wars"] = [second_war]
    combined = observe_procurement_package_budget_v1(post, {"observed": [employed, second]}, purpose_war_ids=[134217796])
    assert combined["original_package_gold_limit_raw"] == 21744724
    assert combined["remaining_package_gold_raw"] == 144724
    disjoint = deepcopy(post)
    disjoint["active_wars"][0]["war_id"] = 999
    assert observe_procurement_package_budget_v1(disjoint, {"observed": [employed, second]}, purpose_war_ids=[999])["status"] == "no_prior_package"


def test_missing_legacy_package_anchor_does_not_invent_a_new_budget(tmp_path):
    driver = WarDriver(tmp_path)
    employed = purchase_fixture(driver)
    employed["decision"]["selected_candidate"].pop("cash_opportunity_cost_limit_raw")
    assert observe_procurement_package_budget_v1(after_frame(driver), {"observed": [employed]},
        purpose_war_ids=[100663323])["status"] == "unavailable"


def test_unknown_pending_still_blocks_any_second_hire(tmp_path):
    driver = WarDriver(tmp_path)
    pending = purchase_fixture(driver)
    pending.update(company_id=0, status="submission_unresolved", pre_capture_epoch=0)
    write_json_atomic(tmp_path / "war-mercenary-pending-v1.json",
        {"schema": "xar.war-mercenary-pending.v1", "pending": pending, "observed": []})
    driver.execute_step(consumer.QUERY_STEP, expected_revision=driver.snapshot["revision"])
    snapshot = driver.take_snapshot()
    planned = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"}, snapshot=snapshot,
        history=snapshot["native_command_history"], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
    assert planned["war_mercenary_status"] == "pending_unresolved_never_resubmit"
    assert planned["selected_step"] == "life-advance" and driver.hire_count == 0


def test_inventory_can_be_observed_during_army_order_before_employer_readback(tmp_path):
    driver = WarDriver(tmp_path)
    pending = purchase_fixture(driver)
    pending["status"] = "submission_unresolved"
    write_json_atomic(tmp_path / "war-mercenary-pending-v1.json",
        {"schema": "xar.war-mercenary-pending.v1", "pending": pending, "observed": []})
    driver.snapshot = after_frame(driver)
    order = "move-army-1-to-2619"
    planned = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": order},
        snapshot=driver.snapshot, history=[], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
    assert planned["selected_step"] == order and driver.hire_count == 0
    saved = consumer._ledger(tmp_path)
    first = saved["pending"]["first_raised_inventory_observation_v1"]
    assert first["observed_new_player_armies"][0]["army_id"] == 4
    assert saved["pending"]["status"] == "submission_unresolved" and saved["observed"] == []
    # The army can merge before the independent market employer capture.
    driver.snapshot["player_armies"] = [army(1, 1700)]
    driver.query_count = 1
    driver.execute_step(consumer.QUERY_STEP, expected_revision=driver.snapshot["revision"])
    after_market = context(driver.snapshot, [company(152, 21100000, 856)], epoch=2)
    after_market["rows"][0]["employer_id"] = driver.snapshot["played_character"]["character_id"]
    driver.recorded[-1][1]["player_mercenary_context"] = after_market
    snapshot = driver.take_snapshot()
    receipt = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"},
        snapshot=snapshot, history=snapshot["native_command_history"], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
    assert receipt["war_mercenary_status"] == "employment_independently_observed"
    observed = consumer._ledger(tmp_path)["observed"][0]
    assert observed["first_raised_inventory_observation_v1"] == first
    assert observed["payment_verified"] is False and observed["army_creation_verified"] is False


def test_minus100_active_war_remains_in_global_survival_risk(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["active_wars"][0]["player_relative_war_score"] = -100
    priority = observe_war_spending_priority_v1(driver.snapshot)
    war = priority["wars"][0]
    assert war["active_war_observed"] is True and war["war_resolution_verified"] is False
    assert war["new_procurement_suppressed_by_score_policy"] is True
    assert "score_defeat_threshold_reached_war_still_observed_active" in war["protect_cash_reasons"]
    assert priority["primary_war_hostile_union_v1"]["observed_current_soldiers"] == 1500
