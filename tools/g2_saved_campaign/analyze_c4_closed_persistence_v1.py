"""Analyze pinned, naturally closed small C4 receipts; no game or Driver reads.

Evidence layer: actual runtime stage/response projections, not a benchmark,
lossless history audit, WAL qualification or sustained-throughput acceptance.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
from ck3_live_run_id import current_machine_id

PACK = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
PINS = {
    "CLOSED-FRAGMENT-0202-0251-COMPACT62.json": (136681, "083c47f193b5ae1ce4cb10889978e272072ea1c7396f620e1041c6c0c9eaa59b"),
    "C4-CLOSED-STAGE-TRACE62.jsonl": (111191, "0ae1031c5ca707d0332e31d2b751cab943f54f65e5e88849c915eb9221abc312"),
    "C4-CLOSED-STAGE-TRACE62.json": (889, "a00fb5565f23a458bc849a9fd1b467a84d46bf12820abe906762733f88ddc600"),
    "CLOSED-0211-TIMING-HEADER62.json": (2317, "0bae2fc33eec254a3f44106547297c3e6f839fcd218cce47ec4c98930e8b40b7"),
}
OLD_LEDGER = "docs/ck3-native-ai/evidence/robert-v20261019-closed-wall-ledger03.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_pinned(path, expected, pins):
    require(path.stat().st_size <= 256 * 1024, "input exceeds small sealed scope")
    data = path.read_bytes()
    actual = (len(data), hashlib.sha256(data).hexdigest())
    require(actual == expected, f"sealed input mismatch: {path}")
    pins.append({"path": str(path), "bytes": actual[0], "sha256": actual[1]})
    return data


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(start, end):
    return (utc(end) - utc(start)).total_seconds()


def analyze(pack):
    pins = []
    values = {name: read_pinned(pack / name, pin, pins) for name, pin in PINS.items()}
    compact = json.loads(values["CLOSED-FRAGMENT-0202-0251-COMPACT62.json"])
    trace = [json.loads(line) for line in values["C4-CLOSED-STAGE-TRACE62.jsonl"].splitlines()]
    trace_receipt = json.loads(values["C4-CLOSED-STAGE-TRACE62.json"])
    header = json.loads(values["CLOSED-0211-TIMING-HEADER62.json"])
    old = json.loads(read_pinned(REPO / OLD_LEDGER, (28228, "0647fb0e1383bafab9db4aa8e3f84f9b73c9bba7e7e29138f1d60e02b059e775"), pins))
    machine = current_machine_id()
    require(all(doc["machine_id"] == machine for doc in (compact, trace_receipt, header, old)), "machine identity mismatch")
    require(compact["range_closed"] and len(trace) == trace_receipt["rows"] == 417, "closed trace shape")
    rows = [dict(row) for row in compact["responses"]]
    by_sequence = {row["sequence"]: row for row in rows}
    require(header["sequence"] == 211 and by_sequence[211].get("elapsed_seconds") is None, "211 supplement scope")
    by_sequence[211].update(header["timing"])
    by_sequence[211]["selected_step"] = header["existing_context_receipts"][-1]["content"]["selected_step"]
    met = [row for row in rows if row.get("after_frame")]
    require(len(met) == 24 and met[-1]["sequence"] == 250, "settled MET pairs")
    dates = [row["after_frame"]["date_raw"] for row in met]
    require(dates == sorted(dates), "date order")
    days = (dates[-1] - dates[0]) / 24
    require(days == 46 and by_sequence[251]["is_error"] is True, "partial FULL endpoints")
    start = compact["C4_first_AUTO_start_utc"]
    end = by_sequence[202]["ended_at_utc"]
    windows = {}
    for label, anchor, origin in (
        ("entire_run_including_all_maintenance", compact["run_wall_start_utc"], old["actual_date_endpoints"]["initial"]),
        ("SDK115_including_all_maintenance", compact["adopted_SDK_first_AUTO_start_utc"], old["actual_date_endpoints"]["new_SDK_opening"]),
        ("C4_failed_FULL_including_251_and_outer_failure", start, dates[0]),
    ):
        wall = seconds(anchor, end)
        elapsed_days = (dates[-1] - origin) / 24
        windows[label] = {"start_utc": anchor, "end_utc": end, "wall_seconds": wall,
                          "actual_days": elapsed_days, "seconds_per_actual_day": wall / elapsed_days}
    windows["C4_settled_prefix_only"] = {"start_utc": start, "end_utc": met[-1]["ended_at_utc"],
        "wall_seconds": seconds(start, met[-1]["ended_at_utc"]), "actual_days": days,
        "scope": "24 paired cycles only; excludes pending251, not whole-run qualification"}
    timed = [row for row in rows if row.get("elapsed_seconds") is not None]
    require(len(timed) == 49, "all child RPC timing including supplemented211")
    rpc_groups = defaultdict(lambda: {"count": 0, "elapsed_seconds": 0.0})
    for row in timed:
        key = row.get("selected_step") or row["request"].get("tool") or "unknown"
        if key.startswith("query-war-entry-assessments-"):
            key = "query-war-entry-assessments-*"
        if row["sequence"] == 251:
            key = "AUTO251_publisher_failure"
        rpc_groups[key]["count"] += 1
        rpc_groups[key]["elapsed_seconds"] += row["elapsed_seconds"]
    stages = defaultdict(list)
    for row in trace:
        require(type(row["elapsed_ns"]) is int and row["elapsed_ns"] >= 0, "stage elapsed scalar")
        stages[row["stage"]].append(row)
    stage_totals = {name: {"count": len(group), "wall_seconds_sum": sum(r["elapsed_ns"] for r in group) / 1e9,
        "wall_seconds_max": max(r["elapsed_ns"] for r in group) / 1e9} for name, group in stages.items()}
    parents = sorted(stages["driver.full_state_persistence"], key=lambda r: r["finished_at_utc"])
    require(len(parents) == 14 and len({r["persistence_attempt_id"] for r in parents}) == 14, "persistence identity")
    barriers, reason_totals = [], defaultdict(lambda: {"count": 0, "seconds": 0.0})
    for parent in parents:
        require(parent["persistence_outcome"] == "write_replace_returned" and parent["actual_wal_append_count"] == 0, "full-write outcome")
        children = [r for r in trace if r.get("step") == parent["persistence_attempt_id"]]
        encoded = [r for r in children if r["stage"] == "driver.full_state_utf8_encoding"]
        streamed = [r for r in children if r["stage"] == "driver.full_state_temp_stream_write"]
        require(len(encoded) == len(streamed) == 1, "parent encoding/write association")
        require(encoded[0]["history_json_bytes"] == parent["history_json_bytes"], "history size identity")
        require(encoded[0]["persistence_attempt_id"] == parent["persistence_attempt_id"], "attempt scalar identity")
        reason = parent["full_barrier_reason"]
        reason_totals[reason]["count"] += 1
        reason_totals[reason]["seconds"] += parent["elapsed_ns"] / 1e9
        barriers.append({key: parent[key] for key in ("persistence_attempt_id", "finished_at_utc", "full_barrier_reason",
            "history_json_bytes", "history_rows", "timeline_append_candidate", "candidate_append_run_length",
            "closed_candidate_run_length", "candidate_activation_churn_count", "full_write_success_count")}
            | {"full_seconds": parent["elapsed_ns"] / 1e9, "logical_payload_bytes": streamed[0]["payload_bytes"],
               "child_stage_seconds": {r["stage"]: r["elapsed_ns"] / 1e9 for r in children}})
    candidates = [row for row in parents if row["timeline_append_candidate"]]
    require(len(candidates) == 6 and all(row["candidate_append_run_length"] == 1 for row in candidates), "candidate runs")
    advances = []
    for row in rows:
        if row.get("selected_step") != "life-advance":
            continue
        observed = row["observed_timing_and_dates"]
        clock = observed["/result/campaign_deadline_native_clock_v1"]
        advances.append({"sequence": row["sequence"], "elapsed_seconds": row["elapsed_seconds"],
            "actual_days": (observed["/result/ending_date/date_raw"] - observed["/result/starting_date/date_raw"]) / 24,
            "trigger_reasons": clock["stopped"]["trigger_reasons"],
            "exact_one_day_qualification_claimed": clock["exact_one_day_qualification_claimed"]})
    return {"schema": "xar.ck3.c4-closed-persistence-analysis.v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "sourcepins": pins,
        "evidence_layer": "naturally closed runtime scalar receipts; no synthetic benchmark or production change",
        "source_business_commit": compact["business_source_commit"], "control_status": compact["control_status"],
        "windows": windows, "snapshot_observed_utc": compact["observed_at_utc"],
        "open_maintenance_wall_after_closed_endpoint_seconds": seconds(end, compact["observed_at_utc"]),
        "last_verified_date_raw": dates[-1], "settled_cycle_count": 24, "pending_unpaired_sequence": 251,
        "RPC_timing_count": len(timed), "RPC_elapsed_sum_seconds": sum(r["elapsed_seconds"] for r in timed),
        "C4_other_wall_seconds": seconds(start, end) - sum(r["elapsed_seconds"] for r in timed),
        "RPC_groups": dict(rpc_groups), "stage_totals": stage_totals,
        "stage_overlap_rule": "nested parent/child totals must not be added; elapsed_ns is wall, not CPU",
        "persistence_reasons": dict(reason_totals), "persistence_attempts": barriers,
        "growth": {"first_history_json_bytes": parents[0]["history_json_bytes"], "last_history_json_bytes": parents[-1]["history_json_bytes"],
            "history_json_growth_bytes": parents[-1]["history_json_bytes"] - parents[0]["history_json_bytes"],
            "history_row_growth": parents[-1]["history_rows"] - parents[0]["history_rows"],
            "logical_full_payload_bytes_sum": sum(r["logical_payload_bytes"] for r in barriers),
            "scope": "observed first/last full barrier, not retained allocation, full Driver size, or future model"},
        "WAL_assessment": {"candidate_count": 6, "longest_candidate_run": 1, "closed_length_one_runs": sum(r["closed_candidate_run_length"] == 1 for r in parents),
            "actual_append_count": 0, "qualified_current_append_count": None,
            "policy": "candidate is only timeline-family classification, not WAL eligibility",
            "conclusion": "No demonstrated consecutive append saving. Existing experimental activation rewrites sealed base; full barriers reset it. Multiday calls remain outside old exact-one-day qualification. Keep default off."},
        "life_advance_observations": advances, "ordinary_event_wait_fix_actual_case_seen": any(r["trigger_reasons"] != ["date_deadline"] for r in advances),
        "limitations": ["107-day cumulative wall still includes all earlier maintenance; local46d cannot qualify sustained goal.",
            "AUTO251 failed publication, no paired MET and no full-cycle credit. Post-endpoint maintenance is listed for next cumulative update.",
            "Prior reported 3.4GB Driver cannot be attributed from this window; no old/live Driver or SAVE body was inspected.",
            "Stage totals overlap and no Native-only split of declarable211 is available here.",
            "History growth between barriers groups deferred queries and command rows; it cannot identify one row's bytes.",
            "Two ~100ms persistence tails localize to open/replace; their cause is unproven, not assigned to Defender."],
        "sustained_goal_qualified": False, "game_RPC_calls": 0, "Driver_SAVE_reads": 0, "external_writes_bytes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.pack)
    result["producer"] = {"path": str(Path(__file__).relative_to(REPO)), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result["storage"] = {"pool": "existing REPO-ONLY-MICROPOOL01", "producer_closed": True, "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size,
        "windows": result["windows"], "persistence_reasons": result["persistence_reasons"]}))


if __name__ == "__main__":
    main()
