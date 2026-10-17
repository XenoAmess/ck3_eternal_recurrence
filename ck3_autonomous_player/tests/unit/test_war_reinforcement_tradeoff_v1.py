"""Synthetic normal Service closure plus one frozen actual losing-war projection."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from test_g2_normal_construction_cli_service_compound_v1 import NormalConstructionFixtureDriver
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, plan_construction_private, write_construction_ledger,
)
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer.war_mercenary_consumer_v1 import (
    HIRE_CAPABILITY, HIRE_STEP, QUERY_CAPABILITY, QUERY_STEP,
    ROOT_CAPABILITY, ROOT_STEP,
    plan_war_mercenary_turn_v1, submit_war_mercenary_v1,
)
from xar_autoplayer.war_reinforcement_tradeoff_v1 import (
    assess_mercenary_reinforcement_v1, observe_war_spending_priority_v1,
)


def army(identity=1, soldiers=800, province=2623, **updates):
    return {"army_id": identity, "soldiers": soldiers, "current_province_id": province,
            "controllable": True, "in_combat": False, "retreating": False,
            "move_target_observable": False, "move_target_province_id": None,
            "route_province_ids": [], "route_source_count": 0,
            "route_read_status": "complete_empty", "army_state": "regular", **updates}


def company(identity=0, price=15_000_000, troops=1200, spawn=2623):
    return {"company_id": identity, "employer_id": None, "manager_slot_index": identity,
            "troop_strength": {"available": True, "unavailable_reason": None, "current_soldiers": troops},
            "final_terms": {"available": True, "unavailable_reason": None,
                "can_hire": True, "can_afford": True, "payment_status": 2,
                "resource_scale": 100000, "resource_costs_raw": [price] + [0] * 9,
                "hire_duration_months": 36, "can_hire_reasons_available": True,
                "can_hire_reason_literal": "", "can_afford_reasons_available": True,
                "can_afford_reason_literal": ""},
            "location": {"company_home_title_id": 10, "company_home_province_id": 2632,
                "hire_auto_raise_province_id": spawn, "actor_active_war_count": 1,
                "hire_auto_raise_attempted_in_active_war": True,
                "company_home_ready": True, "company_home_failure": "none",
                "company_home_source": "synthetic native callback",
                "hire_auto_raise_position_ready": True, "hire_auto_raise_position_failure": "none",
                "hire_auto_raise_position_source": "synthetic native selector"},
            "composition_v1": {"available": True, "unavailable_reason": None,
                "company_id": identity, "holder_available": True,
                "holder_unavailable_reason": None, "holder_character_id": 456,
                "regiment_count": 1, "covered_regiment_count": 1,
                "current_regiment_soldiers": troops, "maximum_regiment_soldiers": troops,
                "positive_siege_tier_current_soldiers": 0, "maximum_siege_tier_raw": 0,
                "regiments": [{"ordinal": 0, "persistent_regiment_id": 12,
                    "current_soldiers": troops, "maximum_soldiers": troops,
                    "type_status": "not_maa", "maa_type_key": None, "siege_tier_raw": None}]},
            "readiness_v1": {"composition_ready": True, "hire_terms_ready": True, "hire_ready": True}}


def context(snapshot, rows=None, epoch=1):
    return {"schema": "ck3_12004_player_mercenary_context_v1",
            "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
            "actor_character_id": snapshot["played_character"]["character_id"],
            "date_raw": snapshot["date_raw"], "capture_epoch": epoch,
            "read_only": True, "native_hire_mode": 1, "available": True,
            "unavailable_reason": None, "rows": rows if rows is not None else [company()]}


class WarDriver(NormalConstructionFixtureDriver):
    def __init__(self, directory):
        super().__init__(directory)
        self.snapshot["active_wars"] = [{
            "war_id": 100663323, "player_side": "defender",
            "player_is_primary_war_leader": True, "player_relative_war_score": -12,
            "targeted_title_ids": [2230], "enemy_armies": [army(2, 1500, 2629, controllable=False)]}]
        self.snapshot["player_armies"] = [army()]
        self.snapshot["campaign_root_context"] = {
            "status": "available", "player_character_id": self.snapshot["played_character"]["character_id"],
            "snapshot_revision": self.snapshot["native_revision"], "date_raw": self.snapshot["date_raw"],
            "readiness": {"ready": True},
            "player_monthly_gold_income": {"raw": 592266, "scale": 100000},
            "player_max_monthly_gold_maintenance_v1": {
                "status": "available", "value": {"raw": 451200, "scale": 100000}}}
        self.query_count = self.hire_count = self.advance_count = 0
        self.employed = False

    def capabilities(self):
        return {"action_steps": ["life-advance", QUERY_STEP, HIRE_STEP],
                "bridge_capabilities": [QUERY_CAPABILITY, HIRE_CAPABILITY]}

    def execute_step(self, step, *, expected_revision):
        if step == QUERY_STEP:
            self._war_mercenary_query_frame_v1 = observed_frame(self.snapshot)
            self.query_count += 1
            value = context(self.snapshot, epoch=self.query_count)
            if self.employed:
                value["rows"][0]["employer_id"] = self.snapshot["played_character"]["character_id"]
            result = {"step": step, "accepted": True, "status": "completed", "read_only": True,
                      "query_sequence": self.query_count, "snapshot_revision": self.snapshot["native_revision"],
                      "date_raw": self.snapshot["date_raw"], "player_mercenary_context": value,
                      "mercenary_query_source_frame_v1": observed_frame(self.snapshot)}
            self.recorded.append((step, result))
            return result
        self.advance_count += 1
        return {"step": step, "accepted": True, "status": "completed"}

    def hire_mercenary_v1(self, *, company_id, expected_revision):
        self.hire_count += 1
        return {"step": HIRE_STEP, "accepted": True, "status": "submitted_verification_pending",
                "mercenary_hire": {"company_id": company_id, "after_state_observed": False}}


def test_actual_losing_defence_keeps_war_clock_and_skips_building_quote(tmp_path):
    packet = json.loads((Path(__file__).resolve().parents[3] /
        "docs/ck3-native-ai/evidence/p50-current-war-risk-input-2026-10-18.json").read_text(encoding="utf-8"))
    snapshot = packet["snapshot"]
    priority = observe_war_spending_priority_v1(snapshot)
    assert priority["defer_new_economic_construction"] is True
    war = priority["wars"][0]
    assert war["war_id"] == 100663323 and war["player_relative_war_score"] == -12
    assert war["possible_defensive_target_title_ids"] == [2230]
    assert war["observed_player_raised_soldiers"] is None
    assert war["observed_enemy_raised_soldiers"] is None
    driver = WarDriver(tmp_path)
    baseline = {"revision": snapshot["revision"], "plan": {
        "phase": "normal-war-clock", "selected_step": "life-advance"}}
    result = plan_construction_private(driver, baseline, snapshot, [], {"life-advance"})
    assert result["plan"]["selected_step"] == "life-advance"
    assert result["plan"]["construction_spending_deferred_v1"]["original_selected_step"] == "life-advance"
    assert driver.requests == []  # no optional quote or cash query before preserving the war turn
    planned = plan_war_mercenary_turn_v1(driver, baseline["plan"], snapshot=snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY, HIRE_CAPABILITY})
    assert planned["selected_step"] == QUERY_STEP


def test_cheapest_adequate_local_company_changes_count_balance_without_a_win_claim(tmp_path):
    driver = WarDriver(tmp_path)
    rows = [company(3, 5_000_000, 200), company(2, 10_000_000, 1300, 99),
            company(1, 18_000_000, 1800), company(0, 15_000_000, 1200)]
    value = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot, rows),
                                             campaign_root=driver.snapshot["campaign_root_context"])
    assert value["selected_company_id"] == 0  # full CompanyID zero is legitimate
    assert value["selected_candidate"]["friendly_staging_soldiers"] == 800
    assert value["selected_candidate"]["reinforced_staging_soldiers"] == 2000
    assert value["arrival_eta_days"] is None and value["battle_win_probability"] is None
    assert value["postcondition_verified"] is False
    budget = value["selected_candidate"]["finance"]
    assert budget["contract_months"] == 36 and budget["contract_gold_raw"] == 15_000_000
    assert budget["maintenance_allocation_raw"] == 451200 * 18
    assert budget["required_gold_reserve_raw"] == 20_000_000
    assert budget["gross_less_maximum_military_raw"] == 141066
    assert budget["gross_less_maximum_military_is_net_income"] is False
    assert budget["future_gross_income_credited_raw"] == 0


def test_actual_normal_query_strengths_survive_null_sem_counts_and_reach_a_hypothetical_hire(tmp_path):
    packet = json.loads((Path(__file__).resolve().parents[3] /
        "docs/ck3-native-ai/evidence/p50-actual-operational-strength-2026-10-18.json").read_text(encoding="utf-8"))
    snapshot = packet["snapshot"]
    assert all(row["soldiers"] is None for row in snapshot["player_armies"])
    priority = observe_war_spending_priority_v1(snapshot)
    assert priority["wars"][0]["observed_player_raised_soldiers"] == 1351
    assert priority["wars"][0]["observed_enemy_raised_soldiers"] == 1575
    assert priority["wars"][0]["existing_operational_strength_balance_v1"] == snapshot["active_wars"][0]["actual_existing_strength_balance"]
    # Only the operational inputs above are actual. Market and current finance
    # below are explicitly synthetic to qualify the new decision path offline.
    synthetic = WarDriver(tmp_path)
    snapshot = deepcopy(snapshot)
    snapshot["played_character_gold"] = {"raw": 41336412, "scale": 100000}
    finance = deepcopy(synthetic.snapshot["campaign_root_context"])
    finance.update(player_character_id=snapshot["played_character"]["character_id"],
                   snapshot_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"])
    decision = assess_mercenary_reinforcement_v1(snapshot, context(snapshot), campaign_root=finance)
    assert decision["selected_company_id"] == 0
    assert decision["selected_candidate"]["reinforced_staging_soldiers"] == 2551
    assert decision["selected_candidate"]["numerical_balance_reversed_war_ids"] == [100663323]
    assert decision["selected_candidate"]["finance"]["cash_only_maximum_military_runway"]["whole_months"] == 58
    stale = deepcopy(snapshot)
    stale["army_strengths_queried_revision"] += 1
    assert observe_war_spending_priority_v1(stale)["wars"][0]["observed_player_raised_soldiers"] is None
    assert assess_mercenary_reinforcement_v1(stale, context(stale), campaign_root=finance)["selected_company_id"] is None


def test_high_maintenance_changes_the_cash_decision_even_when_200_gold_remains(tmp_path):
    driver = WarDriver(tmp_path)
    root = driver.snapshot["campaign_root_context"]
    root["player_max_monthly_gold_maintenance_v1"]["value"]["raw"] = 2_000_000
    value = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot), campaign_root=root)
    assert value["selected_company_id"] is None
    assert value["candidates"][0]["finance"]["required_gold_reserve_raw"] == 36_000_000
    stale = deepcopy(root)
    stale["date_raw"] -= 24
    assert assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot), campaign_root=stale)["selected_company_id"] is None


@pytest.mark.parametrize("change", ["debt", "reserve", "moving", "combat", "unknown_strength", "terminal"])
def test_rejects_unhelpful_or_untimely_spend_and_keeps_input(change, tmp_path):
    driver = WarDriver(tmp_path)
    value = context(driver.snapshot)
    if change == "debt":
        value["rows"][0]["final_terms"].update(can_afford=False, payment_status=1)
    elif change == "reserve":
        value["rows"][0]["final_terms"]["resource_costs_raw"][0] = 31_000_000
    elif change == "moving":
        driver.snapshot["player_armies"][0].update(army_state="moving", route_province_ids=[2629])
    elif change == "combat":
        driver.snapshot["player_armies"][0]["in_combat"] = True
    elif change == "unknown_strength":
        driver.snapshot["active_wars"][0]["enemy_armies"][0]["soldiers"] = None
    else:
        driver.snapshot["active_wars"][0]["player_relative_war_score"] = -100
    before = deepcopy((driver.snapshot, value))
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, value,
                                                campaign_root=driver.snapshot["campaign_root_context"])
    assert decision["selected_company_id"] is None
    assert (driver.snapshot, value) == before


def test_winning_or_allied_war_does_not_become_a_blanket_building_ban(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot["active_wars"][0]["player_relative_war_score"] = 12
    assert not observe_war_spending_priority_v1(driver.snapshot)["defer_new_economic_construction"]


def test_high_threat_keeps_an_existing_building_receipt_and_concrete_army_order(tmp_path):
    driver = WarDriver(tmp_path)
    pending = {"episode_run_id": driver.snapshot["episode_run_id"], "pre_native_revision": 2,
               "source_bridge_pid": 123, "source_bridge_creation_date": "fixture"}
    write_construction_ledger(tmp_path, {"schema": "xar.ck3.construction_formal_pending_v1",
                                       "pending": pending, "applied": None, "applied_prior": []})
    baseline = {"revision": 3, "plan": {"selected_step": "life-advance"}}
    with patch("xar_autoplayer.bridge.domain_construction_private_transport_v1._identity", return_value=(123, "fixture")):
        due = plan_construction_private(driver, baseline, driver.snapshot, [], set())
    assert due["plan"]["selected_step"] == RECEIPT_STEP
    deferred = plan_war_mercenary_turn_v1(driver, baseline["plan"], snapshot=driver.snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY, HIRE_CAPABILITY})
    assert deferred["selected_step"] == "life-advance"
    assert deferred["war_mercenary_status"] == "existing_construction_pending_receipt_keeps_priority"
    move = {"selected_step": "move-army-1-to-2629"}
    unchanged = plan_war_mercenary_turn_v1(driver, move, snapshot=driver.snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY, HIRE_CAPABILITY})
    assert unchanged["selected_step"] == move["selected_step"]
    driver.snapshot["active_wars"][0].update(player_is_primary_war_leader=False, player_relative_war_score=-80)
    assert not observe_war_spending_priority_v1(driver.snapshot)["defer_new_economic_construction"]


def test_registered_normal_plan_query_hire_pending_cold_employer_readback(tmp_path):
    from mcp import Client

    baseline = {"policy": "synthetic-normal-war", "phase": "life_advance", "selected_step": "life-advance"}

    async def run():
        driver = WarDriver(tmp_path)
        with (patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline),
              patch.object(GameplayBridgeService, "_select_auto_camera_hotspot",
                           return_value={"status": "unavailable", "available": False,
                                         "reason": "camera is outside this synthetic Service fixture"})):
            async with Client(mcp_server.create_server(driver)) as client:
                first = await client.call_tool("ck3_auto_turn", {})
                assert not first.is_error, first.content
                assert first.structured_content["selected_step"] == QUERY_STEP
                second = await client.call_tool("ck3_auto_turn", {})
                assert not second.is_error, second.content
                assert second.structured_content["selected_step"] == HIRE_STEP
                assert second.structured_content["result"]["postcondition_verified"] is False
                assert driver.hire_count == 1 and driver.query_count == 1
            cold = WarDriver(tmp_path)
            cold.employed = True
            cold.query_count = 1  # a genuinely later synthetic native capture
            async with Client(mcp_server.create_server(cold)) as client:
                query = await client.call_tool("ck3_auto_turn", {})
                assert not query.is_error, query.content
                assert query.structured_content["selected_step"] == QUERY_STEP
                receipt = await client.call_tool("ck3_plan_turn", {})
                assert not receipt.is_error, receipt.content
                plan = receipt.structured_content["plan"]
                assert plan["war_mercenary_status"] == "employment_independently_observed"
                assert plan["war_mercenary_receipt"]["payment_verified"] is False
                again = await client.call_tool("ck3_plan_turn", {})
                assert not again.is_error, again.content
                assert "no_duplicate_hire" in again.structured_content["plan"]["war_mercenary_status"]
                assert cold.hire_count == 0

    asyncio.run(run())


def test_query_failure_does_not_starve_existing_war_clock_or_repeat_each_plan(tmp_path):
    driver = WarDriver(tmp_path)
    baseline = {"selected_step": "life-advance"}
    first = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY})
    assert first["selected_step"] == QUERY_STEP
    preview = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY})
    assert preview["selected_step"] == QUERY_STEP  # planning alone never consumes a query
    driver._war_mercenary_query_frame_v1 = observed_frame(driver.snapshot)  # synthetic failed execution
    following = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
        history=[], bridge_capabilities={QUERY_CAPABILITY})
    assert following["selected_step"] == "life-advance"


def test_missing_finance_uses_existing_root_query_and_does_not_loop_if_it_fails(tmp_path):
    driver = WarDriver(tmp_path)
    driver.execute_step(QUERY_STEP, expected_revision=driver.snapshot["revision"])
    driver.snapshot.pop("campaign_root_context")
    history = driver.take_snapshot()["native_command_history"]
    caps = {QUERY_CAPABILITY, HIRE_CAPABILITY, ROOT_CAPABILITY}
    baseline = {"selected_step": "life-advance"}
    planned = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
                                       history=history, bridge_capabilities=caps)
    assert planned["selected_step"] == ROOT_STEP
    driver._war_mercenary_root_query_frame_v1 = observed_frame(driver.snapshot)
    continued = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
                                         history=history, bridge_capabilities=caps)
    assert continued["selected_step"] == "life-advance"


def test_lost_hire_ack_retains_pending_and_never_resubmits(tmp_path):
    driver = WarDriver(tmp_path)
    decision = assess_mercenary_reinforcement_v1(driver.snapshot, context(driver.snapshot),
                                                campaign_root=driver.snapshot["campaign_root_context"])
    plan = {"war_mercenary_source_frame": observed_frame(driver.snapshot),
            "war_mercenary_decision_v1": decision, "war_mercenary_pre_capture_epoch": 1}
    driver.hire_mercenary_v1 = lambda **kwargs: (_ for _ in ()).throw(TimeoutError("synthetic lost ACK"))
    with pytest.raises(TimeoutError):
        submit_war_mercenary_v1(driver, plan=plan, expected_revision=driver.snapshot["revision"])
    with pytest.raises(ValueError, match="never be resubmitted"):
        submit_war_mercenary_v1(driver, plan=plan, expected_revision=driver.snapshot["revision"])


def test_known_rejection_does_not_repeat_the_same_hire_from_the_old_quote(tmp_path):
    driver = WarDriver(tmp_path)
    driver.execute_step(QUERY_STEP, expected_revision=driver.snapshot["revision"])
    history = driver.take_snapshot()["native_command_history"]
    baseline = {"selected_step": "life-advance"}
    caps = {QUERY_CAPABILITY, HIRE_CAPABILITY}
    planned = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
                                       history=history, bridge_capabilities=caps)
    assert planned["selected_step"] == HIRE_STEP
    driver.hire_mercenary_v1 = lambda **kwargs: {"status": "rejected", "accepted": False}
    submitted = submit_war_mercenary_v1(driver, plan=planned, expected_revision=driver.snapshot["revision"])
    assert submitted["status"] == "rejected"
    following = plan_war_mercenary_turn_v1(driver, baseline, snapshot=driver.snapshot,
                                         history=history, bridge_capabilities=caps)
    assert following["selected_step"] == "life-advance"
    assert "no_retry_loop" in following["war_mercenary_status"]


def test_real_native_driver_records_the_query_frame_for_the_normal_consumer():
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.war_mercenary_consumer_v1 import _context

    class Endpoint:
        pipe_name = r"\\.\pipe\offline-war-mercenary-query-fixture"

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def send(self, request):
            if request.get("type") == "execute_step":
                leaf = context({"played_character": {"character_id": 29829}, "date_raw": 53178312})
                self.on_frame({"type": "command_result", "protocol_version": 1,
                    "request_id": request["request_id"], "ok": True,
                    "result": {"step": QUERY_STEP, "accepted": True, "status": "completed",
                        "read_only": True, "query_sequence": 1, "snapshot_revision": 3,
                        "date_raw": 53178312, "player_mercenary_context": leaf}})

        def close(self):
            pass

        def transport_error(self):
            return None

    endpoint = Endpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
    try:
        endpoint.on_frame({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 4242, "session_generation": 0,
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", QUERY_CAPABILITY]})
        endpoint.on_frame({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:3", "revision": 3,
            "state": {"phase": "map_hud", "date": "synthetic-only", "date_raw": 53178312,
                "speed": 1, "paused": True, "map_ready": True, "history": [],
                "played_character": {"character_id": 29829, "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "player_armies": [], "active_wars": []}})
        before = driver.take_snapshot()
        result = driver.execute_step(QUERY_STEP, expected_revision=before["revision"])
        assert result["mercenary_query_source_frame_v1"] == observed_frame(before)
        after = driver.take_snapshot()
        consumed = _context(after["native_command_history"], after)
        assert consumed is not None and consumed["rows"][0]["company_id"] == 0
    finally:
        driver.close()
