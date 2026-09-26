"""Verify a cold-reloaded AI-controlled battle from day six to native defeat."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_SHA = "9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A"
SEED_SHA = "9B51A2FB20C7F931CF4E9F2A33F1E7598F517C4E793CE0CEFCFEF48C0D65BD2F"
START_DATE = 53146368
COMBAT_ID = 16777218
WAR_ID = 4
AI_ARMY_ID = 18
AI_OWNER_ID = 29829
PLAYER_ID = 31549


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def response(attempt: Path, stem: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / f"{stem}.json"
    data = read(path)
    if data.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native request failed: {stem}")
    return data["body"], sha(path)


def build(seed: Path, observation: Path, game_exe: Path) -> dict:
    seed_save = seed / "ai-defender-day06-seed-immutable.ck3"
    seed_summary = read(seed / "seed-summary.json")
    seed_capture = read(seed / "ck3-output/capture-report.json")
    seed_action, seed_action_sha = response(seed, "003-switch-character")
    seed_snapshot, seed_snapshot_sha = response(seed, "004-after-snapshot")
    seed_war = next(w for w in seed_snapshot["active_wars"] if w["war_id"] == WAR_ID)
    seed_checkpoint, seed_checkpoint_sha = response(seed, "006-seed-save")
    seed_request = read(seed / "ck3-output/interactive-requests/003-switch-character.json")
    if not (
        sha(game_exe) == EXE_SHA
        and seed_summary["source_save_sha256"] == SOURCE_SHA
        and sha(seed_save) == SEED_SHA
        and seed_summary["seed_save_sha256"] == SEED_SHA
        and seed_checkpoint["checkpoint"]["sha256"].upper() == SEED_SHA
        and seed_summary["response_sha256"]["switch"] == seed_action_sha
        and seed_summary["response_sha256"]["after_snapshot"] == seed_snapshot_sha
        and seed_summary["response_sha256"]["seed_save"] == seed_checkpoint_sha
        and seed_request["tool"] == "ck3_set_played_character_v1"
        and seed_request["arguments"]["character_id"] == PLAYER_ID
        and seed_action["accepted"] is True
        and seed_action["postcondition_verified"] is True
        and seed_snapshot["played_character"]["character_id"] == PLAYER_ID
        and seed_snapshot["date_raw"] == START_DATE
        and seed_war["player_side"] == "defender"
        and seed_war["player_is_primary_war_leader"] is True
        and seed_capture["worker"]["ok"] is True
        and seed_capture["environment_session_complete"] is True
        and not seed_capture["cleanup_process_inventory"]["processes"]
    ):
        raise ValueError("seed switch, exact build, checkpoint, or cleanup differs")

    capture_path = observation / "ck3-output/capture-report.json"
    capture = read(capture_path)
    launch = read(observation / "launch-argv.json")
    argv = launch["argv"]
    bridge = Path(argv[argv.index("--bridge-dll") + 1])
    if not (
        capture["checkpoint_source"]["save"]["sha256"].upper() == SEED_SHA
        and capture["checkpoint_source"]["source_lifecycle"]["source"]
            == "pure-vanilla-enabled-mods-empty"
        and sha(bridge) == launch["bridge_sha256"]
        and capture["worker"]["ok"] is True
        and capture["environment_session_complete"] is True
        and not capture["cleanup_process_inventory"]["processes"]
    ):
        raise ValueError("observer was not an exact isolated clean capture")

    observations_path = observation / "daily-observations.jsonl"
    rows = [json.loads(line) for line in observations_path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 27:
        raise ValueError("expected 26 one-day advances and terminal observation")
    request_names = set()
    for index, row in enumerate(rows):
        snapshot_name = "001-snapshot" if index == 0 else f"{index:02d}-snapshot"
        terminal_name = "002-terminal" if index == 0 else f"{index:02d}-terminal"
        snapshot, snapshot_sha = response(observation, snapshot_name)
        terminal, terminal_sha = response(observation, terminal_name)
        request_names.update((snapshot_name, terminal_name))
        frame = terminal["battle_terminal_transition"]
        prior = frame["prior"]
        expected_side0 = [16777221, 16777231, 27]
        if index >= 6:
            expected_side0.append(22)
        if index >= 16:
            expected_side0.append(28)
        war = next((w for w in snapshot["active_wars"] if w["war_id"] == WAR_ID), None)
        enemy = next((a for a in war["enemy_armies"] if a["army_id"] == AI_ARMY_ID), None) if war else None
        if not (
            row["index"] == index
            and row["date_raw"] == snapshot["date_raw"] == START_DATE + index * 24
            and snapshot["paused"] is True
            and snapshot["played_character"]["character_id"] == PLAYER_ID
            and enemy is not None
            and enemy["owner_character_id"] == AI_OWNER_ID
            and enemy["controllable"] is False
            and row["enemy_army18"] == enemy
            and row["terminal_kind"] == frame["prior"]["terminal_kind"]
            and row["terminal_journal"] == frame["terminal_journal"]
            and prior["attacker_public_cunit_ids_in_stored_order"] == expected_side0
            and prior["defender_public_cunit_ids_in_stored_order"] == [AI_ARMY_ID]
            and row["response_sha256"]["snapshot"] == snapshot_sha
            and row["response_sha256"]["terminal"] == terminal_sha
        ):
            raise ValueError(f"observation drift at day {index}")
        if index:
            advance_name = f"{index:02d}-advance"
            advance, advance_sha = response(observation, advance_name)
            request_names.add(advance_name)
            if not (
                advance["step"] == "life-advance"
                and advance["starting_date_raw"] == START_DATE + (index - 1) * 24
                and advance["ending_date_raw"] == START_DATE + index * 24
                and row["response_sha256"]["advance"] == advance_sha
            ):
                raise ValueError(f"daily advance drift at day {index}")
        elif row["response_sha256"]["advance"] is not None:
            raise ValueError("initial frame has an advance response")
        if index < 26:
            if not (
                enemy["in_combat"] is True
                and enemy["retreating"] is False
                and frame["prior"]["combat_id"] == COMBAT_ID
                and frame["prior"]["terminal_kind"] == "active_not_terminal"
                and frame["removal"]["prior_combat_strictly_resolves"] is True
                and frame["terminal_journal"]["event_status"] == "not_observed"
            ):
                raise ValueError(f"premature retreat or unexpected terminal at day {index}")
        else:
            if not (
                enemy["in_combat"] is False
                and enemy["retreating"] is True
                and frame["prior"]["terminal_kind"] == "normal_result"
                and frame["prior"]["terminal_date_raw"] == snapshot["date_raw"]
                and frame["prior"]["winner_raw"] == 0
                and frame["prior"]["suppress_normal_result_envelopes"] is False
                and frame["prior"]["battle_warscore"]["status"] == "recorded"
                and frame["prior"]["defender_public_cunit_ids_in_stored_order"] == [AI_ARMY_ID]
                and frame["prior"]["battle_warscore"]["winner_is_war_attacker"] is False
                and frame["terminal_journal"]["event_status"] == "observed"
                and frame["removal"]["prior_combat_strictly_resolves"] is False
                and frame["subject"]["combat_backlink_id"] is None
                and frame["successor"]["state"] == "subject_retreating"
            ):
                raise ValueError("normal defeat to retreat transition differs")
            terminal_frame = frame
    actual_names = {
        path.stem for path in (observation / "ck3-output/interactive-requests").glob("*.json")
    }
    if actual_names != request_names | {"999-finish"}:
        raise ValueError("observer performed an unexpected interaction")
    return {
        "schema": "ck3.native_ai_battle_retreat_observation.v1",
        "game_version": "1.19.0.6",
        "game_executable_sha256": EXE_SHA,
        "bridge_dll_sha256": launch["bridge_sha256"],
        "source_save_sha256": SOURCE_SHA,
        "seed_save_sha256": SEED_SHA,
        "seed_summary_sha256": sha(seed / "seed-summary.json"),
        "seed_capture_report_sha256": sha(seed / "ck3-output/capture-report.json"),
        "observation_capture_report_sha256": sha(capture_path),
        "daily_observations_sha256": sha(observations_path),
        "observation_frames": len(rows),
        "one_day_advances": len(rows) - 1,
        "first_date_raw": START_DATE,
        "terminal_date_raw": rows[-1]["date_raw"],
        "combat_id": COMBAT_ID,
        "war_id": WAR_ID,
        "ai_subject_public_cunit_id": AI_ARMY_ID,
        "ai_subject_owner_character_id": AI_OWNER_ID,
        "played_character_id": PLAYER_ID,
        "voluntary_retreat_observed_before_terminal": False,
        "general_ai_voluntary_retreat_absence_proven": False,
        "native_terminal": terminal_frame,
        "source_process_cleanup_green": True,
        "observation_process_cleanup_green": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-attempt", type=Path, required=True)
    parser.add_argument("--observation-attempt", type=Path, required=True)
    parser.add_argument("--game-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.seed_attempt, args.observation_attempt, args.game_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output)}))


if __name__ == "__main__":
    main()
