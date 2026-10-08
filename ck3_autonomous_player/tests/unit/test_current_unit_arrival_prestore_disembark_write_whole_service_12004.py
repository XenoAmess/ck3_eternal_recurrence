"""Sole fresh compiled whole-wire consumer for the local disembark-days write.

Only explicit --source-root, --native-wire and --output-dir launch this case.
Hello/paused frame/request association are synthetic; native Army rows and
current Army reader context are preserved from the one compiled producer run.
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

PROJECTION = "current_unit_arrival_prestore_disembark_write_v1"
ARRIVAL = "current_unit_next_arrival_transition_v1"
RAW_FIELDS = (
    "current_province_type_tag_u32", "unit_kind_18_raw_i32",
    "current_province_definition_byte_1b_u8",
    "first_route_target_province_definition_byte_1b_u8",
    "loaded_disembark_penalty_days_rule_i32",
)
SCENES = (
    "disembark_rule_positive", "disembark_rule_zero", "disembark_rule_negative",
    "disembark_rule_unavailable", "disembark_target_medium_zero",
    "disembark_unit_kind_bypass", "disembark_arrival_not_selected",
)
# five observed raw values; conditional call/write/value/ready; raw demand flags
EXPECTED = (
    ((0x50726F76, 0, 0, 1, 34), True, True, 34, True, (True, True, True, True, True)),
    ((0x50726F76, 0, 0, 1, 0), True, True, 0, True, (True, True, True, True, True)),
    ((0x50726F76, 0, 0, 1, -1), True, True, -1, True, (True, True, True, True, True)),
    ((0x50726F76, 0, 0, 1, None), True, True, None, False, (True, True, True, True, True)),
    ((0x50726F76, 0, 0, 0, None), True, False, None, True, (True, True, False, True, False)),
    ((0x50726F76, 1, None, None, None), False, False, None, True, (True, True, False, False, False)),
    ((None, None, None, None, None), False, False, None, True, (False, False, False, False, False)),
)
FALSE_FIELDS = (
    "actual_future_frame_observed", "actual_prestore_callback_executed",
    "actual_fixed_disembark_write_observed", "final_disembark_penalty_reconstructed",
    "final_arrival_reconstructed", "final_helper_current_province_reconstructed",
    "unit30_or_unit160_reconstructed", "recursive_other_unit_arrival_reconstructed",
    "full_unit_new_date_callback_ready", "repeated_callback_effects_reconstructed",
    "battle_contact_supply_day_effects_reconstructed", "native_action_executed",
)
_OPTIONS = None


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def _assert_native_values(case: unittest.TestCase, original: object,
                          observed: object, path: str) -> None:
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
    """Ping acknowledgement and outer request_id correlation only."""

    def __init__(self, scene: str, route: str, whole: dict[str, object]) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_bridge_mcp_unit_disembark_write_" + scene + "_" + route
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


class CurrentUnitArrivalPrestoreDisembarkWriteWholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_loaded_rule_value_reaches_the_conditional_fixed_write_through_registered_routes(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("this sole consumer requires its explicit readonly CLI")
        from xar_autoplayer.bridge import army_current_unit_arrival_prestore_disembark_write_projection as leaf
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
                         project / "src/xar_autoplayer/bridge/army_current_unit_arrival_prestore_disembark_write_projection.py")
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
            "synthetic_boundary": "endpoint hello/paused frame/request_id association only",
            "business_path": "actual NativeHeadlessGameplayDriver -> GameplayBridgeService -> registered MCP",
            "current_context_source": "original ReadArmiesForCharacters12004 current_army_context",
            "projection_boundary": "local conditional Army1D0 fixed write24E2822; held stage inputs and normal returns",
            "full_native_snapshot_pipeline_qualified": False,
            "optional_raw_increments": list(RAW_FIELDS), "passes": [],
        }
        active: dict[str, object] | None = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()
        prefix_key = ("army_current_unit_next_movement_prefix_projection.py",
                      "project_current_unit_next_movement_prefix_v1")
        selection_key = ("army_current_unit_next_first_edge_selection_projection.py",
                         "project_current_unit_next_first_edge_selection_v1")
        arrival_key = ("army_current_unit_next_arrival_transition_projection.py",
                       "project_current_unit_next_arrival_transition_v1")
        write_key = ("army_current_unit_arrival_prestore_disembark_write_projection.py",
                     "project_current_unit_arrival_prestore_disembark_write_v1")
        watched = {
            ("mcp_server.py", "ck3_execute_step"), ("mcp_server.py", "ck3_query_army_strengths"),
            ("service.py", "execute_step"), ("service.py", "query_army_strengths"),
            ("service.py", "_unit_next_movement_projection_rows"),
            ("native_driver.py", "execute_step"), ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("war_contract.py", "_normalize_current_movement_progress"),
            ("war_contract.py", "normalize_armies"),
            ("army_current_disembark_penalty_contract.py", "normalize_current_disembark_penalty_v1"),
            prefix_key, selection_key, arrival_key, write_key,
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
                if key in {selection_key, arrival_key}:
                    self.assertEqual(len(active["prefix_returns"]), 1)
                    self.assertIs(frame.f_locals["movement_prefix"], active["prefix_returns"][0])
                if key == arrival_key:
                    self.assertEqual(len(active["selection_returns"]), 1)
                    self.assertIs(frame.f_locals["first_edge_selection"], active["selection_returns"][0])
                    active["army_context_object"] = frame.f_locals["army_context"]
                if key == write_key:
                    self.assertEqual(len(active["arrival_returns"]), 1)
                    self.assertIs(frame.f_locals["arrival_transition"], active["arrival_returns"][0])
                    self.assertIs(frame.f_locals["army_context"], active["army_context_object"])
            elif event == "return" and key == prefix_key:
                active["prefix_returns"].append(value)
            elif event == "return" and key == selection_key:
                active["selection_returns"].append(value)
            elif event == "return" and key == arrival_key:
                active["arrival_returns"].append(value)
            elif event == "return" and key == write_key:
                active["write_returns"].append(value)
            elif event == "return" and key == ("native_driver.py", "execute_step"):
                active["driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", active["service_function"]):
                active["service_result"] = deepcopy(value)

        try:
            sys.setprofile(observe)
            threading.setprofile(observe)
            for ordinal, (scene, expected) in enumerate(zip(SCENES, EXPECTED), 1):
                raw_values, call, write, value, ready, demanded = expected
                whole = packet["samples"][scene]
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
                self.assertEqual(row["army_id"], 16777217)
                self.assertEqual(row["native_carmy_id"], 33554433)
                self.assertEqual(row["monthly_loss_budget_inputs_v1"]["unit_native_170_raw"], 2)
                self.assertIs(row["monthly_loss_budget_inputs_v1"]["ready"], False)
                self.assertEqual(row["current_unit_new_date_schedule_inputs_v1"]["subject_stored_id_positions"], [1, 3])
                self.assertEqual(row["current_unit_new_date_callback_entry_inputs_v1"]["unit_route_count_i32"], 2)
                movement = row["current_movement_progress"]
                for field, observed in zip(RAW_FIELDS, raw_values):
                    self.assertIn(field, movement)
                    self.assertEqual(movement[field], observed)
                    self.assertIs(type(movement[field]), type(observed))
                self.assertEqual(movement["unit_state_raw"], 6)
                self.assertEqual(movement["accumulated_movement_weight_raw"], 100)
                self.assertEqual(movement["cached_edge_speed_raw"], 7)
                self.assertIs(movement["native_army_movement_admission"], True)
                self.assertEqual(movement["first_route_target_province_type_tag_u32"], 0x50726F76)
                arrival_selected = scene != "disembark_arrival_not_selected"
                cost = 106 if arrival_selected else 107
                duration, ratio = (85714, 94339) if arrival_selected else (100000, 93457)
                self.assertEqual(movement["first_route_edge_weight_cost_raw"], cost)
                self.assertEqual(movement["first_route_edge_remaining_duration"], {"raw": duration, "scale": 100000})
                self.assertEqual(movement["normalized_edge_progress"], {"raw": ratio, "scale": 100000})
                days = row["current_disembark_penalty_v1"]
                self.assertEqual(set(days), {"schema_version", "source", "status", "remaining_days", "unavailable_reason"})
                self.assertEqual(days["schema_version"], 1)
                self.assertEqual(days["source"], "native_current_disembark_penalty_days_12003")
                self.assertEqual(days["status"], "available")
                self.assertIs(type(days["remaining_days"]), int)
                self.assertEqual(days["remaining_days"], 12)
                self.assertIsNone(days["unavailable_reason"])
                sidecar = json.loads((wire_path.parent / (scene + ".native-context.json")).read_text(encoding="utf-8"))
                self.assertEqual(sidecar["schema"], "xar.unit-first-disembark-write-native-context.v1")
                original_armies = sidecar["current_army_context"]
                self.assertEqual(len(original_armies), 1)
                original_army = original_armies[0]
                self.assertEqual(original_army["army_id"], row["army_id"])
                self.assertEqual(original_army["current_province_id"], 1)
                self.assertEqual(original_army["route_province_ids"], [2, 3])
                self.assertEqual(original_army["route_source_count"], 2)
                self.assertEqual(original_army["route_read_status"], "complete_nonempty")
                self.assertEqual(original_army["army_state_code"], 6)
                self.assertEqual(sidecar["current_army_context_producer"],
                                 "ReadArmiesForCharacters12004 -> production ReadArmiesForCharacters")
                self.assertIs(sidecar["full_nativeframe_pipeline_exercised"], False)
                callbacks = sidecar["callbacks"]
                self.assertEqual(callbacks["unit_state"], 2)
                self.assertEqual(callbacks["read_armies_for_characters"], 1)
                self.assertEqual(callbacks["current_disembark_penalty_days"], 1)
                self.assertEqual(callbacks["army_departure_helper"], 0)
                self.assertEqual(callbacks["fixed_disembark_days_writer"], 0)
                self.assertEqual(callbacks["arrival_helper"], 0)
                self.assertEqual(callbacks["first_province_writer"], 0)
                self.assertEqual(callbacks["current_edge_speed"], 0)
                self.assertEqual(callbacks["native_army_movement_admission"], 1)
                self.assertEqual(callbacks["first_route_edge_weight_cost"], 1)
                self.assertEqual(callbacks["normalized_edge_progress"], 1)
                self.assertEqual(callbacks["first_route_edge_remaining_duration"], 1)
                context = sidecar["synthetic_context"]
                self.assertEqual(context["snapshot_id"], "native:1")
                self.assertIs(type(context["native_revision"]), int)
                self.assertEqual(context["native_revision"], 1)
                self.assertEqual(context["actor_character_id"], 29829)
                self.assertEqual(context["date_raw"], 53288448)
                self.assertIs(context["paused"], True)
                self.assertIs(context["map_ready"], True)

                for route in ("ck3_execute_step", "ck3_query_army_strengths"):
                    case_dir = output_dir / scene / route
                    case_dir.mkdir(parents=True, exist_ok=True)
                    endpoint = _CompiledWholeEndpoint(scene, route, whole)
                    driver = None
                    observed: dict[str, object] = {
                        "scene": scene, "route": route, "calls": [],
                        "prefix_returns": [], "selection_returns": [],
                        "arrival_returns": [], "write_returns": [],
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
                                "paused": True, "map_ready": True, "history": [],
                                "active_event": None, "pending_character_interaction": None,
                                "played_character": {"character_id": context["actor_character_id"], "alive": True},
                                "player_armies": deepcopy(original_armies), "active_wars": [],
                            },
                        })
                        before = driver.take_snapshot()
                        observed["before"] = deepcopy(before)
                        self.assertEqual(before["snapshot_id"], "native:1")
                        self.assertEqual(before["native_revision"], context["native_revision"])
                        self.assertIs(type(before["revision"]), int)
                        self.assertGreater(before["revision"], 0)
                        canonical = before["player_armies"][0]
                        for field in (
                            "army_id", "owner_character_id", "controllable", "current_province_id",
                            "route_province_ids", "route_read_status", "route_source_count",
                            "move_target_province_id", "move_target_observable", "army_state_code",
                        ):
                            self.assertEqual(canonical[field], original_army[field])
                        kwargs = {"expected_revision": before["revision"]}
                        if route == "ck3_execute_step":
                            kwargs["step"] = "query-army-strengths-v1"
                        else:
                            kwargs["army_ids"] = [row["army_id"]]
                        registered = await server.call_tool(route, kwargs)
                        self.assertIs(registered.is_error, False)
                        result = registered.structured_content
                        self.assertEqual(result, observed["service_result"])
                        _assert_native_values(self, native, observed["driver_result"], "driver")
                        _assert_native_values(self, native, result, "registered")
                        for field in ("snapshot_id", "revision", "native_revision"):
                            self.assertEqual(result["queried_" + field], before[field])
                        if route == "ck3_query_army_strengths":
                            for field in ("snapshot_id", "revision", "native_revision", "date_raw"):
                                self.assertEqual(result["source"][field], before[field])
                        provenance = {field: before[field] for field in ("snapshot_id", "revision", "native_revision")}
                        arrival_rows = result[ARRIVAL]
                        self.assertEqual(len(arrival_rows), 1)
                        self.assertEqual(arrival_rows[0]["source_provenance"], provenance)
                        arrival = arrival_rows[0]["projection"]
                        self.assertIs(arrival["arrival_transition_input_ready"], True)
                        self.assertIs(arrival["conditional_first_province_assignment_selected"], arrival_selected)
                        self.assertEqual(arrival["conditional_current_province_id_after_first_assignment"],
                                         2 if arrival_selected else 1)
                        self.assertEqual(arrival["conditional_unit_168_raw_after_arrival_subtraction"],
                                         1 if arrival_selected else 107)
                        derived = result[PROJECTION]
                        self.assertEqual(len(derived), 1)
                        self.assertEqual(set(derived[0]), {"army_id", "source_provenance", "projection"})
                        self.assertEqual(derived[0]["army_id"], row["army_id"])
                        self.assertEqual(derived[0]["source_provenance"], provenance)
                        projection = derived[0]["projection"]
                        self.assertEqual(projection["source"], "source_conditional_unit_arrival_prestore_disembark_write_12004")
                        self.assertEqual(projection["projection_boundary"],
                                         "first_selected_arrival_prestore_local_army1d0_fixed_write_24e2822")
                        self.assertIs(projection["fixed_disembark_write_input_ready"], ready)
                        self.assertIs(projection["conditional_prestore_24e23e0_call_selected"], call)
                        self.assertIs(projection["conditional_fixed_disembark_days_write_selected"], write)
                        self.assertEqual(projection["conditional_disembark_days_fixed_write_value_i32"], value)
                        self.assertIs(type(projection["conditional_disembark_days_fixed_write_value_i32"]), type(value))
                        self.assertIs(projection["loaded_days_rule_demanded_by_conditional_fixed_write"], demanded[-1])
                        self.assertEqual(projection["raw_input_demanded_by_conditional_fixed_write"],
                                         dict(zip(RAW_FIELDS, demanded)))
                        for field, raw in zip(RAW_FIELDS, raw_values):
                            self.assertEqual(projection[field], raw)
                            self.assertIs(type(projection[field]), type(raw))
                        self.assertEqual(projection["observed_current_disembark_penalty_existing"], days)
                        self.assertEqual(projection["current_remaining_duration_days_existing"],
                                         movement["first_route_edge_remaining_duration"])
                        self.assertEqual(projection["unavailable_reason"],
                                         None if ready else "loaded_disembark_penalty_days_rule_unavailable")
                        self.assertIs(projection["prior170_or_descriptor1_demanded_by_fixed_write"], False)
                        self.assertIs(projection["native_fleet_validity_demanded_by_fixed_write"], False)
                        self.assertIs(projection["current_remaining_days_readiness_demanded_by_fixed_write"], False)
                        self.assertEqual(projection["descriptor_byte2_caller_constant"], 0)
                        self.assertEqual(projection["current_province_id_existing"], 1)
                        self.assertEqual(projection["current_route_province_ids_existing"], [2, 3])
                        for field in FALSE_FIELDS:
                            self.assertIs(projection[field], False)
                        self.assertEqual(observed["army_context_object"], canonical)
                        for field in ("prefix_returns", "selection_returns", "arrival_returns", "write_returns"):
                            self.assertEqual(len(observed[field]), 1)
                        executed = {(Path(item["source"]).name, item["function"]) for item in observed["calls"]}
                        self.assertTrue({
                            ("mcp_server.py", route), ("service.py", observed["service_function"]),
                            ("service.py", "_unit_next_movement_projection_rows"),
                            ("native_driver.py", "execute_step"),
                            ("native_driver.py", "_execute_army_strength_query"),
                            ("war_contract.py", "_normalize_army_strength_row"),
                            ("war_contract.py", "_normalize_current_movement_progress"),
                            ("war_contract.py", "normalize_armies"),
                            ("army_current_disembark_penalty_contract.py", "normalize_current_disembark_penalty_v1"),
                            prefix_key, selection_key, arrival_key, write_key,
                        } <= executed, executed)
                        commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
                        pings = [item for item in endpoint.requests if item["type"] == "ping"]
                        self.assertEqual(len(commands), 1)
                        self.assertEqual(len(pings), 1)
                        self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
                        self.assertEqual(len(endpoint.delivered), 1)
                        delivered = endpoint.delivered[0]
                        self.assertEqual(delivered["request_id"], commands[0]["request_id"])
                        for key in whole:
                            if key != "request_id":
                                self.assertEqual(delivered[key], whole[key])
                        self.assertEqual(delivered["result"], native)
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
            self.assertEqual(len(receipt["passes"]), 14)
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
