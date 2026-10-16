"""Focused contract tests for cold-restored construction readbacks.

The fixture is a reduced, immutable N40 P02 AUTO11 receipt. No game or SDK is
started by these tests.
"""

import copy
import json
from pathlib import Path

import pytest

from construction_cold_readback_classifier_v1 import classify_construction_cold_requery_v1


FIXTURE = Path(__file__).with_name("fixtures") / "construction_cold_readback_p02_0011_minimal.json"


def _case():
    row = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return row["body"], row["state"], row["initial_frame"], row["game_pid"]


def _next(body, *, date, native, public, proof, phase="construction_completion_watch",
          completed=False):
    result = copy.deepcopy(body)
    result["plan"]["phase"] = phase
    result["plan"]["construction_pending_action"] = copy.deepcopy(body["result"])
    frame = result["planning_source_frame"]
    frame.update(date_raw=date, native_revision=native, revision=public,
                 snapshot_id=f"native:{native}")
    inner = result["result"]
    inner.update(post_date_raw=date, post_native_revision=native,
                 post_public_revision=public, post_snapshot_id=f"native:{native}",
                 post_proof_epoch=proof, completion_last_check_date_raw=date)
    if completed:
        inner.update(completion_status="completed", completion_observed_date_raw=date)
    progress = inner["construction_progress_observation"]
    progress.update(date_raw=date, native_revision=native,
                    snapshot_id=f"native:{native}")
    income = inner["construction_province_income_observation"]
    income.update(date_raw=date, native_revision=native,
                  snapshot_id=f"native:{native}")
    if completed:
        progress.update(status="not_active", native_remaining_work_raw=None,
                        native_progress_divisor_raw=None)
    return result


def test_actual_cold_receipt_reconciles_without_new_construction_credit():
    body, state, initial, pid = _case()
    before = copy.deepcopy(state)
    observation, after = classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid)
    action = body["result"]["action_request_id"]
    assert observation["category"] == "construction_cold_readonly_reconciliation_observed"
    assert observation["fresh_bridge_pid"] == pid == 226540
    assert observation["old_bridge_pid"] == 270044
    assert observation["typed_nonmaterial_observation"] is True
    assert observation["construction_material_verified"] is False
    assert observation["construction_start_verified"] is False
    assert observation["construction_completion_verified"] is False
    assert observation["business_success_inferred"] is False
    assert observation["replay_allowed"] is False
    assert after["construction_actions"][action]["binding"] == before["construction_actions"][action]["binding"]
    assert before == state
    assert after["construction_actions"][action]["cold_readback_generation_v1"]["last_native_revision"] == 3


def test_due_monthly_readback_and_completion_credit_once():
    body, state, initial, pid = _case()
    _, state = classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid)
    action = body["result"]["action_request_id"]
    binding = copy.deepcopy(state["construction_actions"][action]["binding"])
    monthly = _next(body, date=53234016, native=100, public=99, proof=104000)
    observed, state = classify_construction_cold_requery_v1(
        monthly, state=state, initial_frame=initial, game_pid=pid)
    assert observed["construction_completion_verified"] is False
    assert observed["construction_start_verified"] is False
    completed = _next(monthly, date=53234736, native=200, public=199,
                      proof=105000, completed=True)
    observed, state = classify_construction_cold_requery_v1(
        completed, state=state, initial_frame=initial, game_pid=pid)
    assert observed["construction_completion_verified"] is True
    assert observed["construction_start_verified"] is False
    repeated = _next(completed, date=53234736, native=200, public=200,
                     proof=105100, phase="construction_completed_income_receipt",
                     completed=True)
    observed, state = classify_construction_cold_requery_v1(
        repeated, state=state, initial_frame=initial, game_pid=pid)
    assert observed["construction_completion_verified"] is False
    assert state["construction_actions"][action]["binding"] == binding


