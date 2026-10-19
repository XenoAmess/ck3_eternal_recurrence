"""Real auto_turn scheduling against a synthetic already-published cache."""
from __future__ import annotations

import copy

import pytest

from xar_autoplayer.bridge.realm_overview_camera import PeaceRealmCameraPolicy
from xar_autoplayer.bridge.service import GameplayBridgeService


def snapshot(day=0, *, public=10, native=20):
    return {
        "snapshot_id": f"native:{native}", "revision": public,
        "native_revision": native, "date_raw": 53144328 + day * 24,
        "episode_run_id": "episode", "paused": True, "map_ready": True,
        "played_character": {"character_id": 31254, "alive": True},
        "diagnostics": {"bridge_pid": 123, "connection_generation": 1,
                        "hello": {"expected_ck3_version": "1.20.0.4",
                                  "expected_ck3_sha256": "observed-build"}},
        "active_wars": [{"war_id": 1, "allied_armies": [{
            "army_id": 7, "current_province_id": 2604, "in_combat": True,
            "controllable": True}], "war_objective_province_ids": [2604]}],
        "player_armies": [], "active_event": None,
        "pending_character_interaction": None,
    }


class CacheDriver:
    def __init__(self):
        self.current = None
        self.cache_reads = 0
        self.error = None

    def take_internal_semantic_snapshot(self):
        self.cache_reads += 1
        if self.error:
            raise self.error
        return copy.deepcopy(self.current)

    def take_snapshot(self, *args, **kwargs):
        raise AssertionError("camera requested a Game snapshot")

    def request(self, *args, **kwargs):
        raise AssertionError("camera used the Game pipe")


class Worker:
    def __init__(self):
        self.payloads = []

    def schedule(self, payload):
        self.payloads.append(copy.deepcopy(payload))
        return {"status": "scheduled", "same_frame_with_gameplay_claim": False}


def run_turn(after, *, before=None, driver=None, result_status="executed",
             ending_date=None, presentation="enabled"):
    before = snapshot() if before is None else before
    driver = CacheDriver() if driver is None else driver
    service = GameplayBridgeService(driver)
    frame = service._observed_planning_source_frame(before)
    planned = {"planning_source_frame": frame,
               "_auto_camera_hotspot_input": service._auto_camera_hotspot_input(before, frame),
               "plan": {"selected_step": "life-advance"}}
    if presentation == "missing-input":
        planned.pop("_auto_camera_hotspot_input")
    elif presentation == "nonmapping-input":
        planned["_auto_camera_hotspot_input"] = None
    original = copy.deepcopy(planned)
    service.plan_turn = lambda: planned
    calls = []
    result = {"ending_date_raw": (after.get("date_raw") if ending_date is None
                                  and isinstance(after, dict) else ending_date),
              "marker": "business-result"}

    def execute(planned, *, before_submit):
        calls.append("business")
        driver.current = after
        return {"status": result_status, "selected_step": "life-advance", "result": result}

    service._execute_planned_turn = execute
    service._consume_sway_after_turn = lambda outcome: outcome
    service._consume_feast_after_turn = lambda outcome: outcome
    service._consume_initial_lifestyle_focus_after_turn_v1 = lambda outcome, **kw: outcome
    service._observe_declaration_cooldown_after_turn_v1 = lambda *args: None
    service._observe_family_cooldown_after_turn_v1 = lambda *args: None
    service._observe_wartime_family_cadence_after_turn_v1 = lambda *args: None
    worker = Worker()
    service._auto_camera_worker = worker
    if presentation == "absent-worker":
        service._auto_camera_worker = None
    elif presentation == "noncallable-worker":
        service._auto_camera_worker = type("DisabledWorker", (), {"schedule": None})()
    outcome = service.auto_turn()
    assert calls == ["business"]
    assert outcome["status"] == result_status and outcome["result"] is result
    assert planned == original
    assert outcome["planning_source_frame"] == frame
    return outcome, worker.payloads, driver


