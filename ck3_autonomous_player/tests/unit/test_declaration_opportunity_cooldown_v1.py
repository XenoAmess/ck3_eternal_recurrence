"""A query round earns cooldown credit only after later verified non-declaration."""

from copy import deepcopy
from types import SimpleNamespace

from xar_autoplayer.bridge import declaration_opportunity_cooldown_v1 as cooldown
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn

from test_prewar_surrogate_authority_regression import _snapshot


def frame(date=1_000, revision=10, pid=123, actor=31_254, episode="run-a"):
    return {"status": "complete", "snapshot_id": f"native:{revision}",
            "native_revision": revision, "date_raw": date, "bridge_pid": pid,
            "actor_character_id": actor, "episode_run_id": episode}


def query(sequence):
    return {"step": "query-declarable-wars", "accepted": True,
            "status": "available", "query_sequence": sequence,
            "declarable_wars": [{"declaration_id": "a"}]}


def advance(start, end):
    return {"status": "executed", "selected_step": "life-advance",
            "result": {"step": "life-advance", "progress_status": "postcondition",
                       "starting_date_raw": start, "ending_date_raw": end,
                       "paused": True}}


def snapshot(wars=None, continuity=None, event=None):
    return {"paused": True, "active_wars": [] if wars is None else wars,
            "war_declaration_continuity_v1": continuity, "active_event": event,
            "pending_character_interaction": None}


def completed_round(state_dir, sequence, start, end):
    cooldown.observe_completed_query(state_dir, frame(start, sequence * 2), query(sequence))
    return cooldown.observe_after_turn(
        state_dir, frame(start, sequence * 2 + 1), advance(start, end),
        snapshot(), frame(end, sequence * 2 + 2))


def test_two_separate_completed_no_war_rounds_trigger_exact_month(tmp_path):
    assert completed_round(tmp_path, 1, 1_000, 1_168)["consecutive_no_war_rounds"] == 1
    assert cooldown.view(tmp_path, snapshot(), frame(1_168))["status"] == "inactive"
    result = completed_round(tmp_path, 2, 1_168, 1_336)
    assert result["status"] == "active"
    assert result["cooldown_until_date_raw"] == 1_336 + 30 * 24
    assert cooldown.view(tmp_path, snapshot(), frame(2_055))["status"] == "active"
    assert cooldown.view(tmp_path, snapshot(), frame(2_056))["status"] == "inactive"


def test_query_return_or_duplicate_collect_never_closes_a_round(tmp_path):
    first = cooldown.observe_completed_query(tmp_path, frame(), query(10))
    assert first["consecutive_no_war_rounds"] == 0
    assert first["pending_query_sequence"] == 10
    same_collect = cooldown.observe_completed_query(tmp_path, frame(1_000, 11), query(10))
    assert same_collect["pending_query_sequence"] == 10
    after = cooldown.observe_after_turn(
        tmp_path, frame(1_000, 12), advance(1_000, 1_024), snapshot(), frame(1_024, 13))
    assert after["consecutive_no_war_rounds"] == 1
    assert cooldown.observe_completed_query(tmp_path, frame(1_024, 14), query(10))[
        "pending_query_sequence"] is None
    assert cooldown.observe_completed_query(
        tmp_path, frame(1_024, 14), {**query(11), "status": "pending"})[
        "pending_query_sequence"] is None


def test_submitted_without_real_war_and_popup_do_not_count(tmp_path):
    cooldown.observe_completed_query(tmp_path, frame(), query(1))
    submitted = {"schema": "war-declaration-continuity-v1",
                 "status": "declaration_submitted", "native_response": "accepted"}
    after = cooldown.observe_after_turn(
        tmp_path, frame(1_000, 11), advance(1_000, 1_024),
        snapshot(continuity=submitted), frame(1_024, 12))
    assert after["pending_query_sequence"] == 1
    after = cooldown.observe_after_turn(
        tmp_path, frame(1_024, 13), advance(1_024, 1_048),
        snapshot(event={"event_id": "popup"}), frame(1_048, 14))
    assert after["consecutive_no_war_rounds"] == 0
    assert after["pending_query_sequence"] == 1


def test_real_war_resets_streak_but_ack_or_defense_does_not(tmp_path):
    completed_round(tmp_path, 1, 1_000, 1_024)
    cooldown.observe_completed_query(tmp_path, frame(1_024, 14), query(2))
    defensive = cooldown.view(tmp_path, snapshot(wars=[{"war_id": 7,
        "player_side": "defender"}]), frame(1_024, 14))
    assert defensive["consecutive_no_war_rounds"] == 1
    assert defensive["pending_query_sequence"] is None
    actual = {"schema": "war-declaration-continuity-v1", "status": "war_started",
              "native_response": "accepted", "postcondition_verified": True,
              "war_id": 9}
    assert cooldown.view(tmp_path, snapshot(wars=[{"war_id": 9,
        "player_side": "attacker"}], continuity=actual), frame(1_024, 15))[
        "consecutive_no_war_rounds"] == 0


