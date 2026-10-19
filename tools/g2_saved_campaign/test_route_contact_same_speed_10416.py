"""Closed original clock inputs; negative mutations are synthetic, no live I/O."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from route_contact_exact_day_outcome import classify_route_contact_horizon_one_day_v1 as classify


DATA = json.loads((Path(__file__).parent / "fixtures" /
                   "route10416_closed_classifier_inputs_v1.json").read_text(encoding="utf-8"))


def run(body, proof=None, original=None):
    expected = (original or body)["planning_source_frame"]
    def bound(row, *, initial_frame, game_pid):
        frame = row["planning_source_frame"]
        if (frame != expected or frame.get("status") != "complete"
                or frame.get("bridge_pid") != game_pid):
            raise ValueError("synthetic strict source binding rejected")
        return dict(frame)
    return classify(body, bind_gameplay_frame=bound,
                    initial_frame=expected, game_pid=30852,
                    same_speed_source_proof=proof)


def test_actual_three_requires_source_proof_and_completes_all_original_predicates():
    body = deepcopy(DATA["actual_three"]["body"])
    before = deepcopy(body)
    with pytest.raises(ValueError, match="same-speed omission lacks"):
        run(body)
    credit = run(body, deepcopy(DATA["source_qualified_proof"]))
    assert credit["actual_date_delta_raw"] == 24 and credit["actual_elapsed_days"] == 1
    assert credit["paired_after_metrics_still_required"] is True
    assert credit["replay_allowed"] is False and credit["business_success_inferred"] is False
    assert not credit["action_credit"] and not credit["material_verified"]
    assert body == before and len(body["result"]["actions"]) == 3


@pytest.mark.parametrize("change", ["absent", "driver", "helper", "freeze", "driver_mode",
    "speed", "bool_speed", "basis", "actor", "episode", "connection", "native", "date", "bool_binding"])
def test_unqualified_or_foreign_omission_is_rejected(change):
    body = deepcopy(DATA["actual_three"]["body"])
    proof = deepcopy(DATA["source_qualified_proof"])
    if change == "absent":
        proof = None
    elif change in {"driver", "helper", "freeze", "driver_mode"}:
        proof["source_pins"][change + "_sha256"] = "0" * 64
    elif change in {"speed", "bool_speed"}:
        proof["requested_speed"] = True if change == "bool_speed" else 1
    elif change == "basis":
        proof["basis"] = "unqualified"
    else:
        keys = {"actor": "actor_character_id", "episode": "episode_run_id",
                "connection": "connection_generation", "native": "native_revision",
                "date": "date_raw", "bool_binding": "connection_generation"}
        key = keys[change]
        proof["start_binding"][key] = ("foreign" if change == "episode" else
                                       True if change == "bool_binding" else 999)
    with pytest.raises(ValueError, match="same-speed omission lacks"):
        run(body, proof)


@pytest.mark.parametrize("field,value", [("generation", 570), ("overshoot_days", 1),
    ("signed_date_delta_from_target_raw", 24), ("pause_observed", False),
    ("trigger_reasons", ["terminal"]), ("speed", 1)])
def test_original_native_stop_guards_run_after_three_receipt_admission(field, value):
    body = deepcopy(DATA["actual_three"]["body"])
    stop = body["result"]["exact_day_native_clock"]["stopped"]
    stop[field] = value
    body["result"]["actions"][2]["result"]["tactical_daily_sentinel"][field] = value
    with pytest.raises(ValueError, match="native exact-day deadline/paused stop"):
        run(body, deepcopy(DATA["source_qualified_proof"]))


@pytest.mark.parametrize("change", ["missing", "order", "accepted", "query_clock"])
def test_three_native_receipts_must_all_match_exactly(change):
    body = deepcopy(DATA["actual_three"]["body"])
    rows = body["result"]["actions"]
    if change == "missing":
        rows.pop(1)
    elif change == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif change == "accepted":
        rows[1]["result"]["accepted"] = False
    else:
        rows[2]["result"]["tactical_daily_sentinel"]["generation"] = 570
    with pytest.raises(ValueError, match="native arm/resume/query receipts"):
        run(body, deepcopy(DATA["source_qualified_proof"]))


def test_actual_old_four_and_existing_observed_speed_row_need_no_new_proof():
    body = deepcopy(DATA["actual_four"]["body"])
    assert len(body["result"]["actions"]) == 4
    original = run(body)
    frame = body["planning_source_frame"]
    body["result"]["actions"][0]["result"] = {
        "status": "already_observed", "submitted": False, "accepted": None,
        "observed_speed": 3, "source_snapshot_id": frame["snapshot_id"],
        "source_native_revision": frame["native_revision"], "source_date_raw": frame["date_raw"]}
    assert run(body) == original
    assert original["actual_date_delta_raw"] == 24


def test_default_unrelated_and_foreign_owner_stay_unchanged():
    assert classify({"selected_step": "query-army-strengths-v1"},
                    bind_gameplay_frame=lambda *args, **kwargs: None) is None
    body = deepcopy(DATA["actual_three"]["body"])
    original = deepcopy(body)
    body["planning_source_frame"]["bridge_pid"] = 999
    with pytest.raises(ValueError, match="strict source binding rejected"):
        run(body, DATA["source_qualified_proof"], original=original)
