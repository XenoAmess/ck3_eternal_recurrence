"""SOURCE_PREPARED / NOTRUN: fresh .4 whole Strength wires to actual consumers.

Native fixture memory/callbacks are synthetic. This harness only supplies the
transport, exact-build hello, paused player scope and request correlation token.
It does not replace the driver, Service, row normalizer or current-days projection.
Root supplies four freshly emitted paths and the separately accepted native proof.
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


FAMILY = "current_disembark_penalty_v1"
SOURCE = "native_current_disembark_penalty_days_12003"
CASES = {"zero": 0, "negative": -1, "nonstock": 34, "unavailable": None}
METHOD = "test_fresh_native_whole_rows_keep_signed_current_days_under_exact_12004_source"
CONFIG: argparse.Namespace | None = None


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _assert_preserved(test: unittest.TestCase, original: object, observed: object,
                      path: str) -> None:
    """Preserve every native field and exact type, allowing derived metadata."""
    test.assertIs(type(observed), type(original), path)
    if isinstance(original, dict):
        test.assertTrue(set(original) <= set(observed), path)
        for key, value in original.items():
            _assert_preserved(test, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        test.assertEqual(len(original), len(observed), path)
        for index, value in enumerate(original):
            _assert_preserved(test, value, observed[index], f"{path}[{index}]")
    else:
        test.assertEqual(observed, original, path)


class SyntheticCurrentDisembark12004Endpoint:
    """Only the offline transport; the complete native result remains intact."""
    pipe_name = r"\\.\pipe\synthetic-current-disembark-12004-whole-not-live"

    def __init__(self, wire: dict[str, object]):
        self.wire = deepcopy(wire)
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
        if frame.get("step") != "query-army-strengths-v1":
            raise AssertionError("only the existing readonly Strength query is supplied")
        delivered = deepcopy(self.wire)
        delivered["request_id"] = frame["request_id"]
        self.delivered_frames.append(deepcopy(delivered))
        self.publish(delivered)

    def transport_error(self):
        return None

    def close(self):
        pass


def _synthetic_frame(rows: list[dict[str, object]]) -> dict[str, object]:
    """Scope identifiers copied from wire; other frame metadata is synthetic."""
    armies = [{
        "army_id": row["army_id"], "owner_character_id": 29829,
        "soldiers": row["current_soldiers"], "current_province_id": 470,
        "move_target_province_id": None, "controllable": True,
        "route_province_ids": [], "combat_id": None, "retreating": False,
    } for row in rows]
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": "synthetic-current-disembark-12004:40", "revision": 40,
        "state": {
            "phase": "map_hud", "date": "synthetic-not-live", "date_raw": 1000,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": 29829, "alive": True},
            "player_armies": armies, "active_wars": [],
        },
    }


class CurrentDisembarkPenaltyWholeService12004Tests(unittest.TestCase):
    def test_fresh_native_whole_rows_keep_signed_current_days_under_exact_12004_source(self):
        self.assertIsNotNone(CONFIG, "use the separately named CLI with fresh wire paths")
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        had_failure = False
        compound = {
            "schema": "xar.current-disembark-12004.whole-service.compound.v1",
            "status": "RED", "qualification": "fresh fixture checks only",
            "live": False, "source_commit": CONFIG.source_commit,
            "sole_method": self._testMethodName, "scenes": [],
            "actual_driver_class": "NativeHeadlessGameplayDriver",
            "actual_service_class": "GameplayBridgeService",
            "synthetic_boundary": "Native fixture memory/callbacks; endpoint, exact .4 hello, paused frame/player scope and request_id correlation. Native whole result fields remain unchanged.",
            "native_EXE_ABI_proof_from_test": False,
            "actual_disembark_observed": False,
            "future_route_landing_days_ready": False,
            "loaded_landing_duration_observed": False,
            "old_GREEN_replays": 0, "game_process_SDK_operations": 0,
        }
        try:
            self.assertEqual(sys.flags.optimize, 0, "the sole run requires no -O")
            self.assertTrue(CONFIG.source_commit, "Root supplies actual adopted source metadata")
            supplied_root = Path(CONFIG.source_root)
            source = (supplied_root / "ck3_autonomous_player"
                      if (supplied_root / "ck3_autonomous_player").is_dir()
                      else supplied_root)
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir(),
                            "supply the complete adopted project root")
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # These production imports execute only in Root's authorized run.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            self.assertEqual(CK3_12004.executable_sha256.upper(),
                             "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            compound["source_root"] = source.as_posix()
            for label, cls in (("driver_module", NativeHeadlessGameplayDriver),
                               ("service_module", GameplayBridgeService)):
                module_file = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(module_file.is_relative_to((source / "src").resolve()))
                compound[label] = module_file.as_posix()
            proof = Path(CONFIG.native_proof)
            proof_bytes = proof.read_bytes()
            (output / "Root-accepted-native-proof.json").write_bytes(proof_bytes)
            compound["Root_accepted_native_proof_path"] = proof.as_posix()
            wires: dict[str, Path] = {}
            for item in CONFIG.wire:
                case, separator, value = item.partition("=")
                self.assertEqual(separator, "=", "--wire CASE=PATH")
                self.assertIn(case, CASES)
                self.assertNotIn(case, wires)
                self.assertTrue(value)
                wires[case] = Path(value)
            self.assertEqual(set(wires), set(CASES), "one fresh whole wire for each of four cases")
            self.assertEqual(len({path.resolve() for path in wires.values()}), 4,
                             "four independently emitted native whole files")
            compound["native_whole_paths"] = {case: path.as_posix() for case, path in wires.items()}

            for case, expected_days in CASES.items():
                with self.subTest(case=case):
                    case_dir = output / case
                    case_dir.mkdir(parents=True, exist_ok=True)
                    case_started = time.perf_counter()
                    previous_profile = sys.getprofile()
                    endpoint = None
                    driver = None
                    receipt = {
                        "schema": "xar.current-disembark-12004.whole-service.scene.v1",
                        "case": case, "status": "RED", "live": False,
                        "native_wire_path": wires[case].as_posix(),
                        "source_commit": CONFIG.source_commit,
                        "expected_current_days": expected_days,
                        "actual_driver_result": None, "actual_service_result": None,
                        "actual_exception": None, "call_trace": [],
                        "future_route_landing_days_ready": False,
                    }
                    try:
                        original_bytes = wires[case].read_bytes()
                        (case_dir / "authority-native-whole.json").write_bytes(original_bytes)
                        wire = json.loads(original_bytes)
                        authority = deepcopy(wire)
                        self.assertEqual(wire["type"], "command_result")
                        self.assertEqual(wire["protocol_version"], 1)
                        self.assertIs(wire["ok"], True)
                        self.assertEqual(set(wire["result"]), {
                            "step", "accepted", "status", "query_sequence", "army_strengths"})
                        self.assertEqual(wire["result"]["step"], "query-army-strengths-v1")
                        self.assertIs(wire["result"]["accepted"], True)
                        self.assertEqual(wire["result"]["status"], "available")
                        self.assertIs(type(wire["result"]["query_sequence"]), int)
                        self.assertEqual(wire["result"]["query_sequence"], tuple(CASES).index(case) + 1)
                        rows = wire["result"]["army_strengths"]
                        self.assertEqual(len(rows), 1)
                        row = rows[0]
                        self.assertEqual(row["scope_role"], "player")
                        self.assertEqual(row["war_ids"], [])
                        self.assertEqual(row["status"], "available")
                        self.assertEqual(row["army_id"], 16777217)
                        self.assertEqual(row["native_carmy_id"], 33554433)
                        self.assertEqual(row["regiment_count"], 2)
                        raw = row[FAMILY]
                        self.assertEqual(set(raw), {"schema_version", "source", "status", "remaining_days", "unavailable_reason"})
                        self.assertIs(type(raw["schema_version"]), int)
                        self.assertEqual(raw["schema_version"], 1)
                        self.assertEqual(raw["source"], SOURCE)
                        self.assertIs(type(raw["remaining_days"]), type(expected_days))
                        self.assertEqual(raw["remaining_days"], expected_days)
                        self.assertEqual(raw["status"], "unavailable" if expected_days is None else "available")
                        if expected_days is None:
                            self.assertIs(type(raw["unavailable_reason"]), str)
                            self.assertEqual(raw["unavailable_reason"], "disembark_getter_not_bound")
                        else:
                            self.assertIsNone(raw["unavailable_reason"])
                        _write_json(case_dir / "authority-raw-sibling.json", raw)
                        endpoint = SyntheticCurrentDisembark12004Endpoint(wire)
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
                            "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
                        }
                        frame = _synthetic_frame(rows)
                        _write_json(case_dir / "synthetic-hello.json", hello)
                        _write_json(case_dir / "synthetic-paused-scope-frame.json", frame)
                        endpoint.publish(hello)
                        endpoint.publish(frame)
                        before = driver.take_snapshot()
                        receipt["before_synthetic_frame"] = deepcopy(before)
                        interesting = {
                            ("service.py", "query_army_strengths"),
                            ("service.py", "execute_step"),
                            ("native_driver.py", "execute_step"),
                            ("native_driver.py", "_execute_army_strength_query"),
                            ("native_driver.py", "_execute_primitive_step"),
                            ("war_contract.py", "normalize_army_strengths"),
                            ("army_current_disembark_penalty_contract.py", "normalize_current_disembark_penalty_v1"),
                            ("army_current_disembark_penalty_contract.py", "project_current_disembark_penalty_v1"),
                        }

                        def observe_call(frame_object, event, argument):
                            key = (Path(frame_object.f_code.co_filename).name,
                                   frame_object.f_code.co_name)
                            if key not in interesting:
                                return
                            if event == "call":
                                receipt["call_trace"].append({
                                    "source": frame_object.f_code.co_filename, "function": key[1]})
                            elif event == "return" and key == ("native_driver.py", "execute_step"):
                                receipt["actual_driver_result"] = deepcopy(argument)
                            elif event == "return" and key == ("service.py", "query_army_strengths"):
                                receipt["actual_service_result"] = deepcopy(argument)

                        sys.setprofile(observe_call)
                        observed = service.query_army_strengths(
                            [row["army_id"]], expected_revision=before["revision"])
                        sys.setprofile(previous_profile)
                        _assert_preserved(self, wire["result"], receipt["actual_driver_result"], "actual-driver")
                        _assert_preserved(self, wire["result"], observed, "actual-service")
                        self.assertEqual(receipt["actual_service_result"], observed)
                        _assert_preserved(self, raw, observed["army_strengths"][0][FAMILY], "raw-sibling")
                        self.assertEqual(len(observed[FAMILY]), 1)
                        derived = observed[FAMILY][0]
                        self.assertEqual(derived["army_id"], row["army_id"])
                        projection = derived["projection"]
                        self.assertEqual(projection["source"], "source_bound_current_disembark_penalty_days_12003")
                        self.assertEqual(projection["status"], raw["status"])
                        self.assertIs(projection["current_disembark_days_ready"], expected_days is not None)
                        self.assertIs(type(projection["remaining_days"]), type(expected_days))
                        self.assertEqual(projection["remaining_days"], expected_days)
                        self.assertEqual(projection["unavailable_reason"], raw["unavailable_reason"])
                        self.assertIs(projection["future_route_landing_days_ready"], False)
                        _assert_preserved(self, raw, projection["observed_current_disembark_penalty"], "projection-input")
                        provenance = projection["source_provenance"]
                        self.assertEqual(provenance["game_version"], CK3_12004.game_version)
                        self.assertEqual(provenance["executable_sha256"], CK3_12004.executable_sha256)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
                            self.assertEqual(provenance[key], before[key])
                        after = driver.take_snapshot()
                        receipt["after_synthetic_frame"] = deepcopy(after)
                        for key in ("snapshot_id", "revision", "native_revision", "date_raw", "paused", "player_armies", "played_character"):
                            _assert_preserved(self, before[key], after[key], "same-frame." + key)
                        requests = [item for item in endpoint.requests if item.get("type") == "execute_step"]
                        self.assertEqual(len(requests), 1)
                        self.assertEqual(requests[0]["step"], "query-army-strengths-v1")
                        self.assertEqual(len(endpoint.delivered_frames), 1)
                        delivered = endpoint.delivered_frames[0]
                        self.assertEqual(delivered["request_id"], requests[0]["request_id"])
                        for key in wire:
                            if key != "request_id":
                                _assert_preserved(self, wire[key], delivered[key], "runtime-transport." + key)
                        executed = {(Path(item["source"]).name, item["function"]) for item in receipt["call_trace"]}
                        self.assertTrue(interesting <= executed, "actual driver/Service/strict normalizer/projection ran")
                        self.assertEqual(wire, authority, "whole authority fields are never replaced")
                        _write_json(case_dir / "returned-raw-sibling.json", observed["army_strengths"][0][FAMILY])
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
                        _write_json(case_dir / "actual-driver-result.json", receipt["actual_driver_result"])
                        _write_json(case_dir / "actual-service-result.json", receipt["actual_service_result"])
                        compound["scenes"].append({
                            "case": case, "status": receipt["status"],
                            "receipt": (case_dir / "scene-receipt.json").as_posix(),
                            "actual_exception": receipt["actual_exception"],
                            "elapsed_seconds": receipt["elapsed_seconds"],
                        })
                        _write_json(output / "service-compound-receipt.json", compound)
            self.assertFalse(had_failure, "each native whole scene and driver cleanup must pass")
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
    parser.add_argument("--native-proof", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--wire", action="append", required=True, metavar="CASE=PATH")
    CONFIG = parser.parse_args()
    suite = unittest.TestSuite([CurrentDisembarkPenaltyWholeService12004Tests(METHOD)])
    run = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if run.wasSuccessful() else 1)
