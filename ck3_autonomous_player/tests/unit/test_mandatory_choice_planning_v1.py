from __future__ import annotations

import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.mandatory_choice_planning_v1 import (
    QUERY_CAPABILITY, QUERY_STEP, SELECT_STEP, plan_native_mandatory_choice_v1,
)
from xar_autoplayer.mandatory_choice_evidence_v1 import capture_before


def snapshot():
    return {"snapshot_id": "native:100", "revision": 20,
            "native_revision": 100, "date_raw": 53112345,
            "episode_run_id": "episode-1", "played_character": {"character_id": 31254},
            "diagnostics": {"bridge_pid": 555, "connection_generation": 3},
            "top_exclusive_modal_choice_hint": {
                "status": "present",
                "source": "application_main_pump_observed_modal_receiver",
                "opaque_root_id": "0xA", "owner_verified": True,
                "max_observation_age_ms": 2000},
            "active_event": None, "pending_character_interaction": None}


def frame():
    return {"game_pid": 555, "connection_generation": 3,
            "revision": 20, "native_revision": 100, "date_raw": 53112345,
            "actor_character_id": 31254, "episode_run_id": "episode-1",
            "snapshot_id": "native:100"}


def dto():
    return {"schema": "xar.native-mandatory-choice-window/v1",
            "query_id": "query-1", "frame_binding": frame(),
            "window_id": "modal-kind-7", "window_instance_id": "modal-instance-9",
            "window_type": "unknown", "choices_complete": True,
            "blocking_proof": {"kind": "exclusive_modal_blocks_input",
                               "verified": True, "source": "native.receiver",
                               "receiver_identity": "modal-instance-9"},
            "choices": [
                {"choice_id": "close", "action_token": "close-token", "role": "close_x",
                 "visible": True, "enabled": True, "is_choice": False,
                 "bounds": {"top": 0, "left": 0, "width": 10, "height": 10}},
                {"choice_id": "disabled", "action_token": "disabled-token", "role": "choice",
                 "visible": True, "enabled": False, "is_choice": True,
                 "bounds": {"top": 20, "left": 10, "width": 10, "height": 10}},
                {"choice_id": "right", "action_token": "right-token", "role": "choice",
                 "visible": True, "enabled": True, "is_choice": True,
                 "bounds": {"top": 30, "left": 80, "width": 10, "height": 10}},
                {"choice_id": "first-enabled", "action_token": "first-token", "role": "choice",
                 "visible": True, "enabled": True, "is_choice": True,
                 "bounds": {"top": 30, "left": 20, "width": 10, "height": 10}},
            ]}


def plan(commands=(), snap=None, steps=None, caps=None, **kwargs):
    return plan_native_mandatory_choice_v1(list(commands),
        snapshot=snapshot() if snap is None else snap,
        action_steps={QUERY_STEP} if steps is None else steps,
        bridge_capabilities={QUERY_CAPABILITY} if caps is None else caps,
        **kwargs)


def query_row(window=None):
    result = {"step": QUERY_STEP, "accepted": True,
              "queried_snapshot_id": "native:100", "queried_revision": 20,
              "queried_native_revision": 100,
              "mandatory_choice": dto() if window is None else window}
    return {"command": QUERY_STEP, "ok": True, "result": result}


def test_hint_queries_then_selects_first_actual_enabled_choice(tmp_path):
    first = plan()
    assert first["selected_step"] == QUERY_STEP
    second = plan([query_row()])
    assert second["selected_step"] == SELECT_STEP
    selection = second["unknown_mandatory_choice_v1"]["selection"]
    assert selection["choice_id"] == "first-enabled"
    assert selection["action_token"] == "first-token"
    assert second["mandatory_choice_decision"]["semantic_optimal"] is False
    ticket = capture_before(tmp_path, {"snapshot_id": "native:100", "revision": 20,
                                       "plan": second})
    assert Path(ticket["before"]["path"]).exists()


