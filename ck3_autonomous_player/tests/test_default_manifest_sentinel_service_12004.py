"""One whole native consumer of default actual4 manifest/sentinel MCP routes.

Four original compiled packets are required. Only transport/default capability
advertisement and the paused frame are synthetic; driver state and history are
initialized and consumed through production code. Root owns qualification.
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
TARGET_DATE_RAW = 53236632
PLAYER_ID = 29829
ARMY_ID = 83886367
GAME_VERSION = "1.20.0.4"
EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
MANIFEST_STEP = "query-loaded-feature-manifest-v1"
ARM_STEP = (
    "research-arm-tactical-daily-sentinel-v1-53236608-to-53236632-"
    "speed-1-mode-terminal-a-1-83886367"
)
CANCEL_STEP = "research-cancel-tactical-daily-sentinel-v1-generation-1"
STATUS_STEP = "research-query-tactical-daily-sentinel-v1"
ARM_CAPABILITY = "game.command.research-arm-tactical-daily-sentinel-v1-N"
CANCEL_CAPABILITY = "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"
PACKETS = (
    ("01-loaded-feature-manifest.json", MANIFEST_STEP),
    ("02-sentinel-arm.json", ARM_STEP),
    ("03-sentinel-cancel.json", CANCEL_STEP),
    ("04-sentinel-status-idle.json", STATUS_STEP),
)


def _load_implementation():
    projection = Path(os.environ.get(
        "XAR_DEFAULT_MANIFEST_SENTINEL_PROJECTION_ROOT",
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
        "version_identity", "loaded_feature_manifest_contract", "native_driver",
        "service", "mcp_server",
    ):
        fullname = f"xar_autoplayer.bridge.{name}"
        module = (
            importlib.reload(sys.modules[fullname]) if fullname in sys.modules
            else importlib.import_module(fullname)
        )
        expected = projection / f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"default whole consumer loaded outside adopted actual4 tree: {name}")
        loaded[name] = module
    return loaded


def _replay_driver(modules, packets):
    native = modules["native_driver"]
    manifest = modules["loaded_feature_manifest_contract"]

    class WholePacketEndpoint:
        pipe_name = native.DEFAULT_PIPE_NAME

        def __init__(self):
            self.requests = []
            self.delivered_frames = []
            self.on_frame = None

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def send(self, request):
            index = len(self.requests)
            filename, expected_step, packet = packets[index]
            if request["step"] != expected_step:
                raise AssertionError(f"unexpected native request for original wire {filename}")
            self.requests.append(deepcopy(request))
            response = deepcopy(packet)
            # Transport correlation only; every native result field is intact.
            response["request_id"] = request["request_id"]
            self.delivered_frames.append(deepcopy(response))
            self.on_frame(response)

        def close(self):
            pass

    class PausedFrameNativeDriver(native.NativeHeadlessGameplayDriver):
        def __init__(self):
            self.scope = {
                "format_version": 1, "source": "named-pipe",
                "backend_id": "native-headless",
                "snapshot_id": "synthetic-paused-default-manifest-sentinel-actual4:11",
                "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
                "date_raw": DATE_RAW, "speed": 1, "paused": True, "map_ready": True,
                "phase": "map_hud", "episode_run_id": "synthetic-native-player-29829",
                "played_character": {"character_id": PLAYER_ID, "alive": True},
                "player_armies": [{
                    "army_id": ARMY_ID, "native_carmy_id": 50331794,
                    "owner_character_id": PLAYER_ID, "controllable": True,
                    "current_province_id": 2669, "retreating": False,
                }],
                "active_wars": [],
                "diagnostics": {"hello": {
                    "game_version": GAME_VERSION,
                    "expected_ck3_version": GAME_VERSION,
                    "expected_ck3_sha256": EXE_SHA256,
                }},
            }
            super().__init__(endpoint=WholePacketEndpoint(), command_timeout_seconds=1.0)

        def take_snapshot(self):
            return deepcopy(self.scope)

        def capabilities(self):
            # Advertise existing default generic templates only. Concrete
            # fixture arm/cancel actions must be admitted by production code.
            advertised = [
                manifest.QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
                ARM_CAPABILITY, CANCEL_CAPABILITY,
                "game.command.research-query-tactical-daily-sentinel-v1",
            ]
            return {
                "backend_id": "native-headless", "bridge_capabilities": advertised,
                "action_steps": native._action_steps(
                    advertised, player_armies=self.scope["player_armies"], paused=True,
                ),
            }

    return PausedFrameNativeDriver()


def _expected_sentinel_status(state):
    """Hardcoded native scene values, used only as assertion expectations."""
    return {
        "state": state, "generation": 1,
        "starting_date_raw": DATE_RAW, "target_date_raw": TARGET_DATE_RAW,
        "last_observed_date_raw": DATE_RAW, "trigger_date_raw": 0,
        "speed": 1, "mode": "terminal_or_sentinel", "army_count": 1,
        "combat_count": 0, "completed_daily_ticks": 0,
        "intermediate_pause_count": 0, "trigger_flags": 0, "trigger_reasons": [],
        "signed_date_delta_from_target_raw": 0, "overshoot_days": -1,
        "pause_wrapper_called": False, "pause_observed": False,
        "terminal_observed": False, "abnormal": False,
    }


class DefaultManifestSentinelServiceTests(unittest.TestCase):
    def test_whole_native_default_routes_registered_mcp_compound(self):
        native_dir_value = os.environ.get("XAR_DEFAULT_MANIFEST_SENTINEL_NATIVE_DIR")
        if not native_dir_value:
            print("NOT RUN: XAR_DEFAULT_MANIFEST_SENTINEL_NATIVE_DIR is unset; original native whole packets required")
            self.skipTest("NOT RUN: compiled actual4 default manifest/sentinel packets unavailable")
        native_dir = Path(native_dir_value)
        report_path = Path(os.environ.get(
            "XAR_DEFAULT_MANIFEST_SENTINEL_SERVICE_REPORT",
            str(native_dir / "default-manifest-sentinel-service-compound-result.json"),
        ))
        occurrences = []
        report = {
            "schema": "default-manifest-sentinel-service-compound-12004-v1",
            "status": "RED", "test_method_count": 1,
            "native_packet_count": 4, "derived_packet_count": 0,
            "native_body_rows_replaced": False, "payload_resigned": False,
            "concrete_arm_cancel_advertisements_added": False,
            "driver_state_or_history_replaced": False,
            "fake_boundary": "transport/default capability advertisements and paused player frame only",
            "game_touched": False, "daily_ticks_executed": 0,
            "live_validation": False, "occurrences": occurrences,
        }
        driver = None
        try:
            packets = []
            for filename, step in PACKETS:
                packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(packet["result"]["step"], step)
                self.assertIs(packet["result"]["accepted"], True)
                packets.append((filename, step, packet))
            modules = _load_implementation()
            report["loaded_module_paths"] = {
                name: str(module.__file__) for name, module in modules.items()
            }
            driver = _replay_driver(modules, packets)
            advertised = driver.capabilities()
            self.assertIn(ARM_CAPABILITY, advertised["bridge_capabilities"])
            self.assertIn(CANCEL_CAPABILITY, advertised["bridge_capabilities"])
            self.assertNotIn(ARM_STEP, advertised["action_steps"])
            self.assertNotIn(CANCEL_STEP, advertised["action_steps"])
            self.assertIn(STATUS_STEP, advertised["action_steps"])
            self.assertEqual(driver._command_history, [])
            report["default_advertisements"] = deepcopy(advertised)
            server = modules["mcp_server"].create_server(driver)

            async def consume():
                tools = {tool.name: tool for tool in await server.list_tools()}
                typed = tools["ck3_query_loaded_feature_manifest_v1"]
                self.assertEqual(set(typed.input_schema["properties"]), {"expected_revision"})
                self.assertEqual(typed.input_schema["required"], ["expected_revision"])
                raw = tools["ck3_execute_step"]
                self.assertEqual(set(raw.input_schema["properties"]), {
                    "step", "expected_revision", "expected_h2743_frame",
                })
                self.assertEqual(raw.input_schema["required"], ["step"])
                for index, (filename, step, packet) in enumerate(packets):
                    original = packet["result"]
                    if index == 0:
                        response = await server.call_tool("ck3_query_loaded_feature_manifest_v1", {
                            "expected_revision": PUBLIC_REVISION,
                        })
                    else:
                        response = await server.call_tool("ck3_execute_step", {
                            "step": step, "expected_revision": PUBLIC_REVISION,
                        })
                    self.assertFalse(getattr(response, "is_error", getattr(response, "isError", False)))
                    observed = response.structured_content
                    self.assertIsInstance(observed, dict)
                    # Every field in the original native command.result is
                    # preserved. Existing production projections may add metadata.
                    self.assertEqual({name: observed[name] for name in original}, original)
                    delivered = driver.endpoint.delivered_frames[index]
                    self.assertEqual(delivered["result"], original)
                    self.assertEqual(len(driver.endpoint.requests), index + 1)
                    request = driver.endpoint.requests[index]
                    self.assertEqual(request["step"], step)
                    self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                    self.assertEqual(len(driver._command_history), index + 1)
                    history = driver._command_history[index]
                    self.assertEqual(history["command"], step)
                    self.assertIs(history["ok"], True)
                    self.assertEqual({name: history["result"][name] for name in original}, original)
                    self.assertEqual(observed["backend_id"], "native-headless")
                    if index == 0:
                        leaf = original["loaded_feature_manifest"]
                        self.assertEqual(observed["loaded_feature_manifest"], leaf)
                        self.assertEqual(leaf["schema"], "loaded-feature-manifest-v1")
                        self.assertEqual(leaf["schema_version"], 1)
                        self.assertEqual(leaf["status"], "available")
                        self.assertEqual(leaf["snapshot_revision"], NATIVE_REVISION)
                        self.assertEqual(leaf["date_raw"], DATE_RAW)
                        self.assertEqual(leaf["build"], {"version": GAME_VERSION, "exe_sha256": EXE_SHA256})
                        self.assertEqual(leaf["provenance"], {
                            "feature_root_slot_rva": "0x5CB87F8",
                            "feature_bitset_rva": "root+0x2B0",
                            "feature_enum_table_rva": "0x47334D0..0x4733580",
                            "script_dlc_set_rva": "0x5CC15E0",
                            "backend_id": "ck3-1.20.0.4-native-loaded-feature-manifest-v1",
                        })
                        flags = leaf["effective_feature_flags"]
                        self.assertEqual(flags["native_count"], 44)
                        self.assertEqual(len(flags["items"]), 44)
                        self.assertEqual([row["native_index"] for row in flags["items"]], list(range(44)))
                        self.assertEqual([row["native_index"] for row in flags["items"] if row["enabled"]], [0, 5, 43])
                        self.assertEqual(leaf["script_dlc_keys"]["enumerated_count"], 3)
                        self.assertEqual(leaf["script_dlc_keys"]["keys"], ["A Flavor Pack", "The Royal Court", "É Pack"])
                        self.assertEqual(leaf["entitlements"], {
                            "status": "unavailable", "unavailable_reason": "store_verdict_provenance_unclosed",
                            "items": None,
                        })
                        self.assertEqual(leaf["readiness"], {
                            "effective_feature_flags_ready": True, "script_dlc_keys_ready": True,
                            "entitlements_ready": False, "same_frame_ready": True, "actionable_ready": True,
                        })
                        self.assertEqual(observed["scope"], "exact-loaded-feature-manifest")
                        self.assertEqual(observed["binding"]["revision"], PUBLIC_REVISION)
                        self.assertEqual(observed["binding"]["native_revision"], NATIVE_REVISION)
                        self.assertEqual(observed["binding"]["date_raw"], DATE_RAW)
                        self.assertIs(observed["loaded_feature_manifest_ready"], True)
                    else:
                        # Sentinel raw packets omit backend_id; only the real
                        # primitive's established backend annotation is added.
                        self.assertEqual(set(observed), set(original) | {"backend_id"})
                        self.assertEqual(history["result"], observed)
                        if index in {1, 3}:
                            self.assertEqual(original["status"], "available")
                            self.assertEqual(original["tactical_daily_sentinel"],
                                             _expected_sentinel_status("armed" if index == 1 else "idle"))
                        else:
                            self.assertEqual(original["status"], "canceled")
                            self.assertNotIn("tactical_daily_sentinel", original)
                    occurrences.append({
                        "wire": str(native_dir / filename), "status": "GREEN", "step": step,
                        "provenance": "original full native command_result",
                        "native_result": deepcopy(original),
                        "registered_mcp_result": deepcopy(observed),
                    })

            asyncio.run(consume())
            self.assertEqual(len(occurrences), 4)
            self.assertEqual([row["step"] for row in driver.endpoint.requests], [step for _, step in PACKETS])
            report["command_history"] = deepcopy(driver._command_history)
            report["status"] = "GREEN"
            report["readiness"] = "static-ready"
        except Exception as error:
            report["failure"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            if driver is not None:
                driver.endpoint.close()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
