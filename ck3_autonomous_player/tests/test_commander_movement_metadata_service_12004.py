"""Whole native movement metadata consumer for the adopted actual4 source.

The new getter metadata is pinned to the finite mapper's actual4 proof.
Two original compiled whole packets must exercise both actual4 and legacy
selection. Root qualifies the method; no Python native-body variants are used.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import sys
import unittest


PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53236608
ARMY_ID = 83886367
NATIVE_ARMY_ID = 50331794
PLAYER_ID = 29829
PACKETS = (
    (
        "01-actual4-movement.json",
        "ck3_12004_army_commander_candidates_v1",
        "ck3_12004_army_current_movement_speed_v1",
        {"land": "0x24AA920", "naval": "0x24AABE0", "current_edge": "0x24AB5A0"},
    ),
    (
        "02-legacy-movement.json",
        "ck3_12003_army_commander_candidates_v1",
        "ck3_12003_army_current_movement_speed_v1",
        {"land": "0x24AA940", "naval": "0x24AAC00", "current_edge": "0x24AB5C0"},
    ),
)


def _load_implementation():
    """Load the whole adopted driver/state/Service/MCP source path."""
    projection = Path(os.environ.get(
        "XAR_COMMANDER_MOVEMENT_METADATA_PROJECTION_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )).resolve()
    for relative in ("tools", "ck3_workshop_mcp/src", "ck3_autonomous_player/src"):
        sys.path.insert(0, str(projection / relative))
    import xar_autoplayer.bridge as bridge

    bridge.__path__.insert(0, str(
        projection / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    ))
    loaded = {}
    for name in (
        "army_family_12004_identity", "army_commander_candidates",
        "native_driver", "service", "mcp_server",
    ):
        fullname = f"xar_autoplayer.bridge.{name}"
        module = (
            importlib.reload(sys.modules[fullname]) if fullname in sys.modules
            else importlib.import_module(fullname)
        )
        expected = projection / f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"whole consumer loaded outside adopted actual4 source: {name}")
        loaded[name] = module
    return loaded


def _replay_driver(modules, packet):
    """Use genuine production initialization, frame ingest/state and execution."""
    contract = modules["army_commander_candidates"]
    native = modules["native_driver"]

    class WholePacketEndpoint:
        pipe_name = native.DEFAULT_PIPE_NAME

        def __init__(self):
            self.requests = []
            self.on_frame = None

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def send(self, request):
            self.requests.append(deepcopy(request))
            response = deepcopy(packet)
            # Transport correlation only; the original whole result is intact.
            response["request_id"] = request["request_id"]
            self.on_frame(response)

        def close(self):
            pass

    class PausedScopeReplay(native.NativeHeadlessGameplayDriver):
        def __init__(self):
            self.scope = {
                "paused": True, "map_ready": True, "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
                "snapshot_id": "synthetic-paused-commandermovementmetadata-actual4:11",
                "played_character": {"character_id": PLAYER_ID, "alive": True},
                "player_armies": [{
                    "army_id": ARMY_ID, "controllable": True,
                    "owner_character_id": PLAYER_ID,
                }],
                "active_wars": [],
            }
            super().__init__(endpoint=WholePacketEndpoint(), command_timeout_seconds=1.0)

        def take_snapshot(self):
            return deepcopy(self.scope)

        def capabilities(self):
            advertised = [
                contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_FOR_TARGET_CAPABILITY,
            ]
            return {
                "bridge_capabilities": advertised, "backend_id": "native-headless",
                "action_steps": native._action_steps(
                    advertised, player_armies=self.scope["player_armies"], paused=True,
                ),
            }

    return PausedScopeReplay()


class CommanderMovementMetadataServiceTests(unittest.TestCase):
    def test_whole_native_query_registered_mcp_compound(self):
        native_dir_value = os.environ.get("XAR_COMMANDER_MOVEMENT_METADATA_NATIVE_DIR")
        if not native_dir_value:
            print("NOT RUN: XAR_COMMANDER_MOVEMENT_METADATA_NATIVE_DIR is unset; genuine whole wires required")
            self.skipTest("NOT RUN: native actual4/legacy movement metadata wires unavailable")
        native_dir = Path(native_dir_value)
        report_path = Path(os.environ.get(
            "XAR_COMMANDER_MOVEMENT_METADATA_SERVICE_REPORT",
            str(native_dir / "commander-movement-metadata-service-compound-result.json"),
        ))
        occurrences = []
        report = {
            "schema": "commander-movement-metadata-service-compound-12004-v1",
            "status": "RED", "test_method_count": 1,
            "native_scene_count": 2, "native_packet_count": 2,
            "derived_packet_count": 0, "native_body_rows_replaced": False,
            "native_metadata_rewritten_in_python": False, "payload_resigned": False,
            "fake_boundary": "transport endpoint/advertisement and paused scope only",
            "game_touched": False, "live_validation": False,
            "occurrences": occurrences,
        }
        try:
            modules = _load_implementation()
            report["loaded_module_paths"] = {
                name: str(module.__file__) for name, module in modules.items()
            }
            contract = modules["army_commander_candidates"]
            preserved_scenes = []

            async def replay(filename, packet, parent_schema, movement_schema, getters):
                expected = packet["result"]["army_commander_candidates"]
                movement = expected["current_movement_speed"]
                target = expected.get("target_province_id")
                driver = _replay_driver(modules, packet)
                server = modules["mcp_server"].create_server(driver)
                try:
                    tools = await server.list_tools()
                    tool = next(row for row in tools if row.name == "ck3_query_army_commander_candidates_v1")
                    self.assertEqual(set(tool.input_schema["properties"]), {
                        "army_id", "expected_revision", "target_province_id",
                    })
                    self.assertEqual(tool.input_schema["required"], ["army_id"])
                    self.assertTrue(getattr(tool.annotations, "read_only_hint",
                                           getattr(tool.annotations, "readOnlyHint", False)))
                    arguments = {"army_id": ARMY_ID, "expected_revision": PUBLIC_REVISION}
                    if target is not None:
                        arguments["target_province_id"] = target
                    response = await server.call_tool("ck3_query_army_commander_candidates_v1", arguments)
                    self.assertFalse(getattr(response, "is_error", getattr(response, "isError", False)))
                    observed = response.structured_content
                    self.assertIsInstance(observed, dict)
                    # Compare the complete original native result, including
                    # every current/candidate/target role and movement field.
                    self.assertEqual(observed["army_commander_candidates"], expected)
                    self.assertEqual(observed["queried_revision"], PUBLIC_REVISION)
                    self.assertEqual(observed["queried_native_revision"], NATIVE_REVISION)
                    self.assertEqual(observed["date_raw"], DATE_RAW)
                    self.assertEqual(observed["query_sequence"], 7)
                    self.assertEqual(observed["backend_id"], "native-headless")
                    self.assertEqual(len(driver.endpoint.requests), 1)
                    request = driver.endpoint.requests[0]
                    step = contract.query_army_commander_candidates_v1_step(
                        ARMY_ID, target_province_id=target,
                    )
                    self.assertEqual(request["step"], step)
                    self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                    self.assertEqual(len(driver._command_history), 1)
                    self.assertTrue(driver._command_history[0]["ok"])
                    self.assertEqual(driver._command_history[0]["command"], step)
                    self.assertEqual(expected["schema"], parent_schema)
                    self.assertEqual(expected["army_id"], ARMY_ID)
                    self.assertEqual(expected["native_carmy_id"], NATIVE_ARMY_ID)
                    self.assertEqual(expected["owner_character_id"], PLAYER_ID)
                    self.assertEqual(expected["status"], "available")
                    self.assertIsNone(target)
                    self.assertIs(expected["candidate_collection_complete"], True)
                    self.assertEqual(expected["candidate_source_count"], 1)
                    self.assertEqual(len(expected["candidates"]), 1)
                    role = expected["current_commander"]
                    self.assertEqual(role["status"], "available")
                    self.assertEqual(role["character_id"], 30000)
                    self.assertIsNone(role["unavailable_reason"])
                    martial = role["current_total_martial"]
                    self.assertEqual(martial["status"], "available")
                    self.assertEqual(martial["source"],
                                     "native_current_assigned_commander_total_skill_cache")
                    self.assertEqual(martial["source_character_id"], 30000)
                    self.assertIs(type(martial["skill_index"]), int)
                    self.assertEqual(martial["skill_index"], 1)
                    self.assertIs(type(martial["value"]), int)
                    self.assertEqual(martial["value"], 17)
                    self.assertIsNone(martial["unavailable_reason"])
                    candidate = expected["candidates"][0]
                    self.assertEqual(candidate["character_id"], 30001)
                    self.assertIs(candidate["available"], True)
                    self.assertIs(candidate["final_eligibility_observable"], True)
                    self.assertIs(candidate["can_assign"], True)
                    self.assertIs(candidate["quality_observable"], True)
                    self.assertEqual(candidate["native_ai_base_quality"], 125)
                    self.assertEqual(candidate["generic_advantage_points"], 0)
                    self.assertEqual(candidate["siege_phase_time_modifier_raw"], 0)
                    self.assertIsNone(candidate["unavailable_reason"])
                    self.assertNotIn("target_roll_bounds", candidate)
                    self.assertNotEqual(role["character_id"], candidate["character_id"])
                    self.assertEqual(movement["schema"], movement_schema)
                    self.assertEqual(movement["source"], "native_selected_cunit_movement_rates")
                    self.assertEqual(movement["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(movement["date_raw"], DATE_RAW)
                    self.assertIs(movement["context_observable"], True)
                    self.assertEqual(movement["public_cunit_id"], ARMY_ID)
                    self.assertEqual(movement["native_carmy_id"], NATIVE_ARMY_ID)
                    self.assertEqual(movement["owner_character_id"], PLAYER_ID)
                    self.assertEqual(movement["current_commander_character_id"],
                                     expected["current_commander"]["character_id"])
                    self.assertEqual(movement["current_province_id"], 2669)
                    self.assertEqual(movement["route_read_status"], "complete_empty")
                    self.assertEqual(movement["route_source_count"], 0)
                    for kind, getter in getters.items():
                        rate = movement[kind]
                        self.assertEqual(rate["native_getter_rva"], getter)
                        self.assertEqual(rate["scale"], 100000)
                        if kind == "current_edge":
                            self.assertEqual(rate["status"], "not_applicable")
                            self.assertIsNone(rate["raw"])
                            self.assertEqual(rate["unavailable_reason"], "empty_route")
                        else:
                            self.assertEqual(rate["status"], "available")
                            self.assertIs(type(rate["raw"]), int)
                            self.assertEqual(rate["raw"], {"land": 125000, "naval": 250000}[kind])
                            self.assertIsNone(rate["unavailable_reason"])
                    # These are assertion projections only. Neither the wire
                    # nor the result sent into production ingest is modified.
                    preserved_scenes.append({
                        "current_commander": expected["current_commander"],
                        "candidates": expected["candidates"],
                        "target_province_id": target,
                        "movement_context": {
                            name: value for name, value in movement.items()
                            if name not in {"schema", "land", "naval", "current_edge"}
                        },
                        "movement_rates": {
                            kind: {name: value for name, value in movement[kind].items()
                                   if name != "native_getter_rva"}
                            for kind in getters
                        },
                    })
                    occurrences.append({
                        "wire": str(native_dir / filename),
                        "provenance": "native whole command_result",
                        "status": "GREEN", "step": step,
                        "parent_schema": parent_schema, "movement_schema": movement_schema,
                        "getters": getters,
                        "current_role_status": expected["current_commander"]["status"],
                        "rate_raw": {kind: movement[kind]["raw"] for kind in getters},
                    })
                finally:
                    driver.endpoint.close()

            async def consume():
                for filename, parent_schema, movement_schema, getters in PACKETS:
                    packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                    self.assertIs(packet["ok"], True)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertEqual(packet["protocol_version"], 1)
                    envelope = packet["result"]
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["query_sequence"], 7)
                    await replay(filename, packet, parent_schema, movement_schema, getters)

            asyncio.run(consume())
            self.assertEqual(len(occurrences), 2)
            self.assertEqual(preserved_scenes[0], preserved_scenes[1])
            report["status"] = "GREEN"
            report["readiness"] = "static-ready"
        except Exception as error:
            report["failure"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
