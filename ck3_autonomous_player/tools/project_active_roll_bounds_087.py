"""Project the exact 087 read-only active-commander next-roll receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = {
    "c087-before-snapshot": "59BBCA62C10D4E900C77C16F697EF090092A7F777824914C4AED4CC8194A7E9C",
    "c087-battle-control": "3D8ECE6EE38809E370891668022445C94A9BC57DD6F97898607C93F5F78D753C",
    "c087-after-snapshot": "39C137C40788171FA429D56C8A37994D9D27E3BD26F6038B3763BF20C6968F46",
    "cleanup-check": "DE39DF25956F79FDD132D402931F83184C6257BE48D986FFEA38A7F005ADBE36",
}
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "EC0B57EC5036A10A87FDCBB8CC2E9DAB12EE2629CD442DBB9AC76BF0BAE63B92"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def _read(path: Path, expected_sha: str) -> dict[str, object]:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    value = json.loads(raw)
    assert isinstance(value, dict), path
    return value


def project(attempt_dir: Path) -> dict[str, object]:
    response_dir = attempt_dir / "ck3-output" / "interactive-requests-responses"
    before = _read(response_dir / "c087-before-snapshot.json", SOURCE_SHA256["c087-before-snapshot"])
    control = _read(response_dir / "c087-battle-control.json", SOURCE_SHA256["c087-battle-control"])
    after = _read(response_dir / "c087-after-snapshot.json", SOURCE_SHA256["c087-after-snapshot"])
    cleanup = _read(attempt_dir / "cleanup-check.json", SOURCE_SHA256["cleanup-check"])
    freeze = json.loads((attempt_dir / "input-freeze.json").read_text(encoding="utf-8"))
    assert freeze["source"]["sha256"] == SAVE_SHA256
    assert freeze["bridge"]["sha256"] == BRIDGE_SHA256
    assert freeze["exe_sha256"] == EXE_SHA256
    assert all(row["result"] == "CALL_COMPLETED" for row in (before, control, after))
    first, last = before["body"], after["body"]
    assert first["paused"] is last["paused"] is True
    assert first["date_raw"] == last["date_raw"] == 53146488
    for key in ("snapshot_id", "revision", "native_revision"):
        assert first[key] == last[key]
    body = control["body"]
    assert body["queried_snapshot_id"] == first["snapshot_id"]
    assert body["queried_revision"] == first["revision"]
    assert body["queried_native_revision"] == first["native_revision"]
    battle = body["battle_control_snapshot"]
    receipt = body["active_combat_resume_inputs_v1"]
    assert battle["combat_id"] == receipt["source"]["combat_id"] == 16777218
    assert battle["province_id"] == receipt["source"]["province_id"] == 2633
    assert battle["snapshot_revision"] == receipt["source"]["snapshot_revision"] == first["native_revision"]
    assert battle["observed_date_raw"] == receipt["source"]["observed_date_raw"] == first["date_raw"]
    assert battle["subject_public_cunit_id"] == receipt["source"]["subject_public_cunit_id"] == 18
    assert battle["side_index"] == 1 and battle["phase"] == "main" and battle["phase_day"] == 7
    assert receipt["status"] == "unavailable" and receipt["input_observation_ready"] is False
    assert "selected_commander_next_roll_bounds" not in receipt["missing_required_domains"]
    assert len(receipt["missing_required_domains"]) == 4
    bounds = []
    for index, role in enumerate(("attacker", "defender")):
        row = receipt["observed"][f"side_{index}_selected_commander_next_roll_bounds"]
        assert row == {"status": "available", "effective_min_roll": 0,
                       "effective_max_roll": 10, "unavailable_reason": None}
        bounds.append({"side_index": index,
                       "selected_commander_character_id": battle[role]["selected_commander_character_id"],
                       "current_roll_points": battle[role]["current_roll_points"],
                       "next_roll_bounds": row})
    assert [row["selected_commander_character_id"] for row in bounds] == [34320, 29829]
    assert cleanup["cleanup_ok"] is True and cleanup["capture_returncode"] == 0
    assert cleanup["shutdown"]["tree_gone"] is True
    assert cleanup["shutdown"]["job_active_processes_final"] == 0
    return {
        "schema": "ck3.native_active_commander_next_roll_087.v1",
        "source": {"attempt": 87, "sha256": SOURCE_SHA256,
                   "exe_sha256": EXE_SHA256, "bridge_sha256": BRIDGE_SHA256,
                   "save_sha256": SAVE_SHA256},
        "identity": {"snapshot_id": first["snapshot_id"],
                     "public_revision": first["revision"],
                     "native_revision": first["native_revision"],
                     "date_raw": first["date_raw"],
                     "combat_id": battle["combat_id"],
                     "province_id": battle["province_id"],
                     "subject_public_cunit_id": 18,
                     "subject_side_index": battle["side_index"]},
        "actual": {"phase": battle["phase"], "phase_day": battle["phase_day"],
                   "roll_cadence_counter": battle["roll_cadence_counter"],
                   "sides": bounds},
        "active_resume": {"status": receipt["status"],
                          "reason": receipt["unavailable_reason"],
                          "missing_required_domains": receipt["missing_required_domains"]},
        "cleanup_ok": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = project(args.attempt_dir)
    if args.fixture is not None:
        assert result == json.loads(args.fixture.read_text(encoding="utf-8"))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        assert not args.output.exists(), args.output
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
