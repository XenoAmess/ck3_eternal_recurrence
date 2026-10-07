"""One fresh compiled whole-wire consumer for conditional Unit entry state.

Run only with explicit --source-root, --native-wire and --output-dir.
The endpoint supplies synthetic transport/scope and correlates request_id only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading
import traceback
import unittest

FAMILY = "current_unit_new_date_callback_entry_inputs_v1"
SCHEDULE = "current_unit_new_date_schedule_inputs_v1"
PROJECTION = "current_unit_new_date_entry_normalization_v1"
VALUE = "conditional_unit_170_raw_after_next_new_date_entry_prefix"
CLOCK = "source_derived_next_daily_supply_frame_inputs_v1"
SCENES = (
    "state2_empty_repeats", "state3_empty_repeats", "nonempty_route",
    "negative_route_count", "zero_occurrences", "typed_unavailable",
)
# Expected source branch outcomes, never replacement native business rows.
EXPECTED = (
    (2, 0, [1, 3], 0), (3, 0, [1, 3], 0), (2, 2, [1, 3], 2),
    (3, -2, [1, 3], 3), (2, 0, [], 2), (2, None, [1, 3], None),
)
FALSE_FIELDS = (
    "actual_unit_new_date_callback_observed",
    "actual_movement_or_arrival_observed",
    "actual_future_frame_observed",
    "earlier_stage_outputs_reconstructed",
    "repeated_full_callback_effects_reconstructed",
    "full_daily_supply_transition_ready",
    "full_monthly_ready",
)
_OPTIONS = None


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def _assert_native_values(case: unittest.TestCase, original: object,
                          observed: object, path: str) -> None:
    """Check every original native value as a subset of production enrichment."""
    if isinstance(original, dict):
        case.assertIsInstance(observed, dict, path)
        for key, value in original.items():
            case.assertIn(key, observed, path)
            _assert_native_values(case, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        case.assertIsInstance(observed, list, path)
        case.assertEqual(len(observed), len(original), path)
        for index, value in enumerate(original):
            _assert_native_values(case, value, observed[index], f"{path}[{index}]")
    else:
        case.assertIs(type(observed), type(original), path)
        case.assertEqual(observed, original, path)


class _CompiledWholeEndpoint:
    """No callback execution, action completion or business row is manufactured."""

    def __init__(self, scene: str, route: str, whole: dict[str, object]) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_bridge_mcp_unit_entry_prefix_" + scene + "_" + route
        self.whole = whole
        self.requests: list[dict[str, object]] = []
        self.delivered: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("production driver did not start the endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        self.requests.append(deepcopy(frame))
        if frame.get("type") == "ping":
            self.publish({"type": "pong", "protocol_version": 1,
                          "request_id": frame["request_id"]})
            return
        if frame.get("type") != "execute_step" or frame.get("step") != "query-army-strengths-v1":
            raise AssertionError("unexpected transport request: " + str(frame))
        delivered = deepcopy(self.whole)
        delivered["request_id"] = frame["request_id"]
        self.delivered.append(deepcopy(delivered))
        self.publish(delivered)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class CurrentUnitNewDateEntryNormalizationWholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_native_whole_entry_prefix_reaches_both_registered_service_routes(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("this sole consumer requires its explicit readonly CLI")
        from xar_autoplayer.bridge import army_current_unit_new_date_entry_normalization_projection as leaf
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

        source_root = _OPTIONS.source_root.resolve()
        project = source_root / "ck3_autonomous_player"
        if not project.is_dir():
            project = source_root
        self.assertEqual(Path(leaf.__file__).resolve(),
                         project / "src/xar_autoplayer/bridge/army_current_unit_new_date_entry_normalization_projection.py")
        wire_path = _OPTIONS.native_wire.resolve()
        output_dir = _OPTIONS.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        packet = json.loads(wire_path.read_text(encoding="utf-8"))
        self.assertEqual(set(packet), {"schema_version", "scene_order", "samples"})
        self.assertIs(type(packet["schema_version"]), int)
        self.assertEqual(packet["schema_version"], 1)
        self.assertEqual(packet["scene_order"], list(SCENES))
        self.assertEqual(set(packet["samples"]), set(SCENES))
        receipt: dict[str, object] = {
            "date": "2026-10-07", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(source_root), "native_wire": str(wire_path),
            "scene_order": list(SCENES), "native_body_rewrites": 0,
            "native_producer_reexecution": 0,
            "synthetic_boundary": "endpoint hello/paused scope/request_id correlation only",
            "business_path": "actual NativeHeadlessGameplayDriver -> GameplayBridgeService -> registered MCP",
            "projection_boundary": "first selected entry prefix, never full repeated callbacks",
            "passes": [],
        }
        active: dict[str, object] | None = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()
        watched = {
            ("mcp_server.py", "ck3_execute_step"),
            ("mcp_server.py", "ck3_query_army_strengths"),
            ("service.py", "execute_step"), ("service.py", "query_army_strengths"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("army_current_unit_new_date_entry_normalization_projection.py",
             "normalize_current_unit_new_date_callback_entry_inputs_v1"),
            ("army_current_unit_new_date_entry_normalization_projection.py",
             "project_current_unit_new_date_entry_normalization_v1"),
        }

        def observe(frame, event, value):
            if active is None:
                return
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in watched:
                return
            if event == "call":
                active["calls"].append({"source": frame.f_code.co_filename, "function": key[1]})
                if key[0] == "service.py":
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, active["driver"])
            elif event == "return" and key == ("native_driver.py", "execute_step"):
                active["driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", active["service_function"]):
                active["service_result"] = deepcopy(value)

        observed_date_independent_ready = False
        try:
            # One observer spans all passes, including a reused SDK worker thread.
            sys.setprofile(observe)
            threading.setprofile(observe)
            for ordinal, (scene, expected) in enumerate(zip(SCENES, EXPECTED), 1):
                raw_state, route_count, positions, expected_value = expected
                whole = packet["samples"][scene]
                self.assertIsInstance(whole, dict)
                self.assertEqual(whole["type"], "command_result")
                self.assertEqual(whole["protocol_version"], 1)
                self.assertIs(whole["ok"], True)
                self.assertIsInstance(whole["request_id"], str)
                native = whole["result"]
                self.assertEqual(set(native),
                                 {"step", "accepted", "status", "query_sequence", "army_strengths"})
                self.assertEqual(native["step"], "query-army-strengths-v1")
                self.assertIs(native["accepted"], True)
                self.assertEqual(native["status"], "available")
                self.assertEqual(native["query_sequence"], ordinal)
                self.assertEqual(len(native["army_strengths"]), 1)
                row = native["army_strengths"][0]
                self.assertEqual(row["status"], "available")
                inputs, schedule, budget = row[FAMILY], row[SCHEDULE], row["monthly_loss_budget_inputs_v1"]
                self.assertEqual(set(inputs), {
                    "schema_version", "source", "capture_boundary", "status", "ready",
                    "unavailable_reason", "subject_army_id_u32", "subject_carmy_id_u32",
                    "unit_route_count_i32",
                })
                self.assertEqual(inputs["schema_version"], 1)
                self.assertEqual(inputs["source"], "native_current_unit_new_date_callback_entry_inputs_12004")
                self.assertEqual(inputs["capture_boundary"], "current_query_before_unit_new_date_stage")
                self.assertEqual(inputs["subject_army_id_u32"], row["army_id"] & 0xFFFFFFFF)
                self.assertEqual(inputs["subject_carmy_id_u32"], row["native_carmy_id"] & 0xFFFFFFFF)
                self.assertEqual(inputs["unit_route_count_i32"], route_count)
                self.assertEqual(budget["unit_native_170_raw"], raw_state)
                # Genuine raw170 is captured before optional budget callbacks.
                self.assertIs(budget["ready"], False)
                self.assertEqual(schedule["subject_stored_id_positions"], positions)
                self.assertEqual(schedule["subject_stored_id_occurrence_count_i32"], len(positions))
                self.assertIs(schedule["ready"], True)
                prefix_ready = scene != "typed_unavailable"
                self.assertIs(inputs["ready"], prefix_ready)
                self.assertEqual(inputs["status"], "available" if prefix_ready else "unavailable")
                self.assertEqual(inputs["unavailable_reason"], None if prefix_ready else
                                 "current_unit_new_date_callback_entry_unit_type_unavailable")
                sidecar = json.loads(
                    (wire_path.parent / (scene + ".native-context.json")).read_text(encoding="utf-8"))
                context = sidecar["synthetic_context"]
                self.assertEqual(context["snapshot_id"], "native:1")
                self.assertIs(type(context["native_revision"]), int)
                self.assertEqual(context["native_revision"], 1)
                self.assertEqual(context["date_raw"], 53288448)
                self.assertEqual(context["actor_character_id"], 29829)
                self.assertIs(context["paused"], True)
                self.assertIs(context["map_ready"], True)

                for route in ("ck3_execute_step", "ck3_query_army_strengths"):
                    case_dir = output_dir / scene / route
                    case_dir.mkdir(parents=True, exist_ok=True)
                    endpoint = _CompiledWholeEndpoint(scene, route, whole)
                    driver = None
                    observed: dict[str, object] = {
                        "scene": scene, "route": route, "calls": [],
                        "service_function": "execute_step" if route == "ck3_execute_step" else "query_army_strengths",
                    }
                    receipt["passes"].append(observed)
                    active = observed
                    try:
                        driver = NativeHeadlessGameplayDriver(
                            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                            state_dir=case_dir / "driver-state", episode_projection="native_campaign")
                        observed["driver"] = driver
                        self.assertIs(type(driver), NativeHeadlessGameplayDriver)
                        server = create_server(driver)
                        self.assertIn(route, server._tool_manager._tools)
                        endpoint.publish({
                            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                            "pid": context["bridge_host_pid"], "connection_generation": 1,
                            "game_version": CK3_12004.game_version,
                            "executable_sha256": CK3_12004.executable_sha256,
                            "expected_ck3_version": CK3_12004.game_version,
                            "expected_ck3_sha256": CK3_12004.executable_sha256,
                            "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
                        })
                        endpoint.publish({
                            "type": "state_snapshot", "protocol_version": 1,
                            "snapshot_id": context["snapshot_id"], "revision": context["native_revision"],
                            "state": {
                                "phase": "map_hud", "date": "synthetic-current-not-live",
                                "date_raw": context["date_raw"], "speed": 1,
                                "paused": True, "map_ready": True, "history": [], "active_event": None,
                                "pending_character_interaction": None,
                                "played_character": {"character_id": context["actor_character_id"], "alive": True},
                                "player_armies": [{
                                    "army_id": row["army_id"], "controllable": True,
                                    "owner_character_id": context["actor_character_id"],
                                    "current_province_id": context["current_province_id"],
                                }],
                                "active_wars": [],
                            },
                        })
                        before = driver.take_snapshot()
                        observed["before"] = deepcopy(before)
                        self.assertEqual(before["snapshot_id"], "native:1")
                        self.assertEqual(before["native_revision"], context["native_revision"])
                        self.assertIs(type(before["revision"]), int)
                        self.assertGreater(before["revision"], 0)
                        self.assertEqual(before["date_raw"], context["date_raw"])
                        kwargs = {"expected_revision": before["revision"]}
                        if route == "ck3_execute_step":
                            kwargs["step"] = "query-army-strengths-v1"
                        else:
                            kwargs["army_ids"] = [row["army_id"]]
                        registered = await server.call_tool(route, kwargs)
                        self.assertIs(registered.is_error, False)
                        result = registered.structured_content
                        self.assertIsInstance(result, dict)
                        self.assertEqual(result, observed["service_result"])
                        _assert_native_values(self, native, observed["driver_result"], "driver")
                        _assert_native_values(self, native, result, "registered")
                        self.assertEqual(result["army_strengths"][0][FAMILY], inputs)
                        for field in ("snapshot_id", "revision", "native_revision"):
                            self.assertEqual(result["queried_" + field], before[field])
                        if route == "ck3_query_army_strengths":
                            for field in ("snapshot_id", "revision", "native_revision", "date_raw"):
                                self.assertEqual(result["source"][field], before[field])
                        derived = result[PROJECTION]
                        self.assertEqual(len(derived), 1)
                        self.assertEqual(derived[0]["army_id"], row["army_id"])
                        self.assertEqual(derived[0]["source_provenance"], {
                            field: before[field] for field in ("snapshot_id", "revision", "native_revision")
                        })
                        projection = derived[0]["projection"]
                        self.assertEqual(projection["projection_boundary"], "first_selected_unit_new_date_entry_prefix")
                        self.assertEqual(projection["condition"],
                                         "observed_schedule_receiver_state_and_route_count_held_at_first_selected_entry")
                        self.assertIs(projection["prefix_input_ready"], prefix_ready)
                        self.assertEqual(projection[VALUE], expected_value)
                        self.assertEqual(projection["unavailable_reason"], inputs["unavailable_reason"])
                        self.assertEqual(projection["unit_native_170_raw"], raw_state)
                        self.assertEqual(projection["unit_route_count_i32"], route_count)
                        self.assertEqual(projection["subject_stored_id_positions"], positions)
                        self.assertIs(projection["scheduled_by_observed_stored_ids"], bool(positions))
                        self.assertIs(projection["conditional_first_entry_prefix_would_write"],
                                      None if not prefix_ready else scene in SCENES[:2])
                        for field in FALSE_FIELDS:
                            self.assertIs(projection[field], False)
                        original_clock = row.get(CLOCK) or {}
                        self.assertIs(projection["source_derived_full_cdate64_ready"],
                                      original_clock.get("source_derived_full_cdate64_ready", False))
                        for field in (
                            "source_derived_next_date_raw_i32", "source_derived_next_native_day_index_raw_i32",
                            "source_derived_next_date_storage_raw64", "source_derived_next_calendar_day_u8",
                            "source_derived_next_calendar_month_u8",
                        ):
                            self.assertEqual(projection[field], original_clock.get(field))
                        if prefix_ready and not projection["source_derived_full_cdate64_ready"]:
                            observed_date_independent_ready = True
                        executed = {(Path(item["source"]).name, item["function"]) for item in observed["calls"]}
                        self.assertTrue({
                            ("mcp_server.py", route), ("service.py", observed["service_function"]),
                            ("native_driver.py", "execute_step"),
                            ("native_driver.py", "_execute_army_strength_query"),
                            ("war_contract.py", "_normalize_army_strength_row"),
                            ("army_current_unit_new_date_entry_normalization_projection.py",
                             "normalize_current_unit_new_date_callback_entry_inputs_v1"),
                            ("army_current_unit_new_date_entry_normalization_projection.py",
                             "project_current_unit_new_date_entry_normalization_v1"),
                        } <= executed, executed)
                        commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
                        pings = [item for item in endpoint.requests if item["type"] == "ping"]
                        self.assertEqual(len(commands), 1)
                        self.assertEqual(len(pings), 1)
                        self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
                        self.assertEqual(len(endpoint.delivered), 1)
                        delivered = endpoint.delivered[0]
                        self.assertEqual(delivered["request_id"], commands[0]["request_id"])
                        self.assertEqual(delivered["result"], native)
                        for key in whole:
                            if key != "request_id":
                                self.assertEqual(delivered[key], whole[key])
                        observed["transport_requests"] = deepcopy(endpoint.requests)
                        observed["registered_result"] = registered.model_dump(mode="json", by_alias=True)
                        _write_json(case_dir / "actual-driver-result.json", observed["driver_result"])
                        _write_json(case_dir / "actual-service-result.json", result)
                        _write_json(case_dir / "actual-registered-result.json", observed["registered_result"])
                    finally:
                        if driver is not None:
                            driver.close()
                        observed.pop("driver", None)
                        active = None
            self.assertTrue(observed_date_independent_ready, "date-free prefix was not exercised without full clock")
            self.assertEqual(len(receipt["passes"]), 12)
            receipt["status"] = "GREEN"
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            active = None
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            for observed in receipt["passes"]:
                observed.pop("driver", None)
            _write_json(output_dir / "COMPOUND-RECEIPT.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    _OPTIONS = parser.parse_args()
    _root = _OPTIONS.source_root.resolve()
    _project = _root / "ck3_autonomous_player"
    if not _project.is_dir():
        _project = _root
    sys.path.insert(0, str(_project / "src"))
    unittest.main(argv=[sys.argv[0]], verbosity=2)
