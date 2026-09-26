"""Prove that the agent's native v3 base input equals the direct v2 eval.

The v2 inputs are independently compared with next schedule in the referenced
per-day parity reports. This bridge does not assert transition/odds fidelity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _read(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def project_day(attempt: Path, v2_parity: Path, source_day: int) -> dict:
    parity, parity_sha = _read(v2_parity)
    base = attempt / "ck3-output/interactive-requests-responses"
    v2_receipt, v2_sha = _read(base / f"d{source_day}-direct-stats-v2.json")
    v3_receipt, v3_sha = _read(base / f"d{source_day}-direct-stats-v3.json")
    v2 = v2_receipt["body"]
    v3 = v3_receipt["body"]
    v2_inputs = v2["combat_simulation_inputs"]
    v3_inputs = v3["combat_simulation_inputs"]
    if (parity.get("schema") != "ck3.native_paused_stat_eval_next_schedule_parity.v1"
            or parity.get("source_day") != source_day
            or parity["response_sha256"]["native_v2_direct"] != v2_sha
            or parity["paused_direct_equals_next_schedule_count"] != parity["regiment_count"]
            or v2_receipt.get("result") != "CALL_COMPLETED"
            or v3_receipt.get("result") != "CALL_COMPLETED"
            or v2.get("status") != "available" or v3.get("status") != "available"
            or v2.get("queried_revision") != v3.get("queried_revision")
            or v2.get("target_province_id") != v3.get("target_province_id")
            or v3_inputs.get("base_inputs") != v2_inputs):
        raise ValueError("native v3 base inputs differ from proven v2 current-frame stats")
    return {"source_day": source_day,
            "v2_next_schedule_parity_report_sha256": parity_sha,
            "v2_live_response_sha256": v2_sha, "v3_live_response_sha256": v3_sha,
            "same_paused_revision": v3["queried_revision"],
            "regiment_count": parity["regiment_count"],
            "v3_base_inputs_exactly_equal_to_v2": True,
            "v2_equals_next_schedule_count": parity["regiment_count"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day11-attempt", type=Path, required=True)
    parser.add_argument("--day21-attempt", type=Path, required=True)
    parser.add_argument("--day11-v2-parity", type=Path, required=True)
    parser.add_argument("--day21-v2-parity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    days = [project_day(args.day11_attempt, args.day11_v2_parity, 11),
            project_day(args.day21_attempt, args.day21_v2_parity, 21)]
    report = {"schema": "ck3.native_paused_v3_base_equals_v2_schedule_parity.v1",
              "game_build": "1.19.0.6", "case_days": days,
              "total_v3_direct_equals_next_schedule_regiments": sum(
                  day["regiment_count"] for day in days),
              "current_paused_frame_stat_input_parity_proven_in_these_cases": True,
              "future_day_modifier_state_prediction_proven": False,
              "whole_battle_transition_or_win_rate_native_parity_proven": False}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "total": report["total_v3_direct_equals_next_schedule_regiments"]}))


if __name__ == "__main__":
    main()