def test_eight_day_business_uses_current_positions_dates_and_build_without_query():
    after = snapshot(8, public=11, native=21)
    after["active_wars"][0]["allied_armies"][0]["current_province_id"] = 2700
    after["active_wars"][0]["war_objective_province_ids"] = [2700]
    after["diagnostics"]["hello"]["expected_ck3_sha256"] = "current-build"
    outcome, payloads, driver = run_turn(after)
    assert driver.cache_reads == 1 and len(payloads) == 1
    payload = payloads[0]
    assert payload["source_frame"]["date_raw"] == after["date_raw"]
    assert payload["source_frame"]["native_revision"] == 21
    assert payload["active_wars"][0]["allied_armies"][0]["current_province_id"] == 2700
    assert payload["active_wars"][0]["war_objective_province_ids"] == [2700]
    assert payload["source_build"]["executable_sha256"] == "current-build"
    assert after["date_raw"] - outcome["planning_source_frame"]["date_raw"] == 8 * 24 > 7 * 24
    assert after["date_raw"] - payload["source_frame"]["date_raw"] == 0
    assert outcome["camera_follow"]["same_frame_with_gameplay_claim"] is False


def test_same_frame_zero_day_action_remains_supported():
    outcome, payloads, driver = run_turn(snapshot())
    assert driver.cache_reads == 1
    assert payloads[0]["source_frame"] == outcome["planning_source_frame"]
    assert outcome["camera_follow"]["status"] == "scheduled"


@pytest.mark.parametrize("presentation", ["missing-input", "nonmapping-input",
                                        "absent-worker", "noncallable-worker"])
def test_ineligible_presentation_does_not_read_cache_or_replay_business(presentation):
    outcome, payloads, driver = run_turn(snapshot(8, public=11, native=21),
                                       presentation=presentation, result_status="pending")
    assert driver.cache_reads == 0 and payloads == []
    assert outcome["camera_follow"]["status"] == "unavailable"


@pytest.mark.parametrize("kind", ["missing", "exception", "partial", "date-backward",
                                  "native-backward", "public-backward", "before-end",
                                  "actor", "episode", "connection", "Game", "dead", "not-map"])
def test_invalid_cache_only_degrades_camera_and_never_replays_business(kind):
    after = snapshot(8, public=11, native=21)
    driver = CacheDriver()
    ending = None
    if kind == "missing":
        after = None
    elif kind == "exception":
        driver.error = ValueError("cached publication unavailable")
    elif kind == "partial":
        after.pop("native_revision")
    elif kind == "date-backward":
        after["date_raw"] = snapshot()["date_raw"] - 24
    elif kind == "native-backward":
        after["native_revision"] = 19
    elif kind == "public-backward":
        after["revision"] = 9
    elif kind == "before-end":
        ending = after["date_raw"] + 24
    elif kind == "actor":
        after["played_character"]["character_id"] = 40526
    elif kind == "episode":
        after["episode_run_id"] = "other-episode"
    elif kind == "connection":
        after["diagnostics"]["connection_generation"] = 2
    elif kind == "Game":
        after["diagnostics"]["bridge_pid"] = 999
    elif kind == "dead":
        after["played_character"]["alive"] = False
    elif kind == "not-map":
        after["map_ready"] = False
    outcome, payloads, driver = run_turn(after, driver=driver, ending_date=ending,
                                       result_status="pending")
    assert driver.cache_reads == 1 and payloads == []
    assert outcome["camera_follow"]["status"] == "unavailable"
    assert outcome["camera_follow"]["same_frame_with_gameplay_claim"] is False


def test_absent_cache_reader_has_no_fallback_to_preaction_armies():
    driver = CacheDriver()
    driver.take_internal_semantic_snapshot = None
    outcome, payloads, driver = run_turn(snapshot(8), driver=driver)
    assert driver.cache_reads == 0 and payloads == []
    assert outcome["camera_follow"]["status"] == "unavailable"


def test_current_mandatory_state_replaces_old_battle_and_interrupts_overview():
    after = snapshot(8, public=11, native=21)
    after["active_wars"] = []
    after["active_event"] = {"event_key": "observed-current-event"}
    after["pending_character_interaction"] = {"instance": 8}
    after["top_exclusive_modal_choice_hint"] = {"status": "present"}
    _, payloads, driver = run_turn(after)
    payload = payloads[0]
    assert driver.cache_reads == 1 and payload["active_wars"] == []
    assert payload["has_active_event"] is True
    assert payload["has_pending_interaction"] is True and payload["mandatory_choice"] is True
    policy = PeaceRealmCameraPolicy()
    policy.observe({**payload, "has_active_event": False,
                    "has_pending_interaction": False, "mandatory_choice": False}, None)
    policy.mode = "realm"
    assert policy.observe(payload, None)["mode"] == "cancel"
