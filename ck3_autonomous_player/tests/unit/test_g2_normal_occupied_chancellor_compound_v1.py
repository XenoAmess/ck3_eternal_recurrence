"""ONE new registered ordinary occupied-Chancellor compound, Root FIRST0.

Use the existing Council DTO/Driver fixture shape and real consumer, selector,
typed action contract and registered Service. Chancellor skill/gates/holder
poststates are explicitly offline fixtures, not new native/live qualification.
"""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_private_council_formal_consumer_v1 import OfflineChancellorDriver
from test_council_assign_councillor_action_v1 import _ack, _receipt
from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    build_assign_councillor_request_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.private_council_formal_consumer_v1 import (
    RECEIPT_STEP, SUBMIT_STEP, read_council_ledger,
)


class NormalOccupiedChancellorDriver(OfflineChancellorDriver):
    nonwar_only = False

    def __init__(self, state_dir, *, candidate_skill=13, can_replace=True):
        super().__init__(state_dir, candidate_character_id=909, diplomacy=7)
        self.phase = "pre"
        self.candidate_skill = candidate_skill
        self.can_replace = can_replace
        self.new_holder = 910

    def capabilities(self):
        return {"action_steps": ["life-advance", "query-army-strengths-v1"],
                "bridge_capabilities": []}

    def take_internal_semantic_snapshot(self):
        value = super().take_internal_semantic_snapshot()
        revision = {"pre": 1, "post": 2, "current": 3}[self.phase]
        value.update(snapshot_id=f"native:{revision}", revision=revision,
                     native_revision=revision)
        return value

    take_snapshot = take_internal_semantic_snapshot

    def query_council_final_gates_private_v1(self, *, expected_revision, **arguments):
        value = super().query_council_final_gates_private_v1(
            expected_revision=expected_revision, **arguments)
        role = arguments.get("position_key", "councillor_steward")
        if role == "councillor_chancellor":
            payload = value["council_composition_candidates"]
            post = self.phase != "pre"
            payload["position"].update(incumbent_character_id=self.new_holder if post else 909,
                incumbent_main_skill={"key": "diplomacy", "value": self.candidate_skill if post else 7})
            payload["candidates"][0].update(character_id=self.new_holder + 1 if post else self.new_holder,
                main_skill={"key": "diplomacy", "value": self.candidate_skill})
            gate = value["council_final_gates"]["rows"][0]
            gate.update(character_id=payload["candidates"][0]["character_id"],
                        incumbent_can_be_fired=self.can_replace)
        return value

    def execute_step(self, step, *, expected_revision):
        value = super().execute_step(step, expected_revision=expected_revision)
        row = next(row for row in value["campaign_root_context"]["council"]["positions"]
                   if row["position_key"] == "councillor_chancellor")
        row["incumbent_character_id"] = self.new_holder if self.phase != "pre" else 909
        return value

    def submit_council_assign_private_v1(self, *, query, candidate_character_id,
                                       expected_revision, action_request_id):
        assert self.phase == "pre"
        assert self.last_queried_role == "councillor_chancellor"
        assert query["council_composition_candidates"]["position"]["incumbent_character_id"] == 909
        assert candidate_character_id == self.new_holder
        assert expected_revision == self.take_snapshot()["revision"]
        self.submit_calls += 1
        request = build_assign_councillor_request_v1(query["council_composition_candidates"],
            candidate_character_id=candidate_character_id, request_id=action_request_id)
        self.native_ack = _ack(request)
        return {"council_assign_councillor_ack": deepcopy(self.native_ack),
                "action_request_id": action_request_id, "request": request.as_wire_fields()}

    def query_council_assign_receipt_private_v1(self, *, pending, expected_revision):
        assert self.phase == "post"
        assert pending["council_assign_councillor_ack"] == self.native_ack
        assert expected_revision == self.take_snapshot()["revision"]
        self.receipt_calls += 1
        receipt = _receipt(self.native_ack)
        snapshot = self.take_snapshot()
        receipt.update(post_snapshot_id=snapshot["snapshot_id"],
            post_public_revision=snapshot["revision"], post_native_revision=snapshot["native_revision"],
            post_date_raw=snapshot["date_raw"])
        return {"council_assign_councillor_receipt": receipt}


