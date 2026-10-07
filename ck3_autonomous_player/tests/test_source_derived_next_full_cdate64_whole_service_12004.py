"""One fresh compiled Source23 whole Army wire through actual registered MCP paths.

Only transport, exact-build hello, paused player scope and outer request correlation
are synthetic. Root exclusively owns the first execution of this consumer.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import threading
import time
import traceback
import unittest

METHOD = "test_first_native_full_cdate64_reaches_execute_and_direct_service"
CONFIG: argparse.Namespace | None = None
FAMILY = "source_derived_next_daily_supply_frame_inputs_v1"
NEW_VALUES = (
    "source_derived_next_date_storage_raw64",
    "source_derived_next_calendar_day_u8",
    "source_derived_next_calendar_month_u8",
)
FULL_READY = "source_derived_full_cdate64_ready"
FALSE_NATIVE = (
    "actual_future_date_stage_observed", "actual_future_callback_observed",
    "future_bucket_mutations_reconstructed", "future_stock_or_strength_ready",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
FALSE_PROJECTION = (
    *FALSE_NATIVE, "future_supply_eligibility_ready",
)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _preserved(test: unittest.TestCase, original: object, observed: object, path: str) -> None:
    test.assertIs(type(observed), type(original), path)
    if isinstance(original, dict):
        test.assertTrue(set(original) <= set(observed), path)
        for key, value in original.items():
            _preserved(test, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        test.assertEqual(len(observed), len(original), path)
        for index, value in enumerate(original):
            _preserved(test, value, observed[index], f"{path}[{index}]")
    else:
        test.assertEqual(observed, original, path)


class _CompiledWholeEndpoint:
    """Answer the real ping and correlate one unchanged native command body."""
    pipe_name = r"\\.\pipe\xar-source23-full-cdate64-12004-fixture"

    def __init__(self, whole: dict[str, object]) -> None:
        self.whole = deepcopy(whole)
        self.on_frame = None
        self.requests: list[dict[str, object]] = []
        self.delivered_frames: list[dict[str, object]] = []

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        if not callable(self.on_frame):
            raise AssertionError("actual driver did not install a frame receiver")
        self.on_frame(deepcopy(frame))

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(deepcopy(request))
        if request.get("type") == "ping":
            self.publish({
                "type": "pong", "protocol_version": 1,
                "request_id": request["request_id"],
            })
            return
        if (request.get("type") != "execute_step"
                or request.get("step") != self.whole["result"]["step"]):
            raise AssertionError("fixture supports only ping and its compiled Army query")
        if self.delivered_frames:
            raise AssertionError("each fresh driver consumes the compiled whole exactly once")
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered_frames.append(deepcopy(response))
        self.publish(response)

    def transport_error(self):
        return None

    def close(self) -> None:
        pass


class SourceDerivedNextFullCdate64WholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_native_full_cdate64_reaches_execute_and_direct_service(self) -> None:
        self.assertIsNotNone(CONFIG)
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        receipt = {
            "schema": "xar.source23-full-cdate6412004.whole-service.v1",
            "status": "RED", "sole_method": self._testMethodName,
            "native_producer_scene_count": 1, "compiled_whole_reexecutions": 0,
            "registered_routes": ["ck3_execute_step", "ck3_query_army_strengths"],
            "live": False, "old_GREEN_replays": 0, "passes": [],
            "synthetic_boundary": (
                "One fresh compiled complete native Army result is consumed unchanged. "
                "Fixture owns native memory/static tables; this consumer owns only "
                "endpoint, hello/pong, paused current scope and outer request_id."
            ),
            "legacy_compatibility_boundary": (
                "Only a detached copy of the actual Source23 leaf loses its four new "
                "optional keys for legacy19 normalize/pure projection; transport "
                "and authoritative native body are never rewritten."
            ),
        }
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()
        try:
            self.assertEqual(sys.flags.optimize, 0)
            supplied = Path(CONFIG.source_root)
            source = (supplied / "ck3_autonomous_player"
                      if (supplied / "ck3_autonomous_player").is_dir() else supplied)
            self.assertTrue((source / "src" / "xar_autoplayer").is_dir())
            sys.path.insert(0, str(source.parent / "tools"))
            sys.path.insert(0, str(source / "src"))
            # Production imports occur only in Root's explicit sole execution.
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.version_identity import CK3_12004
            from xar_autoplayer.bridge.war_contract import (
                QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP,
            )
            from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_contract import (
                normalize_source_derived_next_daily_supply_frame_inputs_v1,
            )
            from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_projection import (
                project_native_next_daily_supply_schedule_v1,
            )
            self.assertEqual(CK3_12004.game_version, "1.20.0.4")
            receipt["source_root"] = source.as_posix()
            for cls in (NativeHeadlessGameplayDriver, GameplayBridgeService):
                loaded = Path(sys.modules[cls.__module__].__file__).resolve()
                self.assertTrue(loaded.is_relative_to((source / "src").resolve()))
            wire_path = Path(CONFIG.native_wire)
            self.assertEqual(wire_path.name, "01-source-derived-next-full-cdate64.json")
            native_bytes = wire_path.read_bytes()
            (output / "authority-native-whole.json").write_bytes(native_bytes)
            whole = json.loads(native_bytes)
            authority = deepcopy(whole)
            context_path = wire_path.with_name(
                "01-source-derived-next-full-cdate64-native-context.json")
            context_bytes = context_path.read_bytes()
            (output / "authority-native-context.json").write_bytes(context_bytes)
            context = json.loads(context_bytes)
            transport = context["synthetic_context"]
            receipt["native_wire"] = wire_path.as_posix()
            receipt["native_context"] = context
            self.assertEqual(whole["type"], "command_result")
            self.assertEqual(whole["protocol_version"], 1)
            self.assertIs(whole["ok"], True)
            native = whole["result"]
            self.assertEqual(set(native), {
                "step", "accepted", "status", "query_sequence", "army_strengths",
            })
            self.assertEqual(native["step"], QUERY_ARMY_STRENGTHS_STEP)
            self.assertIs(native["accepted"], True)
            self.assertEqual(native["query_sequence"], 1)
            self.assertEqual(len(native["army_strengths"]), 1)
            row = native["army_strengths"][0]
            leaf = row[FAMILY]
            schedule = row["future_daily_supply_schedule_inputs_v1"]
            expected_storage = 53288472 | (28 << 32) | (1 << 40) | (1083 << 48)
            self.assertEqual(len(leaf), 23)
            self.assertEqual(leaf["schema_version"], 1)
            self.assertEqual(leaf["source"], "native_source_derived_next_daily_supply_frame_inputs_12004")
            self.assertEqual(leaf["stage"], "source_derived_conditional_next_date_pair")
            self.assertIs(leaf["ready"], True)
            self.assertEqual(leaf["status"], "available")
            self.assertIsNone(leaf["unavailable_reason"])
            self.assertEqual(leaf["current_date_raw_i32"], 53288448)
            self.assertEqual(leaf["current_native_day_index_raw_i32"], 12)
            self.assertEqual(leaf["current_date_storage_raw64"], (7 << 32) | 53288448)
            self.assertEqual(leaf["source_derived_next_date_raw_i32"], 53288472)
            self.assertEqual(leaf["source_derived_next_native_day_index_raw_i32"], 395353)
            self.assertIs(leaf[FULL_READY], True)
            self.assertEqual(leaf[NEW_VALUES[0]], expected_storage)
            self.assertEqual(leaf[NEW_VALUES[1]], 28)
            self.assertEqual(leaf[NEW_VALUES[2]], 1)
            self.assertEqual(row["army_id"], 16777217)
            self.assertEqual(leaf["subject_army_id_u32"], row["army_id"] & 0xFFFFFFFF)
            self.assertEqual(leaf["subject_carmy_id_u32"], row["native_carmy_id"] & 0xFFFFFFFF)
            self.assertEqual(row["scope_role"], "player")
            self.assertEqual(row["war_ids"], [])
            self.assertEqual(transport["date_raw"], leaf["current_date_raw_i32"])
            self.assertEqual(transport["scope_army_ids"], [row["army_id"]])
            self.assertEqual(transport["native_revision"], 1)
            self.assertEqual(transport["snapshot_id"], "native:1")
            self.assertIs(transport["paused"], True)
            self.assertIs(transport["map_ready"], True)
            self.assertEqual(len(schedule["phases"]), 30)
            self.assertIs(schedule["ready"], False)
            self.assertEqual(schedule["status"], "partial")
            for key in FALSE_NATIVE:
                self.assertIs(leaf[key], False)
            normalized = normalize_source_derived_next_daily_supply_frame_inputs_v1(
                leaf, expected_army_id=row["army_id"],
                expected_carmy_id=row["native_carmy_id"])
            self.assertEqual(normalized, leaf)

            for registered_name in receipt["registered_routes"]:
                case_dir = output / registered_name
                case_dir.mkdir()
                endpoint = _CompiledWholeEndpoint(whole)
                driver = None
                observed_pass = {"registered_tool": registered_name, "call_trace": []}
                receipt["passes"].append(observed_pass)
                interesting = {
                    ("mcp_server.py", registered_name),
                    ("service.py", "execute_step" if registered_name == "ck3_execute_step"
                     else "query_army_strengths"),
                    ("native_driver.py", "execute_step"),
                    ("native_driver.py", "_execute_army_strength_query"),
                    ("native_driver.py", "_execute_primitive_step"),
                    ("war_contract.py", "normalize_army_strengths"),
                    ("army_source_derived_next_daily_supply_frame_contract.py",
                     "normalize_source_derived_next_daily_supply_frame_inputs_v1"),
                }
                if registered_name == "ck3_query_army_strengths":
                    interesting.add(("army_source_derived_next_daily_supply_frame_projection.py",
                                     "project_native_next_daily_supply_schedule_v1"))

                def observe(frame, event, value):
                    key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
                    if key not in interesting:
                        return
                    if event == "call":
                        observed_pass["call_trace"].append({
                            "source": frame.f_code.co_filename, "function": key[1],
                        })
                        if key[0] == "service.py":
                            self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                            self.assertIs(frame.f_locals["self"].driver, driver)
                    elif event == "return" and key == ("native_driver.py", "execute_step"):
                        observed_pass["actual_driver_result"] = deepcopy(value)
                    elif event == "return" and key[0] == "service.py":
                        observed_pass["actual_service_result"] = deepcopy(value)

                try:
                    driver = NativeHeadlessGameplayDriver(
                        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                        state_dir=case_dir / "driver-state", episode_projection="native_campaign")
                    self.assertIs(type(driver), NativeHeadlessGameplayDriver)
                    server = create_server(driver)
                    self.assertIn(registered_name, server._tool_manager._tools)
                    hello = {
                        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                        "pid": transport["bridge_host_pid"], "connection_generation": 1,
                        "game_version": CK3_12004.game_version,
                        "executable_sha256": CK3_12004.executable_sha256,
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                        "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
                    }
                    paused = {
                        "type": "state_snapshot", "protocol_version": 1,
                        "snapshot_id": transport["snapshot_id"],
                        "revision": transport["native_revision"],
                        "state": {
                            "phase": "map_hud", "date": "synthetic-current-not-live",
                            "date_raw": transport["date_raw"], "speed": 1,
                            "paused": transport["paused"], "map_ready": transport["map_ready"],
                            "history": [], "active_event": None, "pending_character_interaction": None,
                            "played_character": {
                                "character_id": transport["actor_character_id"], "alive": True,
                            },
                            "player_armies": [{
                                "army_id": row["army_id"], "controllable": True,
                                "owner_character_id": transport["actor_character_id"],
                                "current_province_id": transport["current_province_id"],
                            }],
                            "active_wars": [],
                        },
                    }
                    endpoint.publish(hello)
                    endpoint.publish(paused)
                    before = driver.take_snapshot()
                    observed_pass["before"] = deepcopy(before)
                    self.assertEqual(before["snapshot_id"], transport["snapshot_id"])
                    self.assertEqual(before["snapshot_id"], "native:1")
                    # Hello and the first semantic snapshot each advance public revision.
                    self.assertEqual(before["revision"], 2)
                    self.assertEqual(before["native_revision"], transport["native_revision"])
                    self.assertEqual(before["date_raw"], transport["date_raw"])
                    kwargs = {"expected_revision": before["revision"]}
                    if registered_name == "ck3_execute_step":
                        kwargs["step"] = QUERY_ARMY_STRENGTHS_STEP
                    else:
                        kwargs["army_ids"] = [row["army_id"]]
                    sys.setprofile(observe)
                    threading.setprofile(observe)
                    registered = await server.call_tool(registered_name, kwargs)
                    sys.setprofile(previous_profile)
                    threading.setprofile(previous_thread_profile)
                    self.assertIs(registered.is_error, False)
                    observed = registered.structured_content
                    self.assertIsInstance(observed, dict)
                    self.assertEqual(observed, observed_pass["actual_service_result"])
                    observed_pass["actual_registered_result"] = registered.model_dump(
                        mode="json", by_alias=True)
                    _preserved(self, native, observed_pass["actual_driver_result"], "driver")
                    _preserved(self, native, observed, registered_name)
                    self.assertEqual(observed["army_strengths"][0][FAMILY], leaf)
                    for key in ("revision", "native_revision", "snapshot_id"):
                        self.assertEqual(observed["queried_" + key], before[key])
                    if registered_name == "ck3_query_army_strengths":
                        for key in ("date_raw", "revision", "native_revision", "snapshot_id"):
                            self.assertEqual(observed["source"][key], before[key])
                        projections = observed["same_input_conditional_future_daily_supply_schedule_v1"]
                        self.assertEqual(len(projections), 1)
                        self.assertEqual(projections[0]["army_id"], row["army_id"])
                        projected = projections[0]["projection"]
                        self.assertIs(projected["ready"], False)
                        self.assertEqual(projected["status"], "partial")
                        self.assertIs(projected["full_future_cdate64_reconstructed"], True)
                        self.assertIs(projected[FULL_READY], True)
                        self.assertEqual(projected["source_next_pair"], leaf)
                        for key in NEW_VALUES:
                            self.assertEqual(projected[key], leaf[key])
                        self.assertEqual(len(projected["prospective_frames"]), 1)
                        selected = projected["prospective_frames"][0]
                        self.assertEqual(selected["date_storage_raw64"], expected_storage)
                        self.assertEqual(selected["calendar_day_u8"], 28)
                        self.assertEqual(selected["calendar_month_u8"], 1)
                        self.assertIs(selected[FULL_READY], True)
                        self.assertIs(selected["actual_native_frame_observed"], False)
                        self.assertIs(selected["actual_callback_observed"], False)
                        self.assertEqual(selected["selected_phase_index_i32"], 13)
                        phase = schedule["phases"][13]
                        self.assertIs(selected["conditional_bucket_occurrences_ready"], phase["ready"])
                        self.assertEqual(selected["matching_positions"], phase["matching_positions"])
                        self.assertEqual(selected["subject_occurrence_count_i32"],
                                         phase["subject_occurrence_count_i32"])
                        self.assertTrue(projected["unavailable_phases"])
                        for key in FALSE_PROJECTION:
                            self.assertIs(projected[key], False)
                        observed_pass["projection"] = projected
                    commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
                    pings = [item for item in endpoint.requests if item["type"] == "ping"]
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(len(pings), 1)
                    self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
                    self.assertEqual(len(endpoint.delivered_frames), 1)
                    delivered = endpoint.delivered_frames[0]
                    self.assertEqual(delivered["request_id"], commands[0]["request_id"])
                    for key in authority:
                        if key != "request_id":
                            self.assertEqual(delivered[key], authority[key])
                    self.assertEqual(whole, authority)
                    executed = {(Path(item["source"]).name, item["function"])
                                for item in observed_pass["call_trace"]}
                    self.assertTrue(interesting <= executed)
                finally:
                    sys.setprofile(previous_profile)
                    threading.setprofile(previous_thread_profile)
                    observed_pass["transport_requests"] = deepcopy(endpoint.requests)
                    observed_pass["runtime_whole_frames"] = deepcopy(endpoint.delivered_frames)
                    if driver is not None:
                        driver.close()
                    _write(case_dir / "actual-pass.json", observed_pass)

            legacy = {key: deepcopy(value) for key, value in leaf.items()
                      if key not in {*NEW_VALUES, FULL_READY}}
            self.assertEqual(len(legacy), 19)
            legacy_normalized = normalize_source_derived_next_daily_supply_frame_inputs_v1(
                legacy, expected_army_id=row["army_id"],
                expected_carmy_id=row["native_carmy_id"])
            self.assertEqual(legacy_normalized, legacy)
            self.assertNotIn(FULL_READY, legacy_normalized)
            legacy_row = deepcopy(row)
            legacy_row[FAMILY] = legacy
            legacy_projection = project_native_next_daily_supply_schedule_v1(legacy_row)
            self.assertIs(legacy_projection["full_future_cdate64_reconstructed"], False)
            self.assertIs(legacy_projection[FULL_READY], False)
            self.assertEqual(legacy_projection["source_next_pair"], legacy)
            self.assertNotIn(FULL_READY, legacy_projection["source_next_pair"])
            for key in NEW_VALUES:
                self.assertIsNone(legacy_projection[key])
            for key in FALSE_PROJECTION:
                self.assertIs(legacy_projection[key], False)
            self.assertIs(legacy_projection["ready"], False)
            receipt["legacy19_normalized"] = legacy_normalized
            receipt["legacy19_projection"] = legacy_projection
            receipt["status"] = "GREEN"
            receipt["native_body_changed"] = False
            receipt["registered_tool_calls"] = 2
            receipt["native_command_consumptions"] = 2
        except Exception as error:
            receipt["actual_exception"] = {"type": type(error).__name__, "message": str(error)}
            receipt["traceback"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            receipt["elapsed_seconds"] = time.perf_counter() - started
            receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            _write(output / "sole-compound-receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    CONFIG = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        SourceDerivedNextFullCdate64WholeService12004Tests(METHOD),
    ]))
    sys.exit(0 if result.wasSuccessful() else 1)
