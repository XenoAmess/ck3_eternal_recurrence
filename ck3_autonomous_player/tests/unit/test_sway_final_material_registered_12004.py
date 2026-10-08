"""SOURCE_NOTRUN: one new final-material compound through complete wire contexts.

The full completion/opinion envelopes use the existing qualified actual4 DTO
and serializers' context. All values, dates, IDs and world frames here are
explicitly synthetic consumer inputs. No native fixture is replayed, no new
native qualification or real material is claimed, and no game/SDK is contacted.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT.parent / "tools"),
               str(ROOT.parent / "ck3_workshop_mcp" / "src")]

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger

ACTOR, TARGET, GENERATION = 29829, 39001, 12  # Synthetic target, not historic34333.
INSTANCE = (GENERATION << 24) | 711
COMPLETION = "ck3_query_active_scheme_sway_completion_private_v1"
OPINION = "ck3_query_active_scheme_sway_outcome_opinion_private_v1"
COMPLETION_STEP = "query-sway-completion-v1-private"
OPINION_STEP = "query-sway-outcome-opinion-v1-private"


class FullWireContextDriver:
    """Production wrappers/protocol cache; fixture source endpoint/world only."""

    command_timeout_seconds = 30.0
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True
    query_active_scheme_sway_completion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_completion_private_v1)
    query_active_scheme_sway_outcome_opinion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_outcome_opinion_private_v1)

    def __init__(self, state_dir):
        self.state_dir, self.endpoint = state_dir, self
        self.mode, self.sway, self.blocker = "active", 75, None
        self.native_revision, self.date = 7, 53310000
        self.requests = []
        self.state = NativeProtocolState("synthetic-final-sway-material-wire-context")
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        })
        self.publish()

    def publish(self):
        assert self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{self.native_revision}", "revision": self.native_revision,
            "state": {"date_raw": self.date, "speed": 1, "paused": True, "map_ready": True,
                      "played_character": {"character_id": ACTOR, "alive": True},
                      "active_event": None, "pending_character_interaction": None,
                      "one_life_settlement": None, "active_wars": [],
                      "player_armies": [], "history": []},
        }) == "state_snapshot"

    def advance(self):
        self.native_revision += 1
        self.date += 24
        self.publish()

    def take_snapshot(self):
        return self.state.semantic_snapshot()

    def take_snapshot_without_native_command_history(self):
        return self.take_snapshot()

    def completion_body(self):
        present, ended = self.mode != "purged", self.mode == "terminal"
        return {
            "schema": "xar.ck3.sway_completion.v1", "schema_version": 1,
            "build_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
            "adapter_id": "ck3-1.20.0.4-msvc-x64",
            "private_build": True, "read_only": True, "advertised": False,
            "available": True, "unavailable_reason": "",
            "snapshot_revision": self.native_revision, "date_raw": self.date,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": GENERATION,
            "native_source_kind": "native_scheme_storage",
            "current_instance_retention": "until_native_manager_purge",
            "instance_source_observed": True, "instance_present": present,
            "storage_slot_reused": False, "exact_instance_join_ready": present,
            "native_owner_raw": (0xFFFFFFFF if ended else ACTOR) if present else None,
            "owner_matches_actor": present and not ended, "owner_cleared": ended,
            "native_status_observed": present,
            "native_status_raw": int(ended) if present else None,
            "native_status_key": "terminated_unattributed" if ended else "continue" if present else "unknown",
            "native_terminal_state_observed": ended,
            "native_success_chance_observed": False, "native_success_chance_raw": None,
            "native_success_chance_scale": 100000, "native_success_chance_unit": "percent",
            "native_can_continue_observed": False, "native_can_continue": None,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def opinion_body(self):
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "build": CK3_12004.game_version,
            "available": True, "unavailable_reason": "",
            "snapshot_revision": self.native_revision, "date_raw": self.date,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "target_opinion_of_actor": min(100, self.sway + (self.blocker or 0)),
            "scheme_sway_opinion": {"observed": True, "present": True, "value": self.sway},
            "sway_blocker_opinion": {"observed": True, "present": self.blocker is not None,
                                     "value": self.blocker},
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        }

    def send(self, request):
        assert request["expected_revision"] == self.native_revision
        assert request["actor_character_id"] == ACTOR
        assert request["target_character_id"] == TARGET
        if request["step"] == COMPLETION_STEP:
            assert request["scheme_instance_id"] == INSTANCE
            field, body = "sway_completion", self.completion_body()
        else:
            assert request["step"] == OPINION_STEP  # No Start or Stop action.
            field, body = "sway_outcome_opinion", self.opinion_body()
        packet = {
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": {"step": request["step"], "accepted": True, "status": "available",
                       "private_build": True, "read_only": True, "advertised": False,
                       "backend_id": "native-headless", field: body},
        }
        assert self.state.ingest(packet) == "command_result"
        self.requests.append(deepcopy(packet))

    def execute_step(self, step, *, expected_revision):
        assert step == "life-advance" and expected_revision == self.take_snapshot()["revision"]
        self.advance()
        return {"status": "completed", "step": step}


def seed(state_dir):
    state_dir.mkdir()
    (state_dir / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": {
            "action_id": "sway-synthetic-final-material", "status": "applied",
            "postcondition_verified": True, "actor_character_id": ACTOR,
            "target_character_id": TARGET, "post_native_revision": 5,
            "post_date_raw": 53309952, "next_turn_consumed": True,
            "native_receipt": {"scheme_instance_id": INSTANCE,
                               "scheme_instance_generation": GENERATION},
        },
    }), encoding="utf-8")
    return FullWireContextDriver(state_dir)


class FinalMaterialSoleCompound(unittest.IsolatedAsyncioTestCase):
    async def test_final_named_gain_normal_turn_and_independent_controls(self):
        from mcp import Client

        outputs = {}

        async def call(client, name, arguments):
            result = await client.call_tool(name, arguments)
            self.assertFalse(result.is_error, result.content)
            return result.structured_content

        async def completion(client, driver):
            return await call(client, COMPLETION, {
                "expected_revision": driver.take_snapshot()["revision"],
                "target_character_id": TARGET, "scheme_instance_id": INSTANCE})

        async def reads(client, driver):
            await completion(client, driver)
            result = await call(client, OPINION, {
                "expected_revision": driver.take_snapshot()["revision"],
                "target_character_id": TARGET})
            self.assertFalse(result["instance_terminal_outcome_observed"])
            return read_sway_ledger(driver.state_dir)["resolved"]

        def planned_turn(service):
            return {"revision": service.driver.take_snapshot()["revision"],
                    "plan": {"selected_step": "life-advance"}}

        with tempfile.TemporaryDirectory(prefix="sway-final-material-") as temporary:
            directory = Path(temporary)
            driver = seed(directory / "positive")
            with patch.object(GameplayBridgeService, "plan_turn", planned_turn):
                async with Client(create_server(driver)) as client:
                    baseline = await reads(client, driver)
                    self.assertTrue(baseline["material_intervention"]["tracked_instance_active"])
                    self.assertFalse(baseline["material_intervention"]["incremental_named_gain_observed"])
                    outputs["1_active_baseline"] = baseline
                    driver.advance(); driver.mode, driver.sway = "terminal", 100
                    final = await reads(client, driver)
                    material = final["material_intervention"]
                    self.assertFalse(material["tracked_instance_active"])
                    self.assertTrue(material["incremental_named_gain_observed"])
                    self.assertEqual(material["previous_scheme_sway_opinion"]["value"], 75)
                    self.assertEqual(material["scheme_sway_opinion"]["value"], 100)
                    self.assertTrue(material["instance_terminal_outcome_observed"])
                    self.assertFalse(material["terminal_cause_observed"])
                    self.assertEqual(material["terminal_cause"], "unknown")
                    outputs["2_final_named_gain"] = final
                    following = await call(client, "ck3_auto_turn", {})
                    consumed = following["sway_following_turn"]
                    self.assertTrue(consumed["material_intervention"]["next_turn_consumed"])
                    self.assertTrue(consumed["material_intervention"]["incremental_named_gain_observed"])
                    self.assertTrue(consumed["terminal_intervention"]["next_turn_consumed"])
                    self.assertEqual(consumed["native_receipt"], baseline["native_receipt"])
                    outputs["3_normal_following"] = consumed
                async with Client(create_server(driver)) as cold:
                    repeated = await reads(cold, driver)
                    self.assertTrue(repeated["material_intervention"]["next_turn_consumed"])
                    self.assertNotIn("sway_following_turn", await call(cold, "ck3_auto_turn", {}))
                    outputs["4_cold_no_rearm"] = repeated
            negative = seed(directory / "negative")
            async with Client(create_server(negative)) as client:
                await reads(client, negative)
                negative.advance(); negative.mode, negative.blocker = "terminal", -10
                setback = await reads(client, negative)
                self.assertTrue(setback["material_intervention"]["dedicated_setback_observed"])
                self.assertFalse(setback["material_intervention"]["incremental_named_gain_observed"])
                self.assertEqual(setback["terminal_intervention"]["terminal_cause"], "unknown")
                outputs["5_independent_setback"] = setback
            purged = seed(directory / "purged-before-opinion")
            async with Client(create_server(purged)) as client:
                await reads(client, purged)
                purged.advance(); purged.mode = "terminal"
                await completion(client, purged)  # End retained; no final opinion read yet.
                purged.advance(); purged.mode, purged.sway = "purged", 100
                late = await reads(client, purged)
                self.assertFalse(late["latest_instance_observation"]["instance_terminal_outcome_observed"])
                self.assertTrue(late["terminal_intervention"]["instance_terminal_outcome_observed"])
                self.assertFalse(late["material_intervention"]["incremental_named_gain_observed"])
                outputs["6_purged_no_final_gain_attribution"] = late
            self.assertIsNone(read_sway_ledger(driver.state_dir)["pending"])
        self.assertEqual(len(outputs), 6)
        output = os.environ.get("XAR_SWAY_FINAL_MATERIAL_12004_OUTPUT")
        if output:
            Path(output).write_text(json.dumps({
                "qualification": "offline synthetic full-wire-context consumer; not live/material",
                "compound_cases": 6, "production_path": "registered MCP -> native Driver transport -> Service -> normal turn",
                "synthetic_context": "all full envelopes/world/values/IDs/dates; existing actual4 DTO source reused",
                "new_native_CPP_or_observer": 0, "Start_or_Stop_calls": 0,
                "terminal_cause": "unknown", "outputs": outputs,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
