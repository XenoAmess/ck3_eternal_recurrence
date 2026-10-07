"""AUTHORED_NOTRUN: registered reads -> real Service turn -> cold Sway ledger.

Inputs and gameplay frames are synthetic normalized fixture sources. Existing
actual4 native qualification is reused; this compound tests the new Python
production path and grants no live or natural-termination credit.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger


ACTOR, TARGET, INSTANCE, GENERATION = 29829, 34333, 134217986, 8
DATE = 53288448


class LifecycleSourceDriver:
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.frame = {
            "paused": True, "map_ready": True, "revision": 7,
            "native_revision": 7, "date_raw": DATE,
            "played_character": {"character_id": ACTOR, "alive": True},
        }
        self.completion = self._completion()
        self.calls = []
        self.snapshot_calls = 0

    def _completion(self):
        return {
            "schema": "xar.ck3.sway_completion.v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": GENERATION,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"],
            "instance_source_observed": True, "instance_present": True,
            "storage_slot_reused": False, "exact_instance_join_ready": True,
            "owner_matches_actor": True, "owner_cleared": False,
            "native_owner_raw": ACTOR, "native_status_observed": True,
            "native_status_raw": 0, "native_status_key": "continue",
            "native_terminal_state_observed": False,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def query_active_scheme_sway_completion_private_v1(self, **arguments):
        self.calls.append(("completion", arguments))
        return deepcopy(self.completion)

    def query_active_scheme_sway_outcome_opinion_private_v1(self, **arguments):
        self.calls.append(("opinion", arguments))
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"], "target_opinion_of_actor": 27,
            "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            # The opinion reader itself has no instance/terminal measurement.
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        }

    def execute_step(self, step, *, expected_revision):
        self.calls.append((step, expected_revision))
        assert expected_revision == self.frame["revision"]
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        return {"status": "completed", "step": step}

    def take_snapshot_without_native_command_history(self):
        self.snapshot_calls += 1
        return deepcopy(self.frame)

    def take_snapshot(self):
        return self.take_snapshot_without_native_command_history()


def test_registered_sway_material_and_terminal_reach_normal_and_cold_turn(tmp_path: Path):
    from mcp import Client

    original = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": ACTOR, "target_character_id": TARGET,
        "action_id": "sway-original", "post_native_revision": 5,
        "post_date_raw": DATE, "next_turn_consumed": True,
        "following_native_revision": 6, "following_date_raw": DATE,
        "native_receipt": {"scheme_instance_id": INSTANCE,
                           "scheme_instance_generation": GENERATION},
    }
    (tmp_path / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": original,
    }), encoding="utf-8")
    driver = LifecycleSourceDriver(tmp_path)

    def planned_turn(_service):
        # Only the planner selection and backend frame are fixture sources;
        # the normal Service dispatcher/registered tools are production code.
        return {"revision": driver.frame["revision"], "plan": {"selected_step": "pause-map"}}

    async def call(client, name, arguments):
        result = await client.call_tool(name, arguments)
        assert not result.is_error, result.content
        return result.structured_content

    async def reads(client):
        arguments = {"expected_revision": driver.frame["revision"],
                     "target_character_id": TARGET}
        completion = await call(client, "ck3_query_active_scheme_sway_completion_private_v1",
                                {**arguments, "scheme_instance_id": INSTANCE})
        assert completion == driver.completion
        opinion = await call(client, "ck3_query_active_scheme_sway_outcome_opinion_private_v1",
                             arguments)
        assert opinion["instance_terminal_outcome_observed"] is False
        return read_sway_ledger(tmp_path)["resolved"]

    async def exercise():
        with patch.object(GameplayBridgeService, "plan_turn", planned_turn):
            async with Client(create_server(driver)) as client:
                current = await reads(client)
                assert current["material_intervention"]["dedicated_benefit_observed"]
                assert not current["terminal_intervention"]["instance_terminal_outcome_observed"]
                first = await call(client, "ck3_auto_turn", {})
                assert first["status"] == "executed"
                assert first["sway_following_turn"]["material_intervention"]["next_turn_consumed"]
                assert first["sway_following_turn"]["following_native_revision"] == 6
                # Retained exact-ID termination is independent of its useful modifier.
                driver.completion = {**driver._completion(),
                    "owner_matches_actor": False, "owner_cleared": True,
                    "native_owner_raw": 0xFFFFFFFF, "native_status_raw": 1,
                    "native_status_key": "terminated_unattributed",
                    "native_terminal_state_observed": True}
                staged = await reads(client)
                assert staged["material_intervention"]["instance_terminal_outcome_observed"]
                assert staged["material_intervention"]["dedicated_benefit_observed"]
                assert not staged["terminal_intervention"]["next_turn_consumed"]
            # New server/Service instance reopens the durable original ledger.
            async with Client(create_server(driver)) as cold_client:
                later = await call(cold_client, "ck3_auto_turn", {})
                resolved = later["sway_following_turn"]
                terminal = resolved["terminal_intervention"]
                assert terminal["next_turn_consumed"]
                assert terminal["instance_terminal_outcome_observed"]
                assert terminal["native_status_key"] == "terminated_unattributed"
                assert terminal["terminal_cause_observed"] is False
                assert terminal["terminal_cause"] == "unknown"
                assert resolved["native_receipt"] == original["native_receipt"]
                # Repeating the same retained fact cannot rearm it after cold consumption.
                driver.completion.update(snapshot_revision=driver.frame["native_revision"])
                await reads(cold_client)
                before_reads = driver.snapshot_calls
                repeat = await call(cold_client, "ck3_auto_turn", {})
                assert "sway_following_turn" not in repeat
                assert driver.snapshot_calls == before_reads
                # Purged absence is absence; it cannot erase the earlier real end.
                driver.completion = {**driver._completion(),
                    "instance_present": False, "exact_instance_join_ready": False,
                    "native_status_observed": False, "native_status_raw": None,
                    "native_status_key": "unknown", "native_terminal_state_observed": False}
                absent = await reads(cold_client)
                assert not absent["latest_instance_observation"]["instance_terminal_outcome_observed"]
                assert absent["terminal_intervention"]["instance_terminal_outcome_observed"]
                assert absent["terminal_intervention"]["native_observation"]["instance_present"]
                assert not absent["material_intervention"]["tracked_instance_active"]
                assert absent["material_intervention"]["dedicated_benefit_observed"]
                before_reads = driver.snapshot_calls
                blocked_service = GameplayBridgeService(driver)
                with patch.object(blocked_service, "plan_turn", return_value={"plan": {"selected_step": None}}):
                    assert blocked_service.auto_turn()["status"] == "blocked"
                assert driver.snapshot_calls == before_reads

    asyncio.run(exercise())
    assert read_sway_ledger(tmp_path)["pending"] is None
    assert {name for name, _ in driver.calls} == {"completion", "opinion", "pause-map"}
