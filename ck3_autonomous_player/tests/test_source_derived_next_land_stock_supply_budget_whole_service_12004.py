"""SOURCE_PREPARED/NOTRUN: three complete LAND programs in one whole consumer."""
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

METHOD = "test_source_next_land_stock_budget_reaches_same_army_service"
CONFIG: argparse.Namespace | None = None
CASES = (
    {"name": "01-land-over-limit-loss", "stock": 100000000, "usage": 101,
     "rate": -100000, "changed": 99900000, "post": 99900000,
     "state": 2, "fraction": 25000, "budget": 25, "gain": 0,
     "loss": 100000, "fixed": 0, "floor": 100000, "divisor": 100000,
     "division_path": "fast"},
    {"name": "02-land-under-limit-gain-cap", "stock": 199000000, "usage": 99,
     "rate": 2000000, "changed": 201000000, "post": 200000000,
     "state": 0, "fraction": 0, "budget": 0, "gain": 2000000,
     "loss": 0, "fixed": 0, "floor": 100000, "divisor": None,
     "division_path": "not_negative"},
    {"name": "03-land-zero-divisor-cap", "stock": 100000000, "usage": 101,
     "rate": 4294967295, "changed": 4394967295, "post": 200000000,
     "state": 0, "fraction": 0, "budget": 0, "gain": 0,
     "loss": 100000, "fixed": -100000, "floor": 0, "divisor": 0,
     "division_path": "zero_divisor_positive_u32_max"},
)


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


class SyntheticLandStockBudgetTransport:
    """Outer request correlation only; native whole bodies remain unchanged."""
    pipe_name = r"\\.\pipe\synthetic-next-land-stock-budget-not-live"

    def __init__(self, whole):
        self.whole = deepcopy(whole)
        self.on_frame = None
        self.requests = []
        self.delivered_frames = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        if not callable(self.on_frame):
            raise RuntimeError("actual driver did not register its frame receiver")
        self.on_frame(deepcopy(frame))

    def send(self, request):
        self.requests.append(deepcopy(request))
        if request.get("type") != "execute_step":
            return
        if request.get("step") != self.whole["result"]["step"]:
            raise AssertionError("each fresh whole supplies only its actual Army query")
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered_frames.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self):
        pass


