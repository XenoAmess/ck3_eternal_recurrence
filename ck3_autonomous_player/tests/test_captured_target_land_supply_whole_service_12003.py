"""One NOTRUN consumer of new whole native target previews through real APIs.

NativeHeadlessGameplayDriver and GameplayBridgeService remain production code.
Only the endpoint, hello, paused scope/frame and transport request-id are synthetic.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unittest


FAMILY = "captured_target_land_supply_inputs_v1"
NATIVE_CASES = (
    "01-at-sea-target-context",
    "02-ready-false-and-zero",
    "03-independent-component-failure",
    "04-independent-resupply-failure",
    "05-absent-gain-resupply-false",
    "06-absent-gain-resupply-true",
    "07-same-origin-target-copy",
    "08-legacy-omission-native-commander-context",
)
SYNTHETIC_CASES = (
    "09-synthetic-unexpected-key",
    "10-synthetic-bool-as-raw-integer",
    "11-synthetic-signed-width",
    "12-synthetic-readiness-mismatch",
    "13-synthetic-target-id-mismatch",
)
ALL_CASES = NATIVE_CASES + SYNTHETIC_CASES


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sibling(wire: dict[str, object]) -> object:
    return wire["result"]["route_preview"]["province_supply"]["target"].get(FAMILY)


def _assert_preserved(test: unittest.TestCase, expected: object, actual: object,
                      path: str) -> None:
    """Compare native values with exact types; production metadata may be added."""
    test.assertIs(type(actual), type(expected), path)
    if isinstance(expected, dict):
        test.assertTrue(set(expected) <= set(actual), path)
        for key, value in expected.items():
            _assert_preserved(test, value, actual[key], path + "." + key)
    elif isinstance(expected, list):
        test.assertEqual(len(expected), len(actual), path)
        for index, value in enumerate(expected):
            _assert_preserved(test, value, actual[index], f"{path}[{index}]")
    else:
        test.assertEqual(actual, expected, path)


def _expected_family(case: str) -> dict[str, object] | None:
    """Literal fixture expectations only; this never supplies driver input."""
    if case == NATIVE_CASES[7]:
        return None
    component_ready = case != NATIVE_CASES[2]
    resupply_ready = case != NATIVE_CASES[3]
    component_reason = (None if component_ready else
                        "native_target_province_component_output_unavailable")
    resupply_reason = (None if resupply_ready else
                       "native_target_resupply_predicate_unavailable")
    return {
        "source": "native_captured_target_land_supply_inputs",
        "input_basis": "captured_owner_and_target_province",
        "scale": 100000,
        "status": "available" if component_ready and resupply_ready else "partial",
        "subject_army_id": 67108883,
        "subject_carmy_id": 33554443,
        "owner_character_id": 29829,
        "province_id": 470 if case == NATIVE_CASES[6] else 471,
        "native_province_component_applicable": case != NATIVE_CASES[1],
        "province_component_raw": (None if not component_ready else
                                   0 if case == NATIVE_CASES[1] else -612345),
        "native_resupply_eligible": (None if not resupply_ready else
                                     case not in (NATIVE_CASES[1], NATIVE_CASES[4])),
        "loaded_gain_raw": (None if case in (NATIVE_CASES[4], NATIVE_CASES[5]) else
                            0 if case == NATIVE_CASES[1] else 1750000),
        "current_inputs_ready": component_ready and resupply_ready,
        "province_component_observation_ready": component_ready,
        "resupply_observation_ready": resupply_ready,
        "unavailable_reason": component_reason or resupply_reason,
        "province_component_unavailable_reason": component_reason,
        "resupply_unavailable_reason": resupply_reason,
    }


def _malformed_copy(authority: dict[str, object], scene: str) -> dict[str, object]:
    copied = deepcopy(authority)
    family = _sibling(copied)
    if scene == SYNTHETIC_CASES[0]:
        family["synthetic_unexpected_key"] = 0
    elif scene == SYNTHETIC_CASES[1]:
        family["loaded_gain_raw"] = True
    elif scene == SYNTHETIC_CASES[2]:
        family["province_component_raw"] = 1 << 63
    elif scene == SYNTHETIC_CASES[3]:
        family["current_inputs_ready"] = False
    elif scene == SYNTHETIC_CASES[4]:
        family["province_id"] = 472
    else:
        raise ValueError("unknown explicitly synthetic parser scene")
    return copied


def _assert_native_context(test: unittest.TestCase, context: dict[str, object],
                           case: str) -> None:
    """Assert the frozen new fixture's actual callback context, never live ABI."""
    test.assertEqual(context["schema"], "xar.captured-target-land-supply.native-whole-context.v1")
    test.assertEqual(context["case"], case)
    for key in ("synthetic_fixture", "command_envelope_synthetic", "accepted_preview_synthetic",
                "input_memory_unchanged", "original_preview_fields_unchanged"):
        test.assertIs(context[key], True, key)
    for key in ("live_capture", "actual_target_arrival_observed", "actual_callback_observed",
                "full_target_rate_ready", "full_daily_supply_transition_ready", "full_monthly_ready"):
        test.assertIs(context[key], False, key)
    for key in ("supply_mutator_calls", "movement_mutator_calls"):
        test.assertIs(type(context[key]), int, key)
        test.assertEqual(context[key], 0, key)
    test.assertEqual(context["fixture_subject_fleet_association_raw"], 16777217)
    test.assertIs(context["native_commander_fallback_used"], case == NATIVE_CASES[7])
    count_keys = ("legacy_limit", "legacy_usage", "target_component_predicate",
                  "target_component_reader", "target_resupply_predicate", "present_fleet_predicate")
    values = {
        NATIVE_CASES[0]: (2, 2, 1, 1, 1, 0),
        NATIVE_CASES[1]: (2, 2, 1, 0, 1, 0),
        NATIVE_CASES[2]: (2, 2, 1, 1, 1, 0),
        NATIVE_CASES[3]: (2, 2, 1, 1, 0, 0),
        NATIVE_CASES[4]: (2, 2, 1, 1, 1, 0),
        NATIVE_CASES[5]: (2, 2, 1, 1, 1, 0),
        NATIVE_CASES[6]: (1, 1, 1, 1, 1, 0),
        NATIVE_CASES[7]: (2, 2, 0, 0, 0, 0),
    }
    _assert_preserved(test, dict(zip(count_keys, values[case])), context["counts"], "native-counts")
    test.assertEqual(set(context["counts"]), set(count_keys))
    events = context["callbacks"]
    test.assertIs(type(events), list)
    event_counts = dict(zip(NATIVE_CASES, (12, 11, 12, 11, 12, 12, 9, 7)))
    test.assertEqual(len(events), event_counts[case])
    test.assertEqual([event["requested_id"] for event in events if event["callback"] == "resolve_character"],
                     [29829] if case == NATIVE_CASES[7] else [29829, 29830])
    test.assertEqual([event["requested_id"] for event in events if event["callback"] == "resolve_province"],
                     [470, 470] if case == NATIVE_CASES[6] else
                     [470, 471] if case == NATIVE_CASES[7] else [470, 471, 471])
    target = 470 if case == NATIVE_CASES[6] else 471
    for event in events:
        callback = event["callback"]
        if callback in ("province_supply_limit", "province_supply_usage"):
            for key in ("receiver_exact", "owner_exact", "details_null"):
                test.assertIs(event[key], True, callback + "." + key)
            if callback == "province_supply_limit":
                test.assertIs(event["commander_exact"], True)
                test.assertEqual(event["returned_raw"], 1000 if event["province_id"] == 470 else 2345)
            else:
                test.assertEqual(event["mode"], 0)
                test.assertEqual(event["returned_raw"], 321 if event["province_id"] == 470 else 678)
        elif callback == "target_component_predicate":
            test.assertEqual(event["province_id"], target)
            test.assertIs(event["receiver_exact"], True)
            test.assertIs(event["returned_bool"], case != NATIVE_CASES[1])
        elif callback == "target_component_reader":
            test.assertEqual(event["province_id"], target)
            test.assertIs(event["receiver_exact"], True, "receiver is actual target+30")
            test.assertIs(event["details_null"], True)
            test.assertEqual(event["ordinal"], 427)
            test.assertEqual(event["multiplier"], 100000)
            test.assertEqual(event["mode"], 0)
            test.assertEqual(event["returned_raw"], None if case == NATIVE_CASES[2] else -612345)
            test.assertIs(event["returned_null_output"], case == NATIVE_CASES[2])
        elif callback == "target_resupply_predicate":
            test.assertEqual(event["province_id"], target)
            test.assertIs(event["receiver_exact"], True)
            test.assertIs(event["owner_exact"], True)
            test.assertIs(event["returned_bool"], case not in (NATIVE_CASES[1], NATIVE_CASES[4]))


