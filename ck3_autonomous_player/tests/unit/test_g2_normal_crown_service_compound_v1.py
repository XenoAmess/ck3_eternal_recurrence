"""Root FIRST0: ordinary registered Crown loop with qualified native wires.

The four native command_result bodies are replayed unchanged. Baseline choice,
paused outer frames and following/cold queries are explicit fixture seams. The
latter DTOs qualify Service consumption, not another native observation or live
campaign. No direct enact tool or nonwar planner is used by the ordinary loop.
"""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_realm_law_formal_registered_12004 import (
    ACTION_ID, LAW, FormalWholeWireDriver, WIRE_FILES,
)
from xar_autoplayer.bridge import realm_law_formal_private_transport as formal
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer import crown_authority_formal_consumer_v1 as consumer
from xar_autoplayer.crown_authority_policy_v1 import choose_crown_authority_upgrade_v1
from xar_autoplayer.environment import write_json_atomic


class NormalCrownFixtureDriver(FormalWholeWireDriver):
    def __init__(self, wires, state_dir, *, enabled=True):
        super().__init__(wires, enabled=enabled)
        self.state_dir = state_dir
        self.nonwar_only = False
        self._session_bridge_pid = 881
        self.recorded = []
        self.current_law_observed = False
        self.frame.update(episode_run_id="normal-crown-whole-wire-fixture12004",
                          active_event=None, pending_character_interaction=None,
                          active_wars=[], player_armies=[], native_command_history=[])

    def take_internal_semantic_snapshot(self):
        return self.take_snapshot()

    def capabilities(self):
        return {"backend_id": "native-headless", "action_steps": [
            "life-advance", "query-army-strengths-v1"], "bridge_capabilities": []}

    def _record_command(self, step, *, ok, result):
        self.recorded.append({"command": step, "ok": ok, "result": deepcopy(result)})
        self.frame["native_command_history"] = deepcopy(self.recorded)

    def wait_for_command_result(self, request_id, timeout):
        request = self.sent[-1]
        if request["step"] != formal.QUERY_STEP or not self.current_law_observed:
            return super().wait_for_command_result(request_id, timeout)
        # A source-shaped *new* following/cold query; the four qualified native
        # envelopes remain untouched and are not relabeled as this new frame.
        response = deepcopy(self.wires["query"])
        response["request_id"] = request_id
        value = response["result"]["observation"]
        value.update(snapshot_revision=self.frame["native_revision"],
                     native_snapshot_revision=self.frame["native_revision"],
                     proof_epoch=self.frame["native_revision"],
                     date_raw=self.frame["date_raw"], active_law_key=LAW)
        for row in value["candidates"]:
            row["is_active"] = row["law_key"] == LAW
            row["can_enact"] = False
            row["blocked_reason"] = "already_active" if row["is_active"] else "fixture_native_final_blocked"
        for row in value["resources"]:
            if row["currency_key"] == "prestige":
                row["amount_raw"] = 30000000
        return response


