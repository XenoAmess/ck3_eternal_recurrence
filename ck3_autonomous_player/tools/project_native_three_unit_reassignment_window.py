"""Verify one three-unit owner-subset retreat and bounded AI rejoin window."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_SHA = "0E5AD3066B97689178797F1F9D3C35CA3700D513FAE6F6B032A3E8BF7BD1FB2A"
SWITCHED_SHA = "337B8818E819CA45A217F3751B1E0242045372084A265FEBF91C93D2BCB9F020"
AI_SEED_SHA = "B07F9A4A821C6C29242511047F068DA8889653AA7F9E19CA2007EC5C4E4615D7"
COMBAT_ID = 16777218
WITHDRAWN_ID = 16777221
DATE_RAW = 53146728


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def response(attempt: Path, stem: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / f"{stem}.json"
    raw = load(path)
    if raw.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native call failed: {stem}")
    return raw["body"], sha(path)


def checked_capture(attempt: Path, source_sha: str) -> str:
    path = attempt / "ck3-output/capture-report.json"
    data = load(path)
    launch = load(attempt / "launch-argv.json")
    argv = launch["argv"]
    bridge_path = Path(argv[argv.index("--bridge-dll") + 1])
    if not (
        data["checkpoint_source"]["save"]["sha256"].upper() == source_sha
        and data["checkpoint_source"]["source_lifecycle"]["source"]
            == "pure-vanilla-enabled-mods-empty"
        and data["worker"]["ok"] is True
        and data["environment_session_complete"] is True
        and not data["cleanup_process_inventory"]["processes"]
        and sha(bridge_path) == launch["bridge_sha256"]
    ):
        raise ValueError("isolated capture identity or cleanup differs")
    return sha(path)


def build(source: Path, structure: Path, withdrawal: Path, observation: Path,
          game_exe: Path) -> dict:
    if sha(game_exe) != EXE_SHA:
        raise ValueError("game executable changed")
    if sha(source / "d21-immutable.ck3") != SOURCE_SHA:
        raise ValueError("day-21 immutable source changed")
    if sha(structure / "d21-player-defender-immutable.ck3") != SWITCHED_SHA:
        raise ValueError("switched player seed changed")
    if sha(withdrawal / "d21-ai-withdrawn-immutable.ck3") != AI_SEED_SHA:
        raise ValueError("AI withdrawal seed changed")
    structure_capture_sha = checked_capture(structure, SOURCE_SHA)
    withdrawal_capture_sha = checked_capture(withdrawal, SWITCHED_SHA)
    observation_capture_sha = checked_capture(observation, AI_SEED_SHA)

    structure_summary_path = structure / "structure-readback.json"
    structure_summary = load(structure_summary_path)
    before, before_sha = response(structure, "001-before")
    switched, switch_sha = response(structure, "005-switch")
    after, after_sha = response(structure, "006-after")
    saved, save_sha = response(structure, "010-save")
    if not (
        before["date_raw"] == after["date_raw"] == DATE_RAW
        and before["played_character"]["character_id"] == 29829
        and after["played_character"]["character_id"] == 31549
        and switched["accepted"] is True
        and switched["postcondition_verified"] is True
        and structure_summary["before_snapshot_sha256"] == before_sha
        and structure_summary["switch_sha256"] == switch_sha
        and structure_summary["after_snapshot_sha256"] == after_sha
        and structure_summary["save_response_sha256"] == save_sha
        and saved["checkpoint"]["sha256"].upper() == SWITCHED_SHA
        and structure_summary["save_sha256"] == SWITCHED_SHA
    ):
        raise ValueError("three-unit seed switch differs")
    expected_before = [WITHDRAWN_ID, 27, 16777231]
    expected_after = [16777231, 27]
    for index, army_id in enumerate((WITHDRAWN_ID, 16777231, 27), start=2):
        body, body_sha = response(structure, f"{index:03d}-before-army-{army_id}")
        frame = body["battle_reinforcement_assignment"]
        if not (
            frame["status"] == "available"
            and frame["coordinator_id"] == 3
            and frame["assignment"]["active_combat_id"] == COMBAT_ID
            and frame["native_order"]["parent_subunits_in_stored_order"][0]
                ["public_cunit_ids_in_stored_order"] == expected_before
            and structure_summary["before"][str(army_id)]["response_sha256"] == body_sha
        ):
            raise ValueError(f"pre-switch parent differs for {army_id}")
    for index, army_id in enumerate((WITHDRAWN_ID, 16777231, 27), start=7):
        body, body_sha = response(structure, f"{index:03d}-after-army-{army_id}")
        frame = body["battle_reinforcement_assignment"]
        if structure_summary["after"][str(army_id)]["response_sha256"] != body_sha:
            raise ValueError("post-switch response SHA differs")
        if army_id == WITHDRAWN_ID:
            if frame["status"] != "unavailable" or frame["unavailable_reason"] != "subunit_backlink_mismatch":
                raise ValueError("player CUnit did not leave AI membership")
        elif not (
            frame["status"] == "available"
            and frame["coordinator_id"] == 3
            and frame["assignment"]["active_combat_id"] == COMBAT_ID
            and frame["native_order"]["parent_subunits_in_stored_order"][0]
                ["public_cunit_ids_in_stored_order"] == expected_after
        ):
            raise ValueError(f"two-anchor parent differs for {army_id}")

    withdrawal_summary_path = withdrawal / "withdrawal-summary.json"
    withdrawal_summary = load(withdrawal_summary_path)
    control, control_sha = response(withdrawal, "002-control")
    preview, preview_sha = response(withdrawal, "003-preview-2639")
    order, order_sha = response(withdrawal, "008-order")
    post, post_sha = response(withdrawal, "009-post-0")
    terminal, terminal_sha = response(withdrawal, "021-terminal")
    saved_withdrawn, saved_withdrawn_sha = response(withdrawal, "022-post-withdrawal-save")
    returned, returned_sha = response(withdrawal, "023-return-player")
    ai_snapshot, ai_snapshot_sha = response(withdrawal, "024-ai-snapshot")
    saved_ai, saved_ai_sha = response(withdrawal, "025-ai-save")
    battle = control["battle_control_snapshot"]
    frame = terminal["battle_terminal_transition"]
    player_army = next(a for a in post["player_armies"] if a["army_id"] == WITHDRAWN_ID)
    war = next(w for w in ai_snapshot["active_wars"] if w["war_id"] == 4)
    ai_army = next(a for a in war["enemy_armies"] if a["army_id"] == WITHDRAWN_ID)
    if not (
        battle["combat_id"] == COMBAT_ID
        and battle["side_scope"] == "owner_subset"
        and battle["legality"]["legal_now"] is True
        and battle["legality"]["elapsed_whole_days"] == 20
        and preview["status"] == "available"
        and preview["action_ready"] is True
        and preview["target_preview"]["candidate_token"]
        and order["accepted"] is True
        and order["status"] == "accepted_verification_pending"
        and player_army["retreating"] is True
        and player_army["in_combat"] is False
        and player_army["route_province_ids"] == [2639]
        and frame["prior"]["terminal_kind"] == "active_not_terminal"
        and frame["prior"]["attacker_public_cunit_ids_in_stored_order"]
            == [16777231, 27, 22]
        and frame["prior"]["defender_public_cunit_ids_in_stored_order"] == [18]
        and saved_withdrawn["checkpoint"]["sha256"].upper()
            == sha(withdrawal / "d21-player-withdrawn-immutable.ck3")
        and returned["postcondition_verified"] is True
        and ai_snapshot["played_character"]["character_id"] == 29829
        and ai_army["controllable"] is False
        and ai_army["retreating"] is True
        and saved_ai["checkpoint"]["sha256"].upper() == AI_SEED_SHA
        and withdrawal_summary["ai_seed_sha256"] == AI_SEED_SHA
    ):
        raise ValueError("native withdrawal or same-day return differs")
    for key, observed in (
        ("control", control_sha), ("selected_preview", preview_sha),
        ("order", order_sha), ("post", post_sha), ("terminal", terminal_sha),
        ("withdrawn_save", saved_withdrawn_sha), ("return_player", returned_sha),
        ("ai_snapshot", ai_snapshot_sha), ("ai_save", saved_ai_sha),
    ):
        if withdrawal_summary["response_sha256"][key] != observed:
            raise ValueError(f"withdrawal response SHA differs: {key}")

    daily_path = observation / "daily-observations.jsonl"
    rows = [json.loads(line) for line in daily_path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 12:
        raise ValueError("expected 11 one-day advances before terminal")
    for index, row in enumerate(rows):
        snapshot_name = "00-snapshot" if index == 0 else f"{index:02d}-snapshot"
        snapshot, snapshot_sha = response(observation, snapshot_name)
        if not (
            row["day_index"] == index
            and row["date_raw"] == snapshot["date_raw"] == DATE_RAW + index * 24
            and snapshot["paused"] is True
            and snapshot["played_character"]["character_id"] == 29829
            and row["response_sha256"]["snapshot"] == snapshot_sha
        ):
            raise ValueError(f"daily snapshot drift at {index}")
        if index:
            advance, advance_sha = response(observation, f"{index:02d}-advance")
            if not (
                advance["step"] == "life-advance"
                and advance["starting_date_raw"] == DATE_RAW + (index - 1) * 24
                and advance["ending_date_raw"] == DATE_RAW + index * 24
                and row["response_sha256"]["advance"] == advance_sha
            ):
                raise ValueError(f"daily advance drift at {index}")
        elif row["response_sha256"]["advance"] is not None:
            raise ValueError("initial row has an advance")
        for slot, army_id in enumerate((WITHDRAWN_ID, 16777231, 27), start=1):
            key = str(army_id)
            assignment, assignment_sha = response(
                observation, f"{index:02d}-assignment-{slot}-{army_id}"
            )
            if not (
                assignment["battle_reinforcement_assignment"] == row["assignments"][key]
                and row["response_sha256"]["assignments"][key] == assignment_sha
            ):
                raise ValueError(f"daily assignment drift at {index}/{army_id}")
        t, terminal_sha = response(observation, f"{index:02d}-terminal")
        tframe = t["battle_terminal_transition"]
        if not (
            row["response_sha256"]["terminal"] == terminal_sha
            and row["terminal_kind"] == tframe["prior"]["terminal_kind"]
            and row["terminal_journal"] == tframe["terminal_journal"]
            and row["side0_roster"]
                == tframe["prior"]["attacker_public_cunit_ids_in_stored_order"]
            and row["enemy21"]["controllable"] is False
            and WITHDRAWN_ID not in row["side0_roster"]
            and all(row["assignments"][str(a)]["status"] == "available"
                    for a in (16777231, 27))
            and all(row["assignments"][str(a)]["signal"]["asking_for_help"] is False
                    for a in (16777231, 27))
        ):
            raise ValueError(f"daily terminal/requester drift at {index}")
        withdrawn = row["assignments"][str(WITHDRAWN_ID)]
        if index == 0:
            if withdrawn["status"] != "unavailable" or withdrawn["unavailable_reason"] != "subunit_backlink_mismatch":
                raise ValueError("cold first-frame AI backlink differs")
        elif not (
            withdrawn["status"] == "available"
            and withdrawn["signal"]["assigned_to_help"] is False
            and withdrawn["assignment"]["assignment_target_province_id"] is None
        ):
            raise ValueError(f"AI assignment drift at {index}")
        if index < 11 and row["terminal_kind"] != "active_not_terminal":
            raise ValueError("battle ended before expected terminal day")
    first = rows[0]
    day1 = rows[1]
    day10 = rows[10]
    final = rows[11]
    if not (
        first["side0_roster"] == [16777231, 27, 22]
        and day1["side0_roster"] == [16777231, 27, 22, 28]
        and day1["assignments"][str(WITHDRAWN_ID)]["coordinator_id"] == 3
        and day1["assignments"][str(WITHDRAWN_ID)]["native_order"]
            ["parent_subunits_in_stored_order"][0]["public_cunit_ids_in_stored_order"]
            == [22, 28, WITHDRAWN_ID, 27, 16777231]
        and day10["enemy21"]["retreating"] is False
        and day10["enemy21"]["move_target_province_id"] == 2633
        and day10["assignments"][str(WITHDRAWN_ID)]["route"]
            ["arrival_date_raws"] == [53147304]
        and final["terminal_kind"] == "normal_result"
        and final["winner_raw"] == 0
        and final["date_raw"] == 53146992
        and 53147304 > final["date_raw"]
    ):
        raise ValueError("bounded AI return or terminal timing differs")
    return {
        "schema": "ck3.native_three_unit_reassignment_window.v1",
        "game_version": "1.19.0.6",
        "game_executable_sha256": EXE_SHA,
        "source_day21_save_sha256": SOURCE_SHA,
        "switched_player_seed_sha256": SWITCHED_SHA,
        "ai_withdrawn_seed_sha256": AI_SEED_SHA,
        "structure_readback_sha256": sha(structure_summary_path),
        "withdrawal_summary_sha256": sha(withdrawal_summary_path),
        "daily_observations_sha256": sha(daily_path),
        "capture_report_sha256": {
            "structure": structure_capture_sha,
            "withdrawal": withdrawal_capture_sha,
            "observation": observation_capture_sha,
        },
        "source_date_raw": DATE_RAW,
        "terminal_date_raw": final["date_raw"],
        "combat_id": COMBAT_ID,
        "withdrawn_public_cunit_id": WITHDRAWN_ID,
        "owner_subset_retreat_live_ready": True,
        "retained_multi_cunit_parent_live_ready": True,
        "ai_membership_reopened_day_index": 1,
        "requester_asking_observed": False,
        "assignment_target_or_eta_observed": False,
        "same_combat_rejoin_observed": False,
        "ordinary_ai_return_move_observed_day_index": 10,
        "ordinary_ai_return_arrival_date_raw": 53147304,
        "return_arrival_after_battle_terminal": True,
        "generic_ai_help_policy_absence_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-attempt", type=Path, required=True)
    parser.add_argument("--structure-attempt", type=Path, required=True)
    parser.add_argument("--withdrawal-attempt", type=Path, required=True)
    parser.add_argument("--observation-attempt", type=Path, required=True)
    parser.add_argument("--game-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.source_attempt, args.structure_attempt,
                   args.withdrawal_attempt, args.observation_attempt,
                   args.game_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output)}))


if __name__ == "__main__":
    main()
