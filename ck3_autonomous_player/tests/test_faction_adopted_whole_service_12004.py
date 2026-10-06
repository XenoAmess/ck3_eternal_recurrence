"""SOURCE_PREPARED / NOTRUN: fresh actual4 Faction whole wires to real consumers.

Transport, paused scope, process/checkpoint metadata, UUID input and optional
planner selection are synthetic. Each native whole command_result remains
authoritative and is saved byte-for-byte. Root alone runs this sole compound
through the existing Service and registered MCP entrances after source adoption.
"""
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
from unittest.mock import patch
import uuid


METHOD = "test_fresh_native_whole_faction_alerts_and_gift_routes_keep_exact_12004_contract"
SCENES = (
    ("known-empty", "alerts-known-empty.command-result.json"),
    ("character-member", "alerts-character-member.command-result.json"),
    ("county-member", "alerts-county-member.command-result.json"),
    ("unavailable", "alerts-unavailable.command-result.json"),
)
CONFIG: argparse.Namespace | None = None
FIXTURE_UUID_HEX = "00000000000000000000000000000001"
FIXTURE_GIFT_REQUEST_ID = "faction-gift-" + FIXTURE_UUID_HEX
GIFT_SCENES = (
    ("can-send-false", "preview", 1, "no_legal_candidate"),
    ("preview", "preview", 1, "preview_ready"),
    ("submit-pending", "submit", 1, "submitted_verification_pending"),
    ("receipt-unchanged", "receipt", 2, "postcondition_red"),
    ("receipt-applied", "receipt", 3, "applied"),
    ("cold-persisted", "cold", 4, "independent_read_complete"),
    ("cold-absent", "cold", 5, "independent_read_complete"),
    ("known-empty", "preview", 5, "known_empty"),
)
GIFT_TOOLS = {
    "preview": "ck3_query_faction_gift_candidate_private_v1",
    "submit": "ck3_send_faction_gift_private_v1",
    "receipt": "ck3_query_faction_gift_receipt_private_v1",
    "cold": "ck3_query_faction_gift_cold_recovery_private_v1",
}
GIFT_STEPS = {
    "preview": "private-query-faction-gift-member-v1",
    "submit": "private-submit-faction-gift-member-v1",
    "receipt": "private-query-faction-gift-receipt-v1",
    "cold": "private-query-faction-gift-cold-recovery-v1",
}


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
        if frame.get("step") != self.whole_wire["result"]["step"]:
            raise AssertionError("the fixture supplies only its frozen existing native step")
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
    def test_fresh_native_whole_faction_alerts_and_gift_routes_keep_exact_12004_contract(self):
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
            "original_whole_scene_count": 12, "transport_request_hard_bound": 15,
            "gift_successful_pending_submit_qualified": False,
            "gift_source_fixture_boundaries": [
                "The unrun native producer receives the same fixed UUID request input as the real production submit generator; neither nested ACK nor native result is edited.",
                "Known-empty native whole is also consumed in an explicitly synthetic positive-root negative probe, separately from the actual zero-root preflight rejection.",
                "Separate fixture ledgers use real unchanged begin/mark helpers; synthetic process/checkpoint metadata is not a live process or save proof.",
                "Service auto_turn uses an explicit fixture planner wrapper with actual candidate/pending pure helpers. Driver, registered closures, ledger helpers and native bodies are not replaced.",
            ],
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
                            self.assertIsNone(raw["date_raw"])
                            self.assertIsNone(raw["player_character_id"])
                            self.assertIsNone(raw["targeting_faction_count"])
                            self.assertEqual(raw["targeting_factions"], [])
                            self.assertEqual(raw["county_exposures"], [])
                            self.assertTrue(all(value is False for value in raw["readiness"].values()))
                            self.assertEqual(raw["planner_projection"]["status"], "unavailable")
                            self.assertIsNone(raw["planner_projection"]["present"])
                            self.assertIsNone(raw["planner_projection"]["dangerous"])
                            self.assertIs(type(raw["unavailable_reason"]), str)
                            self.assertEqual(raw["unavailable_reason"], "unsupported_build")
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
            self.assertFalse(had_failure, "all four alerts scenes and cleanup must pass")
            _consume_gift_scenes(self, source, output, compound,
                                 NativeHeadlessGameplayDriver, GameplayBridgeService, CK3_12004)
            self.assertEqual(len(compound["scenes"]), 12)
            self.assertEqual(compound["transport_request_count"], 15)
            self.assertLessEqual(compound["transport_request_count"], compound["transport_request_hard_bound"])
            self.assertEqual(set(compound["gift_private_routes_executed"]), set(GIFT_TOOLS.values()))
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


