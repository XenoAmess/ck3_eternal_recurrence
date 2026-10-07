"""SOURCE_PREPARED/NOTRUN: one fresh whole Army write join via actual Service."""
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

METHOD = "test_next_updater_write_join_reaches_same_army_service"
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


class SyntheticWriteJoinTransport:
    """Transport-only outer correlation over an unchanged native whole body."""
    pipe_name = r"\\.\pipe\synthetic-next-updater-writes-not-live"

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


class NextUpdaterWriteWholeService12004Tests(unittest.TestCase):
    def test_next_updater_write_join_reaches_same_army_service(self):
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        endpoint = None
        driver = None
        prior_profile = sys.getprofile()
        prior_thread_profile = threading.getprofile()
        receipt = {
            "schema": "xar.next-updater-writes12004.whole-service.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "new_native_scene_count": 1,
            "transport_request_hard_bound": 1, "live": False,
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "registered_route": "ck3_query_army_strengths",
            "native_result": None, "actual_driver_result": None,
            "actual_service_result": None, "actual_registered_result": None,
            "actual_exception": None, "call_trace": [], "old_GREEN_replays": 0,
            "synthetic_boundary": "Native producer owns current memory/callbacks and source calendar input. Only hello/current paused frame/scope and outer request correlation are synthetic transport; future whole CDate remains original native authority.",
            "actual_future_callback_observed": False,
            "actual_future_writes_observed": False,
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
            self.assertEqual(context["schema"], "xar.source-derived-next-updater-writes-native-context.v1")
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
            clock = row["army_update_clock_v1"]
            caller = row["monthly_caller_effect_inputs_v1"]
            gates = row["monthly_loss_budget_inputs_v1"]
            self.assertEqual(len(future), 23)
            self.assertIs(future["source_derived_full_cdate64_ready"], True)
            self.assertIs(type(future["source_derived_next_date_storage_raw64"]), int)
            self.assertEqual(future["current_date_raw_i32"], 53288448)
            self.assertEqual(future["source_derived_next_date_raw_i32"], 53288472)
            self.assertEqual(clock["current_date_raw"], 53288448)
            self.assertEqual(clock["grace_anchor_date_raw"], 53288400)
            self.assertEqual(clock["loaded_grace_days"], 2)
            self.assertEqual(caller["army_byte_22_raw"], 0)
            self.assertEqual(clock["last_supply_update_date_storage_raw64"], 21528124856)
            self.assertEqual(clock["grace_anchor_date_storage_raw64"], 38707994064)
            self.assertEqual(future["source_derived_next_date_storage_raw64"], 304845178016701976)
            self.assertEqual(caller["current_date_storage_raw64"], future["current_date_storage_raw64"])
            self.assertNotEqual(clock["last_supply_update_date_storage_raw64"], caller["current_date_storage_raw64"])
            self.assertEqual(gates["unit_native_170_raw"], 1)
            self.assertIs(gates["native_unit_in_combat"], False)
            self.assertIs(gates["native_unit_gathering"], False)
            self.assertEqual(gates["army_gathering_count_raw"], 0)
            self.assertEqual(transport["date_raw"], future["current_date_raw_i32"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            endpoint = SyntheticWriteJoinTransport(whole)
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
                ("army_next_updater_write_projection.py", "project_source_derived_next_updater_writes_v1"),
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
            self.assertEqual(observed["army_strengths"][0]["army_update_clock_v1"], clock)
            self.assertEqual(observed["army_strengths"][0]["monthly_caller_effect_inputs_v1"], caller)
            self.assertEqual(observed["army_strengths"][0]["monthly_loss_budget_inputs_v1"], gates)
            self.assertEqual(observed["army_strengths"][0]["source_derived_next_daily_supply_frame_inputs_v1"], future)
            joined = observed["source_derived_next_updater_writes_v1"]
            self.assertEqual(len(joined), 1)
            self.assertEqual(joined[0]["army_id"], row["army_id"])
            projection = joined[0]["projection"]
            self.assertEqual(projection["source"], "same_input_conditional_source_derived_next_updater_writes")
            self.assertEqual(projection["status"], "available")
            self.assertIs(projection["ready"], True)
            self.assertEqual(projection["missing_inputs"], [])
            self.assertEqual(projection["condition"], "one source updater invocation for this CURRENT captured receiver at source-derived next passedDate, all non-date gate values unchanged after earlier Unit stages")
            self.assertEqual(projection["source_next_date"], future)
            self.assertEqual(projection["observed_current_army_byte_22_raw"], 0)
            self.assertEqual(projection["observed_current_last_supply_update_date_storage_raw64"], clock["last_supply_update_date_storage_raw64"])
            self.assertIs(projection["observed_current_update_date_comparison_ready"], True)
            self.assertIs(projection["observed_current_update_date_matches_current_clock"], False)
            self.assertIs(projection["observed_current_clock_matches_source_seed"], True)
            self.assertEqual(projection["observed_current_grace_elapsed_days"], 2)
            self.assertIs(projection["next_admission"]["ready"], True)
            self.assertIs(projection["next_admission"]["admitted"], True)
            grace = projection["next_admission"]["witnesses"][-1]
            self.assertEqual(grace["input"], "native_grace_strict_greater")
            self.assertEqual(grace["elapsed_days"], 3)
            self.assertEqual(grace["loaded_grace_days"], 2)
            writes = projection["conditional_writes"]
            self.assertEqual(len(writes), 2)
            self.assertEqual([(item["order"], item["member"]) for item in writes], [(0, "CArmy+0x22"), (1, "CArmy+0x188")])
            self.assertIs(writes[0]["write_ready"], True)
            self.assertEqual(writes[0]["conditional_value"], 1)
            self.assertEqual(writes[0]["observed_value"], 0)
            self.assertIs(writes[1]["write_ready"], True)
            self.assertIs(writes[1]["would_write"], True)
            self.assertIs(writes[1]["after_value_ready"], True)
            self.assertEqual(writes[1]["conditional_value"], future["source_derived_next_date_storage_raw64"])
            self.assertEqual(writes[1]["observed_value"], clock["last_supply_update_date_storage_raw64"])
            self.assertEqual(writes[1]["value_origin"], "source_derived_next_full_cdate64")
            anchor = projection["conditional_grace_anchor_190"]
            self.assertIs(anchor["would_write"], False)
            self.assertEqual(anchor["observed_value"], clock["grace_anchor_date_storage_raw64"])
            self.assertEqual(anchor["conditional_value"], anchor["observed_value"])
            self.assertEqual(anchor["conditional_low32"], clock["grace_anchor_date_raw"])
            for write in writes:
                self.assertIs(write["actual_write_observed"], False)
            for key in ("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                        "actual_future_callback_observed", "actual_future_writes_observed",
                        "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready"):
                self.assertIs(projection[key], False)
            current_risk = observed["current_callback_supply_risk_v1"][0]["projection"]
            self.assertIs(current_risk["admission_ready"], True)
            self.assertIs(current_risk["conditional_callback_admitted"], False)
            self.assertEqual(current_risk["admission_rejection"], "native_grace_strict_greater")
            self.assertEqual(observed["army_strengths"][0]["monthly_caller_effect_inputs_v1"]["army_byte_22_raw"], 0)
            _write(output / "actual-next-updater-write-projection.json", projection)
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
        NextUpdaterWriteWholeService12004Tests(METHOD)]))
    sys.exit(0 if result.wasSuccessful() else 1)
