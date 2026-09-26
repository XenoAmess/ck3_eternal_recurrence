"""Project what two complete natural-join traces actually expose at schedule/fire.

The two immutable captures establish same-day roster expansion. This projector
keeps the still-unobserved event identity and combat-width inputs explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_native_join_full_day import CASES, project


def _load(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def project_case(attempt: Path, source_day: int) -> dict:
    validated = project(attempt, source_day)
    prefix = CASES[source_day]["prefix"]
    receipt_path = (attempt / "ck3-output" / "interactive-requests-responses"
                    / f"{prefix}-finish.json")
    receipt, sha = _load(receipt_path)
    if sha != validated["response_sha256"][f"{prefix}-finish"]:
        raise ValueError("validated finish receipt changed")
    trace = receipt["body"]["managed_trace"]["trace"]
    records = trace["records"]
    source_date = validated["source_date_raw"]
    arrival_date = validated["arrival_date_raw"]
    if (len(records) != 7 or any(row["capture_failure_flags"] for row in records)
            or any(row["native_date_raw"] != source_date for row in records[:2])
            or any(row["native_date_raw"] != arrival_date for row in records[2:])):
        raise ValueError("schedule/fire dates or capture flags changed")

    rolls = records[0]["advantage_rolls_raw"]
    base_advantage = records[0]["base_advantage_raw"]
    resolved_advantage = records[0]["resolved_advantage_raw"]
    if any((row["advantage_rolls_raw"] != rolls
            or row["base_advantage_raw"] != base_advantage
            or row["resolved_advantage_raw"] != resolved_advantage)
           for row in records):
        raise ValueError("retained advantage fields changed across captured boundaries")

    rng_before = records[0]["schedule_local_rng"]
    rng_after = records[1]["schedule_local_rng"]
    if rng_before["present"] is not True or rng_after["present"] is not True:
        raise ValueError("source schedule RNG snapshots missing")
    sides = [
        {
            "side_index": side,
            "source_regiment_count": len(records[1]["sides"][side]["regiments"]),
            "arrival_prefire_regiment_count": len(records[2]["sides"][side]["regiments"]),
            "source_fighting_raw": records[1]["sides"][side]["current_fighting_total_raw"],
            "arrival_prefire_fighting_raw": records[2]["sides"][side]["current_fighting_total_raw"],
            "source_first_fighting_subtotal_raw": records[1]["sides"][side]["first_fighting_subtotal_raw"],
            "arrival_prefire_first_fighting_subtotal_raw": records[2]["sides"][side]["first_fighting_subtotal_raw"],
            "scheduled_event_load_indexes": [
                row["sides"][side]["scheduled_commander_native_event_load_index"]
                for row in records],
        }
        for side in (0, 1)
    ]
    if (sides[0]["arrival_prefire_regiment_count"] <= sides[0]["source_regiment_count"]
            or sides[1]["arrival_prefire_regiment_count"] != sides[1]["source_regiment_count"]):
        raise ValueError("expected side0-only roster expansion absent")
    if trace["effect_roots"]:
        raise ValueError("this bounded projection assumes no captured effect roots")
    if any(index is not None for side in sides
           for index in side["scheduled_event_load_indexes"]):
        raise ValueError("this bounded projection assumes no resolved event load index")

    return {
        "source_day": source_day,
        "source_date_raw": source_date,
        "arrival_date_raw": arrival_date,
        "combat_id": validated["combat_id"],
        "joining_army_id": validated["joining_army_id"],
        "source_save_sha256": validated["source_save_sha256"],
        "bridge_dll_sha256": validated["bridge_dll_sha256"],
        "finish_response_sha256": sha,
        "capture_report_sha256": validated["capture_report_sha256"],
        "capture_failure_flags": trace["failure_flags"],
        "old_side0_army_ids": validated["old_side0_army_ids"],
        "new_side0_army_ids": validated["new_side0_army_ids"],
        "retained_advantage_rolls_raw": rolls,
        "retained_base_advantage_raw": base_advantage,
        "retained_resolved_advantage_raw": resolved_advantage,
        "source_schedule_rng_word0_before": rng_before["word0"],
        "source_schedule_rng_word0_after": rng_after["word0"],
        "sides": sides,
        "outgoing_damage": trace["outgoing_damage"],
        "post_counter_attack": trace["post_counter_attack"],
        "captured_effect_root_count": len(trace["effect_roots"]),
        "native_event_load_indexes_resolved": False,
        "explicit_width_input_captured": False,
        "general_join_schedule_order_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day11-attempt", type=Path, required=True)
    parser.add_argument("--day21-attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "ck3.native_join_schedule_boundary.v1",
              "game_build": "1.19.0.6",
              "cases": [project_case(args.day11_attempt, 11),
                        project_case(args.day21_attempt, 21)]}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "case_count": len(report["cases"])}))


if __name__ == "__main__":
    main()
