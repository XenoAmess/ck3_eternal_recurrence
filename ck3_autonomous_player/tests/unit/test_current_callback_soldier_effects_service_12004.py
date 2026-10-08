"""One new source-shaped registered-Service compound; Root owns FIRST."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest


class _CurrentCallbackEndpoint:
    """Supply whole source-shaped query bodies and correlate only the nonce."""

    pipe_name = r"\\.\pipe\source-current-callback-soldiers-not-live"

    def __init__(self):
        self.on_frame = None
        self.whole = None
        self.requests = []
        self.delivered = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        if self.on_frame is None:
            raise AssertionError("actual NativeDriver did not start the endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request.get("type") == "ping":
            self.publish({"protocol_version": 1, "type": "pong",
                          "request_id": request["request_id"]})
            return
        if (request.get("type") != "execute_step" or self.whole is None
                or request.get("step") != self.whole["result"]["step"]):
            raise AssertionError("fixture permits only the existing Army query")
        self.requests.append(deepcopy(request))
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self):
        pass


class CurrentCallbackSoldierEffectsService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_current_callback_budget_interleaves_conditional_soldier_stages(self):
        from test_current_callback_supply_risk_service_12004 import current_packet
        from test_native_bridge_driver import _army, _hello, _snapshot
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import (
            QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP,
        )

        self.assertEqual(sys.flags.optimize, 0)

        def packet(specs, fraction=40000, siege=2, raid=2):
            row = current_packet()
            strength_template = row["regiment_strengths"][0]
            data_template = row["regiment_replenishment_records_v1"][0]
            strengths, data_rows = [], []
            for index, (current, maximum, tier, eligible, skipped, physical, aliases) in enumerate(specs):
                regiment = 10 * (index + 1)
                strength = deepcopy(strength_template)
                strength.update(army_regiment_id=regiment, current_soldiers=current,
                                maximum_soldiers=maximum, siege_tier=tier,
                                maa_type_key=f"tier_{tier}", native_supply_loss_eligible=eligible)
                data = deepcopy(data_template)
                data.update(army_regiment_id=regiment, native_data_record_count=aliases,
                            native_loss_writer_skipped=skipped)
                record = data["records"][0]
                record.update(persistent_regiment_id=100 + regiment, chunk_index=0,
                              chunk_army_regiment_id=regiment, current_soldiers=physical,
                              effective_current_soldiers=physical,
                              maximum_soldiers=maximum // aliases, state_raw=0)
                data["records"] = [{**deepcopy(record), "record_index": i} for i in range(aliases)]
                strengths.append(strength)
                data_rows.append(data)
            row.update(regiment_count=len(strengths), regiment_strengths=strengths,
                       regiment_replenishment_records_v1=data_rows,
                       current_soldiers=sum(item["current_soldiers"] for item in strengths),
                       maximum_soldiers=sum(item["maximum_soldiers"] for item in strengths),
                       current_attrition_fraction_raw=0)
            row["monthly_loss_budget_inputs_v1"].update(
                loaded_supply_state_levels=[7, 0], loaded_supply_state_fractions_raw=[0, fraction],
                commander_valid=False, commander_supply_modifier_id=None,
                commander_supply_modifier_raw=None)
            row["loss_application_inputs_v1"].update(
                whole_soldiers=row["current_soldiers"],
                definition_le_zero_soldiers=sum(item["current_soldiers"] for item in strengths
                                               if item["siege_tier"] <= 0),
                supply_eligible_soldiers=sum(item["current_soldiers"] for item in strengths
                                             if item["native_supply_loss_eligible"]),
                definition_le_zero_supply_eligible_soldiers=sum(
                    item["current_soldiers"] for item in strengths
                    if item["siege_tier"] <= 0 and item["native_supply_loss_eligible"]),
                current_supply_loss_budget=0, siege_loss_budget=siege, raid_loss_budget=raid,
                siege_active=siege > 0, raid_active=raid > 0,
                raid_association_id=0 if raid > 0 else -1,
                siege_rate_raw=25000 if siege else 0, raid_rate_raw=25000 if raid else 0)
            return row

        ordinary = ((1, 1, 0, True, False, 1, 1),
                    (4, 4, 1, True, False, 4, 1),
                    (3, 3, 0, False, False, 3, 1))
        main = packet(ordinary)
        alias = packet(((4, 4, 0, True, False, 2, 2),), fraction=50000, siege=0, raid=0)
        skipped = packet(((1, 1, 0, True, True, 1, 1),), fraction=100000, siege=0, raid=0)
        zero = packet(ordinary)
        zero.update(current_supply_raw=None, current_supply_capacity_raw=None,
                    current_supply_change_monthly_raw=None)
        zero["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="unused_stock_inputs_unavailable",
            unit_native_170_raw=3, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None)
        missing = packet(ordinary)
        missing.pop("regiment_replenishment_records_v1")
        scenes = (("crossed-stock-four-pass", main, 2, 2, -6, 4),
                  ("physical-alias-reload", alias, 2, 0, -2, 4),
                  ("character-writer-skipped", skipped, 1, 1, 0, 1),
                  ("known-zero-unused-stock", zero, 0, 4, -4, 4),
                  ("positive-budget-missing-DATA", missing, 2, None, None, None))
        report = {
            "schema": "xar.current-callback-soldier-effects12004.registered-service.v1",
            "status": "RED", "sole_method": self._testMethodName,
            "registered_tool": "ck3_query_army_strengths", "scene_count": 5,
            "fixture_boundary": "New source-shaped whole query envelopes; original native reader not executed.",
            "compiled_native_producer": False, "old_GREEN_replays": 0,
            "live": False, "actual_loss": False, "actual_post_stage_current": None,
            "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
            "scenes": [],
        }

        def persist():
            if target := os.environ.get("XAR_CURRENT_CALLBACK_SOLDIER_EFFECTS_FIRST_OUTPUT"):
                path = Path(target)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        active = {}
        interesting = {
            ("mcp_server.py", "ck3_query_army_strengths"),
            ("service.py", "query_army_strengths"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("native_driver.py", "_execute_primitive_step"),
            ("war_contract.py", "normalize_army_strengths"),
            ("army_current_callback_supply_risk_projection.py", "project_current_callback_supply_risk_v1"),
            ("army_current_callback_soldier_effects_projection.py", "project_current_callback_soldier_effects_v1"),
            ("army_loss_sequence_replay.py", "project_conditional_army_loss_sequence"),
            ("army_chunk_loss_writeback_projection.py", "project_observed_writer_chunk_changes"),
            ("army_regiment_refresh_projection.py", "project_observed_raised_regiment_refresh"),
        }

        def observe(frame, event, value):
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in interesting or not active:
                return
            if event == "call":
                active["call_trace"].append({"source": frame.f_code.co_filename, "function": key[1]})
                if key == ("service.py", "query_army_strengths"):
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, driver)
            elif event == "return" and key == ("native_driver.py", "execute_step"):
                active["actual_driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", "query_army_strengths"):
                active["actual_service_result"] = deepcopy(value)

        prior_profile, prior_thread_profile = sys.getprofile(), threading.getprofile()
        endpoint, driver = _CurrentCallbackEndpoint(), None
        persist()
        try:
            with tempfile.TemporaryDirectory(prefix="current-callback-soldiers-") as temp:
                driver = NativeHeadlessGameplayDriver(
                    endpoint=endpoint, state_dir=Path(temp) / "state", save_dir=Path(temp) / "unused-save",
                    command_timeout_seconds=0.1, episode_projection="native_campaign")
                hello = _hello("bridge.heartbeat", "game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY)
                hello.update(game_version=CK3_12004.game_version,
                             executable_sha256=CK3_12004.executable_sha256)
                endpoint.publish(hello)
                server = create_server(driver)
                sys.setprofile(observe)
                threading.setprofile(observe)
                for index, (name, source, budget, final, delta, old_final) in enumerate(scenes, 1):
                    with self.subTest(scene=name):
                        original = deepcopy(source)
                        endpoint.whole = {
                            "type": "command_result", "protocol_version": 1,
                            "request_id": f"authored-{name}", "ok": True,
                            "result": {"step": QUERY_ARMY_STRENGTHS_STEP, "accepted": True,
                                       "status": "available", "query_sequence": index,
                                       "army_strengths": [deepcopy(source)]},
                        }
                        authority = deepcopy(endpoint.whole)
                        endpoint.publish(_snapshot(
                            revision=index, date_raw=264,
                            played_character={"character_id": 29829, "alive": True, "name": "Robert"},
                            player_armies=[_army(0, soldiers=source["current_soldiers"], owner_character_id=29829)],
                            active_wars=[]))
                        before = driver.take_snapshot()
                        active = {"scene": name, "status": "RED", "call_trace": [],
                                  "source_shaped_native_envelope": authority}
                        report["scenes"].append(active)
                        response = await server.call_tool("ck3_query_army_strengths", {
                            "army_ids": [0], "expected_revision": before["revision"]})
                        active["registered_response"] = response.model_dump(mode="json", by_alias=True)
                        self.assertIs(response.is_error, False)
                        result = response.structured_content
                        self.assertIsInstance(result, dict)
                        self.assertEqual(result, active["actual_service_result"])
                        self.assertEqual(response.model_dump(mode="json", by_alias=True)["structuredContent"], result)
                        self.assertEqual(result["source"]["game_version"], "1.20.0.4")
                        self.assertEqual(result["source"]["executable_sha256"].upper(), CK3_12004.executable_sha256.upper())
                        self.assertEqual(result["queried_native_revision"], index)
                        self.assertEqual(len(endpoint.requests), index)
                        self.assertEqual(endpoint.requests[-1]["expected_revision"], index)
                        self.assertEqual(endpoint.delivered[-1]["result"], authority["result"])
                        self.assertEqual(endpoint.whole, authority)
                        self.assertEqual(source, original)
                        for raw_key, value in original.items():
                            self.assertEqual(result["army_strengths"][0][raw_key], value, raw_key)
                            self.assertEqual(driver._army_strength_query["army_strengths"][0][raw_key], value, raw_key)
                        effects = result["current_callback_soldier_effects_v1"][0]["projection"]
                        risk = result["current_callback_supply_risk_v1"][0]["projection"]
                        sequence = effects["conditional_loss_sequence_v1"]
                        self.assertEqual(effects["source_contract_game_version"], "1.20.0.4")
                        self.assertEqual(effects["source_entries"], {
                            "caller": "24E3410", "writer": "2634190", "record_selector": "260DB50",
                            "current_setter": "2657E80", "raised_refresh": "2633320", "residual_allocator": "2A957E0"})
                        self.assertEqual(sequence["source_contract_game_version"], "1.20.0.3")
                        self.assertIs(effects["conditional_supply_budget_ready"], True)
                        self.assertEqual(effects["conditional_supply_budget_soldiers"], budget)
                        self.assertEqual(effects["observed_current_supply_budget_soldiers"], 0)
                        self.assertEqual((effects["observed_siege_budget_soldiers"], effects["observed_raid_budget_soldiers"]),
                                         (source["loss_application_inputs_v1"]["siege_loss_budget"], source["loss_application_inputs_v1"]["raid_loss_budget"]))
                        self.assertEqual(sequence["conditional_final_current_soldiers"], final)
                        self.assertEqual(sequence["conditional_physical_current_delta"], delta)
                        self.assertIs(effects["conditional_soldier_effects_ready"], final is not None)
                        self.assertIs(effects["ready"], final is not None)
                        allocation = result["loss_allocation_requests_v1"][0]
                        self.assertEqual(allocation["same_input_conditional_loss_sequence_v1"]["conditional_final_current_soldiers"], old_final)
                        self.assertIs(allocation["applied_loss_ready"], False)
                        self.assertIsNone(allocation["applied_soldier_loss"])
                        self.assertIs(sequence["actual_loss"], False)
                        self.assertIsNone(sequence["actual_post_stage_current"])
                        for key in ("actual_callback_observed", "actual_loss", "earlier_stage_outputs_reconstructed",
                                    "future_callback_selection_ready", "full_daily_supply_transition_ready", "full_monthly_ready"):
                            self.assertIs(effects[key], False, key)
                        self.assertIsNone(effects["actual_post_stage_current"])
                        phases = sequence["passes"]
                        if name == "crossed-stock-four-pass":
                            self.assertEqual(risk["conditional_post_stock_raw"], 650000)
                            self.assertEqual(risk["observed_subject_callback_positions"], [1, 3])
                            self.assertEqual([stage["phase"] for stage in phases], [
                                "supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"])
                            self.assertEqual([stage["native_filter_flags"] for stage in phases], [3, 2, 1, 0])
                            self.assertEqual([stage["request_budget_soldiers"] for stage in phases], [2, 1, 4, 1])
                            self.assertEqual([stage["native_eligible_total_soldiers"] for stage in phases], [1, 4, 3, 3])
                            self.assertEqual([[request["requested_soldiers"] for request in stage["requests"]] for stage in phases],
                                             [[1], [0, 1], [0, 3], [0, 1]])
                            self.assertEqual([item["current_soldiers"] for item in sequence["conditional_final_regiment_strengths"]], [0, 2, 0])
                        elif name == "physical-alias-reload":
                            writer = phases[0]["requests"][0]["conditional_chunk_writeback"]
                            self.assertEqual(writer["physical_current_delta"], -2)
                            self.assertEqual(writer["conditional_raised_regiment_refresh"]["current_soldiers"], 0)
                            self.assertEqual([(write["pass"], write["current_before"], write["current_after"]) for write in writer["writes"]],
                                             [(1, 2, 0), (2, 0, 0)])
                            self.assertEqual(len(sequence["conditional_physical_chunks_after"]), 1)
                        elif name == "character-writer-skipped":
                            request = phases[0]["requests"][0]
                            self.assertEqual(request["requested_soldiers"], 1)
                            writer = request["conditional_chunk_writeback"]
                            self.assertIs(writer["writer_skipped"], True)
                            self.assertIs(writer["refresh_requested"], False)
                            self.assertEqual(writer["conditional_raised_regiment_refresh"]["status"], "not_called")
                        elif name == "known-zero-unused-stock":
                            self.assertIs(risk["ready"], False)
                            self.assertIs(risk["conditional_callback_admitted"], False)
                            self.assertEqual(risk["admission_rejection"], "unit_native_170_raw")
                            self.assertIs(effects["conditional_post_stock_ready"], False)
                            self.assertIsNone(effects["conditional_post_stock_raw"])
                            self.assertEqual(effects["missing_inputs"], [])
                        else:
                            self.assertEqual(effects["status"], "partial")
                            self.assertEqual(sequence["status"], "partial")
                            self.assertIs(sequence["conditional_sequence_ready"], False)
                            self.assertIsNone(sequence["conditional_final_regiment_strengths"])
                            self.assertEqual(effects["missing_inputs"], [{
                                "phase": "supply_preferred", "army_regiment_id": 10,
                                "inputs": ["matching_native_regiment_and_DATA"]}])
                        executed = {(Path(item["source"]).name, item["function"]) for item in active["call_trace"]}
                        reached = interesting - ({("army_regiment_refresh_projection.py", "project_observed_raised_regiment_refresh")}
                                                 if name in {"character-writer-skipped", "positive-budget-missing-DATA"} else set())
                        self.assertTrue(reached <= executed)
                        self.assertEqual(sum(item["function"] == "project_current_callback_supply_risk_v1"
                                             for item in active["call_trace"]), 1)
                        self.assertEqual(sum(item["function"] == "query_army_strengths"
                                             for item in active["call_trace"]), 1)
                        active.update(status="GREEN", registered_result=result,
                                      driver_cache=deepcopy(driver._army_strength_query),
                                      transport_request=deepcopy(endpoint.requests[-1]))
                        persist()
                self.assertEqual(len(report["scenes"]), 5)
                self.assertTrue(all(scene["status"] == "GREEN" for scene in report["scenes"]))
                self.assertEqual(len(endpoint.requests), 5)
                report.update(status="GREEN", actual_registered_queries=5,
                              actual_native_driver_queries=5, actual_service_queries=5)
        except BaseException as error:
            report["failure"] = {"type": type(error).__name__, "message": str(error)}
            raise
        finally:
            sys.setprofile(prior_profile)
            threading.setprofile(prior_thread_profile)
            if driver is not None:
                driver.close()
            persist()


if __name__ == "__main__":
    unittest.main()
