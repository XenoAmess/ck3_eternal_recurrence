"""Project the hash-bound 093 same-frame active counter receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SHA256 = {
    "snapshot": "A49400E9E5AFDA8F832FDCC6BEB66E152621267898C25FCB09E2FCA3492C866C",
    "control": "D422C36240CD58F61D74F8B10756F01C63F8902E500E3E29066275E71F3C492A",
    "input_freeze": "13A1B65355CCBBD987367837C6E16C4883BADD6C33D46D978050F6445BD738A5",
    "summary": "AC11791CD56C5293D40779CA994305E2744C31BBF1D3D9665B3939A241A35BFB",
    "cleanup": "38917314E6AFB4B36EF74C48442D628A8AC323EF5AC2EF34C920A72AD5AD2E92",
    "capture_report": "9796EA6C7120B0CDB55227CE0E721FB404B58201DAD73C902DE92AAD2A5B01B9",
}
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "0E7DCBB78E77B76EB1912D9EB630D9E7A41C6D4A4EDF0A38EC4C364CAF6F66CF"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"
COUNTER_GAP = "active_regiment_counter_class_stack_context"


def read(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    value = json.loads(raw)
    assert isinstance(value, dict), path
    return value


def project(attempt_dir: Path) -> dict:
    responses = attempt_dir / "ck3-output/interactive-requests-responses"
    snapshot = read(responses / "c093-before-snapshot.json", SHA256["snapshot"])
    control = read(responses / "c093-control.json", SHA256["control"])
    freeze = read(attempt_dir / "input-freeze.json", SHA256["input_freeze"])
    summary = read(attempt_dir / "readonly-summary.json", SHA256["summary"])
    cleanup = read(attempt_dir / "cleanup-check.json", SHA256["cleanup"])
    report = read(attempt_dir / "ck3-output/capture-report.json", SHA256["capture_report"])
    assert freeze["source"]["sha256"] == SAVE_SHA256
    assert freeze["bridge"]["sha256"] == BRIDGE_SHA256
    assert freeze["exe_sha256"] == EXE_SHA256
    assert snapshot["result"] == control["result"] == "CALL_COMPLETED"
    assert cleanup["cleanup_ok"] is True and cleanup["capture_returncode"] == 0
    assert cleanup["shutdown"]["tree_gone"] is True
    assert cleanup["shutdown"]["job_active_processes_final"] == 0
    assert report["result"] == "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO"

    before = snapshot["body"]
    payload = control["body"]
    battle = payload["battle_control_snapshot"]
    resume = payload["active_combat_resume_inputs_v1"]
    counter = battle["active_counter_inputs_v1"]
    assert before["paused"] is True and before["date_raw"] == 53146488
    assert battle["observed_date_raw"] == before["date_raw"]
    assert battle["combat_id"] == resume["source"]["combat_id"] == 16777218
    assert battle["side_index"] == 1
    assert counter["status"] == "available" and counter["operand_census_complete"] is True
    assert resume["observed"]["active_counter_inputs_v1"] == counter
    assert resume["status"] == "unavailable" and resume["input_observation_ready"] is False
    assert COUNTER_GAP in resume["missing_required_domains"]
    assert summary["control_response_sha256"] == SHA256["control"]
    assert summary["snapshot_response_sha256"] == SHA256["snapshot"]
    assert summary["counter_entry_counts"] == [len(side["men_at_arms_entries"])
                                               for side in counter["sides"]]
    assert summary["counter_contexts"] == counter["contexts"]
    assert summary["resume_missing_domains"] == resume["missing_required_domains"]
    return {
        "schema": "ck3.native_active_resume_counter_receipt_093.v1",
        "source": {"attempt": 93, "sha256": SHA256,
                   "exe_sha256": EXE_SHA256, "bridge_sha256": BRIDGE_SHA256,
                   "save_sha256": SAVE_SHA256},
        "identity": {"snapshot_id": before["snapshot_id"],
                     "date_raw": before["date_raw"],
                     "combat_id": battle["combat_id"],
                     "subject_public_cunit_id": battle["subject_public_cunit_id"],
                     "side_index": battle["side_index"]},
        "observed": {"counter_class_count": counter["class_count"],
                     "counter_entry_counts": summary["counter_entry_counts"],
                     "counter_contexts": counter["contexts"],
                     "resume_counter_equals_parent": True,
                     "resume_status": resume["status"],
                     "resume_input_observation_ready": resume["input_observation_ready"],
                     "resume_missing_domains": resume["missing_required_domains"]},
        "cleanup_ok": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = project(args.attempt_dir)
    if args.fixture is not None:
        assert value == json.loads(args.fixture.read_text(encoding="utf-8"))
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        assert not args.output.exists(), args.output
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
