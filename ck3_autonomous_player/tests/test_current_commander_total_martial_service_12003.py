"""One compound Service/MCP consumer of actual whole current-martial wires.

Seven native scenes yield eight original packets (zero and negative are
separate occurrences). Only the labeled legacy-null variant is derived.
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


PACKETS = (
    ("01-current-outside-pool", "01-current-outside-pool.json", 23),
    ("02-current-and-selected-distinct", "02-current-and-selected-distinct.json", 23),
    ("03-current-zero-negative", "03-current-zero-negative-zero.json", 0),
    ("03-current-zero-negative", "03-current-zero-negative-negative.json", -7),
    ("04-current-absent", "04-current-absent.json", None),
    ("05-current-identity-unavailable", "05-current-identity-unavailable.json", None),
    ("06-skill-reader-unavailable", "06-skill-reader-unavailable.json", None),
    ("07-legacy-omission", "07-legacy-omission.json", None),
)
PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53236608
ARMY_ID = 83886367
NATIVE_ARMY_ID = 50331794
PLAYER_ID = 29829
SOURCE = "native_current_assigned_commander_total_skill_cache"


def _load_implementation():
    projection = Path(os.environ.get(
        "XAR_CURRENT_COMMANDER_TOTAL_MARTIAL_PROJECTION_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )).resolve()
    baseline = Path(os.environ.get(
        "XAR_CURRENT_COMMANDER_TOTAL_MARTIAL_BASELINE_ROOT", str(projection),
    )).resolve()
    sys.path.insert(0, str(baseline / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge as bridge

    bridge.__path__.insert(0, str(
        projection / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    ))
    loaded = {}
    for name in (
        "army_commander_current_martial", "army_commander_candidates",
        "native_driver", "service", "mcp_server",
    ):
        fullname = f"xar_autoplayer.bridge.{name}"
        module = (
            importlib.reload(sys.modules[fullname]) if fullname in sys.modules
            else importlib.import_module(fullname)
        )
        expected = projection / f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"compound consumer loaded outside its exact projection: {name}")
        loaded[name] = module
    return loaded


def _replay_driver(modules, packet):
    """Retain production initialization, ingest, execution and result history."""
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
            # Transport correlation only: the complete native result is intact.
            response["request_id"] = request["request_id"]
            self.on_frame(response)

        def close(self):
            pass

    class PausedScopeReplay(native.NativeHeadlessGameplayDriver):
        def __init__(self):
            self.scope = {
                "paused": True, "map_ready": True, "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
                "snapshot_id": "synthetic-paused-current-martial:11",
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
            # Fake transport advertisement; production projection remains used.
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


class CurrentCommanderTotalMartialServiceTests(unittest.TestCase):
    def test_whole_native_query_registered_mcp_compound(self):
        native_dir_value = os.environ.get("XAR_CURRENT_COMMANDER_TOTAL_MARTIAL_NATIVE_DIR")
        if not native_dir_value:
            print("NOT RUN: XAR_CURRENT_COMMANDER_TOTAL_MARTIAL_NATIVE_DIR is unset; actual whole wires required")
            self.skipTest("NOT RUN: actual current-martial native wires unavailable")
        native_dir = Path(native_dir_value)
        report_path = Path(os.environ.get(
            "XAR_CURRENT_COMMANDER_TOTAL_MARTIAL_SERVICE_REPORT",
            str(native_dir / "current-martial-service-compound-result.json"),
        ))
        occurrences = []
        report = {
            "schema": "current-commander-total-martial-service-compound-v1",
            "status": "RED", "test_method_count": 1, "native_scene_count": 7,
            "native_packet_count": 8, "derived_legacy_null_count": 1,
            "native_rows_replaced": False,
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

            async def replay(scene, filename, packet, expected_value, *, derived=False):
                expected = packet["result"]["army_commander_candidates"]
                role = expected["current_commander"]
                target = expected.get("target_province_id")
                driver = _replay_driver(modules, packet)
                server = modules["mcp_server"].create_server(driver)
                try:
                    tools = await server.list_tools()
                    tool = next(row for row in tools if row.name == "ck3_query_army_commander_candidates_v1")
                    properties = tool.input_schema["properties"]
                    self.assertEqual(set(properties), {"army_id", "expected_revision", "target_province_id"})
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
                    # The actual whole frame proves this optional field does
                    # not rewrite candidate/target/movement observations.
                    self.assertEqual(observed["army_commander_candidates"], expected)
                    self.assertEqual(observed["queried_revision"], PUBLIC_REVISION)
                    self.assertEqual(observed["queried_native_revision"], NATIVE_REVISION)
                    self.assertEqual(observed["date_raw"], DATE_RAW)
                    self.assertEqual(observed["query_sequence"], packet["result"]["query_sequence"])
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
                    self.assertEqual(expected["native_carmy_id"], NATIVE_ARMY_ID)
                    self.assertEqual(expected["owner_character_id"], PLAYER_ID)
                    self.assertTrue(expected["candidate_collection_complete"])
                    self.assertEqual(expected["candidate_source_count"], len(expected["candidates"]))
                    self.assertEqual([row["character_id"] for row in expected["candidates"]], [30000, 30001])
                    self.assertEqual(expected["eligibility_mode"], 1)
                    self.assertIs(expected["collection_filter_now"], False)
                    self.assertIs(expected["collection_allow_guests"], True)
                    if scene == "07-legacy-omission":
                        if derived:
                            self.assertIn("current_total_martial", role)
                            self.assertIsNone(role["current_total_martial"])
                        else:
                            self.assertNotIn("current_total_martial", role)
                    else:
                        leaf = role["current_total_martial"]
                        self.assertIsInstance(leaf, dict)
                        self.assertEqual(leaf["source"], SOURCE)
                        self.assertIs(type(leaf["skill_index"]), int)
                        self.assertEqual(leaf["skill_index"], 1)
                        self.assertEqual(leaf["source_character_id"], role["character_id"])
                        if expected_value is not None:
                            self.assertEqual(role["status"], "available")
                            self.assertEqual(role["character_id"], PLAYER_ID)
                            self.assertEqual(leaf["status"], "available")
                            self.assertIs(type(leaf["value"]), int)
                            self.assertEqual(leaf["value"], expected_value)
                            self.assertIsNone(leaf["unavailable_reason"])
                            self.assertNotIn(leaf["source_character_id"],
                                             [row["character_id"] for row in expected["candidates"]])
                        else:
                            self.assertEqual(leaf["status"], "unavailable")
                            self.assertIsNone(leaf["value"])
                            self.assertIsInstance(leaf["unavailable_reason"], str)
                            self.assertTrue(leaf["unavailable_reason"].strip())
                        if scene == "04-current-absent":
                            self.assertEqual(role["status"], "absent")
                            self.assertIsNone(role["character_id"])
                            self.assertIsNone(leaf["source_character_id"])
                            self.assertEqual(leaf["unavailable_reason"], "current_commander_absent")
                        elif scene == "05-current-identity-unavailable":
                            self.assertEqual(expected["status"], "partial")
                            self.assertEqual(role["status"], "unavailable")
                            self.assertEqual(role["character_id"], PLAYER_ID)
                            self.assertEqual(leaf["unavailable_reason"], "current_commander_identity_unavailable")
                        elif scene == "06-skill-reader-unavailable":
                            self.assertEqual(expected["status"], "available")
                            self.assertEqual(role["status"], "available")
                            self.assertEqual(leaf["unavailable_reason"], "current_commander_skill_reader_unavailable")
                            self.assertEqual(target, 2669)
                            self.assertTrue(all("target_roll_bounds" in row for row in expected["candidates"]))
                    occurrences.append({
                        "scene": scene, "wire": str(native_dir / filename),
                        "provenance": "derived synthetic legacy-null compatibility" if derived else "native whole command_result",
                        "status": "GREEN", "step": step,
                        "current_role_status": role["status"],
                        "current_total_martial_value": expected_value,
                    })
                finally:
                    driver.endpoint.close()

            async def consume():
                legacy = None
                for scene, filename, expected_value in PACKETS:
                    packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                    self.assertIs(packet["ok"], True)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertEqual(packet["protocol_version"], 1)
                    envelope = packet["result"]
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["army_commander_candidates"]["army_id"], ARMY_ID)
                    with self.subTest(native_scene=scene, original_wire=filename):
                        await replay(scene, filename, packet, expected_value)
                    if scene == "07-legacy-omission":
                        legacy = packet
                # Only allowed derived alteration, separately labeled in receipt.
                null_variant = deepcopy(legacy)
                null_variant["result"]["army_commander_candidates"]["current_commander"]["current_total_martial"] = None
                with self.subTest(derived_synthetic="07-explicit-null"):
                    await replay("07-legacy-omission", "07-legacy-omission.json",
                                 null_variant, None, derived=True)

            asyncio.run(consume())
            self.assertEqual(len(occurrences), 9)
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
