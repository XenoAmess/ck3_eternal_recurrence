"""Verify and project the frozen 072 AI terminal-reentry observation, read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "docs/ck3-native-ai/research/winner-ai-terminal-reentry-072.json"


def read_json(path: Path, expected_sha: str | None = None) -> dict:
    raw = path.read_bytes()
    if expected_sha is not None:
        assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    return json.loads(raw)


def project(attempt: Path) -> dict:
    vector = read_json(VECTOR)
    assert vector["schema"] == "ck3.native_ai_winner_terminal_reentry_frozen_vector.v1"
    assert attempt.resolve() == Path(vector["attempt_path"]).resolve()
    raw = {name: read_json(attempt / name, sha)
           for name, sha in vector["evidence_sha256"].items()}
    private = raw["ck3-output/interactive-requests-responses/26-ai-reentry.json"]
    terminal = raw["ck3-output/interactive-requests-responses/26-winner-terminal-a.json"]
    observer = private["body"]["observer"]
    native = terminal["body"]["battle_terminal_transition"]
    summary = read_json(attempt / "probe-summary.json")
    freeze = read_json(attempt / "input-freeze.json")
    audit = raw["audit-result.json"]
    session = raw["ck3-output/session-result.json"]
    capture = raw["ck3-output/capture-report.json"]
    assert freeze["repo_commit"] == vector["observer_source_commit"]
    assert freeze["game_exe"]["sha256"] == vector["exe_sha256"]
    assert freeze["binaries"]["xar_ck3_bridge.dll"]["sha256"] == vector["observer_dll_sha256"]
    assert read_json(attempt / "ck3-output/live-run-identity.json")["identities"][0]["run_id"] == vector["run_id"]
    assert private["result"] == terminal["result"] == "CALL_COMPLETED"
    assert private["body"]["accepted"] is True
    assert observer["installed"] is True and observer["failure_flags"] == 0
    assert observer["overflow_count"] == 0
    assert observer["builder_matching_calls"] == vector["builder"]["matching_calls"]
    assert observer["submit_matching_calls"] == vector["builder"]["main_submit_calls"]
    assert observer["fallback_submit_matching_calls"] == vector["fallback_submit"]["matching_calls"]
    assert len(observer["builder_outcomes"]) == len(observer["records"]) == 1
    outcome = observer["builder_outcomes"][0]
    submit = observer["records"][0]
    builder_fields = {"return_rva": "builder_return_rva", "outcome_code": "outcome"}
    for key, value in vector["builder"].items():
        if key not in {"matching_calls", "outcome_name"}:
            assert outcome[builder_fields.get(key, key)] == value, key
    for key, value in vector["fallback_submit"].items():
        if key != "matching_calls":
            assert submit[key if key != "return_rva" else "submit_return_rva"] == value, key
    assert outcome["cunit_id"] == submit["cunit_id"] == vector["subject"]["cunit_id"]
    assert outcome["target_province_id"] == submit["command_target_province_id"] == vector["subject"]["target_province_id"]
    assert native["prior"]["terminal_kind"] == vector["terminal"]["kind"]
    assert native["terminal_journal"]["event_sequence"] == vector["terminal"]["event_sequence"]
    assert summary["before_terminal"]["day_index"] == vector["before_terminal"]["day_index"]
    assert summary["before_terminal"]["subject"]["move_target_province_id"] == vector["before_terminal"]["private_target_province_id"]
    assert summary["terminal"]["day_index"] == vector["terminal"]["day_index"]
    assert summary["terminal"]["winner_army"]["route_province_ids"] == vector["terminal"]["route_province_ids"]
    assert audit["status"] == "GREEN" and all(audit["checks"].values())
    assert session["ok"] is True and session["shutdown"]["cleanup_proven"] is True
    assert capture["environment_session_complete"] is True
    return {"schema": "ck3.native_ai_winner_terminal_reentry_projection.v1",
            "case_id": vector["case_id"], "result": "verified",
            "run_id": vector["run_id"], "observed_event_class":
            vector["consumer_boundary"]["observed_event_class"],
            "builder_outcome": vector["builder"]["outcome_name"],
            "fallback_queue_accepted": submit["queue_accepted"],
            "post_queue_movement_executed": None,
            "general_ai_dispatch_rule_proven": False,
            "raw_response_sha256": vector["evidence_sha256"]["ck3-output/interactive-requests-responses/26-ai-reentry.json"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.attempt), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
