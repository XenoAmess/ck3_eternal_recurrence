"""Emergency funding policy and ordinary Service; all game replies synthetic."""
import asyncio
from copy import deepcopy
from unittest.mock import patch

import pytest

from test_war_reinforcement_tradeoff_v1 import WarDriver, army, company, context
from xar_autoplayer.activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.construction_formal_consumer import plan_construction_private, ROOT_QUERY_STEP
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer import war_mercenary_consumer_v1 as consumer
from xar_autoplayer.war_strategic_reserve_v1 import assess_mercenary_reinforcement_v1
from xar_autoplayer.war_emergency_budget_v1 import observe_emergency_recovery_v1


def crisis(driver, *, level=1):
    snapshot = driver.snapshot
    snapshot["played_character_gold"]["raw"] = 35000000
    war = snapshot["active_wars"][0]
    war.update(player_relative_war_score=-60 if level == 1 else -90,
               primary_opponent_character_id=999)
    war["enemy_armies"][0].update(soldiers=2000, owner_character_id=999)
    if level == 2:
        war["objective_province_states"] = [{"province_id": 2629, "occupation_observable": True,
            "is_occupied": True, "occupying_character_id": 999}]
    return snapshot


def spending_for(driver):
    snapshot = driver.snapshot
    return observe_feast_start_budget_v1(snapshot, {
            "actor_character_id": snapshot["played_character"]["character_id"],
            "snapshot_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
            "post_snapshot_id": snapshot["snapshot_id"], "queried_revision": snapshot["revision"]},
            state_dir=driver.state_dir, campaign_root=snapshot["campaign_root_context"])


def assess(driver, *, price=28000000, troops=1400, ledger=None, spending=None):
    snapshot = driver.snapshot
    if spending is None:
        spending = spending_for(driver)
    return assess_mercenary_reinforcement_v1(snapshot,
        context(snapshot, [company(7, price, troops, 9999)]), campaign_root=snapshot["campaign_root_context"],
        procurement_ledger=ledger, spending_observation=spending)


def employed(driver, decision, identity="synthetic-emergency-a"):
    return {"action_request_id": identity, "status": "employment_observed", "company_id": 7,
        "source_frame": observed_frame(driver.snapshot), "pre_capture_epoch": 1,
        "pre_player_army_ids": [1], "decision": deepcopy(decision)}


def next_frame(driver):
    driver.snapshot["native_revision"] += 1
    driver.snapshot["revision"] += 1
    driver.snapshot["snapshot_id"] = "synthetic-next-emergency-frame"
    driver.snapshot["campaign_root_context"]["snapshot_revision"] = driver.snapshot["native_revision"]