class SourceDerivedNextLandStockSupplyBudgetWholeService12004Tests(unittest.TestCase):
    def test_source_next_land_stock_budget_reaches_same_army_service(self):
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        compound = {
            "schema": "xar.source-next-land-stock-supply-budget12004.whole-service.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "new_native_scene_count": 3,
            "transport_request_hard_bound": 3, "registered_route": "ck3_query_army_strengths",
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService", "scenes": [],
            "old_GREEN_replays": 0, "live": False,
            "actual_future_callback_observed": False, "actual_future_stock_observed": False,
            "actual_future_supply_budget_observed": False,
            "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0)
            supplied = Path(CONFIG.source_root)
            source = supplied / "ck3_autonomous_player" if (supplied / "ck3_autonomous_player").is_dir() else supplied
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir())
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # Production imports happen only in Root's future explicit sole run.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP
            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            compound["source_root"] = source.as_posix()
            for key, cls in (("driver_module", NativeHeadlessGameplayDriver), ("service_module", GameplayBridgeService)):
                module = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(module.is_relative_to((source / "src").resolve()))
                compound[key] = module.as_posix()
            for case in CASES:
                with self.subTest(scene=case["name"]):
                    self._consume_scene(case, output, compound, NativeHeadlessGameplayDriver,
                                        GameplayBridgeService, create_server, CK3_12004,
                                        QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP)
            self.assertEqual(len(compound["scenes"]), 3)
            self.assertTrue(all(scene["status"] == "GREEN" for scene in compound["scenes"]))
            self.assertEqual(sum(scene["transport_request_count"] for scene in compound["scenes"]), 3)
            self.assertEqual(sum(scene["actual_service_calls"] for scene in compound["scenes"]), 3)
            compound.update(status="GREEN", transport_request_count=3, actual_service_calls=3,
                            registered_tool_calls=3, whole_native_bodies_preserved=True)
        except Exception as error:
            compound["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
            compound["traceback"] = traceback.format_exc()
            raise
        finally:
            compound["elapsed_seconds"] = time.perf_counter() - started
            compound["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            _write(output / "three-scene-compound-receipt.json", compound)

    def _consume_scene(self, case, root_output, compound, Driver, Service, create_server,
                       identity, query_capability, query_step):
        output = root_output / case["name"]
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        driver = endpoint = None
        prior_profile, prior_thread_profile = sys.getprofile(), threading.getprofile()
        receipt = {
            "scene": case["name"], "status": "RED", "native_result": None,
            "actual_driver_result": None, "actual_service_result": None,
            "actual_registered_result": None, "actual_exception": None, "call_trace": [],
            "synthetic_boundary": "Original native current memory/callbacks and source-next CDate are fixture authority. Only compatible hello/current paused scope and outer request correlation are synthetic transport. Capacity/Province/owner/usage/commander inputs are held, never observed future outputs.",
            "heartbeat_published": False, "actual_future_callback_observed": False,
            "actual_future_rate_getter_observed": False, "actual_future_capacity_getter_observed": False,
            "actual_future_stock_observed": False, "actual_future_supply_budget_observed": False,
            "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
        }
        try:
            wire_path = Path(CONFIG.wire_dir) / (case["name"] + ".json")
            wire_bytes = wire_path.read_bytes()
            (output / "authority-native-whole.json").write_bytes(wire_bytes)
            whole = json.loads(wire_bytes)
            authority = deepcopy(whole)
            context_path = wire_path.with_name(wire_path.stem + "-native-context.json")
            context_bytes = context_path.read_bytes()
            (output / "authority-native-context.json").write_bytes(context_bytes)
            context = json.loads(context_bytes)
            self.assertEqual(context["schema"], "xar.source-derived-next-land-stock-supply-budget-native-context.v1")
            transport = context["synthetic_context"]
            receipt.update(native_wire_path=wire_path.as_posix(), native_context_path=context_path.as_posix(), native_context=context)
            self.assertEqual(whole["type"], "command_result")
            self.assertEqual(whole["protocol_version"], 1)
            self.assertIs(whole["ok"], True)
            native = whole["result"]
            receipt["native_result"] = deepcopy(native)
            self.assertEqual(set(native) - {"backend_id"}, {"step", "accepted", "status", "query_sequence", "army_strengths"})
            self.assertEqual(native["step"], query_step)
            self.assertIs(native["accepted"], True)
            self.assertIs(type(native["query_sequence"]), int)
            self.assertGreater(native["query_sequence"], 0)
            self.assertEqual(len(native["army_strengths"]), 1)
            row = native["army_strengths"][0]
            self.assertEqual(row["status"], "available")
            self.assertEqual(row["scope_role"], "player")
            self.assertEqual(row["war_ids"], [])
            future = row["source_derived_next_daily_supply_frame_inputs_v1"]
            land = row["current_land_supply_rate_inputs_v1"]
            gain = row["current_land_resupply_v1"]
            province = row["current_province_supply_contributors_v1"]
            fleet = row["current_fleet_supply_tick_inputs_v1"]
            numeric = row["monthly_loss_budget_inputs_v1"]
            losses = row["loss_application_inputs_v1"]
            self.assertEqual(row["current_supply_raw"], case["stock"])
            self.assertEqual(row["current_supply_capacity_raw"], 200000000)
            self.assertEqual(row["current_supply_change_monthly_raw"], case["rate"])
            self.assertEqual(future["current_date_raw_i32"], 53288448)
            self.assertEqual(future["source_derived_next_date_raw_i32"], 53288472)
            self.assertEqual(future["source_derived_next_native_day_index_raw_i32"], 395353)
            self.assertIs(future["source_derived_full_cdate64_ready"], True)
            self.assertIs(type(future["source_derived_next_date_storage_raw64"]), int)
            self.assertGreaterEqual(future["source_derived_next_date_storage_raw64"], -(1 << 63))
            self.assertLess(future["source_derived_next_date_storage_raw64"], 1 << 63)
            self.assertIs(land["current_observation_ready"], True)
            self.assertIs(land["native_land_branch_applicable"], True)
            self.assertEqual(land["province_component_raw"], 0)
            self.assertEqual(land["loaded_excess_slope_raw"], 100000)
            self.assertEqual(land["loaded_min_loss_raw"], 100000)
            self.assertEqual(land["loaded_max_loss_raw"], 500000)
            self.assertEqual(land["commander_modifier_1a9_raw"], case["fixed"])
            self.assertEqual(land["loaded_divisor_floor_raw"], case["floor"])
            self.assertEqual(land["commander_resolved_full_id"], 83886081)
            self.assertIs(gain["current_observation_ready"], True)
            if case["usage"] <= 100:
                self.assertIs(gain["native_resupply_eligible"], True)
            else:
                self.assertIs(type(gain["native_resupply_eligible"]), bool)
            self.assertIs(province["current_usage_ready"], True)
            self.assertEqual(province["native_supply_usage_soldiers"], case["usage"])
            self.assertEqual(province["native_supply_limit_soldiers"], 100)
            self.assertEqual(fleet["status"], "not_fleet")
            self.assertIs(fleet["ready"], True)
            self.assertIs(fleet["native_fleet_branch_applicable"], False)
            self.assertIs(numeric["native_fleet_supply_loss_suppressed"], False)
            self.assertEqual(numeric["loaded_supply_state_levels"], [2000, 1000, 0])
            self.assertEqual(numeric["loaded_supply_state_fractions_raw"], [0, 12500, 25000])
            self.assertIs(numeric["commander_valid"], True)
            self.assertEqual(numeric["commander_supply_modifier_raw"], 0)
            self.assertEqual(losses["current_supply_loss_budget"], 12)
            self.assertEqual(losses["supply_eligible_soldiers"], 100)
            self.assertEqual(transport["date_raw"], future["current_date_raw_i32"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            endpoint = SyntheticLandStockBudgetTransport(whole)
            driver = Driver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                            episode_projection="native_campaign")
            self.assertIs(type(driver), Driver)
            server = create_server(driver)
            self.assertIn("ck3_query_army_strengths", server._tool_manager._tools)
            hello = {"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                     "pid": transport["bridge_host_pid"], "session_generation": 0,
                     "game_version": identity.game_version, "executable_sha256": identity.executable_sha256,
                     "expected_ck3_version": identity.game_version, "expected_ck3_sha256": identity.executable_sha256,
                     "capabilities": ["game.state.snapshot", query_capability]}
            frame = {"type": "state_snapshot", "protocol_version": 1,
                     "snapshot_id": transport["snapshot_id"], "revision": transport["native_revision"],
                     "state": {"phase": "map_hud", "date": "synthetic-current-not-live",
                               "date_raw": transport["date_raw"], "speed": 1, "paused": transport["paused"],
                               "map_ready": transport["map_ready"], "history": [], "active_event": None,
                               "pending_character_interaction": None,
                               "played_character": {"character_id": transport["actor_character_id"], "alive": True},
                               "player_armies": [{"army_id": row["army_id"], "controllable": True,
                                                  "owner_character_id": transport["actor_character_id"],
                                                  "current_province_id": transport["current_province_id"]}],
                               "active_wars": []}}
            _write(output / "synthetic-hello.json", hello)
            _write(output / "synthetic-current-frame.json", frame)
            endpoint.publish(hello)
            endpoint.publish(frame)
            before = driver.take_snapshot()
            receipt["before_current_synthetic_frame"] = deepcopy(before)
            interesting = {
                ("mcp_server.py", "ck3_query_army_strengths"),
                ("service.py", "query_army_strengths"), ("service.py", "execute_step"),
                ("native_driver.py", "execute_step"), ("native_driver.py", "_execute_army_strength_query"),
                ("native_driver.py", "_execute_primitive_step"), ("war_contract.py", "normalize_army_strengths"),
                ("army_next_land_stock_supply_budget_projection.py", "project_source_derived_next_land_stock_supply_budget_v1"),
                ("army_next_updater_write_projection.py", "project_source_derived_next_updater_writes_v1"),
                ("army_current_land_supply_rate_contract.py", "normalize_current_land_supply_rate_inputs_v1"),
                ("army_current_land_resupply_contract.py", "normalize_current_land_resupply_v1"),
                ("army_current_province_supply_contributors_contract.py", "normalize_current_province_supply_contributors_v1"),
                ("army_full_land_supply_rate_projection.py", "project_full_land_supply_rate_v1"),
                ("army_next_fleet_supply_budget_projection.py", "_project_source_next_fleet_supply_budget_at_stock_v1"),
                ("army_monthly_loss_budget_projection.py", "_derive_supply_component"),
            }
            if case["loss"]:
                interesting.add(("army_full_land_supply_rate_projection.py", "_native_fixed_div"))

            def observe(frame, event, value):
                key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
                if key not in interesting:
                    return
                if event == "call":
                    receipt["call_trace"].append({"source": frame.f_code.co_filename, "function": key[1]})
                    if key == ("service.py", "query_army_strengths"):
                        self.assertIs(type(frame.f_locals["self"]), Service)
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
            projection = observed["source_derived_next_land_stock_supply_budget_v1"][0]["projection"]
            _write(output / "actual-next-land-stock-supply-budget-projection.json", projection)
            self.assertEqual(projection["source"], "same_input_conditional_source_derived_next_land_stock_supply_budget")
            self.assertIs(projection["ready"], True)
            self.assertEqual(projection["status"], "available")
            self.assertEqual(projection["missing_inputs"], [])
            self.assertEqual(projection["source_next_date"], future)
            self.assertIs(projection["next_admission"]["admitted"], True)
            self.assertEqual(projection["next_admission"]["witnesses"][-1]["elapsed_days"], 3)
            self.assertIs(projection["ordered_pre_rate_writes_ready"], True)
            self.assertEqual(projection["conditional_pre_rate_writes"][1]["conditional_value"], future["source_derived_next_date_storage_raw64"])
            rate = projection["conditional_rate"]
            self.assertIs(rate["ready"], True)
            self.assertEqual(rate["basis"], "same_query_land_numeric_kernel_at_captured_native_usage")
            self.assertEqual(rate["usage_basis"], "captured_current_native_usage_unchanged")
            self.assertEqual(rate["native_usage_soldiers"], case["usage"])
            self.assertEqual(rate["native_limit_soldiers"], 100)
            self.assertEqual(rate["raw"], case["rate"])
            self.assertIs(rate["conditional_refill_usage_used"], False)
            self.assertIs(rate["captured_target_context_used"], False)
            land_rate = rate["full_land_rate_projection"]
            self.assertEqual(land_rate["excess_loss_raw"], case["loss"])
            self.assertEqual(land_rate["gain_component_raw"], case["gain"])
            self.assertEqual(land_rate["commander_divisor_raw"], case["divisor"])
            self.assertEqual(land_rate["division_path"], case["division_path"])
            post = projection["conditional_post_updater_stock"]
            self.assertIs(post["ready"], True)
            self.assertEqual(post["signed64_add_raw"], case["changed"])
            self.assertEqual(post["raw"], case["post"])
            self.assertEqual(post["clamp_branch"], "min_changed_captured_capacity")
            self.assertEqual(post["capacity_basis"], "captured_current_capacity_unchanged")
            self.assertIs(post["actual_future_capacity_observed"], False)
            budget = projection["conditional_budget_getter"]
            self.assertIs(budget["would_call"], True)
            self.assertIs(budget["suppression"], False)
            self.assertEqual(budget["stock_basis"], "conditional_post_updater_stock")
            self.assertEqual(budget["stock_raw"], case["post"])
            self.assertEqual(budget["state_index"], case["state"])
            self.assertEqual(budget["base_fraction_raw"], case["fraction"])
            self.assertEqual(budget["effective_fraction_raw"], case["fraction"])
            self.assertIs(budget["ready"], True)
            self.assertEqual(budget["soldiers"], case["budget"])
            held = observed["source_derived_next_fleet_supply_budget_v1"][0]["projection"]
            self.assertEqual(held["conditional_supply_budget_soldiers"], 12)
            self.assertEqual(held["held_current_supply_stock_raw"], case["stock"])
            current = observed["current_callback_supply_risk_v1"][0]["projection"]
            self.assertIs(current["conditional_callback_admitted"], False)
            self.assertEqual(current["conditional_post_stock_raw"], case["stock"])
            self.assertEqual(current["conditional_supply_budget_soldiers"], 0)
            for key in ("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                        "actual_future_callback_observed", "actual_future_rate_getter_observed",
                        "actual_future_stock_observed", "actual_future_supply_budget_observed",
                        "actual_physical_loss_observed", "future_stock_or_strength_ready",
                        "full_daily_supply_transition_ready", "full_monthly_ready"):
                self.assertIs(projection[key], False)
            self.assertEqual(observed["army_strengths"][0]["current_supply_raw"], case["stock"])
            self.assertEqual(observed["army_strengths"][0]["current_supply_change_monthly_raw"], case["rate"])
            self.assertEqual(observed["army_strengths"][0]["loss_application_inputs_v1"]["current_supply_loss_budget"], 12)
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
            self.assertTrue(interesting <= executed, "actual registered/driver/strict/Service program path must run")
            self.assertEqual(sum(item["function"] == "query_army_strengths" and Path(item["source"]).name == "service.py" for item in receipt["call_trace"]), 1)
            receipt.update(status="GREEN", whole_native_body_preserved=True)
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
            receipt["transport_request_count"] = sum(request.get("type") == "execute_step" for request in receipt.get("transport_requests", []))
            receipt["actual_service_calls"] = sum(item["function"] == "query_army_strengths" and Path(item["source"]).name == "service.py" for item in receipt["call_trace"])
            receipt["elapsed_seconds"] = time.perf_counter() - started
            receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            for filename, key in (("actual-driver-result.json", "actual_driver_result"),
                                  ("actual-service-result.json", "actual_service_result"),
                                  ("actual-registered-result.json", "actual_registered_result"),
                                  ("call-trace.json", "call_trace")):
                _write(output / filename, receipt[key])
            _write(output / "scene-receipt.json", receipt)
            compound["scenes"].append({"scene": case["name"], "status": receipt["status"],
                                       "transport_request_count": receipt["transport_request_count"],
                                       "actual_service_calls": receipt["actual_service_calls"],
                                       "receipt": (output / "scene-receipt.json").as_posix(),
                                       "actual_exception": receipt["actual_exception"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--source-commit")
    parser.add_argument("--wire-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        SourceDerivedNextLandStockSupplyBudgetWholeService12004Tests(METHOD)]))
    sys.exit(0 if result.wasSuccessful() else 1)