class SyntheticTargetPreviewEndpoint:
    """Offline transport only: publishes the whole native command result unchanged.

    The original native request_id is saved; only that correlation token is rebound
    to the actual production driver's request. No preview field is reconstructed.
    """
    pipe_name = r"\\.\pipe\synthetic-target-land-whole-preview-not-live"

    def __init__(self, wire: dict[str, object], expected_step: str):
        self.wire = deepcopy(wire)
        self.expected_step = expected_step
        self.on_frame = None
        self.requests = []
        self.delivered_frames = []
        self.closed = False

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        if not callable(self.on_frame):
            raise RuntimeError("actual driver did not install frame receiver")
        self.on_frame(deepcopy(frame))

    def send(self, frame):
        self.requests.append(deepcopy(frame))
        if frame.get("type") != "execute_step":
            return
        if frame.get("step") != self.expected_step:
            raise AssertionError("only the existing readonly preview is permitted")
        delivered = deepcopy(self.wire)
        delivered["request_id"] = frame["request_id"]
        self.delivered_frames.append(deepcopy(delivered))
        self.publish(delivered)

    def transport_error(self):
        return None

    def close(self):
        self.closed = True


def _synthetic_frame(preview: dict[str, object]) -> dict[str, object]:
    """Required transport/scope metadata, explicitly synthetic and never live."""
    owner = preview["province_supply"]["owner_character_id"]
    army = {
        "army_id": preview["army_id"], "owner_character_id": owner,
        "soldiers": 160, "current_province_id": preview["origin_province_id"],
        "move_target_province_id": None, "controllable": True,
        "route_province_ids": [], "combat_id": None, "retreating": False,
    }
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": "synthetic-target-preview:40", "revision": 40,
        "state": {
            "phase": "map_hud", "date": "synthetic-not-live", "date_raw": 1000,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": owner, "alive": True},
            "player_armies": [army], "active_wars": [],
        },
    }


