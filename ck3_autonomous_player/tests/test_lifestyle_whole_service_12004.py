"""Consume the four fresh native Lifestyle current-state wires, offline only.

Source prepared; imports and the sole compound method run only in Root FIRST.
Lifestyle has no named MCP closure or advertised public Lifestyle step. This
fixture uses the existing typed private Driver and existing Service observer.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
import traceback
import unittest


CONFIG = None
METHOD = "test_four_native_current_state_wholes_keep_private_driver_and_service_observer_contract"
STEP = "private-query-player-lifestyle-current-state-v1"
EPISODE = "native-29829-fixture"
SCENES = (
    ("01-no-current-focus", None),
    ("02-current-focus-progress", None),
    ("03-native-sample-drift", "native_sample_drift"),
    ("04-old-sha-rejected", "exact_build_not_admitted"),
)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _assert_preserved(test: unittest.TestCase, original: object,
                      observed: object, path: str) -> None:
    test.assertIs(type(observed), type(original), path)
    if isinstance(original, dict):
        test.assertTrue(set(original) <= set(observed), path)
        for key, value in original.items():
            _assert_preserved(test, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        test.assertEqual(len(observed), len(original), path)
        for index, value in enumerate(original):
            _assert_preserved(test, value, observed[index], f"{path}[{index}]")
    else:
        test.assertEqual(observed, original, path)


class SyntheticLifestyle12004Endpoint:
    """Synthetic transport; only the outer request correlation may change."""

    pipe_name = r"\\.\pipe\synthetic-lifestyle-current-state-12004-not-live"

    def __init__(self, whole_wire: dict[str, object]):
        self.whole_wire = deepcopy(whole_wire)
        self.on_frame = None
        self.requests: list[dict[str, object]] = []
        self.delivered_frames: list[dict[str, object]] = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        if not callable(self.on_frame):
            raise RuntimeError("actual driver did not install its frame receiver")
        self.on_frame(deepcopy(frame))

    def send(self, frame):
        self.requests.append(deepcopy(frame))
        if frame.get("type") != "execute_step":
            return
        if frame.get("step") != STEP:
            raise AssertionError("only the four original current-state wires are supplied")
        delivered = deepcopy(self.whole_wire)
        delivered["request_id"] = frame["request_id"]
        self.delivered_frames.append(deepcopy(delivered))
        self.publish(delivered)

    def transport_error(self):
        return None

    def close(self):
        pass


def _synthetic_paused_frame() -> dict[str, object]:
    # The native fixture's Frame/Source callbacks are synthetic too. These are
    # their explicit context values, including for the two unavailable wires.
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": "synthetic-lifestyle-current-state-12004:7", "revision": 7,
        "state": {
            "phase": "map_hud", "date": "synthetic-not-live", "date_raw": 1234,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "one_life_terminal_reason": None,
            "played_character": {"character_id": 29829, "alive": True},
            "player_armies": [], "active_wars": [], "episode_run_id": EPISODE,
        },
    }


class LifestyleWholeService12004Tests(unittest.TestCase):
    def test_four_native_current_state_wholes_keep_private_driver_and_service_observer_contract(self):
        self.assertIsNotNone(CONFIG, "Root supplies the four explicit CLI inputs")
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        compound = {
            "schema": "xar.lifestyle-current-state-12004.private-whole-consumer.v1",
            "status": "RED", "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "scenes": [],
            "original_whole_scene_count": 4, "native_execute_request_bound": 4,
            "registered_lifestyle_named_tool": False,
            "public_lifestyle_generic_step": False,
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "actual_service_consumer": "_observe_opening_lifestyle_perks_v1",
            "qualification": "offline current-state typed transport and Service observer only",
            "synthetic_boundary": "Native producer Frame/Source callbacks, endpoint, exact4 hello, paused state and outer request_id correlation are synthetic. Native result/error and snapshot sidecar are not rewritten.",
            "native_EXE_ABI_proof_from_test": False, "live": False,
            "selector_or_queue_exercised": False,
            "professional_workforce_native_route_exercised": False,
            "formal_legal_candidate_inventory_qualified": False,
            "full_private_route_set_qualified": False,
            "full_Service_planning_or_auto_turn_qualified": False,
            "game_process_SDK_operations": 0, "old_GREEN_replays": 0,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0)
            self.assertTrue(CONFIG.source_commit)
            supplied = Path(CONFIG.source_root)
            source = (supplied / "ck3_autonomous_player"
                      if (supplied / "ck3_autonomous_player").is_dir() else supplied)
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir())
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # Production imports happen only in Root's future authorized FIRST.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.version_identity import CK3_12004

            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            compound["source_root"] = source.as_posix()
            compound["native_wire_dir"] = Path(CONFIG.native_wire_dir).as_posix()
            for key, cls in (("driver_module", NativeHeadlessGameplayDriver),
                             ("service_module", GameplayBridgeService)):
                module_path = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(module_path.is_relative_to((source / "src").resolve()))
                compound[key] = module_path.as_posix()

            for case, native_failure in SCENES:
                with self.subTest(case=case):
                    case_dir = output / case
                    case_dir.mkdir(parents=True, exist_ok=True)
                    case_started = time.perf_counter()
                    receipt = {"case": case, "status": "RED", "call_trace": [],
                               "native_source_callbacks": {
                                   "frame_calls": 0 if case == "04-old-sha-rejected" else 1 if native_failure else 2,
                                   "source_calls": 0 if case == "04-old-sha-rejected" else 2,
                                   "origin": "Frozen producer assertions; not live callback observations"}}
                    driver = None
                    endpoint = None
                    previous_profile = sys.getprofile()
                    try:
                        wire_path = Path(CONFIG.native_wire_dir) / (case + ".json")
                        snapshot_path = Path(CONFIG.native_wire_dir) / (case + "-snapshot.json")
                        wire_bytes = wire_path.read_bytes()
                        snapshot_bytes = snapshot_path.read_bytes()
                        (case_dir / "original-whole.json").write_bytes(wire_bytes)
                        (case_dir / "original-snapshot.json").write_bytes(snapshot_bytes)
                        wire = json.loads(wire_bytes)
                        raw_snapshot = json.loads(snapshot_bytes)
                        self.assertEqual(wire["type"], "command_result")
                        self.assertEqual(wire["protocol_version"], 1)
                        self.assertEqual(wire["request_id"], case)
                        self.assertIs(raw_snapshot["private_build"], True)
                        self.assertIs(raw_snapshot["advertised"], False)

                        endpoint = SyntheticLifestyle12004Endpoint(wire)
                        driver = NativeHeadlessGameplayDriver(
                            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                            allow_private_lifestyle_formal_trial=True,
                            episode_projection="native_campaign")
                        service = GameplayBridgeService(driver)
                        self.assertIs(type(driver), NativeHeadlessGameplayDriver)
                        self.assertIs(service.driver, driver)
                        hello = {
                            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                            "pid": 4242, "session_generation": 0,
                            "game_version": CK3_12004.game_version,
                            "executable_sha256": CK3_12004.executable_sha256,
                            "expected_ck3_version": CK3_12004.game_version,
                            "expected_ck3_sha256": CK3_12004.executable_sha256,
                            "capabilities": ["game.state.snapshot"],
                        }
                        paused_frame = _synthetic_paused_frame()
                        _write_json(case_dir / "synthetic-hello.json", hello)
                        _write_json(case_dir / "synthetic-paused-frame.json", paused_frame)
                        endpoint.publish(hello)
                        endpoint.publish(paused_frame)
                        before = driver.take_internal_semantic_snapshot()
                        self.assertEqual(before["snapshot_id"], "native:7")
                        self.assertEqual(before["native_revision"], 7)
                        self.assertEqual(before["date_raw"], 1234)
                        self.assertEqual(before["episode_run_id"], EPISODE)
                        self.assertIs(before["paused"], True)
                        receipt["before_synthetic_frame"] = deepcopy(before)
                        interesting = {
                            ("native_driver.py", "query_player_lifestyle_current_state_private_v1"),
                            ("player_lifestyle_private_transport_v1.py", "query_player_lifestyle_private_v1"),
                            ("service.py", "_observe_opening_lifestyle_perks_v1"),
                            ("service.py", "snapshot"),
                        }

                        def observe_call(frame, event, argument):
                            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
                            if key in interesting and event == "call":
                                receipt["call_trace"].append({"source": frame.f_code.co_filename,
                                                              "function": key[1]})

                        sys.setprofile(observe_call)
                        query = driver.query_player_lifestyle_current_state_private_v1(
                            expected_revision=before["revision"])
                        service_observation = service._observe_opening_lifestyle_perks_v1(
                            before=before,
                            focus=(query["snapshot"]["current_focus"]
                                   if query.get("status") == "available" else {}),
                            revision=before["revision"], formal_query=query)
                        sys.setprofile(previous_profile)
                        receipt["actual_driver_normalized_query"] = deepcopy(query)
                        receipt["actual_service_observation"] = deepcopy(service_observation)
                        _write_json(case_dir / "normalized-query.json", query)
                        _write_json(case_dir / "service-observation.json", service_observation)
                        after = driver.take_internal_semantic_snapshot()
                        receipt["after_synthetic_frame"] = deepcopy(after)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                                    "episode_run_id", "paused", "map_ready"):
                            self.assertEqual(after[key], before[key])

                        requests = [frame for frame in endpoint.requests
                                    if frame.get("type") == "execute_step"]
                        self.assertEqual(len(requests), 1)
                        request = requests[0]
                        self.assertEqual(request["step"], STEP)
                        self.assertEqual(request["expected_revision"], 7)
                        self.assertEqual(request["expected_snapshot_id"], "native:7")
                        self.assertEqual(request["episode_run_id"], EPISODE)
                        self.assertEqual(request["expected_date_raw"], 1234)
                        self.assertEqual(request["expected_player_character_id"], 29829)
                        self.assertTrue(request["request_id"].startswith("life-query-"))
                        self.assertEqual(len(endpoint.delivered_frames), 1)
                        delivered = endpoint.delivered_frames[0]
                        self.assertEqual(delivered["request_id"], request["request_id"])
                        restored_outer = deepcopy(delivered)
                        restored_outer["request_id"] = wire["request_id"]
                        self.assertEqual(restored_outer, wire)
                        _assert_preserved(self, wire.get("result"), delivered.get("result"), "native-result")
                        self.assertEqual(query["step"], STEP)
                        self.assertEqual(query["request_id"], request["request_id"])
                        self.assertEqual(service_observation["status"], "unknown")
                        self.assertIsNone(service_observation["legal_candidate_count_in_scope"])
                        self.assertIsNone(service_observation["policy_target_final_legal"])
                        self.assertIsNone(service_observation["policy_target_owned"])

                        if native_failure is None:
                            self.assertIs(wire["ok"], True)
                            result = wire["result"]
                            self.assertEqual(result["step"], STEP)
                            self.assertIs(result["private_build"], True)
                            self.assertIs(result["advertised"], False)
                            self.assertEqual(result["status"], "available")
                            self.assertEqual(result["episode_run_id"], EPISODE)
                            self.assertEqual(result["snapshot"], raw_snapshot)
                            self.assertEqual(query["status"], "available")
                            _assert_preserved(self, raw_snapshot, query["snapshot"], "normalized-snapshot")
                            self.assertEqual(set(query["snapshot"]), set(raw_snapshot) | {"episode_run_id"})
                            self.assertEqual(query["snapshot"]["episode_run_id"], EPISODE)
                            self.assertIsNone(query["formal_precondition_status"])
                            self.assertEqual(raw_snapshot["readiness"], {
                                "current_focus_ready": True, "lifestyle_progress_ready": True,
                                "owned_perks_ready": True, "legal_focus_candidates_ready": False,
                                "legal_perk_candidates_ready": False, "same_frame_ready": True})
                            self.assertEqual(service_observation["query_status"], "legal_candidates_unavailable")
                            self.assertEqual(raw_snapshot["actor_traits"], {"status": "unavailable"})
                            for key in ("legal_focus_candidates", "legal_perk_candidates"):
                                self.assertEqual(raw_snapshot[key]["status"], "unavailable")
                                self.assertEqual(raw_snapshot[key]["items"], [])
                            if case == "01-no-current-focus":
                                self.assertEqual(raw_snapshot["current_focus"], {"presence": "absent"})
                                self.assertEqual(raw_snapshot["current_lifestyle_progress"], {"presence": "absent"})
                                self.assertEqual(raw_snapshot["owned_perk_keys"], [])
                            else:
                                self.assertEqual(raw_snapshot["current_focus"], {
                                    "presence": "present", "key": "stewardship_wealth_focus",
                                    "lifestyle_key": "stewardship_lifestyle"})
                                self.assertEqual(raw_snapshot["current_lifestyle_progress"], {
                                    "presence": "present", "lifestyle_key": "stewardship_lifestyle",
                                    "xp_total_raw": 12345678, "xp_within_level_raw": 2345678,
                                    "xp_per_level": 1000, "unspent_perk_points": 2,
                                    "used_perk_points": 3})
                                self.assertEqual(raw_snapshot["owned_perk_keys"], ["cutting_corners_perk"])
                            receipt["current_state_ready"] = True
                        else:
                            self.assertIs(wire["ok"], False)
                            self.assertEqual(raw_snapshot, {
                                "private_build": True, "advertised": False, "status": "unavailable",
                                "unavailable_reason": native_failure})
                            self.assertIn(native_failure, json.dumps(wire["error"]))
                            self.assertEqual(query["status"], "native_query_unavailable")
                            self.assertEqual(query["native_error"], wire["error"])
                            self.assertNotIn("snapshot", query)
                            self.assertEqual(service_observation["query_status"], "native_query_unavailable")
                            self.assertEqual(service_observation["native_error"], wire["error"])
                            receipt["current_state_ready"] = False
                        required_calls = {
                            "query_player_lifestyle_current_state_private_v1",
                            "query_player_lifestyle_private_v1",
                            "_observe_opening_lifestyle_perks_v1",
                        }
                        self.assertTrue(required_calls <= {row["function"] for row in receipt["call_trace"]})
                        receipt["execute_request_count"] = 1
                        receipt["legal_candidates_ready"] = False
                        receipt["status"] = "GREEN"
                        _write_json(case_dir / "request.json", request)
                        _write_json(case_dir / "runtime-whole.json", delivered)
                    except Exception as error:
                        receipt["error_type"] = type(error).__name__
                        receipt["error"] = str(error)
                        receipt["traceback"] = traceback.format_exc()
                        raise
                    finally:
                        primary_failure_active = sys.exc_info()[0] is not None
                        cleanup_error = None
                        sys.setprofile(previous_profile)
                        if endpoint is not None:
                            receipt["transport_requests"] = deepcopy(endpoint.requests)
                            receipt["runtime_whole_frames"] = deepcopy(endpoint.delivered_frames)
                        if driver is not None:
                            try:
                                driver.close()
                            except Exception as error:
                                cleanup_error = error
                                receipt["cleanup_error"] = {"type": type(error).__name__, "message": str(error)}
                                receipt["status"] = "RED"
                        receipt["elapsed_seconds"] = time.perf_counter() - case_started
                        _write_json(case_dir / "receipt.json", receipt)
                        compound["scenes"].append(receipt)
                        _write_json(output / "compound-receipt.json", compound)
                        if cleanup_error is not None and not primary_failure_active:
                            raise cleanup_error
            self.assertEqual(len(compound["scenes"]), 4)
            self.assertTrue(all(row["status"] == "GREEN" for row in compound["scenes"]))
            self.assertEqual(sum(row["execute_request_count"] for row in compound["scenes"]), 4)
            compound["status"] = "GREEN"
        except Exception as error:
            compound["error_type"] = type(error).__name__
            compound["error"] = str(error)
            raise
        finally:
            compound["elapsed_seconds"] = time.perf_counter() - started
            _write_json(output / "compound-receipt.json", compound)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--native-wire-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    suite = unittest.TestSuite([LifestyleWholeService12004Tests(METHOD)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
