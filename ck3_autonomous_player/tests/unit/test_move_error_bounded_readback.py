"""Real Service/Driver/primitive/history with delayed Native snapshot input.

The endpoint and snapshot I/O are fake. The planner input is preselected, so
this does not attest ordinary planner selection or actual Native execution.
Public 256 and Native 3207 deliberately differ, as in the original fixture.
"""
from copy import deepcopy
import time
from types import SimpleNamespace

import pytest

from test_move_unknown_ack_recovery import FIXTURE, classify, scenario
from test_native_bridge_driver import FakeEndpoint
from test_observed_move_intent import FIXTURE as OBSERVED_FIXTURE, TAIL
from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.service import GameplayBridgeService


def delayed_scenario(*, change=None, native_error=None):
    driver, sent, frame, run = scenario(
        change=change,
        native_error=native_error or "CK3 move-army state is unavailable",
    )
    before, after = deepcopy(FIXTURE["before"]), deepcopy(FIXTURE["after"])
    if change:
        change(before, after)
    published = []
    waits = []
    driver.take_snapshot = lambda: deepcopy(after if published else before)

    def read_changed_snapshot(revision, *, timeout_seconds):
        waits.append((revision, timeout_seconds))
        published.append(True)
        return deepcopy(after)

    driver.wait_for_change = read_changed_snapshot
    return driver, sent, frame, run, waits, before


def test_delayed_snapshot_uses_real_primitive_once_and_preserves_unknown_ack():
    driver, sent, frame, run, waits, _ = delayed_scenario()
    try:
        assert driver._execute_primitive_step.__func__ is native.NativeHeadlessGameplayDriver._execute_primitive_step
        assert driver._wait_for_snapshot.__func__ is native.NativeHeadlessGameplayDriver._wait_for_snapshot
        assert driver._record_command.__func__ is native.NativeHeadlessGameplayDriver._record_command
        body = run()
        assert len(sent) == 1 and sent[0]["expected_revision"] == 3207
        assert len(waits) == 1 and waits[0][0] == 256
        assert 0 < waits[0][1] <= 2.0
        result = body["result"]
        assert result["source_frame"]["revision"] == 256
        assert result["source_frame"]["native_revision"] == 3207
        assert result["observed_frame"]["revision"] == 257
        assert result["observed_frame"]["native_revision"] == 3208
        assert result["native_ack_status"] == "unknown_after_error"
        assert result["accepted"] is False
        assert result["native_error_evidence"]["native_request"] == sent[0]
        assert len(driver._command_history) == 1
        assert driver._command_history[0]["ok"] is False
        credit = classify(body, frame)
        assert credit["typed_nonmaterial_observation"] is True
        for key in ("primitive_accepted", "date_advance_observed", "business_success_inferred", "replay_allowed"):
            assert credit[key] is False
    finally:
        driver.close()


@pytest.mark.parametrize("change", [
    lambda before, after: after["diagnostics"].update(connection_generation=99),
    lambda before, after: after["played_character"].update(character_id=999),
    lambda before, after: after["player_armies"][0].update(route_province_ids=[5983, 5999]),
])
def test_mismatched_delayed_frame_preserves_error_and_one_submission(change):
    driver, sent, _, run, waits, _ = delayed_scenario(change=change)
    try:
        with pytest.raises(native._NativeCommandRejectedError):
            run()
        assert len(sent) == 1 and len(waits) == 1
        assert len(driver._command_history) == 1
        assert driver._command_history[0]["ok"] is False
    finally:
        driver.close()


def test_no_new_snapshot_exhausts_configured_bound_without_resubmission():
    driver, sent, _, run, waits, before = delayed_scenario()
    driver.command_timeout_seconds = 0.01

    def no_publication(revision, *, timeout_seconds):
        waits.append((revision, timeout_seconds))
        time.sleep(timeout_seconds)
        return deepcopy(before)

    driver.wait_for_change = no_publication
    try:
        with pytest.raises(native._NativeCommandRejectedError, match="CK3 move-army state is unavailable"):
            run()
        assert len(sent) == 1 and waits
        assert all(0 < timeout <= 0.01 for _, timeout in waits)
        assert len(driver._command_history) == 1
        assert driver._command_history[0]["ok"] is False
    finally:
        driver.close()


def test_other_native_error_never_waits_for_route_publication():
    driver, sent, _, run, waits, _ = delayed_scenario(native_error="unrelated native rejection")
    try:
        with pytest.raises(native._NativeCommandRejectedError, match="unrelated native rejection"):
            run()
        assert len(sent) == 1 and waits == []
        assert len(driver._command_history) == 1
        assert driver._command_history[0]["ok"] is False
    finally:
        driver.close()


