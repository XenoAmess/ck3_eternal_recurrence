"""Sole preserved whole-native loss observation -> registered MCP consumer.

Root executes this readonly CLI once with the new native fixture's JSON output.
The endpoint only supplies hello/snapshot context and correlates request_id.
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


FAMILY = "actual_loss_writer_observations_v1"
ROUTE = "ck3_query_army_strengths"
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


class _PreservedWholeEndpoint:
    def __init__(self, whole: dict[str, object]) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_actual_loss_writer_whole_fixture"
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
            raise AssertionError("production driver did not start its endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        self.requests.append(deepcopy(frame))
        if frame.get("type") == "ping":
            self.publish({"type": "pong", "protocol_version": 1,
                          "request_id": frame["request_id"]})
            return
        if (frame.get("type"), frame.get("step")) != (
                "execute_step", "query-army-strengths-v1"):
            raise AssertionError("unexpected transport request: " + str(frame))
        delivered = deepcopy(self.whole)
        delivered["request_id"] = frame["request_id"]
        self.delivered.append(deepcopy(delivered))
        self.publish(delivered)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class ActualLossWriterRegisteredMcp12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_natural_writer_whole_wire_through_registered_query(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("use this sole consumer's explicit readonly CLI")
        from xar_autoplayer.bridge import war_contract
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        source_root = _OPTIONS.source_root.resolve()
        project = source_root / "ck3_autonomous_player"
        if not project.is_dir():
            project = source_root
        self.assertEqual(Path(war_contract.__file__).resolve(),
                         project / "src/xar_autoplayer/bridge/war_contract.py")
        native_path = _OPTIONS.native_wire.resolve()
        output_dir = _OPTIONS.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        packet = json.loads(native_path.read_text(encoding="utf-8"))
        self.assertEqual(set(packet), {"schema_version", "fixture_receipt", "whole"})
        self.assertIs(type(packet["schema_version"]), int)
        self.assertEqual(packet["schema_version"], 1)
        fixture = packet["fixture_receipt"]
        self.assertEqual(fixture["original_target_kind"], "typed_fixture_callback")
        self.assertIs(fixture["native_EXE_invoked"], False)
        self.assertEqual(fixture["wrapper_invocations"], 3)
        self.assertEqual(fixture["original_invocations"], 3)
        self.assertIs(fixture["original_exactly_once_per_wrapper"], True)
        self.assertIs(fixture["full_id_membership_proven"], True)
        self.assertIs(fixture["cached_change_and_physical_change_separate"], True)
        self.assertIs(fixture["residual_flags_unresolved"], True)
        whole = packet["whole"]
        self.assertEqual(whole["type"], "command_result")
        self.assertIs(whole["ok"], True)
        native = whole["result"]
        self.assertEqual(native["step"], "query-army-strengths-v1")
        self.assertIs(native["accepted"], True)
        self.assertEqual(native["status"], "available")
        rows = native["army_strengths"]
        self.assertEqual([row["army_id"] for row in rows], [11, 12])
        self._assert_observations(rows, fixture)

        receipt: dict[str, object] = {
            "date": "2026-10-09", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(source_root), "native_wire": str(native_path),
            "registered_tool": ROUTE, "native_producer_reexecution": 0,
            "native_body_rewrites": 0,
            "synthetic_boundary": "hello/paused scope/request_id correlation only",
            "native_fixture_receipt": fixture,
            "calls": [],
        }
        watched = {
            ("mcp_server.py", ROUTE), ("service.py", "query_army_strengths"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
        }
        endpoint = _PreservedWholeEndpoint(whole)
        driver = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()

        def observe(frame, event, value):
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in watched:
                return
            if event == "call":
                receipt["calls"].append({"source": frame.f_code.co_filename,
                                         "function": key[1]})
                if key == ("service.py", "query_army_strengths"):
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, driver)
            elif event == "return" and key == ("native_driver.py", "execute_step"):
                receipt["driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", "query_army_strengths"):
                receipt["service_result"] = deepcopy(value)

        try:
            sys.setprofile(observe)
            threading.setprofile(observe)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                state_dir=output_dir / "driver-state", episode_projection="native_campaign")
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
                    "date_raw": fixture["observed_date_raw"], "speed": 1,
                    "paused": True, "map_ready": True, "history": [], "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {"character_id": 29829, "alive": True},
                    "player_armies": [
                        {"army_id": row["army_id"], "controllable": True,
                         "owner_character_id": 29829, "current_province_id": 100}
                        for row in rows
                    ],
                    "active_wars": [],
                },
            })
            before = driver.take_snapshot()
            self.assertEqual(before["snapshot_id"], "native:1")
            self.assertEqual(before["native_revision"], 1)
            result = await server.call_tool(ROUTE, {
                "army_ids": [11, 12], "expected_revision": before["revision"],
            })
            self.assertIs(result.is_error, False)
            registered = result.structured_content
            self.assertIsInstance(registered, dict)
            self.assertEqual(registered, receipt["service_result"])
            _assert_native_values(self, native, receipt["driver_result"], "driver")
            _assert_native_values(self, native, registered, "registered")
            self._assert_observations(registered["army_strengths"], fixture)
            for field in ("snapshot_id", "revision", "native_revision", "date_raw"):
                self.assertEqual(registered["source"][field], before[field])
            executed = {(Path(item["source"]).name, item["function"])
                        for item in receipt["calls"]}
            self.assertTrue(watched <= executed, executed)
            commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
            self.assertEqual(len(endpoint.delivered), 1)
            delivered = endpoint.delivered[0]
            self.assertEqual(delivered["result"], native)
            for key in whole:
                if key != "request_id":
                    self.assertEqual(delivered[key], whole[key])
            receipt["transport_requests"] = deepcopy(endpoint.requests)
            receipt["registered_result"] = result.model_dump(mode="json", by_alias=True)
            receipt["status"] = "GREEN"
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            if driver is not None:
                driver.close()
            _write_json(output_dir / "COMPOUND-RECEIPT.json", receipt)

    def _assert_observations(self, rows, fixture) -> None:
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn(FAMILY, row)
            observations = row[FAMILY]
            self.assertEqual(observations["status"], "available")
            self.assertEqual(observations["source"], "native_natural_writer_entry_return")
            self.assertEqual(observations["membership_basis"], "membership_at_query")
            self.assertEqual(observations["oldest_available_sequence"], 1)
            self.assertEqual(observations["latest_sequence"], 3)
            self.assertEqual(observations["overwritten_events"], 0)
            self.assertEqual(observations["unattributed_capture_failures"], 0)
        matched, different_generation = rows
        full_id = fixture["current_full_regiment_id"]
        wrong_id = fixture["same_index_other_generation_id"]
        self.assertNotEqual(full_id, wrong_id)
        self.assertEqual(full_id & 0xFFFFFF, wrong_id & 0xFFFFFF)
        self.assertEqual(matched["regiment_strengths"][0]["army_regiment_id"], full_id)
        self.assertEqual(different_generation["regiment_strengths"][0]["army_regiment_id"], wrong_id)
        self.assertEqual(different_generation[FAMILY]["event_count"], 0)
        self.assertEqual(different_generation[FAMILY]["events"], [])
        observations = matched[FAMILY]
        self.assertEqual(observations["event_count"], 3)
        events = observations["events"]
        self.assertEqual([event["sequence"] for event in events], [1, 2, 3])
        self.assertEqual([event["cached_current_delta"] for event in events], [-7, 0, 5])
        self.assertEqual([event["actual_physical_soldier_debit"] for event in events], [7, 0, 0])
        self.assertEqual(fixture["cached_current_deltas"], [-7, 0, 5])
        self.assertEqual(fixture["physical_soldier_debits"], [7, 0, 0])
        self.assertEqual(fixture["residual_caller_return_rva"], 0x2A958E8)
        self.assertEqual(fixture["residual_caller_kind"], "residual_allocator")
        for index, event in enumerate(events):
            self.assertEqual(event["army_regiment_id"], full_id)
            self.assertEqual(event["request_raw"], 700000 if index == 0 else 0)
            self.assertEqual(event["request_scale"], 100000)
            self.assertEqual(event["observed_date_raw"], fixture["observed_date_raw"])
            self.assertIs(event["same_instance_after"], True)
            self.assertEqual(event["before_current_soldiers"], [100, 93, 88][index])
            self.assertEqual(event["after_current_soldiers"], 93)
            self.assertEqual(event["before_maximum_soldiers"], 120)
            self.assertEqual(event["after_maximum_soldiers"], 120)
            self.assertEqual(event["cached_maximum_delta"], 0)
            self.assertEqual(event["capture_failure_flags"], 0)
            self.assertEqual(event["native_data_record_count"], 2)
            self.assertEqual(event["captured_data_record_count"], 2)
            self.assertEqual(event["physical_slot_count"], 1)
            self.assertIs(event["physical_capture_complete"], True)
            self.assertIs(event["physical_debit_observed"], True)
            self.assertEqual(event["caller_kind"], "other_writer_caller")
            self.assertNotIn("residual_flags", event)
            self.assertNotIn("army_id_at_invocation", event)
            self.assertEqual(event["data_aliases"], [
                {"data_record_index": position,
                 "persistent_regiment_id": fixture["persistent_regiment_id"],
                 "data_chunk_ordinal": 2, "physical_slot_index": 0}
                for position in range(2)
            ])
            self.assertEqual(event["physical_slots"], [{
                "physical_slot_index": 0,
                "before": {"current_soldiers": 100 if index == 0 else 93,
                           "maximum_soldiers": 120, "state_raw": 1},
                "after": {"current_soldiers": 93,
                          "maximum_soldiers": 120, "state_raw": 1},
                "same_instance_after": True,
            }])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    _OPTIONS = parser.parse_args()
    _source_root = _OPTIONS.source_root.resolve()
    _project = _source_root / "ck3_autonomous_player"
    if not _project.is_dir():
        _project = _source_root
    _repository = _project.parent
    sys.path[0:0] = [
        str(_repository / "tools"),
        str(_repository / "ck3_workshop_mcp/src"),
        str(_project / "src"),
    ]
    unittest.main(argv=[sys.argv[0]], verbosity=2)
