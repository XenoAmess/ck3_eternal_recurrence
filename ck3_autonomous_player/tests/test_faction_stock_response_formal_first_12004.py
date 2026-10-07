"""One new offline formal-selection compound; Root supplies retained native wholes.

Original whole bodies remain original. Controlled comparison cases explicitly
change synthetic treasury or stock-watch input; those are not native captures.
No game, SDK server, process operation, native producer or previous test runs.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
import unittest
from unittest.mock import patch

CONFIG = None


class OfflineEndpoint:
    pipe_name = r"\\.\pipe\faction-stock-response-formal-first-offline"

    def __init__(self, wires):
        self.wires = wires
        self.on_frame = None
        self.requests = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, frame):
        self.requests.append(deepcopy(frame))
        if frame.get("type") != "execute_step":
            return
        wire = deepcopy(self.wires[frame["step"]])
        wire["request_id"] = frame["request_id"]
        self.publish(wire)

    def transport_error(self):
        return None

    def close(self):
        pass


class FactionStockResponseFormalFirst12004(unittest.TestCase):
    def test_existing_native_stock_threat_changes_real_formal_faction_response(self):
        started = time.perf_counter()
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=False)
        receipt = {
            "schema": "xar.faction-stock-response-formal-first-12004.v1",
            "status": "RED", "live": False, "source_commit": CONFIG.source_commit,
            "source_root": CONFIG.source_root, "method": self._testMethodName,
            "scenes": [], "native_producer_runs": 0, "old_test_runs": 0,
            "game_process_SDK_operations": 0, "game_days_advanced": 0,
            "G2_M4_complete": False,
            "boundary": "Offline endpoint/hello/paused scope/root/checkpoint/building quote/baseline are synthetic. A retains both original whole bodies. B changes treasury only as a controlled comparison input. C is a controlled watch input. D retains original unavailable alert whole. No native body mutation is native evidence.",
        }
        source = Path(CONFIG.source_root)
        project = source / "ck3_autonomous_player"
        sys.path.insert(0, str(source / "tools"))
        sys.path.insert(0, str(project / "src"))
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.player_faction_alerts_contract import QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY
        from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
        from xar_autoplayer.bridge import service as service_module
        import xar_autoplayer.m5_peacetime_proposal_sources_v1 as source_module
        original = {}
        for name in ("alerts-character-member", "gift-preview", "alerts-unavailable"):
            path = Path(CONFIG.native_wire_dir) / (name + ".command-result.json")
            body = path.read_bytes()
            (output / ("retained-" + path.name)).write_bytes(body)
            original[name] = json.loads(body)
        public_step = "query-player-faction-alerts-v1"
        gift_step = "private-query-faction-gift-member-v1"
        try:
            for name in ("original-positive-gift", "controlled-danger-vs-income",
                         "controlled-watch-vs-income", "unavailable-alert-vs-income"):
                scene_dir = output / name
                scene_dir.mkdir()
                alerts = deepcopy(original["alerts-character-member"])
                gift = deepcopy(original["gift-preview"])
                controlled = name != "original-positive-gift"
                gold = 40_000_000 if controlled else 20_000_000
                if controlled:
                    gift["result"]["native"]["observation"]["player_gold_raw"] = gold
                if name == "controlled-watch-vs-income":
                    raw = alerts["result"]["player_faction_alerts"]
                    row = raw["targeting_factions"][0]
                    row["dangerous_by_stock_rule"] = False
                    row["danger_reason"] = "non_peasant_discontent_not_increasing"
                    row["discontent_per_month"]["raw"] = 0
                    row["months_until_max_discontent"] = 0
                    raw["planner_projection"].update({"dangerous": False,
                        "dangerous_faction_ids": [], "watch_faction_ids": [83886083]})
                elif name == "unavailable-alert-vs-income":
                    alerts = deepcopy(original["alerts-unavailable"])
                endpoint = OfflineEndpoint({public_step: alerts, gift_step: gift})
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint, state_dir=scene_dir / "state",
                    command_timeout_seconds=1.0, episode_projection="native_campaign",
                    allow_private_m5_joint_collector=True,
                    allow_private_faction_gift_formal_trial=True,
                    private_faction_round_id="R1")
                try:
                    endpoint.publish({"type": "hello", "protocol_version": 1,
                        "bridge_version": "0.1.0", "pid": 1200401,
                        "session_generation": 0, "game_version": CK3_12004.game_version,
                        "executable_sha256": CK3_12004.executable_sha256,
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                        "capabilities": ["game.state.snapshot", "game.command.life-advance",
                                         QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY]})
                    endpoint.publish({"type": "heartbeat", "protocol_version": 1,
                        "sequence": 1, "g2_faction_gift_mitigation_async_glue_v1": {"private_build": True}})
                    endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                        "snapshot_id": "faction-formal-first:1", "revision": 1,
                        "state": {"phase": "map_hud", "date": "synthetic-not-live",
                            "date_raw": 53175816, "speed": 1, "paused": True, "map_ready": True,
                            "history": [], "active_event": None, "pending_character_interaction": None,
                            "one_life_terminal_reason": None,
                            "played_character": {"character_id": 50331649, "alive": True},
                            "played_character_gold": {"raw": gold, "scale": 100_000},
                            "player_armies": [], "active_wars": [],
                            "episode_run_id": "faction-formal-first-offline"}})
                    snapshot = driver.take_snapshot()
                    root = {"status": "available", "snapshot_revision": snapshot["native_revision"],
                        "date_raw": snapshot["date_raw"], "player_character_id": 50331649,
                        "player_character_alive": True, "government": {"key": "feudal_government"},
                        "player_targeting_faction_count": 1, "direct_landed_vassal_character_ids": [67108866]}
                    with driver._history_lock:
                        driver._command_history = [{"command": "query-campaign-root-context-v1",
                            "ok": True, "result": {"status": "available", "campaign_root_context": root}}]
                    with driver._driver_state_lock:
                        driver._last_checkpoint = {"status": "saved", "sha256": "a" * 64,
                            "date_raw": snapshot["date_raw"], "episode_run_id": snapshot["episode_run_id"]}
                    building = {"status": "selected" if controlled else "no_legal_budgeted_building",
                        "world": {"player_gold_raw": gold},
                        "source_frame": {**observed_frame(snapshot), "actor_character_id": 50331649}}
                    if controlled:
                        building["candidate"] = {"barony_title_id": 501, "province_id": 601,
                            "building_type_id": 701, "slot_index": 1,
                            "stock_gold_cost_raw": 3_000_000, "gold_before_raw": gold,
                            "authored_monthly_income_hundredths": 35}
                    baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                        "selected_step": "life-advance", "reason": "synthetic ordinary baseline"}
                    with patch.object(service_module, "choose_one_life_turn", return_value=baseline), \
                            patch.object(source_module, "query_construction_private", return_value=building):
                        planned = GameplayBridgeService(driver).plan_turn()
                    plan = planned["plan"]
                    receipt["last_plan"] = planned
                    receipt["last_requests"] = deepcopy(endpoint.requests)
                    self.assertIn("m5_joint_query_only", plan, json.dumps(plan))
                    dispatch = plan["m5_joint_query_only"]["dispatch"]
                    should_gift = name in {"original-positive-gift", "controlled-danger-vs-income"}
                    self.assertEqual(plan["selected_step"], "private-submit-faction-gift-member-v1"
                                     if should_gift else "private-submit-player-construction-v1")
                    self.assertIs(plan["m5_joint_formal_action_ready"], True)
                    rows = dispatch["analysis"]["evaluated"]
                    faction = next(row for row in rows if row["domain"] == "diplomacy")
                    threat = faction["evidence"]["stock_threat_response"]
                    self.assertIs(threat["exact_ultimatum_timing_ready"], False)
                    if should_gift:
                        self.assertEqual(threat["native_row"], original["alerts-character-member"]
                                         ["result"]["player_faction_alerts"]["targeting_factions"][0])
                        self.assertIs(threat["dangerous_response_ready"], True)
                        self.assertEqual(threat["native_row"]["months_until_max_discontent"], 20)
                    else:
                        self.assertIs(threat["dangerous_response_ready"], False)
                    self.assertEqual(sum(request.get("step") == public_step for request in endpoint.requests), 1)
                    self.assertFalse(any(str(request.get("step", "")).startswith("private-submit")
                                         for request in endpoint.requests))
                    if not controlled:
                        self.assertEqual(endpoint.wires[gift_step], original["gift-preview"])
                        self.assertEqual(endpoint.wires[public_step], original["alerts-character-member"])
                    scene = {"case": name, "status": "GREEN", "controlled_input": controlled,
                        "plan": planned, "requests": endpoint.requests,
                        "alert_input": endpoint.wires[public_step], "gift_input": endpoint.wires[gift_step]}
                    (scene_dir / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
                    receipt["scenes"].append({"case": name, "status": "GREEN",
                        "selected_step": plan["selected_step"], "dangerous_response_ready": threat["dangerous_response_ready"],
                        "alert_reads": 1, "actual_submit_calls": 0})
                finally:
                    driver.close()
            receipt["status"] = "GREEN"
        except Exception:
            receipt["traceback"] = traceback.format_exc()
            raise
        finally:
            receipt["elapsed_seconds"] = time.perf_counter() - started
            receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            (output / "FIRST-COMPOUND-RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for argument in ("source-root", "source-commit", "native-wire-dir", "output-dir"):
        parser.add_argument("--" + argument, required=True)
    CONFIG = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FactionStockResponseFormalFirst12004)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
