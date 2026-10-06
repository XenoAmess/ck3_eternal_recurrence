"""One compound registered-MCP replay of seven genuine whole native queries.

No native candidate row is constructed or replaced here. The only derived
packet is the explicitly labeled null-compatibility variant of scene 07.
Without XAR_COMMANDER_TARGET_ROLL_NATIVE_DIR this test is NOT RUN, not GREEN.
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


SCENES = (
    "01-target-distinguishes-candidates",
    "02-separate-negative-truncation",
    "03-available-zero-negative",
    "04-target-failure-independent-pool",
    "05-one-modifier-failure",
    "06-complete-empty-target",
    "07-legacy-omission",
)
PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53236608
ARMY_ID = 83886367
PLAYER_ID = 29829
SOURCE = "native_current_candidate_target_roll_context"


def _load_implementation() -> dict[str, object]:
    """Load the external projection while resolving untouched baseline modules."""
    projection = Path(os.environ.get(
        "XAR_COMMANDER_TARGET_ROLL_PROJECTION_ROOT", str(Path(__file__).resolve().parents[2])
    )).resolve()
    baseline = Path(os.environ.get(
        "XAR_COMMANDER_TARGET_ROLL_BASELINE_ROOT", str(projection)
    )).resolve()
    sys.path.insert(0, str(baseline / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge as bridge

    bridge.__path__.insert(0, str(
        projection / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    ))
    loaded = {}
    for name in (
        "army_commander_target_rolls", "army_commander_candidates",
        "native_driver", "service", "mcp_server",
    ):
        fullname = f"xar_autoplayer.bridge.{name}"
        module = (
            importlib.reload(sys.modules[fullname]) if fullname in sys.modules
            else importlib.import_module(fullname)
        )
        expected = projection / f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"compound replay loaded a baseline module: {name}")
        loaded[name] = module
    return loaded


def _replay_driver(modules: dict[str, object], packet: dict[str, object]):
    """Replace transport and its paused snapshot, retain the production driver."""
    contract = modules["army_commander_candidates"]
    native = modules["native_driver"]

    class PacketEndpoint:
        pipe_name = native.DEFAULT_PIPE_NAME

        def __init__(self):
            self.requests = []
            self.on_frame = None

        def start(self, on_frame, on_disconnect):
            # The real driver constructor supplies _ingest. It creates the
            # real NativeProtocolState before registering this callback.
            self.on_frame = on_frame

        def send(self, request):
            self.requests.append(deepcopy(request))
            # The native result, including every row, is unchanged. Only the
            # transport correlation ID follows this production submission.
            response = deepcopy(packet)
            response["request_id"] = request["request_id"]
            # Synchronous delivery enters the real state command-result cache
            # before wait_for_command_result. This query needs no hello,
            # descriptor or semantic-state ingestion: its paused snapshot and
            # transport advertisement are the explicit fake boundaries.
            self.on_frame(response)

        def close(self):
            pass

    class PausedSnapshotReplay(native.NativeHeadlessGameplayDriver):
        def __init__(self):
            self.replay_frame = {
                "paused": True, "map_ready": True, "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
                "snapshot_id": "synthetic-paused-commander-target-roll:11",
                "played_character": {"character_id": PLAYER_ID, "alive": True},
                "player_armies": [{
                    "army_id": ARMY_ID, "controllable": True,
                    "owner_character_id": PLAYER_ID,
                }],
                "active_wars": [],
            }
            super().__init__(endpoint=PacketEndpoint(), command_timeout_seconds=1.0)

        def take_snapshot(self):
            return deepcopy(self.replay_frame)

        def capabilities(self):
            # This is the fake transport's advertisement. Concrete action
            # projection still uses the production native_driver helper.
            advertised = [
                contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_FOR_TARGET_CAPABILITY,
            ]
            return {
                "bridge_capabilities": advertised, "backend_id": "native-headless",
                "action_steps": native._action_steps(
                    advertised, player_armies=self.replay_frame["player_armies"],
                    paused=True,
                ),
            }

    return PausedSnapshotReplay()


class CommanderCandidateTargetRollServiceTests(unittest.TestCase):
    def test_whole_native_query_registered_mcp_compound(self):
        native_dir_value = os.environ.get("XAR_COMMANDER_TARGET_ROLL_NATIVE_DIR")
        if not native_dir_value:
            print("NOT RUN: XAR_COMMANDER_TARGET_ROLL_NATIVE_DIR is unset; seven native wires required")
            self.skipTest("NOT RUN: genuine whole native commander query wires unavailable")
        native_dir = Path(native_dir_value)
        report_path = Path(os.environ.get(
            "XAR_COMMANDER_TARGET_ROLL_SERVICE_REPORT",
            str(native_dir / "service-compound-result.json"),
        ))
        reports = []
        report = {
            "schema": "commander-target-roll-service-compound-v1",
            "status": "RED", "test_method_count": 1,
            "native_scene_count": 7, "derived_synthetic_variant_count": 1,
            "fake_boundary": "transport endpoint, capability advertisement and paused snapshot",
            "native_candidate_rows_replaced": False,
            "live_validation": False, "local_ck3_touched": False,
            "scenes": reports,
        }
        try:
            modules = _load_implementation()
            report["loaded_modules"] = {
                name: str(module.__file__) for name, module in modules.items()
            }
            contract = modules["army_commander_candidates"]

            async def replay(scene: str, packet: dict[str, object], *, derived: bool = False):
                expected = packet["result"]["army_commander_candidates"]
                target = expected.get("target_province_id")
                driver = _replay_driver(modules, packet)
                server = modules["mcp_server"].create_server(driver)
                try:
                    tools = await server.list_tools()
                    tool = next(row for row in tools if row.name == "ck3_query_army_commander_candidates_v1")
                    properties = tool.input_schema["properties"]
                    self.assertIn("expected_revision", properties)
                    self.assertIn("target_province_id", properties)
                    self.assertEqual(tool.input_schema["required"], ["army_id"])
                    target_schema = properties["target_province_id"]
                    numeric = next((item for item in target_schema.get("anyOf", [target_schema])
                                    if item.get("type") == "integer"), None)
                    self.assertIsNotNone(numeric)
                    self.assertEqual(numeric["minimum"], 1)
                    self.assertEqual(numeric["maximum"], 2**31 - 1)
                    self.assertTrue(getattr(tool.annotations, "read_only_hint",
                                           getattr(tool.annotations, "readOnlyHint", False)))
                    arguments = {"army_id": ARMY_ID, "expected_revision": PUBLIC_REVISION}
                    if target is not None:
                        arguments["target_province_id"] = target
                    response = await server.call_tool("ck3_query_army_commander_candidates_v1", arguments)
                    self.assertFalse(getattr(response, "is_error", getattr(response, "isError", False)))
                    observed = response.structured_content
                    self.assertIsInstance(observed, dict)
                    # Equality covers the original pool, eligibility, quality,
                    # current selected-unit fields and the independent leaf.
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
                    self.assertEqual(contract.parse_query_army_commander_candidates_v1_for_target_step(step),
                                     (ARMY_ID, target) if target is not None else None)
                    self.assertEqual(contract.parse_query_army_commander_candidates_v1_step(step),
                                     ARMY_ID if target is None else None)
                    self.assertEqual(expected["status"], "available")
                    self.assertTrue(expected["candidate_collection_complete"])
                    self.assertEqual(expected["candidate_source_count"], len(expected["candidates"]))
                    self.assertEqual(expected["eligibility_mode"], 1)
                    self.assertIs(expected["collection_filter_now"], False)
                    self.assertIs(expected["collection_allow_guests"], True)
                    rows = expected["candidates"]
                    if scene.startswith("06-"):
                        self.assertEqual(rows, [])
                        self.assertIsNotNone(target)
                    else:
                        self.assertEqual(len(rows), 2)
                        self.assertEqual([row["can_assign"] for row in rows], [True, False])
                        self.assertTrue(all(row["character_id"] is not None for row in rows))
                        self.assertTrue(all(row["final_eligibility_observable"] for row in rows))
                        self.assertTrue(all(row["quality_observable"] for row in rows))
                    if scene.startswith("07-"):
                        if derived:
                            self.assertIsNone(expected["target_province_id"])
                            self.assertTrue(all(row["target_roll_bounds"] is None for row in rows))
                        else:
                            self.assertNotIn("target_province_id", expected)
                            self.assertTrue(all("target_roll_bounds" not in row for row in rows))
                    else:
                        self.assertIs(type(target), int)
                        for row in rows:
                            leaf = row["target_roll_bounds"]
                            self.assertEqual(leaf["source"], SOURCE)
                            self.assertEqual(leaf["source_target_province_id"], target)
                            if leaf["status"] == "available":
                                self.assertIsNone(leaf["unavailable_reason"])
                                for name in ("effective_min_roll", "effective_max_roll"):
                                    self.assertIs(type(leaf[name]), int)
                                    self.assertTrue(-(2**31) <= leaf[name] <= 2**31 - 1)
                            else:
                                self.assertEqual(leaf["status"], "unavailable")
                                self.assertIsNone(leaf["effective_min_roll"])
                                self.assertIsNone(leaf["effective_max_roll"])
                                self.assertIsInstance(leaf["unavailable_reason"], str)
                                self.assertTrue(leaf["unavailable_reason"].strip())
                        expected_bounds = {
                            "01-target-distinguishes-candidates": [(-2, 13), (2, 9)],
                            "02-separate-negative-truncation": [(0, 10), (-1, 10)],
                            "03-available-zero-negative": [(0, 0), (-3, -1)],
                            "04-target-failure-independent-pool": [None, None],
                            "05-one-modifier-failure": [None, (0, 10)],
                            "06-complete-empty-target": [],
                        }[scene]
                        actual_bounds = [
                            (row["target_roll_bounds"]["effective_min_roll"],
                             row["target_roll_bounds"]["effective_max_roll"])
                            if row["target_roll_bounds"]["status"] == "available" else None
                            for row in rows
                        ]
                        self.assertEqual(actual_bounds, expected_bounds)
                        if scene.startswith("01-"):
                            self.assertEqual(rows[0]["native_ai_base_quality"], rows[1]["native_ai_base_quality"])
                            self.assertEqual(rows[0]["generic_advantage_points"], rows[1]["generic_advantage_points"])
                    reports.append({
                        "scene": scene, "status": "GREEN",
                        "provenance": "derived synthetic compatibility variant" if derived else "native whole query",
                        "native_wire": str(native_dir / f"{SCENES[6] if derived else scene}.json"),
                        "step": step,
                    })
                finally:
                    driver.endpoint.close()

            async def check_compound():
                legacy = None
                for scene in SCENES:
                    path = native_dir / f"{scene}.json"
                    packet = json.loads(path.read_text(encoding="utf-8-sig"))
                    self.assertIs(packet["ok"], True)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertEqual(packet["protocol_version"], 1)
                    envelope = packet["result"]
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["army_commander_candidates"]["army_id"], ARMY_ID)
                    self.assertEqual(envelope["army_commander_candidates"]["owner_character_id"], PLAYER_ID)
                    with self.subTest(native_scene=scene):
                        await replay(scene, packet)
                    if scene == SCENES[6]:
                        legacy = packet
                # Sole permitted row alteration: an openly synthetic null
                # compatibility variant derived from the genuine legacy wire.
                null_variant = deepcopy(legacy)
                null_frame = null_variant["result"]["army_commander_candidates"]
                null_frame["target_province_id"] = None
                for row in null_frame["candidates"]:
                    row["target_roll_bounds"] = None
                with self.subTest(derived_synthetic_variant="07-explicit-null-compatibility"):
                    await replay("07-derived-synthetic-explicit-null-compatibility", null_variant, derived=True)

            asyncio.run(check_compound())
            self.assertEqual(len(reports), 8)
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
