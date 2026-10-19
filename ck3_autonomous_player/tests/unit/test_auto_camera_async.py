"""Focused offline checks for ordinary camera bypass and source-frame binding."""
from __future__ import annotations

import threading
import time

from xar_autoplayer.bridge import auto_camera_follow as camera
from xar_autoplayer.bridge import service
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex


def wait_for(predicate, timeout: float = 2.0):
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "worker did not finish"
        time.sleep(0.005)


def test_one_worker_latest_pending() -> None:
    entered = threading.Event()
    release = threading.Event()
    calls: list[int] = []

    def work(payload):
        n = len(calls) + 1
        calls.append(payload)
        if n == 1:
            entered.set()
            assert release.wait(2)
        return {"status": "available", "call": n}

    worker = camera.LatestCameraFollowWorker(work, quiet_seconds=0)
    first = worker.schedule(1)
    assert entered.wait(2)
    thread = worker._thread
    second = worker.schedule(2)
    third = worker.schedule(3)
    assert third["superseded_pending_request_id"] == second["request_id"]
    assert third["status"] == "scheduled"
    release.set()
    wait_for(lambda: worker.latest_actual() is not None
             and worker.latest_actual()["request_id"] == third["request_id"])
    assert calls == [1, 3]
    assert first["request_id"] != third["request_id"]
    assert worker._thread is thread
    assert worker.latest_actual()["same_frame_with_gameplay_claim"] is False
    worker.close_without_wait()


def test_failure_does_not_stop_worker() -> None:
    count = 0

    def work(payload):
        nonlocal count
        count += 1
        if count == 1:
            raise RuntimeError("presentation failure")
        return {"status": "available"}

    worker = camera.LatestCameraFollowWorker(work, quiet_seconds=0)
    first = worker.schedule("first")
    wait_for(lambda: worker.latest_actual() is not None)
    assert worker.latest_actual()["request_id"] == first["request_id"]
    assert worker.latest_actual()["status"] == "failed"
    assert len(worker.recent_failures()) == 1
    second = worker.schedule("second")
    wait_for(lambda: worker.latest_actual()["request_id"] == second["request_id"])
    assert worker.latest_actual()["status"] == "completed"
    worker.close_without_wait()


def test_auto_turn_business_first_and_source_binding() -> None:
    frame = {
        "snapshot_id": "native:9", "revision": 4, "native_revision": 9,
        "date_raw": 53144328, "episode_run_id": "episode-1",
        "played_character": {"character_id": 31254, "alive": True},
        "map_ready": True,
        "diagnostics": {"connection_generation": 2, "bridge_pid": 127268},
    }
    observed = service.GameplayBridgeService._observed_planning_source_frame(frame)
    assert observed["status"] == "complete"
    assert observed["actor_character_id"] == 31254
    assert observed["bridge_pid"] == 127268
    assert service.GameplayBridgeService._observed_planning_source_frame(
        {**frame, "diagnostics": {}}
    )["status"] == "partial"

    entered = threading.Event()
    release = threading.Event()
    order: list[str] = []

    def present(payload):
        order.append("camera")
        entered.set()
        assert release.wait(2)
        return service.GameplayBridgeService._select_auto_camera_hotspot(obj, payload)

    class Driver:
        def take_internal_semantic_snapshot(self):
            return {**frame, "active_wars": [{"war_id": 16777224,
                "allied_armies": [{"army_id": 1, "current_province_id": 2640,
                                    "in_combat": True, "controllable": True}]}]}

    obj = service.GameplayBridgeService(Driver())
    obj._publish_camera_presentation_v1 = lambda intent, payload: {
        "status": "queued_native_presentation", "mode": intent["mode"],
        "native_command_pipe_used": False,
    }
    obj._war_hotspot_camera_index = LandedProvinceIndex(
        {2640: "b_enna"}, {2640: "c_enna"}, (),
    )
    obj._war_hotspot_camera_index_error = None
    obj.center_map_on_landed_title_v1 = lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("ordinary auto submitted Native camera"))
    )
    obj.capabilities = lambda: (
        (_ for _ in ()).throw(AssertionError("ordinary auto read Native capabilities"))
    )
    obj.snapshot = lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("ordinary auto read Native snapshot"))
    )
    obj._auto_camera_worker = camera.LatestCameraFollowWorker(
        present, quiet_seconds=0,
    )
    obj.plan_turn = lambda: {
        "plan": {"selected_step": "business"},
        "planning_source_frame": observed,
        "_auto_camera_hotspot_input":
            service.GameplayBridgeService._auto_camera_hotspot_input(
                {
                    "map_ready": True,
                    "active_wars": [{
                        "war_id": 16777224,
                        "allied_armies": [{
                            "army_id": 1,
                            "current_province_id": 2640,
                            "in_combat": True,
                            "controllable": True,
                        }],
                    }],
                },
                observed,
            ),
    }

    def execute(planned, *, before_submit):
        order.append("business")
        before_submit(planned)
        return {"status": "executed", "selected_step": "business"}

    obj._execute_planned_turn = execute
    obj._consume_sway_after_turn = lambda outcome: outcome
    obj._consume_feast_after_turn = lambda outcome: outcome
    obj._consume_initial_lifestyle_focus_after_turn_v1 = (
        lambda outcome, *, planning_frame: outcome
    )
    began = time.monotonic()
    result = obj.auto_turn(before_submit=lambda planned: order.append("decision"))
    assert time.monotonic() - began < 0.2
    assert order[:2] == ["business", "decision"]
    assert result["planning_source_frame"] == observed
    assert result["camera_follow"]["status"] == "scheduled"
    assert result["camera_follow"]["same_frame_with_gameplay_claim"] is False
    assert entered.wait(2)
    release.set()
    wait_for(lambda: obj._auto_camera_worker.latest_actual() is not None)
    actual = obj._auto_camera_worker.latest_actual()
    assert actual["status"] == "pending"
    assert actual["available"] is False
    assert actual["receipt"]["native_command_submitted"] is False
    assert actual["receipt"]["hotspot"]["province_id"] == 2640
    assert actual["receipt"]["source_frame"] == observed
    obj._auto_camera_worker.close_without_wait()


if __name__ == "__main__":
    test_one_worker_latest_pending()
    test_failure_does_not_stop_worker()
    test_auto_turn_business_first_and_source_binding()
    print("GREEN: latest coalescing, failure isolation, business-before-camera, source frame")
