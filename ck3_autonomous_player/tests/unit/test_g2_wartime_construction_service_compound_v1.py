"""Root-only FIRST: real normal Service, cash/quote transport and durable receipt.

The game envelopes, process identity and ordinary baseline chooser are synthetic.
No native producer, CK3 process or production-live outcome is qualified here.
"""

import asyncio
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_construction_formal_private_consumer import root
from test_construction_monthly_budget_v1 import cash_fixture
from test_g2_normal_construction_cli_service_compound_v1 import NormalConstructionFixtureDriver
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, SUBMIT_STEP, read_construction_ledger,
)


class WartimeConstructionDriver(NormalConstructionFixtureDriver):
    query_construction_cash_outcome_private_v1 = NativeHeadlessGameplayDriver.query_construction_cash_outcome_private_v1
    query_war_cash_current_resources_private_v1 = NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1

    def __init__(self, directory, *, all_raised=5_000_000, missing=False):
        super().__init__(directory)
        self.allow_private_construction_formal_trial = True
        self.allow_private_war_cash_query = True
        self.all_raised_expense = all_raised
        self.missing_raised = missing
        self.set_frame(3)

    def set_frame(self, revision):
        self.snapshot = self.current_frame(revision)
        self.snapshot["active_wars"] = [{"war_id": 100663329}]
        self.snapshot["player_armies"] = [{"army_id": 218104048}]
        current_root = root(revision)[0]["result"]
        current_root["campaign_root_context"]["date_raw"] = self.snapshot["date_raw"]
        self.recorded = [("query-campaign-root-context-v1", current_root)]

    def take_internal_semantic_snapshot(self):
        return self.take_snapshot()

    def capabilities(self):
        value = super().capabilities()
        return {**value, "action_steps": [*value["action_steps"], "query-army-strengths-v1"]}

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        if request["step"] != CURRENT_STEP:
            return super().wait_for_command_result(request_id, timeout)
        cash = cash_fixture(
            gold=self.snapshot["played_character_gold"]["raw"],
            gross=450_000, expenses=10_400_000,
            current=2_000_000, all_raised=self.all_raised_expense,
        )
        cash.update(
            snapshot_revision=self.snapshot["native_revision"],
            date_raw=self.snapshot["date_raw"],
            active_war_ids=[100663329], player_army_ids=[218104048],
        )
        for row in cash["military_expenses"].values():
            row["war_ids"] = [100663329]
        if self.missing_raised:
            cash["status"] = "partial"
            cash["readiness"]["all_raised_military_expenses_ready"] = False
            cash["military_expenses"]["all_raised"].update(
                status="unavailable", unavailable_reason="fixture_native_expense_unavailable",
                resource_raw_native=None, gold_raw=None, treasury_raw=None,
            )
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": CURRENT_STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True, "advertised": False,
                "backend_id": "native-headless", "war_cash_current_resources": cash,
            },
        }


