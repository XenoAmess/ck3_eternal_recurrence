"""Bind a native day-05 maim writeback to the agent's reloaded day-06 v3 input."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    row = json.loads(path.read_text(encoding="utf-8"))
    if row["result"] != "CALL_COMPLETED":
        raise ValueError(f"incomplete native response: {name}")
    return row["body"], digest(path)


def index(base: dict) -> tuple[dict[int, tuple[int, dict]], dict[int, tuple[int, dict]]]:
    regiments = {r["regiment_id"]: (a["army_id"], r)
                 for a in base["armies"] for r in a["regiments"]}
    knights = {r["character_id"]: (a["army_id"], r)
               for a in base["armies"] for r in a["knights"]["members"]}
    return regiments, knights


def build(before: Path, after: Path, maim_report: Path) -> dict:
    prior = json.loads(maim_report.read_text(encoding="utf-8"))
    summary = json.loads((before / "one-day-summary.json").read_text(encoding="utf-8"))
    first_body, first_sha = response(before, "004-v3.json")
    finish, finish_sha = response(before, "007-finish.json")
    saved, save_response_sha = response(before, "008-after-save.json")
    source_save = before / "ck3-state/profile/save games/xar_episode_seed.ck3"
    post_save = before / "d06-postevent-immutable.ck3"
    if (digest(source_save) != prior["source_save_sha256"]
            or digest(post_save) != prior["post_save_sha256"]
            or finish_sha != prior["trace_response_sha256"]
            or summary["trace_response_sha256"] != finish_sha
            or save_response_sha != summary["post_event_save_response_sha256"]
            or saved["checkpoint"]["sha256"].upper() != digest(post_save)
            or finish["status"] != "bounded_trace_available"
            or finish["managed_trace"]["trace"]["failure_flags"] != 0
            or prior["newly_appended_events"] != [{
                "left_character_id": 34333,
                "right_character_id": 47032,
                "stable_key": "knight_maimed_by_enemy",
                "type_raw": 2,
                "side_index": 1,
                "target_right": False,
            }]):
        raise ValueError("day-05 maim source identity or event evidence changed")
    snapshot, snapshot_sha = response(after, "001-initial-snapshot.json")
    control, control_sha = response(after, "002-control.json")
    second_body, second_sha = response(after, "003-v3.json")
    after_summary = json.loads((after / "next-input-summary.json").read_text(encoding="utf-8"))
    capture_path = after / "ck3-output/capture-report.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (after_summary["source_save_sha256"] != digest(post_save)
            or after_summary["snapshot_response_sha256"] != snapshot_sha
            or after_summary["control_response_sha256"] != control_sha
            or after_summary["v3_response_sha256"] != second_sha
            or capture["checkpoint_source"]["save"]["sha256"].upper() != digest(post_save)
            or snapshot["paused"] is not True or snapshot["date_raw"] != 53146368
            or first_body["combat_simulation_inputs"]["completeness"]["base_input_observation_ready"] is not True
            or second_body["combat_simulation_inputs"]["completeness"]["base_input_observation_ready"] is not True
            or second_body["queried_revision"] != snapshot["revision"]
            or control["queried_revision"] != snapshot["revision"]
            or control["battle_control_snapshot"]["combat_id"] != 16777218
            or capture["worker"]["ok"] is not True
            or capture["environment_session_complete"] is not True
            or capture["cleanup_process_inventory"]["processes"]):
        raise ValueError("day-06 isolated paused native query or cleanup failed")
    first = first_body["combat_simulation_inputs"]["base_inputs"]
    second = second_body["combat_simulation_inputs"]["base_inputs"]
    fr, fk = index(first)
    sr, sk = index(second)
    if (len(fr) != 51 or len(sr) != 51 or fr.keys() != sr.keys()
            or len(fk) != 24 or len(sk) != 24 or fk.keys() != sk.keys()
            or any(fk[key] != sk[key] for key in fk if key != 34333)
            or any(fr[key][1]["effective_stats"] != sr[key][1]["effective_stats"]
                   for key in fr if key != 61)
            or any(fr[key][0] != sr[key][0] for key in fr)
            or any(fk[key][0] != sk[key][0] for key in fk)):
        raise ValueError("unexpected participant or effective-stat transition")
    before_knight = fk[34333][1]
    after_knight = sk[34333][1]
    before_regiment = fr[61][1]
    after_regiment = sr[61][1]
    if (before_knight["source_regiment_id"] != 61
            or after_knight["source_regiment_id"] != 61
            or before_knight["prowess"] != 11 or after_knight["prowess"] != 7
            or before_knight["knight_effectiveness_raw"] != 175000
            or after_knight["knight_effectiveness_raw"] != 175000
            or before_knight["effective_damage_raw"] != 96250000
            or after_knight["effective_damage_raw"] != 61250000
            or before_knight["effective_toughness_raw"] != 19250000
            or after_knight["effective_toughness_raw"] != 12250000
            or before_regiment["current_soldiers"] != 1
            or after_regiment["current_soldiers"] != 1
            or before_regiment["effective_stats"]["damage_raw"] != 96250000
            or after_regiment["effective_stats"]["damage_raw"] != 61250000
            or before_regiment["effective_stats"]["toughness_raw"] != 19250000
            or after_regiment["effective_stats"]["toughness_raw"] != 12250000):
        raise ValueError("maimed knight's next input differs from the native vector")
    soldier_deltas = [{"regiment_id": key,
                       "before": fr[key][1]["current_soldiers"],
                       "after": sr[key][1]["current_soldiers"]}
                      for key in sorted(fr)
                      if fr[key][1]["current_soldiers"] != sr[key][1]["current_soldiers"]]
    return {
        "schema": "ck3.native_knight_maim_next_input.v1",
        "game_version": "1.19.0.6",
        "combat_id": 16777218,
        "source_day": 5,
        "next_day": 6,
        "source_save_sha256": digest(source_save),
        "post_event_save_sha256": digest(post_save),
        "maim_report_sha256": digest(maim_report),
        "source_v3_response_sha256": first_sha,
        "source_trace_response_sha256": finish_sha,
        "next_snapshot_response_sha256": snapshot_sha,
        "next_control_response_sha256": control_sha,
        "next_v3_response_sha256": second_sha,
        "next_capture_report_sha256": digest(capture_path),
        "next_capture_cleanup_processes": 0,
        "regiments_before_after": [len(fr), len(sr)],
        "knights_before_after": [len(fk), len(sk)],
        "unchanged_other_knight_rows": 23,
        "unchanged_other_regiment_effective_stat_rows": 50,
        "maimed_character_id": 34333,
        "maimed_regiment_id": 61,
        "maimed_next_input_before": before_knight,
        "maimed_next_input_after": after_knight,
        "maimed_regiment_current_soldiers_before_after": [1, 1],
        "other_regiment_soldier_changes": soldier_deltas,
        "full_mutable_write_set_proven": False,
        "all_future_day_transitions_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-attempt", required=True, type=Path)
    parser.add_argument("--after-attempt", required=True, type=Path)
    parser.add_argument("--maim-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.before_attempt, args.after_attempt, args.maim_report)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
