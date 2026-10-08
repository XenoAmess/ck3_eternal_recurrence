"""Sole FIRST: observed own contribution uses the existing daily siege cadence.

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

from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot, _war
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.war_contract import normalize_objective_province_states
from xar_autoplayer.bridge.war_occupation_targets_contract import normalize_war_occupation_targets_v1


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
    date_raw, speed, native_revision = start_date, 1, envelope["snapshot_revision"]
    progressed_work = 100_000
    endpoint = FakeEndpoint()
    save_dir = tmp_path / "isolated-profile" / "save games"
    save_dir.mkdir(parents=True)
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        state_dir=tmp_path / "driver-state", save_dir=save_dir,
        command_timeout_seconds=0.1, checkpoint_timeout_seconds=1.0,
        checkpoint_poll_interval_seconds=0.005)
    driver.require_initial_lifestyle_focus_before_date_advance = False
    endpoint.publish(_hello(
        "game.state.snapshot", "game.state.active-wars", "game.state.player-armies",
        "game.state.army-routes", "game.state.war-objective-garrison",
        "game.state.war-objective-siege-progress", "game.command.set-speed-1",
        "game.command.set-speed-3", "game.command.set-speed-5",
        "game.command.resume-map", "game.command.pause-map", "game.command.save-checkpoint"))

    def publish(*, paused):
        nonlocal native_revision
        native_revision += 1
        observed = copy.deepcopy(original_rows)
        siege_state = next(row for row in observed if row["province_id"] == 2608)
        siege = siege_state["active_siege"]
        if date_raw > start_date:
            siege["current_work"]["raw"] = progressed_work
            siege["remaining_work"]["raw"] = siege["total_work"]["raw"] - progressed_work
            siege["progress_fraction"]["raw"] = progressed_work * 100_000 // siege["total_work"]["raw"]
        if not paused:
            for row in observed:
                row["siege_observable"] = False
                row["active_siege"] = None
        endpoint.publish(_snapshot(native_revision, date_raw=date_raw, speed=speed,
            paused=paused, played_character={"character_id": 29829, "alive": True},
            active_wars=[_war(100663329, allied_armies=[player], score=0,
                war_objective_province_ids=[2606, 2608], objective_province_states=observed)],
            player_armies=[player]))

    publish(paused=True)
    assert driver.state.diagnostics()["last_rejected_state_snapshot"] is None

    def answer(request):
        nonlocal date_raw, speed
        if request.get("type") != "execute_step":
            return
        step = request["step"]
        result = {"step": step, "accepted": True, "status": "submitted"}
        if step == "save-checkpoint":
            result["submission"] = {"sequence": len(endpoint.frames),
                "requested_save_name": "xar_checkpoint", "date_raw": date_raw}
        endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": result})
        if step.startswith("set-speed-"):
            speed = int(step.rsplit("-", 1)[1])
            publish(paused=True)
        elif step == "resume-map":
            # The retained R0047 sparse fast arm is exposed by the old path.
            # The corrected contribution classifier selects its slow daily arm.
            date_raw += (13 if speed == 5 else 1) * 24
            publish(paused=False)
        elif step == "pause-map":
            publish(paused=True)
        elif step == "save-checkpoint":
            (save_dir / "xar_checkpoint.ck3").write_bytes(
                f"synthetic siege material checkpoint at raw {date_raw}".encode("ascii"))
        else:
            raise AssertionError(f"unexpected extra primitive: {step}")
    endpoint.send_hook = answer

    async def run():
        async with Client(create_server(driver)) as client:
            planned = await client.call_tool("ck3_plan_turn", {})
            assert not planned.is_error, planned.content
            plan = planned.structured_content["plan"]
            assert plan["phase"] == "native_war_siege_progress", plan
            assert plan["selected_step"] == "life-advance"
            assert plan["siege_state"]["subject_contribution"]["status"] == "eligible"
            assert plan["siege_state"]["subject_contribution"]["matches_current_selection"] is False
            advanced = await client.call_tool("ck3_auto_turn", {})
            assert not advanced.is_error, advanced.content
            result = advanced.structured_content["result"]
            assert result["requested_horizon_days"] == result["elapsed_days"] == 1
            assert result["timeline_speed"] == 1 and result["paused"] is True
            assert [row["step"] for row in result["actions"]] == ["set-speed-1", "resume-map", "pause-map"]
            # This is a later independently published rich paused frame. The
            # running null was not interpreted as a completed siege/capture.
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
        output.write_text(json.dumps({"schema": "xar.foreign-siege-material-service-first12004.v1",
            "input_packet": str(packet_path), "result": report,
            "boundary": "reused qualified whole input; synthetic clock/work/file outputs; real registered normal Service, Driver and materialization",
            "production_live": False, "game_days_credit": 0, "capture_credit": False,
            "old_qualification_replay": False}, indent=2) + "\n", encoding="utf-8")