def _gift_frame(revision: int) -> dict[str, object]:
    return {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": f"synthetic-faction-gift-12004:{revision}", "revision": revision,
        "state": {
            "phase": "map_hud", "date": "synthetic-not-live", "date_raw": 53175816,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "one_life_terminal_reason": None,
            "played_character": {"character_id": 50331649, "alive": True},
            "player_armies": [], "active_wars": [],
            "episode_run_id": "faction-whole-12004-gift",
        },
    }


def _gift_stage(test, stage_dir, case, mode, revision, whole_wire, entrance,
                preview_whole, submit_whole, candidate, driver_class, service_class,
                build_identity, compound):
    from xar_autoplayer.bridge import faction_gift_formal_route_v1 as formal
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.faction_gift_formal_candidate_v1 import choose_private_faction_gift_candidate_v1
    from xar_autoplayer.faction_gift_pending_v1 import (
        begin_faction_gift_submission_v1, mark_faction_gift_ack_pending_v1,
        read_faction_gift_ledger_v1,
    )

    stage_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    endpoint = None
    driver = None
    previous_profile = sys.getprofile()
    previous_thread_profile = threading.getprofile()
    native = whole_wire["result"]
    cold = mode == "cold"
    pid = 1200402 if cold else 1200401
    creation = "fixture-process-2" if cold else "fixture-process-1"
    round_id = "R2" if cold else "R1"
    receipt = {
        "schema": "xar.faction-adopted-12004.gift-entrance.v1",
        "case": case, "entrance": entrance, "status": "RED", "live": False,
        "native_result": deepcopy(native), "actual_raw_driver_result": None,
        "actual_driver_result": None, "actual_mcp_result": None,
        "actual_service_result": None, "actual_planner_output": None,
        "actual_exception": None, "expected_error": None, "call_trace": [],
        "process_identity_synthetic": {"pid": pid, "creation_date": creation, "round_id": round_id},
        "source_fixture_boundary": "Paused frame/root/process/checkpoint, fixed real UUID generation input and optional planner selection are synthetic. Real driver, MCP closures, candidate/ledger/classifier helpers and immutable whole result remain unchanged.",
        "controlled_uuid_input": {"text": "00000000-0000-0000-0000-000000000001",
                                  "hex": FIXTURE_UUID_HEX,
                                  "generated_request_id": FIXTURE_GIFT_REQUEST_ID},
        "successful_pending_submission_qualified": False,
    }
    interesting = {
        ("mcp_server.py", name) for name in GIFT_TOOLS.values()
    } | {
        ("service.py", "auto_turn"), ("service.py", "_execute_planned_turn"),
        ("native_driver.py", "query_faction_gift_private_candidate_v1"),
        ("native_driver.py", "submit_faction_gift_private_v1"),
        ("native_driver.py", "query_faction_gift_receipt_private_v1"),
        ("native_driver.py", "query_faction_gift_cold_recovery_private_v1"),
        ("faction_gift_private_transport_v1.py", "query_faction_gift_private_candidate_v1"),
        ("faction_gift_formal_route_v1.py", "_send"),
        ("faction_gift_formal_route_v1.py", "plan_faction_gift_private_v1"),
        ("faction_gift_formal_route_v1.py", "submit_faction_gift_private_v1"),
        ("faction_gift_formal_route_v1.py", "query_faction_gift_receipt_private_v1"),
        ("faction_gift_formal_route_v1.py", "query_faction_gift_cold_recovery_private_v1"),
        ("faction_gift_formal_candidate_v1.py", "choose_private_faction_gift_candidate_v1"),
        ("faction_gift_policy_v1.py", "choose_faction_gift_v1"),
        ("faction_gift_pending_v1.py", "begin_faction_gift_submission_v1"),
        ("faction_gift_pending_v1.py", "mark_faction_gift_ack_pending_v1"),
        ("faction_gift_pending_v1.py", "complete_faction_gift_after_independent_receipt_v1"),
        ("faction_gift_pending_v1.py", "mark_faction_gift_restore_requery_v1"),
        ("faction_gift_pending_v1.py", "resolve_faction_gift_after_cold_native_query_v1"),
        ("faction_gift_cold_recovery_contract_v1.py", "evaluate_faction_gift_cold_recovery_v1"),
    }

    def observe_call(frame_object, event, argument):
        key = (Path(frame_object.f_code.co_filename).name, frame_object.f_code.co_name)
        if key not in interesting:
            return
        if event == "call":
            receipt["call_trace"].append({"source": frame_object.f_code.co_filename,
                                          "function": key[1], "thread_id": threading.get_ident()})
        elif event == "return":
            if key == ("faction_gift_formal_route_v1.py", "_send") and isinstance(argument, dict):
                receipt["actual_raw_driver_result"] = deepcopy(argument)
            elif key == ("faction_gift_private_transport_v1.py", "query_faction_gift_private_candidate_v1"):
                raw_result = frame_object.f_locals.get("result")
                if isinstance(raw_result, dict):
                    receipt["actual_raw_driver_result"] = deepcopy(raw_result)
            elif key[0] == "native_driver.py" and isinstance(argument, dict):
                receipt["actual_driver_result"] = deepcopy(argument)
            elif key == ("service.py", "auto_turn"):
                receipt["actual_service_result"] = deepcopy(argument)

    try:
        endpoint = SyntheticFaction12004Endpoint(whole_wire)
        driver = driver_class(endpoint.pipe_name, endpoint=endpoint,
                              state_dir=stage_dir / "managed-fixture-state",
                              command_timeout_seconds=1.0, episode_projection="native_campaign",
                              allow_private_faction_gift_formal_trial=True,
                              private_faction_round_id=round_id)
        test.assertIs(type(driver), driver_class)
        hello = {
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": pid, "session_generation": 0,
            "game_version": build_identity.game_version,
            "executable_sha256": build_identity.executable_sha256,
            "expected_ck3_version": build_identity.game_version,
            "expected_ck3_sha256": build_identity.executable_sha256,
            "capabilities": ["game.state.snapshot"],
        }
        frame = _gift_frame(revision)
        heartbeat = {"type": "heartbeat", "protocol_version": 1, "sequence": 1,
                     "g2_faction_gift_mitigation_async_glue_v1": {"private_build": True}}
        for name, item in (("synthetic-hello.json", hello), ("synthetic-paused-frame.json", frame),
                           ("synthetic-heartbeat.json", heartbeat)):
            _write_json(stage_dir / name, item)
            endpoint.publish(item)
        # These are the existing runtime identity/checkpoint fixture seams.
        # Their providers carry no actual process/save qualification.
        driver._session_bridge_pid = pid
        before = driver.take_internal_semantic_snapshot()
        receipt["before_synthetic_frame"] = deepcopy(before)
        test.assertEqual(before["native_revision"], revision)
        test.assertEqual(before["date_raw"], 53175816)
        test.assertEqual(before["played_character"]["character_id"], 50331649)
        checkpoint = {"status": "saved", "sha256": "a" * 64, "date_raw": 53175816,
                      "episode_run_id": before["episode_run_id"]}
        with driver._driver_state_lock:
            driver._last_checkpoint = deepcopy(checkpoint)
        root = {"snapshot_revision": revision, "date_raw": 53175816,
                "player_character_id": 50331649, "government": {"key": "feudal_government"},
                "player_targeting_faction_count": 1,
                "direct_landed_vassal_character_ids": [67108866]}
        receipt["checkpoint_synthetic"] = deepcopy(checkpoint)
        receipt["root_synthetic"] = deepcopy(root)
        sys.setprofile(observe_call)
        threading.setprofile(observe_call)
        pending = None
        if mode in {"receipt", "cold"}:
            begin_faction_gift_submission_v1(
                driver.state_dir, request_id=FIXTURE_GIFT_REQUEST_ID,
                episode_run_id=before["episode_run_id"], source_round_id="R1",
                source_bridge_pid=1200401, source_bridge_creation_date="fixture-process-1",
                observation=preview_whole["result"]["native"]["observation"],
                minimum_gold_reserve_raw=5000000,
                checkpoint_sha256_before_submit=checkpoint["sha256"])
            seeded = mark_faction_gift_ack_pending_v1(
                driver.state_dir, request_id=FIXTURE_GIFT_REQUEST_ID,
                ack=submit_whole["result"]["native"]["ack"])
            pending = seeded["pending"]
            receipt["seeded_pending_from_real_helpers"] = deepcopy(pending)
            _assert_preserved(test, submit_whole["result"]["native"]["ack"], pending["ack"], "seeded-native-ack")
        observed = None
        with patch.object(formal, "_process_identity", return_value={"creation_date": creation}), \
                patch.object(formal.uuid, "uuid4", return_value=uuid.UUID(hex=FIXTURE_UUID_HEX)):
            if entrance == "registered_mcp":
                # Test the exact four existing conditional registrations once.
                if case == "can-send-false":
                    matrix = []
                    for query_enabled, action_enabled in ((False, False), (True, False),
                                                          (False, True), (True, True)):
                        driver.allow_private_faction_gift_query = query_enabled
                        driver.allow_private_faction_gift_action = action_enabled
                        matrix_server = create_server(driver)
                        tool_names = set(matrix_server._tool_manager._tools)
                        expected = ({GIFT_TOOLS["preview"]} if query_enabled else set())
                        if action_enabled:
                            expected |= {GIFT_TOOLS[name] for name in ("submit", "receipt", "cold")}
                        test.assertEqual(tool_names & set(GIFT_TOOLS.values()), expected)
                        test.assertIn("ck3_query_player_faction_alerts_v1", tool_names)
                        matrix.append({"query_enabled": query_enabled, "action_enabled": action_enabled,
                                       "registered_gift_tools": sorted(expected)})
                    receipt["actual_registration_condition_matrix"] = matrix
                    compound["actual_registration_condition_matrix"] = deepcopy(matrix)
                driver.allow_private_faction_gift_query = True
                driver.allow_private_faction_gift_action = True
                server = create_server(driver)
                test.assertTrue(set(GIFT_TOOLS.values()) <= set(server._tool_manager._tools))
                tool_name = GIFT_TOOLS[mode]
                arguments = {"expected_revision": before["revision"]}
                if mode == "preview":
                    arguments.update(same_frame_root=root, minimum_gold_reserve_raw=5000000)
                elif mode == "submit":
                    test.assertIsInstance(candidate, dict)
                    arguments.update(candidate=candidate, checkpoint=checkpoint)
                else:
                    arguments["pending"] = pending
                receipt["registered_tool"] = tool_name
                receipt["registered_arguments"] = deepcopy(arguments)
                if case == "known-empty":
                    zero_root = {**root, "player_targeting_faction_count": 0}
                    zero_arguments = {**arguments, "same_frame_root": zero_root}
                    request_count_before = len(endpoint.requests)
                    zero_result = asyncio.run(server.call_tool(tool_name, zero_arguments))
                    test.assertIs(zero_result.is_error, True)
                    zero_text = "\n".join(getattr(item, "text", "") for item in zero_result.content)
                    test.assertIn("private faction query lacks a nonempty exact targeting count", zero_text)
                    test.assertEqual(len(endpoint.requests), request_count_before)
                    receipt["known_empty_authoritative_zero_root"] = {
                        "input": deepcopy(zero_arguments),
                        "actual_mcp_result": zero_result.model_dump(mode="json", by_alias=True),
                        "transport_requests": 0, "expected_preflight_error": True,
                    }
                    _write_json(stage_dir / "known-empty-zero-root-input.json", zero_arguments)
                    _write_json(stage_dir / "known-empty-zero-root-output.json",
                                receipt["known_empty_authoritative_zero_root"])
                    receipt["known_empty_positive_root_boundary"] = (
                        "Explicit synthetic positive-root negative protocol probe only; native empty body is unchanged and no readiness is credited.")
                mcp_result = asyncio.run(server.call_tool(tool_name, arguments))
                receipt["actual_mcp_result"] = mcp_result.model_dump(mode="json", by_alias=True)
                if case == "receipt-unchanged":
                    test.assertIs(mcp_result.is_error, True)
                    error_text = "\n".join(getattr(item, "text", "") for item in mcp_result.content)
                    expected_text = "private faction receipt did not prove material application"
                    test.assertIn(expected_text, error_text)
                    receipt["expected_error"] = {"MCP_is_error": True, "message": error_text,
                                                 "expected_source_error": "StepPostconditionError"}
                else:
                    test.assertIs(mcp_result.is_error, False)
                    observed = mcp_result.structured_content
                    test.assertIsInstance(observed, dict)
                    test.assertEqual(len(mcp_result.content), 1)
                    test.assertEqual(json.loads(mcp_result.content[0].text), observed)
                compound["gift_private_routes_executed"].append(tool_name)
            else:
                test.assertEqual(entrance, "service_auto_turn")
                service = service_class(driver)
                test.assertIs(service.driver, driver)

                def fixture_plan_turn():
                    current = driver.take_internal_semantic_snapshot()
                    baseline = {"snapshot_id": current["snapshot_id"], "revision": current["revision"],
                                "plan": {"selected_step": "life-advance"}}
                    if mode == "submit":
                        # Actual existing pure helper constructs this candidate
                        # from the unchanged preview whole, not invented fields.
                        actual_candidate = choose_private_faction_gift_candidate_v1(
                            current, root, preview_whole["result"], minimum_gold_reserve_raw=5000000)
                        test.assertEqual(actual_candidate["status"], "selected")
                        planned = {**baseline, "plan": {
                            "selected_step": GIFT_STEPS[mode],
                            "faction_gift_action": actual_candidate,
                            "faction_gift_pre_submit_checkpoint": checkpoint}}
                    else:
                        planned = formal.plan_faction_gift_private_v1(
                            driver, baseline, current, [], set())
                    test.assertEqual(planned["plan"]["selected_step"], GIFT_STEPS[mode])
                    receipt["actual_planner_output"] = deepcopy(planned)
                    return planned

                # Only global plan selection is a fixture seam. auto_turn and
                # its real typed dispatcher/driver/ledger route remain original.
                with patch.object(service, "plan_turn", new=fixture_plan_turn):
                    outcome = service.auto_turn()
                    receipt["actual_service_result"] = deepcopy(outcome)
                    test.assertEqual(outcome["status"], "executed")
                    test.assertEqual(outcome["selected_step"], GIFT_STEPS[mode])
                    observed = outcome["result"]
        sys.setprofile(previous_profile)
        threading.setprofile(previous_thread_profile)
        _assert_preserved(test, native, receipt["actual_raw_driver_result"], "whole-native-driver-result")
        if mode == "preview":
            expected_status, expected_reason = {
                "can-send-false": ("no_legal_candidate", "complete_native_no_legal_member"),
                "preview": ("selected", "one_budgeted_native_legal_faction_member"),
                "known-empty": ("unavailable", "native_preview_not_terminal"),
            }[case]
            test.assertEqual(observed["status"], expected_status)
            test.assertEqual(observed["reason"], expected_reason)
            if case != "known-empty":
                _assert_preserved(test, native["native"]["observation"], observed["observation"], "candidate-observation")
                test.assertIs(observed["public_capability_advertised"], False)
                test.assertIs(observed["gift_submission_enabled"], False)
            if case == "preview":
                test.assertEqual(set(observed), {"status", "reason", "observation", "candidate_source",
                                               "public_capability_advertised", "gift_submission_enabled", "choice"})
                test.assertEqual(observed["choice"], {
                    "source_faction_id": 83886083, "recipient_character_id": 67108866,
                    "membership_role": "leader", "snapshot_revision": 1,
                    "native_snapshot_revision": 1, "date_raw": 53175816,
                    "player_character_id": 50331649, "definition_stable_hash": 2003662901,
                    "gold_cost_raw": 7500000, "opinion_delta": 35,
                    "minimum_gold_reserve_raw": 5000000})
                test.assertIs(type(observed["observation"]["recipient_opinion_of_player"]), int)
                test.assertEqual(observed["observation"]["recipient_opinion_of_player"], 0)
            elif case == "known-empty":
                test.assertEqual(set(observed), {"status", "reason"})
                test.assertNotIn("choice", observed)
                _write_json(stage_dir / "known-empty-positive-root-input.json", receipt["registered_arguments"])
                _write_json(stage_dir / "known-empty-positive-root-output.json", observed)
        elif mode == "submit":
            _assert_preserved(test, native, observed, "submitted-native-result")
            test.assertEqual(observed["status"], "submitted_verification_pending")
            ledger = read_faction_gift_ledger_v1(driver.state_dir)
            test.assertEqual(ledger["pending"]["status"], "submitted_verification_pending")
            test.assertEqual(ledger["pending"]["request_id"], FIXTURE_GIFT_REQUEST_ID)
            test.assertEqual(native["native"]["ack"]["request_id"], FIXTURE_GIFT_REQUEST_ID)
            test.assertEqual(ledger["pending"]["ack"], native["native"]["ack"])
            test.assertEqual(observed["pending_ledger"], ledger)
            test.assertEqual(ledger["resolved_request_outcomes"], {})
            receipt["successful_pending_submission_qualified"] = True
            compound["gift_successful_pending_submit_qualified"] = True
        elif case == "receipt-unchanged":
            ledger = read_faction_gift_ledger_v1(driver.state_dir)
            test.assertEqual(ledger["pending"], pending)
            test.assertEqual(native["status"], "postcondition_red")
            test.assertIn("gift_gold_delta_not_observed", json.dumps(native))
        else:
            _assert_preserved(test, native, observed, "material-returned-native-result")
            ledger = read_faction_gift_ledger_v1(driver.state_dir)
            test.assertIsNone(ledger["pending"])
            test.assertEqual(ledger["resolved_request_outcomes"][FIXTURE_GIFT_REQUEST_ID], "applied")
            if mode == "receipt":
                test.assertEqual(observed["status"], "applied")
                test.assertIs(observed["receipt"]["postcondition_verified"], True)
                test.assertEqual(observed["receipt"]["post_player_gold_raw"], 12500000)
                test.assertEqual(observed["receipt"]["post_gift_opinion_modifier_value"], 35)
            else:
                classification = observed["cold_recovery_classification"]
                test.assertEqual(classification["status"], "applied")
                test.assertEqual(classification["reason"], "independent_gold_gift_and_faction_readback")
                test.assertIs(classification["threat_resolved"], case == "cold-absent")
                test.assertIs(classification["action_retry_allowed"], False)
                test.assertIs(observed["native"]["observation"]["source_faction_present"], case == "cold-persisted")
        receipt["actual_ledger_after"] = read_faction_gift_ledger_v1(driver.state_dir)
        receipt["actual_return"] = deepcopy(observed)
        requests = [item for item in endpoint.requests if item.get("type") == "execute_step"]
        test.assertEqual(len(requests), 1, "one transport delivery per gift entrance")
        test.assertEqual(len(endpoint.delivered_frames), 1)
        test.assertEqual(requests[0]["step"], GIFT_STEPS[mode])
        delivered = endpoint.delivered_frames[0]
        test.assertEqual(delivered["request_id"], requests[0]["request_id"])
        for key in whole_wire:
            if key != "request_id":
                _assert_preserved(test, whole_wire[key], delivered[key], "immutable-runtime-whole." + key)
        executed = {(Path(item["source"]).name, item["function"]) for item in receipt["call_trace"]}
        driver_method = {"preview": "query_faction_gift_private_candidate_v1",
                         "submit": "submit_faction_gift_private_v1",
                         "receipt": "query_faction_gift_receipt_private_v1",
                         "cold": "query_faction_gift_cold_recovery_private_v1"}[mode]
        test.assertIn(("native_driver.py", driver_method), executed)
        if mode == "submit":
            test.assertIn(("faction_gift_pending_v1.py", "begin_faction_gift_submission_v1"), executed)
            test.assertIn(("faction_gift_pending_v1.py", "mark_faction_gift_ack_pending_v1"), executed)
        if entrance == "registered_mcp":
            test.assertIn(("mcp_server.py", GIFT_TOOLS[mode]), executed)
        else:
            test.assertIn(("service.py", "auto_turn"), executed)
            test.assertIn(("service.py", "_execute_planned_turn"), executed)
            expected_helper = (("faction_gift_formal_candidate_v1.py", "choose_private_faction_gift_candidate_v1")
                               if mode == "submit" else
                               ("faction_gift_formal_route_v1.py", "plan_faction_gift_private_v1"))
            test.assertIn(expected_helper, executed)
        if mode == "preview" and case != "known-empty":
            test.assertIn(("faction_gift_policy_v1.py", "choose_faction_gift_v1"), executed)
        if mode == "cold":
            test.assertIn(("faction_gift_cold_recovery_contract_v1.py", "evaluate_faction_gift_cold_recovery_v1"), executed)
        receipt["status"] = "GREEN"
        return deepcopy(observed), receipt
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
            request_count = len([item for item in endpoint.requests if item.get("type") == "execute_step"])
            receipt["transport_request_count"] = request_count
            compound["transport_request_count"] += request_count
        if driver is not None:
            try:
                receipt["actual_ledger_finally"] = read_faction_gift_ledger_v1(driver.state_dir)
                driver.close()
            except Exception as error:
                receipt["status"] = "RED"
                receipt["cleanup_exception"] = {"type": type(error).__name__, "message": str(error)}
        receipt["elapsed_seconds"] = time.perf_counter() - started
        receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        for filename, value in (("entrance-receipt.json", receipt),
                                ("actual-native-driver-result.json", receipt["actual_raw_driver_result"]),
                                ("actual-driver-result.json", receipt["actual_driver_result"]),
                                ("actual-mcp-result.json", receipt["actual_mcp_result"]),
                                ("actual-service-result.json", receipt["actual_service_result"]),
                                ("actual-planner-output.json", receipt["actual_planner_output"])):
            _write_json(stage_dir / filename, value)


