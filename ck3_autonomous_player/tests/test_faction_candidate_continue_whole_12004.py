"""One new registered MCP compound consuming only fresh continuation wholes.

The transport/hello/paused root are synthetic. Production native whole result
bodies, driver, registered query and existing choice policy remain unchanged.
Root alone executes this compound; no native producer or old test is run here.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import unittest

CONFIG = None
SCENES = ("first-native-denied", "first-already-gifted", "first-human", "all-native-denied")


class Endpoint:
    pipe_name = r"\\.\pipe\faction-candidate-continuation-offline"

    def __init__(self, wire):
        self.wire = wire
        self.on_frame = None
        self.requests = []
        self.delivered = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, frame):
        self.requests.append(deepcopy(frame))
        if frame.get("type") != "execute_step":
            return
        if frame["step"] != self.wire["result"]["step"]:
            raise AssertionError("only the new frozen native preview step is supplied")
        reply = deepcopy(self.wire)
        reply["request_id"] = frame["request_id"]
        self.delivered.append(reply)
        self.publish(reply)

    def transport_error(self):
        return None

    def close(self):
        pass


class FactionCandidateContinueWhole12004(unittest.TestCase):
    def test_native_continuation_wholes_reach_registered_candidate_choice(self):
        started = time.perf_counter()
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=False)
        source = Path(CONFIG.source_root)
        for path in (source / "tools", source / "ck3_workshop_mcp" / "src",
                     source / "ck3_autonomous_player" / "src"):
            sys.path.insert(0, str(path))
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.version_identity import CK3_12004

        receipt = {"schema": "xar.faction-candidate-continue-12004.first.v1",
                   "status": "RED", "live": False,
                   "source_commit": CONFIG.source_commit, "scenes": [],
                   "new_registered_mcp_calls": 0, "native_producer_runs": 0,
                   "old_test_runs": 0, "game_sdk_operations": 0,
                   "boundary": "Fresh native fixture whole bodies are retained unchanged; endpoint, process identity, paused snapshot and public root are synthetic. No gift is submitted and no faction outcome is claimed."}
        try:
            for scene in SCENES:
                path = Path(CONFIG.native_wire_dir) / (scene + ".command-result.json")
                body = path.read_bytes()
                wire = json.loads(body)
                (output / path.name).write_bytes(body)
                endpoint = Endpoint(wire)
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint,
                    state_dir=output / scene, command_timeout_seconds=1.0,
                    episode_projection="native_campaign",
                    allow_private_faction_gift_formal_trial=True,
                    private_faction_round_id="R1")
                try:
                    endpoint.publish({"type": "hello", "protocol_version": 1,
                        "bridge_version": "0.1.0", "pid": 1200401, "session_generation": 0,
                        "game_version": CK3_12004.game_version,
                        "executable_sha256": CK3_12004.executable_sha256,
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                        "capabilities": ["game.state.snapshot"]})
                    endpoint.publish({"type": "heartbeat", "protocol_version": 1,
                        "sequence": 1, "g2_faction_gift_mitigation_async_glue_v1": {"private_build": True}})
                    endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                        "snapshot_id": "native:1", "revision": 1,
                        "state": {"phase": "map_hud", "date": "synthetic-not-live",
                            "date_raw": 53175816, "speed": 1, "paused": True, "map_ready": True,
                            "history": [], "active_event": None, "pending_character_interaction": None,
                            "one_life_terminal_reason": None,
                            "played_character": {"character_id": 50331649, "alive": True},
                            "player_armies": [], "active_wars": [],
                            "episode_run_id": "faction-continuation-offline"}})
                    before = driver.take_internal_semantic_snapshot()
                    root = {"snapshot_revision": before["native_revision"], "date_raw": 53175816,
                        "player_character_id": 50331649, "government": {"key": "feudal_government"},
                        "player_targeting_faction_count": 1,
                        "direct_landed_vassal_character_ids": [67108866, 117440516]}
                    driver.allow_private_faction_gift_query = True
                    server = create_server(driver)
                    result = asyncio.run(server.call_tool(
                        "ck3_query_faction_gift_candidate_private_v1",
                        {"expected_revision": before["revision"], "same_frame_root": root,
                         "minimum_gold_reserve_raw": 5000000}))
                    receipt["new_registered_mcp_calls"] += 1
                    self.assertIs(result.is_error, False)
                    observed = result.structured_content
                    self.assertIsInstance(observed, dict)
                    self.assertEqual(json.loads(result.content[0].text), observed)
                    self.assertEqual(observed["observation"], wire["result"]["native"]["observation"])
                    if scene == "all-native-denied":
                        self.assertEqual(observed["status"], "no_legal_candidate")
                        self.assertNotIn("choice", observed)
                    else:
                        self.assertEqual(observed["status"], "selected")
                        self.assertEqual(observed["choice"]["recipient_character_id"], 117440516)
                        self.assertEqual(observed["choice"]["source_faction_id"], 83886083)
                        self.assertEqual(observed["choice"]["membership_role"], "character_member")
                        self.assertEqual(observed["choice"]["gold_cost_raw"], 7500000)
                    self.assertEqual(driver.take_internal_semantic_snapshot(), before)
                    requests = [row for row in endpoint.requests if row.get("type") == "execute_step"]
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(len(endpoint.delivered), 1)
                    delivered = endpoint.delivered[0]
                    self.assertEqual({k: v for k, v in delivered.items() if k != "request_id"},
                                     {k: v for k, v in wire.items() if k != "request_id"})
                    receipt["scenes"].append({"name": scene, "status": "GREEN",
                        "actual_mcp_result": result.model_dump(mode="json", by_alias=True),
                        "transport_requests": requests})
                finally:
                    driver.close()
            self.assertEqual(receipt["new_registered_mcp_calls"], 4)
            receipt["status"] = "GREEN_FIXTURE_ONLY"
        finally:
            receipt["elapsed_seconds"] = time.perf_counter() - started
            receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            (output / "FIRST-CONSUMER-RECEIPT.json").write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--native-wire-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "FactionCandidateContinueWhole12004.test_native_continuation_wholes_reach_registered_candidate_choice",
        sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