def test_reviewed_observed_ui_source_is_annotated_without_reusing_old_token(
        tmp_path, monkeypatch):
    from xar_autoplayer import mandatory_choice_offline_analysis_v1 as review
    known = {"known_recovery_source": "observed-UI",
             "source_key": "f" * 64, "observed_choice_id": "old-instance-choice",
             "business_effect_known": False, "semantic_optimal": False}
    monkeypatch.setattr(review, "lookup_observed_ui_recovery",
                        lambda _dto, **_kwargs: known)
    decided = plan([query_row()], known_review_root=tmp_path,
                   backend_sha256="b" * 64)
    assert decided["phase"] == "known_observed_ui_recovery_first_enabled"
    assert decided["known_ui_recovery_source"] == known
    assert decided["unknown_mandatory_choice_v1"]["selection"]["choice_id"] == "first-enabled"
    assert decided["unknown_mandatory_choice_v1"]["selection"]["action_token"] == "first-token"
    assert decided["unknown_mandatory_choice_v1"]["semantic_optimal"] is False


def test_known_event_requires_native_root_proof_before_generic_action():
    known = snapshot()
    known["active_event"] = {"instance_id": 9}
    assert plan(snap=known)["selected_step"] == QUERY_STEP
    assert plan([query_row()], snap=known) is None
    unknown = snapshot()
    unknown["top_exclusive_modal_choice_hint"]["status"] = "unknown"
    unknown["top_exclusive_modal_choice_hint"]["source"] = (
        "owner_pump_cache_unavailable_or_expired")
    unknown["top_exclusive_modal_choice_hint"]["owner_verified"] = False
    unknown["top_exclusive_modal_choice_hint"]["opaque_root_id"] = None
    assert plan(snap=unknown) is None
    for changed in ({"owner_verified": False}, {"opaque_root_id": None},
                    {"max_observation_age_ms": 5000},
                    {"source": "pipe_worker_readonly_modal_receiver_candidate"}):
        unverified = snapshot()
        unverified["top_exclusive_modal_choice_hint"].update(changed)
        assert plan(snap=unverified) is None


def test_capability_absent_blocks_only_observed_top_modal():
    result = plan(caps=set())
    assert result["phase"] == "unknown_mandatory_choice_mechanism_unavailable"
    assert result["selected_step"] is None


def test_stale_and_incomplete_catalogue_never_select():
    old = query_row()
    old["result"]["queried_native_revision"] = 99
    assert plan([old])["selected_step"] == QUERY_STEP
    incomplete = dto()
    incomplete["choices_complete"] = False
    assert plan([query_row(incomplete)])["selected_step"] is None


def test_failed_same_frame_query_is_not_retried():
    bad = query_row()
    bad["ok"] = False
    assert plan([bad])["phase"] == "unknown_mandatory_choice_query_failed"


def test_auto_turn_history_nested_query_receipt_is_consumed():
    native = query_row()["result"]
    row = {"command": "auto-turn", "ok": True,
           "result": {"auto_turn": {"selected_step": QUERY_STEP, "result": native}}}
    assert plan([row])["unknown_mandatory_choice_v1"]["selection"]["choice_id"] == "first-enabled"


def test_pending_token_cannot_be_dispatched_twice_to_same_blocking_instance():
    current = snapshot()
    current.update(snapshot_id="native:101", revision=21, native_revision=101)
    new_frame = {**frame(), "snapshot_id": "native:101", "revision": 21,
                 "native_revision": 101}
    same_window = dto()
    same_window["frame_binding"] = new_frame
    query = query_row(same_window)
    query["result"].update(queried_snapshot_id="native:101",
                           queried_revision=21, queried_native_revision=101)
    prior = {"command": "auto-turn", "ok": True,
             "result": {"auto_turn": {"selected_step": SELECT_STEP,
                "status": "pending", "result": {"accepted": True,
                    "verification_pending": True},
                "plan": {"unknown_mandatory_choice_v1": {
                    "frame_binding": frame(), "native_window": dto()}}}}}
    blocked = plan([prior, query], snap=current)
    assert blocked["phase"] == "unknown_mandatory_choice_pending_verification"
    assert blocked["selected_step"] is None
    different = copy.deepcopy(query)
    different["result"]["mandatory_choice"]["window_instance_id"] = "modal-instance-10"
    assert plan([prior, different], snap=current)["selected_step"] == SELECT_STEP
