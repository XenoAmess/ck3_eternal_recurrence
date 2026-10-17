"""Source-only strategic policy plus real registered Service, synthetic native I/O."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
from xar_autoplayer import war_strategic_reserve_v1 as candidate
from xar_autoplayer import war_mercenary_consumer_v1 as consumer


def test_strategic_reserve_policy_and_registered_service(tmp_path):
    from test_war_reinforcement_tradeoff_v1 import WarDriver, army, company, context
    from xar_autoplayer.bridge import mcp_server
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
    from xar_autoplayer.bridge.projected_contact_contract import query_projected_contact_scope_v1_step
    from mcp import Client

    checks = []
    def check(name, function):
        function()
        checks.append({"name": name, "passed": True})

    if True:
        base = tmp_path
        driver = WarDriver(base / "pure")
        root = driver.snapshot["campaign_root_context"]
        root["primary_title"] = {"title_id": 2230}
        snapshot = deepcopy(driver.snapshot)
        snapshot["player_armies"][0]["owner_character_id"] = snapshot["played_character"]["character_id"]
        # A second remote threat is deliberately retained: no company can
        # reverse its global count; strategic reserves still have a purpose.
        snapshot["active_wars"].append({**deepcopy(snapshot["active_wars"][0]),
            "war_id": 100663324, "enemy_armies": [army(3, 9000, 9999, controllable=False)]})
        rows = [company(0, 10_000_000, 1200, 999), company(1, 15_000_000, 1300, 998),
                company(2, 16_000_000, 1000, 997), company(3, 18_000_000, 1800, 996)]
        decision = candidate.assess_mercenary_reinforcement_v1(snapshot, context(snapshot, rows), campaign_root=root)
        before = deepcopy((snapshot, rows))

        def strategic():
            assert decision["selected_company_id"] == 0
            assert len(decision["candidates"]) == len(rows)
            assert all(not row["rejection_reasons"] for row in decision["candidates"])
            assert all(row["friendly_staging_soldiers"] is None for row in decision["candidates"])
            assert decision["selected_candidate"]["numerical_balance_reversed_war_ids"] == []
            assert decision["selected_candidate"]["purpose_war_ids"] == [100663323]
            assert decision["war_spending_priority"]["primary_war_hostile_union_v1"]["observed_current_soldiers"] == 10500
            assert decision["arrival_eta_days"] is None and decision["battle_win_probability"] is None
            assert decision["selected_candidate"]["arrival_risk_accepted_for_strategic_purpose"] is True
            assert (snapshot, rows) == before
        check("all_rows_retained_no_staging_or_global_reversal_veto", strategic)

        def local_evidence():
            frame = deepcopy(snapshot)
            frame["diagnostics"]["connection_generation"] = 1
            actor = frame["played_character"]["character_id"]
            p = {"status": "available", "scope_kind": "hypothetical_arrival_against_current_target_state",
                 "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
                 "subject_army_id": 1, "subject_native_carmy_id": 100, "subject_owner_character_id": actor,
                 "subject_current_province_id": 2623, "target_province_id": 2629,
                 "incoming_entry_province_id": 2623, "observed_target_public_cunit_ids": [2],
                 "observed_target_combat_ids": [], "transition_kind": "create_new",
                 "selected_current_combat_id": None, "selected_current_combat_array_index": None,
                 "projected_subject_side": "attacker", "projected_initiator_is_defender_observable": True,
                 "projected_initiator_is_defender": False, "incoming_adjacency_kind_raw": 0,
                 "projected_attacker_army_ids": [1], "projected_defender_army_ids": [2],
                 "contact_projection_inputs_complete": True}
            command = query_projected_contact_scope_v1_step(1, 2629, 2623)
            reply = {"queried_snapshot_id": frame["snapshot_id"], "queried_revision": frame["revision"],
                     "queried_native_revision": frame["native_revision"], "queried_connection_generation": 1,
                     "queried_episode_run_id": frame["episode_run_id"], "projected_contact_scope": p}
            history = [{"command": command, "ok": True, "result": reply}]
            plan = {"projected_contact_scope": p}
            value = candidate.assess_mercenary_reinforcement_v1(frame, context(frame, rows), campaign_root=root,
                                                               operational_plan=plan, history=history)
            assert value["selected_company_id"] == 0
            chosen = value["selected_candidate"]
            assert chosen["local_comparison"]["status"] == "available"
            assert chosen["local_comparison"]["local_hostile_army_ids"] == [2]
            assert chosen["local_comparison"]["allocated_player_army_ids"] == [1]
            assert chosen["local_comparison"]["enemy_current_soldiers"] == 1500
            assert chosen["conditional_local_player_soldiers_after_arrival"] == 2000
            assert chosen["numerical_balance_reversed_war_ids"] == [100663323]
            assert chosen["comparison_enemy_current_soldiers"] == 10500
            # Faked plan membership alone and all stale source dimensions do
            # not acquire local credit. They retain only strategic purposes.
            no_query = candidate.assess_mercenary_reinforcement_v1(frame, context(frame, rows), campaign_root=root,
                                                                  operational_plan=plan)
            assert no_query["selected_candidate"]["local_comparison"]["status"] == "unavailable"
            for key in ("queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "queried_episode_run_id"):
                altered = deepcopy(history)
                altered[0]["result"][key] = "stale"
                result = candidate.assess_mercenary_reinforcement_v1(frame, context(frame, rows), campaign_root=root,
                                                                   operational_plan=plan, history=altered)
                assert result["selected_candidate"]["numerical_balance_reversed_war_ids"] == []
        check("real_normal_contact_selector_and_five_stale_binding_negatives", local_evidence)

        mutations = {
            "native_can_hire": lambda s, c, r: c["rows"][0]["final_terms"].update(can_hire=False),
            "native_can_afford": lambda s, c, r: c["rows"][0]["final_terms"].update(can_afford=False),
            "employed": lambda s, c, r: c["rows"][0].update(employer_id=987),
            "incomplete_ten_resource_quote": lambda s, c, r: c["rows"][0]["final_terms"].update(resource_costs_raw=[0]),
            "wrong_quote_scale": lambda s, c, r: c["rows"][0]["final_terms"].update(resource_scale=100),
            "negative_resource_cost": lambda s, c, r: c["rows"][0]["final_terms"]["resource_costs_raw"].__setitem__(1, -1),
            "reserve": lambda s, c, r: c["rows"][0]["final_terms"]["resource_costs_raw"].__setitem__(0, 31_000_000),
            "high_military_allocation": lambda s, c, r: r["player_max_monthly_gold_maintenance_v1"]["value"].update(raw=3_000_000),
            "stale_root": lambda s, c, r: r.update(date_raw=r["date_raw"]-24),
            "stale_actor": lambda s, c, r: c.update(actor_character_id=987),
            "stale_date": lambda s, c, r: c.update(date_raw=c["date_raw"]-24),
            "spawn_unknown": lambda s, c, r: c["rows"][0]["location"].update(hire_auto_raise_position_ready=False),
            "positive_strength_unknown": lambda s, c, r: c["rows"][0]["troop_strength"].update(current_soldiers=None),
            "known_hostile_spawn": lambda s, c, r: c["rows"][0]["location"].update(hire_auto_raise_province_id=2629),
            "no_recoverable_own_war": lambda s, c, r: [w.update(player_relative_war_score=-100) for w in s["active_wars"]],
        }
        for name, mutate in mutations.items():
            def negative(mutate=mutate):
                frame, current_root = deepcopy(snapshot), deepcopy(root)
                market = context(frame, [company(0, 10_000_000, 1200, 999)])
                mutate(frame, market, current_root)
                result = candidate.assess_mercenary_reinforcement_v1(frame, market, campaign_root=current_root)
                assert result["selected_company_id"] is None, name
                assert len(result["candidates"]) == 1
            check("negative_" + name, negative)

        def no_deficit_query():
            frame = deepcopy(snapshot)
            frame["player_armies"][0]["soldiers"] = 20000
            priority = candidate.observe_war_spending_priority_v1(frame, campaign_root=root)
            assert priority["primary_war_hostile_union_v1"]["shared_force_deficit"] is False
            assert candidate.observe_mercenary_purchase_model_need_v1(priority)["query_can_change_strategic_reserve_model"] is True
        check("losing_title_exposure_queries_even_when_count_leading", no_deficit_query)

        def strategic_thresholds():
            def evaluate(*, score=-12, primary=False, directly_held=False, price=10_000_000, troops=1200,
                         own_soldiers=2000, occupation=False):
                frame, current_root = deepcopy(snapshot), deepcopy(root)
                current_root.pop("primary_title", None)
                current_root.pop("held_title_partition", None)
                if primary:
                    current_root["primary_title"] = {"title_id": 2230}
                if directly_held:
                    current_root["held_title_partition"] = [{"title": {"title_id": 2230}}]
                frame["player_armies"][0]["soldiers"] = own_soldiers
                frame["active_wars"] = [frame["active_wars"][0]]
                war = frame["active_wars"][0]
                war["player_relative_war_score"] = score
                if occupation:
                    war["primary_opponent_character_id"] = 987
                    war["objective_province_states"] = [{"province_id": 2629, "occupation_observable": True,
                        "is_occupied": True, "occupying_character_id": 987}]
                return candidate.assess_mercenary_reinforcement_v1(frame,
                    context(frame, [company(0, price, troops, 999)]), campaign_root=current_root)
            assert evaluate()["selected_company_id"] is None  # minor generic loss, no local evidence
            assert evaluate(score=-24)["selected_company_id"] is None
            assert evaluate(score=-25)["selected_company_id"] == 0
            assert evaluate(score=-1, primary=True)["selected_company_id"] == 0
            assert evaluate(score=-1, directly_held=True)["selected_company_id"] == 0
            assert evaluate(score=-1, occupation=True)["selected_company_id"] == 0
            assert evaluate(score=-1, primary=True, troops=200)["selected_company_id"] is None
            assert evaluate(score=-25, price=18_000_000)["selected_company_id"] is None
            assert evaluate(score=-25, primary=True, price=18_000_000)["selected_company_id"] == 0
            assert evaluate(score=-25, primary=True, price=26_000_000)["selected_company_id"] is None
            assert evaluate(score=1, primary=True)["selected_company_id"] is None
        check("eleven_stakes_score_marginal_and_cash_opportunity_cost_cases", strategic_thresholds)

        async def service_chain():
            scene = base / "registered-service"
            d = WarDriver(scene)
            d.snapshot["campaign_root_context"]["primary_title"] = {"title_id": 2230}
            d.snapshot["player_armies"][0]["soldiers"] = 2000  # already ahead of 1500
            baseline = {"policy": "offline-source-candidate", "phase": "life_advance", "selected_step": "life-advance"}
            original_context = context
            def no_staging_context(s, rows=None, epoch=1):
                return original_context(s, rows if rows is not None else [company(0, 10_000_000, 1200, 999)], epoch)
            with (patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline),
                  patch("test_war_reinforcement_tradeoff_v1.context", side_effect=no_staging_context),
                  patch.object(GameplayBridgeService, "_select_auto_camera_hotspot",
                               return_value={"status": "unavailable", "available": False, "reason": "offline fixture"})):
                async with Client(mcp_server.create_server(d)) as client:
                    query = await client.call_tool("ck3_auto_turn", {})
                    assert not query.is_error, query.content
                    assert query.structured_content["selected_step"] == consumer.QUERY_STEP
                    hire = await client.call_tool("ck3_auto_turn", {})
                    assert not hire.is_error, hire.content
                    assert hire.structured_content["selected_step"] == consumer.HIRE_STEP
                    assert d.hire_count == 1
                    chosen = hire.structured_content["plan"]["war_mercenary_decision_v1"]["selected_candidate"]
                    assert chosen["purpose_war_ids"] == [100663323]
                    assert chosen["numerical_balance_reversed_war_ids"] == []
                    assert chosen["arrival_eta_days"] is None
                    assert hire.structured_content["result"]["payment_verified"] is False
                    # Unknown acknowledgement remains pending; repeated planning
                    # can query observations but cannot submit a second hire.
                    again = await client.call_tool("ck3_auto_turn", {})
                    assert not again.is_error, again.content
                    assert d.hire_count == 1
                cold = WarDriver(scene)
                cold.snapshot["campaign_root_context"]["primary_title"] = {"title_id": 2230}
                cold.employed, cold.query_count = True, d.query_count
                async with Client(mcp_server.create_server(cold)) as client:
                    after_query = await client.call_tool("ck3_auto_turn", {})
                    assert not after_query.is_error, after_query.content
                    receipt = await client.call_tool("ck3_plan_turn", {})
                    assert not receipt.is_error, receipt.content
                    result = receipt.structured_content["plan"]
                    assert result["war_mercenary_status"] == "employment_independently_observed"
                    observed = result["war_mercenary_receipt"]
                    assert observed["payment_verified"] is False and observed["army_creation_verified"] is False
                    post = observed["post_hire_observations_v1"]
                    assert post["post_treasury_raw"] is not None
                    assert post["pre_player_army_ids"] == [1]
                    assert post["pre_treasury_raw"] == chosen["finance"]["observed_treasury_raw"]
                    assert post["pre_source_frame"] == observed["source_frame"]
                    assert post["pre_capture_epoch"] == observed["pre_capture_epoch"]
                    assert observed["decision"]["selected_candidate"] == chosen
                    no_duplicate = await client.call_tool("ck3_plan_turn", {})
                    assert not no_duplicate.is_error, no_duplicate.content
                    assert "no_duplicate_hire" in no_duplicate.structured_content["plan"]["war_mercenary_status"]
                    assert cold.hire_count == 0
            return {"registered_service": True, "query_count": d.query_count,
                    "hire_count": d.hire_count, "cold_hire_count": cold.hire_count,
                    "unverified_payment_and_army_preserved": True,
                    "native_replies": "synthetic outer I/O; no live call", "post_observation": observed["post_hire_observations_v1"]}
        chain = asyncio.run(service_chain())
        checks.append({"name": "registered_mcp_service_query_single_hire_unknown_no_retry_cold_employer_and_wallet_inventory", "passed": True})

        def concrete_actions_and_windows():
            for step in ("move-army-1-to-2629", "query-army-strengths-v1", "some-existing-war-termination"):
                result = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": step}, snapshot=driver.snapshot,
                    history=[], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
                assert result["selected_step"] == step
            for key in ("active_event", "pending_character_interaction"):
                frame = deepcopy(driver.snapshot)
                frame[key] = {"id": "mandatory"}
                result = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"}, snapshot=frame,
                    history=[], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
                assert result["selected_step"] == "life-advance"
            mild = deepcopy(driver.snapshot)
            mild["player_armies"][0]["soldiers"] = 2000
            mild["campaign_root_context"].pop("primary_title", None)
            result = consumer.plan_war_mercenary_turn_v1(driver, {"selected_step": "life-advance"}, snapshot=mild,
                history=[], bridge_capabilities={consumer.QUERY_CAPABILITY, consumer.HIRE_CAPABILITY})
            assert result["war_mercenary_status"] == "strategic_model_has_no_current_evidenced_purpose_keep_war_action"
            assert "当前尚无足够战略采购用途" in result["war_decision_presentation_v1"]["reason"]
        check("concrete_army_orders_and_mandatory_windows_keep_priority", concrete_actions_and_windows)

    output = os.environ.get("XAR_STRATEGIC_MERCENARY_QUALIFICATION_OUTPUT")
    if output:
        packet = {"schema": "xar.strategic-mercenary-public-source-qualification.v1",
                  "machine_id": "xenoamess-full-tower-eb9d2c1186",
                  "observed_utc": datetime.now(timezone.utc).isoformat(),
                  "checks": checks, "check_count": len(checks), "service_chain": chain,
                  "source_pins": [dict(path=str(Path(module.__file__)), bytes=Path(module.__file__).stat().st_size,
                     sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()) for module in (candidate, consumer)],
                  "outer_native_replies_and_chooser": "explicit synthetic fixture; real registered MCP and Service",
                  "live_game_native_calls": 0, "actual_hire_payment_army_arrival_or_war_credit": False}
        Path(output).write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
