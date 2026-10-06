"""SOURCE_PREPARED / NOTRUN: fresh actual4 Faction whole wires to real consumers.

Only the transport, paused frame and request correlation are synthetic. The
native whole command_result remains authoritative and is saved byte-for-byte.
Root alone runs this separately named sole Service method after source adoption.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
import unittest


METHOD = "test_fresh_native_whole_faction_alerts_keep_exact_12004_service_contract"
SCENES = (
    ("known-empty", "alerts-known-empty.command-result.json"),
    ("character-member", "alerts-character-member.command-result.json"),
    ("county-member", "alerts-county-member.command-result.json"),
    ("unavailable", "alerts-unavailable.command-result.json"),
)
CONFIG: argparse.Namespace | None = None


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


class SyntheticFaction12004Endpoint:
    """Offline frame transport only; no handwritten native result or rows."""
    pipe_name = r"\\.\pipe\synthetic-faction-adopted-12004-whole-not-live"

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
        if frame.get("step") != "query-player-faction-alerts-v1":
            raise AssertionError("this fixture supplies the existing readonly alerts query")
        delivered = deepcopy(self.whole_wire)
        # Production request correlation is runtime transport metadata. Native
        # result, schema, readiness, numeric fields and provenance are unchanged.
        delivered["request_id"] = frame["request_id"]
        self.delivered_frames.append(deepcopy(delivered))
        self.publish(delivered)

    def transport_error(self):
        return None

    def close(self):
        pass


def _synthetic_paused_frame(native_result: dict[str, object]) -> dict[str, object]:
    raw = native_result["player_faction_alerts"]
    # Common native revision/date/actor are supplied by the actual serialized
    # frame; an unavailable actor/date uses the explicit synthetic fixture scope.
    date_raw = raw["date_raw"] if raw["date_raw"] is not None else 1000
    actor_id = raw["player_character_id"] if raw["player_character_id"] is not None else 50331649
    revision = native_result["snapshot_revision"]
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": f"synthetic-faction-12004:{revision}", "revision": revision,
        "state": {
            "phase": "map_hud", "date": "synthetic-not-live", "date_raw": date_raw,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": actor_id, "alive": True},
            "player_armies": [], "active_wars": [],
        },
    }


class FactionAdoptedWholeService12004Tests(unittest.TestCase):
    def test_fresh_native_whole_faction_alerts_keep_exact_12004_service_contract(self):
        self.assertIsNotNone(CONFIG, "Root supplies the separately named CLI inputs")
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        had_failure = False
        compound = {
            "schema": "xar.faction-adopted-12004.whole-service.compound.v1",
            "status": "RED", "qualification": "fresh offline fixture only", "live": False,
            "source_commit": CONFIG.source_commit, "sole_method": self._testMethodName,
            "scenes": [], "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "registered_alerts_route": "ck3_query_player_faction_alerts_v1",
            "native_source_proof_doc": "docs/ck3-native-ai/ck3-1.20.0.4-faction-adopted-native.md",
            "synthetic_boundary": "Native fixture memory/callbacks; endpoint, exact4 hello, paused frame and request_id correlation only. Whole native result fields are not replaced.",
            "native_EXE_ABI_proof_from_test": False,
            "actual_gift_submitted": False, "actual_faction_transition_observed": False,
            "exact_ultimatum_timing_ready": False,
            "gift_private_routes_executed": [], "old_GREEN_replays": 0,
            "game_process_SDK_operations": 0,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0, "Root's sole run uses no -O")
            self.assertTrue(CONFIG.source_commit, "Root supplies the actual adopted source commit")
            supplied_root = Path(CONFIG.source_root)
            source = (supplied_root / "ck3_autonomous_player"
                      if (supplied_root / "ck3_autonomous_player").is_dir()
                      else supplied_root)
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir(),
                            "supply the complete adopted project source root")
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # These production imports occur only in Root's future authorized run.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.player_faction_alerts_contract import (
                QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY,
                QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
            )

            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            compound["source_root"] = source.as_posix()
            compound["native_wire_dir"] = Path(CONFIG.native_wire_dir).as_posix()
            for name, cls in (("driver_module", NativeHeadlessGameplayDriver),
                              ("service_module", GameplayBridgeService)):
                module_file = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(module_file.is_relative_to((source / "src").resolve()))
                compound[name] = module_file.as_posix()

            for case, filename in SCENES:
                with self.subTest(case=case):
                    case_dir = output / case
                    case_dir.mkdir(parents=True, exist_ok=True)
                    case_started = time.perf_counter()
                    previous_profile = sys.getprofile()
                    endpoint = None
                    driver = None
                    receipt = {
                        "schema": "xar.faction-adopted-12004.whole-service.scene.v1",
                        "case": case, "status": "RED", "live": False,
                        "native_wire_path": (Path(CONFIG.native_wire_dir) / filename).as_posix(),
                        "source_commit": CONFIG.source_commit,
                        "native_result": None, "actual_driver_result": None,
                        "actual_service_result": None, "actual_exception": None,
                        "call_trace": [], "exact_ultimatum_timing_ready": False,
                    }
                    try:
                        wire_path = Path(CONFIG.native_wire_dir) / filename
                        original_bytes = wire_path.read_bytes()
                        (case_dir / "authority-native-whole.json").write_bytes(original_bytes)
                        wire = json.loads(original_bytes)
                        authority = deepcopy(wire)
                        self.assertEqual(wire["type"], "command_result")
                        self.assertEqual(wire["protocol_version"], 1)
                        self.assertIs(wire["ok"], True)
                        native = wire["result"]
                        receipt["native_result"] = deepcopy(native)
                        self.assertEqual(set(native), {
                            "step", "accepted", "status", "query_sequence",
                            "snapshot_revision", "player_faction_alerts",
                            "player_faction_alerts_ready", "backend_id"})
                        self.assertEqual(native["step"], QUERY_PLAYER_FACTION_ALERTS_V1_STEP)
                        self.assertIs(native["accepted"], True)
                        self.assertEqual(native["backend_id"], "native-headless")
                        self.assertIs(type(native["query_sequence"]), int)
                        self.assertGreater(native["query_sequence"], 0)
                        self.assertLessEqual(native["query_sequence"], 2**64 - 1)
                        self.assertEqual(native["query_sequence"], tuple(case_name for case_name, _ in SCENES).index(case) + 1)
                        self.assertIs(type(native["snapshot_revision"]), int)
                        self.assertGreater(native["snapshot_revision"], 0)
                        self.assertLessEqual(native["snapshot_revision"], 2**64 - 1)
                        self.assertEqual(native["snapshot_revision"], 1)
                        raw = native["player_faction_alerts"]
                        self.assertIs(type(raw["schema_version"]), int)
                        self.assertEqual(raw["schema_version"], 1)
                        self.assertEqual(raw["snapshot_revision"], native["snapshot_revision"])
                        self.assertEqual(raw["provenance"]["game_version"], CK3_12004.game_version)
                        self.assertEqual(raw["provenance"]["executable_sha256"], CK3_12004.executable_sha256)
                        self.assertIs(raw["readiness"]["exact_ultimatum_timing_ready"], False)
                        self.assertIs(raw["planner_projection"]["exact_ultimatum_timing_ready"], False)
                        _write_json(case_dir / "authority-raw-sibling.json", raw)

                        endpoint = SyntheticFaction12004Endpoint(wire)
                        driver = NativeHeadlessGameplayDriver(
                            endpoint.pipe_name, endpoint=endpoint,
                            command_timeout_seconds=1.0, episode_projection="native_campaign")
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
                            "capabilities": ["game.state.snapshot", QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY],
                        }
                        paused_frame = _synthetic_paused_frame(native)
                        _write_json(case_dir / "synthetic-hello.json", hello)
                        _write_json(case_dir / "synthetic-paused-frame.json", paused_frame)
                        endpoint.publish(hello)
                        endpoint.publish(paused_frame)
                        before = driver.take_snapshot()
                        receipt["before_synthetic_frame"] = deepcopy(before)
                        self.assertEqual(before["native_revision"], native["snapshot_revision"])
                        interesting = {
                            ("service.py", "query_player_faction_alerts_v1"),
                            ("service.py", "execute_step"),
                            ("native_driver.py", "execute_step"),
                            ("native_driver.py", "_execute_player_faction_alerts_v1_query"),
                            ("native_driver.py", "_execute_primitive_step"),
                            ("player_faction_alerts_contract.py", "normalize_player_faction_alerts_v1"),
                            ("player_faction_alerts_contract.py", "validate_player_faction_war_handoffs_v1"),
                        }

                        def observe_call(frame_object, event, argument):
                            key = (Path(frame_object.f_code.co_filename).name,
                                   frame_object.f_code.co_name)
                            if key not in interesting:
                                return
                            if event == "call":
                                receipt["call_trace"].append({
                                    "source": frame_object.f_code.co_filename,
                                    "function": key[1]})
                            elif event == "return" and key == ("native_driver.py", "execute_step"):
                                receipt["actual_driver_result"] = deepcopy(argument)
                            elif event == "return" and key == ("service.py", "query_player_faction_alerts_v1"):
                                receipt["actual_service_result"] = deepcopy(argument)

                        sys.setprofile(observe_call)
                        observed = service.query_player_faction_alerts_v1(
                            expected_revision=before["revision"])
                        sys.setprofile(previous_profile)
                        _assert_preserved(self, native, receipt["actual_driver_result"], "actual-driver")
                        _assert_preserved(self, native, observed, "actual-service")
                        self.assertEqual(receipt["actual_service_result"], observed)
                        _assert_preserved(self, raw, observed["player_faction_alerts"], "raw-sibling")
                        self.assertEqual(observed["scope"], "exact-player-faction-alerts")
                        self.assertEqual(set(observed["build"]), {"version", "exe_sha256"})
                        self.assertEqual(observed["build"]["version"], CK3_12004.game_version)
                        self.assertEqual(observed["build"]["exe_sha256"], CK3_12004.executable_sha256)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
                            self.assertEqual(observed["source"][key], before[key])
                            self.assertEqual(observed["binding"][key], before[key])
                        self.assertEqual(observed["binding"]["expected_revision"], before["revision"])
                        self.assertIs(observed["source"]["paused"], True)
                        self.assertIs(observed["player_faction_alerts_ready"], raw["readiness"]["alert_ready"])

                        if case == "known-empty":
                            self.assertEqual(raw["status"], "available")
                            self.assertEqual(raw["date_raw"], 53175816)
                            self.assertEqual(raw["player_character_id"], 50331649)
                            self.assertIs(type(raw["targeting_faction_count"]), int)
                            self.assertEqual(raw["targeting_faction_count"], 0)
                            self.assertEqual(raw["targeting_factions"], [])
                            self.assertEqual(raw["county_exposures"], [])
                            self.assertIs(raw["readiness"]["alert_ready"], True)
                            self.assertIs(raw["planner_projection"]["present"], False)
                            self.assertIs(raw["planner_projection"]["dangerous"], False)
                            for name, value in raw["readiness"].items():
                                self.assertIs(value, name != "exact_ultimatum_timing_ready")
                        elif case == "unavailable":
                            self.assertEqual(raw["status"], "unavailable")
                            self.assertEqual(raw["date_raw"], 0)
                            self.assertIsNone(raw["player_character_id"])
                            self.assertIsNone(raw["targeting_faction_count"])
                            self.assertEqual(raw["targeting_factions"], [])
                            self.assertEqual(raw["county_exposures"], [])
                            self.assertTrue(all(value is False for value in raw["readiness"].values()))
                            self.assertEqual(raw["planner_projection"]["status"], "unavailable")
                            self.assertIsNone(raw["planner_projection"]["present"])
                            self.assertIsNone(raw["planner_projection"]["dangerous"])
                            self.assertIs(type(raw["unavailable_reason"]), str)
                            self.assertEqual(raw["unavailable_reason"], "exact_build_not_admitted")
                        else:
                            self.assertEqual(raw["status"], "available")
                            self.assertEqual(raw["date_raw"], 53175816)
                            self.assertEqual(raw["player_character_id"], 50331649)
                            self.assertEqual(raw["targeting_faction_count"], 1)
                            self.assertEqual(len(raw["targeting_factions"]), 1)
                            self.assertIs(raw["readiness"]["alert_ready"], True)
                            self.assertIs(raw["planner_projection"]["present"], True)
                            row = raw["targeting_factions"][0]
                            self.assertEqual(row["faction_id"], 83886083)
                            self.assertEqual(row["target_character_id"], 50331649)
                            self.assertEqual(row["leader_character_id"], 67108866)
                            if case == "character-member":
                                self.assertEqual(row["faction_type_key"], "liberty_faction")
                                self.assertEqual(row["character_member_ids"], [67108866])
                                self.assertIs(row["dangerous_by_stock_rule"], True)
                                for name, expected_raw in (("power", 11000000),
                                                          ("power_threshold", 8000000),
                                                          ("discontent", 7000000),
                                                          ("discontent_per_month", 100000)):
                                    self.assertIs(type(row[name]["raw"]), int)
                                    self.assertEqual(row[name]["raw"], expected_raw)
                                    self.assertEqual(row[name]["scale"], 100000)
                                self.assertEqual(row["months_until_max_discontent"], 20)
                            else:
                                self.assertEqual(row["faction_type_key"], "populist_faction")
                                self.assertEqual(row["character_member_ids"], [])
                                self.assertEqual(row["county_member_title_ids"], [100663300])
                                self.assertEqual(len(row["county_member_observations"]), 1)
                                county = row["county_member_observations"][0]
                                self.assertEqual(county["county_title_id"], 100663300)
                                self.assertIs(type(county["county_opinion"]["raw"]), int)
                                self.assertEqual(county["county_opinion"]["raw"], 0)
                                self.assertEqual(county["county_opinion"]["scale"], 1)
                                self.assertIs(type(county["native_county_join_score"]["raw"]), int)
                                self.assertEqual(county["native_county_join_score"]["raw"], 0)
                                self.assertEqual(county["native_county_join_score"]["scale"], 100000)
                                self.assertIs(county["can_add_county"], False)
                                self.assertIs(county["removal_queued"], False)
                                self.assertEqual(county["native_leave_score_threshold"]["raw"], -10)
                                self.assertEqual(county["native_leave_score_threshold"]["scale"], 1)

                        after = driver.take_snapshot()
                        receipt["after_synthetic_frame"] = deepcopy(after)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw", "paused", "played_character"):
                            _assert_preserved(self, before[key], after[key], "same-frame." + key)
                        requests = [item for item in endpoint.requests if item.get("type") == "execute_step"]
                        self.assertEqual(len(requests), 1)
                        self.assertEqual(requests[0]["step"], QUERY_PLAYER_FACTION_ALERTS_V1_STEP)
                        self.assertEqual(len(endpoint.delivered_frames), 1)
                        delivered = endpoint.delivered_frames[0]
                        self.assertEqual(delivered["request_id"], requests[0]["request_id"])
                        for key in wire:
                            if key != "request_id":
                                _assert_preserved(self, wire[key], delivered[key], "runtime-transport." + key)
                        executed = {(Path(item["source"]).name, item["function"]) for item in receipt["call_trace"]}
                        self.assertTrue(interesting <= executed, "real Service/driver/primitive/strict normalizer path ran")
                        normalizer_calls = [item for item in receipt["call_trace"]
                                            if item["function"] == "normalize_player_faction_alerts_v1"]
                        self.assertGreaterEqual(len(normalizer_calls), 2, "strict normalization at driver and Service")
                        self.assertEqual(wire, authority, "whole native authority remains unchanged")
                        _write_json(case_dir / "returned-raw-sibling.json", observed["player_faction_alerts"])
                        receipt["status"] = "GREEN"
                    except Exception as error:
                        had_failure = True
                        receipt["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
                        receipt["traceback"] = traceback.format_exc()
                        raise
                    finally:
                        sys.setprofile(previous_profile)
                        if endpoint is not None:
                            receipt["transport_requests"] = deepcopy(endpoint.requests)
                            receipt["runtime_whole_frames"] = deepcopy(endpoint.delivered_frames)
                        if driver is not None:
                            try:
                                driver.close()
                            except Exception as error:
                                had_failure = True
                                receipt["status"] = "RED"
                                receipt["cleanup_exception"] = {"type": type(error).__name__, "message": str(error)}
                        receipt["elapsed_seconds"] = time.perf_counter() - case_started
                        receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
                        _write_json(case_dir / "scene-receipt.json", receipt)
                        _write_json(case_dir / "native-result.json", receipt["native_result"])
                        _write_json(case_dir / "actual-driver-result.json", receipt["actual_driver_result"])
                        _write_json(case_dir / "actual-service-result.json", receipt["actual_service_result"])
                        compound["scenes"].append({
                            "case": case, "status": receipt["status"],
                            "receipt": (case_dir / "scene-receipt.json").as_posix(),
                            "actual_exception": receipt["actual_exception"],
                            "elapsed_seconds": receipt["elapsed_seconds"],
                        })
                        _write_json(output / "service-compound-receipt.json", compound)
            self.assertFalse(had_failure, "all four native scenes and cleanup must pass")
            compound["status"] = "GREEN"
        except Exception as error:
            compound["setup_or_scene_exception"] = {"type": type(error).__name__, "message": str(error)}
            compound["traceback"] = traceback.format_exc()
            raise
        finally:
            compound["elapsed_seconds"] = time.perf_counter() - started
            compound["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            compound["passed_scenes"] = [item["case"] for item in compound["scenes"] if item["status"] == "GREEN"]
            compound["failed_scenes"] = [item["case"] for item in compound["scenes"] if item["status"] != "GREEN"]
            _write_json(output / "service-compound-receipt.json", compound)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--native-wire-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    suite = unittest.TestSuite([FactionAdoptedWholeService12004Tests(METHOD)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
