"""One real Service/registered MCP consumer of four native whole packets.

Only the endpoint and enclosing hello/paused scope are synthetic. The
production driver initializes its own protocol state and command history;
native command_result bodies are never replaced or derived in Python.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ARMY_ID = 83886367
NATIVE_ARMY_ID = 50331794
PLAYER_ID = 29829
CURRENT_ID = 30000
PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53288448
SOURCE = "native_current_assigned_commander_ai_base_quality"
PACKETS = (
    ("quality-current-outside-pool.json", 37),
    ("quality-current-zero.json", 0),
    ("quality-current-unavailable.json", None),
    ("quality-candidate-comparison.json", 37),
)
REPORT_NAME = "current-commander-native-ai-base-quality-service-result.json"
_CONFIG: dict[str, Path | None] | None = None


def _configuration() -> dict[str, Path | None]:
    if _CONFIG is not None:
        return _CONFIG
    native_dir = os.environ.get("XAR_CURRENT_COMMANDER_BASE_QUALITY_NATIVE_DIR")
    output_dir = os.environ.get("XAR_CURRENT_COMMANDER_BASE_QUALITY_OUTPUT_DIR")
    return {
        "source_root": Path(os.environ.get(
            "XAR_CURRENT_COMMANDER_BASE_QUALITY_SOURCE_ROOT",
            str(Path(__file__).resolve().parents[2]),
        )).resolve(),
        "native_dir": Path(native_dir).resolve() if native_dir else None,
        "output_dir": Path(output_dir).resolve() if output_dir else None,
    }


def _persist(output_dir: Path | None, report: dict[str, object]) -> None:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / REPORT_NAME).write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8",
        )


def _load_implementation(source_root: Path):
    for relative in ("tools", "ck3_workshop_mcp/src", "ck3_autonomous_player/src"):
        sys.path.insert(0, str(source_root / relative))
    loaded = {}
    for name in (
        "army_commander_current_base_quality", "army_commander_current_martial",
        "army_commander_candidates", "army_family_12004_identity",
        "version_identity", "native_driver", "service", "mcp_server",
    ):
        module = importlib.import_module(f"xar_autoplayer.bridge.{name}")
        expected = source_root / f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"whole consumer loaded outside its source projection: {name}")
        loaded[name] = module
    return loaded


def _driver_for_packet(modules, packet, state_dir: Path):
    native = modules["native_driver"]
    contract = modules["army_commander_candidates"]
    identity = modules["version_identity"].CK3_12004

    class WholeNativeEndpoint:
        pipe_name = native.DEFAULT_PIPE_NAME

        def __init__(self):
            self.requests = []
            self.transport_requests = []
            self.responses = []
            self.on_frame = None
            self.on_disconnect = None

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame
            self.on_disconnect = on_disconnect

        def publish_scope(self):
            self.on_frame({
                "type": "hello", "protocol_version": 1, "pid": 4242,
                "connection_generation": 1,
                "game_version": identity.game_version,
                "executable_sha256": identity.executable_sha256,
                "expected_ck3_version": identity.game_version,
                "expected_ck3_sha256": identity.executable_sha256,
                "capabilities": [
                    "game.state.snapshot",
                    contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                    contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_FOR_TARGET_CAPABILITY,
                ],
            })
            # Three explicitly synthetic enclosing frame identities yield the
            # frozen public revision4 through real protocol ingest (hello=1).
            for occurrence in (1, 2, 3):
                self.on_frame({
                    "type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": f"synthetic-quality-paused-scope:{occurrence}",
                    "revision": NATIVE_REVISION,
                    "state": {
                        "paused": True, "map_ready": True, "date_raw": DATE_RAW,
                        "played_character": {"character_id": PLAYER_ID, "alive": True},
                        "player_armies": [{
                            "army_id": ARMY_ID, "owner_character_id": PLAYER_ID,
                            "controllable": True, "current_province_id": 2669,
                        }],
                        "active_wars": [],
                    },
                })

        def send(self, request):
            self.transport_requests.append(deepcopy(request))
            if request["type"] == "ping":
                self.on_frame({
                    "type": "pong", "protocol_version": 1,
                    "request_id": request["request_id"],
                })
                return
            if request["type"] != "execute_step":
                raise RuntimeError(f"unexpected fixture transport request: {request['type']}")
            self.requests.append(deepcopy(request))
            response = deepcopy(packet)
            # The sole native packet change is protocol request correlation.
            response["request_id"] = request["request_id"]
            self.responses.append(deepcopy(response))
            self.on_frame(response)

        def close(self):
            if self.on_disconnect is not None:
                self.on_disconnect()

    endpoint = WholeNativeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(
        endpoint=endpoint, state_dir=state_dir, save_dir=state_dir / "saves",
        command_timeout_seconds=1.0, episode_projection="native_campaign",
    )
    endpoint.publish_scope()
    return driver


class CurrentCommanderNativeAiBaseQualityServiceTests(unittest.TestCase):
    def test_whole_native_query_registered_mcp_compound(self):
        config = _configuration()
        source_root = config["source_root"]
        native_dir = config["native_dir"]
        output_dir = config["output_dir"]
        missing = (["--native-dir"] if native_dir is None else [
            str(native_dir / filename) for filename, _ in PACKETS
            if not (native_dir / filename).is_file()
        ])
        if missing:
            _persist(output_dir, {
                "status": "NOTRUN", "missing_inputs": missing,
                "test_method_count": 1, "native_packets_consumed": 0,
                "live_validation": False,
            })
            print("NOTRUN: genuine four native whole-query wires are required")
            self.skipTest("NOTRUN: native quality whole packets unavailable")
        report = {
            "schema": "current-commander-native-ai-base-quality-service-12004-v1",
            "status": "RED", "test_method_count": 1,
            "native_scene_count": 4, "native_packet_count": 4,
            "derived_packet_count": 0, "native_body_rows_replaced": False,
            "fake_boundary": "transport endpoint/correlation and enclosing hello/paused scope only",
            "driver_methods_patched": False, "production_state_ingest": True,
            "game_touched": False, "live_validation": False, "occurrences": [],
        }
        try:
            modules = _load_implementation(source_root)
            report["loaded_module_paths"] = {
                name: str(module.__file__) for name, module in modules.items()
            }
            contract = modules["army_commander_candidates"]
            step = contract.query_army_commander_candidates_v1_step(ARMY_ID)

            async def consume():
                for filename, expected_value in PACKETS:
                    packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                    original = deepcopy(packet)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertEqual(packet["protocol_version"], 1)
                    self.assertIs(packet["ok"], True)
                    envelope = packet["result"]
                    self.assertEqual(envelope["step"], step)
                    self.assertIs(envelope["accepted"], True)
                    self.assertIs(envelope["read_only"], True)
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["query_sequence"], 7)
                    expected = envelope["army_commander_candidates"]
                    with tempfile.TemporaryDirectory(prefix="quality-service-scope-") as temporary:
                        driver = _driver_for_packet(modules, packet, Path(temporary))
                        try:
                            scope = driver.take_snapshot()
                            self.assertEqual(scope["revision"], PUBLIC_REVISION)
                            self.assertEqual(scope["native_revision"], NATIVE_REVISION)
                            self.assertEqual(scope["date_raw"], DATE_RAW)
                            self.assertEqual(driver._command_history, [])
                            self.assertTrue(driver.state._raw_state_snapshot_accepted)
                            self.assertTrue(driver.capabilities()["snapshot"])
                            server = modules["mcp_server"].create_server(driver)
                            tools = await server.list_tools()
                            tool = next(row for row in tools if row.name == "ck3_query_army_commander_candidates_v1")
                            self.assertEqual(set(tool.input_schema["properties"]), {
                                "army_id", "expected_revision", "target_province_id",
                            })
                            self.assertEqual(tool.input_schema["required"], ["army_id"])
                            self.assertTrue(getattr(tool.annotations, "read_only_hint",
                                                   getattr(tool.annotations, "readOnlyHint", False)))
                            response = await server.call_tool(
                                "ck3_query_army_commander_candidates_v1",
                                {"army_id": ARMY_ID, "expected_revision": PUBLIC_REVISION},
                            )
                            self.assertFalse(getattr(response, "is_error", getattr(response, "isError", False)))
                            observed = response.structured_content
                            self.assertIsInstance(observed, dict)
                            self.assertEqual(observed["army_commander_candidates"], expected)
                            self.assertEqual(observed["queried_revision"], PUBLIC_REVISION)
                            self.assertEqual(observed["queried_native_revision"], NATIVE_REVISION)
                            self.assertEqual(observed["date_raw"], DATE_RAW)
                            self.assertEqual(observed["query_sequence"], 7)
                            self.assertEqual(observed["backend_id"], "native-headless")
                            self.assertEqual(len(driver.endpoint.requests), 1)
                            self.assertEqual(driver.endpoint.requests[0]["step"], step)
                            self.assertEqual(driver.endpoint.requests[0]["expected_revision"], NATIVE_REVISION)
                            self.assertEqual(driver.endpoint.responses[0]["result"], original["result"])
                            self.assertEqual(packet, original)
                            self.assertEqual(len(driver._command_history), 1)
                            self.assertIs(driver._command_history[0]["ok"], True)
                            self.assertEqual(driver._command_history[0]["command"], step)
                            self.assertEqual(expected["schema"], "ck3_12004_army_commander_candidates_v1")
                            self.assertEqual(expected["army_id"], ARMY_ID)
                            self.assertEqual(expected["native_carmy_id"], NATIVE_ARMY_ID)
                            self.assertEqual(expected["owner_character_id"], PLAYER_ID)
                            self.assertEqual(expected["eligibility_mode"], 1)
                            self.assertIs(expected["collection_filter_now"], False)
                            self.assertIs(expected["collection_allow_guests"], True)
                            self.assertIs(expected["candidate_collection_complete"], True)
                            self.assertEqual(expected["candidate_source_count"], 2)
                            self.assertIsNone(expected.get("target_province_id"))
                            role = expected["current_commander"]
                            leaf = role["current_native_ai_base_quality"]
                            self.assertEqual(set(leaf), {
                                "status", "source", "source_character_id", "value", "unavailable_reason",
                            })
                            self.assertEqual(role["character_id"], CURRENT_ID)
                            self.assertEqual(leaf["source_character_id"], CURRENT_ID)
                            self.assertEqual(leaf["source"], SOURCE)
                            self.assertEqual(leaf["value"], expected_value)
                            martial = role["current_total_martial"]
                            comparison = filename == "quality-candidate-comparison.json"
                            candidates = expected["candidates"]
                            self.assertEqual([row["character_id"] for row in candidates],
                                             [CURRENT_ID, 30001] if comparison else [30001, 30002])
                            self.assertEqual([row["native_ai_base_quality"] for row in candidates],
                                             [37, 25] if comparison else [25, 15])
                            self.assertEqual([row["generic_advantage_points"] for row in candidates],
                                             [9, 7] if comparison else [7, 2])
                            self.assertEqual([row["can_assign"] for row in candidates],
                                             [False, True] if comparison else [True, True])
                            self.assertEqual([row["siege_phase_time_modifier_raw"] for row in candidates],
                                             [0, 0] if comparison else [0, -10000])
                            for row in candidates:
                                self.assertIs(row["available"], True)
                                self.assertIs(row["final_eligibility_observable"], True)
                                self.assertIs(row["quality_observable"], True)
                                self.assertIsNone(row["unavailable_reason"])
                            if expected_value is None:
                                self.assertEqual(expected["status"], "partial")
                                self.assertEqual(role["status"], "unavailable")
                                self.assertEqual(leaf["status"], "unavailable")
                                self.assertIsNone(leaf["value"])
                                self.assertEqual(leaf["unavailable_reason"], "current_commander_identity_unavailable")
                                self.assertEqual(martial["status"], "unavailable")
                                self.assertIsNone(martial["value"])
                                self.assertEqual(martial["source_character_id"], CURRENT_ID)
                            else:
                                self.assertEqual(expected["status"], "available")
                                self.assertEqual(role["status"], "available")
                                self.assertEqual(leaf["status"], "available")
                                self.assertIs(type(leaf["value"]), int)
                                self.assertIsNone(leaf["unavailable_reason"])
                                self.assertEqual(martial["value"], 17)
                                self.assertNotEqual(leaf["value"], martial["value"])
                            if not comparison:
                                self.assertNotIn(CURRENT_ID, [row["character_id"] for row in candidates])
                            else:
                                self.assertEqual(leaf["value"], candidates[0]["native_ai_base_quality"])
                                self.assertNotEqual(leaf["value"], candidates[0]["generic_advantage_points"])
                                self.assertNotEqual(martial["value"], candidates[0]["generic_advantage_points"])
                                self.assertIs(candidates[0]["can_assign"], False)
                                self.assertIs(candidates[1]["can_assign"], True)
                                self.assertGreater(leaf["value"], candidates[1]["native_ai_base_quality"])
                                self.assertEqual(role["status"], "available")
                            movement = expected["current_movement_speed"]
                            self.assertEqual(movement["schema"], "ck3_12004_army_current_movement_speed_v1")
                            self.assertEqual(movement["public_cunit_id"], ARMY_ID)
                            self.assertEqual(movement["native_carmy_id"], NATIVE_ARMY_ID)
                            self.assertEqual(movement["current_commander_character_id"], CURRENT_ID)
                            self.assertEqual(movement["current_province_id"], 2669)
                            self.assertEqual(movement["route_read_status"], "complete_empty")
                            self.assertEqual(movement["route_source_count"], 0)
                            self.assertEqual(movement["land"]["raw"], 125000)
                            self.assertEqual(movement["naval"]["raw"], 250000)
                            self.assertEqual(movement["current_edge"]["status"], "not_applicable")
                            self.assertIsNone(movement["current_edge"]["raw"])
                            self.assertEqual(movement["current_edge"]["unavailable_reason"], "empty_route")
                            report["occurrences"].append({
                                "wire": str(native_dir / filename), "status": "GREEN",
                                "provenance": "genuine native whole command_result",
                                "current_character_id": CURRENT_ID,
                                "current_quality": leaf["value"],
                                "candidate_ids": [row["character_id"] for row in candidates],
                                "command_history_count": len(driver._command_history),
                            })
                        finally:
                            driver.endpoint.close()

            asyncio.run(consume())
            self.assertEqual(len(report["occurrences"]), 4)
            report["status"] = "GREEN"
            report["readiness"] = "static-ready; whole fixture consumption only"
        except Exception as error:
            report["failure"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            _persist(output_dir, report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    global _CONFIG
    _CONFIG = {
        "source_root": arguments.source_root.resolve(),
        "native_dir": arguments.native_dir.resolve(),
        "output_dir": arguments.output_dir.resolve(),
    }
    suite = unittest.TestSuite([CurrentCommanderNativeAiBaseQualityServiceTests(
        "test_whole_native_query_registered_mcp_compound",
    )])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
