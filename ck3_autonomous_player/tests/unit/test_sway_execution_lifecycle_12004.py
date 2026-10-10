"""One newly produced actual4 native packet -> registered real Driver -> normal/cold ledger.

Native operands, backend frames and independent completion/opinion reads are
owned fixture inputs. No Game, natural hidden outcome or G2 credit is claimed.
The packet must come from the new current-profile FIRST, never old producer replay.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_ck3_12002_sway_completion_execution_wire import ProtocolSwayExecutionDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger


class CurrentPhaseDriver(ProtocolSwayExecutionDriver):
    query_active_scheme_sway_completion_execution_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_completion_execution_private_v1)
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    def __init__(self, packet, state_dir):
        super().__init__(packet)
        self.state_dir = state_dir
        self.terminal = False
        self.native = packet["result"]["sway_completion_execution"]

    def take_snapshot_without_native_command_history(self):
        return self.state.semantic_snapshot()

    def query_active_scheme_sway_completion_private_v1(self, **arguments):
        frame = self.take_snapshot()
        return {
            "schema": "xar.ck3.sway_completion.v1", "available": True,
            "actor_character_id": self.native["actor_character_id"],
            "target_character_id": self.native["target_character_id"],
            "scheme_instance_id": self.native["scheme_instance_id"],
            "scheme_instance_generation": self.native["scheme_instance_id"] >> 24,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
            "instance_source_observed": True, "instance_present": True,
            "storage_slot_reused": False, "exact_instance_join_ready": True,
            "owner_matches_actor": not self.terminal, "owner_cleared": self.terminal,
            "native_owner_raw": 0xFFFFFFFF if self.terminal else self.native["actor_character_id"],
            "native_status_observed": True, "native_status_raw": int(self.terminal),
            "native_status_key": "terminated_unattributed" if self.terminal else "continue",
            "native_terminal_state_observed": self.terminal,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def query_active_scheme_sway_outcome_opinion_private_v1(self, **arguments):
        frame = self.take_snapshot()
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "available": True,
            "actor_character_id": self.native["actor_character_id"],
            "target_character_id": self.native["target_character_id"],
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
            "target_opinion_of_actor": 27,
            "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        }

    def execute_step(self, step, *, expected_revision):
        frame = self.take_snapshot()
        assert step == "pause-map" and expected_revision == frame["revision"]
        revision = frame["native_revision"] + 1
        self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{revision}", "revision": revision,
            "state": {
                "date_raw": frame["date_raw"], "speed": 5, "paused": True, "map_ready": True,
                "played_character": frame["played_character"],
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [], "player_armies": [], "history": [],
            },
        })
        return {"status": "completed", "step": step}


def test_current_native_hidden_phase_reaches_registered_normal_and_cold_turn(tmp_path: Path):
    from mcp import Client

    packet = json.loads(Path(os.environ["XAR_SWAY_EXECUTION_FIRST_PACKET"]).read_text(encoding="utf-8"))
    assert packet["result"]["build_version"] == CK3_12004.game_version
    assert packet["result"]["executable_sha256"] == CK3_12004.executable_sha256
    native = packet["result"]["sway_completion_execution"]
    assert [row["phase_result"] for row in native["records"]] == ["failure", "success"]
    driver = CurrentPhaseDriver(packet, tmp_path)
    original = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": native["actor_character_id"],
        "target_character_id": native["target_character_id"], "action_id": "original-sway",
        "post_native_revision": packet["result"]["snapshot_revision"] - 2,
        "post_date_raw": packet["result"]["date_raw"], "next_turn_consumed": True,
        "native_receipt": {"scheme_instance_id": native["scheme_instance_id"],
                           "scheme_instance_generation": native["scheme_instance_id"] >> 24},
    }
    (tmp_path / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": original}), encoding="utf-8")

    def planned_turn(_service):
        return {"revision": driver.take_snapshot()["revision"],
                "plan": {"selected_step": "pause-map"}}

    async def call(client, name, arguments):
        response = await client.call_tool(name, arguments)
        assert not response.is_error, response.content
        return response.structured_content

    def arguments():
        return {"expected_revision": driver.take_snapshot()["revision"],
                "target_character_id": native["target_character_id"]}

    async def phase(client):
        # Later frames are fixture backend stamps; source records stay exactly
        # those newly emitted by the current-profile installed native wrapper.
        driver.packet["result"]["snapshot_revision"] = driver.take_snapshot()["native_revision"]
        return await call(client, "ck3_query_active_scheme_sway_completion_execution_private_v1",
                          {**arguments(), "scheme_instance_id": native["scheme_instance_id"]})

    async def independent_reads(client):
        await call(client, "ck3_query_active_scheme_sway_completion_private_v1",
                   {**arguments(), "scheme_instance_id": native["scheme_instance_id"]})
        await call(client, "ck3_query_active_scheme_sway_outcome_opinion_private_v1", arguments())

    async def exercise():
        with patch.object(GameplayBridgeService, "plan_turn", planned_turn):
            async with Client(create_server(driver)) as client:
                result = await phase(client)
                assert result["records"] == native["records"]
                staged = read_sway_ledger(tmp_path)["resolved"]
                phase_record = staged["phase_intervention"]
                assert phase_record["phase_result"] == "success"
                assert phase_record["executing_input_observed"]
                assert not phase_record["material_effect_observed"]
                assert not phase_record["native_terminal_state_observed"]
                assert "material_intervention" not in staged and "terminal_intervention" not in staged
                await independent_reads(client)
                consumed = await call(client, "ck3_auto_turn", {})
                resolved = consumed["sway_following_turn"]
                assert resolved["phase_intervention"]["next_turn_consumed"]
                assert resolved["material_intervention"]["dedicated_benefit_observed"]
                assert not resolved["terminal_intervention"]["instance_terminal_outcome_observed"]
            # A new Service consumes a later independent retained end without
            # rearming the copied hidden phase or changing the original start.
            async with Client(create_server(driver)) as cold:
                await phase(cold)
                driver.terminal = True
                await independent_reads(cold)
                later = await call(cold, "ck3_auto_turn", {})
                resolved = later["sway_following_turn"]
                assert resolved["phase_intervention"]["next_turn_consumed"]
                assert resolved["phase_intervention"]["following_native_revision"] == (
                    consumed["sway_following_turn"]["phase_intervention"]["following_native_revision"])
                assert resolved["terminal_intervention"]["instance_terminal_outcome_observed"]
                assert resolved["terminal_intervention"]["terminal_cause"] == "unknown"
                assert not resolved["phase_intervention"]["native_terminal_state_observed"]
                assert resolved["native_receipt"] == original["native_receipt"]
                await phase(cold)
                repeat = await call(cold, "ck3_auto_turn", {})
                assert "sway_following_turn" not in repeat

    asyncio.run(exercise())
    assert len(driver.sent) == 3
    assert {request["step"] for request in driver.sent} == {"query-sway-completion-execution-v1-private"}
    assert read_sway_ledger(tmp_path)["pending"] is None
