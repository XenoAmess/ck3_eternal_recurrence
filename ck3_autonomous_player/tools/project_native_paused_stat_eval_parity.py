"""Compare a paused native v2 stat evaluation to the next schedule boundary.

Each comparison uses two isolated replays of the same immutable stock CK3 save:
one read-only paused query, and one bounded native day-advance trace. It does
not assert that future days without a new paused observation are predictable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CASES = {11: (53146488, 51, 32, 24), 21: (53146728, 63, 37, 27)}


def _read(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def _receipt(base: Path, name: str) -> tuple[dict, str]:
    data, digest = _read(base / f"{name}.json")
    if data.get("result") != "CALL_COMPLETED":
        raise ValueError(f"incomplete response: {name}")
    return data["body"], digest


def _insert(mapping: dict, key: int, value: dict, role: str) -> None:
    if key in mapping:
        raise ValueError(f"duplicate regiment {key} in {role}")
    mapping[key] = value


def project(paused_attempt: Path, trace_attempt: Path, source_day: int) -> dict:
    date_raw, expected_count, expected_changed, expected_knights = CASES[source_day]
    source, source_sha = _read(paused_attempt / "ck3-output/checkpoint-copy.json")
    trace_source, trace_source_sha = _read(trace_attempt / "ck3-output/checkpoint-copy.json")
    if (source["source"]["save"]["sha256"] != trace_source["source"]["save"]["sha256"]
            or source["source"]["date_raw"] != date_raw
            or trace_source["source"]["date_raw"] != date_raw):
        raise ValueError("paused query and native trace do not share the same immutable save")
    preflight, preflight_sha = _read(paused_attempt / "ck3-output/preflight.json")
    session, session_sha = _read(paused_attempt / "ck3-output/session-result.json")
    if (preflight["game"]["sha256"] != EXE_SHA256
            or session["shutdown"]["cleanup_proven"] is not True):
        raise ValueError("game build or paused-session cleanup invalid")
    paused_base = paused_attempt / "ck3-output/interactive-requests-responses"
    trace_base = trace_attempt / "ck3-output/interactive-requests-responses"
    before, before_sha = _receipt(paused_base, f"d{source_day}-before-snapshot")
    control, control_sha = _receipt(paused_base, f"d{source_day}-before-control")
    direct, direct_sha = _receipt(paused_base, f"d{source_day}-direct-stats-v2")
    after, after_sha = _receipt(paused_base, f"d{source_day}-after-snapshot")
    trace_prefix = "d11r2" if source_day == 11 else "d21"
    finished, finish_sha = _receipt(trace_base, f"{trace_prefix}-finish")
    control = control["battle_control_snapshot"]
    native = direct["combat_simulation_inputs"]
    trace = finished["managed_trace"]["trace"]
    boundary = trace["records"][0]
    if (not before["paused"] or not after["paused"]
            or before["date_raw"] != date_raw or after["date_raw"] != date_raw
            or before["revision"] != after["revision"]
            or control["combat_id"] != 16777218 or control["observed_date_raw"] != date_raw
            or direct["status"] != "available" or direct["queried_revision"] != before["revision"]
            or direct["target_province_id"] != 2633 or direct["common_war_ids"] != [4]
            or native["completeness"]["input_observation_ready"] is not True
            or trace["failure_flags"] != 0 or len(trace["records"]) != 7
            or boundary["native_date_raw"] != date_raw
            or boundary["boundary"] != "native_capture_before_side0_schedule_call_0x27FB58F"):
        raise ValueError("paused or native schedule identity drifted")
    control_rows = {}
    schedule_rows = {}
    for side_index, role in enumerate(("attacker", "defender")):
        for row in (*control[role]["levy_entries"], *control[role]["men_at_arms_entries"]):
            _insert(control_rows, row["regiment_id"], (side_index, row), "control")
        for row in boundary["sides"][side_index]["regiments"]:
            _insert(schedule_rows, row["regiment_id"], (side_index, row), "schedule")
    direct_rows = {}
    direct_knights = {}
    for army in native["armies"]:
        side_index = 0 if army["encounter_role"] == "attacker" else 1
        for row in army["regiments"]:
            if row["effective_stats"]["status"] != "available":
                raise ValueError("native direct regiment stats unavailable")
            _insert(direct_rows, row["regiment_id"], (side_index, row), "direct")
        for row in army["knights"]["members"]:
            _insert(direct_knights, row["source_regiment_id"], row, "direct knight")
    if (control_rows.keys() != direct_rows.keys()
            or direct_rows.keys() != schedule_rows.keys()
            or len(direct_rows) != expected_count
            or len(direct_knights) != expected_knights):
        raise ValueError("regiment roster or knight census differs across reads")
    compared = []
    changed = 0
    for regiment_id in sorted(direct_rows):
        control_side, old = control_rows[regiment_id]
        direct_side, new = direct_rows[regiment_id]
        schedule_side, scheduled = schedule_rows[regiment_id]
        if control_side != direct_side or direct_side != schedule_side:
            raise ValueError("regiment battle side changed")
        old_pair = (old["effective_damage_raw"], old["effective_toughness_raw"])
        new_pair = (new["effective_stats"]["damage_raw"],
                    new["effective_stats"]["toughness_raw"])
        schedule_pair = (scheduled["effective_damage_raw"],
                         scheduled["effective_toughness_raw"])
        if new_pair != schedule_pair:
            raise ValueError(f"paused native evaluator did not predict schedule row {regiment_id}")
        changed += old_pair != new_pair
        knight = direct_knights.get(regiment_id)
        if knight and ((knight["effective_damage_raw"], knight["effective_toughness_raw"])
                       != new_pair):
            raise ValueError("direct knight contribution differs from native regiment evaluator")
        compared.append({"side_index": direct_side, "regiment_id": regiment_id,
                         "kind": "knight" if knight else new["kind"]["value"],
                         "old_cached_damage_raw": old_pair[0],
                         "old_cached_toughness_raw": old_pair[1],
                         "paused_direct_damage_raw": new_pair[0],
                         "paused_direct_toughness_raw": new_pair[1],
                         "next_schedule_damage_raw": schedule_pair[0],
                         "next_schedule_toughness_raw": schedule_pair[1],
                         "knight_character_id": knight["character_id"] if knight else None,
                         "knight_prowess": knight["prowess"] if knight else None,
                         "knight_effectiveness_raw":
                         knight["knight_effectiveness_raw"] if knight else None})
    if changed != expected_changed:
        raise ValueError("cached-to-direct stat change count drifted")
    return {"schema": "ck3.native_paused_stat_eval_next_schedule_parity.v1",
            "game_build": "1.19.0.6", "exe_sha256": EXE_SHA256,
            "source_day": source_day, "date_raw": date_raw, "combat_id": 16777218,
            "source_save_sha256": source["source"]["save"]["sha256"],
            "paused_checkpoint_copy_sha256": source_sha,
            "trace_checkpoint_copy_sha256": trace_source_sha,
            "paused_preflight_sha256": preflight_sha,
            "paused_session_result_sha256": session_sha,
            "response_sha256": {"before": before_sha, "control": control_sha,
                                "native_v2_direct": direct_sha, "after": after_sha,
                                "next_schedule_trace": finish_sha},
            "query_target_province_id": 2633,
            "query_attacker_entry_province_id": direct["attacker_entry_province_id"],
            "query_attacker_army_ids": direct["attacker_army_ids"],
            "query_defender_army_ids": direct["defender_army_ids"],
            "paused_same_revision_and_date_after_read": True,
            "regiment_count": len(compared),
            "control_cache_differs_from_direct_count": changed,
            "knight_direct_effectiveness_count": len(direct_knights),
            "paused_direct_equals_next_schedule_count": len(compared),
            "per_regiment_comparison": compared,
            "next_day_same_saved_state_input_parity_proven": True,
            "arbitrary_future_daily_modifier_state_predicted": False,
            "specific_modifier_decomposition_proven": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paused-attempt", type=Path, required=True)
    parser.add_argument("--trace-attempt", type=Path, required=True)
    parser.add_argument("--source-day", type=int, choices=sorted(CASES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.paused_attempt, args.trace_attempt, args.source_day)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "regiment_count": report["regiment_count"],
                      "cache_differs_count": report["control_cache_differs_from_direct_count"],
                      "direct_equals_schedule_count": report["paused_direct_equals_next_schedule_count"]}))


if __name__ == "__main__":
    main()
