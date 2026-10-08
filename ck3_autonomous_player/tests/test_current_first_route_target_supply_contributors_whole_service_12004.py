"""SOURCE_PREPARED/NOTRUN: fresh first-route target whole wires, one compound."""
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

METHOD = "test_first_route_target_contributors_reach_same_army_service"
CONFIG: argparse.Namespace | None = None
FAMILY = "current_first_route_target_supply_contributors_v1"
CASES = (
    {"name": "01-target-subject-absent", "status": "available", "ready": True,
     "usage": 0, "roster_count": 0, "matches": [], "included_count": 0,
     "witness": "observed_absent", "reason": None},
    {"name": "02-target-subject-duplicate", "status": "available", "ready": True,
     "usage": 200, "roster_count": 2, "matches": [0, 1], "included_count": 2,
     "witness": "observed_present", "reason": None},
    {"name": "03-target-excluded-and-unresolved", "status": "partial", "ready": False,
     "usage": 0, "roster_count": 2, "matches": [], "included_count": None,
     "witness": "unavailable", "reason": "current_province_contributors_partial"},
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


class SyntheticFirstRouteTargetTransport:
    """Compatible current scope and outer nonce only; no native body changes."""
    pipe_name = r"\\.\pipe\synthetic-first-route-target-not-live"

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
            raise AssertionError("each original whole supplies only its actual Army query")
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered_frames.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self):
        pass


