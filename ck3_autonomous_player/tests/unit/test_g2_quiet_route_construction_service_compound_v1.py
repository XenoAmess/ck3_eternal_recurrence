"""Root-only FIRST of quiet-route construction through registered normal Service.

Game envelopes and the already-qualified baseline plan are synthetic. The native
contact proof is not exercised here; Service, transports and durable material are.
"""

import asyncio
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_g2_wartime_construction_service_compound_v1 import WartimeConstructionDriver
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.bridge.war_contract import advance_route_contact_horizon_step, move_army_step
from xar_autoplayer.construction_formal_consumer import RECEIPT_STEP, SUBMIT_STEP, read_construction_ledger


def test_registered_quiet_route_quote_submit_receipt_cold_and_clock_fallback(tmp_path):
    from mcp import Client

    quiet_step = advance_route_contact_horizon_step(218104048, 2615, [134218098])
    move_step = move_army_step(218104048, 2615)
    quiet_plan = {
        "policy": "one-life-turn-v1",
        "phase": "native_war_route_contact_horizon_progress",
        "selected_step": quiet_step,
        "reason": "synthetic already-qualified one-day contact-free route baseline",
    }
    records = []

    class QuietRouteDriver(WartimeConstructionDriver):
        def capabilities(self):
            value = super().capabilities()
            return {**value, "action_steps": [*value["action_steps"], quiet_step, move_step]}

    def driver_for(name, **kwargs):
        directory = tmp_path / name
        directory.mkdir()
        return QuietRouteDriver(directory, **kwargs)

    def sends(driver):
        return sum(request["step"] == transport.ACTION_NATIVE for request in driver.requests)

    async def run():
        with (
            patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=quiet_plan),
            patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("use normal planner")),
            patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("use normal executor")),
            patch.object(transport, "_identity", return_value=(901, "fixture-quiet-route")),
            patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(901, "fixture-quiet-route")),
        ):
            driver = driver_for("quiet-affordable")
            async with Client(mcp_server.create_server(driver)) as client:
                selected = await client.call_tool("ck3_plan_turn", {})
                assert not selected.is_error, selected.content
                plan = selected.structured_content["plan"]
                assert plan["selected_step"] == SUBMIT_STEP
                assert plan["phase"] == "construction_wartime_typed_submit"
                assert [row["step"] for row in driver.requests] == [CURRENT_STEP, transport.QUERY_NATIVE]
                assert all(row["scenario_floor_ready"] is True for row in plan["construction_monthly_budget"]["scenarios"].values())
                assert sends(driver) == 0
                submitted = await client.call_tool("ck3_auto_turn", {})
                assert not submitted.is_error, submitted.content
                assert submitted.structured_content["result"]["status"] == "submitted_verification_pending"
                original_id = read_construction_ledger(driver.state_dir)["pending"]["action_request_id"]
                repeated = await client.call_tool("ck3_plan_turn", {})
                assert not repeated.is_error, repeated.content
                assert "construction_pending_action" in repeated.structured_content["plan"]
                assert sends(driver) == 1
                driver.set_frame(4)
                material = await client.call_tool("ck3_auto_turn", {})
                assert not material.is_error, material.content
                assert material.structured_content["selected_step"] == RECEIPT_STEP
                receipt = material.structured_content["result"]
                assert receipt["action_request_id"] == original_id
                assert receipt["status"] == "applied" and receipt["postcondition_verified"] is True
                assert receipt["post_player_gold_raw"] == 35_000_000
                assert receipt["candidate"]["province_id"] == 2635
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                assert following.structured_content["plan"]["construction_receipt_consumed"]["action_request_id"] == original_id
                assert sends(driver) == 1

            cold = QuietRouteDriver(driver.state_dir)
            cold.set_frame(4)
            with (
                patch.object(transport, "_identity", return_value=(902, "fixture-quiet-route-cold")),
                patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(902, "fixture-quiet-route-cold")),
            ):
                async with Client(mcp_server.create_server(cold)) as client:
                    recovered = await client.call_tool("ck3_auto_turn", {})
                    assert not recovered.is_error, recovered.content
                    assert recovered.structured_content["selected_step"] == RECEIPT_STEP
                    assert recovered.structured_content["result"]["action_request_id"] == original_id
                    assert recovered.structured_content["result"]["postcondition_verified"] is True
            assert sends(cold) == 0
            records.append({"scene": "quiet-affordable", "original_clock_step": quiet_step,
                            "submit_count": sends(driver), "material": copy.deepcopy(receipt), "cold_submit_count": 0})

            shortfall = driver_for("quiet-observed-reserve-shortfall", all_raised=10_000_000)
            async with Client(mcp_server.create_server(shortfall)) as client:
                deferred = await client.call_tool("ck3_plan_turn", {})
                assert not deferred.is_error, deferred.content
                plan = deferred.structured_content["plan"]
                assert plan["selected_step"] == quiet_step
                assert plan["phase"] == "construction_cash_budget_deferred"
                assert plan["construction_monthly_budget"]["scenarios"]["all_raised"]["scenario_floor_ready"] is False
            assert sends(shortfall) == 0
            records.append({"scene": "quiet-observed-reserve-shortfall", "plan": plan, "submit_count": 0})

            concrete = driver_for("concrete-move-keeps-priority")
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value={
                **quiet_plan, "phase": "native_war_pursuit_move", "selected_step": move_step,
            }):
                async with Client(mcp_server.create_server(concrete)) as client:
                    preserved = await client.call_tool("ck3_plan_turn", {})
                    assert not preserved.is_error, preserved.content
                    assert preserved.structured_content["plan"]["selected_step"] == move_step
            assert sends(concrete) == 0
            assert not any(row["step"] == CURRENT_STEP for row in concrete.requests)
            records.append({"scene": "concrete-move-keeps-priority", "selected_step": move_step, "submit_count": 0})

    asyncio.run(run())
    output_path = os.environ.get("XAR_QUIET_ROUTE_CONSTRUCTION_SERVICE_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "schema": "xar.quiet-route-construction-service-first12004.v1",
            "input_boundary": "synthetic game/process/qualified baseline; real registered normal Service and transports",
            "scenes": records, "native_contact_qualification": False,
            "production_live": False, "m4_complete": False,
        }, indent=2) + "\n", encoding="utf-8")
