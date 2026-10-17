"""Production execute_step/error path, synthetic endpoints only.

The historical 869 target/date/negative handle shape motivates these cases.
The actual public Driver hook is compared with its diagnostic callback disabled.
Neither constructed running frame is claimed to be 869's actual missing frame.
"""
from contextlib import redirect_stderr
from io import StringIO
import json
from unittest.mock import patch

import pytest

from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot, _tactical_sentinel_status, _war
from xar_autoplayer.bridge.driver import StepPostconditionError
from xar_autoplayer.bridge import native_driver as runtime
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.tactical_pause_boundary_diagnostics_v1 import record_failure_v1
from xar_autoplayer.bridge.war_contract import war_objective_hold_sentinel_advance_step


def failed_run(change, *, observe):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=.1,
                         life_advance_timeout_seconds=.1, allow_stationary_objective_hold_sentinel_canary=True,
                         route_contact_timeline_speed=5, allow_route_contact_high_speed_ab=True)
    endpoint.publish(_hello("game.state.snapshot", "game.command.set-speed-5", "game.command.resume-map",
                            "game.command.pause-map", "game.command.research-arm-tactical-daily-sentinel-v1-N",
                            "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
                            "game.command.research-query-tactical-daily-sentinel-v1"))
    start, target = 53347608, 53347776
    player = _army(167772577, province_id=2619, army_state="regular", army_state_code=1,
                   route_province_ids=[], owner_character_id=40695, in_combat=False, retreating=False)
    war = _war(100663323, allied_armies=[player], war_objective_province_ids=[2619])
    war["player_is_primary_war_leader"] = True
    played = {"character_id": 40695, "alive": True}
    pending = {"instance_id": -1761607550, "sender_character_id": 59833, "auto_accept_notification": False}
    endpoint.publish(_snapshot(1, date_raw=start, played_character=played, active_wars=[war], player_armies=[player]))
    arm = _tactical_sentinel_status(state="armed", generation=42, starting_date_raw=start,
                                    target_date_raw=target, observed_date_raw=start, speed=5,
                                    mode="decision_epoch", army_count=1, combat_count=0)
    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        step = frame["step"]
        result = {"step": step, "accepted": True, "status": "submitted"}
        if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            result.update(status="available", tactical_daily_sentinel=arm)
        endpoint.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": frame["request_id"], "ok": True, "result": result})
        if step == "set-speed-5":
            endpoint.publish(_snapshot(2, date_raw=start, speed=5, played_character=played,
                                        active_wars=[war], player_armies=[player]))
        elif step == "resume-map":
            endpoint.publish(_snapshot(3, date_raw=target - 24 if change == "date" else target,
                                        speed=5, paused=False, played_character=played, active_wars=[war],
                                        player_armies=[player], pending_character_interaction=pending))
        elif step == "pause-map":
            after_pending = {**pending, "instance_id": pending["instance_id"] + (change == "identity")}
            endpoint.publish(_snapshot(4, date_raw=target, speed=5, paused=True,
                                        played_character=played, active_wars=[war], player_armies=[player],
                                        pending_character_interaction=after_pending))
    endpoint.send_hook = answer
    step = war_objective_hold_sentinel_advance_step(100663323, 167772577, 2619, target, timeline_speed=5)
    stderr = StringIO()
    try:
        observer = patch("xar_autoplayer.bridge.tactical_pause_boundary_diagnostics_v1.record_failure_v1",
                         wraps=record_failure_v1) if observe else patch(
            "xar_autoplayer.bridge.tactical_pause_boundary_diagnostics_v1.record_failure_v1", return_value=None)
        with redirect_stderr(stderr), observer as called, pytest.raises(StepPostconditionError) as caught:
            driver.execute_step(step)
        assert called.call_count == 1
        if observe:
            assert called.call_args.kwargs["fresh_boundary"] is runtime._fresh_battle_sentinel_player_decision_boundary
            assert called.call_args.kwargs["same_boundary"] is runtime._same_battle_sentinel_player_decision_boundary
            assert called.call_args.kwargs["decision_is_new"] is runtime._battle_sentinel_player_decision_is_new
        steps = [f["step"] for f in endpoint.frames if f.get("type") == "execute_step"]
        return caught.value, steps, stderr.getvalue()
    finally:
        driver.close()


def compare_observed_and_unobserved_public_failure(change):
    original_error, original_steps, original_stderr = failed_run(change, observe=False)
    error, steps, stderr = failed_run(change, observe=True)
    assert str(error) == str(original_error)  # Existing fullmatch recovery contracts remain intact.
    assert "did not stabilize on one fresh paused frame" in str(error)
    assert steps == original_steps
    assert steps.count("resume-map") == 1 and steps.count("pause-map") == 1
    assert not any(s.startswith("research-cancel-") for s in steps)
    assert error.step_result["elapsed_days"] == original_error.step_result["elapsed_days"] == 7
    assert original_stderr == ""
    assert len(stderr.splitlines()) == 1 and len(stderr.encode("utf-8")) <= 8193
    record = json.loads(stderr)
    assert record == error.step_result["player_decision_pause_diagnostics_v1"]
    assert record["diagnostic_only"] is True and record["new_native_queries"] == 0
    assert record["before_pause"]["paused"] is False and record["after_pause"]["paused"] is True
    assert record["before_pause"]["played_character_id"] == record["after_pause"]["played_character_id"] == 40695
    assert record["expected_boundary"]["instance_id"] == -1761607550
    return record


def test_production_date_drift_retains_original_failure_and_logs_actual_failed_predicates():
    record = compare_observed_and_unobserved_public_failure("date")
    assert record["before_pause"]["observed_date_raw"] == 53347752
    assert record["after_pause"]["observed_date_raw"] == 53347776
    assert record["observations"]["date_equal"] is False
    assert "original_fresh_boundary" in record["failed_predicates"]
    assert record["observations"]["public_revision_increased"] is True


def test_production_changed_notification_retains_original_failure_and_logs_identity_difference():
    record = compare_observed_and_unobserved_public_failure("identity")
    assert record["before_pause"]["observed_date_raw"] == record["after_pause"]["observed_date_raw"]
    assert record["inspected_boundary"]["instance_id"] == -1761607549
    assert "original_expected_boundary_identity" in record["failed_predicates"]
    assert record["observations"]["date_equal"] is True
