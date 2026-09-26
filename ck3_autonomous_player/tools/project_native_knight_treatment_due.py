"""Project one native queued wound-treatment event across its two-day due boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TARGET = 34333
EVENT = 'event="health.0101"'
FAILURE = 'modifier="safe_wound_treatment_failure_modifier"'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    row = json.loads(path.read_text(encoding="utf-8"))
    if row["result"] != "CALL_COMPLETED":
        raise ValueError(f"incomplete native response: {name}")
    return row["body"], digest(path)


def save_projection(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    start = text.index(f"\n\t{TARGET}={{")
    end = text.index("\n\t}", start)
    block = text[start:end]
    date = re.search(r"\n\s*meta_date=([^\n]+)", text)
    health = re.search(r"\n\t\t\thealth=([^\n]+)", block)
    traits = re.search(r"traits=\{([^}]+)\}", block)
    if date is None or health is None or traits is None:
        raise ValueError("target character or save date unavailable")
    expirations = re.findall(r"expiration_date=([^\n]+)", block)
    return {
        "meta_date": date.group(1),
        "target_character_id": TARGET,
        "base_health_stored": health.group(1),
        "trait_indices": [int(value) for value in traits.group(1).split()],
        "safe_failure_modifier_present": FAILURE in block,
        "modifier_expiration_dates": expirations,
        "health_0101_queued_count": text.count(EVENT),
    }


def knight(base: dict, character_id: int) -> dict:
    found = [r for army in base["armies"]
             for r in army["knights"]["members"] if r["character_id"] == character_id]
    if len(found) != 1:
        raise ValueError("target knight not unique in v3")
    return found[0]


def regiment(base: dict, regiment_id: int) -> dict:
    found = [r for army in base["armies"]
             for r in army["regiments"] if r["regiment_id"] == regiment_id]
    if len(found) != 1:
        raise ValueError("target regiment not unique in v3")
    return found[0]


def build(source: Path, attempt: Path, maim_report: Path,
          next_input_report: Path, rakaly: Path, game_root: Path) -> dict:
    prior = json.loads(maim_report.read_text(encoding="utf-8"))
    next_input = json.loads(next_input_report.read_text(encoding="utf-8"))
    summary = json.loads((attempt / "treatment-due-summary.json").read_text(encoding="utf-8"))
    day8_summary = json.loads((attempt / "day8-v3-summary.json").read_text(encoding="utf-8"))
    captures = attempt / "ck3-output/capture-report.json"
    capture = json.loads(captures.read_text(encoding="utf-8"))
    source_save = source / "d06-postevent-immutable.ck3"
    if (digest(source_save) != prior["post_save_sha256"]
            or digest(source_save) != summary["source_save_sha256"]
            or next_input["post_event_save_sha256"] != digest(source_save)
            or digest(rakaly) != prior["rakaly_exe_sha256"]
            or digest(game_root / "binaries/ck3.exe") != prior["game_executable_sha256"]
            or capture["checkpoint_source"]["save"]["sha256"].upper() != digest(source_save)
            or capture["worker"]["ok"] is not True
            or capture["environment_session_complete"] is not True
            or capture["cleanup_process_inventory"]["processes"]):
        raise ValueError("native source/build/cleanup identity changed")
    daily = {row["day"]: row for row in summary["daily"]}
    if daily.keys() != {7, 8} or summary["initial_revision"] != 4:
        raise ValueError("two-day source trajectory changed")
    response_names = {7: ("002-advance.json", "003-snapshot.json", "004-save.json"),
                      8: ("005-advance.json", "006-snapshot.json", "007-save.json")}
    projections = {6: save_projection(source / "d06-melted.ck3")}
    for day in (7, 8):
        row = daily[day]
        advance, advance_sha = response(attempt, response_names[day][0])
        snapshot, snapshot_sha = response(attempt, response_names[day][1])
        saved, saved_sha = response(attempt, response_names[day][2])
        save = attempt / f"d0{day}-treatment-immutable.ck3"
        if (advance_sha != row["advance_response_sha256"]
                or snapshot_sha != row["snapshot_response_sha256"]
                or saved_sha != row["save_response_sha256"]
                or digest(save) != row["save_sha256"]
                or saved["checkpoint"]["sha256"].upper() != digest(save)
                or advance["starting_date_raw"] != row["date_raw"] - 24
                or advance["ending_date_raw"] != row["date_raw"]
                or snapshot["date_raw"] != row["date_raw"]
                or snapshot["paused"] is not True):
            raise ValueError(f"day {day} save/receipt or paused boundary changed")
        projections[day] = save_projection(attempt / f"d0{day}-melted.ck3")
    if (projections[6]["meta_date"] != "1066.12.9"
            or projections[7]["meta_date"] != "1066.12.10"
            or projections[8]["meta_date"] != "1066.12.11"
            or [projections[d]["health_0101_queued_count"] for d in (6, 7, 8)] != [1, 1, 0]
            or [projections[d]["safe_failure_modifier_present"] for d in (6, 7, 8)] != [False, False, True]
            or projections[8]["modifier_expiration_dates"] != ["1067.12.11"]
            or len({projections[d]["base_health_stored"] for d in (6, 7, 8)}) != 1
            or len({tuple(projections[d]["trait_indices"]) for d in (6, 7, 8)}) != 1):
        raise ValueError("health.0101 due-date writeback differs from observed source")
    snap8, snap8_sha = response(attempt, "009-final-snapshot.json")
    control, control_sha = response(attempt, "010-control.json")
    v3_day8, v3_sha = response(attempt, "011-v3.json")
    v3_day6, day6_sha = response(source.parent / "episode01-day06-maim-next-input-attempt-040", "003-v3.json")
    if (snap8_sha != day8_summary["snapshot_response_sha256"]
            or control_sha != day8_summary["control_response_sha256"]
            or v3_sha != day8_summary["v3_response_sha256"]
            or day6_sha != next_input["next_v3_response_sha256"]
            or snap8["paused"] is not True or snap8["date_raw"] != 53146416
            or control["battle_control_snapshot"]["combat_id"] != 16777218):
        raise ValueError("day-08 v3 identity changed")
    base6 = v3_day6["combat_simulation_inputs"]["base_inputs"]
    base8 = v3_day8["combat_simulation_inputs"]["base_inputs"]
    victim6, victim8 = knight(base6, TARGET), knight(base8, TARGET)
    regiment6, regiment8 = regiment(base6, 61), regiment(base8, 61)
    if (victim6 != victim8 or regiment6 != regiment8
            or victim8["prowess"] != 7
            or regiment8["effective_stats"]["damage_raw"] != 61250000
            or regiment8["effective_stats"]["toughness_raw"] != 12250000):
        raise ValueError("target battle inputs changed across treatment event")
    health_events = (game_root / "game/events/health_events.txt").read_text(encoding="utf-8-sig")
    health_effects = (game_root / "game/common/scripted_effects/20_health_effects.txt").read_text(encoding="utf-8-sig")
    health_modifiers = (game_root / "game/common/modifiers/00_health_modifiers.txt").read_text(encoding="utf-8-sig")
    basic_values = (game_root / "game/common/script_values/00_basic_values.txt").read_text(encoding="utf-8-sig")
    if (not re.search(r"health\.0101\s*=\s*\{.*?wound_treatment_results_effect\s*=\s*"
                      r"\{\s*TREATMENT\s*=\s*safe\s+OUTCOME\s*=\s*failure\s*\}",
                      health_events, re.DOTALL)
            or not re.search(r"add_character_modifier\s*=\s*\{\s*modifier\s*=\s*"
                             r"safe_wound_treatment_failure_modifier\s+days\s*=\s*"
                             r"wound_treatment_failure_duration\s*\}", health_effects)
            or not re.search(r"safe_wound_treatment_failure_modifier\s*=\s*\{"
                             r"[^}]*\bhealth\s*=\s*-0\.5\b", health_modifiers)
            or not re.search(r"\bwound_treatment_failure_duration\s*=\s*365\b", basic_values)):
        raise ValueError("stock treatment event, modifier or duration source drifted")
    return {
        "schema": "ck3.native_knight_treatment_due.v1",
        "game_version": "1.19.0.6",
        "combat_id": 16777218,
        "target_character_id": TARGET,
        "source_save_sha256": digest(source_save),
        "maim_report_sha256": digest(maim_report),
        "next_input_report_sha256": digest(next_input_report),
        "rakaly_exe_sha256": digest(rakaly),
        "script_sha256": {
            "health_events": digest(game_root / "game/events/health_events.txt"),
            "health_effects": digest(game_root / "game/common/scripted_effects/20_health_effects.txt"),
            "health_modifiers": digest(game_root / "game/common/modifiers/00_health_modifiers.txt"),
            "basic_values": digest(game_root / "game/common/script_values/00_basic_values.txt"),
        },
        "initial_snapshot_response_sha256": summary["initial_snapshot_response_sha256"],
        "daily_receipts": daily,
        "melted_save_sha256_by_day": {
            str(d): digest(source / "d06-melted.ck3") if d == 6
            else digest(attempt / f"d0{d}-melted.ck3") for d in (6, 7, 8)},
        "character_save_projection_by_day": {str(d): projections[d] for d in (6, 7, 8)},
        "day6_v3_response_sha256": day6_sha,
        "day8_v3_response_sha256": v3_sha,
        "day8_capture_report_sha256": digest(captures),
        "day8_capture_cleanup_processes": 0,
        "target_knight_v3_row_unchanged_day6_to_day8": True,
        "target_regiment_v3_row_unchanged_day6_to_day8": True,
        "safe_failure_modifier_script_health_delta": "-0.5",
        "safe_failure_modifier_script_duration_days": 365,
        "effective_health_numeric_directly_queried": False,
        "other_phase_effects_excluded": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-attempt", required=True, type=Path)
    parser.add_argument("--due-attempt", required=True, type=Path)
    parser.add_argument("--maim-report", required=True, type=Path)
    parser.add_argument("--next-input-report", required=True, type=Path)
    parser.add_argument("--rakaly-exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.source_attempt, args.due_attempt, args.maim_report,
                   args.next_input_report, args.rakaly_exe, args.game_root)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