def _consume_gift_scenes(test, source, output, compound, driver_class, service_class, build_identity):
    native_dir = Path(CONFIG.native_wire_dir)
    preview_bytes = (native_dir / "gift-preview.command-result.json").read_bytes()
    submit_bytes = (native_dir / "gift-submit-pending.command-result.json").read_bytes()
    preview_whole = json.loads(preview_bytes)
    submit_whole = json.loads(submit_bytes)
    reference_dir = output / "gift-original-input-references"
    reference_dir.mkdir(parents=True, exist_ok=True)
    (reference_dir / "gift-preview.command-result.json").write_bytes(preview_bytes)
    (reference_dir / "gift-submit-pending.command-result.json").write_bytes(submit_bytes)
    compound["gift_candidate_pending_input_authority"] = {
        "preview_whole": (native_dir / "gift-preview.command-result.json").as_posix(),
        "submit_whole": (native_dir / "gift-submit-pending.command-result.json").as_posix()}
    compound["transport_request_count"] = 4  # Each preceding alerts scene verified one.
    candidate = None
    had_failure = False
    for case, mode, revision, expected_status in GIFT_SCENES:
        with test.subTest(gift_case=case):
            case_dir = output / ("gift-" + case)
            case_dir.mkdir(parents=True, exist_ok=True)
            filename = "gift-" + case + ".command-result.json"
            receipt = {"case": "gift-" + case, "status": "RED", "live": False,
                       "native_wire_path": (native_dir / filename).as_posix(),
                       "entrances": [], "actual_exception": None}
            started = time.perf_counter()
            try:
                original_bytes = (native_dir / filename).read_bytes()
                (case_dir / "authority-native-whole.json").write_bytes(original_bytes)
                whole_wire = json.loads(original_bytes)
                original = deepcopy(whole_wire)
                test.assertEqual(whole_wire["type"], "command_result")
                test.assertEqual(whole_wire["protocol_version"], 1)
                test.assertIs(whole_wire["ok"], True)
                native = whole_wire["result"]
                test.assertEqual(set(native), {"step", "accepted", "private_build", "advertised",
                                             "status", "native", "receipt"})
                test.assertEqual(native["step"], GIFT_STEPS[mode])
                test.assertEqual(native["status"], expected_status)
                test.assertIs(native["accepted"], True)
                test.assertIs(native["private_build"], True)
                test.assertIs(native["advertised"], False)
                _write_json(case_dir / "authority-raw-sibling.json", native["native"])
                observed, stage = _gift_stage(
                    test, case_dir / "registered-mcp", case, mode, revision, whole_wire,
                    "registered_mcp", preview_whole, submit_whole, candidate,
                    driver_class, service_class, build_identity, compound)
                receipt["entrances"].append({"name": "registered_mcp", "status": stage["status"],
                                             "receipt": (case_dir / "registered-mcp" / "entrance-receipt.json").as_posix()})
                test.assertEqual(stage["status"], "GREEN")
                if case == "preview":
                    candidate = deepcopy(observed)
                    compound["actual_registered_candidate"] = deepcopy(candidate)
                if case in {"submit-pending", "receipt-applied", "cold-absent"}:
                    _, stage = _gift_stage(
                        test, case_dir / "service-auto-turn", case, mode, revision, whole_wire,
                        "service_auto_turn", preview_whole, submit_whole, candidate,
                        driver_class, service_class, build_identity, compound)
                    receipt["entrances"].append({"name": "service_auto_turn", "status": stage["status"],
                                                 "receipt": (case_dir / "service-auto-turn" / "entrance-receipt.json").as_posix()})
                    test.assertEqual(stage["status"], "GREEN")
                test.assertEqual(whole_wire, original, "all original native gift fields remain unchanged")
                receipt["status"] = "GREEN"
            except Exception as error:
                had_failure = True
                receipt["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
                receipt["traceback"] = traceback.format_exc()
                raise
            finally:
                receipt["elapsed_seconds"] = time.perf_counter() - started
                receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
                _write_json(case_dir / "scene-receipt.json", receipt)
                compound["scenes"].append({"case": receipt["case"], "status": receipt["status"],
                                           "receipt": (case_dir / "scene-receipt.json").as_posix(),
                                           "actual_exception": receipt["actual_exception"],
                                           "elapsed_seconds": receipt["elapsed_seconds"]})
                _write_json(output / "service-compound-receipt.json", compound)
    test.assertFalse(had_failure, "all eight original gift cases and their real entrance paths must pass")


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
