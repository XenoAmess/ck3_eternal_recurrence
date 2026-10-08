"""One offline actual-driver compound for the ordinary hire strength fallback.

Root runs this explicit CLI once. The Army packet/context are retained qualified
producer inputs. Holy-order, hire, cash and enclosing snapshots are synthetic
transport callbacks, never live game outcomes. No old test case is imported.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


_CONFIG: dict[str, Path] = {}
_ARMY_STEP = "query-army-strengths-v1"
_HOLY_STEP = "query-player-holy-order-context-v1"
_HIRE_STEP = "hire-holy-order-v1"
_CASH_STEP = "query-war-cash-current-resources-v1"


class HolyOrderNativeReadbackV1Tests(unittest.TestCase):
    def test_actual_native_driver_ordinary_hire_and_service_strength_fallback(self) -> None:
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build
        from xar_autoplayer.bridge.war_contract import normalize_army_strengths

        fixture_path = _CONFIG["native_fixture"]
        context_path = _CONFIG["native_context"]
        output_dir = _CONFIG["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=False)
        fixture_bytes = fixture_path.read_bytes()
        context_bytes = context_path.read_bytes()
        packet = json.loads(fixture_bytes.decode("utf-8-sig"))
        native_context = json.loads(context_bytes.decode("utf-8-sig"))
        report = {
            "schema": "xar.holy-order-native-strength-fallback-first.v1",
            "status": "RED", "new_compound_cases": 1, "old_case_executions": 0,
            "source_root": str(_CONFIG["source_root"]),
            "qualified_army_packet": str(fixture_path),
            "qualified_army_context": str(context_path),
            "synthetic_holy_hire_cash_and_snapshots": True,
            "new_native_producer_executions": 0, "sdk_calls": 0,
            "game_operations": 0, "live": False,
        }
        endpoint = None
        driver = None
        try:
            self.assertEqual(set(packet), {"type", "protocol_version", "request_id", "ok", "result"})
            self.assertEqual(packet["type"], "command_result")
            self.assertEqual(packet["protocol_version"], 1)
            self.assertIs(packet["ok"], True)
            self.assertEqual(packet["request_id"], "unit-first-edge-selection-edge_above_cost")
            self.assertEqual(native_context["scene"], "edge_above_cost")
            identity = native_context["actual4_identity"]
            self.assertEqual(require_exact_native_build(identity["game_version"], identity["executable_sha256"]), CK3_12004)
            original = packet["result"]
            self.assertEqual(set(original), {"step", "accepted", "status", "query_sequence", "army_strengths"})
            self.assertEqual(original["step"], _ARMY_STEP)
            self.assertIs(original["accepted"], True)
            self.assertEqual(original["status"], "available")
            self.assertEqual(original["query_sequence"], 1)
            self.assertEqual(len(original["army_strengths"]), 1)
            native_row = original["army_strengths"][0]
            self.assertEqual((native_row["army_id"], native_row["native_carmy_id"], native_row["current_soldiers"]),
                             (16777217, 33554433, 100))
            self.assertEqual(native_row["scope_role"], "player")
            self.assertEqual(native_row["war_ids"], [])
            self.assertEqual([row["army_regiment_id"] for row in native_row["regiment_strengths"]],
                             [50331649, 50331649])
            scope = [{"army_id": native_row["army_id"], "scope_role": "player", "war_ids": []}]
            expected_rows = normalize_army_strengths(deepcopy(original["army_strengths"]), expected_scope=scope)
            frame = native_context["synthetic_context"]
            self.assertEqual((frame["actor_character_id"], frame["native_revision"], frame["date_raw"]),
                             (29829, 1, 53288448))

            test = self

            class Endpoint:
                pipe_name = r"\\.\pipe\holy-order-native-readback-offline"

                def __init__(self) -> None:
                    self.on_frame = None
                    self.submitted = False
                    self.requests = []
                    self.responses = []
                    self.native_hire_body = None

                def start(self, on_frame, on_disconnect) -> None:
                    self.on_frame = on_frame

                def publish(self, value) -> None:
                    test.assertTrue(callable(self.on_frame))
                    self.on_frame(deepcopy(value))

                def snapshot(self, *, include_native_command_history=True):
                    # Keep the qualified packet's original native clock. These
                    # public before/after views and material changes are synthetic.
                    public_revision = 42 if self.submitted else 41
                    return {
                        "snapshot_id": f"synthetic-holy-material:{public_revision}",
                        "revision": public_revision, "native_revision": frame["native_revision"],
                        "date_raw": frame["date_raw"], "paused": True, "map_ready": True,
                        "backend_id": "native-headless", "history": [],
                        "active_event": None, "pending_character_interaction": None,
                        "played_character": {"character_id": 29829, "alive": True},
                        "active_wars": [{"war_id": 44, "allied_armies": [], "enemy_armies": []}],
                        "player_armies": [{"army_id": native_row["army_id"], "controllable": True,
                            "owner_character_id": 4444, "current_province_id": 460,
                            "soldiers": native_row["current_soldiers"]}] if self.submitted else [],
                        "played_character_gold": {"raw": 1000000, "scale": 100000},
                        "played_character_prestige": {"raw": 300000, "scale": 100000},
                        "played_character_piety": {"raw": 800000 if self.submitted else 1000000, "scale": 100000},
                        "diagnostics": {"connection_generation": 1, "hello": {
                            "expected_ck3_version": CK3_12004.game_version,
                            "expected_ck3_sha256": CK3_12004.executable_sha256}},
                    }

                def holy_context(self):
                    association = {"available": True, "unavailable_reason": None,
                                   "applies_to_player": self.submitted, "rows": []}
                    if self.submitted:
                        association["rows"] = [{"regiment_id": row["army_regiment_id"],
                            "available": True, "unavailable_reason": None, "regiment_resolved": True,
                            "native_carmy_id": native_row["native_carmy_id"], "native_carmy_resolved": True,
                            "combat_id": None, "combat_resolved": False} for row in native_row["regiment_strengths"]]
                    return {
                        "schema": "ck3_12004_player_holy_order_context_v1", "read_only": True,
                        "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
                        "available": True, "unavailable_reason": None, "capture_epoch": 12004,
                        "date_raw": frame["date_raw"], "played_character_id": 29829, "raw_scale": 100000,
                        "rows": [{"holy_order_id": 0, "rite_id": 152, "is_military": True,
                            "founder_id": 4444, "patron_id": 4444, "employer_id": 29829 if self.submitted else None,
                            "leased_title_ids": [], "military_terms": {
                                "available": True, "unavailable_reason": None, "resource_scale": 100000,
                                "can_hire": not self.submitted, "can_afford": True,
                                "can_hire_reasons_available": True,
                                "can_hire_reason_literal": "already hired" if self.submitted else "",
                                "can_afford_reasons_available": True, "can_afford_reason_literal": "",
                                "resource_costs_raw": [0, 0, 200000, 0, 0, 0, 0, 0, 0, 0],
                                "current_war_eligibility": {"available": True, "unavailable_reason": None,
                                    "qualifies": True, "reasons_available": True, "reason_literal": ""},
                                "troop_strength": {"available": True, "unavailable_reason": None,
                                    "current_soldiers": native_row["current_soldiers"]},
                                "troop_association": association}}],
                    }

                def cash_context(self):
                    expenses = {}
                    for kind, amount in (("current", 0), ("all_raised", 100000)):
                        vector = [amount] + [0] * 9
                        expenses[kind] = {"status": "available", "owner_character_id": 29829,
                            "resource_id": "29829", "war_ids": [44], "raw_scale": 100000,
                            "time_basis": "month", "source_scope": "actor_owned_military_once_across_all_wars",
                            "future_war_cost_upper_ready": False, "resource_raw_native": vector,
                            "gold_raw": amount, "treasury_raw": 0, "unavailable_reason": None}
                    return {"schema": "xar.ck3.war-cash-current-resources.v1",
                        "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
                        "read_only": True, "advertised": False, "formal_action_ready": False,
                        "status": "available", "played_character_id": 29829,
                        "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
                        "active_war_ids": [44], "player_army_ids": [native_row["army_id"]],
                        "current_treasury": {"raw": 1000000, "scale": 100000},
                        "player_monthly_net_income": {"raw": 250000, "scale": 100000},
                        "military_expenses": expenses}

                def send(self, request) -> None:
                    test.assertEqual(request["type"], "execute_step")
                    test.assertEqual(request["expected_revision"], frame["native_revision"])
                    self.requests.append(deepcopy(request))
                    step = request["step"]
                    if step == _ARMY_STEP:
                        test.assertTrue(self.submitted, "Army read must follow the material post-hire query")
                        test.assertEqual(request["request_id"], packet["request_id"])
                        self.responses.append({"source": "qualified_native_whole_army", "packet": deepcopy(packet)})
                        self.publish(packet)
                        return
                    if step == _HIRE_STEP:
                        test.assertFalse(self.submitted, "ordinary typed hire must be submitted once")
                        test.assertEqual(request["holy_order_id"], 0)
                        body = {"step": step, "game_version": CK3_12004.game_version,
                            "executable_sha256": CK3_12004.executable_sha256, "read_only": False,
                            "command_sequence": 1, "snapshot_revision": frame["native_revision"],
                            "date_raw": frame["date_raw"], "accepted": True, "status": "submitted_verification_pending",
                            "holy_order_hire": {"schema": "ck3_12004_holy_order_hire_action_v1", "status": "submitted",
                                "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
                                "holy_order_id": 0, "actor_character_id": 29829, "native_hire_mode": 3,
                                "holy_order_resolved": True, "native_command_validation_observable": True,
                                "native_command_valid": True, "command_submitted": True,
                                "verification_pending": True, "after_state_observed": False,
                                "prior_employer_character_id": None, "unavailable_reason": None,
                                "prior_context": self.holy_context()}}
                        self.native_hire_body = deepcopy(body)
                    elif step in (_HOLY_STEP, _CASH_STEP):
                        test.assertEqual(request["expected_snapshot_revision"], frame["native_revision"])
                        test.assertTrue(request["request_id"].startswith("g2-read-"))
                        body = {"step": step, "accepted": True, "private_build": True,
                            "read_only": True, "advertised": False,
                            "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
                            "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"]}
                        if step == _HOLY_STEP:
                            body.update(status="observed", domain_key="player_holy_order_context_v1",
                                backend_id="ck3-1.20.0.4-msvc-x64-player-holy-order-context-v1",
                                player_holy_order_context=self.holy_context())
                        else:
                            test.assertTrue(self.submitted)
                            body["war_cash_current_resources"] = self.cash_context()
                    else:
                        test.fail(f"unexpected transport step: {step}")
                    response = {"type": "command_result", "protocol_version": 1,
                        "request_id": request["request_id"], "ok": True, "result": body}
                    self.responses.append({"source": "synthetic_holy_hire_or_cash_callback", "packet": deepcopy(response)})
                    self.publish(response)
                    if step == _HIRE_STEP:
                        self.submitted = True

                def transport_error(self):
                    return None

                def close(self) -> None:
                    pass

            endpoint = Endpoint()
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                 command_timeout_seconds=1.0, episode_projection="native_campaign")
            self.assertIs(type(driver), NativeHeadlessGameplayDriver)
            self.assertFalse(hasattr(driver, "query_army_strengths"), "the actual driver must exercise Service fallback")
            driver.allow_private_player_religion_context_query = True
            driver.allow_private_war_cash_query = True
            capabilities = {"backend_id": "native-headless", "snapshot": True,
                "action_steps": [_HIRE_STEP, _ARMY_STEP],
                "bridge_capabilities": ["game.state.snapshot", "game.command." + _HIRE_STEP,
                                        "game.command." + _ARMY_STEP]}
            endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": frame["bridge_host_pid"], "session_generation": 0,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": capabilities["bridge_capabilities"]})
            baseline = {"policy": "one-life-turn-v1", "phase": "native_war_siege_exit_blocked",
                "selected_step": None, "siege_state": {"status": "insufficient_strength",
                    "province_id": 2592, "player_army_besieging": True, "garrison_size": 200,
                    "besieging_strength": 150}, "pursuit": {"war_id": 44}}
            strength_calls = []
            original_reader = GameplayBridgeService.query_army_strengths

            def observe_real_reader(service, *args, **kwargs):
                self.assertIs(service.driver, driver)
                value = original_reader(service, *args, **kwargs)
                strength_calls.append({"args": deepcopy(args), "kwargs": deepcopy(kwargs), "result": deepcopy(value)})
                return value

            original_execute = driver._execute_primitive_step

            def execute_with_original_army_nonce(step, **kwargs):
                if step == _ARMY_STEP:
                    kwargs["protocol_request_id"] = packet["request_id"]
                return original_execute(step, **kwargs)

            with (
                patch.object(driver, "take_snapshot", side_effect=endpoint.snapshot),
                patch.object(driver, "take_internal_semantic_snapshot", side_effect=endpoint.snapshot),
                patch.object(driver, "capabilities", return_value=deepcopy(capabilities)),
                patch.object(driver, "_execute_primitive_step", side_effect=execute_with_original_army_nonce),
                patch("xar_autoplayer.bridge.service.choose_one_life_turn", side_effect=lambda *args, **kwargs: deepcopy(baseline)),
                patch.object(GameplayBridgeService, "_strategy_state_dir", return_value=None),
                patch.object(GameplayBridgeService, "_prepare_succession_transition_v1", side_effect=lambda snapshot, steps, **kwargs: snapshot),
                patch.object(GameplayBridgeService, "query_army_strengths", new=observe_real_reader),
                patch("xar_autoplayer.bridge.service.normalize_army_strengths", wraps=normalize_army_strengths) as service_normalizer,
                patch("xar_autoplayer.bridge.native_driver.normalize_army_strengths", wraps=normalize_army_strengths) as driver_normalizer,
            ):
                service = GameplayBridgeService(driver)
                selected = service.plan_turn()
                self.assertEqual(selected["plan"]["selected_step"], _HIRE_STEP)
                self.assertEqual(selected["plan"]["holy_order_hire_proposal"]["holy_order_id"], 0)
                self.assertEqual(selected["plan"]["holy_order_hire_proposal"]["military_need"]["additional_soldiers_required"], 50)
                self.assertEqual(selected["plan"]["deferred_siege_plan"], baseline)
                outcome = service.auto_turn()
                self.assertEqual(outcome["status"], "executed")
                self.assertEqual(outcome["selected_step"], _HIRE_STEP)
                result = outcome["result"]
                self.assertEqual({key: result[key] for key in endpoint.native_hire_body}, endpoint.native_hire_body)
                self.assertIs(result["holy_order_hire"]["after_state_observed"], False)
                self.assertIs(result["holy_order_hire"]["verification_pending"], True)
                material = result["holy_order_reinforcement_postcondition"]
                self.assertNotIn("post_query_error", material)
                self.assertEqual(material["status"], "employer_and_usable_army_observed")
                self.assertIs(material["employer_observed"], True)
                self.assertEqual(material["actual_employer_id"], 29829)
                self.assertIs(material["usable_army_observed"], True)
                self.assertEqual(len(material["troop_association"]["rows"]), 2)
                self.assertEqual(material["material_armies"], [{"army_id": 16777217,
                    "native_carmy_id": 33554433, "current_soldiers": 100, "owner_character_id": 4444,
                    "controllable": True, "current_province_id": 460}])
                self.assertEqual(material["quote_raw"], [0, 0, 200000, 0, 0, 0, 0, 0, 0, 0])
                self.assertEqual(material["observed_stock_delta_raw"], {"gold": 0, "prestige": 0, "piety": 200000})
                self.assertIs(material["unchanged_date_quote_delta_match"], True)
                self.assertEqual(material["actor_expenses"]["military_expenses"]["current"]["gold_raw"], 0)
                self.assertEqual(material["actor_expenses"]["military_expenses"]["all_raised"]["gold_raw"], 100000)
                self.assertEqual(material["actor_expenses"]["player_monthly_net_income"], {"raw": 250000, "scale": 100000})
                self.assertIsNone(material["expense_query_error"])
                self.assertEqual(material["after_source_frame"]["revision"], 42)
                self.assertEqual(material["after_source_frame"]["native_revision"], frame["native_revision"])
                self.assertEqual(material["after_source_frame"]["date_raw"], frame["date_raw"])
                self.assertEqual(material["next_formal"], {"selected_step": "preview-move-army-16777217-to-2592",
                    "expected_revision": 42, "army_id": 16777217, "target_province_id": 2592,
                    "source": "observed_order_army_and_original_siege_target"})
                self.assertIs(material["full_hire_loop_complete"], False)
                self.assertEqual(len(strength_calls), 1)
                self.assertEqual(strength_calls[0]["kwargs"], {"army_ids": [16777217], "expected_revision": 42})
                self.assertEqual(service_normalizer.call_count, 1)
                self.assertEqual(driver_normalizer.call_count, 1)
                self.assertEqual(service_normalizer.call_args.kwargs["expected_scope"], scope)
                self.assertEqual(driver_normalizer.call_args.kwargs["expected_scope"], scope)
                actual_strengths = strength_calls[0]["result"]
                self.assertEqual(actual_strengths["queried_revision"], 42)
                self.assertEqual(actual_strengths["queried_native_revision"], frame["native_revision"])
                self.assertEqual(actual_strengths["source"]["date_raw"], frame["date_raw"])
                self.assertEqual(actual_strengths["source"]["game_version"], CK3_12004.game_version)
                self.assertEqual(actual_strengths["source"]["executable_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(len(actual_strengths["army_strengths"]), 1)
                for key, value in expected_rows[0].items():
                    self.assertEqual(actual_strengths["army_strengths"][0][key], value, key)
                self.assertEqual(driver._army_strength_query["army_strengths"], expected_rows)
                self.assertEqual(driver._army_strength_query["query_sequence"], original["query_sequence"])
                second = service.plan_turn()
                self.assertIsNone(second["plan"]["selected_step"])
                self.assertEqual(second["plan"]["holy_order_reinforcement_observation"]["candidate_rows"][0]["reason"],
                                 "already_employed_by_player")
                self.assertEqual(len(strength_calls), 1)
                self.assertEqual([request["step"] for request in endpoint.requests],
                                 [_HOLY_STEP, _HOLY_STEP, _HIRE_STEP, _HOLY_STEP, _ARMY_STEP, _CASH_STEP, _HOLY_STEP])
                whole_responses = [response["packet"] for response in endpoint.responses
                                   if response["source"] == "qualified_native_whole_army"]
                self.assertEqual(whole_responses, [packet])
                self.assertEqual(fixture_path.read_bytes(), fixture_bytes)
                self.assertEqual(context_path.read_bytes(), context_bytes)
                report.update(status="GREEN", actual_native_driver=True,
                    driver_convenience_method_present=False, actual_service_strength_reader_calls=1,
                    actual_service_normalizer_calls=service_normalizer.call_count,
                    actual_driver_normalizer_calls=driver_normalizer.call_count,
                    original_whole_army_packet_preserved=True, original_native_frame_preserved=True,
                    hire_requests=1, army_requests=1, material_employer_and_usable_army_observed=True)
                (output_dir / "COMPOUND-CONSUMPTION.json").write_text(json.dumps({
                    "selected_plan": selected, "outcome": outcome, "next_turn_plan": second,
                    "actual_service_strength_read": strength_calls[0],
                    "transport_requests": endpoint.requests, "transport_responses": endpoint.responses,
                    "native_context": native_context}, indent=2) + "\n", encoding="utf-8")
        except BaseException as error:
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            if driver is not None:
                driver.close()
            (output_dir / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--native-context", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    _CONFIG.update(vars(args))
    sys.path.insert(0, str(args.source_root / "tools"))
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    suite = unittest.TestSuite([HolyOrderNativeReadbackV1Tests(
        "test_actual_native_driver_ordinary_hire_and_service_strength_fallback")])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