class CurrentFirstRouteTargetSupplyContributorsWholeService12004Tests(unittest.TestCase):
    def test_first_route_target_contributors_reach_same_army_service(self):
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        compound = {
            "schema": "xar.current-first-route-target-contributors12004.whole-service.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "new_native_scene_count": 3,
            "transport_request_hard_bound": 3, "registered_route": "ck3_query_army_strengths",
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService", "scenes": [],
            "old_GREEN_replays": 0, "live": False,
            "only_current_target_inputs": True, "actual_arrival_observed": False,
            "actual_after_arrival_usage_observed": False, "full_arrival_supply_transition_ready": False,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0)
            supplied = Path(CONFIG.source_root)
            source = supplied / "ck3_autonomous_player" if (supplied / "ck3_autonomous_player").is_dir() else supplied
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir())
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # Root's sole future execution imports the adopted production tree.
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
            "synthetic_boundary": "The new compiled whole and context are original fixture authority. Only protocol-compatible current paused hello/scope and outer request correlation are synthetic transport. The route is already committed; no arrival, incoming subject, future date, or after-arrival usage is synthesized.",
            "heartbeat_published": False, "only_current_target_inputs": True,
            "actual_arrival_observed": False, "actual_after_arrival_usage_observed": False,
            "full_arrival_supply_transition_ready": False,
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
            self.assertEqual(context["schema"], "xar.current-first-route-target-supply-contributors-native-context.v1")
            transport = context["synthetic_context"]
            army_context = context["synthetic_army_context"]
            receipt.update(native_wire_path=wire_path.as_posix(), native_context_path=context_path.as_posix(), native_context=context)
            self.assertEqual(whole["type"], "command_result")
            self.assertEqual(whole["protocol_version"], 1)
            self.assertIs(whole["ok"], True)
            native = whole["result"]
            receipt["native_result"] = deepcopy(native)
            self.assertEqual(set(native) - {"backend_id"}, {"step", "accepted", "status", "query_sequence", "army_strengths"})
            self.assertEqual(native["step"], query_step)
            self.assertIs(native["accepted"], True)
            self.assertEqual(native["status"], "available")
            self.assertIs(type(native["query_sequence"]), int)
            self.assertGreater(native["query_sequence"], 0)
            self.assertEqual(len(native["army_strengths"]), 1)
            row = native["army_strengths"][0]
            self.assertEqual(row["status"], "available")
            self.assertEqual(row["army_id"], 16777217)
            self.assertEqual(row["native_carmy_id"], 33554433)
            self.assertEqual(row["scope_role"], "player")
            self.assertEqual(row["war_ids"], [])
            self.assertEqual(row["current_supply_raw"], 100000000)
            self.assertEqual(row["current_supply_capacity_raw"], 200000000)
            self.assertEqual(row["current_supply_change_monthly_raw"], 2000000)
            current = row["current_province_supply_contributors_v1"]
            self.assertEqual(current["source"], "native_current_province_mode0")
            self.assertEqual(current["province_id"], 1)
            self.assertIs(current["current_usage_ready"], True)
            self.assertEqual(current["native_supply_limit_soldiers"], 100)
            self.assertEqual(current["native_supply_usage_soldiers"], 100)
            self.assertEqual(current["native_province_unit_count"], 1)
            self.assertEqual(current["occurrences"][0]["army_id"], row["army_id"])
            self.assertEqual(current["occurrences"][0]["native_eligible_current_soldiers"], 100)
            family = row[FAMILY]
            self.assertEqual(len(family), 16)
            self.assertEqual(family["source"], "native_current_first_route_target_supply_contributors_12004")
            self.assertEqual(family["input_basis"], "captured_committed_first_route_target")
            self.assertEqual(family["status"], case["status"])
            self.assertEqual(family["unavailable_reason"], case["reason"])
            self.assertIs(family["current_target_inputs_ready"], case["ready"])
            self.assertEqual(family["subject_army_id"], row["army_id"])
            self.assertEqual(family["subject_carmy_id"], row["native_carmy_id"])
            self.assertEqual(family["current_province_id"], 1)
            self.assertEqual(family["first_route_target_province_id"], 2)
            self.assertEqual(family["route_source_count"], 1)
            self.assertEqual(family["subject_matching_occurrence_indices"], case["matches"])
            self.assertEqual(family["subject_included_occurrence_count"], case["included_count"])
            target = family["target_contributors_v1"]
            self.assertEqual(len(target), 14)
            self.assertEqual(target["source"], "native_current_province_mode0")
            self.assertEqual(target["province_id"], 2)
            self.assertEqual(target["subject_army_id"], row["army_id"])
            self.assertEqual(target["subject_carmy_id"], row["native_carmy_id"])
            self.assertIs(target["current_usage_ready"], True)
            self.assertIs(target["contributors_ready"], case["ready"])
            self.assertEqual(target["native_supply_limit_soldiers"], 100)
            self.assertEqual(target["native_supply_usage_soldiers"], case["usage"])
            self.assertEqual(target["native_province_unit_count"], case["roster_count"])
            self.assertEqual(len(target["occurrences"]), case["roster_count"])
            if case["matches"]:
                for index, occurrence in enumerate(target["occurrences"]):
                    self.assertEqual(occurrence["stored_index"], index)
                    self.assertEqual(occurrence["army_id"], row["army_id"])
                    self.assertEqual(occurrence["native_carmy_id"], row["native_carmy_id"])
                    self.assertIs(occurrence["included"], True)
                    self.assertEqual(occurrence["native_eligible_current_soldiers"], 100)
            elif not case["ready"]:
                self.assertIs(target["occurrences"][0]["included"], False)
                self.assertEqual(target["occurrences"][0]["inclusion_basis"], "native_not_common_war_side")
                self.assertIsNone(target["occurrences"][0]["native_eligible_current_soldiers"])
                self.assertEqual(target["occurrences"][0]["regiments"], [])
                self.assertEqual(target["occurrences"][1]["status"], "unavailable")
                self.assertIsNone(target["occurrences"][1]["included"])
                self.assertIsNone(family["subject_included_occurrence_count"])
            for key in ("actual_arrival_observed", "actual_after_arrival_usage_observed",
                        "full_arrival_supply_transition_ready"):
                self.assertIs(family[key], False)
            self.assertEqual(army_context["army_id"], row["army_id"])
            self.assertEqual(army_context["current_province_id"], family["current_province_id"])
            self.assertEqual(army_context["route_province_ids"], [family["first_route_target_province_id"]])
            self.assertEqual(transport["route_province_ids"], army_context["route_province_ids"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            endpoint = SyntheticFirstRouteTargetTransport(whole)
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
            frame_army = {**deepcopy(army_context), "controllable": True}
            frame = {"type": "state_snapshot", "protocol_version": 1,
                     "snapshot_id": transport["snapshot_id"], "revision": transport["native_revision"],
                     "state": {"phase": "map_hud", "date": "synthetic-current-not-live",
                               "date_raw": transport["date_raw"], "speed": 1, "paused": transport["paused"],
                               "map_ready": transport["map_ready"], "history": [], "active_event": None,
                               "pending_character_interaction": None,
                               "played_character": {"character_id": transport["actor_character_id"], "alive": True},
                               "player_armies": [frame_army], "active_wars": []}}
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
                ("army_current_first_route_target_supply_contributors_contract.py", "normalize_current_first_route_target_supply_contributors_v1"),
                ("army_current_first_route_target_supply_contributors_projection.py", "project_current_first_route_target_supply_contributors_v1"),
                ("army_current_province_supply_contributors_contract.py", "normalize_current_province_supply_contributors_v1"),
            }

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
            items = observed[FAMILY]
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["army_id"], row["army_id"])
            projection = items[0]["projection"]
            _write(output / "actual-current-first-route-target-projection.json", projection)
            self.assertEqual(projection["source"], "current_first_route_target_supply_contributors_observation")
            self.assertEqual(projection["input_basis"], "captured_committed_first_route_target")
            self.assertEqual(projection["status"], case["status"])
            self.assertIs(projection["ready"], case["ready"])
            self.assertIs(projection["current_target_inputs_ready"], case["ready"])
            self.assertIs(projection["same_frame_army_context_ready"], True)
            self.assertIs(projection["only_current_target_inputs"], True)
            self.assertEqual(projection["observed_inputs"], family)
            self.assertIs(projection["target_current_usage_ready"], True)
            self.assertEqual(projection["target_native_supply_limit_soldiers"], 100)
            self.assertEqual(projection["target_native_supply_usage_soldiers"], case["usage"])
            self.assertIs(projection["subject_presence_witness_ready"], case["ready"])
            self.assertEqual(projection["subject_presence_witness"], case["witness"])
            self.assertEqual(projection["missing_inputs"], [] if case["ready"] else [case["reason"]])
            for key in ("actual_arrival_observed", "actual_after_arrival_usage_observed",
                        "full_arrival_supply_transition_ready"):
                self.assertIs(projection[key], False)
            self.assertEqual(observed["army_strengths"][0][FAMILY], family)
            self.assertEqual(observed["army_strengths"][0]["current_province_supply_contributors_v1"], current)
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
            self.assertTrue(interesting <= executed, "actual registered/driver/strict/Service target path must run")
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
        CurrentFirstRouteTargetSupplyContributorsWholeService12004Tests(METHOD)]))
    sys.exit(0 if result.wasSuccessful() else 1)
