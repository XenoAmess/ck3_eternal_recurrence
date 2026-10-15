"""An unreadable typed event may use only its exact Native top-root catalogue."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer import strategy
from xar_autoplayer.mandatory_choice_planning_v1 import (
    QUERY_CAPABILITY, QUERY_STEP, SELECT_STEP, plan_native_mandatory_choice_v1,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mandatory_choice_v1"


def _case():
    native = json.loads((FIXTURES / "native-query-event-same-root.json").read_text(
        encoding="utf-8"))
    actual = json.loads((FIXTURES / "p09-event53-unavailable-typed-query.json").read_text(
        encoding="utf-8"))["typed_result"]
    assert actual["current_event_window_context"]["unavailable_reason"] == "event_saved_scope_invalid"
    query = native["result"]
    dto = query["mandatory_choice"]
    frame = dto["frame_binding"]
    dto["typed_window_relation"]["typed_window_instance_id"] = 53
    snapshot = {
        "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "episode_run_id": frame["episode_run_id"],
        "played_character": {"character_id": frame["actor_character_id"], "alive": True},
        "diagnostics": {"bridge_pid": frame["game_pid"],
                        "connection_generation": frame["connection_generation"]},
        "active_event": {"instance_id": 53, "option_count": 4},
        "pending_character_interaction": None,
        "top_exclusive_modal_choice_hint": {
            "status": "present", "owner_verified": True,
            "source": "application_main_pump_observed_modal_receiver",
            "max_observation_age_ms": 2000,
            "opaque_root_id": dto["window_instance_id"]},
    }
    actual.update(queried_snapshot_id=frame["snapshot_id"],
                  queried_revision=frame["revision"],
                  queried_native_revision=frame["native_revision"],
                  snapshot_revision=frame["native_revision"],
                  date_raw=frame["date_raw"])
    actual["current_event_window_context"].update(
        snapshot_revision=frame["native_revision"], date_raw=frame["date_raw"])
    rows = [
        {"command": "auto-turn", "ok": True,
         "result": {"auto_turn": {
             "selected_step": "query-current-event-window-context-v1",
             "result": actual}}},
        {"command": QUERY_STEP, "ok": True, "result": query},
    ]
    return rows, snapshot


def _plan(rows, snapshot):
    return plan_native_mandatory_choice_v1(
        rows, snapshot=snapshot, action_steps={QUERY_STEP, SELECT_STEP},
        bridge_capabilities={QUERY_CAPABILITY})


def test_actual_p09_unavailable_event53_accepts_only_proved_same_root_token():
    rows, snapshot = _case()
    assert strategy._same_frame_event_window_context(rows, snapshot)["status"] == "unavailable"
    plan = _plan(rows, snapshot)
    assert plan["selected_step"] == SELECT_STEP
    assert plan["unknown_mandatory_choice_v1"]["typed_event_unavailable_same_root_fallback"] is True
    context = plan["unknown_mandatory_choice_v1"]["typed_event_unavailable_context"]
    assert context["unavailable_reason"] == "event_saved_scope_invalid"
    assert context["options"] is None
    assert plan["unknown_mandatory_choice_v1"]["selection"]["action_token"] == (
        rows[-1]["result"]["mandatory_choice"]["choices"][0]["action_token"])


def test_partial_source_identity_is_diagnostic_until_full_generic_query():
    rows, snapshot = _case()
    context = rows[0]["result"]["auto_turn"]["result"]["current_event_window_context"]
    context.update(event_definition_key="stewardship_general.1054",
                   calculated_event_id=21054, runtime_stats_ordinal=3)
    context["readiness"]["event_definition_identity_ready"] = True
    before_query = _plan(rows[:1], snapshot)
    assert before_query["selected_step"] == QUERY_STEP
    stale = copy.deepcopy(rows)
    stale[-1]["result"]["queried_revision"] -= 1
    assert _plan(stale, snapshot)["selected_step"] == QUERY_STEP
    verified = _plan(rows, snapshot)
    assert verified["selected_step"] == SELECT_STEP
    captured = verified["unknown_mandatory_choice_v1"]["typed_event_unavailable_context"]
    assert captured["event_definition_key"] == "stewardship_general.1054"
    assert captured["status"] == "unavailable" and captured["options"] is None


def test_stale_typed_read_or_different_root_never_borrows_event_fallback():
    rows, snapshot = _case()
    stale = copy.deepcopy(rows)
    stale[0]["result"]["auto_turn"]["result"]["queried_native_revision"] -= 1
    assert _plan(stale, snapshot) is None
    wrong = copy.deepcopy(rows)
    wrong[-1]["result"]["mandatory_choice"]["typed_window_relation"][
        "typed_window_instance_id"] = 52
    assert _plan(wrong, snapshot) is None
    changed_root = copy.deepcopy(rows)
    changed_root[-1]["result"]["mandatory_choice"]["typed_window_relation"][
        "typed_opaque_root_id"] = "0xother"
    assert _plan(changed_root, snapshot) is None


def test_available_typed_event_retains_typed_selector_priority(monkeypatch):
    rows, snapshot = _case()
    monkeypatch.setattr(strategy, "_same_frame_event_window_context",
                        lambda _rows, _snapshot: {
                            "status": "available", "current_event_instance_id": 53})
    assert _plan(rows, snapshot) is None
