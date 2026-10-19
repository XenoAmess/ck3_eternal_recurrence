"""Pinned natural C5 follow-up; includes failed adoption/publication wall.

Runtime-projection evidence, not a benchmark or broad event/WAL acceptance.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import argparse

from analyze_c4_closed_persistence_v1 import REPO, PACK, current_machine_id, read_pinned, require, seconds, utc

PINS = {
    "CLOSED-FRAGMENT-0252-0286-COMPACT70.json": (55609, "fc066be0f93adf9141be43ff1b3175565a1781be4735a6f4b72fdec45a199e1e"),
    "C5-CLOSED-STAGE-TRACE70.json": (888, "96e85e205a48212e6a2ed7669810ce2dc39b812af3701f53e64118fe3a2a4773"),
    "C5-CLOSED-STAGE-TRACE70.jsonl": (35349, "47a85997f2672f1bfaa7fc01c97bd5bf5f803d9af6b762e287fb67c2ae6665e3"),
}
C4 = "docs/ck3-native-ai/evidence/c4-closed-persistence-analysis01.json"


def analyze(pack):
    pins = []
    raw = {name: read_pinned(pack / name, pin, pins) for name, pin in PINS.items()}
    compact = json.loads(raw["CLOSED-FRAGMENT-0252-0286-COMPACT70.json"])
    sealed = json.loads(raw["C5-CLOSED-STAGE-TRACE70.json"])
    trace = [json.loads(line) for line in raw["C5-CLOSED-STAGE-TRACE70.jsonl"].splitlines()]
    old = json.loads(read_pinned(REPO / C4, (26589, "c648b3f20c77cd2772d265753721d25791eb92e41c79d87224a3f00e61bbb9f8"), pins))
    machine = current_machine_id()
    require(all(doc["machine_id"] == machine for doc in (compact, sealed, old)), "machine identity")
    require(compact["range_closed"] and len(trace) == sealed["rows"] == 152, "closed trace")
    rows = compact["responses"]
    seq = {r["sequence"]: r for r in rows}
    first = compact["C5_first_AUTO_start_utc"]
    require(first == seq[255]["started_at_utc"] and seq[255]["is_error"] is True, "first failed AUTO anchor")
    require(seq[263]["status"] == "oversized_not_observed", "263 remains unknown, no header")
    require(seq[286]["is_error"] is False and seq[258]["client_error"], "partial publication endpoint")
    start, end = seq[259]["started_at_utc"], seq[258]["ended_at_utc"]
    date0, date1 = seq[260]["after_frame"]["date_raw"], seq[286]["after_frame"]["date_raw"]
    days = (date1 - date0) / 24
    require(days == 3 and seq[284]["after_frame"]["date_raw"] == date1, "verified date endpoints")
    windows = {}
    for label, old_key in (("entire_run_including_maintenance", "entire_run_including_all_maintenance"),
                           ("SDK115_including_maintenance", "SDK115_including_all_maintenance")):
        previous = old["windows"][old_key]
        elapsed_days = previous["actual_days"] + (date1 - old["last_verified_date_raw"]) / 24
        wall = seconds(previous["start_utc"], end)
        windows[label] = {"start_utc": previous["start_utc"], "end_utc": end,
            "wall_seconds": wall, "actual_days": elapsed_days, "seconds_per_actual_day": wall / elapsed_days}
    for label, anchor in (("C5_from_failed_first_AUTO_including_repairs", first), ("FULL258_only_partial_failure_window", start)):
        wall = seconds(anchor, end)
        windows[label] = {"start_utc": anchor, "end_utc": end, "wall_seconds": wall,
                         "actual_days": days, "seconds_per_actual_day": wall / days}
    stages = defaultdict(list)
    for row in trace:
        require(type(row["elapsed_ns"]) is int and row["elapsed_ns"] >= 0, "elapsed scalar")
        stages[row["stage"]].append(row)
    stage_totals = {key: {"count": len(group), "seconds": sum(r["elapsed_ns"] for r in group) / 1e9}
                    for key, group in stages.items()}
    parents = sorted(stages["driver.full_state_persistence"], key=lambda r: r["finished_at_utc"])
    require(len(parents) == 3, "persistence attempts")
    barriers = []
    for parent in parents:
        require(parent["persistence_outcome"] == "write_replace_returned" and parent["actual_wal_append_count"] == 0, "full-write result")
        children = [r for r in trace if r.get("step") == parent["persistence_attempt_id"]]
        encoded = [r for r in children if r["stage"] == "driver.full_state_utf8_encoding"]
        streamed = [r for r in children if r["stage"] == "driver.full_state_temp_stream_write"]
        require(len(encoded) == len(streamed) == 1 and encoded[0]["history_json_bytes"] == parent["history_json_bytes"], "attempt encoding association")
        barriers.append({key: parent[key] for key in ("persistence_attempt_id", "finished_at_utc", "full_barrier_reason",
            "history_json_bytes", "history_rows", "timeline_append_candidate", "candidate_append_run_length",
            "closed_candidate_run_length", "candidate_activation_churn_count")}
            | {"full_seconds": parent["elapsed_ns"] / 1e9, "logical_payload_bytes": streamed[0]["payload_bytes"]})
    require([r["candidate_append_run_length"] for r in parents] == [0, 1, 0], "one interrupted candidate run")
    life = stages["driver.life_advance_total"]
    require(len(life) == 1, "single completed life span")
    life_end = utc(life[0]["finished_at_utc"])
    life_start = life_end - timedelta(seconds=life[0]["elapsed_ns"] / 1e9)
    waits, outside = [], []
    for row in stages["driver.life_advance_public_change_wait"]:
        ended = utc(row["finished_at_utc"])
        started = ended - timedelta(seconds=row["elapsed_ns"] / 1e9)
        (waits if life_start <= started <= ended <= life_end else outside).append(row)
    require(len(waits) == 6 and len(outside) == 1, "public-wait temporal association")
    require(utc(seq[285]["started_at_utc"]) <= utc(outside[0]["finished_at_utc"]) <= utc(seq[285]["ended_at_utc"]), "outside wait belongs to event selection RPC")
    observed = seq[281]["observed_timing_and_dates"]
    clock = observed["/result/campaign_deadline_native_clock_v1"]
    require(observed["/result/active_event/source"] == "native" and clock["early_boundary_cancel"]["accepted"] is True, "actual early event sample")
    require((clock["target_date_raw"] - clock["starting_date_raw"]) / 24 == 8, "original target")
    timed = [r for r in rows if 259 <= r["sequence"] <= 286 and r.get("elapsed_seconds") is not None]
    require(len(timed) == 27, "one missing oversized RPC")
    known_rpc = sum(r["elapsed_seconds"] for r in timed)
    return {"schema": "xar.ck3.c5-closed-persistence-analysis.v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "sourcepins": pins,
        "evidence_layer": "naturally closed scalar runtime receipts; no benchmark or gameplay calls",
        "source_business_commit": compact["business_source_commit"], "control_status": compact["control_status"],
        "windows": windows, "settled_new_cycle_count": 13, "pending_unsettled_cycle": 112,
        "verified_AUTO_pending_settlement": 285, "original_successful_MET_pending_display_settlement": 286,
        "last_verified_date_raw": date1, "inter_generation_maintenance_since_C4_end_seconds": seconds(old["windows"]["C4_failed_FULL_including_251_and_outer_failure"]["end_utc"], first),
        "repair_wall_first_failed_AUTO_to_FULL258_first_AUTO_seconds": seconds(first, start),
        "post_MET286_to_outer_failure_seconds": seconds(seq[286]["ended_at_utc"], end),
        "open_maintenance_after_closed_endpoint_seconds": seconds(end, compact["observed_at_utc"]),
        "known_FULL258_RPC_count": len(timed), "known_FULL258_RPC_seconds": known_rpc,
        "unknown_RPC263_plus_all_other_control_and_publication_seconds": seconds(start, end) - known_rpc,
        "RPC263_upper_interval_seconds_not_its_measured_duration": seconds(seq[262]["ended_at_utc"], seq[264]["started_at_utc"]),
        "RPC263_timing": None, "stage_totals": stage_totals, "stage_rule": "nested and reused labels cannot be added; use time containment",
        "persistence_attempts": barriers,
        "growth": {"first_history_bytes": parents[0]["history_json_bytes"], "last_history_bytes": parents[-1]["history_json_bytes"],
            "bytes_delta": parents[-1]["history_json_bytes"] - parents[0]["history_json_bytes"],
            "rows_delta": parents[-1]["history_rows"] - parents[0]["history_rows"],
            "delta_since_C4_last_barrier_bytes": parents[-1]["history_json_bytes"] - old["growth"]["last_history_json_bytes"],
            "logical_full_payload_bytes_sum": sum(r["logical_payload_bytes"] for r in barriers),
            "scope": "observed barriers only; no long-term extrapolation or allocation claim"},
        "WAL": {"actual_appends": 0, "candidate_runs": [1], "closed_by": "select-event-option-3 full barrier",
            "eligibility_qualified": False, "default_off": True, "demonstrated_consecutive_append_saving": False},
        "ordinary_event_wait_sample": {"sequence": 281, "requested_days": 8, "actual_days": days,
            "active_event_source": observed["/result/active_event/source"], "progress_status": observed["/result/progress_status"],
            "clock_stopped_state": clock["stopped"]["state"], "clock_completed_ticks": clock["stopped"]["completed_daily_ticks"],
            "clock_cancel": clock["early_boundary_cancel"], "AUTO_seconds": seq[281]["elapsed_seconds"],
            "life_total_seconds": life[0]["elapsed_ns"] / 1e9, "within_life_wait_count": len(waits),
            "within_life_wait_seconds": sum(r["elapsed_ns"] for r in waits) / 1e9,
            "outside_life_wait_seconds_in_AUTO285": sum(r["elapsed_ns"] for r in outside) / 1e9,
            "coverage": "this actual ordinary-event early boundary returned without old30s tail; not all variants or batch success"},
        "limitations": ["First failed C5 AUTO and all maintenance remain in adopted-window and cumulative denominators.",
            "263 body was not read and no tiny timing header exists; remainder is not a queue/display attribution.",
            "286 result succeeded; display failure prevents cycle112 settlement, no replay and no extra day credit.",
            "Shared wait stage is still labelled life-advance for event selection; timestamps separate it.",
            "The native-only portion of declarable execution and cause of prior3.4GB Driver remain unqualified."],
        "sustained_goal_qualified": False, "game_RPC_calls": 0, "Driver_SAVE_reads": 0, "external_writes_bytes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.pack)
    result["producer"] = {"path": str(Path(__file__).relative_to(REPO)), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result["storage"] = {"pool": "REPO-ONLY-MICROPOOL01 existing32KiB follow-up", "producer_closed": True,
                         "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    require(len(encoded.encode("utf-8")) <= 16 * 1024, "receipt size budget")
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size, "windows": result["windows"]}))


if __name__ == "__main__":
    main()