def test_real_wire_observation_reaches_ordinary_horizon_then_existing_clock():
    # The starting frame is reconstructed from the actual later SEM shape;
    # Native error/republication are fake inputs. The twelve tail rows are
    # actual; the inert prefix only preserves their original flattened indexes.
    before = deepcopy(OBSERVED_FIXTURE["snapshot_457"])
    before.update(snapshot_id="native:6285", native_revision=6285, revision=303)
    army = next(a for a in before["player_armies"] if a["army_id"] == 167772577)
    army.update(move_target_province_id=None, route_province_ids=[],
                route_read_status="complete_empty", route_source_count=0,
                army_state="regular", army_state_code=1)
    after = deepcopy(OBSERVED_FIXTURE["snapshot_457"])
    after.update(snapshot_id="native:6286", native_revision=6286, revision=304)
    endpoint = FakeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
    driver.state_dir = None
    step = "move-army-167772577-to-2621"
    driver.capabilities = lambda: {"action_steps": [step], "bridge_capabilities": [
        native.MOVE_ARMY_CAPABILITY, native.ARMY_ROUTES_CAPABILITY]}
    published, sent, waits = [], [], []
    driver.take_snapshot = lambda: deepcopy(after if published else before)

    def publish_error(request):
        sent.append(deepcopy(request))
        endpoint.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": False,
                          "error": "CK3 move-army state is unavailable"})

    def publish_new_snapshot(revision, *, timeout_seconds):
        waits.append((revision, timeout_seconds))
        published.append(True)
        return deepcopy(after)

    endpoint.send_hook = publish_error
    driver.wait_for_change = publish_new_snapshot
    service = object.__new__(GameplayBridgeService)
    service.driver = driver
    service._auto_camera_worker = SimpleNamespace(schedule=lambda _: {"status": "test_no_camera"})
    source = service._observed_planning_source_frame(before)
    service.plan_turn = lambda: {
        "plan": {"policy": "one-life-turn-v1", "phase": "native_war_pursuit", "selected_step": step},
        "snapshot_id": before["snapshot_id"], "revision": before["revision"],
        "planning_source_frame": deepcopy(source),
    }
    try:
        body = service.auto_turn()
        assert len(sent) == 1 and sent[0]["expected_revision"] == 6285
        assert len(waits) == 1 and waits[0][0] == 303
        credit = classify(body, source)
        assert credit["typed_nonmaterial_observation"] is True
        assert credit["primitive_accepted"] is False
        assert credit["business_success_inferred"] is False
        assert credit["date_advance_observed"] is False
        assert driver._command_history[0]["ok"] is False
        assert TAIL["inert_prefix_is_actual_history"] is False
        history = [{"command": "history-elided-offline-fixture", "ok": False}
                   for _ in range(TAIL["inert_prefix_count"])]
        history.extend(deepcopy(TAIL["actual_rows"][:-1]))
        # Only this future counterfactual replaces the original failed row
        # with the real producer DTO. The actual error/projection stay intact.
        failed_position = TAIL["actual_rows"][7]["index"] - 1
        assert history[failed_position]["index"] == 7218
        history[failed_position] = {**deepcopy(driver._command_history[0]), "index": 7218}
        cap = OBSERVED_FIXTURE["capabilities_2"]
        query = OBSERVED_FIXTURE["route_query_451"]["selected_step"]
        snapshot = deepcopy(OBSERVED_FIXTURE["snapshot_462"])
        steps = list(cap["action_steps"]) + [query]

        def choose():
            return strategy.choose_one_life_turn(
                history, snapshot=snapshot, action_steps=steps,
                bridge_capabilities=cap["bridge_capabilities"],
                battle_speed_readiness=cap.get("battle_speed_readiness"))

        first = choose()
        assert first["phase"] == "native_war_route_contact_horizon"
        assert first["selected_step"] == query
        assert first["move_intent"]["native_ack_verified"] is False
        # This future Native horizon is explicitly synthetic, not evidence of
        # safety in the actual P44/P45 game or permission to execute a clock.
        horizon = deepcopy(OBSERVED_FIXTURE["route_query_451"]["result"])
        horizon.update(query_sequence=670, snapshot_revision=6286,
                       queried_snapshot_id="native:6286", queried_revision=304,
                       queried_native_revision=6286)
        horizon["route_contact_horizon"].update(snapshot_revision=6286, date_raw=53297328)
        history.append({"command": query, "ok": True, "result": horizon})
        clock = strategy.advance_route_contact_window_step(
            167772577, 2621, horizon["route_contact_horizon"]["hostile_army_ids"], horizon_days=3)
        steps.append(clock)
        second = choose()
        assert second["phase"] == "native_war_route_contact_horizon_progress"
        assert second["selected_step"] == clock
        assert len(sent) == 1
    finally:
        driver.close()