def test_registered_wartime_quote_submit_material_cold_and_observed_cash_floor(tmp_path):
    from mcp import Client

    baseline = {"policy": "normal-fixture", "phase": "life_advance", "selected_step": "life-advance"}
    records = []

    def driver_for(scene, **kwargs):
        directory = tmp_path / scene
        directory.mkdir()
        return WartimeConstructionDriver(directory, **kwargs)

    def sends(driver):
        return sum(request["step"] == transport.ACTION_NATIVE for request in driver.requests)

    async def run():
        with (
            patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline),
            patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("use normal planner")),
            patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("use normal executor")),
            patch.object(transport, "_identity", return_value=(881, "fixture-construction-wartime")),
            patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(881, "fixture-construction-wartime")),
        ):
            driver = driver_for("war-affordable")
            async with Client(mcp_server.create_server(driver)) as client:
                selected = await client.call_tool("ck3_plan_turn", {})
                assert not selected.is_error, selected.content
                plan = selected.structured_content["plan"]
                assert plan["selected_step"] == SUBMIT_STEP
                assert plan["phase"] == "construction_wartime_typed_submit"
                budget = plan["construction_monthly_budget"]
                assert budget["horizon_months"] == 1
                assert budget["scenarios"]["current"]["net_monthly_gold_raw"] == -9_950_000
                assert budget["scenarios"]["all_raised"]["net_monthly_gold_raw"] == -12_950_000
                assert budget["scenarios"]["all_raised"]["minimum_projected_gold_raw"] == 22_050_000
                assert budget["future_war_cost_upper_ready"] is False
                assert all(row["scenario_floor_ready"] is True for row in budget["scenarios"].values())
                assert sends(driver) == 0
                assert [row["step"] for row in driver.requests] == [CURRENT_STEP, transport.QUERY_NATIVE]

                submitted = await client.call_tool("ck3_auto_turn", {})
                assert not submitted.is_error, submitted.content
                assert submitted.structured_content["result"]["status"] == "submitted_verification_pending"
                assert sends(driver) == 1
                pending = read_construction_ledger(driver.state_dir)["pending"]
                assert pending["construction_monthly_budget"]["construction_gold_cost_raw"] == 15_000_000
                repeated = await client.call_tool("ck3_plan_turn", {})
                assert not repeated.is_error, repeated.content
                assert "construction_pending_action" in repeated.structured_content["plan"]
                assert sends(driver) == 1

                driver.set_frame(4)
                material = await client.call_tool("ck3_auto_turn", {})
                assert not material.is_error, material.content
                assert material.structured_content["selected_step"] == RECEIPT_STEP
                receipt = material.structured_content["result"]
                assert receipt["status"] == "applied"
                assert receipt["postcondition_verified"] is True
                assert receipt["post_player_gold_raw"] == 35_000_000
                assert receipt["candidate"]["province_id"] == 2635
                assert read_construction_ledger(driver.state_dir)["pending"] is None
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                assert following.structured_content["plan"]["construction_receipt_consumed"]["action_request_id"] == receipt["action_request_id"]
                assert sends(driver) == 1

            # A different process identity reuses the durable applied receipt;
            # the active tuple is observed again without another action.
            cold = WartimeConstructionDriver(driver.state_dir)
            cold.set_frame(4)
            with (
                patch.object(transport, "_identity", return_value=(882, "fixture-cold-construction")),
                patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(882, "fixture-cold-construction")),
            ):
                async with Client(mcp_server.create_server(cold)) as client:
                    result = await client.call_tool("ck3_auto_turn", {})
                    assert not result.is_error, result.content
                    assert result.structured_content["selected_step"] == RECEIPT_STEP
                    assert result.structured_content["result"]["postcondition_verified"] is True
            assert sends(cold) == 0
            records.append({"scene": "war-affordable", "budget": budget,
                            "submit_count": sends(driver), "material": copy.deepcopy(receipt),
                            "cold_submit_count": sends(cold)})

            for scene, kwargs in (
                ("all-raised-reserve-shortfall", {"all_raised": 10_000_000}),
                ("actual-expense-unavailable", {"missing": True}),
            ):
                deferred = driver_for(scene, **kwargs)
                async with Client(mcp_server.create_server(deferred)) as client:
                    result = await client.call_tool("ck3_plan_turn", {})
                    assert not result.is_error, result.content
                    plan = result.structured_content["plan"]
                    assert plan["selected_step"] == "life-advance"
                    assert plan["phase"] == "construction_cash_budget_deferred"
                    assert plan["construction_monthly_budget"]["scenarios"]["current"]["scenario_floor_ready"] is True
                    assert plan["construction_monthly_budget"]["scenarios"]["all_raised"]["scenario_floor_ready"] is not True
                assert sends(deferred) == 0
                records.append({"scene": scene, "plan": plan, "submit_count": 0})

            war = driver_for("selected-war-work")
            war_step = "query-army-strengths-v1"
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value={**baseline, "selected_step": war_step}):
                async with Client(mcp_server.create_server(war)) as client:
                    result = await client.call_tool("ck3_plan_turn", {})
                    assert not result.is_error, result.content
                    assert result.structured_content["plan"]["selected_step"] == war_step
            assert sends(war) == 0
            assert not any(row["step"] == CURRENT_STEP for row in war.requests)
            records.append({"scene": "selected-war-work", "selected_step": war_step, "submit_count": 0})

    asyncio.run(run())
    output_path = os.environ.get("XAR_WARTIME_CONSTRUCTION_SERVICE_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "schema": "xar.wartime-construction-service-first12004.v1",
            "input_boundary": "synthetic game envelopes/process/baseline; real registered normal Service and transports",
            "scenes": records, "native_qualification": False, "production_live": False,
            "m4_complete": False, "nw_econ_complete": False,
        }, indent=2) + "\n", encoding="utf-8")