class CapturedTargetLandSupplyWholeService12003Tests(unittest.TestCase):
    def test_native_preview_whole_driver_service_preserves_target_inputs_and_rejects_malformed_siblings(self):
        output = Path(os.environ["XAR_TARGET_LAND_OUTPUT_DIR"])
        output.mkdir(parents=True, exist_ok=True)
        compound = {
            "schema": "xar.target-land-whole-service.compound.v1",
            "status": "RED", "readiness": "research", "live": False,
            "source_commit": os.environ.get("XAR_TARGET_LAND_SOURCE_COMMIT"),
            "sole_method": self._testMethodName, "scenes": [],
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "synthetic_boundary": "Endpoint, hello, paused frame/player scope and command-result request_id only; malformed scenes are separately labelled synthetic copies.",
            "actual_disembark_observed": False, "full_target_rate_ready": False,
            "actual_after": False, "full_monthly_ready": False,
            "game_process_sdk_operations": 0, "old_first_replays": 0,
        }
        started = time.perf_counter()
        had_failure = False
        try:
            self.assertEqual(sys.flags.optimize, 0, "FIRST requires no -O")
            self.assertTrue(compound["source_commit"], "Root supplies adopted source metadata")
            supplied_root = Path(os.environ["XAR_TARGET_LAND_SOURCE_ROOT"])
            source = (supplied_root / "ck3_autonomous_player"
                      if (supplied_root / "ck3_autonomous_player").is_dir()
                      else supplied_root)
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir(),
                            "use the complete adopted source root")
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # These project imports execute only when Root runs this new method.
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.version_identity import CK3_12003
            from xar_autoplayer.bridge.war_contract import preview_move_army_step

            compound["source_root"] = source.as_posix()
            compound["driver_module"] = sys.modules[NativeHeadlessGameplayDriver.__module__].__file__
            compound["service_module"] = sys.modules[GameplayBridgeService.__module__].__file__
            wire_dir = Path(os.environ["XAR_TARGET_LAND_WIRE_DIR"])
            selector = os.environ.get("XAR_TARGET_LAND_CASES")
            scenes = ALL_CASES if selector is None else tuple(selector.split(","))
            self.assertTrue(scenes, "resume selection must not be empty")
            self.assertEqual(len(scenes), len(set(scenes)), "no duplicate scene replay")
            self.assertTrue(set(scenes) <= set(ALL_CASES), "exact new scene names only")
            compound["selected_scenes"] = list(scenes)
            compound["native_case_count"] = sum(scene in NATIVE_CASES for scene in scenes)
            compound["synthetic_parser_case_count"] = sum(scene in SYNTHETIC_CASES for scene in scenes)

            for scene in scenes:
                with self.subTest(scene=scene):
                    case_dir = output / scene
                    case_dir.mkdir(parents=True, exist_ok=True)
                    case_started = time.perf_counter()
                    receipt = {
                        "schema": "xar.target-land-whole-service.scene.v1",
                        "scene": scene, "status": "RED", "live": False,
                        "synthetic_parser_copy": scene in SYNTHETIC_CASES,
                        "authority_native_case": NATIVE_CASES[0] if scene in SYNTHETIC_CASES else scene,
                        "source_commit": compound["source_commit"],
                        "actual_driver_class": "NativeHeadlessGameplayDriver",
                        "actual_service_class": "GameplayBridgeService",
                        "actual_driver_result": None, "actual_service_result": None,
                        "actual_exception": None, "call_trace": [],
                        "actual_disembark_observed": False,
                        "full_target_rate_ready": False, "actual_after": False,
                        "full_monthly_ready": False,
                    }
                    endpoint = None
                    driver = None
                    previous_profile = sys.getprofile()
                    try:
                        authority_case = receipt["authority_native_case"]
                        native_path = wire_dir / (authority_case + ".json")
                        native_bytes = native_path.read_bytes()
                        (case_dir / "authority-native-whole.json").write_bytes(native_bytes)
                        authority = json.loads(native_bytes.decode("utf-8-sig"))
                        self.assertIs(type(authority), dict)
                        self.assertEqual(authority["type"], "command_result")
                        self.assertEqual(authority["protocol_version"], 1)
                        self.assertIs(authority["ok"], True)
                        self.assertIs(type(authority["request_id"]), str)
                        sidecar_path = wire_dir / (authority_case + "-native-context.json")
                        sidecar_bytes = sidecar_path.read_bytes()
                        (case_dir / "authority-native-context.json").write_bytes(sidecar_bytes)
                        native_context = json.loads(sidecar_bytes.decode("utf-8-sig"))
                        receipt["native_context"] = native_context
                        _assert_native_context(self, native_context, authority_case)
                        receipt["authority_native_path"] = native_path.as_posix()
                        receipt["authority_native_byte_count"] = len(native_bytes)
                        before_authority = deepcopy(authority)
                        authority_preview = authority["result"]["route_preview"]
                        self.assertEqual(authority_preview["army_id"], 67108883)
                        self.assertEqual(authority_preview["origin_province_id"], 470)
                        expected_target = 470 if authority_case == NATIVE_CASES[6] else 471
                        self.assertEqual(authority_preview["target_province_id"], expected_target)
                        self.assertEqual(authority_preview["route_province_ids"],
                                         [470] if authority_case == NATIVE_CASES[6] else [470, 471])
                        supply = authority_preview["province_supply"]
                        self.assertEqual(supply["status"], "available")
                        self.assertIsNone(supply["unavailable_reason"])
                        self.assertEqual(supply["native_carmy_id"], 33554443)
                        self.assertEqual(supply["owner_character_id"], 29829)
                        self.assertEqual(supply["commander_character_id"],
                                         None if authority_case == NATIVE_CASES[7] else 29830)
                        self.assertNotIn(FAMILY, supply["current"])
                        for role, expected_id, limit, usage in (
                            ("current", 470, 1000, 321),
                            ("target", expected_target,
                             1000 if expected_target == 470 else 2345,
                             321 if expected_target == 470 else 678),
                        ):
                            row = supply[role]
                            self.assertEqual(row["role"], role)
                            self.assertEqual(row["province_id"], expected_id)
                            self.assertEqual(row["status"], "available")
                            self.assertIsNone(row["unavailable_reason"])
                            self.assertEqual(row["scale"], 1)
                            self.assertIs(type(row["native_supply_limit_soldiers"]), int)
                            self.assertIs(type(row["native_supply_usage_soldiers"]), int)
                            self.assertEqual(row["native_supply_limit_soldiers"], limit)
                            self.assertEqual(row["native_supply_usage_soldiers"], usage)
                        expected_family = _expected_family(authority_case)
                        if expected_family is None:
                            self.assertNotIn(FAMILY, supply["target"], "legacy omission is not null")
                        else:
                            self.assertEqual(set(_sibling(authority)), set(expected_family))
                            _assert_preserved(self, expected_family, _sibling(authority), "native-family")
                        _write_json(case_dir / "authority-raw-sibling.json", _sibling(authority))
                        wire = (_malformed_copy(authority, scene)
                                if scene in SYNTHETIC_CASES else deepcopy(authority))
                        _write_json(case_dir / "submitted-whole.json", wire)
                        _write_json(case_dir / "submitted-raw-sibling.json", _sibling(wire))
                        receipt["malformed_source"] = ("Explicitly synthetic copy of new 01 authority; only new sibling altered"
                                                       if scene in SYNTHETIC_CASES else None)
                        preview = wire["result"]["route_preview"]
                        step = preview_move_army_step(preview["army_id"], preview["target_province_id"])
                        self.assertEqual(wire["result"]["step"], step)
                        self.assertIs(wire["result"]["accepted"], True)
                        self.assertEqual(wire["result"]["status"], "available")
                        endpoint = SyntheticTargetPreviewEndpoint(wire, step)
                        driver = NativeHeadlessGameplayDriver(
                            endpoint.pipe_name, endpoint=endpoint,
                            command_timeout_seconds=1.0,
                            episode_projection="native_campaign",
                        )
                        service = GameplayBridgeService(driver)
                        self.assertIs(type(driver), NativeHeadlessGameplayDriver)
                        self.assertIs(service.driver, driver)
                        hello = {
                            "type": "hello", "protocol_version": 1,
                            "bridge_version": "0.1.0", "pid": 4242,
                            "session_generation": 0,
                            "expected_ck3_version": CK3_12003.game_version,
                            "expected_ck3_sha256": CK3_12003.executable_sha256,
                            "capabilities": ["game.state.snapshot", "game.state.army-routes",
                                             "game.command.preview-move-army-N-to-N"],
                        }
                        frame = _synthetic_frame(preview)
                        _write_json(case_dir / "synthetic-hello.json", hello)
                        _write_json(case_dir / "synthetic-paused-scope-frame.json", frame)
                        endpoint.publish(hello)
                        endpoint.publish(frame)
                        before = driver.take_internal_semantic_snapshot()
                        receipt["before_synthetic_frame"] = deepcopy(before)

                        interesting = {
                            ("service.py", "execute_step"),
                            ("native_driver.py", "execute_step"),
                            ("native_driver.py", "_execute_step_unrecorded"),
                            ("native_driver.py", "_execute_native_war_step"),
                            ("native_driver.py", "_execute_primitive_step"),
                            ("native_driver.py", "ingest"),
                            ("army_captured_target_land_supply_inputs_contract.py",
                             "normalize_target_land_supply_in_route_preview"),
                            ("army_captured_target_land_supply_inputs_contract.py",
                             "normalize_captured_target_land_supply_inputs_v1"),
                        }

                        def observe_call(frame_object, event, argument):
                            key = (Path(frame_object.f_code.co_filename).name,
                                   frame_object.f_code.co_name)
                            if key not in interesting:
                                return
                            if event == "call":
                                receipt["call_trace"].append({
                                    "source": frame_object.f_code.co_filename,
                                    "function": key[1],
                                })
                            elif event == "return" and key == ("native_driver.py", "execute_step"):
                                receipt["actual_driver_result"] = deepcopy(argument)
                            elif event == "return" and key == ("service.py", "execute_step"):
                                receipt["actual_service_result"] = deepcopy(argument)

                        sys.setprofile(observe_call)
                        if scene in SYNTHETIC_CASES:
                            with self.assertRaisesRegex(
                                BridgeUnavailableError,
                                "native target Province supply inputs are malformed",
                            ) as captured:
                                service.execute_step(step, expected_revision=before["revision"])
                            receipt["actual_exception"] = {
                                "type": type(captured.exception).__name__,
                                "message": str(captured.exception),
                                "expected_new_sibling_rejection": True,
                            }
                        else:
                            observed = service.execute_step(step, expected_revision=before["revision"])
                            _assert_preserved(self, wire["result"], observed, "whole-native-result")
                            self.assertEqual(receipt["actual_driver_result"], observed)
                            self.assertEqual(receipt["actual_service_result"], observed)
                            observed_preview = observed["route_preview"]
                            self.assertEqual(observed_preview["previewed_date_raw"], 1000)
                            self.assertEqual(observed["queried_snapshot_id"], before["snapshot_id"])
                            self.assertEqual(observed["queried_revision"], before["revision"])
                            self.assertEqual(observed["queried_native_revision"], before["native_revision"])
                            self.assertEqual(observed["queried_connection_generation"],
                                             before["diagnostics"]["connection_generation"])
                            returned_family = observed_preview["province_supply"]["target"].get(FAMILY)
                            receipt["returned_raw_sibling"] = deepcopy(returned_family)
                            if expected_family is None:
                                self.assertNotIn(FAMILY, observed_preview["province_supply"]["target"])
                            else:
                                self.assertEqual(set(returned_family), set(expected_family))
                                _assert_preserved(self, _sibling(wire), returned_family, "returned-family")
                                for absent_claim in ("actual_after", "actual_disembark_observed",
                                                     "full_target_rate_ready", "full_monthly_ready"):
                                    self.assertNotIn(absent_claim, returned_family)
                            _write_json(case_dir / "returned-raw-sibling.json", returned_family)
                        sys.setprofile(previous_profile)
                        after = driver.take_internal_semantic_snapshot()
                        receipt["after_synthetic_frame"] = deepcopy(after)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                                    "paused", "player_armies", "played_character"):
                            _assert_preserved(self, before[key], after[key], "same-frame." + key)
                        requests = [request for request in endpoint.requests
                                    if request.get("type") == "execute_step"]
                        self.assertEqual(len(requests), 1, "one new preview call, no retry")
                        self.assertEqual(requests[0]["step"], step)
                        self.assertEqual(requests[0]["expected_revision"], 40)
                        self.assertEqual(len(endpoint.delivered_frames), 1)
                        delivered = endpoint.delivered_frames[0]
                        self.assertEqual(delivered["request_id"], requests[0]["request_id"])
                        for key in wire:
                            if key != "request_id":
                                _assert_preserved(self, wire[key], delivered[key], "transport." + key)
                        executed = {(Path(item["source"]).name, item["function"])
                                    for item in receipt["call_trace"]}
                        required = interesting - {
                            ("army_captured_target_land_supply_inputs_contract.py",
                             "normalize_captured_target_land_supply_inputs_v1")}
                        self.assertTrue(required <= executed, "actual driver/service/receiver/preview hook ran")
                        if authority_case != NATIVE_CASES[7]:
                            self.assertIn(("army_captured_target_land_supply_inputs_contract.py",
                                           "normalize_captured_target_land_supply_inputs_v1"), executed)
                        self.assertEqual(authority, before_authority, "native authority never mutated")
                        receipt["status"] = "GREEN"
                    except Exception as error:
                        had_failure = True
                        receipt["actual_exception"] = {
                            "type": type(error).__name__, "message": str(error),
                            "expected_new_sibling_rejection": False,
                        }
                        receipt["traceback"] = traceback.format_exc()
                        raise
                    finally:
                        sys.setprofile(previous_profile)
                        cleanup_error = None
                        if endpoint is not None:
                            receipt["execute_step_requests"] = deepcopy(endpoint.requests)
                            receipt["delivered_whole_frames"] = deepcopy(endpoint.delivered_frames)
                        if driver is not None:
                            try:
                                driver.close()
                            except Exception as error:
                                cleanup_error = error
                                had_failure = True
                                receipt["status"] = "RED"
                                receipt["cleanup_exception"] = {
                                    "type": type(error).__name__, "message": str(error),
                                }
                        receipt["elapsed_seconds"] = time.perf_counter() - case_started
                        receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
                        _write_json(case_dir / "scene-receipt.json", receipt)
                        _write_json(case_dir / "actual-driver-result.json", receipt["actual_driver_result"])
                        _write_json(case_dir / "actual-service-result.json", receipt["actual_service_result"])
                        compound["scenes"].append({
                            "scene": scene, "status": receipt["status"],
                            "synthetic_parser_copy": receipt["synthetic_parser_copy"],
                            "receipt": (case_dir / "scene-receipt.json").as_posix(),
                            "actual_exception": receipt["actual_exception"],
                            "elapsed_seconds": receipt["elapsed_seconds"],
                        })
                        _write_json(output / "service-compound-receipt.json", compound)
                        if cleanup_error is not None:
                            raise cleanup_error
            if not had_failure:
                compound["status"] = "GREEN"
                compound["readiness"] = "Selected new fixture checks passed; Root owns combined native/consumer qualification"
                compound["complete_new_protocol"] = set(scenes) == set(ALL_CASES)
        except Exception as error:
            compound["setup_exception"] = {"type": type(error).__name__, "message": str(error)}
            compound["traceback"] = traceback.format_exc()
            raise
        finally:
            compound["elapsed_seconds"] = time.perf_counter() - started
            compound["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            compound["passed_scenes"] = [item["scene"] for item in compound["scenes"] if item["status"] == "GREEN"]
            compound["failed_scenes"] = [item["scene"] for item in compound["scenes"] if item["status"] != "GREEN"]
            _write_json(output / "service-compound-receipt.json", compound)


if __name__ == "__main__":
    unittest.main()
