"""Verify and project the frozen 074 post-submit next-day readback, read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "docs/ck3-native-ai/research/winner-ai-postsubmit-next-day-074.json"


def read_json(path: Path, expected_sha: str | None = None) -> dict:
    raw = path.read_bytes()
    if expected_sha is not None:
        assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    return json.loads(raw)


def project(attempt: Path) -> dict:
    vector = read_json(VECTOR)
    assert vector["schema"] == "ck3.native_ai_winner_postsubmit_next_day_frozen_vector.v1"
    assert attempt.resolve() == Path(vector["attempt_path"]).resolve()
    raw = {name: read_json(attempt / name, sha)
           for name, sha in vector["evidence_sha256"].items()
           if name.endswith(".json")}
    observations_path = attempt / "daily-observations.jsonl"
    assert hashlib.sha256(observations_path.read_bytes()).hexdigest().upper() == \
        vector["evidence_sha256"]["daily-observations.jsonl"]
    rows = [json.loads(line) for line in observations_path.read_text(encoding="utf-8").splitlines()
            if line]
    assert len(rows) == 28
    terminal, next_day = rows[26], rows[27]
    frozen_terminal = vector["terminal_day"]
    frozen_next = vector["next_day"]
    subject = vector["subject"]
    freeze = raw["input-freeze.json"]
    assert freeze["source_save"]["sha256"] == vector["source_save_sha256"]
    assert freeze["game_exe"]["sha256"] == vector["exe_sha256"]
    assert freeze["binaries"]["xar_ck3_bridge.dll"]["sha256"] == vector["observer_dll_sha256"]
    identity = read_json(attempt / "ck3-output/live-run-identity.json")
    assert identity["identities"][0]["run_id"] == vector["run_id"]
    audit = raw["audit-result.json"]
    assert audit["status"] == "GREEN" and len(audit["checks"]) == 31
    assert all(audit["checks"].values())
    assert audit["checks"]["reference_terminal_exact_match_before_next_day"] is True
    assert audit["accepted_command_causally_proven"] is False
    summary = raw["probe-summary.json"]
    assert summary["status"] == "next_day_observed"
    assert summary["movement_observation_class"] == \
        "position_and_route_unchanged_execution_unproven"
    assert summary["queue_acceptance_is_execution_proof"] is False
    for day, row in ((26, terminal), (27, next_day)):
        snapshot = raw[f"ck3-output/interactive-requests-responses/{day}-snapshot.json"]
        private = raw[f"ck3-output/interactive-requests-responses/{day}-ai-reentry.json"]
        transition = raw[f"ck3-output/interactive-requests-responses/{day}-winner-terminal-a.json"]
        assert snapshot["result"] == private["result"] == transition["result"] == "CALL_COMPLETED"
        assert snapshot["body"]["date_raw"] == row["date_raw"]
        assert private["body"]["observer"] == row["ai_reentry_observer"]
        assert transition["body"]["battle_terminal_transition"]["prior"]["combat_id"] == subject["combat_id"]
        war = next(w for w in snapshot["body"]["active_wars"] if w["war_id"] == subject["war_id"])
        army = next(a for a in war["allied_armies"] if a["army_id"] == subject["cunit_id"])
        assert army == row["winner_army"]
        assert army["owner_character_id"] == subject["owner_character_id"]
        assert row["subject"]["move_target_province_id"] == subject["target_province_id"]
        assert row["ai_reentry_observer"]["failure_flags"] == 0
    assert terminal["day_index"] == frozen_terminal["day_index"]
    assert terminal["date_raw"] == frozen_terminal["date_raw"]
    assert terminal["terminal_kind"] == frozen_terminal["terminal_kind"]
    assert terminal["terminal_event_sequence"] == frozen_terminal["event_sequence"]
    assert terminal["winner_raw"] == frozen_terminal["winner_raw"]
    for key in ("current_province_id", "route_province_ids", "army_state"):
        assert terminal["winner_army"][key] == frozen_terminal[key]
    after_observer = terminal["ai_reentry_observer"]
    assert len(after_observer["builder_outcomes"]) == len(after_observer["records"]) == 1
    outcome = after_observer["builder_outcomes"][0]
    submit = after_observer["records"][0]
    assert outcome["result_handled_raw"] == frozen_terminal["builder_result_handled_raw"]
    assert outcome["result_second_raw"] == frozen_terminal["builder_result_second_raw"]
    assert outcome["main_submit_calls"] == frozen_terminal["builder_main_submit_calls"]
    assert after_observer["fallback_submit_matching_calls"] == frozen_terminal["fallback_submit_matching_calls"]
    assert submit["queue_accepted"] == frozen_terminal["fallback_queue_accepted"]
    assert submit["command_target_province_id"] == subject["target_province_id"]
    assert next_day["day_index"] == frozen_next["day_index"]
    assert next_day["date_raw"] == frozen_next["date_raw"]
    for key in ("current_province_id", "route_province_ids", "move_target_province_id", "army_state"):
        assert next_day["winner_army"][key] == frozen_next[key]
    assert next_day["subject"]["movement_or_retreat_state_raw"] == \
        frozen_next["private_movement_or_retreat_state_raw"]
    next_observer = next_day["ai_reentry_observer"]
    assert len(next_observer["builder_outcomes"]) - len(after_observer["builder_outcomes"]) == \
        frozen_next["new_builder_outcomes"]
    assert len(next_observer["records"]) - len(after_observer["records"]) == \
        frozen_next["new_submit_records"]
    assert next_observer["failure_flags"] == frozen_next["observer_failure_flags"]
    assert (next_day["winner_army"]["current_province_id"] != terminal["winner_army"]["current_province_id"]) is \
        frozen_next["position_changed_since_terminal"]
    assert (next_day["winner_army"]["current_province_id"] == subject["target_province_id"]) is \
        frozen_next["target_arrival_observed"]
    session = raw["ck3-output/session-result.json"]
    capture = raw["ck3-output/capture-report.json"]
    assert session["ok"] is True and session["shutdown"]["cleanup_proven"] is True
    assert session["shutdown"]["job_active_processes_final"] == 0
    assert capture["environment_session_complete"] is True
    assert capture["cleanup_process_inventory"]["processes"] == []
    return {
        "schema": "ck3.native_ai_winner_postsubmit_next_day_projection.v1",
        "case_id": vector["case_id"],
        "result": "verified",
        "run_id": vector["run_id"],
        "observed_event_class": vector["consumer_boundary"]["observed_event_class"],
        "day27_position_changed": frozen_next["position_changed_since_terminal"],
        "day27_route_province_ids": frozen_next["route_province_ids"],
        "queue_apply_directly_observed": False,
        "post_queue_movement_executed": None,
        "general_ai_dispatch_rule_proven": False,
        "audit_sha256": vector["evidence_sha256"]["audit-result.json"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.attempt), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
