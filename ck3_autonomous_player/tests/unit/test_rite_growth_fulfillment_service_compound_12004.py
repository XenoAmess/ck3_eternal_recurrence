"""One new ordinary Service compound; native/game effects are in-memory fixtures.

The production Service, current event policy, religion transport and material
comparator execute unchanged. No material metadata is supplied by the fixture.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.player_religion_context_private_transport import (
    query_player_religion_context_private_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.vanilla_events.rite_growth_material import ENDING_FIELD, STARTING_FIELD


def _current_context():
    fixture = Path(__file__).parent / "fixtures" / "rite_growth_event29_nine_scope_12003.json"
    context = json.loads(fixture.read_text(encoding="utf-8"))["context"]
    # Explicit synthetic .4 event source, using the already-reviewed authored
    # shape. Historical artifact provenance is not modified or given live credit.
    context["snapshot_revision"] = 51
    context["provenance"] = {
        "root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC418",
        "manager_offset": "+0x28", "backend_id": CK3_12004.backend_id("event-window-v1")}
    for option in context["options"]:
        option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.4-v1"
    return context


class _ReligionEndpoint:
    def __init__(self, owner):
        self.owner = owner
        self.requests = []
        self.replies = {}

    def send(self, request):
        if request.get("step") != "query-player-religion-context-v1":
            raise AssertionError(f"unexpected request {request}")
        self.requests.append(copy.deepcopy(request))
        source = self.owner.frame
        context = {"schema": "ck3_12004_religion_context_v1",
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
            "available": True, "unavailable_reason": None,
            "capture_epoch": 1000 + source["native_revision"],
            "date_raw": source["date_raw"], "played_character_id": 29829,
            "rite_id": 152, "faith_id": 23, "religion_id": 8, "faith_main_rite_id": 152,
            "faith_key": "catholic", "religion_key": "christianity",
            "faith_fervor_raw": 4336689, "spiritual_fulfillment_raw": self.owner.raw,
            "raw_scale": 100000}
        result = {"step": request["step"], "accepted": True,
            "private_build": True, "read_only": True, "advertised": False,
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
            "backend_id": CK3_12004.backend_id("player-religion-context-v1"),
            "domain_key": "player_religion_context_v1", "status": "observed",
            "snapshot_revision": source["native_revision"], "date_raw": source["date_raw"],
            "player_religion_context": context}
        # Queried snapshot/public revision metadata is produced by the real
        # transport; it is deliberately absent from this native fixture.
        self.replies[request["request_id"]] = {
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": result}

    def wait_for_command_result(self, request_id, timeout_seconds):
        return self.replies.pop(request_id)


class _CurrentEventSourceDriver:
    allow_private_player_religion_context_query = True

    def __init__(self):
        context = _current_context()
        self.frame = {"snapshot_id": "rite-material-current:51", "revision": 7,
            "native_revision": 51, "date_raw": context["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "active_event": {"instance_id": 29, "option_count": 3,
                "options": [{"option_number": i + 1, "enabled": True} for i in range(3)]},
            "pending_character_interaction": None, "active_wars": [], "player_armies": [],
            "diagnostics": {"hello": {"game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256}},
            "history": []}
        native_window = {"step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True, "status": "available", "current_event_window_context": context,
            "queried_snapshot_id": self.frame["snapshot_id"], "queried_revision": 7,
            "queried_native_revision": 51, "snapshot_revision": 51,
            "current_event_instance_id": 29, "date_raw": context["date_raw"]}
        self.frame["history"].append({"command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                                      "ok": True, "result": native_window})
        self.raw = 0
        self.actions = []
        self.endpoint = _ReligionEndpoint(self)
        self.state = self.endpoint

    def capabilities(self):
        return {"backend_id": "synthetic-actual4-rite-event-source",
            "bridge_capabilities": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY],
            "action_steps": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                             "select-event-option-1", "select-event-option-2", "select-event-option-3"]}

    def take_snapshot(self):
        return copy.deepcopy(self.frame)

    def take_snapshot_without_native_command_history(self):
        return self.take_snapshot()

    def query_player_religion_context_private_v1(self, *, expected_revision):
        return query_player_religion_context_private_v1(self, expected_revision=expected_revision)

    def execute_step(self, step, *, expected_revision):
        if step != "select-event-option-1" or expected_revision != self.frame["revision"]:
            raise AssertionError(f"unexpected action {(step, expected_revision)}")
        self.actions.append((step, expected_revision))
        starting = self.take_snapshot()
        self.frame.update(snapshot_id="rite-material-current:52", revision=8,
                          native_revision=52, active_event=None)
        self.raw = 125000
        # Ordinary action-source fields only. The Service must obtain and
        # retain both fulfillment observations independently through transport.
        return {"accepted": True, "step": step, "event_selection": {
            "postcondition_verified": True, "old_event_instance_id": 29,
            "new_event_instance_id": None, "selected_native_option_index": 0,
            "selected_option_number": 1,
            "starting_snapshot_id": starting["snapshot_id"], "starting_revision": 7,
            "ending_snapshot_id": self.frame["snapshot_id"], "ending_revision": 8}}


class RiteGrowthFulfillmentServiceCompound12004Tests(unittest.TestCase):
    def test_normal_plan_submit_and_independent_after_query_reach_material_history(self):
        driver = _CurrentEventSourceDriver()
        service = GameplayBridgeService(driver)
        shown = []

        def before_submit(presentation):
            shown.append(copy.deepcopy(presentation))
            self.assertEqual(driver.actions, [])
            material = presentation["plan"]["event_material_postcondition"]
            self.assertEqual(material["status"], "ready")
            self.assertEqual(material["starting_value"], 0)
            self.assertEqual(material["starting_native_revision"], 51)
            self.assertEqual(len(driver.endpoint.requests), 1)

        outcome = service.auto_turn(before_submit=before_submit)
        self.assertEqual(outcome["status"], "executed")
        self.assertEqual(outcome["selected_step"], "select-event-option-1")
        self.assertEqual(driver.actions, [("select-event-option-1", 7)])
        self.assertEqual(len(shown), 1)
        self.assertEqual([request["expected_revision"] for request in driver.endpoint.requests], [51, 52])
        self.assertEqual(len({request["request_id"] for request in driver.endpoint.requests}), 2)
        result = outcome["result"]
        selection = result["event_selection"]
        self.assertEqual(selection[STARTING_FIELD]["fulfillment_raw"], 0)
        self.assertEqual(selection[ENDING_FIELD]["fulfillment_raw"], 125000)
        self.assertEqual(selection[STARTING_FIELD]["faith_id"], selection[ENDING_FIELD]["faith_id"])
        self.assertEqual(selection[STARTING_FIELD]["rite_id"], selection[ENDING_FIELD]["rite_id"])
        material = result["event_material_postcondition"]
        self.assertEqual(material["status"], "verified_change")
        self.assertTrue(material["material_change_observed"])
        self.assertEqual(material["delta"], 125000)
        self.assertEqual(material["starting_revision"], 7)
        self.assertEqual(material["ending_religion_observation"]["native_revision"], 52)
        self.assertEqual(outcome["plan"]["event_decision"]["campaign_utility_profile"]["objective_id"],
                         "continue_robert_campaign_with_current_rite_and_fulfillment")
        self.assertIsNone(driver.frame["active_event"])
        self.assertEqual(driver.frame["date_raw"], 53265288)


if __name__ == "__main__":
    unittest.main()
