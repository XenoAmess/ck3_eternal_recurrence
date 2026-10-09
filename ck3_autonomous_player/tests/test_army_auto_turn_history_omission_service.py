"""One new auto-turn dispatch compound using an already qualified native whole.

Only the selected plan and endpoint lifecycle are synthetic. No producer or
older test is executed; the prior consumer supplies reusable endpoint helpers.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import traceback
import unittest
from unittest.mock import patch

from test_army_normal_turn_callback_service import (
    _RetainedNativeWholeEndpoint,
    _assert_native_values,
    _write_json,
)


_OPTIONS = None
_SCENE = "arrival_distinct_province"
_STEP = "query-army-strengths-v1"


class ArmyAutoTurnHistoryOmissionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_auto_turn_preserves_whole_and_complete_history_without_export_copy(self):
        if _OPTIONS is None:
            raise RuntimeError("use this compound's explicit readonly CLI")
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

        output = _OPTIONS.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        wire = _OPTIONS.native_wire.resolve()
        packet = json.loads(wire.read_text(encoding="utf-8-sig"))
        whole = packet["samples"][_SCENE]
        native = whole["result"]
        sidecar = json.loads((wire.parent / (_SCENE + ".native-context.json"))
                             .read_text(encoding="utf-8-sig"))
        context = sidecar["synthetic_context"]
        armies = sidecar["current_army_context"]
        receipt = {
            "status": "RED", "native_wire": str(wire), "new_compounds": 1,
            "native_producer_executions": 0, "old_tests_executed": 0,
            "synthetic_boundary": "selected plan, hello/paused transport, request correlation",
            "business_path": "registered ck3_auto_turn -> real Service dispatch -> real NativeHeadless driver",
            "game_or_live_sdk_used": False, "live_speedup_measured": False,
        }
        endpoint = _RetainedNativeWholeEndpoint("history_omission", whole)
        driver = None
        try:
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                state_dir=output / "synthetic-state", episode_projection="native_campaign")
            server = create_server(driver)
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": context["bridge_host_pid"], "connection_generation": 1,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": context["snapshot_id"], "revision": context["native_revision"],
                "state": {
                    "phase": "map_hud", "date": "synthetic-current-not-live",
                    "date_raw": context["date_raw"], "speed": 1, "paused": True,
                    "map_ready": True, "history": [], "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {"character_id": context["actor_character_id"], "alive": True},
                    "player_armies": deepcopy(armies), "active_wars": [],
                },
            })
            before = driver.take_snapshot_without_native_command_history()
            old_history = [{
                "index": index, "command": "query-synthetic-history", "ok": True,
                "result": {"ordered_rows": [{"z": index, "a": None}],
                           "unresolved_intent": {"status": "action_state_unknown", "ack": None}},
            } for index in range(1, 9)]
            with driver._history_lock:
                driver._command_history = deepcopy(old_history)
            planned = {
                "snapshot_id": before["snapshot_id"], "revision": before["revision"],
                "plan": {"phase": "synthetic-selected-army-query", "selected_step": _STEP},
            }
            with (
                patch.object(GameplayBridgeService, "plan_turn", return_value=planned),
                patch.object(driver, "_history_snapshot", wraps=driver._history_snapshot) as copies,
            ):
                registered = await server.call_tool("ck3_auto_turn", {})
                _write_json(output / "actual-registered-response.json",
                            registered.model_dump(mode="json", by_alias=True))
                self.assertIs(registered.is_error, False)
                outcome = registered.structured_content
                self.assertEqual(outcome["status"], "executed")
                self.assertEqual(outcome["selected_step"], _STEP)
                self.assertEqual(copies.call_count, 0)
                result = outcome["result"]
                _assert_native_values(self, native, result, "registered.result")
                for key in ("snapshot_id", "revision", "native_revision"):
                    self.assertEqual(result["queried_" + key], before[key])
                for key in (
                    "current_callback_supply_risk_v1", "current_callback_soldier_effects_v1",
                    "current_unit_new_date_entry_normalization_v1",
                    "current_unit_next_movement_prefix_v1",
                    "current_unit_next_first_edge_selection_v1",
                    "current_unit_next_arrival_transition_v1",
                    "current_unit_arrival_prestore_disembark_write_v1",
                ):
                    self.assertEqual([row["army_id"] for row in result[key]],
                                     [row["army_id"] for row in native["army_strengths"]])
                # The public default still exports the complete detached history.
                public = driver.take_snapshot()
                self.assertEqual(copies.call_count, 1)
                self.assertEqual(public["native_command_history"][:8], old_history)
                self.assertEqual(len(public["native_command_history"]), 9)
                self.assertEqual(public["native_command_history"][-1]["command"], _STEP)
                self.assertEqual(public["native_command_history"][-1]["result"],
                                 driver._command_history[-1]["result"])
                public["native_command_history"][0]["result"]["ordered_rows"][0]["z"] = -1
                self.assertEqual(driver._command_history[0], old_history[0])
            commands = [row for row in endpoint.requests if row.get("type") == "execute_step"]
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0]["step"], _STEP)
            self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
            driver.close()
            state = json.loads((output / "synthetic-state/native-session/driver-state.json")
                               .read_text(encoding="utf-8"))
            self.assertEqual(state["command_history"][:8], old_history)
            self.assertEqual(len(state["command_history"]), 9)
            self.assertEqual(state["command_history"][-1]["command"], _STEP)
            receipt.update({
                "status": "GREEN", "query_transport_calls": 1,
                "full_history_exports_during_auto_turn": 0,
                "public_default_full_history_export_preserved": True,
                "complete_durable_history_entries": 9,
                "native_business_body_preserved": True,
            })
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            if driver is not None:
                driver.close()
            _write_json(output / "COMPOUND-RECEIPT.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    _OPTIONS = parser.parse_args()
    sys.path.insert(0, str(_OPTIONS.source_root.resolve() / "ck3_autonomous_player/src"))
    unittest.main(argv=[sys.argv[0]], verbosity=2)
