"""Project sealed small timing evidence without reading runtime bodies."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/ck3-native-ai/evidence"
MAX_SOURCE_BYTES = 1024 * 1024


def read(name):
    path = EVIDENCE / name
    size = path.stat().st_size
    if size > MAX_SOURCE_BYTES:
        raise ValueError("only sealed small projections are admitted")
    raw = path.read_bytes()
    return json.loads(raw), {"path": path.relative_to(ROOT).as_posix(),
                             "bytes": size, "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True, cwd=ROOT).strip()
    p49, p49_ref = read("p49-settled-performance.json")
    stages, stages_ref = read("p49-stage-slice.json")
    p63, p63_ref = read("p63-r6-performance-and-normal-sdk-close-2026-10-18.json")
    p67, p67_ref = read("p67-p68-combat-query-archive-performance-2026-10-18.json")
    settled = p49["5104-5165"]
    stage = {row["stage"]: row for row in stages["stages"]}
    zero_groups = {key: value for key, value in settled["auto_by_group"].items() if value["game_days"] == 0}
    zero_seconds = sum(row["auto_seconds"] for row in zero_groups.values())
    progress_seconds = sum(row["auto_seconds"] for row in settled["auto_by_group"].values() if row["game_days"] > 0)
    assert sum(row["count"] for row in zero_groups.values()) == settled["zero_date_turns"]
    assert abs(zero_seconds + progress_seconds - settled["rpc_elapsed_by_tool_seconds"]["ck3_auto_turn"]) < 1e-7
    persistence = stage["driver.full_state_persistence"]
    stream = stage["driver.full_state_temp_stream_write"]
    serialize = stage["driver.full_state_json_serialization"]
    result = {
        "schema": "xar.sealed-performance-window-projection.v1",
        "machine_id": machine, "observed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "new arithmetic from sealed historical small evidence; no new runtime timings",
        "sources": [p49_ref, stages_ref, p63_ref, p67_ref],
        "historical_window": {"source_machine_ids": {
                                  "P49_settled": p49.get("machine_id", "unknown"),
                                  "P49_stages": stages.get("machine_id", "unknown"),
                                  "P63": p63["machine_id"]},
                              "P63_same_as_executing_machine": p63["machine_id"] == machine,
                              "stage_lower_source_clock": stages["time_lower"],
                              "stage_upper_source_clock": stages["time_upper"],
                              "P49_machine_identity_note": "small P49 source projections omit machine_id; ownership not inferred from paths or associated P63"},
        "P49_settled": {
            "game_days": settled["game_days"], "wall_seconds": settled["wall_seconds"],
            "turns": settled["turns"], "zero_date_turns": settled["zero_date_turns"],
            "zero_date_turn_fraction": settled["zero_date_turns"] / settled["turns"],
            "zero_date_auto_seconds": zero_seconds,
            "progress_auto_seconds": progress_seconds, "zero_date_groups": zero_groups,
            "rpc_busy_union_seconds": settled["rpc_busy_union_seconds"],
            "unattributed_gap_seconds": settled["unattributed_gap_seconds"],
            "date_changed_wait_seconds": stages["public_change_wait_by_calendar_delta"]["date_changed"]["elapsed_seconds"],
            "same_date_wait_seconds": stages["public_change_wait_by_calendar_delta"]["same_date"]["elapsed_seconds"],
            "plan_unique_wall_seconds": stages["plan_intervals"]["unique_wall_seconds"],
            "native_wait_within_plan_seconds": stages["nested_within_plan"]["native_wait_or_pipe"]["unique_intersection_seconds"],
            "semantic_snapshot_within_plan_seconds": stages["nested_within_plan"]["semantic_snapshot"]["unique_intersection_seconds"],
            "persistence": {"count": persistence["count"],
                            "sum_seconds": persistence["nested_elapsed_sum_seconds"],
                            "max_seconds": persistence["max_seconds"],
                            "stream_write_sum_seconds": stream["nested_elapsed_sum_seconds"],
                            "stream_fraction_of_persistence": stream["nested_elapsed_sum_seconds"] / persistence["nested_elapsed_sum_seconds"],
                            "serialization_sum_seconds": serialize["nested_elapsed_sum_seconds"]},
        },
        "P63": {"R6_window": p63["performance"]["R6_window"],
                "R5_window": p63["performance"]["R5_distinct_window"],
                "same_state_AB": False},
        "seconds_level_hotspot": "21 full-state writes total 10.448259s, 9.954374s in stream.write; JSON serialization is not this window's persistence bottleneck",
        "source_candidate": {"path": "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                             "functions": ["_combat_simulation_inputs_cache_for_snapshot", "_combat_simulation_inputs_v3_cache_for_snapshot"],
                             "issue": "existing frame equality rejection occurs after expensive full payload normalization",
                             "proposal": "reject the same stale frame before payload normalization; keep all current-frame normalization and result guards",
                             "predicted_seconds_saved": None, "new_cache": False, "live_accepted": False},
        "limits": ["Nested stages are overlapping categories and must not be summed into wall time.",
                   "Zero-date queries can be necessary business observations; the fraction is not a removal target.",
                   "P63 R5/R6 are distinct states; their rates are not a controlled speedup ratio.",
                   "P67 87.814s query lacks native/normalization/clone/archive/MCP component timings; no seconds are assigned to a component.",
                   "Actual game's date wait cannot be eliminated by skipping legal observation or changing war policy."],
        "new_game_or_native_calls": 0, "runtime_bodies_read": 0,
        "storage": {"policy_version": "1.0.0", "source_max_bytes": MAX_SOURCE_BYTES,
                    "output_limit_bytes": MAX_SOURCE_BYTES, "deletions": 0,
                    "record_review_at_utc": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 4320 * 3600, timezone.utc).isoformat()},
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    if len(encoded) > MAX_SOURCE_BYTES:
        raise ValueError("projection exceeds its finite output budget")
    args.receipt.write_bytes(encoded)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(encoded),
                      "zero_date_turn_fraction": result["P49_settled"]["zero_date_turn_fraction"],
                      "zero_date_auto_seconds": zero_seconds,
                      "stream_fraction": result["P49_settled"]["persistence"]["stream_fraction_of_persistence"]}))


if __name__ == "__main__":
    main()
