"""Natural C6 completed-cycle analysis; missing outer/native timing stays null."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from analyze_c4_closed_persistence_v1 import REPO, PACK, current_machine_id, read_pinned, require, seconds, utc

PINS = {
    "CLOSED-FRAGMENT-0287-0353-COMPACT72.json": (220024, "51f553dd034d5f29646996a3168a9d29591691a2a13bdf25e4b62d2b8eeffe9e"),
    "C6-CLOSED-STAGE-TRACE72.json": (889, "c15ece2ec096c2fc648931070a4eab5f650742bbbffed5a3142dab2f11402d4d"),
    "C6-CLOSED-STAGE-TRACE72.jsonl": (174365, "0b5f670097d91fa531ec371cf584ff37fba49d8c1a5b5a0d0fee5b9e759b96a2"),
}


def interval(row):
    end = utc(row["finished_at_utc"])
    return end - timedelta(seconds=row["elapsed_ns"] / 1e9), end


def analyze(pack):
    pins = []
    raw = {name: read_pinned(pack / name, pin, pins) for name, pin in PINS.items()}
    compact = json.loads(raw["CLOSED-FRAGMENT-0287-0353-COMPACT72.json"])
    sealed = json.loads(raw["C6-CLOSED-STAGE-TRACE72.json"])
    trace = [json.loads(line) for line in raw["C6-CLOSED-STAGE-TRACE72.jsonl"].splitlines()]
    previous = json.loads(read_pinned(REPO / "docs/ck3-native-ai/evidence/c5-closed-persistence-analysis01.json",
        (9342, "09c162723691ee88e0644adc3f7fb273963b4693df4a19188a083ee99f4d7ad9"), pins))
    machine = current_machine_id()
    require(all(x["machine_id"] == machine for x in (compact, sealed, previous)), "machine identity")
    require(compact["range_closed"] and len(trace) == sealed["rows"] == 631, "closed trace shape")
    seq = {r["sequence"]: r for r in compact["responses"]}
    controls = {}
    for number in (289, 291):
        source = seq[number]["source"]
        original = json.loads(read_pinned(Path(source["path"]), (source["bytes"], source["sha256"]), pins))
        controls[number] = original["result"]["structured_content"]
    require(controls[289]["cumulative_cycles"] == 112 and controls[291]["cumulative_cycles"] == 142,
            "once settlement and new cycles")
    require(controls[291]["actual_turns"] == 30 and controls[291]["status"] == "bounded_loop_finished", "completed FULL")
    require(seq[291]["ended_at_utc"] is None, "outer time remains unavailable")
    rows = [seq[n] for n in range(292, 354)]
    met = [r for r in rows if r.get("after_frame")]
    require(len(met) == 30 and met[-1]["sequence"] == 353, "paired cycles")
    date0, date1 = met[0]["after_frame"]["date_raw"], met[-1]["after_frame"]["date_raw"]
    days = (date1 - date0) / 24
    require(days == 79 and controls[291]["actual_end_date_raw"] == date1, "actual date progress")
    start, end = seq[292]["started_at_utc"], seq[353]["ended_at_utc"]
    warm = seq[287]["started_at_utc"]
    windows = {}
    for name in ("entire_run_including_maintenance", "SDK115_including_maintenance"):
        old = previous["windows"][name]
        actual_days = old["actual_days"] + (date1 - previous["last_verified_date_raw"]) / 24
        wall = seconds(old["start_utc"], end)
        windows[name] = {"start_utc": old["start_utc"], "end_at_verified_MET353_utc": end,
            "wall_seconds": wall, "actual_days": actual_days, "seconds_per_actual_day": wall / actual_days}
    for name, anchor in (("C6_from_warm287_including_startup_SAVE290", warm), ("AUTO292_through_MET353_only", start)):
        wall = seconds(anchor, end)
        windows[name] = {"start_utc": anchor, "end_at_verified_MET353_utc": end,
            "wall_seconds": wall, "actual_days": days, "seconds_per_actual_day": wall / days}
    timed = [r for r in rows if r.get("elapsed_seconds") is not None]
    unknown = [r for r in rows if r.get("status") == "oversized_not_observed"]
    require(len(timed) == 60 and [r["sequence"] for r in unknown] == [296, 328], "missing query timings")
    groups = defaultdict(lambda: {"count": 0, "seconds": 0.0})
    for row in timed:
        key = row.get("selected_step") or row["request"]["tool"]
        if key.startswith("query-war-entry-assessments-"):
            key = "query-war-entry-assessments-*"
        groups[key]["count"] += 1
        groups[key]["seconds"] += row["elapsed_seconds"]
    stages = defaultdict(list)
    for row in trace:
        require(type(row["elapsed_ns"]) is int and row["elapsed_ns"] >= 0, "stage elapsed")
        stages[row["stage"]].append(row)
    totals = {name: {"count": len(group), "seconds": sum(r["elapsed_ns"] for r in group) / 1e9,
                    "max_seconds": max(r["elapsed_ns"] for r in group) / 1e9} for name, group in stages.items()}
    full = sorted(stages["driver.full_state_persistence"], key=lambda r: r["finished_at_utc"])
    require(len(full) == 24 and len({r["persistence_attempt_id"] for r in full}) == 24, "full write attempts")
    reasons = defaultdict(lambda: {"count": 0, "seconds": 0.0})
    logical_bytes = 0
    for parent in full:
        require(parent["persistence_outcome"] == "write_replace_returned" and parent["actual_wal_append_count"] == 0, "write result")
        children = [r for r in trace if r.get("step") == parent["persistence_attempt_id"]]
        encoded = [r for r in children if r["stage"] == "driver.full_state_utf8_encoding"]
        streamed = [r for r in children if r["stage"] == "driver.full_state_temp_stream_write"]
        require(len(encoded) == len(streamed) == 1, "persistence stage association")
        require(encoded[0]["history_json_bytes"] == parent["history_json_bytes"] and
                encoded[0]["persistence_attempt_id"] == parent["persistence_attempt_id"], "encoded history identity")
        logical_bytes += streamed[0]["payload_bytes"]
        reasons[parent["full_barrier_reason"]]["count"] += 1
        reasons[parent["full_barrier_reason"]]["seconds"] += parent["elapsed_ns"] / 1e9
    candidates = [r for r in full if r["timeline_append_candidate"]]
    require(len(candidates) == 11 and all(r["candidate_append_run_length"] == 1 for r in candidates), "candidate runs")
    lifetimes = [interval(r) for r in stages["driver.life_advance_total"]]
    waits = stages["driver.life_advance_public_change_wait"]
    inside = [r for r in waits if any(a <= interval(r)[0] <= interval(r)[1] <= b for a, b in lifetimes)]
    advances = []
    for row in rows:
        if row.get("selected_step") != "life-advance":
            continue
        observed = row["observed_timing_and_dates"]
        clock = observed["/result/campaign_deadline_native_clock_v1"]
        advances.append({"sequence": row["sequence"], "AUTO_seconds": row["elapsed_seconds"],
            "days": (observed["/result/ending_date/date_raw"] - observed["/result/starting_date/date_raw"]) / 24,
            "trigger_reasons": clock["stopped"]["trigger_reasons"], "early_boundary_cancel": clock["early_boundary_cancel"]})
    require(sum(r["days"] for r in advances) == days, "advance sum")
    plans = []
    for row in sorted(stages["service.normal_plan_turn"], key=lambda r: r["elapsed_ns"], reverse=True)[:5]:
        a, b = interval(row)
        matched = [r for r in timed if utc(r["started_at_utc"]) <= a <= b <= utc(r["ended_at_utc"])]
        plans.append({"end_utc": row["finished_at_utc"], "seconds": row["elapsed_ns"] / 1e9,
                      "known_RPC_sequence": matched[0]["sequence"] if matched else None})
    wall = seconds(start, end)
    return {"schema": "xar.ck3.c6-closed-persistence-analysis.v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "sourcepins": pins,
        "evidence_layer": "naturally completed cycles and stage receipts; no benchmark or Native-only attribution",
        "source_business_commit": compact["business_source_commit"], "windows_to_verified_endpoint": windows,
        "control": {"FULL291_status": controls[291]["status"], "settled_cycles_before": 112, "settled_cycles_after": 142,
            "new_cycles": 30, "once289_preexisting_MET286_settlement": True, "once289_new_RPC_count": 0,
            "actual_new_days": days, "last_verified_date_raw": date1, "FULL291_outer_started_utc": None,
            "FULL291_outer_ended_utc": None, "FULL291_complete_outer_wall_seconds": None,
            "FULL291_wall_lower_bound_seconds": wall, "unmeasured_outer_completion_tail_seconds": None,
            "next_FULL354_running_not_consumed": True},
        "maintenance": {"C5_end_to_C6_warm287_seconds": seconds(previous["windows"]["entire_run_including_maintenance"]["end_utc"], warm),
            "warm287_to_first_AUTO292_seconds": seconds(warm, start), "SEM287_seconds": seq[287]["elapsed_seconds"],
            "CAP288_seconds": seq[288]["elapsed_seconds"], "SAVE290_seconds": seq[290]["elapsed_seconds"],
            "all_in_cumulative_wall": True},
        "tool_RPCs": {"full_child_count": len(rows), "known_timing_count": len(timed),
            "known_seconds": sum(r["elapsed_seconds"] for r in timed), "known_groups": dict(groups),
            "unknown_rows": unknown, "missing_RPCs_plus_other_control_wall_seconds": wall - sum(r["elapsed_seconds"] for r in timed),
            "Native_command_count": None, "Native_only_wall_seconds": None,
            "scope": "Tool RPCs may contain planner, Native, verification, serialization and display. Unknown queries are not gaps."},
        "stage_totals": totals, "stage_overlap": "Nested totals cannot be added; elapsed_ns measures wall, not CPU.",
        "persistence": {"full_success_count": 24, "reason_totals": dict(reasons), "logical_payload_bytes_sum": logical_bytes,
            "first_history_bytes": full[0]["history_json_bytes"], "last_history_bytes": full[-1]["history_json_bytes"],
            "history_growth_bytes": full[-1]["history_json_bytes"] - full[0]["history_json_bytes"],
            "first_history_rows": full[0]["history_rows"], "last_history_rows": full[-1]["history_rows"],
            "history_growth_rows": full[-1]["history_rows"] - full[0]["history_rows"],
            "candidate_count": len(candidates), "longest_run": 1, "closed_length_one_runs": sum(r["closed_candidate_run_length"] == 1 for r in full),
            "actual_WAL_appends": 0, "default_off": True, "WAL_qualified": False,
            "saving_conclusion": "No consecutive run; activation rewrite and exact-day eligibility gaps remain. No safe new persistence source change justified by this window."},
        "life": {"count": len(lifetimes), "public_wait_count_inside_life": len(inside),
            "public_wait_seconds_inside_life": sum(r["elapsed_ns"] for r in inside) / 1e9,
            "public_wait_count_outside_life": len(waits) - len(inside), "advance_observations": advances},
        "largest_planning_spans": plans,
        "next_narrow_hotspot": "Planner8.204s versus small choose/capabilities/history/copy subspans; examine preparation/providers, especially plans in missing296/328 windows. Do not attribute them to Native declaration CB or alter strategy.",
        "limits": ["Only AUTO292-to-MET353 is measured for the completed batch; outer FULL timestamps are absent, not filled with file mtime.",
            "C6 startup, warm recovery, SAVE290 and every earlier maintenance gap remain in original-anchor windows.",
            "296/328 Native-only and tool timings are unknown; no body read or extra RPC was used to recover them.",
            "History endpoints are not device allocation, lossless row attribution or a long-term growth forecast.",
            "Quiet first79d completed window cannot qualify sustained30year or war throughput; prior3.4GB cause is not proven."],
        "sustained_goal_qualified": False, "game_RPC_calls": 0, "Driver_SAVE_reads": 0, "external_writes_bytes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.pack)
    result["producer"] = {"path": str(Path(__file__).relative_to(REPO)), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result["storage"] = {"pool": "existing micro32KiB C6 follow-up", "producer_closed": True, "future_writes": 0,
                         "allocated_bytes": None, "physical_credit_bytes": 0}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    require(len(encoded.encode()) <= 16 * 1024, "receipt budget")
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size,
                      "windows": result["windows_to_verified_endpoint"], "persistence": result["persistence"]}))


if __name__ == "__main__":
    main()
