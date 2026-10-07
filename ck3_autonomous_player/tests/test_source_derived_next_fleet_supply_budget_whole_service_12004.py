"""SOURCE_PREPARED/NOTRUN: one fresh held-stock Fleet budget whole consumer."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import threading
import time
import traceback
import unittest

METHOD = "test_source_next_global_date_budget_reaches_same_army_service"
CONFIG: argparse.Namespace | None = None


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _preserved(test: unittest.TestCase, original: object, observed: object, path: str) -> None:
    test.assertIs(type(observed), type(original), path)
    if isinstance(original, dict):
        test.assertTrue(set(original) <= set(observed), path)
        for key, value in original.items():
            _preserved(test, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        test.assertEqual(len(original), len(observed), path)
        for index, value in enumerate(original):
            _preserved(test, value, observed[index], f"{path}[{index}]")
    else:
        test.assertEqual(observed, original, path)


class SyntheticFleetBudgetTransport:
    """Transport-only outer correlation over an unchanged native whole body."""
    pipe_name = r"\\.\pipe\synthetic-next-fleet-supply-budget-not-live"

    def __init__(self, whole):
        self.whole = deepcopy(whole)
        self.on_frame = None
        self.requests = []
        self.delivered_frames = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, value):
        if not callable(self.on_frame):
            raise RuntimeError("actual driver did not register its frame receiver")
        self.on_frame(deepcopy(value))

    def send(self, request):
        self.requests.append(deepcopy(request))
        if request.get("type") != "execute_step":
            return
        if request.get("step") != self.whole["result"]["step"]:
            raise AssertionError("one fresh whole supplies only its Army query")
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered_frames.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self):
        pass


class SourceDerivedNextFleetSupplyBudgetWholeService12004Tests(unittest.TestCase):
    def test_source_next_global_date_budget_reaches_same_army_service(self):
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        endpoint = None
        driver = None
        prior_profile = sys.getprofile()
        prior_thread_profile = threading.getprofile()
        receipt = {
            "schema": "xar.source-next-fleet-supply-budget12004.whole-service.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "new_native_scene_count": 1,
            "transport_request_hard_bound": 1, "live": False,
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "registered_route": "ck3_query_army_strengths",
            "native_result": None, "actual_driver_result": None,
            "actual_service_result": None, "actual_registered_result": None,
            "actual_exception": None, "call_trace": [], "old_GREEN_replays": 0,
            "synthetic_boundary": "Native producer owns current memory/callbacks and source clock input. Only hello/current paused frame/scope and outer request correlation are synthetic transport. Global next clock, current suppression and held stock/count remain original native authority.",
            "actual_future_callback_observed": False,
            "actual_future_supply_budget_observed": False,
            "future_stock_or_strength_ready": False,
            "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0)
            supplied = Path(CONFIG.source_root)
            source = supplied / "ck3_autonomous_player" if (supplied / "ck3_autonomous_player").is_dir() else supplied
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir())
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # Only Root's future explicit sole run imports production code.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP
            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            receipt["source_root"] = source.as_posix()
            for key, cls in (("driver_module", NativeHeadlessGameplayDriver), ("service_module", GameplayBridgeService)):
                module = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(module.is_relative_to((source / "src").resolve()))
                receipt[key] = module.as_posix()
            wire_path = Path(CONFIG.wire)
            original_bytes = wire_path.read_bytes()
            (output / "authority-native-whole.json").write_bytes(original_bytes)
            whole = json.loads(original_bytes)
            authority = deepcopy(whole)
            context_path = Path(CONFIG.context) if CONFIG.context else wire_path.with_name(wire_path.stem + "-native-context.json")
            context_bytes = context_path.read_bytes()
            (output / "authority-native-context.json").write_bytes(context_bytes)
            context = json.loads(context_bytes)
            self.assertEqual(context["schema"], "xar.source-derived-next-fleet-supply-budget-native-context.v1")
            transport = context["synthetic_context"]
            receipt.update(native_wire_path=wire_path.as_posix(), native_context_path=context_path.as_posix(), native_context=context)
            self.assertEqual(whole["type"], "command_result")
            self.assertEqual(whole["protocol_version"], 1)
            self.assertIs(whole["ok"], True)
            native = whole["result"]
            receipt["native_result"] = deepcopy(native)
            self.assertEqual(set(native) - {"backend_id"}, {"step", "accepted", "status", "query_sequence", "army_strengths"})
            self.assertEqual(native["step"], QUERY_ARMY_STRENGTHS_STEP)
            self.assertIs(native["accepted"], True)
            self.assertIs(type(native["query_sequence"]), int)
            self.assertGreater(native["query_sequence"], 0)
            self.assertEqual(len(native["army_strengths"]), 1)
            row = native["army_strengths"][0]
            self.assertEqual(row["status"], "available")
            self.assertEqual(row["scope_role"], "player")
            self.assertEqual(row["war_ids"], [])
            future = row["source_derived_next_daily_supply_frame_inputs_v1"]
            fleet = row["current_fleet_supply_tick_inputs_v1"]
            numeric = row["monthly_loss_budget_inputs_v1"]
            losses = row["loss_application_inputs_v1"]
            self.assertIn(len(future), (19, 23))
            if future.get("source_derived_full_cdate64_ready") is True:
                self.assertIs(type(future["source_derived_next_date_storage_raw64"]), int)
                self.assertGreaterEqual(future["source_derived_next_date_storage_raw64"], -(1 << 63))
                self.assertLess(future["source_derived_next_date_storage_raw64"], 1 << 63)
            self.assertEqual(future["current_date_raw_i32"], 53288448)
            self.assertEqual(future["source_derived_next_date_raw_i32"], 53288472)
            self.assertEqual(row["current_supply_raw"], 123450000)
            self.assertIs(fleet["native_fleet_branch_applicable"], True)
            self.assertEqual(fleet["current_native_date_low32"], 53288448)
            self.assertEqual(fleet["fleet_day_raw"], 53288472)
            self.assertEqual(fleet["loaded_fleet_day_sentinel_raw"], -1)
            self.assertIs(numeric["native_fleet_supply_loss_suppressed"], True)
            self.assertEqual(losses["current_supply_loss_budget"], 0)
            self.assertEqual(numeric["loaded_supply_state_levels"], [2000, 1000, 0])
            self.assertEqual(numeric["loaded_supply_state_fractions_raw"], [0, 12500, 25000])
            self.assertIs(numeric["commander_valid"], False)
            self.assertEqual(losses["supply_eligible_soldiers"], 100)
            self.assertEqual(transport["date_raw"], future["current_date_raw_i32"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            endpoint = SyntheticFleetBudgetTransport(whole)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                   command_timeout_seconds=1.0, episode_projection="native_campaign")
            self.assertIs(type(driver), NativeHeadlessGameplayDriver)
            server = create_server(driver)
            self.assertIn("ck3_query_army_strengths", server._tool_manager._tools)
            hello = {
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": transport["bridge_host_pid"], "session_generation": 0,
                "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version, "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
            }
            current_frame = {
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": transport["snapshot_id"], "revision": transport["native_revision"],
                "state": {"phase": "map_hud", "date": "synthetic-current-not-live",
                          "date_raw": transport["date_raw"], "speed": 1,
                          "paused": transport["paused"], "map_ready": transport["map_ready"],
                          "history": [], "active_event": None, "pending_character_interaction": None,
                          "played_character": {"character_id": transport["actor_character_id"], "alive": True},
                          "player_armies": [{"army_id": row["army_id"], "controllable": True,
                                             "owner_character_id": transport["actor_character_id"],
                                             "current_province_id": transport["current_province_id"]}],
                          "active_wars": []},
            }
            _write(output / "synthetic-hello.json", hello)
            _write(output / "synthetic-current-frame.json", current_frame)
            endpoint.publish(hello)
            endpoint.publish(current_frame)
            before = driver.take_snapshot()
            receipt["before_current_synthetic_frame"] = deepcopy(before)
            receipt["heartbeat_published"] = False
            interesting = {
                ("mcp_server.py", "ck3_query_army_strengths"),
                ("service.py", "query_army_strengths"), ("service.py", "execute_step"),
                ("native_driver.py", "execute_step"),
                ("native_driver.py", "_execute_army_strength_query"),
                ("native_driver.py", "_execute_primitive_step"),
                ("war_contract.py", "normalize_army_strengths"),
                ("army_source_derived_next_daily_supply_frame_contract.py", "normalize_source_derived_next_daily_supply_frame_inputs_v1"),
                ("army_current_fleet_supply_tick_inputs_contract.py", "normalize_current_fleet_supply_tick_inputs_v1"),
                ("army_next_fleet_supply_budget_projection.py", "project_source_derived_next_fleet_supply_budget_v1"),
                ("army_monthly_loss_budget_projection.py", "_derive_supply_component"),
                ("army_monthly_loss_budget_projection.py", "_whole_budget"),
            }

            def observe(frame, event, value):
                key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
                if key not in interesting:
                    return
                if event == "call":
                    receipt["call_trace"].append({"source": frame.f_code.co_filename, "function": key[1]})
                    if key == ("service.py", "query_army_strengths"):
                        self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                        self.assertIs(frame.f_locals["self"].driver, driver)
                elif event == "return" and key == ("native_driver.py", "execute_step"):
                    receipt["actual_driver_result"] = deepcopy(value)
                elif event == "return" and key == ("service.py", "query_army_strengths"):
                    receipt["actual_service_result"] = deepcopy(value)

            sys.setprofile(observe)
            threading.setprofile(observe)
            registered = asyncio.run(server.call_tool("ck3_query_army_strengths", {
                "army_ids": [row["army_id"]], "expected_revision": before["revision"]}))
            sys.setprofile(prior_profile)
            threading.setprofile(prior_thread_profile)
            receipt["actual_registered_result"] = registered.model_dump(mode="json", by_alias=True)
            self.assertIs(registered.is_error, False)
            observed = registered.structured_content
            self.assertIsInstance(observed, dict)
            self.assertEqual(observed, receipt["actual_service_result"])
            _preserved(self, native, receipt["actual_driver_result"], "actual-driver-native")
            _preserved(self, native, observed, "actual-Service-native")
            self.assertEqual(observed["army_strengths"][0]["current_fleet_supply_tick_inputs_v1"], fleet)
            self.assertEqual(observed["army_strengths"][0]["monthly_loss_budget_inputs_v1"], numeric)
            self.assertEqual(observed["army_strengths"][0]["loss_application_inputs_v1"], losses)
            self.assertEqual(observed["army_strengths"][0]["source_derived_next_daily_supply_frame_inputs_v1"], future)
            joined = observed["source_derived_next_fleet_supply_budget_v1"]
            self.assertEqual(len(joined), 1)
            self.assertEqual(joined[0]["army_id"], row["army_id"])
            projection = joined[0]["projection"]
            self.assertEqual(projection["source"], "same_input_conditional_source_derived_next_fleet_supply_budget")
            self.assertEqual(projection["status"], "available")
            self.assertIs(projection["ready"], True)
            self.assertEqual(projection["missing_inputs"], [])
            self.assertEqual(projection["condition"], "one direct 24E32C0 getter evaluation with source-derived next GLOBAL GameState low32 date and CURRENT captured stock/Fleet/commander/eligible-current inputs unchanged")
            self.assertEqual(projection["stock_basis"], "captured_current_stock_unchanged")
            self.assertIs(projection["post_updater_stock_used"], False)
            self.assertEqual(projection["held_current_supply_stock_raw"], row["current_supply_raw"])
            self.assertEqual(projection["source_next_global_clock"], future)
            self.assertEqual(projection["source_next_global_date_raw_i32"], future["source_derived_next_date_raw_i32"])
            self.assertIs(projection["observed_current_native_fleet_supply_loss_suppressed"], True)
            self.assertEqual(projection["observed_current_supply_loss_budget_soldiers"], 0)
            self.assertIs(projection["fleet_date_predicate_ready"], True)
            self.assertIs(projection["conditional_native_fleet_supply_loss_suppressed"], False)
            self.assertIs(projection["global_date_operand_used"], True)
            self.assertEqual(projection["fleet_date_comparison"], "signed_int32_strict_greater_than_global_date")
            self.assertEqual(projection["held_stock_state_index"], 1)
            self.assertEqual(projection["supply_base_fraction_raw"], 12500)
            self.assertEqual(projection["supply_effective_fraction_raw"], 12500)
            self.assertIs(projection["conditional_supply_budget_ready"], True)
            self.assertEqual(projection["conditional_supply_budget_soldiers"], 12)
            for key in ("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                        "actual_future_callback_observed", "actual_future_supply_budget_observed",
                        "future_supply_eligibility_ready", "future_stock_or_strength_ready",
                        "full_daily_supply_transition_ready", "full_monthly_ready"):
                self.assertIs(projection[key], False)
            self.assertEqual(observed["army_strengths"][0]["current_supply_raw"], 123450000)
            self.assertIs(observed["army_strengths"][0]["monthly_loss_budget_inputs_v1"]["native_fleet_supply_loss_suppressed"], True)
            self.assertEqual(observed["army_strengths"][0]["loss_application_inputs_v1"]["current_supply_loss_budget"], 0)
            _write(output / "actual-next-fleet-supply-budget-projection.json", projection)
            requests = [request for request in endpoint.requests if request.get("type") == "execute_step"]
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["expected_revision"], before["native_revision"])
            self.assertEqual(len(endpoint.delivered_frames), 1)
            delivered = endpoint.delivered_frames[0]
            self.assertEqual(delivered["request_id"], requests[0]["request_id"])
            for key in authority:
                if key != "request_id":
                    _preserved(self, authority[key], delivered[key], "runtime-whole." + key)
            self.assertEqual(whole, authority)
            executed = {(Path(item["source"]).name, item["function"]) for item in receipt["call_trace"]}
            self.assertTrue(interesting <= executed, "actual registered/driver/strict/Service projection path must run")
            self.assertEqual(sum(item["function"] == "query_army_strengths" and Path(item["source"]).name == "service.py" for item in receipt["call_trace"]), 1)
            receipt.update(status="GREEN", transport_request_count=1, registered_tool_calls=1,
                           actual_service_calls=1, whole_native_body_preserved=True)
        except Exception as error:
            receipt["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
            receipt["traceback"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(prior_profile)
            threading.setprofile(prior_thread_profile)
            if endpoint is not None:
                receipt["transport_requests"] = deepcopy(endpoint.requests)
                receipt["runtime_whole_frames"] = deepcopy(endpoint.delivered_frames)
            if driver is not None:
                try:
                    driver.close()
                except Exception as error:
                    receipt["status"] = "RED"
                    receipt["cleanup_exception"] = {"type": type(error).__name__, "message": str(error)}
            receipt["elapsed_seconds"] = time.perf_counter() - started
            receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            for filename, key in (("actual-driver-result.json", "actual_driver_result"),
                                  ("actual-service-result.json", "actual_service_result"),
                                  ("actual-registered-result.json", "actual_registered_result"),
                                  ("call-trace.json", "call_trace")):
                _write(output / filename, receipt[key])
            _write(output / "single-scene-compound-receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--source-commit")
    parser.add_argument("--wire", required=True)
    parser.add_argument("--context")
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        SourceDerivedNextFleetSupplyBudgetWholeService12004Tests(METHOD)]))
    sys.exit(0 if result.wasSuccessful() else 1)
