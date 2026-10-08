"""SOURCE_NOTRUN: new episodes after a beneficial retained end.

Normalized native inputs, selected planner step and backend dates are synthetic.
Registered query staging, the formal consumer and normal Service turn are real
production code. This compound does not replay the retained-reader FIRST.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import (
    LEDGER_FILE, SCHEMA, consume_sway_private_once, read_sway_ledger,
)


ACTOR, TARGET, INSTANCE, GENERATION = 29829, 34333, 134217986, 8
DATE = 53288544


class FollowupSourceDriver:
    allow_private_active_scheme_sway_action = True
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.frame = {
            "paused": True, "map_ready": True, "revision": 40,
            "native_revision": 40, "date_raw": DATE,
            "played_character": {"character_id": ACTOR, "alive": True},
            "active_context": {"active_event": None,
                               "pending_character_interaction": None},
        }
        self.active = None
        self.opinion = 27
        self.epoch = 100
        self.submits = []
        self.receipts = []
        self.fail_submit = False

    def take_snapshot_without_native_command_history(self):
        return deepcopy(self.frame)

    def take_snapshot(self):
        return self.take_snapshot_without_native_command_history()

    def query_active_scheme_sway_target_private_v1(self, *, expected_revision,
                                                  target_character_id):
        assert expected_revision == self.frame["revision"]
        self.epoch += 1
        matching = self.active is not None and self.active[0] == target_character_id
        return {
            "schema": "active-scheme-sway-private-read-v1",
            "queried_revision": expected_revision,
            "queried_native_revision": self.frame["native_revision"],
            "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"], "capture_epoch": self.epoch,
            "container_generation": self.epoch,
            "actor_character_id": ACTOR, "target_character_id": target_character_id,
            "target_opinion_of_actor": self.opinion,
            "active_scheme_count": int(self.active is not None),
            "matching_sway_active": matching,
            "native_complete_can_send": self.active is None,
            "native_legal_now": self.active is None,
        }

    def query_active_scheme_sway_completion_private_v1(self, *, expected_revision,
                                                      target_character_id,
                                                      scheme_instance_id):
        assert expected_revision == self.frame["revision"]
        receipt = read_sway_ledger(self.state_dir)["resolved"]["native_receipt"]
        assert scheme_instance_id == receipt["scheme_instance_id"]
        return {
            "schema": "xar.ck3.sway_completion.v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": target_character_id,
            "scheme_instance_id": scheme_instance_id,
            "scheme_instance_generation": receipt["scheme_instance_generation"],
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"],
            "instance_source_observed": True, "instance_present": True,
            "storage_slot_reused": False, "exact_instance_join_ready": True,
            "owner_matches_actor": False, "owner_cleared": True,
            "native_owner_raw": 0xFFFFFFFF, "native_status_observed": True,
            "native_status_raw": 1, "native_status_key": "terminated_unattributed",
            "native_terminal_state_observed": True,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def query_active_scheme_sway_outcome_opinion_private_v1(self, *, expected_revision,
                                                          target_character_id):
        assert expected_revision == self.frame["revision"]
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": target_character_id,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"], "target_opinion_of_actor": self.opinion,
            "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            "instance_terminal_outcome_observed": False,
        }

    def submit_active_scheme_sway_private_v1(self, *, readback, action_id):
        pending = read_sway_ledger(self.state_dir)["pending"]
        assert pending["action_id"] == action_id  # Real durable intent precedes ACK.
        self.submits.append(action_id)
        if self.fail_submit:
            raise BridgeUnavailableError("fixture unavailable submit result")
        self.active = (readback["target_character_id"], 268435700 + len(self.submits), 16)
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        return {"stage": "submitted_verification_pending", "action_id": action_id}

    def query_active_scheme_sway_receipt_private_v1(self, **arguments):
        self.receipts.append(arguments["action_id"])
        assert arguments["expected_revision"] == self.frame["native_revision"]
        assert self.active[0] == arguments["target_character_id"]
        return {"stage": "applied", "postcondition_verified": True,
                "scheme_instance_id": self.active[1],
                "scheme_instance_generation": self.active[2]}

    def execute_step(self, step, *, expected_revision):
        assert step == "life-advance" and expected_revision == self.frame["revision"]
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        self.frame["date_raw"] += 24  # Synthetic one-day backend result, not live evidence.
        return {"status": "completed", "step": step}


def test_beneficial_end_repeat_normal_turn_finish_retarget_and_pending(tmp_path: Path):
    from mcp import Client

    original = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": ACTOR, "target_character_id": TARGET,
        "action_id": "sway-original", "post_native_revision": 38,
        "post_date_raw": DATE - 24, "next_turn_consumed": True,
        "native_receipt": {"scheme_instance_id": INSTANCE,
                           "scheme_instance_generation": GENERATION},
    }
    (tmp_path / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": original,
    }), encoding="utf-8")
    driver = FollowupSourceDriver(tmp_path)

    def choose(target=TARGET):
        before = driver.take_snapshot()
        read = driver.query_active_scheme_sway_target_private_v1(
            expected_revision=before["revision"], target_character_id=target)
        return consume_sway_private_once(
            driver, target_character_id=target, snapshot=before, readback=read)

    def planned_turn(_service):
        return {"revision": driver.frame["revision"],
                "plan": {"selected_step": "life-advance"}}

    async def call(client, name, arguments):
        result = await client.call_tool(name, arguments)
        assert not result.is_error, result.content
        return result.structured_content

    async def stage(client):
        resolved = read_sway_ledger(tmp_path)["resolved"]
        args = {"expected_revision": driver.frame["revision"],
                "target_character_id": resolved["target_character_id"]}
        await call(client, "ck3_query_active_scheme_sway_completion_private_v1",
                   {**args, "scheme_instance_id": resolved["native_receipt"]["scheme_instance_id"]})
        await call(client, "ck3_query_active_scheme_sway_outcome_opinion_private_v1", args)

    async def exercise():
        with patch.object(GameplayBridgeService, "plan_turn", planned_turn):
            async with Client(create_server(driver)) as client:
                # An empty census alone cannot authorize a repeat of the old action.
                assert choose()["followup"]["decision"] == "observe_tracked_instance_end"
                assert driver.submits == []
                await stage(client)
                first = choose()
                assert first["status"] == "applied" and first["postcondition_verified"]
                assert first["followup"]["decision"] == "repeat_selected_target"
                assert first["action_id"] != original["action_id"]
                assert first["native_receipt"]["scheme_instance_id"] != INSTANCE
                assert driver.submits == driver.receipts == [first["action_id"]]
                prior = first["previous_interventions"][0]
                assert prior["native_receipt"] == original["native_receipt"]
                assert not prior["terminal_intervention"]["next_turn_consumed"]
                assert prior["material_intervention"]["dedicated_benefit_observed"]
                assert prior["terminal_intervention"]["terminal_cause"] == "unknown"
                outcome = await call(client, "ck3_auto_turn", {})
                consumed = outcome["sway_following_turn"]
                assert outcome["status"] == "executed" and consumed["next_turn_consumed"]
                prior = consumed["previous_interventions"][0]
                assert prior["material_intervention"]["next_turn_consumed"]
                assert prior["terminal_intervention"]["next_turn_consumed"]
                assert prior["terminal_intervention"]["terminal_cause_observed"] is False
                assert choose()["followup"]["decision"] == "retain_existing_sway"
            # A cold normal Service reopens history without rearming prior facts.
            async with Client(create_server(driver)) as cold:
                assert "sway_following_turn" not in await call(cold, "ck3_auto_turn", {})
                driver.active = None
                driver.opinion = 60
                await stage(cold)
                assert choose()["followup"]["decision"] == "finish_selected_relation"
                assert len(driver.submits) == 1
                driver.opinion = 12
                retarget = choose(34730)  # Explicit synthetic selected relation, not live ranking.
                assert retarget["followup"]["decision"] == "retarget_selected_relation"
                assert retarget["action_id"] != first["action_id"]
                assert len(retarget["previous_interventions"]) == 2
                assert {row["action_id"] for row in retarget["previous_interventions"]} == {
                    original["action_id"], first["action_id"]}
                await call(cold, "ck3_auto_turn", {})
                driver.active = None
                driver.fail_submit = True
                assert choose(36666)["status"] == "submission_unresolved"
                retained = (tmp_path / LEDGER_FILE).read_bytes()
                assert choose(36666)["status"] == "pending_recovery"
                assert len(driver.submits) == 3 and len(set(driver.submits)) == 3
                assert (tmp_path / LEDGER_FILE).read_bytes() == retained

    asyncio.run(exercise())
    assert read_sway_ledger(tmp_path)["resolved"]["target_character_id"] == 34730
