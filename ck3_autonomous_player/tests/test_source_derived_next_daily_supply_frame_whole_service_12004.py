"""SOURCE_PREPARED/NOTRUN: one new full native Army wire to actual driver/Service."""
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

METHOD = "test_new_native_row_next_date_pair_reaches_actual_service"
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


class SyntheticNextFrameEndpoint:
    """Only transport correlation is supplied; original native body is immutable."""
    pipe_name = r"\\.\pipe\synthetic-next-daily-supply-frame-not-live"

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
            raise AssertionError("sole scene supplies only its native Army query")
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered_frames.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self):
        pass


class SourceDerivedNextDailySupplyFrameWholeService12004Tests(unittest.TestCase):
    def test_new_native_row_next_date_pair_reaches_actual_service(self):
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        endpoint = None
        driver = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()
        receipt = {
            "schema": "xar.native-next-supply-frame12004.whole-service.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "original_scene_count": 1,
            "transport_request_hard_bound": 1, "live": False,
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "native_result": None, "actual_driver_result": None,
            "actual_service_result": None, "actual_exception": None,
            "actual_registered_result": None,
            "registered_route": "ck3_query_army_strengths",
            "call_trace": [], "old_GREEN_replays": 0,
            "synthetic_boundary": "Native fixture owned current memory/callbacks; hello/current paused frame/scope and outer nonce transport only. Next pair originates in the same actual native row, never in this consumer.",
            "actual_future_date_stage_observed": False,
            "actual_future_callback_observed": False,
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
            # Root's future explicit sole run imports production modules here.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.war_contract import (
                QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP,
            )
            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            receipt["source_root"] = source.as_posix()
            receipt["native_wire_path"] = Path(CONFIG.wire).as_posix()
            for key, cls in (("driver_module", NativeHeadlessGameplayDriver),
                             ("service_module", GameplayBridgeService)):
                path = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(path.is_relative_to((source / "src").resolve()))
                receipt[key] = path.as_posix()
            original_bytes = Path(CONFIG.wire).read_bytes()
            (output / "authority-native-whole.json").write_bytes(original_bytes)
            whole = json.loads(original_bytes)
            context_path = (Path(CONFIG.context) if CONFIG.context else
                            Path(CONFIG.wire).with_name(Path(CONFIG.wire).stem + "-native-context.json"))
            context_bytes = context_path.read_bytes()
            (output / "authority-native-context.json").write_bytes(context_bytes)
            context = json.loads(context_bytes)
            self.assertEqual(context["schema"],
                             "xar.source-derived-next-daily-supply-frame-native-context.v1")
            transport = context["synthetic_context"]
            receipt["native_context_path"] = context_path.as_posix()
            receipt["native_context"] = deepcopy(context)
            authority = deepcopy(whole)
            self.assertEqual(whole["type"], "command_result")
            self.assertEqual(whole["protocol_version"], 1)
            self.assertIs(whole["ok"], True)
            native = whole["result"]
            receipt["native_result"] = deepcopy(native)
            self.assertEqual(native["step"], QUERY_ARMY_STRENGTHS_STEP)
            self.assertIs(native["accepted"], True)
            self.assertIs(type(native["query_sequence"]), int)
            self.assertGreater(native["query_sequence"], 0)
            self.assertLessEqual(native["query_sequence"], 2**64 - 1)
            self.assertEqual(set(native) - {"backend_id"},
                             {"step", "accepted", "status", "query_sequence", "army_strengths"})
            rows = native["army_strengths"]
            self.assertEqual(len(rows), 1, "one new complete whole scene, one native subject")
            row = rows[0]
            self.assertEqual(row["scope_role"], "player")
            self.assertEqual(row["war_ids"], [])
            leaf = row["source_derived_next_daily_supply_frame_inputs_v1"]
            schedule = row["future_daily_supply_schedule_inputs_v1"]
            _write(output / "authority-native-date-leaf.json", leaf)
            _write(output / "authority-native-schedule-leaf.json", schedule)
            self.assertEqual(len(leaf), 19)
            self.assertEqual(leaf["source"], "native_source_derived_next_daily_supply_frame_inputs_12004")
            self.assertEqual(leaf["stage"], "source_derived_conditional_next_date_pair")
            self.assertEqual(leaf["status"], "available")
            self.assertIs(leaf["ready"], True)
            self.assertIsNone(leaf["unavailable_reason"])
            self.assertEqual(leaf["current_date_raw_i32"], 53288448)
            self.assertEqual(leaf["current_native_day_index_raw_i32"], 12)
            self.assertEqual(leaf["source_derived_next_date_raw_i32"], 53288472)
            self.assertEqual(leaf["source_derived_next_native_day_index_raw_i32"], 395353)
            self.assertEqual(leaf["subject_army_id_u32"], row["army_id"] & 0xFFFFFFFF)
            self.assertEqual(leaf["subject_carmy_id_u32"], row["native_carmy_id"] & 0xFFFFFFFF)
            self.assertEqual(schedule["status"], "partial")
            self.assertIs(schedule["ready"], False)
            self.assertEqual(len(schedule["phases"]), 30)
            phase_index = leaf["source_derived_next_native_day_index_raw_i32"] & 0xFFFFFFFF
            phase_index %= 30
            self.assertEqual(phase_index, 13)
            self.assertEqual(schedule["selected_phase_index_i32"], 12)
            self.assertEqual(schedule["phases"][12]["matching_positions"], [])
            self.assertEqual(schedule["phases"][12]["subject_occurrence_count_i32"], 0)
            phase = schedule["phases"][phase_index]
            self.assertIs(phase["ready"], True)
            self.assertEqual(phase["matching_positions"], [1, 3])
            self.assertEqual(phase["subject_occurrence_count_i32"], 2)
            self.assertIs(schedule["phases"][4]["ready"], False)
            self.assertEqual(transport["date_raw"], leaf["current_date_raw_i32"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            self.assertEqual(transport["scope_role"], "player")
            self.assertEqual(transport["war_ids"], [])
            self.assertIs(transport["paused"], True)
            self.assertIs(transport["map_ready"], True)
            for key in (
                "actual_future_date_stage_observed", "actual_future_callback_observed",
                "future_bucket_mutations_reconstructed", "future_stock_or_strength_ready",
                "full_daily_supply_transition_ready", "full_monthly_ready",
            ):
                self.assertIs(leaf[key], False)
            endpoint = SyntheticNextFrameEndpoint(whole)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                episode_projection="native_campaign")
            self.assertIs(type(driver), NativeHeadlessGameplayDriver)
            server = create_server(driver)
            self.assertIn("ck3_query_army_strengths", server._tool_manager._tools)
            hello = {
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": transport["bridge_host_pid"], "session_generation": 0,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
            }
            paused = {
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": transport["snapshot_id"], "revision": transport["native_revision"],
                "state": {
                    "phase": "map_hud", "date": "synthetic-current-not-live",
                    "date_raw": transport["date_raw"], "speed": 1,
                    "paused": transport["paused"], "map_ready": transport["map_ready"], "history": [],
                    "active_event": None, "pending_character_interaction": None,
                    "played_character": {"character_id": transport["actor_character_id"], "alive": True},
                    "player_armies": [{"army_id": row["army_id"], "controllable": True,
                                       "owner_character_id": transport["actor_character_id"],
                                       "current_province_id": transport["current_province_id"]}],
                    "active_wars": [],
                },
            }
            _write(output / "synthetic-hello.json", hello)
            _write(output / "synthetic-current-frame.json", paused)
            endpoint.publish(hello)
            endpoint.publish(paused)
            before = driver.take_snapshot()
            receipt["before_current_synthetic_frame"] = deepcopy(before)
            self.assertEqual(before["date_raw"], leaf["current_date_raw_i32"])
            self.assertEqual(before["native_revision"], transport["native_revision"])
            receipt["heartbeat_published"] = False
            interesting = {
                ("service.py", "query_army_strengths"), ("service.py", "execute_step"),
                ("mcp_server.py", "ck3_query_army_strengths"),
                ("native_driver.py", "execute_step"),
                ("native_driver.py", "_execute_army_strength_query"),
                ("native_driver.py", "_execute_primitive_step"),
                ("war_contract.py", "normalize_army_strengths"),
                ("army_future_daily_supply_schedule_contract.py", "normalize_future_daily_supply_schedule_inputs_v1"),
                ("army_source_derived_next_daily_supply_frame_contract.py", "normalize_source_derived_next_daily_supply_frame_inputs_v1"),
                ("army_source_derived_next_daily_supply_frame_projection.py", "project_native_next_daily_supply_schedule_v1"),
                ("army_future_daily_supply_schedule_projection.py", "project_future_daily_supply_schedule_v1"),
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
                "army_ids": [row["army_id"]], "expected_revision": before["revision"],
            }))
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            receipt["actual_registered_result"] = registered.model_dump(mode="json", by_alias=True)
            self.assertIs(registered.is_error, False)
            observed = registered.structured_content
            self.assertIsInstance(observed, dict)
            self.assertEqual(observed, receipt["actual_service_result"])
            _preserved(self, native, receipt["actual_driver_result"], "actual-native-driver")
            _preserved(self, native, observed, "actual-service")
            self.assertEqual(observed["army_strengths"][0]["source_derived_next_daily_supply_frame_inputs_v1"], leaf)
            self.assertEqual(observed["army_strengths"][0]["future_daily_supply_schedule_inputs_v1"], schedule)
            for key in ("date_raw", "revision", "native_revision", "snapshot_id"):
                self.assertEqual(observed["source"][key], before[key])
            for key in ("revision", "native_revision", "snapshot_id"):
                self.assertEqual(observed["queried_" + key], before[key])
                self.assertEqual(receipt["actual_driver_result"]["queried_" + key], before[key])
            siblings = observed["same_input_conditional_future_daily_supply_schedule_v1"]
            self.assertEqual(len(siblings), 1)
            self.assertEqual(siblings[0]["army_id"], row["army_id"])
            projected = siblings[0]["projection"]
            self.assertIs(projected["ready"], False, "overall current schedule remains partial")
            self.assertEqual(projected["status"], "partial")
            self.assertEqual(len(projected["prospective_frames"]), 1)
            selected = projected["prospective_frames"][0]
            self.assertEqual(selected["date_raw_i32"], leaf["source_derived_next_date_raw_i32"])
            self.assertEqual(selected["native_day_index_raw_i32"], leaf["source_derived_next_native_day_index_raw_i32"])
            self.assertEqual(selected["selected_phase_index_i32"], 13)
            self.assertIs(selected["conditional_bucket_occurrences_ready"], True)
            self.assertEqual(selected["matching_positions"], phase["matching_positions"])
            self.assertEqual(selected["subject_occurrence_count_i32"], phase["subject_occurrence_count_i32"])
            self.assertIsNone(selected["unavailable_reason"])
            self.assertIn(4, projected["unavailable_phases"])
            self.assertEqual(projected["condition"],
                             "source_derived_next_date_and_day_with_observed_buckets_unchanged")
            self.assertIs(projected["calendar_derived"], True)
            self.assertIs(projected["actual_future_date_stage_observed"], False)
            self.assertIs(projected["full_future_cdate64_reconstructed"], False)
            self.assertEqual(projected["source_next_pair"], leaf)
            self.assertIs(projected["source_next_pair"]["ready"], True,
                          "unrelated partial phase does not discard native pair readiness")
            self.assertEqual(selected["origin"], "source_derived_conditional_next_date_pair")
            self.assertIs(selected["actual_native_frame_observed"], False)
            for key in (
                "actual_future_callback_observed", "future_bucket_mutations_reconstructed",
                "future_supply_eligibility_ready", "future_stock_or_strength_ready",
                "full_daily_supply_transition_ready", "full_monthly_ready",
            ):
                self.assertIs(projected[key], False)
            self.assertIs(selected["actual_callback_observed"], False)
            _write(output / "actual-projected-next-frame.json", projected)
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
            self.assertTrue(interesting <= executed, "actual complete production consumer path must run")
            self.assertEqual(sum(item["function"] == "query_army_strengths" and
                                 Path(item["source"]).name == "service.py"
                                 for item in receipt["call_trace"]), 1)
            receipt["status"] = "GREEN"
            receipt["transport_request_count"] = 1
            receipt["registered_tool_calls"] = 1
            receipt["actual_service_calls"] = 1
        except Exception as error:
            receipt["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
            receipt["traceback"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
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
            _write(output / "actual-driver-result.json", receipt["actual_driver_result"])
            _write(output / "actual-service-result.json", receipt["actual_service_result"])
            _write(output / "actual-registered-result.json", receipt["actual_registered_result"])
            _write(output / "call-trace.json", receipt["call_trace"])
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
        SourceDerivedNextDailySupplyFrameWholeService12004Tests(METHOD)]))
    sys.exit(0 if result.wasSuccessful() else 1)
