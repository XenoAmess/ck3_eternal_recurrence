"""One fresh compiled whole-wire consumer for conditional first-edge selection.

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
PROJECTION = "current_unit_next_first_edge_selection_v1"
MOVEMENT_PROJECTION = "current_unit_next_movement_prefix_v1"
VALUE = "conditional_unit_168_raw_after_next_new_date_movement_prefix"
CLOCK = "source_derived_next_daily_supply_frame_inputs_v1"
SCENES = (
    "edge_above_cost", "edge_equal_hold", "edge_below_override",
    "edge_provider_unavailable", "edge_cost_unavailable",
)
# Genuine compiled scenes: cost, provider, current DAYS, ratio, branch, ready, demand, reason
EXPECTED = (
    (106, None, 85714, 94339, True, True, False, None),
    (107, 0, 100000, 93457, False, True, True, None),
    (108, 3, 114285, 92592, True, True, True, None),
    (107, None, 100000, 93457, None, False, True, "first_edge_arrival_provider_byte_e_unavailable"),
    (None, 0, 100000, 93457, None, False, None, "first_route_edge_weight_cost_unavailable"),
)
MOVEMENT_FALSE_FIELDS = (
    "actual_unit_new_date_callback_observed",
    "actual_movement_or_arrival_observed",
    "actual_future_frame_observed",
    "earlier_stage_outputs_reconstructed",
    "intervening_empty_route_handler_reconstructed",
    "route_consumption_or_arrival_reconstructed",
    "repeated_full_callback_effects_reconstructed",
    "full_daily_supply_transition_ready",
    "full_monthly_ready",
)
FALSE_FIELDS = (
    "actual_future_frame_observed", "actual_first_edge_selection_observed",
    "actual_first_edge_arrival_observed", "post_selection_subtraction_reconstructed",
    "route_consumption_reconstructed", "clamp_reconstructed",
    "repeated_callback_effects_reconstructed", "full_unit_new_date_callback_ready",
    "native_action_executed", "earlier_stage_outputs_reconstructed",
    "intervening_empty_route_handler_reconstructed",
    "full_daily_supply_transition_ready", "full_monthly_ready",
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
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_bridge_mcp_unit_first_edge_selection_" + scene + "_" + route
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


class CurrentUnitFirstEdgeSelectionWholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_current_cost_and_provider_select_the_first_edge_branch_through_registered_routes(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("this sole consumer requires its explicit readonly CLI")
        from xar_autoplayer.bridge import army_current_unit_next_first_edge_selection_projection as leaf
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
                         project / "src/xar_autoplayer/bridge/army_current_unit_next_first_edge_selection_projection.py")
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
            "date": "2026-10-08", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(source_root), "native_wire": str(wire_path),
            "scene_order": list(SCENES), "native_body_rewrites": 0,
            "native_producer_reexecution": 0,
            "synthetic_boundary": "endpoint hello/paused scope/request_id correlation only",
            "business_path": "actual NativeHeadlessGameplayDriver -> GameplayBridgeService -> registered MCP",
            "projection_boundary": "first selected signed edge comparison/provider selection before arrival subtraction; inputs held",
            "optional_raw_increments": ["first_route_edge_weight_cost_raw", "first_edge_arrival_provider_byte_e_u8"],
            "passes": [],
        }
        active: dict[str, object] | None = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()
        watched = {
            ("mcp_server.py", "ck3_execute_step"),
            ("mcp_server.py", "ck3_query_army_strengths"),
            ("service.py", "execute_step"), ("service.py", "query_army_strengths"),
            ("service.py", "_unit_next_movement_projection_rows"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("army_current_unit_new_date_entry_normalization_projection.py",
             "normalize_current_unit_new_date_callback_entry_inputs_v1"),
            ("army_current_unit_new_date_entry_normalization_projection.py",
             "project_current_unit_new_date_entry_normalization_v1"),
            ("war_contract.py", "_normalize_current_movement_progress"),
            ("army_current_unit_next_movement_prefix_projection.py",
             "project_current_unit_next_movement_prefix_v1"),
            ("army_current_unit_next_first_edge_selection_projection.py",
             "project_current_unit_next_first_edge_selection_v1"),
        }

        def observe(frame, event, value):
            if active is None:
                return
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in watched:
                return
            if event == "call":
                active["calls"].append({"source": frame.f_code.co_filename, "function": key[1]})
                if key[0] == "service.py" and "self" in frame.f_locals:
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, active["driver"])
                if key == ("army_current_unit_next_first_edge_selection_projection.py",
                           "project_current_unit_next_first_edge_selection_v1"):
                    self.assertEqual(len(active["movement_prefix_returns"]), 1)
                    self.assertIs(frame.f_locals["movement_prefix"], active["movement_prefix_returns"][0])
            elif event == "return" and key == ("army_current_unit_next_movement_prefix_projection.py",
                                             "project_current_unit_next_movement_prefix_v1"):
                active["movement_prefix_returns"].append(value)
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
                cost, provider, duration, ratio, selected, selection_ready, provider_demanded, expected_reason = expected
                raw_state, route_count, positions = 2, 2, [1, 3]
                weight, cached, edge, admission = 100, 7, None, True
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
                self.assertIs(inputs["ready"], True)
                self.assertEqual(inputs["status"], "available")
                self.assertIsNone(inputs["unavailable_reason"])
                movement = row["current_movement_progress"]
                self.assertEqual(movement["accumulated_movement_weight_raw"], weight)
                self.assertEqual(movement["cached_edge_speed_raw"], cached)
                self.assertIn("current_edge_movement_rate_raw", movement)
                self.assertEqual(movement["current_edge_movement_rate_raw"], edge)
                self.assertIn("native_army_movement_admission", movement)
                self.assertIs(movement["native_army_movement_admission"], admission)
                if admission is not None:
                    self.assertIs(type(movement["native_army_movement_admission"]), bool)
                self.assertIn("first_route_edge_weight_cost_raw", movement)
                self.assertIn("first_edge_arrival_provider_byte_e_u8", movement)
                self.assertEqual(movement["first_route_edge_weight_cost_raw"], cost)
                self.assertIs(type(movement["first_route_edge_weight_cost_raw"]), type(cost))
                self.assertEqual(movement["first_edge_arrival_provider_byte_e_u8"], provider)
                self.assertIs(type(movement["first_edge_arrival_provider_byte_e_u8"]), type(provider))
                self.assertEqual(movement["first_route_edge_remaining_duration"], {"raw": duration, "scale": 100000})
                self.assertEqual(movement["normalized_edge_progress"], {"raw": ratio, "scale": 100000})
                self.assertEqual(row["native_army_resolution_v1"]["raw_reference"],
                                 row["native_carmy_id"])
                sidecar = json.loads(
                    (wire_path.parent / (scene + ".native-context.json")).read_text(encoding="utf-8"))
                self.assertEqual(sidecar["schema"], "xar.unit-first-edge-selection-native-context.v1")
                callbacks = sidecar["callbacks"]
                self.assertEqual(callbacks["native_army_movement_admission"], 1)
                self.assertEqual(callbacks["current_edge_speed"], 0)
                self.assertEqual(callbacks["first_route_edge_weight_cost"], 0 if cost is None else 1)
                self.assertEqual(callbacks["normalized_edge_progress"], 1)
                self.assertEqual(callbacks["first_route_edge_remaining_duration"], 1)
                self.assertEqual(callbacks["native_first_edge_provider_getter"], 0)
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
                        "scene": scene, "route": route, "calls": [], "movement_prefix_returns": [],
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
                        prefix_rows = result[MOVEMENT_PROJECTION]
                        self.assertEqual(len(prefix_rows), 1)
                        prefix = prefix_rows[0]["projection"]
                        provenance = {field: before[field] for field in ("snapshot_id", "revision", "native_revision")}
                        self.assertEqual(prefix_rows[0]["source_provenance"], provenance)
                        self.assertIs(prefix["movement_prefix_input_ready"], True)
                        self.assertEqual(prefix[VALUE], 107)
                        self.assertEqual(prefix["movement_gate"], "native_army_predicate_true")
                        self.assertIs(prefix["movement_add_selected"], True)
                        self.assertEqual(prefix["selected_movement_rate_raw"], 7)
                        self.assertIs(prefix["current_edge_rate_demanded_by_conditional_prefix"], False)
                        for field in MOVEMENT_FALSE_FIELDS:
                            self.assertIs(prefix[field], False)
                        derived = result[PROJECTION]
                        self.assertEqual(len(derived), 1)
                        self.assertEqual(set(derived[0]), {"army_id", "source_provenance", "projection"})
                        self.assertEqual(derived[0]["army_id"], row["army_id"])
                        self.assertEqual(derived[0]["source_provenance"], provenance)
                        projection = derived[0]["projection"]
                        self.assertEqual(projection["source"], "source_conditional_unit_next_first_edge_selection_12004")
                        self.assertEqual(projection["projection_boundary"],
                                         "first_selected_unit_new_date_after_add168_before_arrival_subtraction")
                        self.assertEqual(projection["condition"],
                                         "observed_schedule_receiver_route_and_post_entry_movement_operands_cost_context_provider_held_at_first_edge_selection")
                        self.assertIs(projection["first_edge_selection_input_ready"], selection_ready)
                        self.assertIs(projection["conditional_first_edge_arrival_branch_selected"], selected)
                        self.assertEqual(projection["conditional_post_add_unit_168_raw"], 107)
                        self.assertEqual(projection["first_route_edge_weight_cost_raw"], cost)
                        self.assertEqual(projection["first_edge_arrival_provider_byte_e_u8"], provider)
                        self.assertIs(projection["provider_byte_demanded_by_conditional_first_edge_selection"], provider_demanded)
                        self.assertEqual(projection["unavailable_reason"], expected_reason)
                        self.assertIsNone(projection["selection_bypass"])
                        self.assertEqual(projection["subject_stored_id_positions"], [1, 3])
                        self.assertEqual(projection["unit_route_count_i32"], 2)
                        self.assertIs(projection["scheduled_by_observed_stored_ids"], True)
                        self.assertIs(projection["movement_add_selected"], True)
                        # This is the original current native DAYS value, with no next-day subtraction.
                        self.assertEqual(projection["current_remaining_duration_days_existing"],
                                         movement["first_route_edge_remaining_duration"])
                        self.assertEqual(projection["current_remaining_duration_days_existing"],
                                         {"raw": duration, "scale": 100000})
                        for field in FALSE_FIELDS:
                            self.assertIs(projection[field], False)
                        original_clock = row.get(CLOCK) or {}
                        self.assertIs(prefix["source_derived_full_cdate64_ready"],
                                      original_clock.get("source_derived_full_cdate64_ready", False))
                        if selection_ready and not prefix["source_derived_full_cdate64_ready"]:
                            observed_date_independent_ready = True
                        self.assertEqual(len(observed["movement_prefix_returns"]), 1)
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
                            ("war_contract.py", "_normalize_current_movement_progress"),
                            ("army_current_unit_next_movement_prefix_projection.py",
                             "project_current_unit_next_movement_prefix_v1"),
                            ("army_current_unit_next_first_edge_selection_projection.py",
                             "project_current_unit_next_first_edge_selection_v1"),
                            ("service.py", "_unit_next_movement_projection_rows"),
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
            self.assertTrue(observed_date_independent_ready, "date-independent first-edge selection was not exercised without full clock")
            self.assertEqual(len(receipt["passes"]), 10)
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