def test_real_war_cancels_active_month_while_wrong_post_frame_cannot_count(tmp_path):
    cooldown.observe_completed_query(tmp_path, frame(), query(1))
    wrong = cooldown.observe_after_turn(
        tmp_path, frame(1_000, 11), advance(1_000, 1_024),
        snapshot(), frame(1_025, 12))
    assert wrong["pending_query_sequence"] == 1
    assert wrong["consecutive_no_war_rounds"] == 0
    assert cooldown.observe_after_turn(
        tmp_path, frame(1_000, 11), advance(1_000, 1_024),
        snapshot(), frame(1_024, 12))["consecutive_no_war_rounds"] == 1
    completed_round(tmp_path, 2, 1_024, 1_048)
    assert cooldown.view(tmp_path, snapshot(), frame(1_048))["status"] == "active"
    actual = {"schema": "war-declaration-continuity-v1", "status": "war_started",
              "native_response": "accepted", "postcondition_verified": True,
              "war_id": 9}
    reset = cooldown.view(tmp_path, snapshot(wars=[{"war_id": 9,
        "player_side": "attacker"}], continuity=actual), frame(1_048, 15))
    assert reset["status"] == "inactive"
    assert reset["consecutive_no_war_rounds"] == 0


def test_state_survives_service_restart_but_not_actor_episode_or_old_game_query(tmp_path):
    completed_round(tmp_path, 1, 1_000, 1_024)
    cooldown.observe_completed_query(tmp_path, frame(1_024, 14), query(2))
    # A new Service/SDK keeps the same campaign's completed streak. A cold
    # Game PID change discards only its unsettled query evidence.
    resumed = cooldown.view(tmp_path, snapshot(), frame(1_024, 15, pid=999))
    assert resumed["consecutive_no_war_rounds"] == 1
    assert resumed["pending_query_sequence"] is None
    assert cooldown.view(tmp_path, snapshot(), frame(1_024, 15, pid=999,
        episode="run-b"))["consecutive_no_war_rounds"] == 0


def test_service_uses_actual_query_and_advance_receipts_and_collect_payload(tmp_path):
    service = object.__new__(GameplayBridgeService)
    post = {**snapshot(), "snapshot_id": "native:13", "revision": 13,
            "native_revision": 13, "date_raw": 1_024, "episode_run_id": "run-a",
            "played_character": {"character_id": 31_254},
            "diagnostics": {"connection_generation": 2, "bridge_pid": 123}}
    service.driver = SimpleNamespace(state_dir=tmp_path,
        collect_declarable_wars_result_v1=lambda *args, **kwargs: {
            "status": "available", "request_id": "request-2",
            "declaration_result": query(2)})
    service.snapshot = lambda **kwargs: post
    receipt = service._observe_declaration_cooldown_after_turn_v1(
        {"planning_source_frame": frame()},
        {"status": "executed", "selected_step": "query-declarable-wars",
         "result": query(1)})
    assert receipt["pending_query_sequence"] == 1
    receipt = service._observe_declaration_cooldown_after_turn_v1(
        {"planning_source_frame": frame(1_000, 12),
         "_declaration_opportunity_cooldown_v1": receipt},
        advance(1_000, 1_024))
    assert receipt["consecutive_no_war_rounds"] == 1
    assert service.collect_declarable_wars_result_v1(
        "request-2", expected_revision=13)["status"] == "available"
    assert cooldown.view(tmp_path, post, frame(1_024, 13))[
        "pending_query_sequence"] == 2


def test_strategy_skips_stale_opportunities_during_cooldown_but_keeps_war_priority():
    peaceful = _snapshot()
    peaceful["declaration_opportunity_cooldown_v1"] = {
        "schema": cooldown.SCHEMA, "status": "active",
        "cooldown_until_date_raw": peaceful["date_raw"] + 720}
    original = deepcopy(peaceful)
    plan = choose_one_life_turn(
        [{"index": 1, "command": "save-checkpoint", "ok": True}],
        snapshot=peaceful, action_steps={"query-declarable-wars", "life-advance"})
    assert plan["phase"] == "native_war_discovery_cooldown"
    assert plan["selected_step"] == "life-advance"
    assert peaceful == original
    defensive = deepcopy(peaceful)
    defensive["active_wars"] = [{"war_id": 7, "player_side": "defender"}]
    defensive_plan = choose_one_life_turn(
        [{"index": 1, "command": "save-checkpoint", "ok": True}],
        snapshot=defensive, action_steps={"query-declarable-wars", "life-advance"})
    assert defensive_plan["phase"] != "native_war_discovery_cooldown"