def test_registered_normal_crown_submit_independent_receipt_consume_and_precedence(tmp_path):
    from mcp import Client

    directory = os.environ.get("CK3_M7_FORMAL_NATIVE_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root FIRST requires the final GREEN FOUR native wire directory")
    wire_root = Path(directory)
    wires = {name: json.loads((wire_root / filename).read_text(encoding="utf-8"))
             for name, filename in WIRE_FILES.items()}
    originals = deepcopy(wires)
    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    records = []

    async def call(client, name):
        result = await client.call_tool(name, {})
        assert not result.is_error, result.content
        assert isinstance(result.structured_content, dict)
        return result.structured_content

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("ordinary Crown uses normal planner")), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("ordinary Crown uses normal executor")), \
                patch.object(consumer, "_new_action_id", return_value=ACTION_ID):
            disabled = NormalCrownFixtureDriver(wires, tmp_path / "disabled", enabled=False)
            async with Client(create_server(disabled)) as client:
                observed = await call(client, "ck3_plan_turn")
                assert observed["plan"]["selected_step"] == "life-advance"
            assert disabled.sent == []
            records.append({"scene": "existing-opt-in-off", "native_requests": 0})

            driver = NormalCrownFixtureDriver(wires, tmp_path / "warm")
            # Active war/factions are not invented Crown vetoes. The baseline
            # has already resolved urgent priority before this fallback.
            driver.frame["active_wars"] = [{"war_id": 100663329}]
            driver.frame["targeting_faction_count"] = 2
            async with Client(create_server(driver)) as client:
                observed = await call(client, "ck3_plan_turn")
                plan = observed["plan"]
                assert plan["selected_step"] == formal.SUBMIT_STEP
                assert plan["crown_readback"]["queried_revision"] == 41
                assert plan["crown_readback"]["queried_native_revision"] == 40
                assert plan["crown_decision"]["law_key"] == LAW
                assert dict(plan["crown_decision"]["budgets_raw"]) == {"prestige": 20000000}
                assert not any(row["step"] == formal.SUBMIT_STEP for row in driver.sent)

                submitted = await call(client, "ck3_auto_turn")
                assert submitted["selected_step"] == formal.SUBMIT_STEP
                assert submitted["result"]["status"] == "submitted_verification_pending"
                assert submitted["result"]["material_result"] is False
                pending = consumer.read_crown_authority_state_v1(driver.state_dir)["pending"]
                saved_pending = deepcopy(pending)
                assert pending["action_id"] == ACTION_ID and pending["law_key"] == LAW
                assert pending["readback"] == submitted["plan"]["crown_readback"]
                enact = [row for row in driver.sent if row["step"] == formal.SUBMIT_STEP]
                assert len(enact) == 1
                assert enact[0]["budget_prestige_raw"] == 20000000
                assert enact[0]["expected_native_revision"] == 40
                assert enact[0]["expected_proof_epoch"] == 40

                driver.select_receipt("unchanged")
                observed = await call(client, "ck3_plan_turn")
                assert observed["plan"]["selected_step"] == formal.RECEIPT_STEP
                unchanged = await call(client, "ck3_auto_turn")
                assert unchanged["result"]["status"] == "failed"
                assert unchanged["result"]["material_result"] is False
                assert consumer.read_crown_authority_state_v1(driver.state_dir)["pending"] is not None
                same_frame = await call(client, "ck3_plan_turn")
                assert same_frame["plan"]["selected_step"] == "life-advance"
                assert same_frame["plan"]["crown_status"] == "pending_result_observed"

                driver.select_receipt("enacted")
                material = await call(client, "ck3_auto_turn")
                receipt = material["result"]
                assert material["selected_step"] == formal.RECEIPT_STEP
                assert receipt["status"] == "enacted" and receipt["material_result"] is True
                assert receipt["effective_law_key"] == LAW
                assert receipt["effective_law_verified"] and receipt["resources_verified"] and receipt["succession_verified"]
                assert driver.sent[-1]["submitted_request_id"] == ACTION_ID
                state = consumer.read_crown_authority_state_v1(driver.state_dir)
                assert state["pending"] is None
                assert state["resolved"]["native_receipt"] == receipt
                driver.current_law_observed = True
                following = await call(client, "ck3_plan_turn")
                assert following["plan"]["selected_step"] == "life-advance"
                consumed = following["plan"]["crown_result_consumed"]
                assert consumed["next_turn_consumed"] is True
                assert consumed["native_receipt"] == receipt
                assert sum(row["step"] == formal.SUBMIT_STEP for row in driver.sent) == 1
            records.append({"scene": "ordinary-active-war-warm-loop", "submit_count": 1,
                "ack_material": False, "unchanged_material": False,
                "independent_native_material": True, "following_consumed": True})

            # Exact CA1→CA2 costs from the held R76 input shape test the new
            # selector here; this is not a replayed native CA2 result envelope.
            quote = deepcopy(observed["plan"]["crown_pending_action"]["readback"])
            quote["active_law_key"] = "crown_authority_1"
            for row in quote["candidates"]:
                row["is_active"] = row["law_key"] == "crown_authority_1"
                if row["law_key"] == "crown_authority_2":
                    row.update(can_enact=True, costs=[{"currency_key": "prestige", "cost_raw": 119600000}])
            for row in quote["resources"]:
                if row["currency_key"] == "prestige":
                    row["amount_raw"] = 305791610
            choice = choose_crown_authority_upgrade_v1(quote)
            assert choice.status == "ready" and choice.law_key == "crown_authority_2"
            assert dict(choice.budgets_raw) == {"prestige": 119600000}
            assert dict(choice.quoted_post_balances_raw) == {"prestige": 186191610}
            target = next(row for row in quote["candidates"] if row["law_key"] == "crown_authority_2")
            target["can_enact"] = False
            assert choose_crown_authority_upgrade_v1(quote).status == "native_blocked"
            records.append({"scene": "source-shaped-ca1-to-ca2-final-native-permission",
                "exact_prestige_budget_raw": 119600000, "post_prestige_raw": 186191610,
                "native_blocked_consumed": True, "native_wire_requalification": False})

            # Urgent war/route selections are retained without Crown queries.
            urgent = NormalCrownFixtureDriver(wires, tmp_path / "urgent")
            urgent.frame["active_wars"] = [{"war_id": 100663329}]
            urgent_plan = {**baseline, "phase": "native_war_army_query",
                           "selected_step": "query-army-strengths-v1"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=urgent_plan):
                async with Client(create_server(urgent)) as client:
                    observed = await call(client, "ck3_plan_turn")
                    assert observed["plan"]["selected_step"] == "query-army-strengths-v1"
            assert urgent.sent == []
            records.append({"scene": "urgent-war-priority", "native_requests": 0})

            # Explicit earlier-institution selection seam verifies only the new
            # Crown tail. Existing Council/Construction compounds are not replayed.
            for step in ("private-assign-councillor-v1", "private-submit-player-construction-v1"):
                earlier = NormalCrownFixtureDriver(wires, tmp_path / step)
                def select_earlier(_service, planned, _steps):
                    return {**planned, "plan": {**planned["plan"], "selected_step": step}}
                with patch.object(GameplayBridgeService, "_plan_private_council_normal_v1", new=select_earlier):
                    async with Client(create_server(earlier)) as client:
                        observed = await call(client, "ck3_plan_turn")
                        assert observed["plan"]["selected_step"] == step
                assert earlier.sent == []
                records.append({"scene": "earlier-institution-priority", "selected_step": step,
                    "native_requests": 0, "earlier_selection_fixture_seam": True})

            cold = NormalCrownFixtureDriver(wires, tmp_path / "cold")
            cold._session_bridge_pid = 882
            cold.current_law_observed = True
            write_json_atomic(cold.state_dir / "crown-authority-formal-v1.json",
                              {"pending": saved_pending, "resolved": None})
            async with Client(create_server(cold)) as client:
                classified = await call(client, "ck3_auto_turn")
                assert classified["selected_step"] == formal.RECEIPT_STEP
                result = classified["result"]
                assert result["status"] == "cold_current_law_observed"
                assert result["requested_law_observed"] is True
                assert result["material_result"] is False
                assert result["original_native_receipt_available"] is False
                following = await call(client, "ck3_plan_turn")
                consumed = following["plan"]["crown_result_consumed"]
                assert consumed["next_turn_consumed"] is True
                assert consumed["material_result"] is False and consumed["native_receipt"] is None
                assert all(row["step"] == formal.QUERY_STEP for row in cold.sent)
            records.append({"scene": "cold-current-law-classification", "resubmit_count": 0,
                "old_native_receipt_claim": False, "material_result": False,
                "following_current_law_consumed": True})

    asyncio.run(run())
    assert wires == originals
    output_path = os.environ.get("XAR_CROWN_NORMAL_SERVICE_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "schema": "xar.normal-crown-service-evidence12004.v1", "wire_dir": str(wire_root),
            "qualified_whole_wires_unchanged": True, "scenes": records,
            "boundary": "real registered normal Service/Driver; baseline/outer frame/following query fixture seams",
            "native_requalification": False, "game_action": False, "live": False,
            "m7_complete": False,
        }, indent=2) + "\n", encoding="utf-8")
