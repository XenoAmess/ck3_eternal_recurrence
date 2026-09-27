"""Project the exact day-11 active-control/precontact-v3 read-only pair."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = {
    "c086-before-snapshot": "059C435F0F133E7152E4CDDED6AE7432C382674F47870166E8FE906E913E3827",
    "c086-battle-control": "6DFC287C42154486D78E2609AEE1C74B2A00F7E2E018C8FBC4B90D639CC4D550",
    "c086-active-v3": "F191AC1EBB3C9010882B8AD2892346F8B0DAB52D7B64298C017D578B72118793",
    "c086-after-snapshot": "FD9E4E558F2E99C2708559FBA073BAE84B63EF792F27194E3CE5A8A822D84EB2",
    "cleanup-check": "77CBB30E996B556856EA3973826CC68D1B222B3757CC3A00723FB36328659352",
}


def _read(path: Path, expected_sha: str) -> dict[str, object]:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    value = json.loads(raw)
    assert isinstance(value, dict), path
    return value


def project(attempt_dir: Path) -> dict[str, object]:
    directory = attempt_dir / "ck3-output" / "interactive-requests-responses"
    before = _read(directory / "c086-before-snapshot.json", SOURCE_SHA256["c086-before-snapshot"])
    control = _read(directory / "c086-battle-control.json", SOURCE_SHA256["c086-battle-control"])
    v3 = _read(directory / "c086-active-v3.json", SOURCE_SHA256["c086-active-v3"])
    after = _read(directory / "c086-after-snapshot.json", SOURCE_SHA256["c086-after-snapshot"])
    cleanup = _read(attempt_dir / "cleanup-check.json", SOURCE_SHA256["cleanup-check"])
    assert all(row["result"] == "CALL_COMPLETED" for row in (before, control, v3, after))
    first, last = before["body"], after["body"]
    assert first["paused"] is last["paused"] is True
    assert first["date_raw"] == last["date_raw"] == 53146488
    assert first["revision"] == last["revision"] == 5
    assert first["native_revision"] == last["native_revision"] == 4
    assert first["snapshot_id"] == last["snapshot_id"] == "native:4"
    assert cleanup["cleanup_ok"] is True and cleanup["capture_returncode"] == 0
    battle = control["body"]["battle_control_snapshot"]
    receipt = control["body"]["active_combat_resume_inputs_v1"]
    inputs = v3["body"]["combat_simulation_inputs"]
    base = inputs["base_inputs"]
    scenario = base["scenario"]
    assert all(row["body"]["queried_revision"] == 5 for row in (control, v3))
    assert all(row["body"]["queried_native_revision"] == 4 for row in (control, v3))
    assert all(row["body"]["queried_snapshot_id"] == "native:4" for row in (control, v3))
    assert battle["combat_id"] == receipt["source"]["combat_id"] == 16777218
    assert battle["province_id"] == base["target_province_id"] == 2633
    assert receipt["status"] == "unavailable" and receipt["input_observation_ready"] is False
    assert base["participant_policy"] == "explicit_hypothetical_fixed_at_contact_no_reinforcements"
    assert scenario["kind"] == "explicit_hypothetical_contact"
    assert inputs["completeness"]["observation_slice"] == "precontact-phase-event-inputs-v3"
    assert inputs["completeness"]["planner_usable"] is False
    actual_rosters = [
        [row["public_cunit_id"] for row in battle[role]["ordered_armies"]]
        for role in ("attacker", "defender")
    ]
    assert actual_rosters == [scenario["attacker_army_ids"], scenario["defender_army_ids"]]
    observed = [row for row in base["ongoing_combats"] if row["combat_id"] == battle["combat_id"]]
    assert len(observed) == 1
    assert (observed[0]["base_combat_width"], observed[0]["final_combat_width"]) == (
        battle["base_combat_width"], battle["final_combat_width"]
    )
    hypothetical = base["target_province"]["precontact_width"]
    assert hypothetical["status"] == "available"
    assert (hypothetical["base"], hypothetical["final"]) == (1539, 1385)
    assert (battle["base_combat_width"], battle["final_combat_width"]) == (1645, 1480)
    commander_candidates = [
        {
            "army_id": army["native_carmy_id"],
            "character_id": army["commander"]["character_id"],
            "hypothetical_min_roll": army["commander"]["battle_context"]["effective_min_roll"],
            "hypothetical_max_roll": army["commander"]["battle_context"]["effective_max_roll"],
        }
        for army in base["armies"]
    ]
    assert battle["attacker"]["selected_commander_character_id"] in {
        row["character_id"] for row in commander_candidates
    }
    assert battle["defender"]["selected_commander_character_id"] in {
        row["character_id"] for row in commander_candidates
    }
    battle_regiments = {
        row["regiment_id"]: (row["native_carmy_id"], row["current_fighting_raw"])
        for role in ("attacker", "defender")
        for bucket in ("levy_entries", "men_at_arms_entries")
        for row in battle[role][bucket]
    }
    v3_regiments = {
        row["regiment_id"]: (army["native_carmy_id"], row)
        for army in base["armies"] for row in army["regiments"]
    }
    assert len(battle_regiments) == len(v3_regiments) == 51
    assert battle_regiments.keys() == v3_regiments.keys()
    assert all(battle_regiments[regiment_id][0] == v3_regiments[regiment_id][0]
               for regiment_id in battle_regiments)
    different_current_ids = sorted(
        regiment_id for regiment_id, (_, battle_current_raw) in battle_regiments.items()
        if battle_current_raw != v3_regiments[regiment_id][1]["current_soldiers"] * 100000
    )
    assert len(different_current_ids) == 51
    assert battle_regiments[51][1] == 17579130
    assert v3_regiments[51][1]["current_soldiers"] == 193
    assert v3_regiments[51][1]["counter"]["current_chunk_raw"] == 193000
    return {
        "schema": "ck3.native_active_control_precontact_v3_pair.v1",
        "source": {"attempt": 86, "sha256": SOURCE_SHA256},
        "identity": {
            "date_raw": 53146488, "snapshot_id": "native:4",
            "public_revision": 5, "native_revision": 4,
            "combat_id": battle["combat_id"], "province_id": battle["province_id"],
        },
        "actual": {
            "phase": battle["phase"], "phase_day": battle["phase_day"],
            "roll_cadence_counter": battle["roll_cadence_counter"],
            "base_width": battle["base_combat_width"],
            "final_width": battle["final_combat_width"],
            "ordered_army_ids": actual_rosters,
            "selected_commander_character_ids": [
                battle[role]["selected_commander_character_id"]
                for role in ("attacker", "defender")
            ],
            "entry_current_sum_raw": [
                sum(entry["current_fighting_raw"] for bucket in (
                    "levy_entries", "men_at_arms_entries") for entry in battle[role][bucket])
                for role in ("attacker", "defender")
            ],
        },
        "v3": {
            "status": v3["body"]["status"],
            "observation_slice": inputs["completeness"]["observation_slice"],
            "participant_policy": base["participant_policy"],
            "scenario_kind": scenario["kind"],
            "hypothetical_base_width": hypothetical["base"],
            "hypothetical_final_width": hypothetical["final"],
            "ongoing_combat_observed_actual_width": [
                observed[0]["base_combat_width"], observed[0]["final_combat_width"]
            ],
            "commander_candidates": commander_candidates,
            "planner_usable": inputs["completeness"]["planner_usable"],
        },
        "active_resume": {
            "status": receipt["status"],
            "reason": receipt["unavailable_reason"],
            "missing_required_domains": receipt["missing_required_domains"],
        },
        "regiment_crosswalk": {
            "matched_regiment_and_army_ids": 51,
            "current_state_differences": len(different_current_ids),
            "example_regiment_51": {
                "battle_current_raw": battle_regiments[51][1],
                "v3_army_current_soldiers": v3_regiments[51][1]["current_soldiers"],
                "v3_precontact_counter_chunk_raw": v3_regiments[51][1]["counter"]["current_chunk_raw"],
            },
        },
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
