"""Project the exact 088 read-only active-counter receipt into a small vector."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = {
    "c088-before-snapshot": "95C42C520926CF3B66F106ADFBFF4D7E91577F71820F83A7EAFDA8E3E2A11FD4",
    "c088-battle-control": "350941D8F88EAE8BA5F91C9CBDCC8F025920D9F120842C6571E832AD86CF396F",
    "c088-after-snapshot": "5FF86DF09D0DF07F222F89DFD1D42970BA567E56B7C57F481A4D16C1F7BC0351",
    "cleanup-check": "050123AB77778D00B3D6E66A23C0EE033A9ADD938B8DBEBD10A326756B74164F",
}
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "F56304CC0D46BFFCDC3477FEBD823235AB956E8CAFF5DB4F1432F7C6B4279D32"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def _read(path: Path, expected_sha: str) -> dict[str, object]:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    value = json.loads(raw)
    assert isinstance(value, dict), path
    return value


def project(attempt_dir: Path) -> dict[str, object]:
    response_dir = attempt_dir / "ck3-output" / "interactive-requests-responses"
    before = _read(response_dir / "c088-before-snapshot.json", SOURCE_SHA256["c088-before-snapshot"])
    control = _read(response_dir / "c088-battle-control.json", SOURCE_SHA256["c088-battle-control"])
    after = _read(response_dir / "c088-after-snapshot.json", SOURCE_SHA256["c088-after-snapshot"])
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
    counter = battle["active_counter_inputs_v1"]
    assert battle["combat_id"] == counter["source_combat_id"] == 16777218
    assert battle["province_id"] == counter["source_target_province_id"] == 2633
    assert battle["snapshot_revision"] == first["native_revision"]
    assert battle["observed_date_raw"] == first["date_raw"]
    assert battle["subject_public_cunit_id"] == 18 and battle["side_index"] == 1
    assert battle["phase"] == "main" and battle["phase_day"] == 7
    assert counter["status"] == "available" and counter["operand_census_complete"] is True
    assert counter["scale"] == 100000 and counter["class_count"] == 13
    assert len(counter["sides"]) == len(counter["contexts"]) == 2
    side_summary = []
    for index, role in enumerate(("attacker", "defender")):
        side = counter["sides"][index]
        entries = side["men_at_arms_entries"]
        assert side["side_index"] == index
        assert side["primary_owner_character_id"] == battle[role]["primary_participant_character_id"]
        assert len(entries) == len(battle[role]["men_at_arms_entries"])
        for row, parent in zip(entries, battle[role]["men_at_arms_entries"]):
            for key in ("regiment_id", "native_carmy_id", "current_fighting_raw"):
                assert row[key] == parent[key]
        side_summary.append({
            "side_index": index,
            "primary_owner_character_id": side["primary_owner_character_id"],
            "selected_commander_character_id": battle[role]["selected_commander_character_id"],
            "maa_count": len(entries),
            "class_available_count": sum(row["status"] == "available" for row in entries),
            "class_absent_count": sum(row["status"] == "absent" for row in entries),
            "counter_efficiency_raw": side["counter_efficiency_raw"],
            "counter_resistance_raw": side["counter_resistance_raw"],
        })
    assert [row["primary_owner_character_id"] for row in side_summary] == [31549, 29829]
    assert [row["maa_count"] for row in side_summary] == [18, 14]
    assert [row["class_available_count"] for row in side_summary] == [5, 3]
    assert [row["class_absent_count"] for row in side_summary] == [13, 11]
    regiment_51 = next(row for side in counter["sides"]
                       for row in side["men_at_arms_entries"] if row["regiment_id"] == 51)
    assert regiment_51["current_fighting_raw"] == 17579130
    assert regiment_51["current_chunk_raw"] == 175791
    assert [row["class_index"] for row in regiment_51["targets"]] == [4, 5, 8, 9]
    assert receipt["status"] == "unavailable" and receipt["input_observation_ready"] is False
    assert "active_regiment_counter_class_stack_context" in receipt["missing_required_domains"]
    assert cleanup["cleanup_ok"] is True and cleanup["capture_returncode"] == 0
    assert cleanup["shutdown"]["tree_gone"] is True
    assert cleanup["shutdown"]["job_active_processes_final"] == 0
    return {
        "schema": "ck3.native_active_counter_088.v1",
        "source": {"attempt": 88, "sha256": SOURCE_SHA256,
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
                   "counter_status": counter["status"],
                   "class_count": counter["class_count"],
                   "sides": side_summary, "contexts": counter["contexts"],
                   "regiment_51": regiment_51},
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
