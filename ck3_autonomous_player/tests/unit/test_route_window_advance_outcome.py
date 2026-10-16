"""Actual query/three-day result projection; mutants are synthetic contracts."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from xar_autoplayer.bridge.route_contact_window_contract import parse_advance_route_contact_window_step
from xar_autoplayer.bridge.native_driver import _validate_tactical_daily_sentinel_stop

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "route_window_advance_outcome", ROOT / "tools/g2_saved_campaign/route_window_advance_outcome.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FIXTURE = json.loads((Path(__file__).parent / "fixtures/route_window_actual_projection.json").read_text(encoding="utf-8"))


def bind(body, *, initial_frame=None, game_pid=None):
    frame = body["planning_source_frame"]
    assert frame == initial_frame and frame["bridge_pid"] == game_pid
    return deepcopy(frame)


def classify(body):
    frame = body["planning_source_frame"]
    return module.classify_route_contact_window_advance_v1(
        body, bind_gameplay_frame=bind, parse_advance_step=parse_advance_route_contact_window_step,
        validate_sentinel_stop=_validate_tactical_daily_sentinel_stop,
        initial_frame=frame, game_pid=frame["bridge_pid"])


def test_actual_query_and_three_day_result_grant_only_elapsed_dates():
    body, query = deepcopy(FIXTURE["body"]), FIXTURE["query"]
    assert query["planning_source_frame"] == body["planning_source_frame"]
    assert query["selected_step"].split("-h-", 1)[1] == body["selected_step"].split("-h-", 1)[1]
    credit = classify(body)
    assert credit["actual_elapsed_days"] == 3 and credit["actual_date_delta_raw"] == 72
    assert credit["business_success_inferred"] is False and credit["replay_allowed"] is False
    assert credit["primitive_accepted"] is False
    retreating = [a for a in body["result"]["war_progress_before"]["wars"][0]["enemy_armies"]
                  if a.get("retreating") is True]
    assert retreating and all(a["army_id"] not in body["result"]["watch_army_ids"] for a in retreating)


@pytest.mark.parametrize("mutation", ["unknown_retreat", "missing_retreat", "missing_hostile", "wrong_watch",
                                     "overshoot", "bad_after_row", "wrong_selected_war"])
def test_unproven_scope_or_clock_is_rejected(mutation):
    body = deepcopy(FIXTURE["body"])
    inner = body["result"]
    enemy = inner["war_progress_before"]["wars"][0]["enemy_armies"]
    if mutation in ("unknown_retreat", "missing_retreat"):
        row = next(a for a in enemy if a.get("retreating") is True)
        if mutation == "unknown_retreat": row["retreating"] = None
        else: del row["retreating"]
    elif mutation == "missing_hostile":
        enemy[:] = [a for a in enemy if a["army_id"] != 16777794]
    elif mutation == "wrong_watch": inner["watch_army_ids"].append(536871076)
    elif mutation == "overshoot": inner["overshoot_days"] = 1
    elif mutation == "bad_after_row": inner["war_progress_after"]["wars"][0]["enemy_armies"] = None
    else: body["plan"]["active_wars"] = [{"war_id": 999999}]
    with pytest.raises(ValueError): classify(body)


@pytest.mark.parametrize("wars", [[], [{"war_id": 999999, "player_armies": [], "enemy_armies": []}]])
def test_natural_war_change_does_not_infer_victory(wars):
    body = deepcopy(FIXTURE["body"])
    body["result"]["war_progress_after"]["wars"] = wars
    credit = classify(body)
    assert credit["actual_date_delta_raw"] == 72
    assert credit["business_success_inferred"] is False


def test_already_observed_speed_must_bind_exact_native_source():
    body = deepcopy(FIXTURE["body"])
    frame = body["planning_source_frame"]
    first = body["result"]["actions"][0]["result"]
    first.clear()
    first.update(status="already_observed", submitted=False, accepted=None, observed_speed=3,
                 source_snapshot_id=frame["snapshot_id"], source_native_revision=frame["native_revision"],
                 source_date_raw=frame["date_raw"])
    assert classify(body)["actual_elapsed_days"] == 3
    first["source_native_revision"] -= 1
    with pytest.raises(ValueError): classify(body)


def test_public_army_zero_remains_a_valid_watched_subject():
    body = deepcopy(FIXTURE["body"])
    subject, _, _, _ = parse_advance_route_contact_window_step(body["selected_step"])
    body["selected_step"] = body["selected_step"].replace(f"-v1-{subject}-to-", "-v1-0-to-", 1)
    body["plan"]["selected_step"] = body["selected_step"]
    inner = body["result"]
    inner["step"] = body["selected_step"]
    for key in ("war_progress_before", "war_progress_after"):
        for war in inner[key]["wars"]:
            for army in war["player_armies"]:
                if army["army_id"] == subject: army["army_id"] = 0
    watches = sorted(0 if army == subject else army for army in inner["watch_army_ids"])
    inner["watch_army_ids"] = watches
    arm_step = (f"research-arm-tactical-daily-sentinel-v1-{inner['starting_date_raw']}-to-"
                f"{inner['target_date_raw']}-speed-{inner['timeline_speed']}-mode-terminal-a-{len(watches)}-"
                + "-".join(map(str, watches)))
    inner["actions"][1]["step"] = arm_step
    inner["actions"][1]["result"]["step"] = arm_step
    assert classify(body)["actual_elapsed_days"] == 3
