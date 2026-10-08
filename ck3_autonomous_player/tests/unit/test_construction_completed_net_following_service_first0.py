"""One Root-owned compound for completion then ordinary NET consumption.

The native envelopes, prior start receipt and underlying idle choice are
synthetic. Registered MCP, normal Service, strict cash/slot transports,
durable receipt updates and the economic classifier are production code.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_g2_wartime_construction_service_compound_v1 import WartimeConstructionDriver
from test_construction_economic_outcome_v1 import completed_receipt
from test_construction_monthly_budget_v1 import cash_fixture
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.construction_economic_outcome_v1 import construction_economic_outcome_v1
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, read_construction_ledger, write_construction_ledger,
)


def test_registered_completion_gross_then_following_net_is_durable(tmp_path):
    from mcp import Client

    baseline = {"policy": "source-fixture", "phase": "life_advance", "selected_step": "life-advance"}
    identity = (881, "fixture-completed-net-following")
    records = []

    def driver_for(name):
        directory = tmp_path / name
        directory.mkdir()
        driver = WartimeConstructionDriver(directory)
        driver.set_frame(4)
        driver.snapshot["date_raw"] = 53288568 + 30 * 24
        current_root = driver.recorded[0][1]["campaign_root_context"]
        current_root["date_raw"] = driver.snapshot["date_raw"]
        current_root["player_monthly_gold_income"]["raw"] = 450_000
        driver.completed_construction = True
        driver.gold_override = 35_000_000
        driver.province_income_after_completion_raw = 137_000
        return driver

    def seed(driver):
        date = driver.snapshot["date_raw"]
        row = completed_receipt()
        row.update(
            action_request_id="fixture-original-construction", actor_character_id=29829,
            episode_run_id=driver.snapshot["episode_run_id"], completion_status="in_progress",
            completion_observed_date_raw=None,
            pre_native_revision=2, pre_date_raw=date - 744, pre_proof_epoch=20,
            source_bridge_pid=identity[0], source_bridge_creation_date=identity[1],
            post_native_revision=3, post_date_raw=date - 720, post_proof_epoch=30,
            post_bridge_pid=identity[0], post_bridge_creation_date=identity[1],
            completion_last_check_date_raw=date - 720,
            observed_player_monthly_gold_income_raw=None, income_observed_date_raw=None,
            post_player_gold_raw=35_000_000,
        )
        row["candidate"].update(building_type_id=24, slot_index=1,
                                stock_gold_cost_raw=15_000_000, gold_before_raw=50_000_000)
        before = cash_fixture(gold=50_000_000, gross=400_000, expenses=10_400_000,
                              current=2_000_000, all_raised=5_000_000)
        before.update(date_raw=row["pre_date_raw"], snapshot_revision=2,
                      active_war_ids=[100663329], player_army_ids=[218104048])
        for expense in before["military_expenses"].values():
            expense["war_ids"] = [100663329]
        row["pre_cash_v2"] = before
        return row

    async def run():
        with (
            patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline),
            patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("ordinary planner required")),
            patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("ordinary executor required")),
            patch.object(transport, "_identity", return_value=identity),
            patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=identity),
        ):
            driver = driver_for("completion-then-following")
            original = seed(driver)
            write_construction_ledger(driver.state_dir, {
                "pending": None, "applied": original, "applied_prior": [],
            })
            async with Client(mcp_server.create_server(driver)) as client:
                completed = await client.call_tool("ck3_auto_turn", {})
                assert not completed.is_error, completed.content
                completed = completed.structured_content
                assert completed["selected_step"] == RECEIPT_STEP
                material = completed["result"]
                assert material["postcondition_verified"] is True
                assert material["completion_status"] == "completed"
                assert material["observed_player_monthly_gold_income_raw"] == 450_000
                assert material["action_request_id"] == original["action_request_id"]
                assert "post_cash_v2" not in material
                assert [request["step"] for request in driver.requests] == [transport.QUERY_NATIVE]

                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                plan = following.structured_content["plan"]
                consumed = plan["construction_receipt_consumed"]
                durable = read_construction_ledger(driver.state_dir)["applied"]
                assert consumed == durable
                assert consumed["action_request_id"] == material["action_request_id"]
                assert consumed["start_receipt"] == material["start_receipt"]
                assert consumed["pre_cash_v2"] == original["pre_cash_v2"]
                assert consumed["observed_player_monthly_gold_income_raw"] == material["observed_player_monthly_gold_income_raw"]
                assert consumed["income_observed_date_raw"] == material["income_observed_date_raw"]
                assert consumed["post_cash_v2"]["current_treasury"]["raw"] == 35_000_000
                outcome = plan["construction_economic_outcome"]
                assert outcome["readiness"]["player_net_monthly_change_ready"] is True
                assert outcome["observed_cash_change"]["monthly_rate_changes"]["player_monthly_net_income"]["delta_raw"] == 50_000
                assert outcome["observed_cash_change"]["verified_construction_gold_debit_raw"] == 15_000_000
                assert outcome["readiness"]["building_attribution_ready"] is False
                assert outcome["readiness"]["net_benefit_ready"] is False
                assert plan["construction_cash_outcome"]["new_construction_spend_projected_raw"] == 0
                assert [request["step"] for request in driver.requests] == [transport.QUERY_NATIVE, CURRENT_STEP]
                assert plan["selected_step"] == "life-advance"

                repeated = await client.call_tool("ck3_plan_turn", {})
                assert not repeated.is_error, repeated.content
                assert repeated.structured_content["plan"]["construction_economic_outcome"] == outcome
                assert read_construction_ledger(driver.state_dir)["applied"] == durable
                assert [request["step"] for request in driver.requests] == [transport.QUERY_NATIVE, CURRENT_STEP]
                records.append({"scene": "completion-then-following", "material": material,
                                "durable_following": durable, "economic_outcome": outcome})

            # A completed earlier action must receive its missing post packet
            # without overwriting a newer active action in the same ledger.
            older = driver_for("earlier-completed-action")
            prior = copy.deepcopy(material)
            newest = seed(older)
            newest.update(action_request_id="fixture-newer-active-action",
                          post_native_revision=4, post_date_raw=older.snapshot["date_raw"],
                          completion_last_check_date_raw=older.snapshot["date_raw"])
            newest["candidate"].update(barony_title_id=2174, province_id=2629)
            write_construction_ledger(older.state_dir, {
                "pending": None, "applied": newest, "applied_prior": [prior],
            })
            async with Client(mcp_server.create_server(older)) as client:
                selected = await client.call_tool("ck3_plan_turn", {})
                assert not selected.is_error, selected.content
                observed = selected.structured_content["plan"]["construction_receipt_consumed"]
                ledger = read_construction_ledger(older.state_dir)
                assert ledger["applied"] == newest
                assert ledger["applied_prior"] == [observed]
                assert observed["action_request_id"] == prior["action_request_id"]
                assert observed["post_cash_v2"]["date_raw"] == older.snapshot["date_raw"]
                projected = construction_economic_outcome_v1(observed, exact_ck3_build="1.20.0.4")
                assert projected["readiness"]["player_net_monthly_change_ready"] is True
                assert [request["step"] for request in older.requests] == [CURRENT_STEP]
                records.append({"scene": "earlier-completed-action", "selected_receipt": observed,
                                "newer_active_preserved": ledger["applied"]})
            assert all(request["step"] != transport.ACTION_NATIVE
                       for owner in (driver, older) for request in owner.requests)

    asyncio.run(run())
    output = os.environ.get("XAR_CONSTRUCTION_COMPLETED_NET_FOLLOWING_OUTPUT")
    if output:
        with Path(output).open("x", encoding="utf-8") as handle:
            json.dump({"schema": "xar.construction-completed-net-following-first0.v1",
                       "scenes": records, "native_builds": 0, "native_submits": 0,
                       "production_live": False, "m4_complete": False}, handle, indent=2)
            handle.write("\n")
