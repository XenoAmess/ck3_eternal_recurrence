"""Production AUTO/Driver boundary with synthetic transport and camera OS work."""
from copy import deepcopy
from contextlib import contextmanager
import threading
import time

import pytest

from test_native_bridge_driver import (
    FakeEndpoint, _army, _hello, _snapshot, _tactical_sentinel_status, _war,
)
from xar_autoplayer.bridge.auto_camera_follow import LatestCameraFollowWorker
from xar_autoplayer.bridge.auto_camera_pre_advance_v1 import camera_pre_advance_scope_v1
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.realm_overview_camera import EXACT_SHA
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import battle_decision_epoch_advance_step
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex


class ScheduleSpy:
    def __init__(self, order):
        self.calls, self.order = [], order

    def schedule(self, payload, *, urgent=False):
        self.order.append("urgent" if urgent else "post")
        self.calls.append((deepcopy(payload), urgent))
        return {"status": "scheduled", "request_id": f"camera-{len(self.calls)}", "urgent": urgent}

    def latest_actual(self):
        return None


@contextmanager
def tactical(monkeypatch, *, bad_arm=False):
    monkeypatch.setenv("XAR_CK3_ARMY_TIMING_JSONL", "")
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=.1, life_advance_timeout_seconds=.1)
    hello = _hello("game.state.snapshot", "game.command.set-speed-3",
        "game.command.resume-map", "game.command.pause-map",
        "game.command.research-arm-tactical-daily-sentinel-v1-N",
        "game.command.research-query-tactical-daily-sentinel-v1")
    hello.update(expected_ck3_version="1.20.0.4", expected_ck3_sha256=EXACT_SHA)
    endpoint.publish(hello)
    start, target, ending = 53171400, 53171760, 53171448
    player = {"character_id": 31254, "alive": True}

    def snapshot(revision, *, date=start, speed=1, province=1):
        army = _army(501, province_id=province, in_combat=True)
        return _snapshot(revision, date_raw=date, speed=speed, played_character=player,
                         active_wars=[_war(allied_armies=[army])], player_armies=[army])

    endpoint.publish(snapshot(1))
    order = []
    arm = _tactical_sentinel_status(state="armed", generation=7, starting_date_raw=start,
        target_date_raw=target, observed_date_raw=start, speed=3, mode="decision_epoch",
        army_count=1, combat_count=0 if bad_arm else 1)
    stop = _tactical_sentinel_status(state="triggered", generation=7, starting_date_raw=start,
        target_date_raw=target, observed_date_raw=ending, speed=3, mode="decision_epoch",
        army_count=1, completed_daily_ticks=2, trigger_flags=1 << 6,
        trigger_reasons=["combat_phase_changed"], overshoot_days=0,
        pause_wrapper_called=True, pause_observed=True)

    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        step = frame["step"]
        order.append(step)
        result = {"step": step, "accepted": True, "status": "available"}
        if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            result["tactical_daily_sentinel"] = arm
        elif step == "research-query-tactical-daily-sentinel-v1":
            result["tactical_daily_sentinel"] = stop
        endpoint.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": frame["request_id"], "ok": True, "result": result})
        if step == "set-speed-3":
            # A real new already available frame/position, not a date relabel.
            endpoint.publish(snapshot(2, speed=3, province=2))
        elif step == "resume-map":
            endpoint.publish(snapshot(3, date=ending, speed=3, province=2))

    endpoint.send_hook = answer
    service = GameplayBridgeService(driver)
    service.bind_war_hotspot_camera_index(LandedProvinceIndex({1: "b_old", 2: "b_current"}, {}, ()))
    service._auto_camera_worker.close_without_wait()
    service._auto_camera_worker = ScheduleSpy(order)
    initial = driver.take_internal_semantic_snapshot()
    frame = service._observed_planning_source_frame(initial)
    planned = {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "planning_source_frame": frame, "plan": {"selected_step": battle_decision_epoch_advance_step(target)},
        "_auto_camera_hotspot_input": service._auto_camera_hotspot_input(initial, frame)}
    service.plan_turn = lambda: planned
    service._consume_sway_after_turn = lambda outcome: outcome
    service._consume_feast_after_turn = lambda outcome: outcome
    service._consume_initial_lifestyle_focus_after_turn_v1 = lambda outcome, **kwargs: outcome
    service._observe_declaration_cooldown_after_turn_v1 = lambda *args: None
    service._observe_family_cooldown_after_turn_v1 = lambda *args: None
    service._observe_wartime_family_cadence_after_turn_v1 = lambda *args: None
    try:
        yield service, driver, planned, order, initial
    finally:
        driver.close()


