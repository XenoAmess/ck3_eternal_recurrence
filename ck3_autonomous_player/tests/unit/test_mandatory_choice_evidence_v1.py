from __future__ import annotations

import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


from xar_autoplayer.mandatory_choice_evidence_v1 import (
    SCHEMA, capture_after, capture_before, collect_completed,
)


def planned():
    frame = {"snapshot_id": "snap-1", "revision": 4, "native_revision": 7,
             "date_raw": 100, "episode_run_id": "episode", "bridge_pid": 42,
             "connection_generation": 2, "actor_character_id": 123}
    dto = {"schema": "xar.native-mandatory-choice-window/v1", "window_id": "w1",
           "window_instance_id": "i1", "blocking_proof": {"kind": "exclusive_modal_blocks_input",
           "verified": True, "source": "native-receiver"}, "choices_complete": True,
           "frame_binding": frame, "choices": [
               {"choice_id": "c1", "action_token": "t1", "visible": True,
                "enabled": True, "is_choice": True,
                "bounds": {"left": 10, "top": 20, "width": 20, "height": 20}},
               {"choice_id": "c2", "action_token": "t2", "visible": True,
                "enabled": True, "is_choice": True,
                "bounds": {"left": 100, "top": 20, "width": 20, "height": 20}}]}
    capture = {"schema": SCHEMA, "frame_binding": frame, "native_window": dto,
               "blocking_proof_verified": True, "catalogue_complete": True,
               "selection": {"selected_step": "select-native-mandatory-choice-v1",
                             "choice_id": "c1", "action_token": "t1"}}
    return {"snapshot_id": "snap-1", "revision": 4,
            "plan": {"selected_step": "select-native-mandatory-choice-v1",
                     "unknown_mandatory_choice_v1": capture}}


def test_pair_preserves_full_catalogue_and_ack_is_not_completion(tmp_path):
    original = planned()
    ticket = capture_before(tmp_path, original)
    original["plan"]["unknown_mandatory_choice_v1"]["native_window"]["choices"].clear()
    assert collect_completed(tmp_path) == []
    record = capture_after(ticket, outcome={"status": "executed", "result": {
        "accepted": True, "mandatory_choice_postcondition": {"verified": False}}})
    assert record["original_blocking_window_advanced_verified"] is False
    rows = collect_completed(tmp_path)
    assert len(rows) == 1
    assert rows[0]["selection"]["choice_id"] == "c1"
    assert rows[0]["original_blocking_window_advanced_verified"] is False
    assert '"c2"' in Path(rows[0]["before"]).read_text(encoding="utf-8")
    assert collect_completed(tmp_path, [rows[0]["incident_id"]]) == []


def test_exact_postcondition_can_verify_original_window_only(tmp_path):
    ticket = capture_before(tmp_path, planned())
    result = {"accepted": True, "mandatory_choice_postcondition": {
        "verified": True, "old_window_id": "w1", "old_instance": "i1",
        "selected_choice_id": "c1", "old_window_no_longer_blocking": True}}
    assert capture_after(ticket, outcome={"result": result})[
        "original_blocking_window_advanced_verified"] is True
    wrong = copy.deepcopy(result)
    wrong["mandatory_choice_postcondition"]["selected_choice_id"] = "c2"
    other = capture_before(tmp_path, planned())
    assert capture_after(other, outcome={"result": wrong})[
        "original_blocking_window_advanced_verified"] is False


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(snapshot_id="stale"),
    lambda p: p["plan"].update(selected_step="different"),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"].update(blocking_proof_verified=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"].update(catalogue_complete=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"]["native_window"]["blocking_proof"].update(verified=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"]["native_window"].update(choices_complete=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"]["native_window"]["choices"][0].update(is_choice=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"]["native_window"]["choices"][0].update(enabled=False),
    lambda p: p["plan"]["unknown_mandatory_choice_v1"]["selection"].update(action_token="t2"),
])
def test_no_capture_without_exact_frame_and_native_proof(tmp_path, mutation):
    candidate = planned()
    mutation(candidate)
    with pytest.raises(ValueError):
        capture_before(tmp_path, candidate)
