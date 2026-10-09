"""One compound FIRST: ordinary Service selection and the native clock driver.

Only the lower native endpoint and its game observations are synthetic. The H1
normalizer, complete-route projection, normal chooser, Driver dispatch, native
Arm submission and stopped-clock receipt validation use production code.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from test_native_bridge_driver import (
    FakeEndpoint,
    _army,
    _hello,
    _snapshot,
    _tactical_sentinel_status,
    _war,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _normalize_tactical_daily_sentinel_status,
)
from xar_autoplayer.bridge.route_contact_window_contract import (
    advance_route_contact_window_step,
)
from xar_autoplayer.bridge.route_contact_window_projection_v1 import (
    project_route_contact_window_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import (
    advance_route_contact_horizon_step,
    query_route_contact_horizon_step,
)


_START = 24_000
_SUBJECT = 11
_HOSTILE = 21
_TARGET = 2_585
_QUERY = query_route_contact_horizon_step(_SUBJECT, _TARGET, (_HOSTILE,))
_WINDOW = advance_route_contact_window_step(
    _SUBJECT, _TARGET, (_HOSTILE,), horizon_days=3,
)


def _horizon(*, second_day_contact: bool = False) -> dict[str, object]:
    hostile_route = [20, 31, _TARGET] if second_day_contact else [31, _TARGET]
    hostile_arrivals = [_START + 48, _START + 360, _START + 480] if second_day_contact else [
        _START + 360, _START + 480,
    ]
    return {
        "status": "available",
        "date_raw": _START,
        "snapshot_revision": 40,
        "subject_army_id": _SUBJECT,
        "target_province_id": _TARGET,
        "hostile_army_ids": [_HOSTILE],
        "subject_route": {
            "timeline_observable": True,
            "army_id": _SUBJECT,
            "current_province_id": 20,
            "effective_origin_province_id": 31,
            "route_province_ids": [31, _TARGET],
            "arrival_date_raws": [_START + 120, _START + 240],
        },
        "hostile_routes": [{
            "timeline_observable": True,
            "army_id": _HOSTILE,
            "current_province_id": 99,
            "effective_origin_province_id": hostile_route[0],
            "route_province_ids": hostile_route,
            "arrival_date_raws": hostile_arrivals,
        }],
        "horizon_start_date_raw": _START,
        "horizon_end_date_raw": _START + 24,
        "one_day_contact_free": True,
        "conflicts": [],
    }


def _driver_case(*, second_day_contact: bool = False, early_arrival: bool = False):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.2,
        life_advance_timeout_seconds=0.2,
    )
    endpoint.publish(_hello(
        "game.state.snapshot",
        "game.state.war-objectives",
        "game.state.army-routes",
        "game.command.query-route-contact-horizon-v1-N",
        "game.command.set-speed-1",
        "game.command.set-speed-3",
        "game.command.resume-map",
        "game.command.pause-map",
        "game.command.research-arm-tactical-daily-sentinel-v1-N",
        "game.command.research-query-tactical-daily-sentinel-v1",
    ))
    raw_horizon = _horizon(second_day_contact=second_day_contact)
    before = copy.deepcopy(raw_horizon)
    player = _army(
        _SUBJECT, soldiers=900, province_id=20,
        move_target_province_id=_TARGET, army_state="moving",
        route_province_ids=[31, _TARGET],
    )
    enemy = _army(
        _HOSTILE, soldiers=800, province_id=99, controllable=False,
        move_target_province_id=_TARGET, army_state="moving",
        route_province_ids=list(raw_horizon["hostile_routes"][0]["route_province_ids"]),
    )
    war = _war(
        allied_armies=[player], enemy_armies=[enemy], score=0,
        war_objective_province_ids=[_TARGET],
    )
    stop_days = 2 if early_arrival else 3
    stop = _START + stop_days * 24
    armed = _tactical_sentinel_status(
        state="armed", generation=17, starting_date_raw=_START,
        target_date_raw=_START + 72, observed_date_raw=_START, speed=3,
        mode="terminal_or_sentinel", army_count=2, combat_count=0,
    )
    stopped = _tactical_sentinel_status(
        state="triggered", generation=17, starting_date_raw=_START,
        target_date_raw=_START + 72, observed_date_raw=stop, speed=3,
        mode="terminal_or_sentinel", army_count=2, combat_count=0,
        completed_daily_ticks=stop_days,
        trigger_flags=1 << 16 if early_arrival else 1,
        trigger_reasons=["army_position_changed"] if early_arrival else ["date_deadline"],
        overshoot_days=0, pause_wrapper_called=True, pause_observed=True,
    )

    def publish(revision, *, date_raw=_START, speed=1, stopped_position=False):
        observed_player = {
            **player,
            "current_province_id": 31 if stopped_position else 20,
            "route_province_ids": [_TARGET] if stopped_position else [31, _TARGET],
        }
        observed_war = {**war, "allied_armies": [observed_player]}
        endpoint.publish(_snapshot(
            revision, date_raw=date_raw, speed=speed, paused=True,
            active_wars=[observed_war], player_armies=[observed_player],
            played_character={"character_id": 707, "alive": True},
        ))

    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        step = str(frame["step"])
        result = {"step": step, "accepted": True, "status": "available"}
        if step == _QUERY:
            result.update({
                "query_sequence": 1,
                "snapshot_revision": 40,
                "route_contact_horizon": copy.deepcopy(raw_horizon),
            })
        elif step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            result["tactical_daily_sentinel"] = copy.deepcopy(armed)
        elif step == "research-query-tactical-daily-sentinel-v1":
            result["tactical_daily_sentinel"] = copy.deepcopy(stopped)
        endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True, "result": result,
        })
        if step == "set-speed-3":
            publish(41, speed=3)
        elif step == "resume-map":
            publish(42, date_raw=stop, speed=3, stopped_position=early_arrival)

    publish(40)
    endpoint.send_hook = answer
    driver.execute_step(_QUERY, expected_revision=int(driver.take_snapshot()["revision"]))
    service = GameplayBridgeService(driver)
    plan = service.plan_turn()["plan"]
    return driver, endpoint, plan, raw_horizon, before


def test_normal_three_day_window_and_arrival_clock_receipt(tmp_path):
    native_wire_path = Path(os.environ["XAR_NORMAL_THREE_DAY_NATIVE_WIRE"])
    native_wire = json.loads(native_wire_path.read_text(encoding="utf-8-sig"))
    assert native_wire["schema"] == "xar.actual4-route-position-witness-fixture.v1"
    native_statuses = {
        f"{case}.{phase}": _normalize_tactical_daily_sentinel_status(
            native_wire[case][phase]["result"]["tactical_daily_sentinel"],
        )
        for case in ("position_case", "deadline_case")
        for phase in ("armed", "stopped")
    }
    for case in ("position_case", "deadline_case"):
        assert native_statuses[f"{case}.armed"]["state"] == "armed"
        assert native_statuses[f"{case}.stopped"]["state"] == "triggered"
    native_position_stop = native_statuses["position_case.stopped"]
    assert native_position_stop["trigger_flags"] == 1 << 16
    assert native_position_stop["trigger_reasons"] == ["army_position_changed"]
    assert native_position_stop["completed_daily_ticks"] == 2
    native_deadline_stop = native_statuses["deadline_case.stopped"]
    assert native_deadline_stop["trigger_reasons"] == ["date_deadline"]
    assert native_deadline_stop["completed_daily_ticks"] == 3

    records = []
    for early_arrival in (False, True):
        driver, endpoint, plan, raw, before = _driver_case(early_arrival=early_arrival)
        try:
            assert plan["selected_step"] == _WINDOW, plan
            assert _WINDOW in driver.capabilities()["action_steps"]
            history_before = copy.deepcopy(driver.take_snapshot()["native_command_history"])
            assert history_before and raw == before
            result = driver.execute_step(
                plan["selected_step"], expected_revision=int(driver.take_snapshot()["revision"]),
            )
            wire = [str(frame["step"]) for frame in endpoint.frames if frame.get("type") == "execute_step"]
            arms = [step for step in wire if step.startswith("research-arm-tactical-daily-sentinel-v1-")]
            assert arms == [
                f"research-arm-tactical-daily-sentinel-v1-{_START}-to-{_START + 72}"
                "-speed-3-mode-terminal-a-2-11-21"
            ], wire
            assert wire.count("resume-map") == 1 and "pause-map" not in wire
            assert result["sentinel_scope"] == "route_contact_window"
            assert result["progress_status"] == "postcondition"
            assert result["requested_horizon_days"] == 3
            assert result["elapsed_days"] == (2 if early_arrival else 3)
            assert result["ending_date_raw"] == _START + (48 if early_arrival else 72)
            assert result["trigger_reasons"] == (
                ["army_position_changed"] if early_arrival else ["date_deadline"]
            )
            assert result["external_rich_query_count"] == 0
            assert raw == before
            records.append({"case": "arrival_stops_day_two" if early_arrival else "three_days",
                            "plan": plan, "result": result, "wire_steps": wire})
        finally:
            driver.close()

    driver, endpoint, plan, raw, before = _driver_case(second_day_contact=True)
    try:
        projection = project_route_contact_window_v1(raw)
        assert raw["one_day_contact_free"] is True
        assert projection["contact_free"] is False
        assert projection["first_contact_date_raw"] == _START + 48
        assert projection["contact_free_whole_days"] == 1
        assert plan["selected_step"] == advance_route_contact_horizon_step(
            _SUBJECT, _TARGET, (_HOSTILE,),
        ), plan
        assert _WINDOW not in driver.capabilities()["action_steps"]
        assert raw == before
        assert not any(
            str(frame.get("step", "")).startswith("research-arm-tactical-daily-sentinel-v1-")
            for frame in endpoint.frames
        )
        records.append({"case": "day_two_contact_keeps_h1", "plan": plan,
                        "projection": projection})
    finally:
        driver.close()

    output = {
        "schema": "xar.normal-three-day-route-window-first12004.v1",
        "input_boundary": "synthetic native endpoint/game observations; real normal Service and native Driver",
        "native_producer_qualification": {
            "source_path": str(native_wire_path),
            "input_boundary": "new native fixture production-serialized command frames; original IDs and dates retained",
            "original_wire": native_wire,
            "normalized_statuses": native_statuses,
        },
        "records": records,
        "native_fixture_live": False,
        "production_live": False,
    }
    output_path = Path(os.environ.get("XAR_NORMAL_THREE_DAY_ROUTE_WINDOW_OUTPUT", tmp_path / "first.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
