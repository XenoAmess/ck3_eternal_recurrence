"""Sole NEW compiled whole callback observation -> registered MCP consumer.

Root runs this explicit CLI only after coherent native/source qualification.
Transport supplies hello/paused scope and request correlation only. Native rows
and raw observations are delivered unchanged.
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


FAMILY = "actual_supply_callback_observations_v1"
SUMMARY = "actual_supply_callback_observation_summary_v1"
ROUTE = "ck3_query_army_strengths"
_OPTIONS = None


def _preserved(case: unittest.TestCase, original: object, observed: object,
               path: str) -> None:
    if isinstance(original, dict):
        case.assertIsInstance(observed, dict, path)
        for key, value in original.items():
            case.assertIn(key, observed, path)
            _preserved(case, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        case.assertIsInstance(observed, list, path)
        case.assertEqual(len(observed), len(original), path)
        for index, value in enumerate(original):
            _preserved(case, value, observed[index], f"{path}[{index}]")
    else:
        case.assertIs(type(observed), type(original), path)
        case.assertEqual(observed, original, path)


class _WholeEndpoint:
    def __init__(self, whole: dict) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_actual_supply_callback_whole_fixture"
        self.whole = whole
        self.requests = []
        self.delivered = []
        self.on_frame = None
        self.on_disconnect = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame, self.on_disconnect = on_frame, on_disconnect

    def publish(self, frame: dict) -> None:
        if self.on_frame is None:
            raise AssertionError("production endpoint was not started")
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict) -> None:
        self.requests.append(deepcopy(frame))
        if frame.get("type") == "ping":
            self.publish({"type": "pong", "protocol_version": 1,
                          "request_id": frame["request_id"]})
            return
        if (frame.get("type"), frame.get("step")) != (
                "execute_step", "query-army-strengths-v1"):
            raise AssertionError("unexpected transport request: " + str(frame))
        whole = deepcopy(self.whole)
        whole["request_id"] = frame["request_id"]
        self.delivered.append(deepcopy(whole))
        self.publish(whole)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class ActualSupplyCallbackRegisteredMcp12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_natural_supply_callback_whole_wire_registered_service(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("use this sole consumer's explicit CLI")
        from xar_autoplayer.bridge import war_contract
        from xar_autoplayer.bridge import army_actual_supply_callback_observations_contract as contract
        from xar_autoplayer.bridge import army_actual_supply_callback_observation_summary as summary
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        source = _OPTIONS.source_root.resolve()
        project = source / "ck3_autonomous_player"
        if not project.is_dir():
            project = source
        for module in (war_contract, contract, summary):
            self.assertEqual(Path(module.__file__).resolve(),
                             project / "src/xar_autoplayer/bridge" / Path(module.__file__).name)
        output = _OPTIONS.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        packet = json.loads(_OPTIONS.native_wire.read_text(encoding="utf-8"))
        self.assertEqual(set(packet), {"schema_version", "fixture_receipt", "whole"})
        self.assertEqual(packet["schema_version"], 1)
        fixture, whole = packet["fixture_receipt"], packet["whole"]
        self.assertEqual(fixture["original_target_kind"], "typed_fixture_callback")
        self.assertIs(fixture["native_EXE_invoked"], False)
        self.assertEqual(fixture["wrapper_invocations"], 5)
        self.assertEqual(fixture["original_invocations"], 5)
        self.assertIs(fixture["original_exactly_once_per_wrapper"], True)
        self.assertIs(fixture["both_full_id_membership_proven"], True)
        self.assertEqual(whole["type"], "command_result")
        self.assertIs(whole["ok"], True)
        native = whole["result"]
        self.assertEqual(native["step"], "query-army-strengths-v1")
        self.assertIs(native["accepted"], True)
        rows = native["army_strengths"]
        self.assertEqual(len(rows), 2)
        self.assertEqual([row[FAMILY]["event_count"] for row in rows], [5, 0])
        self.assertEqual(rows[0]["army_id"], fixture["matching_army_id"])
        self.assertEqual(rows[0]["native_carmy_id"], fixture["matching_native_carmy_id"])
        self.assertNotEqual(rows[0]["army_id"], rows[1]["army_id"])
        self.assertEqual(rows[0]["army_id"] & 0xFFFFFF, rows[1]["army_id"] & 0xFFFFFF)
        self.assertEqual(rows[0]["native_carmy_id"], rows[1]["native_carmy_id"])
        # The compiled reader also checks an independent native-generation
        # mismatch. It shares the public ID, so it is not a duplicate query row.
        self.assertEqual(fixture["wrong_native_generation_event_count"], 0)
        self.assertNotEqual(fixture["matching_native_carmy_id"],
                            fixture["wrong_native_generation_carmy_id"])
        self.assertEqual(fixture["matching_native_carmy_id"] & 0xFFFFFF,
                         fixture["wrong_native_generation_carmy_id"] & 0xFFFFFF)

        receipt = {
            "date": "2026-10-10", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(source), "native_wire": str(_OPTIONS.native_wire.resolve()),
            "registered_tool": ROUTE, "fixture_receipt": fixture,
            "native_reexecution": 0, "native_row_replacements": 0,
            "synthetic_boundary": "typed original and hello/paused scope/request_id correlation",
            "calls": [],
        }
        watched = {
            ("mcp_server.py", ROUTE), ("service.py", "query_army_strengths"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("army_actual_supply_callback_observations_contract.py",
             "normalize_actual_supply_callback_observations_v1"),
            ("army_actual_supply_callback_observation_summary.py",
             "summarize_actual_supply_callback_observations_v1"),
        }
        endpoint = _WholeEndpoint(whole)
        driver = None
        previous, thread_previous = sys.getprofile(), threading.getprofile()

        def observe(frame, event, value):
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if event == "call" and key in watched:
                receipt["calls"].append({"source": frame.f_code.co_filename, "function": key[1]})
            elif event == "return" and key == ("service.py", "query_army_strengths"):
                receipt["service_result"] = deepcopy(value)

        try:
            sys.setprofile(observe)
            threading.setprofile(observe)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                state_dir=output / "driver-state", episode_projection="native_campaign")
            server = create_server(driver)
            self.assertIn(ROUTE, server._tool_manager._tools)
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 4242, "connection_generation": 1,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", war_contract.QUERY_ARMY_STRENGTHS_CAPABILITY],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:1", "revision": 1,
                "state": {
                    "phase": "map_hud", "date": "synthetic-current-not-live",
                    "date_raw": 53289576, "speed": 1, "paused": True, "map_ready": True,
                    "history": [], "active_event": None, "pending_character_interaction": None,
                    "played_character": {"character_id": 29829, "alive": True},
                    "player_armies": [
                        {"army_id": row["army_id"], "controllable": True,
                         "owner_character_id": 29829, "current_province_id": 100}
                        for row in rows], "active_wars": [],
                },
            })
            before = driver.take_snapshot()
            result = await server.call_tool(ROUTE, {
                "army_ids": [row["army_id"] for row in rows],
                "expected_revision": before["revision"],
            })
            self.assertIs(result.is_error, False)
            registered = result.structured_content
            self.assertEqual(registered, receipt["service_result"])
            _preserved(self, native, registered, "registered")
            observations = registered[SUMMARY]
            self.assertEqual(len(observations), 2)
            matched = observations[0]["observation"]
            self.assertEqual(matched["matching_event_count"], 5)
            self.assertEqual(matched["complete_supply_event_count"], 4)
            self.assertEqual(matched["partial_supply_event_count"], 1)
            self.assertEqual([event["supply_delta_raw"] for event in matched["events"]],
                             [-125000, 0, 0, 125000, None])
            self.assertEqual(matched["sum_observed_supply_delta_raw"], 0)
            self.assertEqual(matched["sum_observed_supply_drain_raw"], 125000)
            self.assertIs(matched["actual_callback_observed"], True)
            fenced = summary.summarize_actual_supply_callback_observations_v1(
                registered["army_strengths"][0], after_sequence=3)
            self.assertEqual([event["sequence"] for event in fenced["events"]], [4, 5])
            self.assertEqual(fenced["sum_observed_supply_delta_raw"], 125000)
            self.assertEqual(fenced["sum_observed_supply_drain_raw"], 0)
            for entry in observations:
                measured = entry["observation"]
                for field in ("actual_physical_soldier_loss_observed", "updater_admission_observed",
                              "future_supply_projected", "full_monthly_execution_observed"):
                    self.assertIs(measured[field], False)
            for entry in observations[1:]:
                self.assertEqual(entry["observation"]["matching_event_count"], 0)
                self.assertIsNone(entry["observation"]["sum_observed_supply_delta_raw"])
            self.assertEqual(len(endpoint.delivered), 1)
            self.assertEqual(endpoint.delivered[0]["result"], native)
            executed = {(Path(item["source"]).name, item["function"]) for item in receipt["calls"]}
            self.assertTrue(watched <= executed, executed)
            receipt["registered_result"] = result.model_dump(mode="json", by_alias=True)
            receipt["status"] = "GREEN"
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(previous)
            threading.setprofile(thread_previous)
            if driver is not None:
                driver.close()
            (output / "COMPOUND-RECEIPT.json").write_text(
                json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
    sys.path[0:0] = [str(_project.parent / "tools"),
                      str(_project.parent / "ck3_workshop_mcp/src"), str(_project / "src")]
    unittest.main(argv=[sys.argv[0]], verbosity=2)