def test_real_auto_validates_arm_then_queues_current_hotspot_before_resume(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        def display(_):
            order.append("display_accepted")
        result = service.auto_turn(before_submit=display)
        urgent, post = service._auto_camera_worker.calls
        assert urgent[1] is True and post[1] is False
        assert urgent[0]["active_wars"][0]["allied_armies"][0]["current_province_id"] == 2
        assert planned["_auto_camera_hotspot_input"]["active_wars"][0]["allied_armies"][0]["current_province_id"] == 1
        arm_index = next(i for i, s in enumerate(order) if s.startswith("research-arm-"))
        assert order.index("display_accepted") < arm_index < order.index("urgent") < order.index("resume-map")
        assert order.index("post") > order.index("resume-map")
        receipt = result["result"]["camera_pre_advance_v1"]
        assert receipt["hotspot"]["title_key"] == "b_current"
        assert receipt["source_frame"]["date_raw"] == planned["planning_source_frame"]["date_raw"]
        assert receipt["new_game_queries"] == 0
        assert result["result"]["elapsed_days"] == 2
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


@pytest.mark.parametrize("decision", ["intercept", "raise"])
def test_before_submit_interception_or_error_never_queues_pre(monkeypatch, decision):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        def display(_):
            order.append("display")
            if decision == "raise":
                raise ValueError("original display error")
            return {"status": "not_accepted"}
        if decision == "raise":
            with pytest.raises(ValueError, match="original display error"):
                service.auto_turn(before_submit=display)
        else:
            assert service.auto_turn(before_submit=display)["status"] == "intercepted"
        assert not any(urgent for _, urgent in service._auto_camera_worker.calls)
        assert "resume-map" not in order
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


def test_real_arm_guard_failure_cannot_queue_pre_or_resume(monkeypatch):
    with tactical(monkeypatch, bad_arm=True) as (service, driver, planned, order, initial):
        with pytest.raises(BridgeUnavailableError, match="arm acknowledgement is inconsistent"):
            service.auto_turn(before_submit=lambda _: None)
        assert not service._auto_camera_worker.calls
        assert "resume-map" not in order
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


def test_sdk_resume_hold_after_valid_arm_cannot_queue_pre_or_resume(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        answer = driver.endpoint.send_hook
        def change_hold_after_arm(frame):
            answer(frame)
            if (frame.get("type") == "execute_step"
                    and frame.get("step", "").startswith("research-arm-")):
                driver._h3937_date_hold_active = lambda *args: True
        driver.endpoint.send_hook = change_hold_after_arm
        with pytest.raises(BridgeUnavailableError, match="H3937 date hold"):
            service.auto_turn(before_submit=lambda _: None)
        assert any(s.startswith("research-arm-") for s in order)
        assert not service._auto_camera_worker.calls
        assert "resume-map" not in order
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


def test_presentation_exception_preserves_original_business_primitives_and_result(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        baseline = driver.execute_step(planned["plan"]["selected_step"], expected_revision=planned["revision"])
        baseline_steps = list(order)
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        def broken(*args, **kwargs):
            raise RuntimeError("camera enqueue failed")
        service._auto_camera_worker.schedule = broken
        result = service.auto_turn(before_submit=lambda _: None)["result"]
        diagnostic = result.pop("camera_pre_advance_v1")
        assert diagnostic["status"] == "unavailable" and "camera enqueue failed" in diagnostic["reason"]
        assert order == baseline_steps
        # Separate synthetic Driver instances mint separate episode IDs.
        assert result.pop("episode_run_id").startswith("native-31254-")
        assert baseline.pop("episode_run_id").startswith("native-31254-")
        assert result == baseline
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


@pytest.mark.parametrize("change", ["actor", "episode", "pid", "generation", "date", "event", "unknown", "static",
                                   "map", "pending", "mandatory", "alive", "build"])
def test_pre_projection_rejects_changed_owner_date_mandatory_or_unknown(monkeypatch, change):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        current = deepcopy(initial)
        if change == "actor": current["played_character"]["character_id"] += 1
        elif change == "episode": current["episode_run_id"] += "-new"
        elif change == "pid": current["diagnostics"]["bridge_pid"] += 1
        elif change == "generation": current["diagnostics"]["connection_generation"] += 1
        elif change == "date": current["date_raw"] += 24
        elif change == "event": current["active_event"] = {"instance_id": 1}
        elif change == "unknown": service._war_hotspot_camera_index = None
        elif change == "map": current["map_ready"] = False
        elif change == "pending": current["pending_character_interaction"] = {"instance_id": 1}
        elif change == "mandatory": current["top_exclusive_modal_choice_hint"] = {"status": "present"}
        elif change == "alive": current["played_character"]["alive"] = False
        elif change == "build": current["diagnostics"]["hello"]["expected_ck3_sha256"] = "unknown"
        elif change == "static":
            for army in current["active_wars"][0]["allied_armies"]: army["in_combat"] = False
        with camera_pre_advance_scope_v1(service, planned):
            receipt = driver._ordinary_auto_camera_pre_resume_v1(step="synthetic_verified_boundary", current=current)
        assert receipt["status"] == "skipped"
        assert not service._auto_camera_worker.calls
        assert not hasattr(driver, "_ordinary_auto_camera_pre_resume_v1")


def test_nonadvancing_blocked_plan_never_calls_display_or_queues_pre(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        planned["plan"]["selected_step"] = None
        def unexpected(_):
            raise AssertionError("blocked plan cannot call before_submit")
        assert service.auto_turn(before_submit=unexpected)["status"] == "blocked"
        assert not any(urgent for _, urgent in service._auto_camera_worker.calls)
        assert "resume-map" not in order


def test_scope_restores_explicit_none_and_moving_projection_is_one_shot(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        driver._ordinary_auto_camera_pre_resume_v1 = None
        current = deepcopy(initial)
        army = current["active_wars"][0]["allied_armies"][0]
        army.update(in_combat=False, move_target_province_id=2)
        with camera_pre_advance_scope_v1(service, planned):
            callback = driver._ordinary_auto_camera_pre_resume_v1
            receipt = callback(step="synthetic_verified_boundary", current=current)
            again = callback(step="synthetic_verified_boundary", current=current)
        assert receipt["hotspot"]["reason"] == "moving_player_army"
        assert again["reason"] == "already_observed_resume_point"
        assert len(service._auto_camera_worker.calls) == 1
        assert driver._ordinary_auto_camera_pre_resume_v1 is None


def test_real_auto_pre_work_runs_during_native_action_and_post_refresh_is_kept(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        entered = threading.Event()
        seen = []
        def work(payload):
            seen.append(payload)
            entered.set()
            return {"status": "queued_native_presentation"}
        worker = LatestCameraFollowWorker(work, quiet_seconds=.01)
        service._auto_camera_worker = worker
        answer = driver.endpoint.send_hook
        def prolonged_answer(frame):
            if frame.get("type") == "execute_step" and frame.get("step") == "resume-map":
                # Only the synthetic transport waits: production gameplay does
                # not wait for camera execution or a camera settled result.
                assert entered.wait(2), "pre work was deferred until action completion"
                order.append("camera_ran_before_action_return")
            answer(frame)
        driver.endpoint.send_hook = prolonged_answer
        try:
            result = service.auto_turn(before_submit=lambda _: None)
            post_id = result["camera_follow"]["request_id"]
            wait_for(lambda: worker.latest_actual() is not None and worker.latest_actual()["request_id"] == post_id)
            assert len(seen) == 2
            assert seen[0]["source_frame"]["date_raw"] == planned["planning_source_frame"]["date_raw"]
            assert seen[1]["source_frame"]["date_raw"] == planned["planning_source_frame"]["date_raw"] + 2 * 24
            assert "camera_ran_before_action_return" in order
            assert result["result"]["elapsed_days"] == 2
        finally:
            worker.close_without_wait()


def wait_for(predicate):
    deadline = time.monotonic() + 2
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(.002)


def gated_worker(work, *, quiet=.25):
    release = threading.Event()
    worker = LatestCameraFollowWorker(work, quiet_seconds=quiet)
    original_run = worker._run
    def run():
        assert release.wait(2)
        original_run()
    worker._run = run
    return worker, release


def test_urgent_pre_is_not_swallowed_by_post_coalescing():
    seen = []
    worker, release = gated_worker(lambda payload: seen.append(payload) or {"status": "queued_native_presentation"}, quiet=.01)
    try:
        pre = worker.schedule("pre", urgent=True)
        post1 = worker.schedule("post-1")
        post2 = worker.schedule("post-2")
        assert worker._urgent_pending["request_id"] == pre["request_id"]
        assert post2["superseded_pending_request_id"] == post1["request_id"]
        release.set()
        wait_for(lambda: len(seen) == 2)
        assert seen == ["pre", "post-2"]
    finally:
        release.set()
        worker.close_without_wait()


def test_urgent_bypasses_quiet_and_drops_older_ordinary_frame():
    seen = []
    worker, release = gated_worker(lambda payload: seen.append(payload) or {"status": "queued_native_presentation"}, quiet=600)
    try:
        ordinary = worker.schedule("old-post")
        eligible = worker._pending["eligible_at"]
        newer = worker.schedule("newer-post")
        assert worker._pending["eligible_at"] == eligible
        pre = worker.schedule("pre", urgent=True)
        assert pre["superseded_pending_request_id"] == newer["request_id"]
        assert worker._pending is None
        assert worker._urgent_pending["eligible_at"] < eligible
        release.set()
        wait_for(lambda: seen)
        assert seen == ["pre"]
        assert ordinary["urgent"] is False and pre["urgent"] is True
    finally:
        release.set()
        worker.close_without_wait()


def test_long_action_starts_pre_work_while_business_keeps_running_and_post_survives():
    entered, finish_pre, business_done = threading.Event(), threading.Event(), threading.Event()
    seen = []
    def work(payload):
        seen.append(payload)
        if payload == "pre":
            entered.set()
            assert finish_pre.wait(2)
        return {"status": "queued_native_presentation"}
    worker = LatestCameraFollowWorker(work, quiet_seconds=0)
    try:
        began = time.monotonic()
        worker.schedule("pre", urgent=True)
        assert time.monotonic() - began < .2
        assert entered.wait(2)
        assert not business_done.is_set()
        # The ordinary operation can complete even while camera work is busy.
        business_done.set()
        post = worker.schedule("post")
        finish_pre.set()
        wait_for(lambda: worker.latest_actual() is not None and worker.latest_actual()["request_id"] == post["request_id"])
        assert seen == ["pre", "post"]
    finally:
        finish_pre.set()
        worker.close_without_wait()
