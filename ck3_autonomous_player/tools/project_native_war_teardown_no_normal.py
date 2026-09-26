"""Bind an isolated war surrender to the exact native no-normal battle terminal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


COMBAT_ID = 16777218
WAR_ID = 4
PLAYER_ARMY_ID = 18
DATE_RAW = 53146368
SOURCE_SAVE_SHA = "9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    row = json.loads(path.read_text(encoding="utf-8"))
    if row["result"] != "CALL_COMPLETED":
        raise ValueError(f"native request failed: {name}")
    return row["body"], digest(path)


def build(source: Path, attempt: Path, game_exe: Path) -> dict:
    preflight_path = attempt / "preflight-summary.json"
    surrender_path = attempt / "surrender-summary.json"
    verification_path = attempt / "verification-summary.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    surrender = json.loads(surrender_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    capture_path = attempt / "ck3-output/capture-report.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    launch = json.loads((attempt / "launch-argv.json").read_text(encoding="utf-8"))
    argv = launch["argv"]
    bridge_path = Path(argv[argv.index("--bridge-dll") + 1])
    source_save = source / "d06-postevent-immutable.ck3"
    post_save = attempt / "post-surrender-immutable.ck3"
    source_sha = digest(source_save)
    if (source_sha != SOURCE_SAVE_SHA
            or preflight["source_save_sha256"] != source_sha
            or capture["checkpoint_source"]["save"]["sha256"].upper() != source_sha
            or capture["worker"]["ok"] is not True
            or capture["environment_session_complete"] is not True
            or capture["cleanup_process_inventory"]["processes"]
            or capture["checkpoint_source"]["source_lifecycle"]["source"]
               != "pure-vanilla-enabled-mods-empty"
            or digest(game_exe) != "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            or digest(bridge_path) != launch["bridge_sha256"]):
        raise ValueError("source exact-build or isolated capture identity differs")
    snapshot0, snapshot0_sha = response(attempt, "001-snapshot.json")
    control, control_sha = response(attempt, "002-control.json")
    terminal0, terminal0_sha = response(attempt, "003-terminal-before.json")
    options, options_sha = response(attempt, "004-war-options.json")
    action, action_sha = response(attempt, "005-surrender.json")
    snapshot1, snapshot1_sha = response(attempt, "006-after-snapshot.json")
    terminal1, terminal1_sha = response(attempt, "007-terminal-after.json")
    saved, saved_sha = response(attempt, "008-after-save.json")
    snapshot2, snapshot2_sha = response(attempt, "009-verification-snapshot.json")
    terminal2, terminal2_sha = response(attempt, "010-terminal-second.json")
    transition, transition_sha = response(attempt, "011-old-transition.json")
    expected_preflight = (snapshot0_sha, control_sha, terminal0_sha, options_sha)
    observed_preflight = tuple(preflight[key] for key in (
        "snapshot_response_sha256", "control_response_sha256",
        "terminal_before_response_sha256", "war_options_response_sha256"))
    expected_surrender = (action_sha, snapshot1_sha, terminal1_sha, saved_sha, digest(post_save))
    observed_surrender = tuple(surrender[key] for key in (
        "action_response_sha256", "snapshot_response_sha256",
        "terminal_response_sha256", "save_response_sha256", "post_save_sha256"))
    expected_verification = (snapshot2_sha, terminal2_sha, transition_sha)
    observed_verification = tuple(verification[key] for key in (
        "snapshot_response_sha256", "terminal_second_response_sha256",
        "old_transition_response_sha256"))
    if (expected_preflight != observed_preflight
            or expected_surrender != observed_surrender
            or expected_verification != observed_verification
            or saved["checkpoint"]["sha256"].upper() != digest(post_save)):
        raise ValueError("source response or post-save SHA binding changed")
    war = [row for row in snapshot0["active_wars"] if row["war_id"] == WAR_ID]
    native_options = options["war_termination_options"]
    option = native_options["options"]["surrender"]
    before = terminal0["battle_terminal_transition"]
    after = terminal1["battle_terminal_transition"]
    second = terminal2["battle_terminal_transition"]
    if (snapshot0["paused"] is not True or snapshot0["date_raw"] != DATE_RAW
            or snapshot1["paused"] is not True or snapshot1["date_raw"] != DATE_RAW
            or snapshot2["paused"] is not True or snapshot2["date_raw"] != DATE_RAW
            or len(war) != 1 or war[0]["player_is_primary_war_leader"] is not True
            or native_options["war_id"] != WAR_ID
            or option["available"] is not True
            or option["native_validator_passed"] is not True
            or option["auto_accept"] is not True
            or control["battle_control_snapshot"]["combat_id"] != COMBAT_ID
            or before["prior"]["terminal_kind"] != "active_not_terminal"
            or before["terminal_journal"]["latest_sequence"] != 0
            or before["subject"]["combat_backlink_id"] != COMBAT_ID
            or before["removal"]["prior_combat_strictly_resolves"] is not True
            or action["step"] != "surrender-war-4"
            or action["accepted"] is not True or action["status"] != "submitted"
            or any(row["war_id"] == WAR_ID for row in snapshot1["active_wars"])
            or any(row["war_id"] == WAR_ID for row in snapshot2["active_wars"])):
        raise ValueError("native surrender precondition or war postcondition differs")
    journal = after["terminal_journal"]
    prior = after["prior"]
    removal = after["removal"]
    subject = after["subject"]
    if (after["status"] != "available"
            or prior["combat_id"] != COMBAT_ID
            or prior["terminal_kind"] != "no_normal_result"
            or prior["terminal_date_raw"] != DATE_RAW
            or prior["suppress_normal_result_envelopes"] is not True
            or prior["phase_raw"] != 1 or prior["phase_day"] != 2
            or prior["winner_raw"] != -1
            or prior["battle_warscore"]["status"] != "not_recorded_by_native"
            or journal["event_status"] != "observed"
            or journal["event_sequence"] != 1
            or removal["prior_combat_strictly_resolves"] is not False
            or removal["prior_province_contains_prior_combat_id"] is not False
            or removal["result_strictly_resolves"] is not False
            or subject["combat_backlink_id"] is not None
            or subject["active_combat_id"] is not None
            or subject["blocked_by_active_combat"] is not False
            or transition["battle_transition_snapshot"]["status"] != "combat_not_found"
            or any(after[key] != second[key] for key in
                   ("prior", "removal", "subject", "successor"))):
        raise ValueError("native no-normal terminal or second readback differs")
    request_path = attempt / "ck3-output/interactive-requests/005-surrender.json"
    private_request = json.loads(request_path.read_text(encoding="utf-8"))
    if (private_request != {
            "action": "private_phase_trace",
            "step": "research-surrender-war-4",
            "expected_revision": preflight["revision"],
            "war_id": WAR_ID,
            "preflight_sha256": digest(preflight_path),
    }):
        raise ValueError("bounded private research request differs")
    return {
        "schema": "ck3.native_war_teardown_no_normal.v1",
        "game_version": "1.19.0.6",
        "game_executable_sha256": digest(game_exe),
        "private_bridge_dll_sha256": launch["bridge_sha256"],
        "source_save_sha256": source_sha,
        "source_date_raw": DATE_RAW,
        "combat_id": COMBAT_ID,
        "war_id": WAR_ID,
        "player_subject_public_cunit_id": PLAYER_ARMY_ID,
        "research_capture_script_sha256": digest(attempt / "capture_session_research.py"),
        "preflight_summary_sha256": digest(preflight_path),
        "surrender_summary_sha256": digest(surrender_path),
        "verification_summary_sha256": digest(verification_path),
        "response_sha256": {
            "initial_snapshot": snapshot0_sha, "initial_control": control_sha,
            "terminal_before": terminal0_sha, "war_options": options_sha,
            "surrender_submission": action_sha, "after_snapshot": snapshot1_sha,
            "terminal_after": terminal1_sha, "after_save": saved_sha,
            "verification_snapshot": snapshot2_sha,
            "terminal_second": terminal2_sha,
            "old_combat_transition": transition_sha,
        },
        "post_surrender_save_sha256": digest(post_save),
        "capture_report_sha256": digest(capture_path),
        "capture_cleanup_processes": 0,
        "native_surrender_validator_passed": True,
        "native_surrender_auto_accept": True,
        "war_absent_same_date": True,
        "terminal_before": before,
        "terminal_after": after,
        "terminal_core_identical_second_query": True,
        "old_combat_transition_status": "combat_not_found",
        "successor_unavailable_not_absence_proven":
            after["successor"]["state"] == "unavailable",
        "normal_battle_result_effects_executed": False,
        "generic_ai_voluntary_retreat_policy_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-attempt", required=True, type=Path)
    parser.add_argument("--terminal-attempt", required=True, type=Path)
    parser.add_argument("--game-exe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.source_attempt, args.terminal_attempt, args.game_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