def test_normal_budget_unchanged_and_high_loss_can_use_emergency_funds(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["played_character_gold"]["raw"] = 35000000
    ordinary = assess(driver)
    assert ordinary["selected_company_id"] is None
    assert ordinary["candidates"][0]["finance"]["required_gold_reserve_raw"] == 20000000
    assert ordinary["candidates"][0]["finance"]["maintenance_allocation_months"] == 18
    crisis(driver)
    decision = assess(driver)
    chosen = decision["selected_candidate"]
    assert chosen["company_id"] == 7 and chosen["gold_cost_raw"] == 28000000
    assert chosen["finance"]["maintenance_allocation_months"] == 6
    assert chosen["finance"]["required_gold_reserve_raw"] == 451200 * 6
    assert chosen["gold_after_hire_raw"] == 7000000  # below the ordinary200 policy
    assert chosen["emergency_budget_revision_v1"]["total_package_limit_raw"] == 32292800
    assert chosen["emergency_marginal_value_v1"]["after_company_arrival"] == 2200
    assert chosen["arrival_eta_days"] is None and chosen["battle_win_probability"] is None
    assert chosen["emergency_arrival_risk_v1"]["cannot_guarantee_arrival_before_loss"] is True


@pytest.mark.parametrize("case", ["no_major_title", "only_bad_score", "stale_root", "unknown_union",
    "spending_unavailable", "insufficient_marginal", "native_rejected", "native_cannot_afford", "incomplete_quote"])
def test_emergency_does_not_bypass_missing_inputs_or_native_guards(tmp_path, case):
    driver = WarDriver(tmp_path)
    crisis(driver)
    snapshot = driver.snapshot
    if case == "no_major_title":
        snapshot["campaign_root_context"]["primary_title"] = {"title_id": 9000}
    elif case == "only_bad_score":
        snapshot["player_armies"][0]["soldiers"] = 3000
    elif case == "stale_root":
        snapshot["campaign_root_context"]["snapshot_revision"] -= 1
    elif case == "unknown_union":
        snapshot["active_wars"][0]["enemy_armies"][0]["soldiers"] = None
    if case in {"native_rejected", "native_cannot_afford", "incomplete_quote"}:
        # Reuse the same real budget observer; replace only the synthetic native terms.
        from test_war_reinforcement_tradeoff_v1 import context as make_context
        value = make_context(snapshot, [company(7, 28000000, 1400, 9999)])
        if case == "native_rejected":
            value["rows"][0]["final_terms"]["can_hire"] = False
        elif case == "native_cannot_afford":
            value["rows"][0]["final_terms"]["can_afford"] = False
        else:
            value["rows"][0]["final_terms"]["resource_costs_raw"] = [28000000]
        spending = observe_feast_start_budget_v1(snapshot, {"actor_character_id": snapshot["played_character"]["character_id"],
            "snapshot_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
            "post_snapshot_id": snapshot["snapshot_id"], "queried_revision": snapshot["revision"]},
            state_dir=tmp_path, campaign_root=snapshot["campaign_root_context"])
        decision = assess_mercenary_reinforcement_v1(snapshot, value,
            campaign_root=snapshot["campaign_root_context"], spending_observation=spending)
    else:
        decision = assess(driver, troops=400 if case == "insufficient_marginal" else 1400,
            spending={"status": "unavailable"} if case == "spending_unavailable" else None)
    assert decision["selected_company_id"] is None


def test_emergency_epoch_is_locked_and_only_new_worse_level_can_expand(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    first = assess(driver)
    receipt = employed(driver, first)
    ledger = {"pending": None, "observed": [receipt]}
    next_frame(driver)
    # Later income or switching focus cannot refresh the original level1 cap.
    driver.snapshot["played_character_gold"]["raw"] = 20000000
    attempted = assess(driver, price=5000000, ledger=ledger)
    assert attempted["selected_company_id"] is None
    candidate = attempted["candidates"][0]
    assert candidate["emergency_budget_revision_v1"]["total_package_limit_raw"] == 32292800
    assert candidate["procurement_package_budget_v1"]["remaining_package_gold_raw"] == 4292800
    crisis(driver, level=2)
    driver.snapshot["played_character_gold"]["raw"] = 20000000
    second = assess(driver, price=6000000, ledger=ledger)
    chosen = second["selected_candidate"]
    assert chosen["emergency_budget_revision_v1"]["level"] == 2
    assert chosen["emergency_budget_revision_v1"]["epoch_id"] == receipt["decision"]["selected_candidate"]["emergency_budget_revision_v1"]["epoch_id"]
    assert chosen["emergency_budget_revision_v1"]["total_package_limit_raw"] == 35000000
    assert chosen["procurement_package_budget_v1"]["remaining_package_gold_raw"] == 7000000
    unknown = {"pending": {**receipt, "status": "submission_unresolved"}, "observed": []}
    assert assess(driver, price=6000000, ledger=unknown)["selected_company_id"] is None


def test_emergency_commitments_are_added_to_military_buffer_and_bad_revision_cannot_refresh(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    spending = spending_for(driver)
    spending["budget"]["reserved_raw"]["gold"] = 7000000
    decision = assess(driver, spending=spending)
    assert decision["selected_company_id"] is None
    assert decision["candidates"][0]["finance"]["required_gold_reserve_raw"] == 7000000 + 451200 * 6
    first = assess(driver)
    receipt = employed(driver, first)
    receipt["decision"]["selected_candidate"]["emergency_budget_revision_v1"]["level"] = True
    next_frame(driver)
    decision = assess(driver, price=1000000, ledger={"pending": None, "observed": [receipt]})
    assert decision["selected_company_id"] is None
    assert decision["candidates"][0]["procurement_package_budget_v1"]["reason"] == "same_package_emergency_revision_binding_unavailable"


def test_complete_quotes_compare_conditional_reversal_before_partial_deficit_closure(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    rows = [company(7, 28000000, 1400, 9999), company(8, 10000000, 800, 9999),
            company(9, 20000000, 1300, 9999), company(10, 5000000, 2000, 9999)]
    rows[-1]["final_terms"]["can_hire"] = False
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot, rows),
        campaign_root=driver.snapshot["campaign_root_context"], spending_observation=spending_for(driver))
    assert decision["selected_company_id"] == 9
    assert [row["company_id"] for row in decision["candidates"]] == [7, 8, 9, 10]
    assert "native_hire_or_affordability_rejected" in decision["candidates"][-1]["rejection_reasons"]
    assert all(row["emergency_marginal_value_v1"]["local_native_members_available"] is False for row in decision["candidates"])


def test_minus100_stays_active_and_highest_loss_emergency_is_focused(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    worst = deepcopy(driver.snapshot["active_wars"][0])
    worst["war_id"] = 991
    worst["player_relative_war_score"] = -100
    worst["enemy_armies"][0]["army_id"] = 992
    worst["objective_province_states"] = [{"province_id": 2629, "occupation_observable": True,
        "is_occupied": True, "occupying_character_id": 999}]
    driver.snapshot["active_wars"].append(worst)
    decision = assess(driver)
    selected = decision["selected_candidate"]
    assert selected["purpose_war_ids"] == [991]
    assert selected["emergency_budget_revision_v1"]["level"] == 2
    assert selected["comparison_enemy_current_soldiers"] == 4000
    evidence = selected["emergency_budget_revision_v1"]["policy_evidence"]
    assert evidence["trigger_evidence"]["war_resolution_verified"] is False
    assert evidence["global_hostile_scope"]["war_ids"] == [driver.snapshot["active_wars"][0]["war_id"], 991]


def test_major_direct_title_requires_native_tier_and_null_optional_siege_inputs_continue(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    root = driver.snapshot["campaign_root_context"]
    root["primary_title"] = {"title_id": 9000}
    root["held_title_partition"] = [{"title": {"title_id": 2230, "tier_raw": 2}}]
    driver.snapshot["active_wars"][0]["objective_province_states"] = [{
        "province_id": 2629, "siege_observable": True,
        "active_siege": {"days_left": 2}, "current_besieging_army_selection": None}]
    assert assess(driver)["selected_company_id"] is None
    root["held_title_partition"][0]["title"]["tier_raw"] = 3
    decision = assess(driver)
    assert decision["selected_company_id"] == 7
    evidence = decision["selected_candidate"]["emergency_budget_revision_v1"]["policy_evidence"]
    assert evidence["level"] == 1
    assert evidence["trigger_evidence"]["observed_risk_deadline_days"] is None


def test_real_registered_service_emergency_query_single_submit_and_unknown_no_retry(tmp_path):
    from mcp import Client
    driver = WarDriver(tmp_path)
    crisis(driver)
    from test_war_reinforcement_tradeoff_v1 import context as original_context
    def quotes(snapshot, rows=None, epoch=1):
        return original_context(snapshot, rows if rows is not None else [company(7, 28000000, 1400, 9999)], epoch)
    async def run():
        baseline = {"phase": "life_advance", "selected_step": "life-advance"}
        with (patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline),
              patch("test_war_reinforcement_tradeoff_v1.context", side_effect=quotes),
              patch.object(GameplayBridgeService, "_select_auto_camera_hotspot", return_value={"status": "unavailable", "available": False})):
            async with Client(mcp_server.create_server(driver)) as client:
                query = await client.call_tool("ck3_auto_turn", {})
                assert not query.is_error and query.structured_content["selected_step"] == consumer.QUERY_STEP
                hire = await client.call_tool("ck3_auto_turn", {})
                assert not hire.is_error and hire.structured_content["selected_step"] == consumer.HIRE_STEP
                assert driver.hire_count == 1
                selected = hire.structured_content["plan"]["war_mercenary_decision_v1"]["selected_candidate"]
                assert selected["emergency_budget_revision_v1"]["level"] == 1
                assert "危机资金等级1" in hire.structured_content["plan"]["war_decision_presentation_v1"]["reason"]
                saved = consumer._ledger(tmp_path)["pending"]
                assert saved["decision"]["selected_candidate"]["emergency_budget_revision_v1"] == selected["emergency_budget_revision_v1"]
                again = await client.call_tool("ck3_auto_turn", {})
                assert not again.is_error and driver.hire_count == 1
                assert consumer._ledger(tmp_path)["pending"] is not None
                assert hire.structured_content["result"]["payment_verified"] is False
    asyncio.run(run())


def test_recovery_defers_new_building_but_uses_existing_root_query(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver)
    first = assess(driver)
    receipt = employed(driver, first)
    ledger = {"schema": "xar.war-mercenary-pending.v1", "pending": None, "observed": [receipt]}
    write_json_atomic(tmp_path / "war-mercenary-pending-v1.json", ledger)
    next_frame(driver)
    driver.snapshot["active_wars"] = []
    driver.snapshot["played_character_gold"]["raw"] = 23000000
    root = driver.snapshot["campaign_root_context"]
    root["player_max_monthly_gold_maintenance_v1"]["value"]["raw"] = 2000000
    recovery = observe_emergency_recovery_v1(driver.snapshot, ledger, root)
    assert recovery["normal_reserve_target_raw"] == 36000000 and recovery["defer_new_economic_construction"]
    planned = {"revision": driver.snapshot["revision"], "plan": {"selected_step": "life-advance",
        "war_emergency_budget_recovery_v1": recovery}}
    with patch("xar_autoplayer.construction_formal_consumer.same_frame_construction_scope_v1", return_value={"status": "root_query_needed"}):
        query = plan_construction_private(driver, planned, driver.snapshot, [], {ROOT_QUERY_STEP})
        assert query["plan"]["selected_step"] == ROOT_QUERY_STEP
    with (patch("xar_autoplayer.construction_formal_consumer.same_frame_construction_scope_v1", return_value={"status": "admitted", "government_key": "feudal_government"}),
          patch("xar_autoplayer.bridge.domain_construction_private_transport_v1.query_construction_private", side_effect=AssertionError("unnecessary building quote"))):
        deferred = plan_construction_private(driver, planned, driver.snapshot, [], {"life-advance"})
        assert deferred["plan"]["selected_step"] == "life-advance"
        assert deferred["plan"]["construction_spending_deferred_v1"]["deferred_domain"] == "new_economic_construction"
    driver.snapshot["played_character_gold"]["raw"] = 40000000
    assert observe_emergency_recovery_v1(driver.snapshot, ledger, root)["defer_new_economic_construction"] is False
