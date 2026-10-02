"""The actual feast.7002 scope shape through the existing production pipeline."""

from __future__ import annotations

import unittest

from test_event_window_context_v1_bridge import _frame, _scope
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.outcome import (
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


class FeastArrival12003PolicyTests(unittest.TestCase):
    def test_sole_host_choice_uses_actual_prestige_observations(self) -> None:
        player = 31853
        context = _frame()
        context.update({
            "event_definition_key": "feast.7002",
            "snapshot_revision": 23, "date_raw": 53328600,
            "current_event_instance_id": 14,
            "root_scope": _scope(character_id=player),
            "saved_scopes": [
                {"name": "activity", "name_identifier": 1,
                 "scope": _scope(raw_type_index=3, type_key="activity", character_id=None)},
                {"name": "host", "name_identifier": 2, "scope": _scope(character_id=player)},
                {"name": "province", "name_identifier": 3,
                 "scope": _scope(raw_type_index=8, type_key="province", character_id=None)},
            ],
            "provenance": {
                "root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC408",
                "manager_offset": "+0x28", "backend_id": "ck3-1.20.0.3-native-event-window-v1",
            },
        })
        option = context["options"][0]
        option.update({
            "native_option_index": 0, "shown": True, "enabled": True,
            "fallback": False, "cancel": False,
            "resolved_name": "We have a lovely time ahead of us!", "unavailable_reason": "",
        })
        option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
        option["effect_indicators"]["rows"] = []
        context = normalize_current_event_window_context_v1(
            context, expected_event_instance_id=14, expected_date_raw=53328600,
            expected_snapshot_revision=23,
        )
        for build in ("1.19.0.6", "1.20.0.2"):
            self.assertEqual(query_vanilla_event_knowledge_v1("feast.7002", build)["status"], "unavailable")
        knowledge = query_vanilla_event_knowledge_v1("feast.7002", "1.20.0.3")
        self.assertEqual(knowledge["status"], "available")
        self.assertFalse(knowledge["analysis"]["new_live_evidence"])
        snapshot = {
            "snapshot_id": "native:23", "revision": 2, "native_revision": 23,
            "date_raw": 53328600, "paused": True, "backend_id": "native-headless",
            "played_character": {"character_id": player, "alive": True},
            "played_character_prestige": {"raw": 42_000_000, "scale": 100_000},
            "active_event": {"instance_id": 14, "option_count": 1},
        }
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "accepted": True,
                "status": "available", "snapshot_revision": 23,
                "current_event_instance_id": 14, "date_raw": 53328600,
                "current_event_window_context": context,
                "queried_snapshot_id": "native:23", "queried_revision": 2,
                "queried_native_revision": 23,
            },
        }]
        plan = choose_one_life_turn(
            history, snapshot=snapshot,
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "select-event-option-1"},
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 0)
        self.assertTrue(plan["event_decision"]["checks"]["scope:host:character_id"])
        self.assertEqual(plan["event_campaign_utility"]["comparison_kind"], "sole_legal_route")
        expectation = plan["event_material_postcondition"]
        self.assertEqual(expectation["status"], "ready")
        self.assertEqual(expectation["metric"], "played_character_prestige.raw")
        self.assertEqual(expectation["expected_relation"], "strictly_increasing")
        selection = {
            "postcondition_verified": True,
            "starting_snapshot_id": "native:23", "starting_revision": 2,
            "ending_snapshot_id": "native:24", "ending_revision": 3,
            "starting_played_character_prestige": {
                "status": "available", "character_id": player, "prestige_raw": 42_000_000, "scale": 100_000,
            },
            "ending_played_character_prestige": {
                "status": "available", "character_id": player, "prestige_raw": 45_500_000, "scale": 100_000,
            },
        }
        material = evaluate_registered_event_material_postcondition_v1(expectation, selection)
        self.assertEqual(material["status"], "verified_change")
        self.assertEqual(material["delta"], 3_500_000)
        selection["ending_played_character_prestige"]["prestige_raw"] = 42_000_000
        no_change = evaluate_registered_event_material_postcondition_v1(expectation, selection)
        self.assertEqual(no_change["status"], "failed")
        self.assertEqual(no_change["unavailable_reason"], "prestige_not_increased")
        old_decision = {**plan["event_decision"], "ck3_build": "1.20.0.2"}
        self.assertIsNone(plan_registered_event_material_postcondition_v1(
            old_decision, snapshot["played_character"],
            played_character_prestige=snapshot["played_character_prestige"],
            snapshot_id="native:23", revision=2,
        ))


    def test_feast_start_actual_sole_option_uses_service_and_observed_advance(self) -> None:
        import copy
        from test_pending_character_interaction_context_v1_bridge import _FakeEndpoint, _semantic_snapshot
        from xar_autoplayer.bridge.event_window_context_contract import _EVENT_PROVENANCE_BY_BACKEND
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12003

        player, event_id, date_raw, native_revision = 31853, 15, 53330784, 23
        context = _frame()
        context.update({
            "event_definition_key": "feast.2001", "calculated_event_id": 5162001,
            "runtime_stats_ordinal": 8308, "snapshot_revision": native_revision,
            "date_raw": date_raw, "current_event_instance_id": event_id,
            "root_scope": _scope(character_id=player),
            "saved_scopes": [
                {"name": "activity", "name_identifier": 2,
                 "scope": _scope(raw_type_index=6, type_key="activity", character_id=None)},
                {"name": "host", "name_identifier": 62, "scope": _scope(character_id=player)},
                {"name": "province", "name_identifier": 37,
                 "scope": _scope(raw_type_index=8, type_key="province", character_id=None)},
            ],
            "provenance": copy.deepcopy(_EVENT_PROVENANCE_BY_BACKEND[CK3_12003.backend_id("event-window-v1")]),
        })
        option = context["options"][0]
        option.update({
            "rendered_index": 0, "native_option_index": 0, "shown": True,
            "enabled": True, "fallback": False, "cancel": False,
            "resolved_name": "\u6b22\u8fce\uff0c\u670b\u53cb\u4eec\uff01", "unavailable_reason": "",
        })
        option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
        option["effect_indicators"]["rows"] = []
        context = normalize_current_event_window_context_v1(
            context, expected_event_instance_id=event_id, expected_date_raw=date_raw,
            expected_snapshot_revision=native_revision,
        )
        knowledge = query_vanilla_event_knowledge_v1("feast.2001", CK3_12003.game_version)
        self.assertEqual(knowledge["status"], "available")
        self.assertFalse(knowledge["analysis"]["new_live_evidence"])

        endpoint = _FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1)
        endpoint.publish({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 7878, "session_generation": 0,
            "game_version": CK3_12003.game_version,
            "expected_ck3_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command.select-event-option-N"],
        })
        before_wire = _semantic_snapshot(native_revision)
        before_wire["state"].update({
            "date_raw": date_raw,
            "played_character": {"character_id": player, "alive": True},
            "active_event": {"instance_id": event_id, "option_count": 5},
            "pending_character_interaction": None,
        })
        endpoint.publish(before_wire)
        before = driver.take_snapshot()
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "accepted": True,
                "status": "available", "snapshot_revision": native_revision,
                "current_event_instance_id": event_id, "date_raw": date_raw,
                "current_event_window_context": context,
                "queried_snapshot_id": before["snapshot_id"], "queried_revision": before["revision"],
                "queried_native_revision": native_revision,
            },
        }]
        plan = choose_one_life_turn(
            history, snapshot=before,
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "select-event-option-1"},
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        decision = plan["event_decision"]
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertTrue(decision["checks"]["scope:host:character_id"])
        self.assertEqual(decision["choice_effect_profile"]["selected_option_effects"], [])
        self.assertEqual(decision["choice_effect_profile"]["common_after_effects"], [])
        self.assertIsNone(decision["choice_effect_profile"]["observable_postcondition"])
        self.assertEqual(plan["event_campaign_utility"]["comparison_kind"], "sole_legal_route")
        self.assertEqual(plan["event_campaign_utility"]["selected_utility"]["material_direction"], "neutral")
        self.assertIsNone(plan.get("event_material_postcondition"))

        def answer(request):
            if request.get("type") != "execute_step":
                return
            self.assertEqual(request["step"], plan["selected_step"])
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": True,
                              "result": {"accepted": True}})
            after_wire = copy.deepcopy(before_wire)
            after_wire["revision"] = native_revision + 1
            after_wire["snapshot_id"] = f"native:{native_revision + 1}"
            after_wire["state"]["active_event"] = None
            endpoint.publish(after_wire)
        endpoint.send_hook = answer
        service = GameplayBridgeService(driver)
        result = service.select_event_option(
            decision["selected_option_number"], event_instance_id=event_id,
            expected_revision=before["revision"],
        )
        selection = result["event_selection"]
        self.assertEqual(result["event_instance_id"], event_id)
        self.assertEqual(result["option_number"], 1)
        self.assertEqual(selection["selected_native_option_index"], 0)
        self.assertTrue(selection["postcondition_verified"])
        self.assertEqual(selection["old_event_instance_id"], event_id)
        self.assertIsNone(selection["new_event_instance_id"])
        after = service.snapshot()
        self.assertIsNone(after["active_event"])
        self.assertTrue(after["paused"])
        self.assertEqual(after["played_character"]["character_id"], player)
        self.assertEqual(after["date_raw"], date_raw)



    def test_feast_drinks_actual_two_options_use_service_and_observed_gold_decrease(self) -> None:
        import copy
        from test_pending_character_interaction_context_v1_bridge import _FakeEndpoint, _semantic_snapshot
        from xar_autoplayer.bridge.event_window_context_contract import _EVENT_PROVENANCE_BY_BACKEND
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12003

        player, event_id, date_raw, native_revision = 31853, 16, 53330832, 9
        context = _frame()
        context.update({
            "event_definition_key": "feast_default.6231", "calculated_event_id": 4796231,
            "runtime_stats_ordinal": 7457, "snapshot_revision": native_revision,
            "date_raw": date_raw, "current_event_instance_id": event_id,
            "root_scope": _scope(character_id=player),
            "saved_scopes": [
                {"name": "activity", "name_identifier": 2,
                 "scope": _scope(raw_type_index=6, type_key="activity", character_id=None)},
                {"name": "host", "name_identifier": 62, "scope": _scope(character_id=player)},
                {"name": "province", "name_identifier": 37,
                 "scope": _scope(raw_type_index=8, type_key="province", character_id=None)},
                {"name": "drunk_guest", "name_identifier": 29266,
                 "scope": _scope(character_id=16843458)},
            ],
            "provenance": copy.deepcopy(_EVENT_PROVENANCE_BY_BACKEND[CK3_12003.backend_id("event-window-v1")]),
        })
        template = context["options"][0]
        context["options"] = []
        labels = (
            "\u8461\u8404\u9152\u5546\u5e94\u8be5\u8fd8\u5728\u57ce\u9547\u91cc\uff01",
            "\u6211\u4eec\u90fd\u5fc5\u987b\u6295\u5165\u8fdb\u6765\u3002\u7aef\u4e0a\u6765\u5427\u3002",
        )
        for native_index, label in enumerate(labels):
            option = copy.deepcopy(template)
            option.update({
                "rendered_index": native_index, "native_option_index": native_index,
                "shown": True, "enabled": True, "fallback": False, "cancel": False,
                "resolved_name": label, "unavailable_reason": "",
            })
            option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
            option["effect_indicators"]["rows"] = []
            context["options"].append(option)
        context = normalize_current_event_window_context_v1(
            context, expected_event_instance_id=event_id, expected_date_raw=date_raw,
            expected_snapshot_revision=native_revision,
        )
        self.assertEqual(len(context["options"]), 2)
        knowledge = query_vanilla_event_knowledge_v1("feast_default.6231", CK3_12003.game_version)
        self.assertEqual(knowledge["status"], "available")
        self.assertFalse(knowledge["analysis"]["new_live_evidence"])

        endpoint = _FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1)
        endpoint.publish({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 7878, "session_generation": 0,
            "game_version": CK3_12003.game_version,
            "expected_ck3_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command.select-event-option-N"],
        })
        before_wire = _semantic_snapshot(native_revision)
        before_wire["state"].update({
            "date_raw": date_raw,
            "played_character": {"character_id": player, "alive": True},
            "active_event": {"instance_id": event_id, "option_count": 4},
            "pending_character_interaction": None,
            # Synthetic observations test decrease; this is not the live fee.
            "played_character_gold": {"raw": 100_000_000, "scale": 100_000},
        })
        endpoint.publish(before_wire)
        before = driver.take_snapshot()
        self.assertEqual(before["active_event"]["option_count"], 4)
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "accepted": True,
                "status": "available", "snapshot_revision": native_revision,
                "current_event_instance_id": event_id, "date_raw": date_raw,
                "current_event_window_context": context,
                "queried_snapshot_id": before["snapshot_id"], "queried_revision": before["revision"],
                "queried_native_revision": native_revision,
            },
        }]
        plan = choose_one_life_turn(
            history, snapshot=before,
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                          "select-event-option-1", "select-event-option-2"},
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        decision = plan["event_decision"]
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["selected_option_number"], 1)
        self.assertTrue(decision["checks"]["scope:host:character_id"])
        utility = plan["event_campaign_utility"]
        self.assertEqual(utility["comparison_kind"], "source_reviewed_ordinal")
        self.assertEqual((utility["selected_rank"], utility["rank_count"]), (1, 2))
        expectation = plan["event_material_postcondition"]
        self.assertEqual(expectation["status"], "ready")
        self.assertEqual(expectation["metric"], "played_character_gold.raw")
        self.assertEqual(expectation["expected_relation"], "strictly_decreasing")

        def answer(request):
            if request.get("type") != "execute_step":
                return
            self.assertEqual(request["step"], plan["selected_step"])
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": True,
                              "result": {"accepted": True}})
            after_wire = copy.deepcopy(before_wire)
            after_wire["revision"] = native_revision + 1
            after_wire["snapshot_id"] = f"native:{native_revision + 1}"
            after_wire["state"]["active_event"] = None
            after_wire["state"]["played_character_gold"]["raw"] = 99_000_000
            endpoint.publish(after_wire)
        endpoint.send_hook = answer
        service = GameplayBridgeService(driver)
        result = service.select_event_option(
            decision["selected_option_number"], event_instance_id=event_id,
            expected_revision=before["revision"],
        )
        selection = result["event_selection"]
        self.assertEqual(result["event_instance_id"], event_id)
        self.assertEqual(selection["selected_native_option_index"], 0)
        self.assertTrue(selection["postcondition_verified"])
        self.assertEqual(selection["old_event_instance_id"], event_id)
        self.assertIsNone(selection["new_event_instance_id"])
        after = service.snapshot()
        self.assertIsNone(after["active_event"])
        self.assertTrue(after["paused"])
        self.assertEqual(after["played_character"]["character_id"], player)
        self.assertEqual(after["date_raw"], date_raw)
        self.assertEqual(selection["starting_played_character_gold"]["gold_raw"], 100_000_000)
        self.assertEqual(selection["ending_played_character_gold"]["gold_raw"], 99_000_000)
        material = evaluate_registered_event_material_postcondition_v1(expectation, selection)
        self.assertEqual(material["status"], "verified_change")
        self.assertEqual(material["delta"], -1_000_000)



if __name__ == "__main__":
    unittest.main()