def test_untracked_same_process_watch_uses_original_classifier():
    body, state, initial, pid = _case()
    body["plan"]["phase"] = "construction_completion_watch"
    assert classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid) is None


def _same_game_worker_reset():
    # Synthetic epoch change applied to the retained cold-readback fixture.
    # It is not represented as a second original native receipt.
    body, state, initial, pid = _case()
    _, state = classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid)
    action = body["result"]["action_request_id"]
    tracker = state["construction_actions"][action]["cold_readback_generation_v1"]
    tracker.update(last_connection_generation=16, last_native_revision=156,
                   last_public_revision=200, last_proof_epoch=300000)
    pending = copy.deepcopy(body["result"])
    pending.update(post_native_revision=156, post_public_revision=200,
                   post_proof_epoch=300000)
    body["plan"]["construction_pending_action"] = pending
    return body, state, initial, pid


def test_same_game_worker_reset_rebinds_readonly_without_action_or_completion_credit():
    body, state, initial, pid = _same_game_worker_reset()
    original = copy.deepcopy(state)
    observation, after = classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid)
    assert observation["category"] == "construction_same_game_worker_epoch_readonly_rebind_observed"
    assert observation["typed_nonmaterial_observation"] is True
    assert observation["construction_material_verified"] is False
    assert observation["construction_completion_verified"] is False
    assert observation["replay_allowed"] is False
    assert state == original
    action = body["result"]["action_request_id"]
    assert after["construction_actions"][action]["binding"] == original["construction_actions"][action]["binding"]
    assert after["construction_actions"][action]["cold_readback_generation_v1"]["last_native_revision"] == 3
    with pytest.raises(ValueError, match="prior verified readback"):
        classify_construction_cold_requery_v1(body, state=after, initial_frame=initial, game_pid=pid)


def test_same_game_worker_reset_requires_matching_prior_readback_and_reset_generation():
    body, state, initial, pid = _same_game_worker_reset()
    body["planning_source_frame"]["connection_generation"] = 16
    with pytest.raises(ValueError, match="prior verified readback"):
        classify_construction_cold_requery_v1(body, state=state, initial_frame=initial, game_pid=pid)


def test_monthly_requires_due_date_and_new_proof():
    body, state, initial, pid = _case()
    _, state = classify_construction_cold_requery_v1(
        body, state=state, initial_frame=initial, game_pid=pid)
    premature = _next(body, date=53233369, native=4, public=3, proof=103172)
    with pytest.raises(ValueError, match="monthly completion watch is not due"):
        classify_construction_cold_requery_v1(
            premature, state=state, initial_frame=initial, game_pid=pid)
    stale = _next(body, date=53234016, native=100, public=99, proof=103171)
    with pytest.raises(ValueError, match="fresh readonly receipt is not on the current frame"):
        classify_construction_cold_requery_v1(
            stale, state=state, initial_frame=initial, game_pid=pid)


@pytest.mark.parametrize("mutation", [
    lambda b, s, p: b["planning_source_frame"].__setitem__("bridge_pid", p + 1),
    lambda b, s, p: b["planning_source_frame"].__setitem__("actor_character_id", 1),
    lambda b, s, p: b["result"].__setitem__("post_bridge_pid", 270044),
    lambda b, s, p: b["result"].__setitem__("post_date_raw", 53233367),
    lambda b, s, p: b["result"]["construction_progress_observation"].__setitem__("snapshot_id", "native:1594"),
    lambda b, s, p: b["result"]["construction_selected_intent"].__setitem__("selected_query_performed_new_submission", True),
    lambda b, s, p: s["construction_actions"][b["result"]["action_request_id"]].__setitem__("pending", True),
])
def test_wrong_identity_frame_or_submitted_action_rejected(mutation):
    body, state, initial, pid = _case()
    mutation(body, state, pid)
    with pytest.raises(ValueError, match="construction cold readonly requery rejected"):
        classify_construction_cold_requery_v1(
            body, state=state, initial_frame=initial, game_pid=pid)
