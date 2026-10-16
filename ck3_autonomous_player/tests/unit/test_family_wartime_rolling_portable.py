"""Rolling family cooldown with committed P09 and P19 fact projections."""
import copy
import json
from pathlib import Path
from xar_autoplayer.bridge import family_wartime_opportunity_cadence_v1 as cadence

FIXTURES=Path(__file__).resolve().parents[1]/"fixtures"
ACTUAL=json.loads((FIXTURES/"family_wartime_noop_0210.json").read_text(encoding="utf-8"))
PROJECTED=json.loads((FIXTURES/"family_p19_completed_projection.json").read_text(encoding="utf-8"))

def observed(day, *, episode=None, heir=39979, changed_spouse=False, unknown=False):
    frame = copy.deepcopy(ACTUAL["frame"])
    plan = copy.deepcopy(ACTUAL["plan"])
    outcome = copy.deepcopy(ACTUAL["outcome"])
    frame["date_raw"] += day * 24
    frame["native_revision"] += day
    if episode is not None:
        frame["episode_run_id"] = episode
    relation = plan["family_marriage_current_relationship"]
    diagnostic = plan["family_marriage_private_diagnostic"]
    relation["native_revision"] = frame["native_revision"]
    relation["root_query_sequence"] += day
    relation["heir_character_id"] = heir
    diagnostic["date_raw"] = frame["date_raw"]
    diagnostic["native_revision"] = frame["native_revision"]
    diagnostic["episode_run_id"] = frame["episode_run_id"]
    diagnostic["legality_query_sequence"] += day
    diagnostic["observed_first_heir_character_id"] = heir
    source = {
        "status": "unknown" if unknown else "reviewed",
        "date_raw": frame["date_raw"],
        "native_revision": frame["native_revision"],
        "actor_character_id": frame["actor_character_id"],
        "episode_run_id": frame["episode_run_id"],
        "heir_character_id": heir,
        "player_spouse_signature": [None, None if changed_spouse else 30887,
                                    [] if changed_spouse else [30887]],
        "expected_successor_character_id": heir,
    }
    plan["_family_wartime_review_v1"] = source
    return frame, plan, outcome


def record(path, day, **kwargs):
    return cadence.observe_after_turn(path, *observed(day, **kwargs))


def test_actual_two_then_one_complete_recheck_after_thirty_days(tmp_path):
    first = record(tmp_path, 0)
    assert first["status"] == "inactive" and first["consecutive_noop_dates"] == 1
    second = record(tmp_path, 7)
    assert second["status"] == "active" and second["qualified_source"] is True
    expiry = second["cooldown_until_date_raw"]
    frame, _, _ = observed(35)
    assert cadence.view(tmp_path, {**frame, "date_raw": expiry - 24})["status"] == "active"
    assert cadence.view(tmp_path, {**frame, "date_raw": expiry})["status"] == "inactive"
    renewed = record(tmp_path, 42)
    assert renewed["status"] == "active" and renewed["remaining_days"] == 30
    assert record(tmp_path, 42)["cooldown_until_date_raw"] == renewed["cooldown_until_date_raw"]
    assert record(tmp_path, 49)["status"] == "active"


def test_changed_source_or_unknown_restarts_two_review_requirement(tmp_path):
    record(tmp_path, 0)
    record(tmp_path, 7)
    changed = record(tmp_path, 42, changed_spouse=True)
    assert changed["status"] == "inactive"
    assert changed["consecutive_noop_dates"] == 1
    assert changed["qualified_source"] is False
    assert record(tmp_path, 49, changed_spouse=True)["status"] == "active"
    assert record(tmp_path, 84, changed_spouse=True, unknown=True)["qualified_source"] is False
    assert record(tmp_path, 91, changed_spouse=True)["consecutive_noop_dates"] == 1


def test_material_and_actor_episode_reset_and_connection_rotation(tmp_path):
    record(tmp_path, 0)
    record(tmp_path, 7)
    frame, _, _ = observed(8)
    rotated = {**frame, "connection_generation": 99}
    assert cadence.view(tmp_path, rotated)["status"] == "active"
    assert cadence.view(tmp_path, {**frame, "actor_character_id": 1})["status"] == "inactive"
    assert cadence.view(tmp_path, {**frame, "episode_run_id": "other"})["status"] == "inactive"
    record(tmp_path, 0)
    record(tmp_path, 7)
    material = {"status": "executed", "selected_step":
                "query-observed-first-heir-marriage-result-v1-private",
                "result": {"status": "marriage", "material_result": True}}
    cleared = cadence.observe_after_turn(tmp_path, frame, {}, material)
    assert cleared["qualified_source"] is False and cleared["status"] == "inactive"


def test_p19_completed_query_replay_first_two_then_q7_renews(tmp_path):
    rows = [PROJECTED["rolling"][str(seq)]["projected"]
            for seq in (32, 40, 87, 95)]
    for index, body in enumerate(rows[:2]):
        receipt = cadence.observe_after_turn(tmp_path, body["planning_source_frame"],
                                             body["plan"], body)
        assert receipt["status"] == ("inactive" if index == 0 else "active")
    assert cadence.view(tmp_path, rows[2]["planning_source_frame"])["status"] == "inactive"
    q7 = cadence.observe_after_turn(tmp_path, rows[2]["planning_source_frame"],
                                    rows[2]["plan"], rows[2])
    assert q7["status"] == "active" and q7["remaining_days"] == 30
    assert cadence.view(tmp_path, rows[3]["planning_source_frame"])["status"] == "active"
