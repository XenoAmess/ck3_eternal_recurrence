"""Sole FIRST: admitted LIFE guard omits history before the daily siege loop.

Reuse the qualified Native33 whole foreign-leader input, then connect real
registered ordinary planning, NativeDriver advance, independent paused siege
observation and checkpoint materialization. Clock/work/file outputs are
declared synthetic; no native producer or previous qualification is replayed.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
from pathlib import Path

from test_exact_day_native_clock_paused_next_frame import ClockProvider
from test_lifestyle_formal_private_consumer import _life_snapshot
from test_native_bridge_driver import _army, _hello, _snapshot, _war
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import QUERY_STEP
from xar_autoplayer.bridge.war_contract import normalize_objective_province_states
from xar_autoplayer.bridge.war_occupation_targets_contract import normalize_war_occupation_targets_v1


class _CountedHistoryPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        detached = list(self)
        memo[id(self)] = detached
        return detached


def test_normal_foreign_leader_contribution_advances_one_day_observes_and_saves(tmp_path):
    from mcp import Client

    packet_path = Path(os.environ["XAR_FOREIGN_SIEGE_QUALIFIED_PACKET"])
    packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
    envelope = packet["result"]
    value = normalize_war_occupation_targets_v1(
        envelope["war_occupation_targets_v1"], expected_war_id=100663329,
        expected_actor_character_id=29829,
        expected_snapshot_revision=envelope["snapshot_revision"],
        expected_date_raw=envelope["date_raw"], expected_player_side="attacker")
    states = normalize_objective_province_states(value["rows"], objective_province_ids=[2606, 2608])
    current = next(row for row in states if row["province_id"] == 2608)
    assert current["active_siege"]["player_army_besieging"] is False
    assert current["current_besieging_army_selection"]["controllable"] is False
    assert current["active_siege"]["current_work"]["raw"] == 0
    original_siege_id = current["active_siege"]["siege_id"]
    original_rows = copy.deepcopy(states)
    player = _army(218104048, province_id=2608, owner_character_id=29829,
        soldiers=1500, army_state="sieging", army_state_code=3,
        move_target_province_id=None, route_province_ids=[], in_combat=False,
        retreating=False)
    start_date = envelope["date_raw"]
    progressed_work = 100_000
    save_dir = tmp_path / "isolated-profile" / "save games"
    save_dir.mkdir(parents=True)

    class SiegeClockProvider(ClockProvider):
        def publish_state(self):
            observed = copy.deepcopy(original_rows)
            siege_state = next(row for row in observed if row["province_id"] == 2608)
            siege = siege_state["active_siege"]
            if self.date_raw > start_date:
                siege["current_work"]["raw"] = progressed_work
                siege["remaining_work"]["raw"] = siege["total_work"]["raw"] - progressed_work
                siege["progress_fraction"]["raw"] = progressed_work * 100_000 // siege["total_work"]["raw"]
            self.publish(_snapshot(self.revision, date_raw=self.date_raw, speed=self.speed,
                paused=self.paused, played_character={"character_id": 29829, "alive": True},
                active_wars=[_war(100663329, allied_armies=[player], score=0,
                    war_objective_province_ids=[2606, 2608], objective_province_states=observed)],
                player_armies=[player]))

        def send(self, request):
            if request.get("type") == "execute_step" and request["step"] == QUERY_STEP:
                self.frames.append(request)
                life = _life_snapshot()
                life.update(snapshot_id=request["expected_snapshot_id"],
                    public_revision=request["expected_revision"],
                    native_revision=request["expected_revision"], proof_epoch=request["expected_revision"],
                    date_raw=request["expected_date_raw"],
                    player_character_id=request["expected_player_character_id"])
                life["current_lifestyle_progress"]["unspent_perk_points"] = 0
                life["legal_perk_candidates"]["items"] = []
                self.publish({"type": "command_result", "protocol_version": 1,
                    "request_id": request["request_id"], "ok": True,
                    "result": {"step": QUERY_STEP, "private_build": True, "advertised": False,
                        "status": "available", "episode_run_id": request["episode_run_id"],
                        "formal_precondition_status": "ready", "snapshot": life}})
                return
            if request.get("type") == "execute_step" and request["step"] == "save-checkpoint":
                self.frames.append(request)
                self.publish({"type": "command_result", "protocol_version": 1,
                    "request_id": request["request_id"], "ok": True,
                    "result": {"step": "save-checkpoint", "accepted": True, "status": "submitted",
                        "submission": {"sequence": len(self.frames),
                            "requested_save_name": "xar_checkpoint", "date_raw": self.date_raw}}})
                (save_dir / "xar_checkpoint.ck3").write_bytes(
                    f"synthetic siege material checkpoint at raw {self.date_raw}".encode("ascii"))
                return
            super().send(request)

    endpoint = SiegeClockProvider()
    endpoint.date_raw, endpoint.revision = start_date, envelope["snapshot_revision"]
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        state_dir=tmp_path / "driver-state", save_dir=save_dir,
        command_timeout_seconds=0.1, checkpoint_timeout_seconds=1.0,
        checkpoint_poll_interval_seconds=0.005)
    driver.require_initial_lifestyle_focus_before_date_advance = False
    driver.allow_private_lifestyle_formal_trial = True
    hello = _hello(
        "game.state.snapshot", "game.state.active-wars", "game.state.player-armies",
        "game.state.army-routes", "game.state.war-objective-garrison",
        "game.state.war-objective-siege-progress", "game.command.set-speed-1",
        "game.command.set-speed-3", "game.command.set-speed-5",
        "game.command.resume-map", "game.command.pause-map", "game.command.save-checkpoint",
        "game.command.research-arm-tactical-daily-sentinel-v1-N",
        "game.command.research-query-tactical-daily-sentinel-v1",
        "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N")
    hello.update(expected_ck3_version=CK3_12004.game_version,
        expected_ck3_sha256=CK3_12004.executable_sha256)
    endpoint.publish(hello)

    endpoint.publish_state()
    assert driver.state.diagnostics()["last_rejected_state_snapshot"] is None
    starting = driver.take_internal_semantic_snapshot()
    retained = [{"index": index, "command": f"retained-plan-{index}", "ok": True,
        "result": {"values": _CountedHistoryPayload(range(32))}} for index in range(1, 33)]
    retained.append({"index": 33, "command": "query-campaign-root-context-v1", "ok": True,
        "result": {"campaign_root_context": {"status": "available",
            "snapshot_revision": starting["native_revision"], "date_raw": start_date,
            "player_character_id": 29829,
            "government": {"key": "feudal_government", "flags": ["government_is_feudal"]}}}})
    with driver._history_lock:
        driver._command_history = retained
        driver._driver_state_dirty = True

    async def run():
        async with Client(create_server(driver)) as client:
            _CountedHistoryPayload.copies = 0
            planned = await client.call_tool("ck3_plan_turn", {})
            assert not planned.is_error, planned.content
            plan = planned.structured_content["plan"]
            assert plan["phase"] == "native_war_siege_progress", plan
            assert plan["selected_step"] == "life-advance"
            assert plan["lifestyle_decision"]["status"] == "no_legal_minimum"
            assert [row["step"] for row in endpoint.frames if row.get("type") == "execute_step"] == [QUERY_STEP]
            assert _CountedHistoryPayload.copies == 0
            # Public full export remains detached and complete. Reset this
            # intentional export before exercising the normal automatic turn.
            public = driver.take_snapshot()
            assert public["native_command_history"] == retained
            assert _CountedHistoryPayload.copies == 32
            public["native_command_history"][0]["result"]["values"].append(-1)
            assert -1 not in retained[0]["result"]["values"]
            _CountedHistoryPayload.copies = 0
            assert plan["siege_state"]["subject_contribution"]["status"] == "eligible"
            assert plan["siege_state"]["subject_contribution"]["matches_current_selection"] is False
            advanced = await client.call_tool("ck3_auto_turn", {})
            assert not advanced.is_error, advanced.content
            result = advanced.structured_content["result"]
            assert result["requested_horizon_days"] == result["elapsed_days"] == 1
            assert result["timeline_speed"] == 5 and result["paused"] is True
            assert result["timeline_policy"] == "player_siege"
            assert _CountedHistoryPayload.copies == 0
            commands = [row["step"] for row in result["actions"]]
            assert commands == ["set-speed-5",
                f"research-arm-tactical-daily-sentinel-v1-{start_date}-to-{start_date + 24}-speed-5-mode-terminal-a-0",
                "resume-map", "research-query-tactical-daily-sentinel-v1"]
            assert commands.count("resume-map") == 1 and "pause-map" not in commands
            clock = result["exact_day_native_clock"]
            assert clock["armed"]["speed"] == clock["stopped"]["speed"] == 5
            assert clock["armed"]["generation"] == clock["stopped"]["generation"] == 37
            assert clock["stopped"]["completed_daily_ticks"] == 1
            assert clock["stopped"]["trigger_reasons"] == ["date_deadline"]
            assert clock["stopped"]["overshoot_days"] == 0
            assert clock["stopped"]["pause_observed"] is True
            # This is a later independently published rich paused frame. The
            # provider publishes only the paused next day, never a running
            # frame; the original sparse unarmed clock would advance 7 days.
            observed = await client.call_tool("ck3_take_snapshot", {})
            assert not observed.is_error, observed.content
            after = observed.structured_content
            assert after["paused"] is True and after["date_raw"] == start_date + 24
            assert after["played_character"]["character_id"] == 29829
            after_state = next(row for row in after["active_wars"][0]["objective_province_states"]
                               if row["province_id"] == 2608)
            after_siege = after_state["active_siege"]
            assert after_siege["siege_id"] == original_siege_id
            assert after_siege["player_army_besieging"] is False
            assert after_siege["current_work"]["raw"] == progressed_work
            assert after_state["is_occupied"] is False
            durable = json.loads(driver._native_driver_state_path().read_bytes())
            assert durable["command_history"][:len(retained)] == retained
            recorded = [row for row in durable["command_history"] if row["command"] == "life-advance"]
            assert len(recorded) == 1 and recorded[0]["result"] == result
            saved = await client.call_tool("ck3_save_checkpoint", {"expected_revision": after["revision"]})
            assert not saved.is_error, saved.content
            checkpoint = saved.structured_content["checkpoint"]
            assert checkpoint["status"] == "saved"
            assert checkpoint["date_raw"] == after["date_raw"]
            assert checkpoint["episode_character_id"] == 29829
            assert checkpoint["size"] == (save_dir / "xar_checkpoint.ck3").stat().st_size
            assert isinstance(checkpoint["sha256"], str) and len(checkpoint["sha256"]) == 64
            return {"phase": plan["phase"], "before_siege_id": original_siege_id,
                "stored_player_leader": False, "subject_contribution": plan["siege_state"]["subject_contribution"],
                "advance": result, "after_date_raw": after["date_raw"],
                "after_current_work_raw": after_siege["current_work"]["raw"],
                "occupation_changed": False, "checkpoint": checkpoint}

    report = asyncio.run(run())
    driver.close()
    output_path = os.environ.get("XAR_FOREIGN_SIEGE_MATERIAL_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"schema": "xar.siege-speed5-native-clock-service-first12004.v1",
            "input_packet": str(packet_path), "result": report,
            "boundary": "reused qualified whole input and ClockProvider; synthetic LIFE/clock/work/file outputs; real registered admitted LIFE/siege normal Service, Driver, full public history export, persistence and checkpoint materialization",
            "production_live": False, "game_days_credit": 0, "capture_credit": False,
            "old_qualification_replay": False}, indent=2) + "\n", encoding="utf-8")
