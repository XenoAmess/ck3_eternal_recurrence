"""One new registered Army response regression using a retained native whole.

The native producer is not rerun. Only hello, paused transport frame and outer
request correlation are synthetic; the selected compiled result is unchanged.
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


SCENE = "arrival_distinct_province"
RISK = "current_callback_supply_risk_v1"
EFFECTS = "current_callback_soldier_effects_v1"
UNIT_PROJECTIONS = (
    "current_unit_new_date_entry_normalization_v1",
    "current_unit_next_movement_prefix_v1",
    "current_unit_next_first_edge_selection_v1",
    "current_unit_next_arrival_transition_v1",
)
FALSE_BOUNDARIES = (
    "actual_callback_observed", "actual_loss",
    "earlier_stage_outputs_reconstructed", "future_callback_selection_ready",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
_OPTIONS = None


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def _assert_native_values(case: unittest.TestCase, original: object,
                          observed: object, path: str) -> None:
    """Production enrichment preserves every native value, type and row order."""
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


class _RetainedNativeWholeEndpoint:
    def __init__(self, route: str, whole: dict[str, object]) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_bridge_mcp_normal_army_callbacks_" + route
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
            raise AssertionError("production driver did not start endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        self.requests.append(deepcopy(frame))
        if frame.get("type") == "ping":
            self.publish({"type": "pong", "protocol_version": 1,
                          "request_id": frame["request_id"]})
            return
        if (frame.get("type") != "execute_step"
                or frame.get("step") != "query-army-strengths-v1"):
            raise AssertionError("unexpected transport request: " + str(frame))
        delivered = deepcopy(self.whole)
        delivered["request_id"] = frame["request_id"]
        self.delivered.append(deepcopy(delivered))
        self.publish(delivered)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class ArmyNormalTurnCallbackServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_ordinary_army_query_preserves_native_rows_and_direct_callback_parity(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("this sole compound requires its explicit readonly CLI")
        from xar_autoplayer.bridge import service as service_module
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

        source_root = _OPTIONS.source_root.resolve()
        project = source_root / "ck3_autonomous_player"
        self.assertEqual(Path(service_module.__file__).resolve(),
                         project / "src/xar_autoplayer/bridge/service.py")
        wire_path = _OPTIONS.native_wire.resolve()
        output_dir = _OPTIONS.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        packet = json.loads(wire_path.read_text(encoding="utf-8-sig"))
        whole = packet["samples"][SCENE]
        self.assertEqual(whole["type"], "command_result")
        self.assertIs(whole["ok"], True)
        native = whole["result"]
        self.assertEqual(native["step"], "query-army-strengths-v1")
        self.assertIs(native["accepted"], True)
        self.assertEqual(len(native["army_strengths"]), 1)
        sidecar_path = wire_path.parent / (SCENE + ".native-context.json")
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
        self.assertEqual(sidecar["current_army_context_producer"],
                         "ReadArmiesForCharacters12004 -> production ReadArmiesForCharacters")
        context = sidecar["synthetic_context"]
        original_armies = sidecar["current_army_context"]
        ids = [row["army_id"] for row in native["army_strengths"]]
        self.assertEqual([row["army_id"] for row in original_armies], ids)
        receipt: dict[str, object] = {
            "date": "2026-10-09", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(source_root), "native_wire": str(wire_path),
            "native_context": str(sidecar_path), "selected_saved_scene": SCENE,
            "new_compounds": 1, "native_producer_reexecution": 0,
            "native_business_body_rewrites": 0,
            "synthetic_boundary": "hello/paused transport frame/request_id correlation",
            "business_path": "registered MCP -> real Service -> real NativeHeadlessGameplayDriver",
            "full_native_snapshot_pipeline_qualified": False,
            "planner_counterpolicy_changed": False,
            "callback_projections_enter_driver_cache": False,
            "passes": [],
        }
        risk_code = service_module.project_current_callback_supply_risk_v1.__code__
        effects_code = service_module.project_current_callback_soldier_effects_v1.__code__
        driver_code = NativeHeadlessGameplayDriver._execute_army_strength_query.__code__
        service_codes = {
            service_module.GameplayBridgeService.execute_step.__code__: "execute_step",
            service_module.GameplayBridgeService.query_army_strengths.__code__: "query_army_strengths",
        }
        active = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()

        def profile(frame, event, value):
            if active is None:
                return
            code = frame.f_code
            if event == "return":
                if code is risk_code:
                    active["projection_order"].append("risk")
                    active["risk_return_objects"].append(value)
                elif code is effects_code:
                    active["projection_order"].append("effects")
                    active["effects_risk_inputs"].append(frame.f_locals["callback_risk"])
                elif code is driver_code:
                    active["driver_result"] = value
                elif code in service_codes:
                    active["service_function"] = service_codes[code]
                    active["service_result"] = value

        sys.setprofile(profile)
        threading.setprofile(profile)
        projections = []
        try:
            for route in ("ck3_execute_step", "ck3_query_army_strengths"):
                case_dir = output_dir / route
                case_dir.mkdir(parents=True, exist_ok=True)
                endpoint = _RetainedNativeWholeEndpoint(route, whole)
                driver = None
                observed = {"projection_order": [], "risk_return_objects": [],
                            "effects_risk_inputs": []}
                active = observed
                try:
                    driver = NativeHeadlessGameplayDriver(
                        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                        state_dir=case_dir / "driver-state", episode_projection="native_campaign")
                    server = create_server(driver)
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
                            "date_raw": context["date_raw"], "speed": 1, "paused": True,
                            "map_ready": True, "history": [], "active_event": None,
                            "pending_character_interaction": None,
                            "played_character": {"character_id": context["actor_character_id"], "alive": True},
                            "player_armies": deepcopy(original_armies), "active_wars": [],
                        },
                    })
                    before = driver.take_snapshot()
                    self.assertEqual(before["snapshot_id"], context["snapshot_id"])
                    self.assertEqual(before["native_revision"], context["native_revision"])
                    self.assertIs(type(before["revision"]), int)
                    kwargs = {"expected_revision": before["revision"]}
                    if route == "ck3_execute_step":
                        kwargs["step"] = "query-army-strengths-v1"
                    else:
                        kwargs["army_ids"] = ids
                    registered = await server.call_tool(route, kwargs)
                    _write_json(case_dir / "actual-registered-response.json",
                                registered.model_dump(mode="json", by_alias=True))
                    _write_json(case_dir / "actual-delivered-command-results.json", endpoint.delivered)
                    self.assertIs(registered.is_error, False)
                    result = registered.structured_content
                    self.assertEqual(result, observed["service_result"])
                    self.assertEqual(observed["service_function"],
                                     "execute_step" if route == "ck3_execute_step" else "query_army_strengths")
                    _assert_native_values(self, native, observed["driver_result"], "driver")
                    _assert_native_values(self, native, result, "registered")
                    for field in ("snapshot_id", "revision", "native_revision"):
                        self.assertEqual(result["queried_" + field], before[field])
                    self.assertEqual(observed["projection_order"], ["risk", "effects"])
                    self.assertEqual(len(observed["risk_return_objects"]), 1)
                    self.assertIs(observed["effects_risk_inputs"][0], observed["risk_return_objects"][0])
                    self.assertNotIn(RISK, observed["driver_result"])
                    self.assertNotIn(EFFECTS, observed["driver_result"])
                    for key in UNIT_PROJECTIONS:
                        self.assertIn(key, result)
                    for key in (RISK, EFFECTS):
                        self.assertEqual([row["army_id"] for row in result[key]], ids)
                        self.assertEqual(set(result[key][0]), {"army_id", "projection"})
                    risk = result[RISK][0]["projection"]
                    effects = result[EFFECTS][0]["projection"]
                    original = native["army_strengths"][0]
                    for field in ("supply_raw", "supply_capacity_raw", "supply_change_monthly_raw", "attrition_fraction_raw"):
                        self.assertEqual(risk["observed_current_" + field], original["current_" + field])
                    self.assertEqual(effects["observed_current_soldiers"], original["current_soldiers"])
                    self.assertEqual(risk["status"], "partial")
                    self.assertIs(risk["ready"], False)
                    self.assertIsNone(risk["conditional_callback_admitted"])
                    self.assertIn("native_unit_in_combat", risk["missing_inputs"])
                    self.assertIs(effects["ready"], False)
                    self.assertIn("conditional_current_callback_supply_budget", effects["missing_inputs"])
                    for projection in (risk, effects):
                        for field in FALSE_BOUNDARIES:
                            self.assertIs(projection[field], False)
                        self.assertIsNone(projection["actual_post_stage_current"])
                    self.assertIs(risk["actual_supply_update_observed"], False)
                    self.assertIs(risk["future_date_or_day_derived"], False)
                    projections.append({RISK: deepcopy(result[RISK]), EFFECTS: deepcopy(result[EFFECTS])})
                    current_frame = driver.take_snapshot()
                    # native_campaign keeps the public semantic frame unchanged;
                    # the Driver owns the validated query cache separately.
                    cached = driver._army_strength_cache_for_snapshot(
                        current_frame, episode_run_id=current_frame.get("episode_run_id"))
                    self.assertIsInstance(cached, dict)
                    self.assertEqual(cached["army_strengths"], observed["driver_result"]["army_strengths"])
                    self.assertEqual(cached["query_sequence"], native["query_sequence"])
                    for field in ("snapshot_id", "revision", "native_revision"):
                        self.assertEqual(cached["queried_" + field], current_frame[field])
                    self.assertNotIn(RISK, cached)
                    self.assertNotIn(EFFECTS, cached)
                    commands = [request for request in endpoint.requests if request["type"] == "execute_step"]
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
                    self.assertEqual(len(endpoint.delivered), 1)
                    delivered = endpoint.delivered[0]
                    for key in whole:
                        if key != "request_id":
                            self.assertEqual(delivered[key], whole[key])
                    self.assertEqual(delivered["request_id"], commands[0]["request_id"])
                    receipt["passes"].append({
                        "route": route, "service_function": observed["service_function"],
                        "queried_snapshot_id": result["queried_snapshot_id"],
                        "queried_revision": result["queried_revision"],
                        "queried_native_revision": result["queried_native_revision"],
                        "query_sequence": result["query_sequence"], "native_requests": len(commands),
                        "projection_order": observed["projection_order"],
                        "native_business_body_preserved": True,
                        "risk_status": risk["status"], "risk_ready": risk["ready"],
                        "effects_status": effects["status"], "effects_ready": effects["ready"],
                        "risk_missing_inputs": risk["missing_inputs"],
                        "effects_missing_inputs": effects["missing_inputs"],
                    })
                finally:
                    active = None
                    if driver is not None:
                        driver.close()
            self.assertEqual(projections[0], projections[1])
            receipt["normal_direct_callback_parity"] = True
            receipt["status"] = "GREEN"
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            active = None
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            _write_json(output_dir / "COMPOUND-RECEIPT.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    _OPTIONS = parser.parse_args()
    sys.path.insert(0, str(_OPTIONS.source_root.resolve() / "ck3_autonomous_player/src"))
    unittest.main(argv=[sys.argv[0]], verbosity=2)