def test_registered_normal_occupied_chancellor_gain_receipt_consume_equal_gate_and_priority(tmp_path):
    from mcp import Client

    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    records = []

    async def call(client, name):
        result = await client.call_tool(name, {})
        assert not result.is_error, result.content
        return result.structured_content

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("ordinary Council stays normal")), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("ordinary Council stays normal")):
            driver = NormalOccupiedChancellorDriver(tmp_path / "occupied-gain")
            async with Client(create_server(driver)) as client:
                observed = await call(client, "ck3_plan_turn")
                plan = observed["plan"]
                assert plan["selected_step"] == SUBMIT_STEP
                decision = plan["council_decision"]
                assert decision["position_key"] == "councillor_chancellor"
                assert decision["outcome"] == "REPLACE_REQUIRED" and decision["skill_gain"] == 6
                assert decision["incumbent_character_id"] == 909
                assert decision["selected_candidate"]["character_id"] == 910
                assert driver.role_queries == ["councillor_steward", "councillor_chancellor"]
                assert driver.submit_calls == 0
                submitted = await call(client, "ck3_auto_turn")
                pending = submitted["result"]
                assert pending["stage"] == "receipt_pending"
                ack = pending["action_ack"]["council_assign_councillor_ack"]
                assert ack["verification_pending"] is True
                assert ack["had_incumbent"] is True and ack["previous_incumbent_character_id"] == 909
                assert ack["route"] == "replace_incumbent" and ack["candidate_character_id"] == 910
                assert read_council_ledger(driver.state_dir)["applied"] is None
                waiting = await call(client, "ck3_plan_turn")
                assert waiting["plan"]["selected_step"] is None
                assert (driver.submit_calls, driver.receipt_calls) == (1, 0)

                driver.phase = "post"
                material = await call(client, "ck3_auto_turn")
                assert material["selected_step"] == RECEIPT_STEP
                assert material["result"]["status"] == "applied"
                assert material["result"]["independent_position"]["incumbent_character_id"] == 910
                assert material["result"]["receipt"]["council_assign_councillor_receipt"]["postcondition_verified"] is True
                driver.phase = "current"
                following = await call(client, "ck3_plan_turn")
                plan = following["plan"]
                assert plan["selected_step"] == "life-advance"
                assert plan["council_decision"]["outcome"] == "NO_CHANGE"
                assert plan["council_decision"]["reason_code"] == "incumbent_not_outperformed"
                assert plan["council_receipt_consumed"]["next_turn_consumed"] is True
                assert plan["council_receipt_consumed"]["next_turn_position"]["incumbent_character_id"] == 910
                assert read_council_ledger(driver.state_dir)["applied"]["next_turn_consumed"] is True
                assert (driver.submit_calls, driver.receipt_calls) == (1, 1)
            records.append({"scene": "occupied-chancellor-positive-gain", "diplomacy_gain": 6,
                "submit_count": 1, "ack_is_material": False, "independent_holder_verified": True,
                "following_consumed": True})

            for scene, skill, can_replace in (("equal-skill", 7, True), ("native-replacement-denied", 13, False)):
                blocked = NormalOccupiedChancellorDriver(tmp_path / scene,
                    candidate_skill=skill, can_replace=can_replace)
                async with Client(create_server(blocked)) as client:
                    observed = await call(client, "ck3_plan_turn")
                    plan = observed["plan"]
                    assert plan["selected_step"] == "life-advance"
                    assert plan["council_decision"]["outcome"] == "NO_CHANGE"
                    if scene == "equal-skill":
                        assert plan["council_decision"]["skill_gain"] == 0
                        assert plan["council_decision"]["reason_code"] == "incumbent_not_outperformed"
                    else:
                        assert plan["council_decision"]["legal_candidate_count"] == 0
                    assert blocked.submit_calls == blocked.receipt_calls == 0
                records.append({"scene": scene, "submit_count": 0})

            steward = NormalOccupiedChancellorDriver(tmp_path / "steward-first")
            steward.steward_improvement = True
            async with Client(create_server(steward)) as client:
                observed = await call(client, "ck3_plan_turn")
                assert observed["plan"]["selected_step"] == SUBMIT_STEP
                assert observed["plan"]["council_decision"]["position_key"] == "councillor_steward"
                assert steward.role_queries == ["councillor_steward"]
                assert steward.submit_calls == 0
            records.append({"scene": "useful-steward-keeps-priority", "chancellor_queries": 0})

            urgent = NormalOccupiedChancellorDriver(tmp_path / "urgent-war")
            urgent_plan = {**baseline, "phase": "native_war_army_strength_query",
                           "selected_step": "query-army-strengths-v1"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=urgent_plan):
                async with Client(create_server(urgent)) as client:
                    observed = await call(client, "ck3_plan_turn")
                    assert observed["plan"]["selected_step"] == "query-army-strengths-v1"
            assert urgent.role_queries == []
            assert urgent.submit_calls == urgent.receipt_calls == urgent.root_calls == 0
            records.append({"scene": "urgent-war-priority", "council_queries": 0})

    asyncio.run(run())
    output_path = os.environ.get("XAR_NORMAL_OCCUPIED_CHANCELLOR_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"schema": "xar.normal-occupied-chancellor-evidence12004.v1",
            "scenes": records, "boundary": "real registered normal Service and typed contracts; explicit synthetic Council DTO/Driver/baseline seams",
            "native_requalification": False, "live": False, "m4_complete": False}, indent=2) + "\n", encoding="utf-8")
